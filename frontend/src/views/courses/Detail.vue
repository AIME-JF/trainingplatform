<template>
  <div v-if="localCourse.title" class="course-detail-page">
    <div class="top-bar">
        <a-breadcrumb>
        <a-breadcrumb-item @click="$router.push('/courses')" style="cursor: pointer; color: var(--police-primary)">
          课程资源
        </a-breadcrumb-item>
        <a-breadcrumb-item>{{ localCourse.title }}</a-breadcrumb-item>
      </a-breadcrumb>
      <div class="top-actions">
        <a-button v-if="authStore.isAdmin || authStore.isInstructor" size="small" @click="editorVisible = true">
          <template #icon><EditOutlined /></template>编辑课程
        </a-button>
        <a-popconfirm
          v-if="authStore.isAdmin || authStore.isInstructor"
          title="确定删除此课程吗？删除后不可恢复。"
          ok-text="确认删除"
          cancel-text="取消"
          @confirm="handleDeleteCourse"
        >
          <a-button size="small" danger>
            <template #icon><DeleteOutlined /></template>删除课程
          </a-button>
        </a-popconfirm>
      </div>
    </div>

    <CourseEditorModal
      v-model:open="editorVisible"
      :course-id="courseId"
      @success="handleEditorSuccess"
    />

    <a-row :gutter="20">
      <a-col :span="16">
        <div class="viewer-card">
          <template v-if="viewerType === 'video'">
            <video
              ref="videoRef"
              :src="currentVideoUrl"
              class="course-video"
              controls
              preload="metadata"
            ></video>
          </template>
          <template v-else-if="viewerType === 'image'">
            <div class="doc-toolbar">
              <div>
                <div class="doc-title">{{ currentChapter.title || localCourse.title }}</div>
                <div class="doc-subtitle">{{ currentChapterBindingText }}</div>
              </div>
              <div class="doc-actions">
                <a-button size="small" type="primary" ghost :href="currentImageUrl" target="_blank">
                  <template #icon><DownloadOutlined /></template>查看原图
                </a-button>
              </div>
            </div>
            <div class="image-stage">
              <img :src="currentImageUrl" class="course-image" :alt="currentChapter.title || localCourse.title" />
            </div>
          </template>
          <template v-else>
            <div class="doc-toolbar">
              <div>
                <div class="doc-title">{{ currentChapter.title || localCourse.title }}</div>
                <div class="doc-subtitle">{{ currentChapterBindingText }}</div>
              </div>
              <div class="doc-actions">
                <a-button size="small" type="primary" ghost :href="currentDocUrl" target="_blank">
                  <template #icon><DownloadOutlined /></template>下载文档
                </a-button>
              </div>
            </div>
            <iframe :src="currentDocUrl" class="doc-iframe" frameborder="0" title="课程文档"></iframe>
          </template>
        </div>

        <a-card :bordered="false" style="margin-top: 16px">
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane key="intro" tab="课程简介">
              <p class="course-description">{{ localCourse.description || '暂无课程简介' }}</p>
              <div class="meta-grid">
                <div class="meta-item"><span class="meta-label">创建者</span><span>{{ localCourse.createdByName || '-' }}</span></div>
                <div class="meta-item"><span class="meta-label">主讲教官</span><span>{{ localCourse.instructorName || '-' }}</span></div>
                <div class="meta-item"><span class="meta-label">章节数量</span><span>{{ localCourse.chapters?.length || 0 }} 章</span></div>
                <div class="meta-item"><span class="meta-label">课程标签</span><span>{{ (localCourse.tags || []).join('、') || '-' }}</span></div>
              </div>
            </a-tab-pane>

            <a-tab-pane v-if="localCourse.canViewLearningStatus" key="learning" tab="学习情况">
              <a-spin :spinning="learningStatusLoading">
                <a-table
                  :data-source="learningStatus"
                  :columns="learningStatusColumns"
                  row-key="userId"
                  :pagination="{ pageSize: 10 }"
                >
                  <template #bodyCell="{ column, record }">
                    <template v-if="column.key === 'progressPercent'">
                      <div class="learning-progress-cell">
                        <a-progress :percent="record.progressPercent || 0" size="small" />
                        <span>{{ record.completedChapterCount || 0 }}/{{ record.chapterCount || 0 }} 章</span>
                      </div>
                    </template>
                    <template v-else-if="column.key === 'lastStudiedChapterTitle'">
                      {{ record.lastStudiedChapterTitle || '-' }}
                    </template>
                    <template v-else-if="column.key === 'lastStudiedAt'">
                      {{ formatDateTime(record.lastStudiedAt) }}
                    </template>
                  </template>
                </a-table>
              </a-spin>
            </a-tab-pane>

            <a-tab-pane key="resources" tab="关联资源" v-if="authStore.isAdmin || authStore.isInstructor">
              <div class="resource-bind-toolbar">
                <a-select
                  v-model:value="selectedResourceId"
                  show-search
                  :options="resourceOptions"
                  :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
                  placeholder="选择资源后绑定到课程"
                  class="resource-bind-select"
                />
                <a-button type="primary" @click="bindSelectedResource">绑定资源</a-button>
                <a-button @click="fetchCourse">刷新</a-button>
              </div>
              <a-table :data-source="courseResources" :columns="resourceColumns" row-key="id" :pagination="false">
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'tags'">
                    <a-space wrap>
                      <a-tag v-for="tag in (record.tags || [])" :key="tag">{{ tag }}</a-tag>
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
                    <a-avatar size="small" style="background: #003087">{{ (item.userName || '?').charAt(0) }}</a-avatar>
                    <span class="qa-user">{{ item.userName }}</span>
                    <span class="qa-text">{{ item.question }}</span>
                  </div>
                  <div v-if="item.answer" class="qa-answer">
                    <a-tag color="gold" size="small">教官回复</a-tag>
                    {{ item.answer }}
                  </div>
                </div>
              </div>
              <a-empty v-else description="暂无答疑内容" />
              <a-input-search
                v-model:value="qaInput"
                placeholder="输入你的问题，按回车或点提交..."
                enter-button="提交"
                :loading="qaSubmitting"
                style="margin-top: 12px"
                @search="handleQASubmit"
              />
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>

      <a-col :span="8">
        <a-card title="课程章节" :bordered="false">
          <div class="chapter-list">
            <div
              v-for="(chapter, idx) in localCourse.chapters"
              :key="chapter.id || idx"
              class="chapter-item"
              :class="{ active: currentChapterIdx === idx }"
              @click="selectChapter(idx)"
            >
              <div class="chapter-main">
                <div class="chapter-index">{{ idx + 1 }}</div>
                <div class="chapter-info">
                  <div class="chapter-title">{{ chapter.title }}</div>
                  <div class="chapter-meta">{{ getChapterMetaText(chapter) }}</div>
                </div>
              </div>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { DeleteOutlined, DownloadOutlined, EditOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import {
  bindCourseResource,
  createCourseQA,
  deleteCourse as apiDeleteCourse,
  getCourse,
  getCourseLearningStatus,
  keepaliveChapterProgress,
  saveCourseNote,
  unbindCourseResource,
  updateChapterProgress,
} from '@/api/course'
import { getResources } from '@/api/resource'
import { useAuthStore } from '@/stores/auth'
import CourseEditorModal from './components/CourseEditorModal.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const courseId = computed(() => route.params.id)
const editorVisible = ref(false)
const activeTab = ref('intro')
const currentChapterIdx = ref(0)
const localCourse = ref({
  title: '',
  description: '',
  createdByName: '',
  instructorName: '',
  tags: [],
  duration: 0,
  studentCount: 0,
  progressPercent: 0,
  canViewLearningStatus: false,
  chapters: [],
})

const videoRef = ref(null)
const pendingSeekSeconds = ref(0)
let lastProgressAt = 0
let lastPersistSignature = ''

const noteContent = ref('')
const noteSaving = ref(false)
const notesSaved = ref(false)
const qaList = ref([])
const qaInput = ref('')
const qaSubmitting = ref(false)

const courseResources = ref([])
const availableResources = ref([])
const selectedResourceId = ref(undefined)
const learningStatus = ref([])
const learningStatusLoading = ref(false)
const learningStatusLoaded = ref(false)

const currentChapter = computed(() => localCourse.value.chapters[currentChapterIdx.value] || {})
const viewerType = computed(() => {
  if (currentChapter.value.contentType === 'video') {
    return 'video'
  }
  if (currentChapter.value.contentType === 'image') {
    return 'image'
  }
  return 'document'
})
const currentVideoUrl = computed(() => currentChapter.value.fileUrl || currentChapter.value.videoUrl || '')
const currentDocUrl = computed(() => currentChapter.value.fileUrl || currentChapter.value.docUrl || '')
const currentImageUrl = computed(() => currentChapter.value.fileUrl || currentChapter.value.docUrl || '')
const currentChapterBindingText = computed(() => getChapterBindingText(currentChapter.value))

const resourceColumns = [
  { title: '标题', dataIndex: 'title', key: 'title' },
  { title: '类型', dataIndex: 'contentType', key: 'contentType', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 120 },
  { title: '标签', key: 'tags' },
  { title: '操作', key: 'action', width: 120 },
]
const learningStatusColumns = [
  { title: '学员', dataIndex: 'userName', key: 'userName', width: 140 },
  { title: '身份证号', dataIndex: 'idCardNumber', key: 'idCardNumber', width: 180 },
  { title: '部门', dataIndex: 'departmentName', key: 'departmentName', width: 180 },
  { title: '课程进度', dataIndex: 'progressPercent', key: 'progressPercent', width: 240 },
  { title: '最近章节', dataIndex: 'lastStudiedChapterTitle', key: 'lastStudiedChapterTitle' },
  { title: '最近学习时间', dataIndex: 'lastStudiedAt', key: 'lastStudiedAt', width: 180 },
]
const resourceOptions = computed(() => (availableResources.value || []).map((item) => ({
  value: item.id,
  label: `${item.title}（${item.status || '-'}）`,
})))

function getNoteCacheKey() {
  return `course_note_${authStore.currentUser?.id || 'guest'}_${courseId.value}`
}

function formatDateTime(value) {
  if (!value) {
    return '-'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '-'
  }
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function recalcChapterLocks() {
  const chapters = localCourse.value.chapters || []
  chapters.forEach((chapter, idx) => {
    chapter.locked = idx > 0 && Number(chapters[idx - 1]?.progress || 0) < 100
  })
}

function calculateCourseProgress(chapters) {
  const list = chapters || []
  if (!list.length) {
    return 0
  }
  return Math.round(list.reduce((sum, chapter) => sum + Math.min(100, Math.max(0, Number(chapter.progress || 0))), 0) / list.length)
}

function getChapterTypeLabel(chapter) {
  if (chapter?.contentType === 'image') {
    return '图片'
  }
  if (chapter?.contentType === 'document') {
    return '文档'
  }
  return '视频'
}

function getChapterBindingText(chapter) {
  if (!chapter) {
    return '请选择章节开始学习'
  }
  const bindingParts = [
    chapter.resourceTitle,
    chapter.resourceFileLabel,
    chapter.resourceFileName,
  ].filter(Boolean)
  if (bindingParts.length) {
    return `当前内容引用：${bindingParts.join(' / ')}`
  }
  if (chapter.fileId) {
    return '当前内容沿用历史文件引用'
  }
  return `${getChapterTypeLabel(chapter)}章节`
}

function getChapterMetaText(chapter) {
  const parts = [getChapterTypeLabel(chapter)]
  if (chapter.resourceTitle) {
    const resourceParts = [chapter.resourceTitle, chapter.resourceFileLabel || chapter.resourceFileName].filter(Boolean).join(' / ')
    parts.push(resourceParts)
  } else if (chapter.fileId) {
    parts.push('历史文件')
  }
  return parts.join(' · ')
}

function resolveChapterIndex(course, chapters) {
  const previousChapterId = currentChapter.value?.id
  const preferredChapterId = previousChapterId || course.lastStudiedChapterId || chapters[0]?.id
  const index = chapters.findIndex((chapter) => chapter.id === preferredChapterId)
  return index >= 0 ? index : 0
}

function resetVideoResumeState() {
  pendingSeekSeconds.value = currentChapter.value?.progress >= 100
    ? 0
    : Math.max(0, Number(currentChapter.value?.playbackSeconds || 0))
  lastProgressAt = 0
  lastPersistSignature = ''
  if (videoRef.value && viewerType.value === 'video') {
    videoRef.value.pause()
  }
}

async function fetchCourse() {
  const data = await getCourse(courseId.value)
  const chapters = (data.chapters || []).map((chapter) => ({
    ...chapter,
    progress: Number(chapter.progress || 0),
    playbackSeconds: Number(chapter.playbackSeconds || 0),
    locked: false,
  }))
  const targetIndex = resolveChapterIndex(data, chapters)
  if (chapters[targetIndex]?.id === data.lastStudiedChapterId) {
    chapters[targetIndex].playbackSeconds = Math.max(
      Number(chapters[targetIndex].playbackSeconds || 0),
      Number(data.lastPlaybackSeconds || 0),
    )
  }

  localCourse.value = {
    ...data,
    createdByName: data.createdByName || '',
    instructorName: data.instructorName || '',
    progressPercent: Number(data.progressPercent || 0),
    canViewLearningStatus: !!data.canViewLearningStatus,
    chapters,
  }
  currentChapterIdx.value = targetIndex
  recalcChapterLocks()
  resetVideoResumeState()
  noteContent.value = data.note?.content ?? localStorage.getItem(getNoteCacheKey()) ?? ''
  qaList.value = data.qaList || []
  courseResources.value = data.resources || []
  learningStatusLoaded.value = false
  if (activeTab.value === 'learning' && localCourse.value.canViewLearningStatus) {
    loadCourseLearningStatus()
  }
}

async function loadCourseLearningStatus() {
  if (!localCourse.value.canViewLearningStatus || learningStatusLoading.value || learningStatusLoaded.value) {
    return
  }
  learningStatusLoading.value = true
  try {
    learningStatus.value = await getCourseLearningStatus(courseId.value)
    learningStatusLoaded.value = true
  } catch (error) {
    learningStatus.value = []
    if (error?.response?.status === 404) {
      localCourse.value.canViewLearningStatus = false
      if (activeTab.value === 'learning') {
        activeTab.value = 'intro'
      }
      return
    }
    message.error(error?.message || '加载学习情况失败')
  } finally {
    learningStatusLoading.value = false
  }
}

async function loadResourceCandidates() {
  if (!(authStore.isAdmin || authStore.isInstructor)) {
    return
  }
  try {
    const response = await getResources({ page: 1, size: 200, status: 'published' })
    availableResources.value = response.items || []
  } catch {
    availableResources.value = []
  }
}

async function bindSelectedResource() {
  if (!selectedResourceId.value) {
    message.warning('请选择资源')
    return
  }
  try {
    await bindCourseResource(courseId.value, {
      resourceId: selectedResourceId.value,
      usageType: 'required',
      sortOrder: 0,
    })
    selectedResourceId.value = undefined
    await fetchCourse()
    message.success('绑定成功')
  } catch (error) {
    message.error(error?.message || '绑定失败')
  }
}

async function removeResource(resourceId) {
  try {
    await unbindCourseResource(courseId.value, resourceId)
    await fetchCourse()
    message.success('解绑成功')
  } catch (error) {
    message.error(error?.message || '解绑失败')
  }
}

async function handleQASubmit() {
  const question = qaInput.value.trim()
  if (!question) {
    message.warning('请输入提问内容')
    return
  }
  qaSubmitting.value = true
  try {
    const item = await createCourseQA(courseId.value, { question })
    qaList.value.unshift(item)
    qaInput.value = ''
    message.success('提问已提交')
  } catch (error) {
    message.error(error?.message || '提交失败，请稍后重试')
  } finally {
    qaSubmitting.value = false
  }
}

async function handleSaveNote() {
  noteSaving.value = true
  try {
    const response = await saveCourseNote(courseId.value, noteContent.value || '')
    noteContent.value = response?.content || ''
    localStorage.setItem(getNoteCacheKey(), noteContent.value)
    notesSaved.value = true
    setTimeout(() => {
      notesSaved.value = false
    }, 2000)
  } catch (error) {
    localStorage.setItem(getNoteCacheKey(), noteContent.value)
    notesSaved.value = true
    setTimeout(() => {
      notesSaved.value = false
    }, 2000)
    message.warning(error?.message || '笔记已暂存到本地')
  } finally {
    noteSaving.value = false
  }
}

function buildProgressPayload() {
  const chapter = currentChapter.value
  if (!chapter?.id) {
    return null
  }

  if (viewerType.value === 'video') {
    const duration = Number(videoRef.value?.duration || 0)
    const seconds = Math.max(0, Math.floor(Number(videoRef.value?.currentTime || chapter.playbackSeconds || 0)))
    const progress = duration > 0
      ? Math.min(100, Math.round((seconds / duration) * 100))
      : Math.max(0, Number(chapter.progress || 0))
    return {
      progress: Math.max(Number(chapter.progress || 0), progress),
      playbackSeconds: seconds,
    }
  }

  return {
    progress: Math.max(0, Number(chapter.progress || 0)),
    playbackSeconds: Math.max(0, Number(chapter.playbackSeconds || 0)),
  }
}

function applyProgress(payload, response) {
  const chapter = currentChapter.value
  if (!chapter?.id) {
    return
  }
  chapter.progress = Math.max(Number(chapter.progress || 0), Number(response?.progress ?? payload.progress ?? 0))
  chapter.playbackSeconds = Math.max(0, Number(response?.playbackSeconds ?? payload.playbackSeconds ?? 0))
  localCourse.value.progressPercent = calculateCourseProgress(localCourse.value.chapters)
  recalcChapterLocks()
}

async function persistCurrentProgress(options = {}) {
  const chapter = currentChapter.value
  const payload = buildProgressPayload()
  if (!chapter?.id || !payload) {
    return
  }
  if (!options.force && payload.progress <= 0 && payload.playbackSeconds <= 0) {
    return
  }

  const signature = `${chapter.id}:${payload.progress}:${payload.playbackSeconds}`
  if (!options.force && signature === lastPersistSignature) {
    return
  }
  lastPersistSignature = signature

  try {
    if (options.preferKeepalive) {
      keepaliveChapterProgress(courseId.value, chapter.id, payload)
      applyProgress(payload)
      return
    }
    const response = await updateChapterProgress(courseId.value, chapter.id, payload)
    applyProgress(payload, response)
  } catch {
    if (!options.preferKeepalive) {
      throw new Error('保存学习进度失败')
    }
  }
}

async function selectChapter(index) {
  const chapter = localCourse.value.chapters[index]
  if (!chapter || index === currentChapterIdx.value) {
    return
  }
  try {
    // 保留接口调用能力，未来可在培训班场景恢复进度记录
  } catch {
    message.warning('上一章节进度保存失败，已继续切换章节')
  }
  currentChapterIdx.value = index
  resetVideoResumeState()
}

function onMetaLoaded() {
  if (!videoRef.value) {
    return
  }
  const duration = Number(videoRef.value.duration || 0)
  const seekSeconds = Math.min(
    Math.max(0, Number(pendingSeekSeconds.value || 0)),
    Math.max(0, duration - 1),
  )
  if (seekSeconds > 0) {
    videoRef.value.currentTime = seekSeconds
  }
  pendingSeekSeconds.value = 0
}

function handleVideoPause() {
  persistCurrentProgress().catch(() => {})
}

async function onVideoEnded() {
  const chapter = currentChapter.value
  if (!chapter?.id) {
    return
  }
  chapter.progress = 100
  chapter.playbackSeconds = Math.floor(Number(videoRef.value?.duration || 0))
  await persistCurrentProgress({ force: true })
}

function onTimeUpdate() {
  if (!videoRef.value || !currentChapter.value?.id) {
    return
  }
  currentChapter.value.playbackSeconds = Math.floor(Number(videoRef.value.currentTime || 0))
  const now = Date.now()
  if (now - lastProgressAt < 5000) {
    return
  }
  lastProgressAt = now
  persistCurrentProgress().catch(() => {})
}

async function markDocProgress() {
  const chapter = currentChapter.value
  if (!chapter?.id) {
    return
  }
  chapter.progress = 100
  chapter.playbackSeconds = 0
  try {
    await persistCurrentProgress({ force: true })
    message.success('已标记本章完成')
  } catch (error) {
    message.warning(error?.message || '进度保存失败，请稍后重试')
  }
}

async function handleDeleteCourse() {
  try {
    await apiDeleteCourse(courseId.value)
    message.success('课程已删除')
    router.push('/courses')
  } catch (error) {
    message.error(error?.message || '删除失败')
  }
}

async function handleEditorSuccess() {
  await fetchCourse()
}

function handleVisibilityChange() {
  // 学员进度记录已移至培训班，保留函数占位
}

function handleBeforeUnload() {
  // 学员进度记录已移至培训班，保留函数占位
}

watch(activeTab, (tab) => {
  if (tab === 'resources' && (authStore.isAdmin || authStore.isInstructor)) {
    loadResourceCandidates()
  }
  if (tab === 'learning') {
    loadCourseLearningStatus()
  }
})

watch(
  () => currentChapter.value?.id,
  () => {
    resetVideoResumeState()
  },
)

onMounted(async () => {
  try {
    await fetchCourse()
  } catch (error) {
    message.error(error?.message || '加载课程失败')
  }
  document.addEventListener('visibilitychange', handleVisibilityChange)
  window.addEventListener('beforeunload', handleBeforeUnload)
  window.addEventListener('pagehide', handleBeforeUnload)
})

onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  window.removeEventListener('beforeunload', handleBeforeUnload)
  window.removeEventListener('pagehide', handleBeforeUnload)
})

onBeforeRouteLeave(() => {
  // 学员进度记录已移至培训班，此处保留钩子占位
  return true
})
</script>

<style scoped>
.course-detail-page { padding: 0; }
.top-bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; gap: 12px; }
.top-actions { display: flex; gap: 8px; }
.viewer-card { border: 1px solid #e8e8e8; border-radius: 8px; overflow: hidden; background: #fff; }
.course-video { width: 100%; height: 420px; display: block; background: #000; }
.doc-toolbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 16px 20px; border-bottom: 1px solid #eef1f5; background: linear-gradient(135deg, #f8fbff, #edf4ff); }
.doc-title { font-size: 16px; font-weight: 600; color: #1f2d3d; }
.doc-subtitle { margin-top: 4px; font-size: 12px; color: #7a8699; }
.doc-actions { display: flex; gap: 8px; }
.doc-iframe { width: 100%; height: 560px; display: block; }
.image-stage { display: flex; align-items: center; justify-content: center; min-height: 560px; padding: 24px; background: #f7f9fc; }
.course-image { max-width: 100%; max-height: 520px; object-fit: contain; border-radius: 8px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08); }
.course-description { line-height: 1.8; color: #444; }
.meta-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 16px; }
.meta-item { display: flex; gap: 8px; font-size: 13px; }
.meta-label { min-width: 60px; color: #888; }
.chapter-list { display: flex; flex-direction: column; gap: 8px; max-height: 640px; overflow-y: auto; }
.chapter-item { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px; border-radius: 8px; border: 1px solid transparent; transition: all 0.2s; cursor: pointer; }
.chapter-item:hover:not(.locked) { background: #f6f9ff; border-color: #dbe7ff; }
.chapter-item.active { background: #edf4ff; border-color: var(--police-primary); }
.chapter-item.locked { opacity: 0.5; cursor: not-allowed; }
.chapter-main { display: flex; align-items: center; gap: 10px; min-width: 0; }
.chapter-index { width: 26px; height: 26px; border-radius: 50%; background: var(--police-primary); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.chapter-title { font-size: 13px; font-weight: 600; color: #1f2d3d; }
.chapter-meta { margin-top: 4px; font-size: 12px; color: #7a8699; }
.chapter-status { flex-shrink: 0; }
.qa-list { display: flex; flex-direction: column; gap: 12px; }
.qa-item { border-left: 3px solid var(--police-primary); padding-left: 12px; }
.qa-question { display: flex; align-items: center; gap: 8px; }
.qa-user { font-size: 12px; color: #888; }
.qa-text { font-size: 13px; color: #333; }
.qa-answer { margin-top: 6px; font-size: 13px; color: #555; background: #fffbe6; padding: 6px 10px; border-radius: 4px; }
.resource-bind-toolbar { margin-bottom: 12px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.resource-bind-select { flex: 1; min-width: 320px; }
.learning-progress-cell { min-width: 180px; }

@media (max-width: 768px) {
  .top-bar { flex-wrap: wrap; }
  .top-actions { width: 100%; }
  .course-video { height: 240px; }
  .doc-toolbar { flex-direction: column; align-items: flex-start; }
  .doc-actions { width: 100%; }
  .doc-iframe { height: 360px; }
  .image-stage { min-height: 360px; padding: 16px; }
  .course-image { max-height: 320px; }
  .meta-grid { grid-template-columns: 1fr; }
  .resource-bind-select { width: 100%; min-width: 0; }
}
</style>
