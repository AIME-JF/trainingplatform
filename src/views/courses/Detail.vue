<template>
  <div class="course-detail-page" v-if="localCourse.title">
    <!-- 面包屑 + 编辑按钮 -->
    <div class="top-bar">
      <a-breadcrumb>
        <a-breadcrumb-item @click="$router.push('/courses')" style="cursor:pointer;color:var(--police-primary)">课程中心</a-breadcrumb-item>
        <a-breadcrumb-item>{{ localCourse.title }}</a-breadcrumb-item>
      </a-breadcrumb>
      <a-button
        v-if="authStore.isAdmin || authStore.isInstructor"
        size="small"
        @click="openEdit"
      >
        <template #icon><EditOutlined /></template>编辑课程
      </a-button>
      <a-popconfirm
        v-if="authStore.isAdmin || authStore.isInstructor"
        title="确定删除此课程吗？删除后不可恢复。"
        ok-text="确认删除"
        cancel-text="取消"
        @confirm="handleDeleteCourse"
      >
        <a-button
          v-if="authStore.isAdmin || authStore.isInstructor"
          size="small"
          danger
        >
          <template #icon><DeleteOutlined /></template>删除课程
        </a-button>
      </a-popconfirm>
    </div>

    <a-row :gutter="20">
      <!-- 左：内容区 + 课程信息 -->
      <a-col :span="16">
        <!-- 视频课件 -->
        <div v-if="isVideo" class="video-player-wrap">
          <div class="video-player" ref="playerWrapRef">
            <video
              ref="videoRef"
              :src="currentVideoUrl"
              class="course-video"
              preload="metadata"
              @play="isPlaying = true"
              @pause="isPlaying = false"
              @ended="onVideoEnded"
              @timeupdate="onTimeUpdate"
              @loadedmetadata="onMetaLoaded"
              @error="videoError = true"
            ></video>
            <div v-if="videoError" class="video-error-mask">
              <div>⚠️ 视频加载失败，请检查网络连接</div>
              <div style="font-size:12px;margin-top:8px;opacity:0.7">{{ currentVideoUrl }}</div>
            </div>
            <div class="video-click-overlay" @click="togglePlay" @dblclick="enterFullscreen"></div>
            <transition name="fade">
              <div v-if="showPlayIcon" class="play-center-icon">{{ isPlaying ? '⏸' : '▶' }}</div>
            </transition>
            <div class="chapter-badge-wrap">
              <div class="chapter-badge">第 {{ currentChapterIdx + 1 }} 章：{{ currentChapter.title }}</div>
            </div>
            <div class="video-controls">
              <div class="controls-left">
                <button class="ctrl-btn" @click="togglePlay">{{ isPlaying ? '⏸' : '▶' }}</button>
                <span class="time-display">{{ currentTime }} / {{ totalDuration }}</span>
              </div>
              <div class="progress-bar-wrap" @click="seekVideo">
                <div class="progress-bar-bg">
                  <div class="progress-bar-fill" :style="{ width: playProgress + '%' }"></div>
                  <div class="progress-handle" :style="{ left: playProgress + '%' }"></div>
                </div>
              </div>
              <div class="controls-right">
                <button class="ctrl-btn" @click="toggleMute">{{ isMuted ? '🔇' : '🔊' }}</button>
                <button class="ctrl-btn" @click="enterFullscreen">⛶ 全屏</button>
              </div>
            </div>
          </div>
        </div>

        <!-- 文档课件 -->
        <div v-else class="doc-viewer-wrap">
          <div class="doc-viewer">
            <div class="doc-header">
              <div class="doc-icon">📄</div>
              <div class="doc-info">
                <div class="doc-title">{{ currentChapter.title || localCourse.title }}</div>
                <div class="doc-meta">
                  <a-tag color="blue">PDF 文档</a-tag>
                  <span>{{ currentChapter.duration || 30 }} 分钟阅读</span>
                </div>
              </div>
              <div style="margin-left:auto">
                <a-button size="small" type="primary" ghost :href="currentDocUrl" target="_blank">
                  <template #icon><DownloadOutlined /></template>下载文档
                </a-button>
              </div>
            </div>
            <div class="doc-iframe-container">
              <div v-if="docLoading" class="doc-loading">
                <a-spin size="large" />
                <div style="margin-top:12px;color:#888">文档加载中...</div>
              </div>
              <div style="position:absolute;right:12px;top:12px;z-index:3" v-if="!docLoading && !docLoadError">
                <a-button size="small" @click="markDocProgress">标记已学习</a-button>
              </div>
              <iframe
                :src="currentDocUrl"
                class="doc-iframe"
                frameborder="0"
                title="课程文档"
                @load="docLoading = false"
                @error="docLoadError = true"
              ></iframe>
              <div v-if="docLoadError" class="doc-error">
                <div>⚠️ 文档加载失败</div>
                <a :href="currentDocUrl" target="_blank" style="color:var(--police-primary)">↗ 在新标签页中打开文档</a>
              </div>
            </div>
          </div>
        </div>

        <!-- 课程信息 Tabs -->
        <a-card :bordered="false" style="margin-top:16px">
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane key="intro" tab="课程简介">
              <p style="line-height:1.8;color:#444">{{ localCourse.description }}</p>
              <div class="meta-grid">
                <div class="meta-item"><span class="meta-l">主讲教官</span><span>{{ localCourse.instructor || '-' }}</span></div>
                <div class="meta-item"><span class="meta-l">课程时长</span><span>{{ localCourse.duration }} 分钟</span></div>
                <div class="meta-item"><span class="meta-l">课件类型</span><span>{{ isVideo ? '🎬 视频课程' : '📄 文档课程' }}</span></div>
                <div class="meta-item"><span class="meta-l">学员人数</span><span>{{ localCourse.studentCount?.toLocaleString() }} 人</span></div>
              </div>
            </a-tab-pane>
            <a-tab-pane key="notes" tab="笔记">
              <a-textarea v-model:value="noteContent" placeholder="记录学习笔记..." :rows="5" />
              <a-button type="primary" style="margin-top:8px" :loading="noteSaving" @click="handleSaveNote">
                {{ notesSaved ? '✓ 已保存' : '保存笔记' }}
              </a-button>
            </a-tab-pane>
            <a-tab-pane key="qa" tab="答疑区">
              <div class="qa-list" v-if="qaList.length">
                <div class="qa-item" v-for="q in qaList" :key="q.id">
                  <div class="qa-question">
                    <a-avatar size="small" style="background:#003087">{{ (q.user || '?').charAt(0) }}</a-avatar>
                    <span class="qa-user">{{ q.user }}</span>
                    <span class="qa-text">{{ q.question }}</span>
                  </div>
                  <div class="qa-answer" v-if="q.answer">
                    <a-tag color="gold" size="small">教官回复</a-tag>
                    {{ q.answer }}
                  </div>
                </div>
              </div>
              <a-empty v-else description="暂无答疑内容" />
              <a-input-search placeholder="提问..." enter-button="提交" style="margin-top:12px" />
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>

      <!-- 右：章节列表 -->
      <a-col :span="8">
        <a-card :title="isVideo ? '课程章节' : '文档目录'" :bordered="false">
          <div class="chapter-list">
            <div
              v-for="(ch, idx) in localCourse.chapters"
              :key="idx"
              class="chapter-item"
              :class="{ active: currentChapterIdx === idx, locked: ch.locked }"
              @click="selectChapter(idx, ch)"
            >
              <div class="ch-left">
                <div class="ch-num">{{ idx + 1 }}</div>
                <div class="ch-info">
                  <div class="ch-title">{{ ch.title }}</div>
                  <div class="ch-meta">{{ ch.duration }}分钟 · {{ isVideo ? '视频' : '阅读' }}</div>
                </div>
              </div>
              <div class="ch-right">
                <a-progress v-if="!ch.locked && ch.progress > 0 && ch.progress < 100" type="circle" :percent="ch.progress" :width="32" />
                <LockOutlined v-if="ch.locked" style="color:#bbb" />
                <CheckCircleFilled v-if="ch.progress === 100" style="color:#52c41a;font-size:18px" />
              </div>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- ─── 编辑课程弹窗 ─── -->
    <a-modal
      v-model:open="editVisible"
      title="编辑课程"
      :width="700"
      @ok="saveEdit"
      :okText="editSaving ? `保存中 ${editUploadPercent}%` : '保存修改'"
      :confirmLoading="editSaving"
      cancel-text="取消"
      :destroy-on-close="true"
    >
      <a-tabs v-model:activeKey="editTab">
        <!-- Tab1: 基本信息 -->
        <a-tab-pane key="basic" tab="📋 基本信息">
          <a-form :label-col="{ span: 5 }" style="margin-top:12px;padding-right:8px">
            <a-form-item label="课程名称" required>
              <a-input v-model:value="editForm.title" />
            </a-form-item>
            <a-form-item label="课程简介">
              <a-textarea v-model:value="editForm.description" :rows="5" :max-length="500" show-count placeholder="课程简介、学习目标..." />
            </a-form-item>
            <a-form-item label="授课教官">
              <a-select
                v-model:value="editForm.instructorId"
                :options="instructorOptions"
                allow-clear
                placeholder="请选择教官"
                style="width:100%"
              />
            </a-form-item>
            <a-form-item label="难度等级">
              <div style="display:flex;align-items:center;gap:12px">
                <a-rate v-model:value="editForm.difficulty" :count="5" />
                <span style="color:#888;font-size:12px">{{ editDifficultyLabel }}</span>
              </div>
            </a-form-item>
            <a-form-item label="课程标签">
              <a-select v-model:value="editForm.tags" mode="tags" style="width:100%" />
            </a-form-item>
            <a-form-item label="是否必修">
              <a-switch v-model:checked="editForm.isRequired" />
            </a-form-item>
          </a-form>
        </a-tab-pane>

        <!-- Tab2: 章节管理 -->
        <a-tab-pane key="chapters" tab="📚 章节管理">
          <div style="margin-top:12px">
            <div v-for="(ch, idx) in editForm.chapters" :key="idx" class="ch-edit-row">
              <div class="ch-edit-header">
                <span class="ch-badge">第 {{ idx + 1 }} 章</span>
                <a-button
                  v-if="editForm.chapters.length > 1"
                  size="small" danger type="text"
                  @click="editForm.chapters.splice(idx, 1)"
                >
                  <template #icon><DeleteOutlined /></template>删除
                </a-button>
              </div>
              <a-row :gutter="10" style="margin-bottom:6px">
                <a-col :span="16">
                  <a-input v-model:value="ch.title" placeholder="章节名称" />
                </a-col>
                <a-col :span="8">
                  <a-input-number v-model:value="ch.duration" :min="5" style="width:100%" addon-after="分钟" />
                </a-col>
              </a-row>
              <a-upload-dragger
                v-model:fileList="ch.fileList"
                :before-upload="() => false"
                :max-count="1"
                accept=".mp4,.pdf,.pptx,.ppt,.doc,.docx"
                class="chapter-upload"
              >
                <p><InboxOutlined style="font-size:22px;color:#003087" /></p>
                <p style="font-size:12px;margin:2px 0">{{ ch.fileList?.length ? '已选择文件，点击更换' : '点击上传此章节新媒体文件（不上传则保留原文件）' }}</p>
              </a-upload-dragger>
            </div>
            <a-button type="dashed" block @click="editForm.chapters.push({ title: '', duration: 30, fileId: null, fileList: [] })" style="margin-top:12px">
              <template #icon><PlusOutlined /></template>添加章节
            </a-button>
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { LockOutlined, CheckCircleFilled, DownloadOutlined, EditOutlined, DeleteOutlined, InboxOutlined, PlusOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import {
  getCourse,
  updateCourse as apiUpdateCourse,
  deleteCourse as apiDeleteCourse,
  updateChapterProgress,
  getCourseNote,
  saveCourseNote,
} from '@/api/course'
import { getUsers } from '@/api/user'
import { uploadFile } from '@/api/media'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const courseId = route.params.id

// 本地可编辑副本
const localCourse = ref({
  title: '',
  chapters: [],
  fileType: 'video',
  description: '',
  instructor: '',
  instructorId: undefined,
  duration: 0,
  studentCount: 0,
})
const instructorOptions = ref([])

async function fetchInstructors() {
  try {
    const res = await getUsers({ role: 'instructor', size: -1 })
    const items = res.items || []
    instructorOptions.value = items.map(i => ({
      value: i.id,
      label: i.nickname || i.username || `教官#${i.id}`,
    }))
  } catch {
    instructorOptions.value = []
  }
}

async function fetchCourse() {
  const data = await getCourse(courseId)
  localCourse.value = {
    ...data,
    instructor: data.instructor || data.instructorName || '',
    chapters: (data.chapters || []).map(ch => ({
      ...ch,
      progress: ch.progress || 0,
      locked: false,
    })),
  }
  recalcChapterLocks()
}

onMounted(async () => {
  try {
    await Promise.all([fetchInstructors(), fetchCourse(), fetchNote()])
  } catch {
    message.error('加载课程失败')
  }
})

const isVideo = computed(() => (localCourse.value.fileType || 'video') === 'video')

// ─── 章节 ───
const currentChapterIdx = ref(0)
const currentChapter = computed(() => localCourse.value.chapters[currentChapterIdx.value] || {})

const selectChapter = async (idx, ch) => {
  if (ch.locked) return

  const prev = currentChapter.value
  if (prev?.id && isVideo.value && videoRef.value?.duration) {
    const percent = Math.min(100, Math.round((videoRef.value.currentTime / videoRef.value.duration) * 100))
    prev.progress = Math.max(prev.progress || 0, percent)
    try { await updateChapterProgress(courseId, prev.id, percent) } catch { /* ignore */ }
  }

  currentChapterIdx.value = idx
  videoError.value = false
  docLoading.value = true
  docLoadError.value = false
}

// ─── 视频播放器 ───
const videoRef = ref(null)
const playerWrapRef = ref(null)
const isPlaying = ref(false)
const isMuted = ref(false)
const playProgress = ref(0)
const currentTime = ref('00:00')
const totalDuration = ref('--:--')
const videoError = ref(false)
const showPlayIcon = ref(false)

const currentVideoUrl = computed(() => currentChapter.value.fileUrl || currentChapter.value.videoUrl || localCourse.value.videoUrl || '')
const currentDocUrl = computed(() => currentChapter.value.fileUrl || currentChapter.value.docUrl || localCourse.value.docUrl || '')

function recalcChapterLocks() {
  if (!localCourse.value.chapters?.length) return
  localCourse.value.chapters = localCourse.value.chapters.map((item, idx, arr) => {
    if (idx === 0) return { ...item, locked: false }
    return { ...item, locked: !((arr[idx - 1]?.progress || 0) >= 100) }
  })
}

let playIconTimer = null
const togglePlay = () => {
  if (!videoRef.value) return
  if (isPlaying.value) videoRef.value.pause()
  else videoRef.value.play()
  showPlayIcon.value = true
  clearTimeout(playIconTimer)
  playIconTimer = setTimeout(() => { showPlayIcon.value = false }, 700)
}

const toggleMute = () => {
  if (!videoRef.value) return
  isMuted.value = !isMuted.value
  videoRef.value.muted = isMuted.value
}

const formatSeconds = (secs) => {
  if (!secs || isNaN(secs)) return '00:00'
  const m = Math.floor(secs / 60).toString().padStart(2, '0')
  const s = Math.floor(secs % 60).toString().padStart(2, '0')
  return `${m}:${s}`
}

const onMetaLoaded = () => {
  if (!videoRef.value) return
  totalDuration.value = formatSeconds(videoRef.value.duration)
  videoError.value = false
}

const onVideoEnded = async () => {
  isPlaying.value = false
  const ch = currentChapter.value
  if (!ch?.id) return
  try {
    await updateChapterProgress(courseId, ch.id, 100)
    ch.progress = 100
    recalcChapterLocks()
  } catch {
    // ignore
  }
}

let lastProgressAt = 0
const onTimeUpdate = async () => {
  if (!videoRef.value) return
  const video = videoRef.value
  const total = video.duration || 0
  playProgress.value = total > 0 ? (video.currentTime / total) * 100 : 0
  currentTime.value = formatSeconds(video.currentTime)

  const now = Date.now()
  const ch = currentChapter.value
  if (!ch?.id || total <= 0 || now - lastProgressAt < 5000) return

  lastProgressAt = now
  const percent = Math.min(100, Math.round((video.currentTime / total) * 100))
  ch.progress = Math.max(ch.progress || 0, percent)
  try { await updateChapterProgress(courseId, ch.id, percent) } catch { /* ignore */ }
}

const seekVideo = (e) => {
  if (!videoRef.value) return
  const rect = e.currentTarget.getBoundingClientRect()
  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
  videoRef.value.currentTime = ratio * (videoRef.value.duration || 0)
}

const markDocProgress = async () => {
  const ch = currentChapter.value
  if (!ch?.id) return
  const nextProgress = Math.max(ch.progress || 0, 100)
  ch.progress = nextProgress
  try {
    await updateChapterProgress(courseId, ch.id, nextProgress)
    recalcChapterLocks()
    message.success('已标记本章完成')
  } catch {
    message.warning('进度保存失败，请稍后重试')
  }
}

const enterFullscreen = () => {
  const el = playerWrapRef.value || videoRef.value
  if (el?.requestFullscreen) el.requestFullscreen()
  else if (el?.webkitRequestFullscreen) el.webkitRequestFullscreen()
}

watch(currentChapterIdx, () => {
  nextTick(() => {
    if (videoRef.value) {
      videoRef.value.pause()
      videoRef.value.currentTime = 0
      isPlaying.value = false
      playProgress.value = 0
      currentTime.value = '00:00'
      totalDuration.value = '--:--'
    }
  })
})

// ─── 文档 ───
const docLoading = ref(true)
const docLoadError = ref(false)

// ─── 通用 ───
const activeTab = ref('intro')
const notesSaved = ref(false)
const qaList = ref([])

const noteContent = ref('')
const noteSaving = ref(false)

async function fetchNote() {
  try {
    const res = await getCourseNote(courseId)
    noteContent.value = res?.content || ''
  } catch {
    const cacheKey = `course_note_${authStore.currentUser?.id || 'guest'}_${courseId}`
    noteContent.value = localStorage.getItem(cacheKey) || ''
  }
}

async function handleSaveNote() {
  noteSaving.value = true
  try {
    const res = await saveCourseNote(courseId, noteContent.value || '')
    noteContent.value = res?.content || ''
    const cacheKey = `course_note_${authStore.currentUser?.id || 'guest'}_${courseId}`
    localStorage.setItem(cacheKey, noteContent.value)
    notesSaved.value = true
    setTimeout(() => { notesSaved.value = false }, 2000)
  } catch (e) {
    const cacheKey = `course_note_${authStore.currentUser?.id || 'guest'}_${courseId}`
    localStorage.setItem(cacheKey, noteContent.value)
    notesSaved.value = true
    setTimeout(() => { notesSaved.value = false }, 2000)
    message.warning(e.message || '笔记已暂存到本地')
  } finally {
    noteSaving.value = false
  }
}

// ─── 编辑弹窗 ───
const editVisible = ref(false)
const editTab = ref('basic')

const editForm = reactive({
  title: '',
  description: '',
  instructorId: undefined,
  difficulty: 3,
  tags: [],
  isRequired: false,
  chapters: [],
})

const editDifficultyLabel = computed(() => {
  const labels = ['', '初级', '初中级', '中级', '中高级', '高级']
  return labels[Math.round(editForm.difficulty)] || ''
})

const openEdit = () => {
  const c = localCourse.value
  editForm.title = c.title
  editForm.description = c.description || ''
  editForm.instructorId = c.instructorId
  editForm.difficulty = c.difficulty || 3
  editForm.tags = [...(c.tags || [])]
  editForm.isRequired = !!c.isRequired
  editForm.chapters = (c.chapters || []).map(ch => ({
    title: ch.title,
    duration: ch.duration || 30,
    fileId: ch.fileId || null,
    fileList: [],
  }))
  editTab.value = 'basic'
  editVisible.value = true
}

const editSaving = ref(false)
const editUploadPercent = ref(0)
let lastEditSubmitAt = 0

const saveEdit = async () => {
  const now = Date.now()
  if (editSaving.value || now - lastEditSubmitAt < 800) return
  lastEditSubmitAt = now
  if (!editForm.title.trim()) return message.warning('课程名称不能为空')
  if (editForm.chapters.some(ch => !ch.title.trim())) return message.warning('章节名称不能为空')

  editSaving.value = true
  try {
    // 上传新文件并构建章节数据
    const newChapters = []
    const uploadTargets = editForm.chapters.filter(ch => ch.fileList?.length > 0).length
    let uploadedCount = 0
    editUploadPercent.value = 0

    for (let idx = 0; idx < editForm.chapters.length; idx++) {
      const ch = editForm.chapters[idx]
      const existing = localCourse.value.chapters[idx] || {}
      let fileId = ch.fileId || existing.fileId || null

      if (ch.fileList?.length > 0) {
        const rawFile = ch.fileList[0].originFileObj || ch.fileList[0]
        if (rawFile && rawFile.name) {
          const fileRes = await uploadFile(rawFile, (percent) => {
            editUploadPercent.value = Math.round(((uploadedCount + percent / 100) / (uploadTargets || 1)) * 100)
          })
          fileId = fileRes.id
          uploadedCount += 1
          editUploadPercent.value = Math.round((uploadedCount / (uploadTargets || 1)) * 100)
        }
      }

      newChapters.push({
        title: ch.title,
        sortOrder: idx,
        duration: ch.duration || 30,
        fileId,
      })
    }

    const courseData = {
      title: editForm.title,
      description: editForm.description,
      instructorId: editForm.instructorId,
      difficulty: editForm.difficulty,
      tags: editForm.tags,
      isRequired: editForm.isRequired,
      duration: newChapters.reduce((s, c) => s + (Number(c.duration) || 0), 0),
      chapters: newChapters,
    }

    await apiUpdateCourse(courseId, courseData)

    await Promise.all([fetchCourse(), fetchNote()])

    if (currentChapterIdx.value >= localCourse.value.chapters.length) {
      currentChapterIdx.value = 0
    }

    editVisible.value = false
    message.success('课程信息已更新')
  } catch (e) {
    message.error(e.message || '保存失败')
  } finally {
    editSaving.value = false
    editUploadPercent.value = 0
  }
}

const handleDeleteCourse = async () => {
  try {
    await apiDeleteCourse(courseId)
    message.success('课程已删除')
    router.push('/courses')
  } catch (err) {
    message.error(err.message || '删除失败')
  }
}
</script>

<style scoped>
.course-detail-page { padding: 0; }

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

/* ─── 视频播放器 ─── */
.video-player-wrap { background: #000; border-radius: 8px; overflow: hidden; }
.video-player { position: relative; }
.course-video { width: 100%; height: 400px; display: block; object-fit: contain; background: #000; }
.video-click-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 48px; cursor: pointer; z-index: 2; }
.video-error-mask { position: absolute; inset: 0; background: linear-gradient(135deg, #001236, #003087); display: flex; flex-direction: column; align-items: center; justify-content: center; color: rgba(255,255,255,0.8); font-size: 15px; z-index: 5; }
.play-center-icon { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 52px; color: rgba(255,255,255,0.85); background: rgba(0,0,0,0.35); width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; z-index: 3; pointer-events: none; }
.fade-enter-active { transition: opacity 0.15s; }
.fade-leave-active { transition: opacity 0.5s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.chapter-badge-wrap { position: absolute; bottom: 60px; left: 14px; z-index: 4; pointer-events: none; }
.chapter-badge { background: rgba(0,0,0,0.55); color: #fff; padding: 4px 12px; border-radius: 4px; font-size: 13px; backdrop-filter: blur(4px); }
.video-controls { background: rgba(0,0,0,0.85); padding: 8px 14px; display: flex; align-items: center; gap: 12px; position: relative; z-index: 10; }
.controls-left { display: flex; align-items: center; gap: 8px; }
.ctrl-btn { background: transparent; border: none; color: #fff; font-size: 17px; cursor: pointer; padding: 4px 8px; border-radius: 4px; transition: background 0.2s; }
.ctrl-btn:hover { background: rgba(255,255,255,0.15); }
.time-display { color: #bbb; font-size: 12px; white-space: nowrap; min-width: 90px; }
.progress-bar-wrap { flex: 1; padding: 8px 0; cursor: pointer; position: relative; }
.progress-bar-bg { height: 4px; background: rgba(255,255,255,0.2); border-radius: 2px; position: relative; }
.progress-bar-fill { height: 100%; background: linear-gradient(90deg, #003087, #c8a84b); border-radius: 2px; transition: width 0.1s linear; }
.progress-handle { position: absolute; top: 50%; transform: translate(-50%, -50%); width: 12px; height: 12px; border-radius: 50%; background: #c8a84b; transition: left 0.1s linear; pointer-events: none; }
.controls-right { display: flex; align-items: center; gap: 4px; white-space: nowrap; }

/* ─── 文档查看器 ─── */
.doc-viewer-wrap { border-radius: 8px; overflow: hidden; border: 1px solid #e8e8e8; }
.doc-viewer { background: #fff; }
.doc-header { display: flex; align-items: center; gap: 14px; padding: 16px 20px; background: linear-gradient(135deg, #f0f5ff, #e8f0fe); border-bottom: 1px solid #d0e0ff; }
.doc-icon { font-size: 40px; }
.doc-title { font-size: 17px; font-weight: 600; color: #001234; margin-bottom: 4px; }
.doc-meta { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #888; }
.doc-iframe-container { position: relative; height: 520px; background: #f5f5f5; }
.doc-loading { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #f9fafc; z-index: 2; }
.doc-iframe { width: 100%; height: 100%; border: none; display: block; }
.doc-error { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; font-size: 15px; color: #888; background: #fafafa; }

/* ─── 通用 ─── */
.meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }
.meta-item { display: flex; gap: 8px; font-size: 13px; }
.meta-l { color: #888; min-width: 60px; }
.chapter-list { display: flex; flex-direction: column; gap: 8px; max-height: 500px; overflow-y: auto; }
.chapter-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; border-radius: 6px; cursor: pointer; transition: all 0.2s; border: 1px solid transparent; }
.chapter-item:hover:not(.locked) { background: #f0f5ff; border-color: #d0e0ff; }
.chapter-item.active { background: #e8f0fe; border-color: var(--police-primary); }
.chapter-item.locked { opacity: 0.5; cursor: not-allowed; }
.ch-left { display: flex; align-items: center; gap: 10px; flex: 1; }
.ch-num { width: 24px; height: 24px; border-radius: 50%; background: var(--police-primary); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; }
.chapter-item.active .ch-num { background: var(--police-gold, #c8a84b); }
.ch-title { font-size: 13px; font-weight: 500; color: #333; }
.ch-meta { font-size: 11px; color: #888; }
.qa-list { display: flex; flex-direction: column; gap: 12px; }
.qa-item { border-left: 3px solid var(--police-primary); padding-left: 12px; }
.qa-question { display: flex; align-items: center; gap: 8px; }
.qa-user { font-size: 12px; color: #888; }
.qa-text { font-size: 13px; color: #333; }
.qa-answer { margin-top: 6px; font-size: 13px; color: #555; background: #fffbe6; padding: 6px 10px; border-radius: 4px; }

/* ─── 编辑弹窗章节 ─── */
.ch-edit-row { border: 1px solid #e8e8e8; border-radius: 6px; padding: 12px; margin-bottom: 10px; background: #fafbfc; }
.ch-edit-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.ch-badge { background: var(--police-primary, #003087); color: #fff; font-size: 11px; font-weight: 600; padding: 2px 10px; border-radius: 10px; }
.chapter-upload :deep(.ant-upload.ant-upload-drag) { padding: 6px 0; }

@media (max-width: 768px) {
  .course-video { height: 240px !important; }
  .doc-iframe-container { height: 340px !important; }
  .meta-grid { grid-template-columns: 1fr !important; }
  .video-controls { flex-wrap: wrap; gap: 8px; justify-content: space-between; }
  .progress-bar-wrap { width: 100%; order: -1; padding: 4px 0; }
}
</style>
