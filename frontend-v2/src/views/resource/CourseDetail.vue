<template>
  <div class="detail-page resource-page">
    <header class="detail-header">
      <div class="header-main">
        <div class="header-actions">
          <a-button ghost @click="router.push('/resource/courses')">返回课程资源</a-button>
          <a-button v-if="authStore.isInstructor" ghost @click="editorVisible = true">编辑课程</a-button>
          <a-popconfirm v-if="authStore.isInstructor" title="确定删除此课程吗？" @confirm="handleDeleteCourse">
            <a-button ghost danger>删除课程</a-button>
          </a-popconfirm>
        </div>
        <h1 class="header-title">{{ course?.title || '课程详情' }}</h1>
        <div class="header-meta">
          <span class="meta-badge">{{ getCourseCategoryLabel(course?.category) }}</span>
          <span class="meta-badge">{{ getCourseFileTypeLabel(course?.file_type) }}</span>
          <span class="meta-item">主讲教官：{{ course?.instructor_name || '-' }}</span>
          <span class="meta-item">章节数：{{ course?.chapter_count || 0 }}</span>
        </div>
      </div>
    </header>

    <section class="page-content">
      <CourseEditorModal v-model:open="editorVisible" :course-id="course?.id || null" @success="fetchCourse" />

      <a-spin v-if="loading" size="large" class="loading-block" />
      <a-empty v-else-if="!course" description="课程不存在或无权限查看" class="loading-block" />

      <template v-else>
        <a-row :gutter="[16, 16]">
          <a-col :xs="24" :xl="16">
            <a-card :bordered="false" class="viewer-card">
              <template v-if="currentChapter?.content_type === 'video' && currentChapter.file_url">
                <video
                  :src="currentChapter.file_url"
                  class="course-video"
                  controls
                  preload="metadata"
                  @ended="markChapterCompleted"
                />
              </template>
              <template v-else-if="currentChapter?.content_type === 'image' && currentChapter.file_url">
                <div class="image-stage">
                  <img :src="currentChapter.file_url" :alt="currentChapter.title" class="course-image" />
                </div>
              </template>
              <template v-else-if="currentChapter?.file_url">
                <iframe :src="currentChapter.file_url" class="doc-frame" title="课程文档预览" />
              </template>
              <a-empty v-else description="当前章节暂无可预览内容" />
            </a-card>

            <a-card :bordered="false" class="section-card">
              <a-tabs v-model:activeKey="activeTab">
                <a-tab-pane key="intro" tab="课程简介">
                  <p class="course-description">{{ course.description || '暂无课程简介' }}</p>
                  <a-descriptions :column="{ xs: 1, md: 2 }" size="small">
                    <a-descriptions-item label="创建者">{{ course.created_by_name || '-' }}</a-descriptions-item>
                    <a-descriptions-item label="主讲教官">{{ course.instructor_name || '-' }}</a-descriptions-item>
                    <a-descriptions-item label="章节数量">{{ course.chapters?.length || 0 }} 章</a-descriptions-item>
                    <a-descriptions-item label="课程标签">{{ formatTagList(course.tags || null) }}</a-descriptions-item>
                  </a-descriptions>
                </a-tab-pane>

                <a-tab-pane v-if="course.can_view_learning_status" key="learning" tab="学习情况">
                  <a-table
                    :data-source="learningStatus"
                    :columns="learningColumns"
                    :loading="learningLoading"
                    row-key="user_id"
                    :pagination="{ pageSize: 10 }"
                    :scroll="{ x: 860 }"
                  >
                    <template #bodyCell="{ column, record }">
                      <template v-if="column.key === 'progress_percent'">
                        <div class="progress-cell">
                          <a-progress :percent="record.progress_percent || 0" size="small" />
                          <span>{{ record.completed_chapter_count || 0 }}/{{ record.chapter_count || 0 }} 章</span>
                        </div>
                      </template>
                      <template v-else-if="column.key === 'last_studied_at'">
                        {{ formatDateTime(record.last_studied_at) }}
                      </template>
                    </template>
                  </a-table>
                </a-tab-pane>

                <a-tab-pane v-if="authStore.isInstructor" key="resources" tab="关联资源">
                  <div class="resource-bind-toolbar">
                    <a-select
                      v-model:value="selectedResourceId"
                      show-search
                      allow-clear
                      :options="resourceOptions"
                      placeholder="选择资源后绑定到课程"
                      class="resource-select"
                    />
                    <a-button type="primary" @click="bindSelectedResource">绑定资源</a-button>
                    <a-button @click="fetchCourse">刷新</a-button>
                  </div>
                  <a-table :data-source="courseResources" :columns="resourceColumns" row-key="id" :pagination="false">
                    <template #bodyCell="{ column, record }">
                      <template v-if="column.key === 'tags'">
                        <a-space wrap>
                          <a-tag v-for="tag in record.tags || []" :key="tag">{{ tag }}</a-tag>
                        </a-space>
                      </template>
                      <template v-else-if="column.key === 'action'">
                        <a-popconfirm title="确认解绑该资源？" @confirm="removeResource(record.id)">
                          <a-button size="small" danger>解绑</a-button>
                        </a-popconfirm>
                      </template>
                    </template>
                  </a-table>
                </a-tab-pane>

                <a-tab-pane key="qa" tab="答疑区">
                  <div v-if="qaList.length" class="qa-list">
                    <div v-for="item in qaList" :key="item.id" class="qa-item">
                      <div class="qa-question">
                        <span class="qa-user">{{ item.user_name || '用户' }}</span>
                        <span>{{ item.question }}</span>
                      </div>
                      <div v-if="item.answer" class="qa-answer">
                        <a-tag color="gold">教官回复</a-tag>
                        {{ item.answer }}
                      </div>
                    </div>
                  </div>
                  <a-empty v-else description="暂无答疑内容" />
                  <a-input-search
                    v-model:value="qaInput"
                    placeholder="输入你的问题，按回车提交"
                    enter-button="提交"
                    :loading="qaSubmitting"
                    class="qa-input"
                    @search="handleQASubmit"
                  />
                </a-tab-pane>
              </a-tabs>
            </a-card>
          </a-col>

          <a-col :xs="24" :xl="8">
            <a-card title="课程章节" :bordered="false" class="section-card">
              <div class="chapter-list">
                <div
                  v-for="(chapter, index) in course.chapters || []"
                  :key="chapter.id || index"
                  class="chapter-item"
                  :class="{ active: currentChapterIndex === index }"
                  @click="selectChapter(index)"
                >
                  <div class="chapter-index">{{ index + 1 }}</div>
                  <div class="chapter-content">
                    <h4>{{ chapter.title }}</h4>
                    <p>{{ chapter.resource_title || '未绑定资源' }}</p>
                    <a-progress :percent="chapter.progress || 0" size="small" />
                  </div>
                </div>
              </div>

              <div v-if="authStore.isStudent && currentChapter" class="chapter-actions">
                <a-button type="primary" block @click="markChapterCompleted">标记本章已完成</a-button>
              </div>
            </a-card>
          </a-col>
        </a-row>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { CourseLearningStatusResponse, CourseQAResponse, CourseResponse, ResourceListItemResponse } from '@/api/learning-resource'
import {
  bindCourseResource,
  createCourseQuestion,
  deleteCourse,
  getCourseDetail,
  getCourseLearningStatus,
  listCourseQa,
  listResources,
  listCourseResources,
  unbindCourseResource,
  updateCourseChapterProgress,
} from '@/api/learning-resource'
import { useAuthStore } from '@/stores/auth'
import CourseEditorModal from '@/components/resource/CourseEditorModal.vue'
import {
  formatDateTime,
  formatTagList,
  getCourseCategoryLabel,
  getCourseFileTypeLabel,
} from '@/utils/learning-resource'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const learningLoading = ref(false)
const course = ref<CourseResponse | null>(null)
const learningStatus = ref<CourseLearningStatusResponse[]>([])
const qaList = ref<CourseQAResponse[]>([])
const qaInput = ref('')
const qaSubmitting = ref(false)
const currentChapterIndex = ref(0)
const activeTab = ref('intro')
const editorVisible = ref(false)
const selectedResourceId = ref<number | undefined>()
const resourceOptions = ref<Array<{ value: number; label: string }>>([])
const courseResources = ref<ResourceListItemResponse[]>([])

const learningColumns = [
  { title: '学员', dataIndex: 'user_name', key: 'user_name', width: 140 },
  { title: '部门', dataIndex: 'department_name', key: 'department_name', width: 180 },
  { title: '课程进度', dataIndex: 'progress_percent', key: 'progress_percent', width: 240 },
  { title: '最近章节', dataIndex: 'last_studied_chapter_title', key: 'last_studied_chapter_title' },
  { title: '最近学习时间', dataIndex: 'last_studied_at', key: 'last_studied_at', width: 180 },
]

const resourceColumns = [
  { title: '标题', dataIndex: 'title', key: 'title' },
  { title: '类型', dataIndex: 'content_type', key: 'content_type', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 120 },
  { title: '标签', dataIndex: 'tags', key: 'tags' },
  { title: '操作', key: 'action', width: 120 },
]

const currentChapter = computed(() => course.value?.chapters?.[currentChapterIndex.value] || null)

onMounted(() => {
  void Promise.all([fetchCourse(), loadBindResources()])
})

async function fetchCourse() {
  const courseId = Number(route.params.id)
  if (!courseId) {
    return
  }
  loading.value = true
  try {
    course.value = await getCourseDetail(courseId)
    qaList.value = await listCourseQa(courseId)
    courseResources.value = await listCourseResources(courseId)
    if (course.value.can_view_learning_status) {
      await fetchLearningStatus(courseId)
    }
    currentChapterIndex.value = 0
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载课程详情失败')
  } finally {
    loading.value = false
  }
}

async function fetchLearningStatus(courseId: number) {
  learningLoading.value = true
  try {
    learningStatus.value = await getCourseLearningStatus(courseId)
  } finally {
    learningLoading.value = false
  }
}

async function loadBindResources() {
  try {
    const response = await listResources({ page: 1, size: -1, my_only: true, status: 'published' })
    resourceOptions.value = (response.items || []).map((item) => ({
      value: item.id,
      label: item.title,
    }))
  } catch {
    resourceOptions.value = []
  }
}

function selectChapter(index: number) {
  currentChapterIndex.value = index
}

async function markChapterCompleted() {
  const courseId = course.value?.id
  const chapterId = currentChapter.value?.id
  if (!courseId || !chapterId) {
    return
  }
  try {
    await updateCourseChapterProgress(courseId, chapterId, { progress: 100 })
    message.success('本章进度已更新')
    await fetchCourse()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '更新学习进度失败')
  }
}

async function handleQASubmit() {
  const question = qaInput.value.trim()
  if (!question || !course.value?.id) {
    return
  }
  qaSubmitting.value = true
  try {
    const item = await createCourseQuestion(course.value.id, { question })
    qaList.value.unshift(item)
    qaInput.value = ''
    message.success('提问已提交')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '提问提交失败')
  } finally {
    qaSubmitting.value = false
  }
}

async function bindSelectedResource() {
  if (!course.value?.id || !selectedResourceId.value) {
    message.warning('请先选择资源')
    return
  }
  try {
    await bindCourseResource(course.value.id, {
      resource_id: selectedResourceId.value,
      usage_type: 'required',
      sort_order: courseResources.value.length,
    })
    selectedResourceId.value = undefined
    message.success('资源绑定成功')
    await fetchCourse()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '绑定失败')
  }
}

async function removeResource(resourceId: number) {
  if (!course.value?.id) {
    return
  }
  try {
    await unbindCourseResource(course.value.id, resourceId)
    message.success('资源已解绑')
    await fetchCourse()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '解绑失败')
  }
}

async function handleDeleteCourse() {
  if (!course.value?.id) {
    return
  }
  try {
    await deleteCourse(course.value.id)
    message.success('课程已删除')
    router.push('/resource/courses')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '删除失败')
  }
}
</script>

<style scoped>
.detail-header {
  background: var(--v2-bg-header);
  padding: 28px 32px;
}

.header-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.header-title {
  font-size: 28px;
  color: var(--v2-text-white);
  margin-bottom: 12px;
}

.header-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.meta-badge,
.meta-item {
  color: rgba(255, 255, 255, 0.86);
}

.meta-badge {
  padding: 4px 12px;
  border-radius: var(--v2-radius-full);
  background: rgba(255, 255, 255, 0.16);
}

.loading-block {
  display: block;
  padding: 80px 0;
  text-align: center;
}

.viewer-card,
.section-card {
  border-radius: var(--v2-radius-lg);
}

.viewer-card {
  overflow: hidden;
}

.course-video,
.course-image,
.doc-frame {
  width: 100%;
  min-height: 420px;
  max-height: 70vh;
  border: 0;
  display: block;
  background: #000;
}

.course-image {
  object-fit: contain;
}

.image-stage {
  background: #000;
}

.section-card {
  margin-top: 16px;
}

.course-description {
  color: var(--v2-text-secondary);
  line-height: 1.8;
  margin-bottom: 16px;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.resource-bind-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.resource-select {
  min-width: 260px;
}

.qa-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qa-item {
  padding: 14px;
  border: 1px solid var(--v2-border);
  border-radius: var(--v2-radius);
}

.qa-question {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.qa-user {
  color: var(--v2-primary);
  font-weight: 600;
}

.qa-answer {
  margin-top: 10px;
  color: var(--v2-text-secondary);
}

.qa-input {
  margin-top: 14px;
}

.chapter-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chapter-item {
  display: flex;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--v2-border);
  border-radius: var(--v2-radius);
  cursor: pointer;
}

.chapter-item.active {
  border-color: var(--v2-primary);
  background: var(--v2-primary-light);
}

.chapter-index {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--v2-primary);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

.chapter-content {
  flex: 1;
}

.chapter-content h4 {
  margin-bottom: 8px;
}

.chapter-content p {
  color: var(--v2-text-secondary);
  font-size: 13px;
  margin-bottom: 10px;
}

.chapter-actions {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .detail-header {
    padding: 22px 16px;
  }

  .header-actions,
  .resource-bind-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
