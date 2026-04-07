<template>
  <DarkPageHeader
    title="课程"
    search-placeholder="搜索课程名称、简介、章节或标签..."
    v-model="filters.search"
    @search="fetchCourses"
  >
    <template #filters>
      <button v-for="ft in fileTypeChips" :key="ft.value ?? 'all'" type="button" class="dark-chip" :class="{ active: filters.file_type === ft.value }" @click="setFileType(ft.value)">{{ ft.label }}</button>
    </template>
    <template #actions>
      <button type="button" class="dark-advanced-toggle" :class="{ expanded: advancedFiltersVisible }" @click="toggleAdvancedFilters">
        <FilterOutlined /><span class="toggle-label">筛选</span>
        <component :is="advancedFiltersVisible ? UpOutlined : DownOutlined" class="toggle-arrow" />
      </button>
      <a-button v-if="canCreateCourse" type="primary" ghost @click="openCreate">创建课程</a-button>
    </template>
    <template #extra>
      <transition name="advanced-filters">
        <div v-show="advancedFiltersVisible" class="dark-adv-row">
          <a-select v-model:value="filters.sort" class="dark-adv-select" @change="fetchCourses">
            <a-select-option value="latest">按最新上线</a-select-option>
            <a-select-option value="learning_priority">按学习进度</a-select-option>
            <a-select-option value="required_first">按必修优先</a-select-option>
            <a-select-option value="duration_asc">按课程时长</a-select-option>
            <a-select-option value="rating">按评分</a-select-option>
            <a-select-option value="students">按学员数</a-select-option>
          </a-select>
          <a-select v-model:value="filters.instructor_id" :options="instructorOptions" allow-clear placeholder="按教官" class="dark-adv-select" @change="fetchCourses" />
          <a-select v-model:value="filters.is_required" allow-clear placeholder="必修/选修" class="dark-adv-select" @change="fetchCourses">
            <a-select-option :value="true">仅看必修</a-select-option>
            <a-select-option :value="false">仅看选修</a-select-option>
          </a-select>
          <a-select v-model:value="filters.learning_status" allow-clear placeholder="学习状态" class="dark-adv-select" @change="fetchCourses">
            <a-select-option value="not_started">未开始</a-select-option>
            <a-select-option value="in_progress">进行中</a-select-option>
            <a-select-option value="completed">已完成</a-select-option>
          </a-select>
          <a-range-picker v-model:value="dateRange" class="dark-adv-date" @change="handleDateRangeChange" />
        </div>
      </transition>
    </template>

    <CourseEditorModal
      v-model:open="editorVisible"
      :course-id="editingCourseId"
      :can-manage="editingCourseCanManage"
      @success="fetchCourses"
    />

    <div class="course-stats">
      <span>共 <strong>{{ courses.length }}</strong> 门课程</span>
      <span v-if="authStore.isStudent">已完成 <strong>{{ completedCount }}</strong> 门</span>
      <span v-if="authStore.isStudent">进行中 <strong>{{ inProgressCount }}</strong> 门</span>
    </div>

    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" />
    </div>

    <a-empty v-else-if="!courses.length" description="暂无符合条件的课程" class="empty-block" />

    <div v-else class="course-grid">
      <div
        v-for="(course, index) in courses"
        :key="course.id"
        class="course-card"
        @click="router.push(`/resource/courses/${course.id}`)"
      >
        <div class="card-cover" :style="{ background: getCourseCoverBackground(course, index) }">
          <div class="cover-labels">
            <a-tag class="cover-tag cover-tag-category">{{ getCourseCategoryLabel(course.category) }}</a-tag>
            <div class="cover-tag-stack">
              <a-tag class="cover-tag cover-tag-type">{{ getCourseFileTypeLabel(course.file_type, course.chapter_count) }}</a-tag>
              <a-tag v-if="course.is_required" class="cover-tag cover-tag-required">必修</a-tag>
            </div>
          </div>

          <div
            class="cover-visual"
            :style="{
              '--cover-visual-accent': getCourseCoverVisual(course.category).accent,
              '--cover-visual-glow': getCourseCoverVisual(course.category).glow,
            }"
          >
            <span class="cover-visual-ring">
              <component :is="getCourseCoverVisual(course.category).icon" class="cover-visual-icon" />
            </span>
          </div>

          <div class="cover-footer">
            <span v-if="authStore.isStudent && course.learning_status === 'in_progress'" class="learning-pill">
              正在学习...
            </span>
            <span class="cover-footer-item">
              <ClockCircleOutlined />
              {{ formatCourseDuration(course.duration_seconds, course.duration) }}
            </span>
            <span class="cover-footer-item">
              <PlayCircleOutlined />
              {{ course.chapter_count || 0 }} 章
            </span>
          </div>
        </div>

        <div class="card-body">
          <div class="card-head">
            <div class="card-head-main">
              <div class="card-title-row">
                <h3>{{ course.title }}</h3>
                <span
                  v-if="authStore.isStudent"
                  class="status-pill"
                  :style="{ color: getCourseLearningStatusColor(course.learning_status) }"
                >
                  {{ getCourseLearningStatusLabel(course.learning_status) }}
                </span>
              </div>
              <p>{{ course.description || '暂无课程简介' }}</p>
            </div>
            <div v-if="course.can_manage_course" class="card-actions" @click.stop>
              <a-button size="small" type="text" @click="openEdit(course.id)">编辑</a-button>
              <a-popconfirm title="确定删除此课程吗？" @confirm="handleDelete(course.id)">
                <a-button size="small" type="text" danger>删除</a-button>
              </a-popconfirm>
            </div>
          </div>

          <div class="meta-grid">
            <span>主讲教官：{{ course.instructor_name || '未设置' }}</span>
            <span>创建于 {{ formatDate(course.created_at) }}</span>
            <span>评分 {{ course.rating || '新课' }}</span>
            <span>{{ course.is_required ? '必修课程' : '选修课程' }}</span>
          </div>

          <div v-if="authStore.isStudent" class="progress-panel">
            <div class="progress-top">
              <span>{{ getCourseLearningStatusLabel(course.learning_status) }}</span>
              <span>{{ course.completed_chapter_count || 0 }}/{{ course.chapter_count || 0 }} 章</span>
            </div>
            <a-progress :percent="course.progress_percent || 0" size="small" />
          </div>
        </div>
      </div>
    </div>
  </DarkPageHeader>
</template>

<script setup lang="ts">
import {
  AppstoreOutlined,
  CarOutlined,
  ClockCircleOutlined,
  DownOutlined,
  FilterOutlined,
  LaptopOutlined,
  PlayCircleOutlined,
  ReadOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
  ThunderboltOutlined,
  UpOutlined,
} from '@ant-design/icons-vue'
import type { Dayjs } from 'dayjs'
import { computed, onMounted, reactive, ref, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { CourseListResponse } from '@/api/learning-resource'
import { deleteCourse, listCourses, listUsers } from '@/api/learning-resource'
import { useAuthStore } from '@/stores/auth'
import CourseEditorModal from '@/components/resource/CourseEditorModal.vue'
import DarkPageHeader from '@/components/common/DarkPageHeader.vue'
import {
  formatCourseDuration,
  formatDate,
  getCourseCategoryLabel,
  getCourseFileTypeLabel,
  getCourseLearningStatusColor,
  getCourseLearningStatusLabel,
  getUserDisplayName,
} from '@/utils/learning-resource'

const router = useRouter()
const authStore = useAuthStore()
const canCreateCourse = computed(() => authStore.hasPermission('CREATE_COURSE'))

const loading = ref(false)
const courses = ref<CourseListResponse[]>([])
const instructorOptions = ref<Array<{ value: number; label: string }>>([])
const editorVisible = ref(false)
const editingCourseId = ref<number | null>(null)
const dateRange = ref<Dayjs[] | null>(null)
const advancedFiltersVisible = ref(false)
const editingCourseCanManage = computed(() => {
  if (!editingCourseId.value) {
    return false
  }
  return !!courses.value.find((item) => item.id === editingCourseId.value)?.can_manage_course
})

const filters = reactive({
  search: '',
  instructor_id: undefined as number | undefined,
  sort: authStore.isStudent ? 'learning_priority' : 'latest',
  is_required: undefined as boolean | undefined,
  learning_status: undefined as string | undefined,
  file_type: undefined as string | undefined,
  created_from: undefined as string | undefined,
  created_to: undefined as string | undefined,
})

interface CourseCoverVisual {
  icon: Component
  background: string
  accent: string
  glow: string
}

const defaultCourseCoverVisual: CourseCoverVisual = {
  icon: ReadOutlined,
  background: 'linear-gradient(135deg, #edf1fb 0%, #e4eaf5 100%)',
  accent: '#7a8fca',
  glow: 'rgba(122, 143, 202, 0.14)',
}

const fallbackCoverBackgrounds = [
  'linear-gradient(135deg, #edf1fb 0%, #e4eaf5 100%)',
  'linear-gradient(135deg, #edf3ee 0%, #e1eae3 100%)',
  'linear-gradient(135deg, #f6eee7 0%, #eee2d7 100%)',
  'linear-gradient(135deg, #edf4f3 0%, #e2ece9 100%)',
]

const courseCoverVisualMap: Record<string, CourseCoverVisual> = {
  law: {
    icon: SafetyCertificateOutlined,
    background: 'linear-gradient(135deg, #edf5ec 0%, #e4eee6 100%)',
    accent: '#6c8f7b',
    glow: 'rgba(108, 143, 123, 0.12)',
  },
  fraud: {
    icon: AppstoreOutlined,
    background: 'linear-gradient(135deg, #eef1fb 0%, #e5e9f6 100%)',
    accent: '#7b8dc6',
    glow: 'rgba(123, 141, 198, 0.14)',
  },
  traffic: {
    icon: CarOutlined,
    background: 'linear-gradient(135deg, #ecf2fb 0%, #dfe9f4 100%)',
    accent: '#6f8fb2',
    glow: 'rgba(111, 143, 178, 0.14)',
  },
  community: {
    icon: TeamOutlined,
    background: 'linear-gradient(135deg, #f7efe7 0%, #efdfd3 100%)',
    accent: '#b08b73',
    glow: 'rgba(176, 139, 115, 0.12)',
  },
  cybersec: {
    icon: LaptopOutlined,
    background: 'linear-gradient(135deg, #edf4f2 0%, #e1ebe8 100%)',
    accent: '#6c9b98',
    glow: 'rgba(108, 155, 152, 0.12)',
  },
  physical: {
    icon: ThunderboltOutlined,
    background: 'linear-gradient(135deg, #f8efe8 0%, #f0dfd1 100%)',
    accent: '#c19475',
  glow: 'rgba(193, 148, 117, 0.12)',
  },
}

const fileTypeChips = [
  { value: undefined as string | undefined, label: '全部' },
  { value: 'video', label: '视频' },
  { value: 'document', label: '文档' },
  { value: 'image', label: '图片' },
  { value: 'mixed', label: '混合' },
]

function setFileType(value: string | undefined) {
  filters.file_type = value
  void fetchCourses()
}

const completedCount = computed(() => courses.value.filter((course) => course.learning_status === 'completed').length)
const inProgressCount = computed(() => courses.value.filter((course) => course.learning_status === 'in_progress').length)

onMounted(async () => {
  await Promise.all([fetchCourses(), loadInstructors()])
})

async function fetchCourses() {
  loading.value = true
  try {
    const response = await listCourses({
      page: 1,
      size: -1,
      search: filters.search || undefined,
      sort: filters.sort || undefined,
      instructor_id: filters.instructor_id,
      is_required: filters.is_required,
      learning_status: filters.learning_status,
      file_type: filters.file_type,
      created_from: filters.created_from,
      created_to: filters.created_to,
    })
    courses.value = [...(response.items || [])]
  } catch (error) {
    message.error(error instanceof Error ? error.message : '课程列表加载失败')
  } finally {
    loading.value = false
  }
}

async function loadInstructors() {
  try {
    const response = await listUsers({ page: 1, size: -1, role: 'instructor' })
    instructorOptions.value = (response.items || []).map((item) => ({
      value: item.id,
      label: getUserDisplayName(item, '教官'),
    }))
  } catch {
    instructorOptions.value = []
  }
}

function handleDateRangeChange(value: Dayjs[] | null) {
  if (value?.length === 2) {
    filters.created_from = value[0].startOf('day').toISOString()
    filters.created_to = value[1].endOf('day').toISOString()
  } else {
    filters.created_from = undefined
    filters.created_to = undefined
  }
  void fetchCourses()
}

function toggleAdvancedFilters() {
  advancedFiltersVisible.value = !advancedFiltersVisible.value
}

function getCourseCoverVisual(category?: string | null) {
  return courseCoverVisualMap[category || ''] || defaultCourseCoverVisual
}

function getCourseCoverBackground(course: CourseListResponse, index: number) {
  if (course.cover_color) {
    return course.cover_color
  }
  const visual = courseCoverVisualMap[course.category || '']
  return visual?.background || fallbackCoverBackgrounds[index % fallbackCoverBackgrounds.length]
}

function openCreate() {
  if (!canCreateCourse.value) {
    message.warning('您没有创建课程权限')
    return
  }
  editingCourseId.value = null
  editorVisible.value = true
}

function openEdit(courseId: number) {
  const target = courses.value.find((item) => item.id === courseId)
  if (!target?.can_manage_course) {
    message.warning('您没有编辑该课程的权限')
    return
  }
  editingCourseId.value = courseId
  editorVisible.value = true
}

async function handleDelete(courseId: number) {
  const target = courses.value.find((item) => item.id === courseId)
  if (!target?.can_manage_course) {
    message.warning('您没有删除该课程的权限')
    return
  }
  try {
    await deleteCourse(courseId)
    message.success('课程已删除')
    await fetchCourses()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '删除失败')
  }
}
</script>

<style scoped>
/* ── dark advanced toggle ── */
.dark-advanced-toggle {
  display: inline-flex; align-items: center; gap: 8px;
  min-height: 36px; padding: 0 14px;
  border: 1px solid rgba(255,255,255,0.16); border-radius: 999px;
  background: transparent; color: rgba(255,255,255,0.72);
  font-size: 14px; font-weight: 600; cursor: pointer;
  transition: background 0.2s, color 0.2s, border-color 0.2s;
}
.dark-advanced-toggle:hover { color: #fff; border-color: rgba(255,255,255,0.24); }
.dark-advanced-toggle.expanded { background: rgba(255,255,255,0.08); color: #fff; }
.toggle-label { display: inline; }
.toggle-arrow { font-size: 11px; }

/* ── dark advanced panel ── */
.dark-adv-row { display: flex; flex-wrap: wrap; gap: 10px; padding: 2px 0 0; }
.dark-adv-select { width: 160px; }
.dark-adv-date { width: auto; }

.dark-adv-row :deep(.ant-select:not(.ant-select-customize-input) .ant-select-selector) {
  background: rgba(255,255,255,0.08) !important; border-color: rgba(255,255,255,0.16) !important;
  color: rgba(255,255,255,0.88) !important; border-radius: 20px !important;
}
.dark-adv-row :deep(.ant-select-arrow),
.dark-adv-row :deep(.ant-select-clear) { color: rgba(255,255,255,0.5) !important; background: transparent !important; }
.dark-adv-row :deep(.ant-select-selection-placeholder) { color: rgba(255,255,255,0.44) !important; }
.dark-adv-row :deep(.ant-picker) {
  background: rgba(255,255,255,0.08) !important; border-color: rgba(255,255,255,0.16) !important;
  border-radius: 20px !important; color: rgba(255,255,255,0.88) !important;
}
.dark-adv-row :deep(.ant-picker input) { color: rgba(255,255,255,0.88) !important; }
.dark-adv-row :deep(.ant-picker-suffix),
.dark-adv-row :deep(.ant-picker-separator),
.dark-adv-row :deep(.ant-picker-clear) { color: rgba(255,255,255,0.44) !important; background: transparent !important; }

.advanced-filters-enter-active,
.advanced-filters-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.advanced-filters-enter-from,
.advanced-filters-leave-to { opacity: 0; transform: translateY(-6px); }

.course-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
  color: var(--v2-text-secondary);
}

.loading-wrapper,
.empty-block {
  padding: 80px 0;
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.course-card {
  overflow: hidden;
  background: var(--v2-bg-card);
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(24, 39, 75, 0.08);
  cursor: pointer;
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 24px 48px rgba(75, 110, 245, 0.12);
}

.card-cover {
  position: relative;
  height: 178px;
  padding: 18px;
  overflow: hidden;
}

.card-cover::before {
  content: '';
  position: absolute;
  right: -34px;
  bottom: -70px;
  width: 210px;
  height: 210px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  filter: blur(8px);
}

.cover-labels {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.cover-tag-stack {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

:deep(.cover-tag.ant-tag) {
  margin: 0;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.35;
  border: 1px solid rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

:deep(.cover-tag-category.ant-tag) {
  color: #405f7f;
}

:deep(.cover-tag-type.ant-tag) {
  color: #7867c6;
}

:deep(.cover-tag-required.ant-tag) {
  color: #cc2f39;
  border-color: rgba(255, 142, 151, 0.48);
  background: rgba(255, 247, 247, 0.96);
}

.cover-visual {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-visual-ring {
  position: relative;
  width: 82px;
  height: 82px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.78);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.7));
  box-shadow:
    0 16px 28px var(--cover-visual-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
}

.cover-visual-icon {
  position: relative;
  z-index: 1;
  font-size: 34px;
  color: var(--cover-visual-accent);
}

.cover-footer {
  position: absolute;
  left: 12px;
  right: 22px;
  bottom: 10px;
  z-index: 2;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.learning-pill,
.cover-footer-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  padding: 0 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.learning-pill {
  color: #fff;
  background: linear-gradient(135deg, #2457f5 0%, #1742c8 100%);
  box-shadow: 0 12px 24px rgba(29, 78, 216, 0.24);
}

.cover-footer-item {
  color: rgba(18, 25, 38, 0.78);
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.72);
}

.card-body {
  padding: 22px 22px 24px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 16px;
}

.card-head-main {
  flex: 1;
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.card-title-row h3 {
  margin: 0;
  font-size: 21px;
  line-height: 1.35;
  color: var(--v2-text-primary);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.08);
  font-size: 12px;
  font-weight: 700;
}

.card-head p {
  margin: 0;
  min-height: 50px;
  color: var(--v2-text-secondary);
  font-size: 14px;
  line-height: 1.8;
}

.card-actions {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
  margin-bottom: 16px;
  color: var(--v2-text-secondary);
  font-size: 14px;
}

.progress-panel {
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(238, 242, 255, 0.95), rgba(245, 247, 255, 0.95));
}

.progress-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  color: var(--v2-text-secondary);
  font-size: 13px;
  font-weight: 600;
}

.progress-panel :deep(.ant-progress-bg),
.progress-panel :deep(.ant-progress-inner) {
  height: 8px !important;
  border-radius: 999px;
}

@media (max-width: 768px) {
  .card-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .dark-adv-row { flex-direction: column; }
  .dark-adv-select, .dark-adv-date { width: 100%; }
  .toggle-label { display: none; }

  .meta-grid,
  .course-grid {
    grid-template-columns: 1fr;
  }

  .card-cover {
    height: 164px;
  }

  .cover-labels {
    flex-direction: column;
  }

  .cover-tag-stack {
    justify-content: flex-start;
  }
}
</style>
