<template>
  <div class="detail-page resource-page">
    <header class="detail-header">
      <div class="header-main">
        <div class="header-actions">
          <a-button ghost @click="router.push('/resource/courses')">返回课程</a-button>
          <a-button v-if="canManageCourse" ghost @click="openEdit">编辑课程</a-button>
          <a-popconfirm v-if="canManageCourse" title="确定删除此课程吗？" @confirm="handleDeleteCourse">
            <a-button ghost danger>删除课程</a-button>
          </a-popconfirm>
        </div>

        <h1 class="header-title">{{ course?.title || '课程详情' }}</h1>

        <div class="header-meta">
          <span class="meta-badge">{{ getCourseCategoryLabel(course?.category) }}</span>
          <span class="meta-badge">{{ getCourseFileTypeLabel(course?.file_type, course?.chapter_count) }}</span>
          <span class="meta-badge">{{ formatCourseDuration(course?.duration_seconds, course?.duration) }}</span>
          <span
            v-if="authStore.isStudent && course"
            class="meta-badge meta-badge-status"
            :style="{ color: getCourseLearningStatusColor(course.learning_status) }"
          >
            {{ getCourseLearningStatusLabel(course.learning_status) }}
          </span>
          <span class="meta-item">主讲教官：{{ course?.instructor_name || '-' }}</span>
          <span class="meta-item">章节数：{{ course?.chapter_count || 0 }}</span>
        </div>
      </div>
    </header>

    <section class="page-content">
      <CourseEditorModal
        v-model:open="editorVisible"
        :course-id="course?.id || null"
        :can-manage="canManageCourse"
        @success="fetchCourse"
      />
      <LibraryItemPickerModal
        v-model:open="pickerVisible"
        :confirm-loading="pickerSubmitting"
        :bound-item-ids="boundLibraryItemIds"
        @confirm="handlePickerConfirm"
      />

      <a-spin v-if="loading" size="large" class="loading-block" />
      <a-empty v-else-if="!course" description="课程不存在或无权限查看" class="loading-block" />

      <template v-else>
        <a-row :gutter="[18, 18]">
          <a-col :xs="24" :xl="16">
            <a-card :bordered="false" class="viewer-card">
              <div class="viewer-head">
                <div>
                  <h2>{{ currentChapter?.title || '请选择章节' }}</h2>
                  <p>{{ currentChapter?.resource_title || '当前章节使用课程绑定资源进行预览' }}</p>
                </div>
                <div v-if="currentChapter" class="viewer-meta">
                  <span class="viewer-meta-item">{{ formatDurationClock(currentChapter.duration_seconds, currentChapter.duration) }}</span>
                  <span class="viewer-meta-item">{{ currentChapter.progress || 0 }}%</span>
                </div>
              </div>

              <template v-if="currentChapter?.content_type === 'video' && currentChapter.file_url">
                <video
                  ref="videoElement"
                  :src="currentChapter.file_url"
                  class="course-video"
                  controls
                  preload="metadata"
                  @loadedmetadata="handleVideoLoadedMetadata"
                  @timeupdate="handleVideoTimeUpdate"
                  @pause="flushVideoProgress"
                  @ended="markChapterCompleted"
                />
              </template>
              <template v-else-if="currentChapter?.content_type === 'audio' && currentChapter.file_url">
                <div class="audio-stage">
                  <audio :src="currentChapter.file_url" class="course-audio" controls preload="metadata" />
                </div>
              </template>
              <template v-else-if="currentChapter?.content_type === 'image' && currentChapter.file_url">
                <div class="image-stage">
                  <img :src="currentChapter.file_url" :alt="currentChapter.title" class="course-image" />
                </div>
              </template>
              <template v-else-if="currentChapter?.content_type === 'knowledge'">
                <div class="knowledge-stage" v-html="currentChapter.knowledge_content_html || '<p>暂无知识点内容</p>'" />
              </template>
              <template v-else-if="currentChapter?.file_url">
                <iframe :src="currentChapter.file_url" class="doc-frame" title="课程文档预览" />
              </template>
              <a-empty v-else description="当前章节暂无可预览内容" />

              <div v-if="authStore.isStudent && currentChapter" class="viewer-actions">
                <div class="viewer-progress-summary">
                  <span class="viewer-summary-label">当前章节进度</span>
                  <strong>{{ currentChapter.progress || 0 }}%</strong>
                </div>
                <a-button type="primary" @click="markChapterCompleted">标记本章已完成</a-button>
              </div>
            </a-card>

            <a-card :bordered="false" class="section-card">
              <a-tabs v-model:activeKey="activeTab">
                <a-tab-pane key="intro" tab="课程简介">
                  <p class="course-description">{{ course.description || '暂无课程简介' }}</p>
                  <a-descriptions :column="{ xs: 1, md: 2 }" size="small">
                    <a-descriptions-item label="创建者">{{ course.created_by_name || '-' }}</a-descriptions-item>
                    <a-descriptions-item label="主讲教官">{{ course.instructor_name || '-' }}</a-descriptions-item>
                    <a-descriptions-item label="课程时长">{{ formatCourseDuration(course.duration_seconds, course.duration) }}</a-descriptions-item>
                    <a-descriptions-item label="课程标签">{{ formatTagList(course.tags || null) }}</a-descriptions-item>
                  </a-descriptions>

                  <div v-if="!authStore.isStudent" class="related-training-section">
                    <div class="related-training-header">
                      <div>
                        <h3>关联班级</h3>
                        <p>仅展示你当前有管理或授课关系的班级，可直接跳转进入班级页面。</p>
                      </div>
                    </div>

                    <a-empty
                      v-if="!course.related_trainings?.length"
                      description="暂无你可管理或授课的关联班级"
                    />

                    <div v-else class="related-training-list">
                      <article
                        v-for="training in course.related_trainings"
                        :key="training.id"
                        class="related-training-card"
                      >
                        <div class="related-training-main">
                          <div class="related-training-top">
                            <h4>{{ training.name }}</h4>
                            <a-tag :color="getTrainingStatusColor(training.status)">{{ getTrainingStatusLabel(training.status) }}</a-tag>
                          </div>
                          <div class="related-training-meta">
                            <span>班级编号：{{ training.class_code || '-' }}</span>
                            <span>班主任：{{ training.instructor_name || '-' }}</span>
                            <span>时间：{{ formatTrainingDateRange(training.start_date, training.end_date) }}</span>
                          </div>
                          <div v-if="training.relation_roles?.length" class="related-training-roles">
                            <a-tag v-for="role in training.relation_roles" :key="role">{{ role }}</a-tag>
                          </div>
                        </div>

                        <a-button type="link" class="related-training-link" @click="goTrainingDetail(training.id)">
                          查看班级
                        </a-button>
                      </article>
                    </div>
                  </div>
                </a-tab-pane>

                <a-tab-pane v-if="authStore.isStudent" key="notes" tab="学习笔记">
                  <div class="notes-panel">
                    <div class="notes-meta">
                      <span>支持边学边记，内容仅自己可见。</span>
                      <span>{{ course.note?.updated_at ? `最近保存：${formatDateTime(course.note.updated_at)}` : '尚未保存笔记' }}</span>
                    </div>
                    <a-textarea
                      v-model:value="noteContent"
                      :rows="10"
                      placeholder="记录重点、疑问、案例要点或后续复习计划"
                    />
                    <div class="notes-actions">
                      <a-button type="primary" :loading="noteSaving" @click="handleSaveNote">保存笔记</a-button>
                    </div>
                  </div>
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

                <a-tab-pane v-if="canManageCourse" key="resources" tab="关联资源">
                  <div class="resource-bind-toolbar">
                    <a-button type="primary" class="resource-picker-btn" @click="openLibraryPicker">
                      从资源库中选择资源
                    </a-button>
                    <a-button @click="fetchCourse">刷新</a-button>
                  </div>
                  <div class="resource-bind-hint">在弹窗中按住 Ctrl + 鼠标左键可多选，点“确定关联”后直接完成批量关联。</div>
                  <a-table :data-source="courseResources" :columns="resourceColumns" row-key="id" :pagination="false">
                    <template #bodyCell="{ column, record }">
                      <template v-if="column.key === 'tags'">
                        <a-space wrap>
                          <a-tag v-for="tag in record.tags || []" :key="tag">{{ tag }}</a-tag>
                        </a-space>
                      </template>
                      <template v-else-if="column.key === 'content_type'">
                        {{ getCourseFileTypeLabel(record.content_type) }}
                      </template>
                      <template v-else-if="column.key === 'status'">
                        <a-tag :color="getBoundResourceStatusColor(record)">
                          {{ record.status_label || record.status || '-' }}
                        </a-tag>
                      </template>
                      <template v-else-if="column.key === 'action'">
                        <a-popconfirm title="确认解绑该资源？" @confirm="removeResource(record.ref_id || record.id)">
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
            <a-card title="课程章节" :bordered="false" class="section-card chapter-card">
              <div class="chapter-summary">
                <span>共 {{ course.chapter_count || 0 }} 章</span>
                <span v-if="authStore.isStudent">已完成 {{ course.completed_chapter_count || 0 }} 章</span>
              </div>

              <div class="chapter-list">
                <div
                  v-for="(chapter, index) in course.chapters || []"
                  :key="chapter.id || index"
                  class="chapter-item"
                  :class="{
                    active: currentChapterIndex === index,
                    completed: (chapter.progress || 0) >= 100,
                    studying: (chapter.progress || 0) > 0 && (chapter.progress || 0) < 100,
                  }"
                  @click="selectChapter(index)"
                >
                  <div class="chapter-index">
                    <CheckCircleFilled v-if="(chapter.progress || 0) >= 100" />
                    <span v-else>{{ index + 1 }}</span>
                  </div>

                  <div class="chapter-content">
                    <div class="chapter-top">
                      <h4>{{ chapter.title }}</h4>
                      <span class="chapter-duration">{{ formatDurationClock(chapter.duration_seconds, chapter.duration) }}</span>
                    </div>
                    <p>{{ chapter.resource_title || '未绑定资源' }}</p>
                    <div class="chapter-status-row">
                      <span class="chapter-status-text">
                        {{ (chapter.progress || 0) >= 100 ? '已学完' : (chapter.progress || 0) > 0 ? '学习中' : '未开始' }}
                      </span>
                      <span>{{ chapter.progress || 0 }}%</span>
                    </div>
                    <a-progress :percent="chapter.progress || 0" size="small" />
                  </div>
                </div>
              </div>
            </a-card>
          </a-col>
        </a-row>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { CheckCircleFilled } from '@ant-design/icons-vue'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type {
  CourseBoundResourceResponse,
  CourseLearningStatusResponse,
  CourseQAResponse,
  CourseResponse,
} from '@/api/learning-resource'
import {
  bindCourseResource,
  createCourseQuestion,
  deleteCourse,
  getCourseDetail,
  getCourseLearningStatus,
  unbindCourseResource,
  updateCourseChapterProgress,
  updateCourseNote,
} from '@/api/learning-resource'
import { useAuthStore } from '@/stores/auth'
import LibraryItemPickerModal from '@/components/library/LibraryItemPickerModal.vue'
import CourseEditorModal from '@/components/resource/CourseEditorModal.vue'
import {
  formatCourseDuration,
  formatDateTime,
  formatDurationClock,
  formatTagList,
  getCourseCategoryLabel,
  getCourseFileTypeLabel,
  getCourseLearningStatusColor,
  getCourseLearningStatusLabel,
} from '@/utils/learning-resource'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const learningLoading = ref(false)
const noteSaving = ref(false)
const course = ref<CourseResponse | null>(null)
const learningStatus = ref<CourseLearningStatusResponse[]>([])
const qaList = ref<CourseQAResponse[]>([])
const qaInput = ref('')
const qaSubmitting = ref(false)
const currentChapterIndex = ref(0)
const activeTab = ref('intro')
const editorVisible = ref(false)
const pickerVisible = ref(false)
const pickerSubmitting = ref(false)
const courseResources = ref<CourseBoundResourceResponse[]>([])
const noteContent = ref('')
const videoElement = ref<HTMLVideoElement | null>(null)
const progressTimer = ref<number | null>(null)
const progressSaving = ref(false)
const lastSavedSignature = ref('')
const restoringPlayback = ref(false)
const canManageCourse = computed(() => !!course.value?.can_manage_course)
const boundLibraryItemIds = computed(() =>
  courseResources.value
    .filter((item) => item.binding_type === 'library_item' && item.library_item_id)
    .map((item) => Number(item.library_item_id))
)

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
  void fetchCourse()
})

onBeforeUnmount(() => {
  clearProgressTimer()
  void flushVideoProgress()
})

watch(() => route.params.id, () => {
  clearProgressTimer()
  pickerVisible.value = false
  courseResources.value = []
  void fetchCourse()
})

async function fetchCourse() {
  const courseId = Number(route.params.id)
  if (!courseId) {
    return
  }
  loading.value = true
  try {
    const detail = await getCourseDetail(courseId)
    course.value = detail
    qaList.value = [...(detail.qa_list || [])]
    courseResources.value = [...(detail.resources || [])]
    noteContent.value = detail.note?.content || ''
    currentChapterIndex.value = resolveInitialChapterIndex(detail)
    lastSavedSignature.value = ''
    if (detail.can_view_learning_status) {
      await fetchLearningStatus(courseId)
    } else {
      learningStatus.value = []
    }
  } catch (error) {
    course.value = null
    qaList.value = []
    courseResources.value = []
    learningStatus.value = []
    noteContent.value = ''
    pickerVisible.value = false
    message.error(error instanceof Error ? error.message : '加载课程详情失败')
  } finally {
    loading.value = false
  }
}

function resolveInitialChapterIndex(detail: CourseResponse) {
  if (detail.last_studied_chapter_id) {
    const index = (detail.chapters || []).findIndex((item) => item.id === detail.last_studied_chapter_id)
    if (index >= 0) {
      return index
    }
  }
  const inProgressIndex = (detail.chapters || []).findIndex((item) => (item.progress || 0) > 0 && (item.progress || 0) < 100)
  if (inProgressIndex >= 0) {
    return inProgressIndex
  }
  const notStartedIndex = (detail.chapters || []).findIndex((item) => (item.progress || 0) <= 0)
  return notStartedIndex >= 0 ? notStartedIndex : 0
}

async function fetchLearningStatus(courseId: number) {
  learningLoading.value = true
  try {
    learningStatus.value = await getCourseLearningStatus(courseId)
  } finally {
    learningLoading.value = false
  }
}

function clearProgressTimer() {
  if (progressTimer.value !== null) {
    window.clearTimeout(progressTimer.value)
    progressTimer.value = null
  }
}

function handleVideoLoadedMetadata() {
  if (!videoElement.value || !currentChapter.value?.playback_seconds) {
    return
  }
  const duration = Number(videoElement.value.duration || 0)
  if (!Number.isFinite(duration) || duration <= 1) {
    return
  }
  restoringPlayback.value = true
  videoElement.value.currentTime = Math.min(currentChapter.value.playback_seconds, Math.max(duration - 1, 0))
  window.setTimeout(() => {
    restoringPlayback.value = false
  }, 200)
}

function handleVideoTimeUpdate() {
  if (!authStore.isStudent || restoringPlayback.value) {
    return
  }
  clearProgressTimer()
  progressTimer.value = window.setTimeout(() => {
    void persistCurrentVideoProgress()
  }, 1500)
}

async function persistCurrentVideoProgress(forceComplete = false, silent = true) {
  if (!authStore.isStudent || !course.value?.id || !currentChapter.value?.id || currentChapter.value.content_type !== 'video' || !videoElement.value) {
    return
  }

  const duration = Number(videoElement.value.duration || 0)
  if (!Number.isFinite(duration) || duration <= 0) {
    return
  }

  const playbackSeconds = Math.max(Math.floor(videoElement.value.currentTime || 0), 0)
  const computedProgress = Math.round((playbackSeconds / duration) * 100)
  const progress = forceComplete
    ? 100
    : Math.min(99, Math.max(computedProgress, currentChapter.value.progress || 0, playbackSeconds > 0 ? 1 : 0))

  await submitChapterProgress(progress, playbackSeconds, silent)
}

async function flushVideoProgress() {
  clearProgressTimer()
  await persistCurrentVideoProgress(false, true)
}

async function submitChapterProgress(progress: number, playbackSeconds: number, silent = true) {
  if (!course.value?.id || !currentChapter.value?.id || progressSaving.value) {
    return
  }

  const signature = `${course.value.id}:${currentChapter.value.id}:${progress}:${playbackSeconds}`
  if (signature === lastSavedSignature.value) {
    return
  }

  progressSaving.value = true
  try {
    await updateCourseChapterProgress(course.value.id, currentChapter.value.id, {
      progress,
      playback_seconds: playbackSeconds,
    })
    lastSavedSignature.value = signature
    syncLocalProgress(currentChapter.value.id, progress, playbackSeconds)
    if (!silent) {
      message.success(progress >= 100 ? '本章已标记完成' : '学习进度已保存')
    }
  } catch (error) {
    if (!silent) {
      message.error(error instanceof Error ? error.message : '更新学习进度失败')
    }
  } finally {
    progressSaving.value = false
  }
}

function syncLocalProgress(chapterId: number, progress: number, playbackSeconds: number) {
  if (!course.value) {
    return
  }

  const chapter = (course.value.chapters || []).find((item) => item.id === chapterId)
  if (!chapter) {
    return
  }

  chapter.progress = Math.max(chapter.progress || 0, progress)
  chapter.playback_seconds = playbackSeconds
  chapter.last_studied_at = new Date().toISOString()

  const chapters = course.value.chapters || []
  const completedCount = chapters.filter((item) => (item.progress || 0) >= 100).length
  const progressPercent = chapters.length
    ? Math.round(chapters.reduce((sum, item) => sum + Math.min(Math.max(item.progress || 0, 0), 100), 0) / chapters.length)
    : 0

  course.value.progress_percent = progressPercent
  course.value.completed_chapter_count = completedCount
  course.value.chapter_count = chapters.length
  course.value.last_studied_at = new Date().toISOString()
  course.value.last_studied_chapter_id = chapter.id
  course.value.last_studied_chapter_title = chapter.title
  course.value.last_playback_seconds = playbackSeconds
  course.value.learning_status = progressPercent >= 100 ? 'completed' : (progressPercent > 0 || playbackSeconds > 0 ? 'in_progress' : 'not_started')
}

async function selectChapter(index: number) {
  if (index === currentChapterIndex.value) {
    return
  }
  await flushVideoProgress()
  currentChapterIndex.value = index
  lastSavedSignature.value = ''
}

async function markChapterCompleted() {
  if (!currentChapter.value) {
    return
  }
  const playbackSeconds = currentChapter.value.content_type === 'video' && videoElement.value
    ? Math.max(Math.floor(videoElement.value.currentTime || 0), 0)
    : Math.max(currentChapter.value.playback_seconds || 0, 0)
  await submitChapterProgress(100, playbackSeconds, false)
}

async function handleSaveNote() {
  if (!course.value?.id) {
    return
  }
  noteSaving.value = true
  try {
    const note = await updateCourseNote(course.value.id, { content: noteContent.value })
    course.value.note = note
    message.success('笔记已保存')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '笔记保存失败')
  } finally {
    noteSaving.value = false
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

function openLibraryPicker() {
  if (!canManageCourse.value) {
    message.warning('仅课程管理者可绑定课程资源')
    return
  }
  pickerVisible.value = true
}

async function handlePickerConfirm(selectedIds: number[]) {
  if (!course.value?.id || !selectedIds.length) {
    message.warning('请先选择资源')
    return
  }
  pickerSubmitting.value = true
  try {
    const startSortOrder = courseResources.value.length
    const results = await Promise.allSettled(
      selectedIds.map((libraryItemId, index) => bindCourseResource(course.value!.id, {
        library_item_id: libraryItemId,
        usage_type: 'required',
        sort_order: startSortOrder + index,
      })),
    )
    const succeeded = results.filter((item) => item.status === 'fulfilled').length
    const failed = results.filter((item) => item.status === 'rejected')

    if (succeeded > 0) {
      pickerVisible.value = false
      await fetchCourse()
    }

    if (!failed.length) {
      message.success(`已关联 ${succeeded} 个资源`)
      return
    }

    if (succeeded > 0) {
      message.warning(`已关联 ${succeeded} 个资源，另有 ${failed.length} 个关联失败`)
      return
    }

    const firstError = failed[0]
    if (firstError?.status === 'rejected') {
      message.error(firstError.reason instanceof Error ? firstError.reason.message : '关联失败')
      return
    }
    message.error('关联失败')
  } finally {
    pickerSubmitting.value = false
  }
}

async function removeResource(resourceId: number) {
  if (!canManageCourse.value) {
    message.warning('仅课程管理者可解绑课程资源')
    return
  }
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
  if (!canManageCourse.value) {
    message.warning('仅课程管理者可删除课程')
    return
  }
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

function openEdit() {
  if (!canManageCourse.value) {
    message.warning('仅课程管理者可编辑课程')
    return
  }
  editorVisible.value = true
}

function getTrainingStatusLabel(status?: string | null) {
  const statusMap: Record<string, string> = {
    upcoming: '未开始',
    active: '进行中',
    ended: '已结束',
  }
  return statusMap[status || ''] || (status || '未知状态')
}

function getTrainingStatusColor(status?: string | null) {
  const statusMap: Record<string, string> = {
    upcoming: 'blue',
    active: 'green',
    ended: 'default',
  }
  return statusMap[status || ''] || 'default'
}

function formatTrainingDateRange(startDate?: string | null, endDate?: string | null) {
  if (!startDate && !endDate) {
    return '-'
  }
  return `${startDate || '-'} ~ ${endDate || '-'}`
}

function goTrainingDetail(trainingId: number) {
  void router.push(`/classes/${trainingId}`)
}

function getBoundResourceStatusColor(resource: CourseBoundResourceResponse) {
  if (resource.binding_type === 'library_item') {
    return resource.status === 'public' ? 'gold' : 'blue'
  }
  const statusMap: Record<string, string> = {
    draft: 'default',
    pending_review: 'orange',
    reviewing: 'processing',
    published: 'green',
    rejected: 'red',
    offline: 'default',
  }
  return statusMap[resource.status || ''] || 'default'
}
</script>

<style scoped>
.detail-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 42%, #0f3460 100%);
  padding: 30px 32px;
}

.header-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.header-title {
  margin: 0 0 12px;
  font-size: 30px;
  color: var(--v2-text-white);
}

.header-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.meta-badge,
.meta-item {
  color: rgba(255, 255, 255, 0.9);
}

.meta-badge {
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(10px);
}

.meta-badge-status {
  font-weight: 700;
  background: rgba(255, 255, 255, 0.94);
}

.loading-block {
  display: block;
  padding: 80px 0;
  text-align: center;
}

.viewer-card,
.section-card {
  border-radius: 20px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
}

.viewer-card {
  overflow: hidden;
}

.viewer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px 0;
}

.viewer-head h2 {
  margin: 0 0 6px;
  font-size: 22px;
  color: var(--v2-text-primary);
}

.viewer-head p {
  margin: 0;
  color: var(--v2-text-secondary);
}

.viewer-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.viewer-meta-item {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  background: var(--v2-primary-light);
  color: var(--v2-primary);
  font-size: 13px;
  font-weight: 700;
}

.course-video,
.course-image,
.doc-frame {
  width: 100%;
  min-height: 420px;
  max-height: 70vh;
  border: 0;
  display: block;
  background: #0b1220;
}

.course-video,
.course-image,
.doc-frame,
.image-stage {
  margin-top: 18px;
}

.audio-stage {
  padding: 26px 22px;
  background: linear-gradient(180deg, rgba(238, 242, 255, 0.72), rgba(248, 250, 252, 0.92));
}

.course-audio {
  width: 100%;
}

.course-image {
  object-fit: contain;
}

.image-stage {
  background: #0b1220;
}

.knowledge-stage {
  min-height: 320px;
  padding: 22px;
  line-height: 1.9;
  color: var(--v2-text-primary);
  background: var(--v2-bg);
}

.viewer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 22px 22px;
}

.viewer-progress-summary {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.viewer-summary-label {
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.viewer-progress-summary strong {
  font-size: 24px;
  color: var(--v2-text-primary);
}

.section-card {
  margin-top: 16px;
}

.course-description {
  color: var(--v2-text-secondary);
  line-height: 1.8;
  margin-bottom: 16px;
}

.related-training-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--v2-border-light);
}

.related-training-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.related-training-header h3 {
  margin: 0 0 6px;
  font-size: 16px;
  color: var(--v2-text-primary);
}

.related-training-header p {
  margin: 0;
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.related-training-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.related-training-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border: 1px solid var(--v2-border-light);
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(75, 110, 245, 0.04) 0%, rgba(255, 255, 255, 0.95) 100%);
}

.related-training-main {
  flex: 1;
  min-width: 0;
}

.related-training-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.related-training-top h4 {
  margin: 0;
  font-size: 15px;
  color: var(--v2-text-primary);
}

.related-training-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.related-training-roles {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.related-training-link {
  flex-shrink: 0;
  padding-inline: 0;
  font-weight: 600;
}

.notes-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.notes-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.notes-actions {
  display: flex;
  justify-content: flex-end;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.resource-bind-toolbar {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.resource-picker-btn {
  min-width: 220px;
  background: linear-gradient(135deg, #2457d6 0%, #4f46e5 100%);
  border: none;
  box-shadow: 0 12px 24px rgba(59, 130, 246, 0.2);
}

.resource-bind-hint {
  margin-bottom: 16px;
  color: var(--v2-text-muted);
  font-size: 13px;
}

.qa-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.qa-item {
  padding: 14px;
  border: 1px solid var(--v2-border);
  border-radius: 16px;
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

.chapter-card {
  position: sticky;
  top: 16px;
}

.chapter-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
  color: var(--v2-text-secondary);
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
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 18px;
  background: #fff;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.chapter-item:hover {
  transform: translateY(-1px);
  border-color: rgba(75, 110, 245, 0.24);
  box-shadow: 0 12px 24px rgba(75, 110, 245, 0.08);
}

.chapter-item.active {
  border-color: rgba(75, 110, 245, 0.35);
  background: linear-gradient(180deg, rgba(238, 242, 255, 0.94), rgba(255, 255, 255, 0.98));
}

.chapter-item.completed {
  border-color: rgba(34, 197, 94, 0.24);
}

.chapter-item.studying {
  border-color: rgba(37, 99, 235, 0.2);
}

.chapter-index {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--v2-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
}

.chapter-item.completed .chapter-index {
  background: #16a34a;
}

.chapter-content {
  flex: 1;
  min-width: 0;
}

.chapter-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.chapter-top h4 {
  margin: 0;
  color: var(--v2-text-primary);
}

.chapter-duration {
  color: var(--v2-text-secondary);
  font-size: 12px;
  white-space: nowrap;
}

.chapter-content p {
  margin: 0 0 10px;
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.chapter-status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  color: var(--v2-text-secondary);
  font-size: 12px;
}

.chapter-status-text {
  font-weight: 600;
}

@media (max-width: 768px) {
  .detail-header {
    padding: 22px 16px;
  }

  .header-actions,
  .resource-bind-toolbar,
  .viewer-head,
  .viewer-actions,
  .notes-meta {
    flex-direction: column;
    align-items: stretch;
  }

  .chapter-card {
    position: static;
  }

  .course-video,
  .course-image,
  .doc-frame {
    min-height: 280px;
  }
}
</style>
