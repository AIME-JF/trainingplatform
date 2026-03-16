<template>
  <div class="course-list-page">
    <div class="page-header">
      <h2>课程中心</h2>
      <a-button v-if="authStore.isInstructor || authStore.isAdmin" type="primary" @click="openCreate">
        <template #icon><PlusOutlined /></template>上传课程
      </a-button>
    </div>

    <CourseEditorModal
      v-model:open="editorVisible"
      :course-id="editingCourseId"
      @success="handleEditorSuccess"
    />

    <a-card class="filter-card" :bordered="false">
      <a-row :gutter="16" align="middle">
        <a-col :span="8">
          <a-input-search v-model:value="searchText" placeholder="搜索课程名称、关键词..." allow-clear />
        </a-col>
        <a-col :span="14">
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
        <a-col :span="2" style="text-align: right">
          <a-select v-model:value="sortBy" size="small" style="width: 100px">
            <a-select-option value="default">默认排序</a-select-option>
            <a-select-option value="rating">按评分</a-select-option>
            <a-select-option value="students">按学员数</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <div class="course-stats">
      共 <strong>{{ filteredCourses.length }}</strong> 门课程
      <span v-if="authStore.isStudent" style="margin-left: 16px">
        已学 <strong style="color: var(--police-gold)">{{ completedCount }}</strong> 门 ·
        进行中 <strong style="color: #1890ff">{{ inProgressCount }}</strong> 门
      </span>
    </div>

    <div class="course-grid">
      <div v-for="course in filteredCourses" :key="course.id" class="course-card" @click="goDetail(course)">
        <div class="course-cover" :style="{ background: course.coverColor }">
          <div class="cover-icon">{{ getCoverIcon(course.category) }}</div>
          <div class="cover-type-badge">
            <a-tag :color="course.fileType === 'video' ? 'purple' : 'cyan'" style="font-size: 10px; margin: 0">
              {{ course.fileType === 'video' ? '🎬 视频' : '📄 文档' }}
            </a-tag>
          </div>
          <div v-if="course.isRequired" class="cover-badge">
            <a-tag color="red" style="font-size: 11px">必修</a-tag>
          </div>
          <div class="cover-duration">{{ formatDuration(course.duration) }}</div>

          <div
            v-if="authStore.isAdmin || authStore.isInstructor"
            class="cover-edit-btn"
            @click.stop="openEdit(course)"
          >
            <EditOutlined /> 编辑
          </div>
          <a-popconfirm
            v-if="authStore.isAdmin || authStore.isInstructor"
            title="确定删除此课程吗？删除后不可恢复。"
            ok-text="确认删除"
            cancel-text="取消"
            @confirm="handleDelete(course)"
          >
            <div class="cover-delete-btn" @click.stop>
              <DeleteOutlined /> 删除
            </div>
          </a-popconfirm>
        </div>

        <div class="course-body">
          <div class="course-category">{{ getCategoryLabel(course.category) }}</div>
          <div class="course-title">{{ course.title }}</div>
          <div class="course-tags">
            <a-tag v-for="tag in (course.tags || []).slice(0, 3)" :key="tag">{{ tag }}</a-tag>
          </div>
          <div class="course-instructor">
            <a-avatar size="small" :style="{ background: '#003087', fontSize: '10px' }">
              {{ getInstructorName(course).charAt(0) || '?' }}
            </a-avatar>
            <span class="instructor-name">{{ getInstructorName(course) || '未设置主讲教官' }}</span>
            <span class="difficulty">
              <span v-for="i in 5" :key="i" :class="i <= (course.difficulty || 0) ? 'star-filled' : 'star-empty'">★</span>
            </span>
          </div>
          <div v-if="authStore.isStudent" class="course-progress">
            <a-progress
              :percent="getCourseProgress(course)"
              :stroke-color="getCourseProgress(course) === 100 ? '#52c41a' : '#003087'"
              size="small"
              :show-info="false"
            />
            <span class="progress-text">{{ getCourseProgress(course) }}% 完成</span>
          </div>
          <div class="course-footer">
            <span><TeamOutlined /> {{ Number(course.studentCount || 0).toLocaleString() }} 人学过</span>
            <span class="rating"><StarFilled style="color: #faad14" /> {{ course.rating || '新课' }}</span>
          </div>
        </div>
      </div>
    </div>

    <a-empty v-if="!filteredCourses.length" description="暂无符合条件的课程" style="margin-top: 80px" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { DeleteOutlined, EditOutlined, PlusOutlined, StarFilled, TeamOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { deleteCourse as apiDeleteCourse, getCourses } from '@/api/course'
import { useAuthStore } from '@/stores/auth'
import { COURSE_CATEGORIES } from '@/mock/courses'
import CourseEditorModal from './components/CourseEditorModal.vue'

const router = useRouter()
const authStore = useAuthStore()

const courseList = ref([])
const loading = ref(false)
const searchText = ref('')
const selectedCategory = ref('all')
const sortBy = ref('default')
const editorVisible = ref(false)
const editingCourseId = ref(null)

const allCategories = COURSE_CATEGORIES.map((item) => (
  item.key === 'all' ? { key: 'all', label: '全部' } : item
))
const categoryColorMap = {
  law: '#003087',
  fraud: '#8B1A1A',
  traffic: '#0A6640',
  community: '#4A3728',
  cybersec: '#1A0A4A',
  physical: '#2D4A1A',
}
const coverIcons = {
  law: '⚖️',
  fraud: '🔍',
  traffic: '🚗',
  community: '🏘️',
  cybersec: '💻',
  physical: '💪',
}

async function fetchCourses() {
  loading.value = true
  try {
    const response = await getCourses({
      size: -1,
      search: searchText.value?.trim() || undefined,
      category: selectedCategory.value !== 'all' ? selectedCategory.value : undefined,
      sort: sortBy.value === 'default' ? undefined : sortBy.value,
    })
    const items = response.items || response || []
    courseList.value = items.map((course) => ({
      ...course,
      coverColor: course.coverColor || categoryColorMap[course.category] || '#003087',
    }))
  } catch (error) {
    message.error(error?.message || '课程列表加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchCourses)

watch([searchText, selectedCategory, sortBy], () => {
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
  editingCourseId.value = null
  editorVisible.value = true
}

function openEdit(course) {
  editingCourseId.value = course.id
  editorVisible.value = true
}

async function handleDelete(course) {
  try {
    await apiDeleteCourse(course.id)
    message.success(`课程『${course.title}』已删除`)
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

function formatDuration(minutes) {
  const value = Number(minutes || 0)
  if (value >= 60) {
    return `${Math.floor(value / 60)}h${value % 60 > 0 ? `${value % 60}min` : ''}`
  }
  return `${value}min`
}

function getCoverIcon(category) {
  return coverIcons[category] ?? '📚'
}

function goDetail(course) {
  router.push({ name: 'CourseDetail', params: { id: course.id } })
}
</script>

<style scoped>
.course-list-page { padding: 0; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.filter-card { margin-bottom: 16px; }
.category-tabs { display: flex; flex-wrap: wrap; gap: 6px; }
.cat-tag { cursor: pointer; font-size: 13px; padding: 2px 10px; border-radius: 12px; }
.course-stats { margin-bottom: 16px; color: #666; font-size: 13px; }
.course-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.course-card { background: #fff; border-radius: 8px; overflow: hidden; cursor: pointer; transition: all 0.25s; border: 1px solid #e8e8e8; }
.course-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,48,135,0.12); border-color: var(--police-primary); }
.course-cover { height: 140px; position: relative; display: flex; align-items: center; justify-content: center; }
.cover-icon { font-size: 48px; }
.cover-badge { position: absolute; top: 10px; left: 10px; }
.cover-type-badge { position: absolute; top: 10px; right: 10px; }
.cover-duration { position: absolute; bottom: 8px; right: 10px; background: rgba(0,0,0,0.5); color: #fff; padding: 1px 8px; border-radius: 10px; font-size: 11px; }
.cover-edit-btn {
  position: absolute; bottom: 8px; left: 10px;
  background: rgba(0,48,135,0.85); color: #fff;
  padding: 2px 10px; border-radius: 10px; font-size: 11px;
  opacity: 0; transition: opacity 0.2s; cursor: pointer;
}
.course-card:hover .cover-edit-btn { opacity: 1; }
.cover-delete-btn {
  position: absolute; bottom: 8px; left: 80px;
  background: rgba(207,19,34,0.85); color: #fff;
  padding: 2px 10px; border-radius: 10px; font-size: 11px;
  opacity: 0; transition: opacity 0.2s; cursor: pointer;
}
.course-card:hover .cover-delete-btn { opacity: 1; }
.course-body { padding: 14px; }
.course-category { color: var(--police-primary); font-size: 11px; font-weight: 600; margin-bottom: 4px; }
.course-title { font-size: 15px; font-weight: 600; color: #1a1a1a; line-height: 1.4; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.course-tags { margin-bottom: 10px; display: flex; gap: 4px; flex-wrap: wrap; }
.course-instructor { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.instructor-name { font-size: 12px; color: #666; flex: 1; }
.star-filled { color: #faad14; }
.star-empty { color: #ddd; }
.course-progress { margin-bottom: 10px; }
.progress-text { font-size: 11px; color: #888; }
.course-footer { display: flex; justify-content: space-between; font-size: 12px; color: #888; border-top: 1px solid #f0f0f0; padding-top: 10px; }
.rating { font-weight: 600; color: #333; }

@media (max-width: 768px) {
  .course-grid { grid-template-columns: 1fr !important; }
  .filter-card :deep(.ant-card-body) { padding: 12px !important; }
  .page-header h2 { font-size: 18px !important; }
}
</style>
