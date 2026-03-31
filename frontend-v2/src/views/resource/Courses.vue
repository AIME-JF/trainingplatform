<template>
  <div class="page-content">
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
          <a-input-search v-model:value="filters.search" placeholder="搜索课程名称、关键词..." @search="fetchCourses" />
        </a-col>
        <a-col :xs="24" :md="8" :xl="5">
          <a-select v-model:value="filters.instructor_id" :options="instructorOptions" allow-clear placeholder="按教官筛选" style="width: 100%" @change="fetchCourses" />
        </a-col>
        <a-col :xs="24" :xl="8">
          <div class="category-tabs">
            <a-tag
              v-for="cat in categoryTabs"
              :key="cat.key"
              :color="filters.category === cat.key ? 'blue' : 'default'"
              class="cat-tag"
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
        <div class="card-cover" :style="{ background: coverColors[index % coverColors.length] }">
          <div class="cover-labels">
            <a-tag>{{ getCourseCategoryLabel(course.category) }}</a-tag>
            <a-tag :color="getCourseFileTypeColor(course.file_type)">{{ getCourseFileTypeLabel(course.file_type) }}</a-tag>
            <a-tag v-if="course.is_required" color="red">必修</a-tag>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { CourseListResponse } from '@/api/learning-resource'
import { deleteCourse, listCourses, listUsers } from '@/api/learning-resource'
import { useAuthStore } from '@/stores/auth'
import CourseEditorModal from '@/components/resource/CourseEditorModal.vue'
import LearningResourceTabs from '@/components/resource/LearningResourceTabs.vue'
import {
  COURSE_CATEGORIES,
  formatDate,
  getCourseCategoryLabel,
  getCourseFileTypeColor,
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

const coverColors = [
  'var(--v2-cover-blue)',
  'var(--v2-cover-green)',
  'var(--v2-cover-purple)',
  'var(--v2-cover-orange)',
  'var(--v2-cover-teal)',
  'var(--v2-cover-pink)',
  'var(--v2-cover-yellow)',
  'var(--v2-cover-rose)',
]

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
  margin-bottom: 20px;
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
  margin-bottom: 16px;
}

.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.cat-tag {
  cursor: pointer;
}

.course-stats {
  margin-bottom: 16px;
  color: var(--v2-text-secondary);
}

.loading-wrapper,
.empty-block {
  padding: 80px 0;
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.course-card {
  overflow: hidden;
  background: var(--v2-bg-card);
  border-radius: var(--v2-radius-lg);
  box-shadow: var(--v2-shadow-sm);
  cursor: pointer;
}

.card-cover {
  height: 120px;
  padding: 14px;
}

.cover-labels {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.card-body {
  padding: 18px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.card-head h3 {
  font-size: 18px;
  margin-bottom: 8px;
}

.card-head p {
  color: var(--v2-text-secondary);
  line-height: 1.7;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--v2-text-secondary);
  font-size: 13px;
  margin-bottom: 10px;
}

@media (max-width: 768px) {
  .page-header,
  .card-head,
  .card-meta {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
