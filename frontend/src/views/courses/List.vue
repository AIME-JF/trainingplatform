<template>
  <div class="course-list-page">
    <div class="page-header">
      <h2>课程</h2>
      <a-button v-if="canCreateCourse" type="primary" @click="openCreate">
        <template #icon><PlusOutlined /></template>创建课程
      </a-button>
    </div>

    <CourseEditorModal
      v-model:open="editorVisible"
      :course-id="editingCourseId"
      @success="handleEditorSuccess"
    />

    <a-card class="filter-card" :bordered="false">
      <a-row :gutter="[16, 16]" align="middle">
        <a-col :xxl="7" :xl="7" :lg="8" :md="12" :sm="24" :xs="24">
          <a-input-search v-model:value="searchText" placeholder="搜索课程名称、关键词..." allow-clear />
        </a-col>
        <a-col :xxl="5" :xl="5" :lg="6" :md="12" :sm="24" :xs="24">
          <a-select
            v-model:value="selectedInstructorId"
            :options="instructorOptions"
            allow-clear
            placeholder="按教官筛选"
            style="width: 100%"
          />
        </a-col>
        <a-col :xxl="10" :xl="10" :lg="8" :md="18" :sm="24" :xs="24">
          <div class="category-tabs">
            <a-tag
              v-for="cat in allCategories"
              :key="cat.key"
              :color="selectedCategory === cat.key ? 'blue' : 'default'"
              class="cat-tag"
              @click="selectedCategory = cat.key"
            >
              {{ cat.label }}
            </a-tag>
          </div>
        </a-col>
        <a-col :xxl="2" :xl="2" :lg="2" :md="6" :sm="24" :xs="24" class="sort-col">
          <a-select v-model:value="sortBy" size="small" style="width: 100%">
            <a-select-option value="default">默认排序</a-select-option>
            <a-select-option value="rating">按评分</a-select-option>
            <a-select-option value="students">按学员数</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <div class="course-stats">
      共 <strong>{{ filteredCourses.length }}</strong> 门课程
      <span v-if="authStore.isStudent" class="stats-progress">
        已学 <strong class="gold-text">{{ completedCount }}</strong> 门 ·
        进行中 <strong class="blue-text">{{ inProgressCount }}</strong> 门
      </span>
    </div>

    <div class="course-grid">
      <div v-for="course in filteredCourses" :key="course.id" class="course-card" @click="goDetail(course)">
        <div class="course-card-head">
          <div class="course-badges">
            <a-tag color="blue">{{ getCategoryLabel(course.category) }}</a-tag>
            <a-tag :color="getCourseTypeTagColor(course.fileType, course.chapterCount)">
              {{ getCourseTypeTagLabel(course.fileType, course.chapterCount) }}
            </a-tag>
            <a-tag v-if="course.isRequired" color="red">必修</a-tag>
          </div>
          <div v-if="canManageCourse" class="course-actions" @click.stop>
            <a-button size="small" type="text" @click="openEdit(course)">
              <template #icon><EditOutlined /></template>编辑
            </a-button>
            <a-popconfirm
              title="确定删除此课程吗？删除后不可恢复。"
              ok-text="确认删除"
              cancel-text="取消"
              @confirm="handleDelete(course)"
            >
              <a-button size="small" danger type="text">
                <template #icon><DeleteOutlined /></template>删除
              </a-button>
            </a-popconfirm>
          </div>
        </div>

        <div class="course-title">{{ course.title }}</div>
        <div class="course-description">{{ course.description || '暂无课程简介' }}</div>

        <div class="course-tags">
          <a-tag v-for="tag in (course.tags || []).slice(0, 4)" :key="tag">{{ tag }}</a-tag>
        </div>

        <div class="course-instructor">
          <div class="instructor-main">
            <a-avatar size="small" :style="{ background: '#003087', fontSize: '10px' }">
              {{ getInstructorName(course).charAt(0) || '?' }}
            </a-avatar>
            <span class="instructor-name">{{ getInstructorName(course) || '未设置主讲教官' }}</span>
          </div>
          <span class="difficulty">
            <span v-for="i in 5" :key="i" :class="i <= (course.difficulty || 0) ? 'star-filled' : 'star-empty'">★</span>
          </span>
        </div>

        <div class="course-meta">
          <span>章节 {{ course.chapterCount || 0 }}</span>
          <span>创建于 {{ formatDate(course.createdAt) }}</span>
        </div>

        <div class="course-footer">
          <span class="rating"><StarFilled style="color: #faad14" /> {{ course.rating || '新课' }}</span>
        </div>
      </div>
    </div>

    <a-empty v-if="!filteredCourses.length" description="暂无符合条件的课程" style="margin-top: 80px" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { DeleteOutlined, EditOutlined, PlusOutlined, StarFilled } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { deleteCourse as apiDeleteCourse, getCourses } from '@/api/course'
import { getUsers } from '@/api/user'
import { useAuthStore } from '@/stores/auth'
import CourseEditorModal from './components/CourseEditorModal.vue'

const COURSE_CATEGORIES = [
  { key: 'all', label: '全部课程' },
  { key: 'law', label: '法律法规' },
  { key: 'fraud', label: '专项业务' },
  { key: 'traffic', label: '交通管理' },
  { key: 'community', label: '基层警务' },
  { key: 'cybersec', label: '科技应用' },
  { key: 'physical', label: '体能技能' },
]

const router = useRouter()
const authStore = useAuthStore()

const courseList = ref([])
const searchText = ref('')
const selectedCategory = ref('all')
const selectedInstructorId = ref(undefined)
const sortBy = ref('default')
const editorVisible = ref(false)
const editingCourseId = ref(null)
const instructorOptions = ref([])

const allCategories = COURSE_CATEGORIES.map((item) => (
  item.key === 'all' ? { key: 'all', label: '全部' } : item
))
const canCreateCourse = computed(() => authStore.hasPermission('CREATE_COURSE'))
const canManageCourse = computed(() => authStore.isAdmin)

async function fetchCourses() {
  try {
    const response = await getCourses({
      size: -1,
      search: searchText.value?.trim() || undefined,
      category: selectedCategory.value !== 'all' ? selectedCategory.value : undefined,
      sort: sortBy.value === 'default' ? undefined : sortBy.value,
      instructorId: selectedInstructorId.value || undefined,
    })
    const items = response.items || response || []
    courseList.value = items
  } catch (error) {
    message.error(error?.message || '课程列表加载失败')
  }
}

async function fetchInstructors() {
  try {
    const response = await getUsers({ role: 'instructor', size: -1 })
    const items = response.items || response || []
    instructorOptions.value = items.map((item) => ({
      value: item.id,
      label: item.nickname || item.username || `教官#${item.id}`,
    }))
  } catch {
    instructorOptions.value = []
  }
}

onMounted(() => {
  fetchCourses()
  fetchInstructors()
})

watch([searchText, selectedCategory, sortBy, selectedInstructorId], () => {
  fetchCourses()
})

const filteredCourses = computed(() => {
  const list = [...courseList.value]
  if (sortBy.value === 'rating') {
    return list.sort((a, b) => Number(b.rating || 0) - Number(a.rating || 0))
  }
  if (sortBy.value === 'students') {
    return list.sort((a, b) => Number(b.studentCount || 0) - Number(a.studentCount || 0))
  }
  return list.sort((a, b) => new Date(b.createdAt || 0) - new Date(a.createdAt || 0))
})

const completedCount = computed(() => courseList.value.filter((course) => getCourseProgress(course) >= 100).length)
const inProgressCount = computed(() => courseList.value.filter((course) => {
  const progress = getCourseProgress(course)
  return progress > 0 && progress < 100
}).length)

function openCreate() {
  if (!canCreateCourse.value) {
    message.warning('当前账号无权创建课程')
    return
  }
  editingCourseId.value = null
  editorVisible.value = true
}

function openEdit(course) {
  if (!canManageCourse.value) {
    message.warning('仅系统管理员可编辑课程')
    return
  }
  editingCourseId.value = course.id
  editorVisible.value = true
}

async function handleDelete(course) {
  if (!canManageCourse.value) {
    message.warning('仅系统管理员可删除课程')
    return
  }
  try {
    await apiDeleteCourse(course.id)
    message.success(`课程《${course.title}》已删除`)
    fetchCourses()
  } catch (error) {
    message.error(error?.message || '删除失败')
  }
}

function handleEditorSuccess() {
  fetchCourses()
}

function getInstructorName(course) {
  return course.instructorName || course.instructor || ''
}

function getCourseProgress(course) {
  return Math.max(0, Math.min(100, Number(course.progressPercent || 0)))
}

function getCategoryLabel(category) {
  return COURSE_CATEGORIES.find((item) => item.key === category)?.label ?? category
}

function formatDate(value) {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '-'
  }
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function getCourseTypeTagLabel(fileType, chapterCount) {
  if (Number(chapterCount || 0) <= 0 || fileType === 'pending') {
    return '未配置'
  }
  if (fileType === 'video') {
    return '视频型'
  }
  if (fileType === 'audio') {
    return '音频型'
  }
  if (fileType === 'image') {
    return '图片型'
  }
  if (fileType === 'knowledge') {
    return '知识点型'
  }
  if (fileType === 'mixed') {
    return '混合型'
  }
  return '文档型'
}

function getCourseTypeTagColor(fileType, chapterCount) {
  if (Number(chapterCount || 0) <= 0 || fileType === 'pending') {
    return 'default'
  }
  if (fileType === 'video') {
    return 'purple'
  }
  if (fileType === 'audio') {
    return 'magenta'
  }
  if (fileType === 'image') {
    return 'green'
  }
  if (fileType === 'knowledge') {
    return 'blue'
  }
  if (fileType === 'mixed') {
    return 'orange'
  }
  return 'cyan'
}

function goDetail(course) {
  router.push({ name: 'CourseDetail', params: { id: course.id } })
}
</script>

<style scoped>
.course-list-page { padding: 0; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; gap: 12px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.filter-card { margin-bottom: 16px; }
.category-tabs { display: flex; flex-wrap: wrap; gap: 6px; }
.cat-tag { cursor: pointer; font-size: 13px; padding: 2px 10px; border-radius: 12px; }
.sort-col { text-align: right; }
.course-stats { margin-bottom: 16px; color: #666; font-size: 13px; }
.stats-progress { margin-left: 16px; }
.gold-text { color: var(--police-gold); }
.blue-text { color: #1890ff; }
.course-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.course-card {
  background: #fff;
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.25s;
  border: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  min-height: 240px;
}
.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 48, 135, 0.12);
  border-color: var(--police-primary);
}
.course-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.course-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.course-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
.course-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.5;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.course-description {
  font-size: 13px;
  line-height: 1.7;
  color: #666;
  min-height: 44px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 12px;
}
.course-tags {
  margin-bottom: 12px;
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  min-height: 28px;
}
.course-instructor {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}
.instructor-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.instructor-name {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.star-filled { color: #faad14; }
.star-empty { color: #ddd; }
.course-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: #7a8699;
  margin-bottom: 12px;
}
.course-progress { margin-bottom: 12px; }
.progress-text { font-size: 11px; color: #888; }
.course-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #888;
  border-top: 1px solid #f0f0f0;
  padding-top: 10px;
  margin-top: auto;
}
.rating { font-weight: 600; color: #333; }

@media (max-width: 992px) {
  .course-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .course-grid { grid-template-columns: 1fr !important; }
  .filter-card :deep(.ant-card-body) { padding: 12px !important; }
  .page-header { flex-wrap: wrap; }
  .page-header h2 { font-size: 18px !important; }
  .sort-col { text-align: left; }
  .course-card-head,
  .course-instructor,
  .course-meta,
  .course-footer {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
