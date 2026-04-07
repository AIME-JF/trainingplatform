<template>
  <a-modal
    :open="open"
    :title="isEditing ? '编辑课程' : '创建课程'"
    :width="780"
    :footer="null"
    :confirm-loading="submitting"
    :destroy-on-close="true"
    @cancel="handleClose"
  >
    <a-spin :spinning="loading">
      <a-steps :current="currentStep" size="small" style="margin: 12px 0 24px">
        <a-step title="基本信息" description="名称、主讲教官、标签" />
        <a-step title="章节资源" description="章节、资源、文件" />
      </a-steps>

      <div v-show="currentStep === 0">
        <a-alert
          type="info"
          show-icon
          message="系统管理员可先创建不含章节的课程，后续再由任课教官补充章节与资源。"
          style="margin-bottom: 16px; font-size: 12px"
        />
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
          <a-form-item label="可见范围">
            <AdmissionScopeSelector
              v-model:scope-type="form.scopeType"
              v-model:scope-target-ids="form.scopeTargetIds"
              :user-role="''"
              all-hint="全体用户都可以查看该课程。"
              user-placeholder="请选择可查看课程的用户"
              department-placeholder="请选择可查看课程的部门"
              role-placeholder="请选择可查看课程的角色"
              user-hint="仅选中的用户可以查看该课程。"
              department-hint="选中部门下的用户可以查看该课程。"
              role-hint="拥有选中角色的用户可以查看该课程。"
            />
          </a-form-item>
        </a-form>
      </div>

      <div v-show="currentStep === 1" class="chapters-editor">
        <a-alert
          type="info"
          show-icon
          message="可先创建不含章节的课程，后续再由任课教官补充章节与资源；已添加章节时，每章仍需绑定自己的资源。"
          style="margin-bottom: 16px; font-size: 12px"
        />
        <a-alert
          v-if="!resourceListLoading && !resourceOptions.length"
          type="warning"
          show-icon
          message="当前账号下暂无资源。请先在【知识库】导入文件或创建知识点，再回来配置课程章节。"
          style="margin-bottom: 16px; font-size: 12px"
        />

        <div v-if="!form.chapters.length" class="chapter-empty-state">
          <a-empty description="当前还没有章节。系统管理员可以先创建课程，后续再由任课教官补充章节资源。" />
        </div>

        <template v-else>
          <CourseChapterResourceSelector
            v-for="(chapter, idx) in form.chapters"
            :key="chapter.localKey"
            :chapter="chapter"
            :index="idx"
            :can-remove="canRemoveChapter(chapter)"
            :resource-options="resourceOptions"
            :resource-loading="resourceListLoading"
            :file-options="getChapterFileOptions(chapter)"
            :file-loading="isChapterFileLoading(chapter)"
            @remove="removeChapter(idx)"
            @change-resource="(value) => handleChapterResourceChange(idx, value)"
            @change-file="(value) => handleChapterFileChange(idx, value)"
          />
        </template>

        <a-button type="dashed" block style="margin-top: 16px" @click="addChapter">
          <template #icon><PlusOutlined /></template>{{ form.chapters.length ? '添加章节' : '添加第一章' }}
        </a-button>
      </div>

      <div class="modal-footer">
        <a-button @click="handleClose">取消</a-button>
        <div style="display: flex; gap: 8px">
          <a-button v-if="currentStep > 0" @click="currentStep -= 1">上一步</a-button>
          <a-button v-if="currentStep < 1" :loading="submitting" @click="handleSubmit">
            {{ isEditing ? '仅保存基本信息' : '先跳过，直接创建' }}
          </a-button>
          <a-button v-if="currentStep < 1" type="primary" @click="goNextStep">下一步</a-button>
          <a-button
            v-if="currentStep === 1"
            type="primary"
            :loading="submitting"
            @click="handleSubmit"
          >
            {{ submitting ? '提交中' : (isEditing ? '保存修改' : '创建课程') }}
          </a-button>
        </div>
      </div>
    </a-spin>
  </a-modal>
</template>

<script setup>
import { computed, reactive, ref, toRef, watch } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { createCourse, createCourseTag, getCourse, getCourseTags, updateCourse } from '@/api/course'
import { getLibraryItem, getLibraryItems } from '@/api/library'
import { getUsers } from '@/api/user'
import AdmissionScopeSelector from '@/views/exam/components/AdmissionScopeSelector.vue'
import { useCreatableTagSelect } from '@/utils/creatableTagSelect'

const COURSE_CATEGORIES = [
  { key: 'law', label: '法律法规' },
  { key: 'fraud', label: '专项业务' },
  { key: 'traffic', label: '交通管理' },
  { key: 'community', label: '基层警务' },
  { key: 'cybersec', label: '科技应用' },
  { key: 'physical', label: '体能技能' },
]
import CourseChapterResourceSelector from './CourseChapterResourceSelector.vue'

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

const courseCategories = COURSE_CATEGORIES
const categoryColorMap = {
  law: '#003087',
  fraud: '#8B1A1A',
  traffic: '#0A6640',
  community: '#4A3728',
  cybersec: '#1A0A4A',
  physical: '#2D4A1A',
}
const resourceTypeLabels = {
  video: '视频',
  document: '文档',
  image: '图片',
  image_text: '图文',
  audio: '音频',
  knowledge: '知识点',
  mixed: '混合',
}

const loading = ref(false)
const submitting = ref(false)
const currentStep = ref(0)
const instructorOptions = ref([])
const resourceListLoading = ref(false)
const resourceOptions = ref([])
const resourceDetailCache = reactive({})
const resourceDetailLoading = reactive({})
let chapterSeed = 0

const form = reactive({
  title: '',
  category: null,
  description: '',
  instructorId: undefined,
  tags: [],
  isRequired: false,
  scopeType: 'all',
  scopeTargetIds: [],
  chapters: [],
})
const formTagsRef = toRef(form, 'tags')
const {
  tagSearching,
  mergedTagOptions,
  normalizeTags,
  fetchTagOptions: loadTagOptions,
  handleTagSearch,
  handleTagChange,
} = useCreatableTagSelect(formTagsRef, {
  fetchTags: getCourseTags,
  createTag: createCourseTag,
  createErrorMessage: (tagName, error) => error?.message || `标签“${tagName}”创建失败`,
})

const isEditing = computed(() => props.courseId !== null && props.courseId !== undefined && props.courseId !== '')

function createChapter(overrides = {}) {
  chapterSeed += 1
  return {
    localKey: `chapter-${chapterSeed}`,
    id: overrides.id ?? undefined,
    title: overrides.title ?? '',
    fileId: overrides.fileId ?? null,
    resourceId: overrides.resourceId ?? null,
    legacyResourceId: overrides.legacyResourceId ?? null,
    fileUrl: overrides.fileUrl ?? '',
    contentType: overrides.contentType ?? null,
    resourceTitle: overrides.resourceTitle ?? '',
    resourceFileName: overrides.resourceFileName ?? '',
    resourceFileLabel: overrides.resourceFileLabel ?? '',
    legacyFileOnly: overrides.legacyFileOnly ?? false,
    originalLegacyFileOnly: overrides.legacyFileOnly ?? false,
    originalFileId: overrides.fileId ?? null,
    originalResourceId: overrides.resourceId ?? null,
    originalLegacyResourceId: overrides.legacyResourceId ?? null,
    originalContentType: overrides.contentType ?? null,
    originalResourceTitle: overrides.resourceTitle ?? '',
    originalResourceFileName: overrides.resourceFileName ?? '',
    originalResourceFileLabel: overrides.resourceFileLabel ?? '',
  }
}

function resetForm() {
  form.title = ''
  form.category = null
  form.description = ''
  form.instructorId = undefined
  form.tags = []
  form.isRequired = false
  form.scopeType = 'all'
  form.scopeTargetIds = []
  form.chapters = []
}

function detectContentType(fileName = '', mimeType = '') {
  const lowerName = String(fileName || '').toLowerCase()
  const lowerMime = String(mimeType || '').toLowerCase()
  if (lowerMime.includes('video') || lowerName.endsWith('.mp4')) {
    return 'video'
  }
  if (lowerMime.includes('audio') || lowerName.endsWith('.mp3') || lowerName.endsWith('.wav') || lowerName.endsWith('.m4a')) {
    return 'audio'
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
  if (
    lowerMime.includes('image')
    || lowerName.endsWith('.png')
    || lowerName.endsWith('.jpg')
    || lowerName.endsWith('.jpeg')
    || lowerName.endsWith('.webp')
    || lowerName.endsWith('.gif')
  ) {
    return 'image'
  }
  return null
}

function formatResourceOptionLabel(resource) {
  const typeText = resourceTypeLabels[resource?.contentType] || ''
  return typeText ? `${resource.title} · ${typeText}` : (resource.title || `资源#${resource.id}`)
}

function upsertResourceOption(resource) {
  if (!resource?.id) {
    return
  }
  const option = {
    value: Number(resource.id),
    label: resource.label || formatResourceOptionLabel(resource),
    title: resource.title || '',
    contentType: resource.contentType || null,
  }
  const index = resourceOptions.value.findIndex((item) => Number(item.value) === Number(option.value))
  if (index >= 0) {
    resourceOptions.value.splice(index, 1, option)
  } else {
    resourceOptions.value.push(option)
  }
}

function buildFileOptions(resourceDetail) {
  if (!resourceDetail?.mediaFileId) {
    return []
  }
  return [{
    value: Number(resourceDetail.mediaFileId),
    label: ['原始文件', resourceDetail.fileName].filter(Boolean).join(' · '),
    fileName: resourceDetail.fileName || '',
    displayLabel: '原始文件',
    contentType: resourceDetail.contentType || detectContentType(resourceDetail.fileName || '', resourceDetail.mimeType || ''),
  }]
}

function getChapterFileOptions(chapter) {
  if (!chapter?.resourceId) {
    return []
  }
  return resourceDetailCache[chapter.resourceId]?.fileOptions || []
}

function isChapterFileLoading(chapter) {
  if (!chapter?.resourceId) {
    return false
  }
  return !!resourceDetailLoading[chapter.resourceId]
}

function applyFileOptionToChapter(chapter, fileOption) {
  if (!chapter) {
    return
  }
  if (!fileOption) {
    chapter.fileId = null
    chapter.resourceFileName = ''
    chapter.resourceFileLabel = ''
    chapter.contentType = null
    return
  }
  chapter.fileId = Number(fileOption.value)
  chapter.resourceFileName = fileOption.fileName || ''
  chapter.resourceFileLabel = fileOption.displayLabel || ''
  chapter.contentType = fileOption.contentType || chapter.contentType || null
}

async function ensureResourceListLoaded() {
  resourceListLoading.value = true
  try {
    const response = await getLibraryItems({
      size: -1,
      scope: 'private',
    })
    const items = response.items || response || []
    resourceOptions.value = []
    items.forEach((item) => upsertResourceOption(item))
  } finally {
    resourceListLoading.value = false
  }
}

async function ensureResourceDetail(resourceId, fallbackTitle = '') {
  const normalizedId = Number(resourceId)
  if (!normalizedId) {
    return null
  }
  if (resourceDetailCache[normalizedId]) {
    return resourceDetailCache[normalizedId]
  }
  if (resourceDetailLoading[normalizedId]) {
    return null
  }

  resourceDetailLoading[normalizedId] = true
  try {
    if (fallbackTitle) {
      upsertResourceOption({ id: normalizedId, title: fallbackTitle })
    }
    const detail = await getLibraryItem(normalizedId)
    const resolved = {
      id: normalizedId,
      title: detail.title || fallbackTitle || `资源#${normalizedId}`,
      contentType: detail.contentType || null,
      fileOptions: buildFileOptions(detail),
    }
    resourceDetailCache[normalizedId] = resolved
    upsertResourceOption({
      id: normalizedId,
      title: resolved.title,
      contentType: resolved.contentType,
    })
    return resolved
  } catch (error) {
    if (fallbackTitle) {
      upsertResourceOption({ id: normalizedId, title: fallbackTitle })
    }
    return null
  } finally {
    resourceDetailLoading[normalizedId] = false
  }
}

async function syncChapterResourceSelection(chapter) {
  if (!chapter?.resourceId) {
    return
  }
  const detail = await ensureResourceDetail(chapter.resourceId, chapter.resourceTitle)
  if (!detail) {
    return
  }
  chapter.resourceTitle = detail.title
  const options = detail.fileOptions || []
  if (!options.length && detail.contentType === 'knowledge') {
    chapter.fileId = null
    chapter.resourceFileName = ''
    chapter.resourceFileLabel = '知识点卡片'
    chapter.contentType = 'knowledge'
    return
  }
  if (!options.length) {
    return
  }
  const selected = options.find((item) => Number(item.value) === Number(chapter.fileId)) || options[0]
  applyFileOptionToChapter(chapter, selected)
}

async function ensureOptionsLoaded() {
  const [instructorResult, resourceResult] = await Promise.allSettled([
    getUsers({ role: 'instructor', size: -1 }),
    ensureResourceListLoaded(),
    loadTagOptions(),
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

  if (resourceResult.status === 'rejected') {
    resourceOptions.value = []
  }
}

async function loadCourseDetail() {
  const course = await getCourse(props.courseId)
  form.title = course.title || ''
  form.category = course.category || null
  form.description = course.description || ''
  form.instructorId = course.instructorId ?? undefined
  form.tags = normalizeTags(course.tags)
  form.isRequired = !!course.isRequired
  form.scopeType = course.scopeType || 'all'
  form.scopeTargetIds = Array.isArray(course.scopeTargetIds) ? course.scopeTargetIds.map((item) => Number(item)).filter((item) => Number.isInteger(item) && item > 0) : []

  form.chapters = (course.chapters || [])
    .slice()
    .sort((a, b) => (a.sortOrder || 0) - (b.sortOrder || 0))
    .map((chapter) => {
      if (chapter.resourceId && chapter.resourceTitle) {
        upsertResourceOption({
          id: chapter.resourceId,
          title: chapter.resourceTitle,
          contentType: chapter.contentType,
        })
      }
      return createChapter({
        id: chapter.id,
        title: chapter.title,
        fileId: chapter.fileId || null,
        resourceId: chapter.libraryItemId || null,
        legacyResourceId: chapter.resourceId || null,
        fileUrl: chapter.fileUrl || '',
        contentType: chapter.contentType || detectContentType(chapter.fileUrl || chapter.videoUrl || chapter.docUrl || ''),
        resourceTitle: chapter.resourceTitle || '',
        resourceFileName: chapter.resourceFileName || '',
        resourceFileLabel: chapter.resourceFileLabel || '',
        legacyFileOnly: !!chapter.fileId && !chapter.libraryItemId,
      })
    })

  if (!form.chapters.length) {
    return
  }

  const resourceIds = [...new Set(form.chapters.map((chapter) => Number(chapter.resourceId)).filter(Boolean))]
  await Promise.allSettled(resourceIds.map((resourceId) => {
    const fallbackTitle = form.chapters.find((item) => Number(item.resourceId) === resourceId)?.resourceTitle || ''
    return ensureResourceDetail(resourceId, fallbackTitle)
  }))
  await Promise.allSettled(form.chapters.map((chapter) => {
    if (chapter.resourceId) {
      return syncChapterResourceSelection(chapter)
    }
    return Promise.resolve()
  }))
}

async function initializeModal() {
  loading.value = true
  currentStep.value = 0
  resourceOptions.value = []
  Object.keys(resourceDetailCache).forEach((key) => {
    delete resourceDetailCache[key]
  })
  Object.keys(resourceDetailLoading).forEach((key) => {
    delete resourceDetailLoading[key]
  })
  try {
    if (!isEditing.value) {
      resetForm()
    }
    await ensureOptionsLoaded()
    if (isEditing.value) {
      await loadCourseDetail()
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
  if (form.scopeType !== 'all' && !form.scopeTargetIds.length) {
    message.warning('请至少选择一个可见范围目标')
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

function canRemoveChapter(chapter) {
  return form.chapters.length > 1 || !chapter?.id
}

async function handleChapterResourceChange(index, value) {
  const chapter = form.chapters[index]
  if (!chapter) {
    return
  }

  const normalizedValue = value ? Number(value) : null
  if (!normalizedValue) {
    if (chapter.originalLegacyFileOnly) {
      chapter.resourceId = null
      chapter.legacyResourceId = chapter.originalLegacyResourceId
      chapter.fileId = chapter.originalFileId
      chapter.contentType = chapter.originalContentType
      chapter.resourceTitle = chapter.originalResourceTitle
      chapter.resourceFileName = chapter.originalResourceFileName
      chapter.resourceFileLabel = chapter.originalResourceFileLabel
      chapter.legacyFileOnly = true
      return
    }
    chapter.resourceId = null
    chapter.legacyResourceId = null
    chapter.fileId = null
    chapter.contentType = null
    chapter.resourceTitle = ''
    chapter.resourceFileName = ''
    chapter.resourceFileLabel = ''
    chapter.legacyFileOnly = false
    return
  }

  chapter.resourceId = normalizedValue
  chapter.legacyResourceId = null
  chapter.fileId = null
  chapter.contentType = null
  chapter.resourceTitle = resourceOptions.value.find((item) => Number(item.value) === normalizedValue)?.title || ''
  chapter.resourceFileName = ''
  chapter.resourceFileLabel = ''
  chapter.legacyFileOnly = false
  await syncChapterResourceSelection(chapter)
}

function handleChapterFileChange(index, value) {
  const chapter = form.chapters[index]
  if (!chapter || !chapter.resourceId) {
    return
  }
  const options = getChapterFileOptions(chapter)
  const target = options.find((item) => Number(item.value) === Number(value)) || options[0]
  applyFileOptionToChapter(chapter, target)
}

function inferCourseFileType() {
  if (!form.chapters.length) {
    return 'pending'
  }
  const types = [...new Set(
    form.chapters
      .map((chapter) => chapter.contentType)
      .filter((item) => ['video', 'document', 'image', 'audio', 'knowledge'].includes(item)),
  )]
  if (!types.length) {
    return 'document'
  }
  if (types.length === 1) {
    return types[0]
  }
  return 'mixed'
}

async function handleSubmit() {
  if (submitting.value) {
    return
  }
  if (!form.title.trim()) {
    message.warning('请输入课程名称')
    return
  }
  if (!form.category) {
    message.warning('请选择课程分类')
    return
  }
  if (form.chapters.length) {
    if (form.chapters.some((chapter) => !chapter.title.trim())) {
      message.warning('请填写所有章节名称')
      return
    }
    if (form.chapters.some((chapter) => !chapter.resourceId && !chapter.legacyResourceId && !chapter.legacyFileOnly)) {
      message.warning('每个章节都需要从知识库选择资源')
      return
    }
  }
  if (form.scopeType !== 'all' && !form.scopeTargetIds.length) {
    message.warning('请至少选择一个可见范围目标')
    return
  }

  submitting.value = true

  try {
    await Promise.allSettled(form.chapters.map((chapter) => {
      if (chapter.resourceId) {
        return syncChapterResourceSelection(chapter)
      }
      return Promise.resolve()
    }))

    const chapters = form.chapters.map((chapter, index) => ({
      id: chapter.id,
      title: chapter.title.trim(),
      sortOrder: index,
      duration: 0,
      fileId: chapter.resourceId
        ? (chapter.contentType === 'knowledge' ? null : (chapter.fileId || null))
        : ((chapter.legacyResourceId || chapter.legacyFileOnly) ? (chapter.fileId || null) : null),
      resourceId: chapter.legacyResourceId || null,
      libraryItemId: chapter.resourceId || null,
    }))

    const normalizedTags = normalizeTags(form.tags)
    const payload = {
      title: form.title.trim(),
      category: form.category,
      description: form.description?.trim() || '',
      instructorId: form.instructorId ?? null,
      tags: normalizedTags,
      isRequired: form.isRequired,
      scopeType: form.scopeType,
      scopeTargetIds: form.scopeType === 'all' ? [] : form.scopeTargetIds,
      fileType: inferCourseFileType(),
      coverColor: categoryColorMap[form.category] || '#003087',
      duration: 0,
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
  }
}
</script>

<style scoped>
.chapters-editor {
  min-height: 240px;
}

.chapter-empty-state {
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  background: #fafcff;
  padding: 12px 0;
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
