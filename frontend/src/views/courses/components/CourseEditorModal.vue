<template>
  <a-modal
    :open="open"
    :title="isEditing ? '编辑课程' : '上传新课程'"
    :width="760"
    :footer="null"
    :confirm-loading="submitting"
    :destroy-on-close="true"
    @cancel="handleClose"
  >
    <a-spin :spinning="loading">
      <a-steps :current="currentStep" size="small" style="margin: 12px 0 24px">
        <a-step title="基本信息" description="名称、主讲教官、标签" />
        <a-step title="章节管理" description="章节、文件、学习时长" />
      </a-steps>

      <div v-show="currentStep === 0">
        <a-form :label-col="{ span: 5 }" style="padding-right: 8px">
          <a-form-item label="课程名称" required>
            <a-input v-model:value="form.title" placeholder="请输入课程名称" />
          </a-form-item>
          <a-form-item label="课程分类" required>
            <a-select v-model:value="form.category" placeholder="选择分类" allow-clear style="width: 100%">
              <a-select-option
                v-for="cat in courseCategories"
                :key="cat.key"
                :value="cat.key"
              >
                {{ cat.label }}
              </a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="课程简介">
            <a-textarea
              v-model:value="form.description"
              :rows="4"
              :max-length="500"
              show-count
              placeholder="请输入课程简介：学习目标、适用对象、主要内容..."
            />
          </a-form-item>
          <a-form-item label="主讲教官">
            <a-select
              v-model:value="form.instructorId"
              :options="instructorOptions"
              allow-clear
              placeholder="请选择主讲教官"
              style="width: 100%"
            />
          </a-form-item>
          <a-form-item label="难度等级">
            <div style="display: flex; align-items: center; gap: 12px">
              <a-rate v-model:value="form.difficulty" :count="5" />
              <span style="color: #888; font-size: 12px">{{ difficultyLabel }}</span>
            </div>
          </a-form-item>
          <a-form-item label="课程标签">
            <a-select
              v-model:value="form.tags"
              mode="tags"
              show-search
              :options="mergedTagOptions"
              :filter-option="false"
              :loading="tagSearching"
              placeholder="支持搜索已有标签，输入后回车可直接创建新标签"
              style="width: 100%"
              @search="handleTagSearch"
              @change="handleTagChange"
            />
          </a-form-item>
          <a-form-item label="是否必修">
            <a-switch v-model:checked="form.isRequired" />
          </a-form-item>
        </a-form>
      </div>

      <div v-show="currentStep === 1" class="chapters-editor">
        <a-alert
          type="info"
          show-icon
          message="视频章节会自动读取视频时长并锁定时长输入；文档章节继续手动填写学习时长。"
          style="margin-bottom: 16px; font-size: 12px"
        />
        <div v-for="(chapter, idx) in form.chapters" :key="chapter.localKey" class="chapter-row">
          <div class="chapter-header">
            <span class="chapter-badge">第 {{ idx + 1 }} 章</span>
            <a-button
              v-if="form.chapters.length > 1"
              size="small"
              danger
              type="text"
              @click="removeChapter(idx)"
            >
              <template #icon><DeleteOutlined /></template>删除
            </a-button>
          </div>

          <a-row :gutter="10" style="margin-bottom: 8px">
            <a-col :span="15">
              <a-input
                v-model:value="chapter.title"
                :placeholder="`章节名称，如：第${idx + 1}章`"
              />
            </a-col>
            <a-col :span="9">
              <a-input-number
                v-model:value="chapter.duration"
                :min="1"
                :max="600"
                :disabled="isVideoChapter(chapter)"
                style="width: 100%"
                addon-after="分钟"
              />
            </a-col>
          </a-row>

          <div class="chapter-meta">
            <span v-if="isVideoChapter(chapter)" class="chapter-meta-item video">
              视频章节：学习时长按视频时长自动换算
            </span>
            <span v-else class="chapter-meta-item doc">
              文档章节：请手动填写建议学习时长
            </span>
            <span v-if="chapter.fileList.length === 0 && (chapter.fileId || chapter.resourceId)" class="chapter-meta-item">
              当前已保留原文件，重新上传会覆盖原文件引用
            </span>
          </div>

          <a-upload-dragger
            :file-list="chapter.fileList"
            :before-upload="() => false"
            :max-count="1"
            accept=".mp4,.pdf,.ppt,.pptx,.doc,.docx"
            class="chapter-upload"
            @change="(info) => handleChapterFileChange(idx, info)"
          >
            <p><InboxOutlined style="font-size: 24px; color: #003087" /></p>
            <p style="font-size: 13px; font-weight: 500; margin: 4px 0">
              {{ chapter.fileList.length ? '已选择文件，点击可更换' : '点击或拖拽上传此章节文件' }}
            </p>
            <p style="font-size: 11px; color: #aaa">支持 MP4 / PDF / PPT / DOC，单文件 ≤ 500MB</p>
          </a-upload-dragger>
        </div>

        <a-button type="dashed" block style="margin-top: 16px" @click="addChapter">
          <template #icon><PlusOutlined /></template>添加章节
        </a-button>
      </div>

      <div class="modal-footer">
        <a-button @click="handleClose">取消</a-button>
        <div style="display: flex; gap: 8px">
          <a-button v-if="currentStep > 0" @click="currentStep -= 1">上一步</a-button>
          <a-button v-if="currentStep < 1" type="primary" @click="goNextStep">下一步</a-button>
          <a-button
            v-if="currentStep === 1"
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
          >
            {{ submitting ? `提交中 ${uploadPercent}%` : (isEditing ? '保存修改' : '提交课程') }}
          </a-button>
        </div>
      </div>
    </a-spin>
  </a-modal>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { DeleteOutlined, InboxOutlined, PlusOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { createCourse, createCourseTag, getCourse, getCourseTags, updateCourse } from '@/api/course'
import { uploadFile } from '@/api/media'
import { getUsers } from '@/api/user'
import { COURSE_CATEGORIES } from '@/mock/courses'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  courseId: {
    type: [Number, String],
    default: null,
  },
})

const emit = defineEmits(['update:open', 'success'])

const courseCategories = COURSE_CATEGORIES.filter((item) => item.key !== 'all')
const categoryColorMap = {
  law: '#003087',
  fraud: '#8B1A1A',
  traffic: '#0A6640',
  community: '#4A3728',
  cybersec: '#1A0A4A',
  physical: '#2D4A1A',
}

const loading = ref(false)
const submitting = ref(false)
const uploadPercent = ref(0)
const currentStep = ref(0)
const instructorOptions = ref([])
const tagOptions = ref([])
const tagSearching = ref(false)
let chapterSeed = 0
let tagSearchTimer = null
const creatingTagNames = new Set()
const knownTagNames = new Set()

const form = reactive({
  title: '',
  category: null,
  description: '',
  instructorId: undefined,
  difficulty: 3,
  tags: [],
  isRequired: false,
  chapters: [],
})

const isEditing = computed(() => props.courseId !== null && props.courseId !== undefined && props.courseId !== '')
const difficultyLabel = computed(() => {
  const labels = ['', '初级', '初中级', '中级', '中高级', '高级']
  return labels[Math.round(form.difficulty)] || ''
})
const mergedTagOptions = computed(() => {
  const values = new Set([
    ...tagOptions.value.map((item) => item.value),
    ...(form.tags || []).map((item) => String(item || '').trim()).filter(Boolean),
  ])
  return Array.from(values).map((value) => ({ value, label: value }))
})

function createChapter(overrides = {}) {
  chapterSeed += 1
  return {
    localKey: `chapter-${chapterSeed}`,
    id: overrides.id ?? undefined,
    title: overrides.title ?? '',
    duration: overrides.duration ?? 30,
    originalDuration: overrides.duration ?? 30,
    fileId: overrides.fileId ?? null,
    resourceId: overrides.resourceId ?? null,
    fileUrl: overrides.fileUrl ?? '',
    contentType: overrides.contentType ?? null,
    originalContentType: overrides.contentType ?? null,
    fileList: [],
  }
}

function resetForm() {
  form.title = ''
  form.category = null
  form.description = ''
  form.instructorId = undefined
  form.difficulty = 3
  form.tags = []
  form.isRequired = false
  form.chapters = [createChapter()]
}

function normalizeTags(tags) {
  const seen = new Set()
  return (tags || [])
    .map((item) => String(item || '').trim())
    .filter((item) => {
      if (!item || seen.has(item)) {
        return false
      }
      seen.add(item)
      return true
    })
}

function rememberTagNames(names) {
  const normalizedTags = normalizeTags(names)
  normalizedTags.forEach((name) => {
    knownTagNames.add(name)
  })
  tagOptions.value = normalizeTags([
    ...tagOptions.value.map((item) => item.value),
    ...normalizedTags,
  ]).map((value) => ({ value, label: value }))
}

function detectContentType(fileName = '', mimeType = '') {
  const lowerName = String(fileName || '').toLowerCase()
  const lowerMime = String(mimeType || '').toLowerCase()
  if (lowerMime.includes('video') || lowerName.endsWith('.mp4')) {
    return 'video'
  }
  if (
    lowerMime.includes('pdf')
    || lowerName.endsWith('.pdf')
    || lowerName.endsWith('.ppt')
    || lowerName.endsWith('.pptx')
    || lowerName.endsWith('.doc')
    || lowerName.endsWith('.docx')
  ) {
    return 'document'
  }
  return null
}

function isVideoChapter(chapter) {
  return chapter.contentType === 'video'
}

function readVideoDuration(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const video = document.createElement('video')
    video.preload = 'metadata'
    video.onloadedmetadata = () => {
      const seconds = Number(video.duration || 0)
      URL.revokeObjectURL(url)
      if (!seconds) {
        reject(new Error('无法读取视频时长'))
        return
      }
      resolve(Math.max(1, Math.ceil(seconds / 60)))
    }
    video.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('视频元数据读取失败'))
    }
    video.src = url
  })
}

async function ensureOptionsLoaded() {
  const [instructorResult, tagResult] = await Promise.allSettled([
    getUsers({ role: 'instructor', size: -1 }),
    getCourseTags(),
  ])

  if (instructorResult.status === 'fulfilled') {
    const items = instructorResult.value.items || instructorResult.value || []
    instructorOptions.value = items.map((item) => ({
      value: item.id,
      label: item.nickname || item.username || `教官#${item.id}`,
    }))
  } else {
    instructorOptions.value = []
  }

  if (tagResult.status === 'fulfilled') {
    const items = tagResult.value || []
    rememberTagNames(items.map((item) => item.name))
  } else {
    tagOptions.value = []
  }
}

async function fetchTagOptions(search = '') {
  tagSearching.value = true
  try {
    const items = await getCourseTags({
      search: search?.trim() || undefined,
    })
    const names = (items || []).map((item) => item.name)
    rememberTagNames(names)
    if (search?.trim()) {
      tagOptions.value = normalizeTags([
        ...form.tags,
        ...names,
      ]).map((value) => ({ value, label: value }))
    }
  } finally {
    tagSearching.value = false
  }
}

function handleTagSearch(value) {
  clearTimeout(tagSearchTimer)
  tagSearchTimer = setTimeout(() => {
    fetchTagOptions(value).catch(() => {})
  }, 250)
}

async function handleTagChange(values) {
  const normalizedTags = normalizeTags(values)
  form.tags = normalizedTags

  const missingTagNames = normalizedTags.filter(
    (name) => !knownTagNames.has(name) && !creatingTagNames.has(name),
  )

  for (const tagName of missingTagNames) {
    creatingTagNames.add(tagName)
    try {
      const createdTag = await createCourseTag({ name: tagName })
      rememberTagNames([createdTag.name])
      form.tags = normalizeTags([...form.tags, createdTag.name])
    } catch (error) {
      form.tags = form.tags.filter((item) => item !== tagName)
      message.error(error?.message || `标签“${tagName}”创建失败`)
    } finally {
      creatingTagNames.delete(tagName)
    }
  }
}

async function loadCourseDetail() {
  const course = await getCourse(props.courseId)
  form.title = course.title || ''
  form.category = course.category || null
  form.description = course.description || ''
  form.instructorId = course.instructorId ?? undefined
  form.difficulty = course.difficulty || 3
  form.tags = normalizeTags(course.tags)
  form.isRequired = !!course.isRequired
  form.chapters = (course.chapters || [])
    .slice()
    .sort((a, b) => (a.sortOrder || 0) - (b.sortOrder || 0))
    .map((chapter) => createChapter({
      id: chapter.id,
      title: chapter.title,
      duration: chapter.duration || 30,
      fileId: chapter.fileId || null,
      resourceId: chapter.resourceId || null,
      fileUrl: chapter.fileUrl || '',
      contentType: chapter.contentType || detectContentType(chapter.fileUrl || chapter.videoUrl || chapter.docUrl || ''),
    }))
  if (!form.chapters.length) {
    form.chapters = [createChapter()]
  }
}

async function initializeModal() {
  loading.value = true
  currentStep.value = 0
  try {
    await ensureOptionsLoaded()
    if (isEditing.value) {
      await loadCourseDetail()
    } else {
      resetForm()
    }
  } catch (error) {
    message.error(error?.message || '课程表单初始化失败')
    emit('update:open', false)
  } finally {
    loading.value = false
  }
}

watch(
  () => props.open,
  (visible) => {
    if (visible) {
      initializeModal()
    }
  },
)

function handleClose() {
  if (submitting.value) {
    return
  }
  emit('update:open', false)
}

function goNextStep() {
  if (!form.title.trim()) {
    message.warning('请输入课程名称')
    return
  }
  if (!form.category) {
    message.warning('请选择课程分类')
    return
  }
  currentStep.value = 1
}

function addChapter() {
  form.chapters.push(createChapter())
}

function removeChapter(index) {
  form.chapters.splice(index, 1)
}

async function handleChapterFileChange(index, info) {
  const chapter = form.chapters[index]
  if (!chapter) {
    return
  }

  chapter.fileList = (info?.fileList || []).slice(-1)
  if (!chapter.fileList.length) {
    chapter.contentType = chapter.originalContentType
    chapter.duration = chapter.originalDuration
    return
  }

  const rawFile = chapter.fileList[0].originFileObj || chapter.fileList[0]
  const contentType = detectContentType(rawFile?.name, rawFile?.type)
  chapter.contentType = contentType

  if (contentType === 'video') {
    try {
      chapter.duration = await readVideoDuration(rawFile)
    } catch (error) {
      chapter.duration = chapter.duration || 1
      message.warning(error?.message || '读取视频时长失败，请重新选择视频')
    }
  }
}

async function handleSubmit() {
  if (!form.title.trim()) {
    message.warning('请输入课程名称')
    return
  }
  if (!form.category) {
    message.warning('请选择课程分类')
    return
  }
  if (form.chapters.some((chapter) => !chapter.title.trim())) {
    message.warning('请填写所有章节名称')
    return
  }
  if (form.chapters.some((chapter) => !chapter.fileList.length && !chapter.fileId && !chapter.resourceId)) {
    message.warning('每个章节都需要上传文件或保留已有文件')
    return
  }

  submitting.value = true
  uploadPercent.value = 0

  try {
    const uploadTargets = form.chapters.filter((chapter) => chapter.fileList.length > 0).length
    let uploadedCount = 0
    const chapters = []

    for (let index = 0; index < form.chapters.length; index += 1) {
      const chapter = form.chapters[index]
      let fileId = chapter.fileId || null
      let resourceId = chapter.resourceId || null
      let contentType = chapter.contentType

      if (chapter.fileList.length > 0) {
        const rawFile = chapter.fileList[0].originFileObj || chapter.fileList[0]
        contentType = detectContentType(rawFile?.name, rawFile?.type)
        const fileResult = await uploadFile(rawFile, (percent) => {
          uploadPercent.value = Math.round(((uploadedCount + percent / 100) / (uploadTargets || 1)) * 100)
        })
        fileId = fileResult.id
        resourceId = null
        uploadedCount += 1
        uploadPercent.value = Math.round((uploadedCount / (uploadTargets || 1)) * 100)
      }

      chapters.push({
        id: chapter.id,
        title: chapter.title.trim(),
        sortOrder: index,
        duration: Math.max(1, Number(chapter.duration) || 0),
        fileId,
        resourceId,
        contentType,
      })
    }

    const totalDuration = chapters.reduce((sum, chapter) => sum + (Number(chapter.duration) || 0), 0)
    const normalizedTags = normalizeTags(form.tags)
    const hasVideo = form.chapters.some((chapter) => isVideoChapter(chapter))
    const payload = {
      title: form.title.trim(),
      category: form.category,
      description: form.description?.trim() || '',
      instructorId: form.instructorId ?? null,
      difficulty: form.difficulty,
      tags: normalizedTags,
      isRequired: form.isRequired,
      fileType: hasVideo ? 'video' : 'document',
      coverColor: categoryColorMap[form.category] || '#003087',
      duration: totalDuration,
      chapters,
    }

    const result = isEditing.value
      ? await updateCourse(props.courseId, payload)
      : await createCourse(payload)

    message.success(isEditing.value ? '课程修改成功' : '课程创建成功')
    emit('success', result)
    emit('update:open', false)
  } catch (error) {
    message.error(error?.message || '课程保存失败')
  } finally {
    submitting.value = false
    uploadPercent.value = 0
  }
}
</script>

<style scoped>
.chapters-editor {
  min-height: 240px;
}

.chapter-row {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 12px;
  background: #fafbfc;
}

.chapter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.chapter-badge {
  background: var(--police-primary, #003087);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
}

.chapter-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.chapter-meta-item {
  font-size: 12px;
  color: #666;
}

.chapter-meta-item.video {
  color: #003087;
}

.chapter-meta-item.doc {
  color: #8b6d00;
}

.chapter-upload :deep(.ant-upload.ant-upload-drag) {
  padding: 8px 0;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 20px;
  margin-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>
