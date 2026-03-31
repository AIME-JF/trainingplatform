<template>
  <div class="page-content resource-page">
    <LearningResourceTabs />

    <div class="page-header">
      <div>
        <h1 class="page-title">课程资源</h1>
        <p class="page-subtitle">围绕课程章节组织学习内容，适合系统化学习。</p>
      </div>
      <a-button v-if="authStore.isInstructor" type="primary" @click="openCreate">创建课程</a-button>
    </div>

    <CourseEditorModal v-model:open="editorVisible" :course-id="editingCourseId" @success="fetchCourses" />

    <a-card :bordered="false" class="filter-card">
      <a-row :gutter="[12, 12]">
        <a-col :xs="24" :xl="8">
          <ResourceSearchInput v-model:value="filters.search" placeholder="搜索课程名称、关键词..." @search="fetchCourses" />
        </a-col>
        <a-col :xs="24" :md="8" :xl="5">
          <a-select v-model:value="filters.instructor_id" :options="instructorOptions" allow-clear placeholder="按教官筛选" style="width: 100%" @change="fetchCourses" />
        </a-col>
        <a-col :xs="24" :xl="8">
          <div class="category-tabs">
            <a-tag
              v-for="cat in categoryTabs"
              :key="cat.key"
              class="cat-tag"
              :class="{ active: filters.category === cat.key }"
              @click="selectCategory(cat.key)"
            >
              {{ cat.label }}
            </a-tag>
          </div>
        </a-col>
        <a-col :xs="24" :md="8" :xl="3">
          <a-select v-model:value="filters.sort" style="width: 100%" @change="fetchCourses">
            <a-select-option value="default">默认排序</a-select-option>
            <a-select-option value="rating">按评分</a-select-option>
            <a-select-option value="students">按学员数</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <div class="course-stats">
      共 <strong>{{ courses.length }}</strong> 门课程
      <span v-if="authStore.isStudent">已学 <strong>{{ completedCount }}</strong> 门，进行中 <strong>{{ inProgressCount }}</strong> 门</span>
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
              <a-tag class="cover-tag cover-tag-type">{{ getCourseFileTypeLabel(course.file_type) }}</a-tag>
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
        </div>
        <div class="card-body">
          <div class="card-head">
            <div>
              <h3>{{ course.title }}</h3>
              <p>{{ course.description || '暂无课程简介' }}</p>
            </div>
            <div v-if="authStore.isInstructor" class="card-actions" @click.stop>
              <a-button size="small" type="text" @click="openEdit(course.id)">编辑</a-button>
              <a-popconfirm title="确定删除此课程吗？" @confirm="handleDelete(course.id)">
                <a-button size="small" type="text" danger>删除</a-button>
              </a-popconfirm>
            </div>
          </div>
          <div class="card-meta">
            <span>主讲教官：{{ course.instructor_name || '未设置' }}</span>
            <span>章节 {{ course.chapter_count || 0 }}</span>
          </div>
          <div class="card-meta">
            <span>创建于 {{ formatDate(course.created_at) }}</span>
            <span>评分 {{ course.rating || '新课' }}</span>
          </div>
          <a-progress v-if="authStore.isStudent" :percent="course.progress_percent || 0" size="small" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { AppstoreOutlined, CarOutlined, LaptopOutlined, ReadOutlined, SafetyCertificateOutlined, TeamOutlined, ThunderboltOutlined } from '@ant-design/icons-vue'
import { computed, onMounted, reactive, ref, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { CourseListResponse } from '@/api/learning-resource'
import { deleteCourse, listCourses, listUsers } from '@/api/learning-resource'
import { useAuthStore } from '@/stores/auth'
import CourseEditorModal from '@/components/resource/CourseEditorModal.vue'
import LearningResourceTabs from '@/components/resource/LearningResourceTabs.vue'
import ResourceSearchInput from '@/components/resource/ResourceSearchInput.vue'
import {
  COURSE_CATEGORIES,
  formatDate,
  getCourseCategoryLabel,
  getCourseFileTypeLabel,
  getUserDisplayName,
} from '@/utils/learning-resource'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const courses = ref<CourseListResponse[]>([])
const instructorOptions = ref<Array<{ value: number; label: string }>>([])
const editorVisible = ref(false)
const editingCourseId = ref<number | null>(null)

const filters = reactive({
  search: '',
  category: 'all',
  instructor_id: undefined as number | undefined,
  sort: 'default',
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

const categoryTabs = COURSE_CATEGORIES.map((item) => (
  item.key === 'all' ? { key: 'all', label: '全部' } : item
))

const completedCount = computed(() => courses.value.filter((course) => (course.progress_percent || 0) >= 100).length)
const inProgressCount = computed(() => courses.value.filter((course) => {
  const progress = course.progress_percent || 0
  return progress > 0 && progress < 100
}).length)

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
      category: filters.category !== 'all' ? filters.category : undefined,
      sort: filters.sort !== 'default' ? filters.sort : undefined,
      instructor_id: filters.instructor_id,
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

function selectCategory(category: string) {
  filters.category = category
  void fetchCourses()
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
  editingCourseId.value = null
  editorVisible.value = true
}

function openEdit(courseId: number) {
  editingCourseId.value = courseId
  editorVisible.value = true
}

async function handleDelete(courseId: number) {
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
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 6px;
}

.page-subtitle {
  color: var(--v2-text-secondary);
}

.filter-card {
  margin-bottom: 20px;
}

.filter-card :deep(.ant-row) {
  align-items: center;
}

.filter-card :deep(.ant-col) {
  display: flex;
  align-items: center;
}

.filter-card :deep(.ant-col > *) {
  width: 100%;
}

.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  min-height: var(--resource-control-height);
}

:deep(.cat-tag.ant-tag) {
  cursor: pointer;
  margin: 0;
  padding: 7px 14px;
  font-size: 14px;
  font-weight: 600;
  color: var(--v2-text-secondary);
  border: 1px solid rgba(75, 110, 245, 0.12);
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 8px 20px rgba(75, 110, 245, 0.06);
  transition:
    color 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease,
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

:deep(.cat-tag.ant-tag:hover),
:deep(.cat-tag.active.ant-tag) {
  color: var(--v2-primary);
  border-color: rgba(75, 110, 245, 0.3);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(237, 242, 255, 0.94));
  box-shadow: 0 12px 24px rgba(75, 110, 245, 0.12);
  transform: translateY(-1px);
}

.course-stats {
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
  position: relative;
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
  box-shadow: 0 22px 46px rgba(75, 110, 245, 0.1);
}

.card-cover {
  position: relative;
  height: 164px;
  padding: 18px;
  overflow: hidden;
}

.card-cover::before {
  content: '';
  position: absolute;
  right: -30px;
  bottom: -64px;
  width: 188px;
  height: 188px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  filter: blur(6px);
}

.card-cover::after {
  content: '';
  position: absolute;
  left: 18px;
  right: 18px;
  bottom: 0;
  height: 1px;
  background: rgba(255, 255, 255, 0.2);
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
  left: 50%;
  top: 55%;
  transform: translate(-50%, -50%);
  z-index: 1;
}

.cover-visual-ring {
  position: relative;
  width: 76px;
  height: 76px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.78);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.68));
  box-shadow:
    0 16px 28px var(--cover-visual-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
}

.cover-visual-ring::after {
  content: '';
  position: absolute;
  inset: 9px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0));
}

.cover-visual-icon {
  position: relative;
  z-index: 1;
  font-size: 32px;
  color: var(--cover-visual-accent);
}

.card-body {
  padding: 22px 22px 24px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.card-head h3 {
  font-size: 22px;
  line-height: 1.28;
  margin-bottom: 10px;
}

.card-head p {
  color: var(--v2-text-secondary);
  font-size: 15px;
  line-height: 1.8;
  min-height: 54px;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--v2-text-secondary);
  font-size: 14px;
  margin-bottom: 12px;
}

.card-actions {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.card-body :deep(.ant-progress) {
  margin-top: 8px;
}

.card-body :deep(.ant-progress-bg),
.card-body :deep(.ant-progress-inner) {
  height: 8px !important;
  border-radius: 999px;
}

@media (max-width: 768px) {
  .page-header,
  .card-head,
  .card-meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .course-grid {
    grid-template-columns: 1fr;
  }

  .card-cover {
    height: 152px;
  }

  .cover-labels {
    flex-direction: column;
  }

  .cover-tag-stack {
    justify-content: flex-start;
  }
}
</style>
