<template>
  <a-modal
    :open="open"
    wrap-class-name="resource-modal"
    :title="courseId ? '编辑课程' : '创建课程'"
    :width="880"
    :footer="null"
    :destroy-on-close="true"
    @cancel="closeModal"
  >
    <a-spin :spinning="loading">
      <a-form layout="vertical">
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="课程名称" required>
              <a-input v-model:value="form.title" placeholder="请输入课程名称" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="课程分类" required>
              <a-select v-model:value="form.category" placeholder="请选择分类">
                <a-select-option
                  v-for="item in categoryOptions"
                  :key="item.key"
                  :value="item.key"
                >
                  {{ item.label }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="课程简介">
          <a-textarea v-model:value="form.description" :rows="4" :maxlength="500" show-count />
        </a-form-item>

        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="主讲教官">
              <a-select v-model:value="form.instructor_id" :options="instructorOptions" allow-clear />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="是否必修">
              <a-switch v-model:checked="form.is_required" />
            </a-form-item>
          </a-col>
        </a-row>

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

        <a-form-item label="可见范围">
          <AdmissionScopeSelector
            v-model:scope-type="form.scope_type"
            v-model:scope-target-ids="form.scope_target_ids"
            user-role=""
            all-hint="全体用户都可以查看该课程。"
            user-placeholder="请选择可查看课程的用户"
            department-placeholder="请选择可查看课程的部门"
            role-placeholder="请选择可查看课程的角色"
            user-hint="仅选中的用户可以查看该课程。"
            department-hint="选中部门下的用户可以查看该课程。"
            role-hint="拥有选中角色的用户可以查看该课程。"
          />
        </a-form-item>

        <div class="chapter-header">
          <div>
            <h3>章节资源</h3>
            <p>可先创建不含章节的课程，后续再由任课教官补充章节与资源；已添加章节时，每章仍需绑定自己的资源。</p>
          </div>
          <a-button type="dashed" @click="addChapter">{{ form.chapters.length ? '添加章节' : '添加第一章' }}</a-button>
        </div>

        <div v-if="!form.chapters.length" class="chapter-empty-state">
          <a-empty description="当前还没有章节。系统管理员可以先创建课程，后续再由任课教官补充章节资源。" />
        </div>

        <template v-else>
          <CourseChapterResourceSelector
            v-for="(chapter, index) in form.chapters"
            :key="chapter.local_key"
            :chapter="chapter"
            :index="index"
            :can-remove="canRemoveChapter(chapter)"
            :resource-options="resourceOptions"
            :file-options="chapterFileOptions[chapter.local_key] || []"
            :resource-loading="resourceLoading"
            :file-loading="chapterFileLoading[chapter.local_key] || false"
            @remove="removeChapter(index)"
            @change-resource="(value) => handleChapterResourceChange(index, value)"
            @change-file="(value) => handleChapterFileChange(index, value)"
          />
        </template>

        <div class="modal-footer">
          <a-button @click="closeModal">取消</a-button>
          <a-button type="primary" :loading="submitting" @click="submitForm">
            {{ submitting ? '提交中' : (courseId ? '保存修改' : '创建课程') }}
          </a-button>
        </div>
      </a-form>
    </a-spin>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, reactive, ref, toRef, watch } from 'vue'
import { message } from 'ant-design-vue'
import type { CourseCreate, CourseResponse, CourseUpdate } from '@/api/learning-resource'
import {
  createCourse,
  createCourseTag,
  getCourseDetail,
  listCourseTags,
  listUsers,
  updateCourse,
} from '@/api/learning-resource'
import type { LibraryItemResponse } from '@/api/library'
import { getLibraryItemDetail, listLibraryItems } from '@/api/library'
import { useCreatableTagSelect } from '@/composables/useCreatableTagSelect'
import { useAuthStore } from '@/stores/auth'
import { COURSE_CATEGORIES, getUserDisplayName } from '@/utils/learning-resource'
import AdmissionScopeSelector from '@/components/common/AdmissionScopeSelector.vue'
import CourseChapterResourceSelector from '@/components/resource/CourseChapterResourceSelector.vue'

interface SelectOption {
  value: number
  label: string
}

interface EditableChapter {
  local_key: string
  id?: number
  title: string
  sort_order: number
  resource_id: number | null
  legacy_resource_id: number | null
  file_id: number | null
  content_type?: string | null
  resource_title?: string
  resource_file_name?: string
  resource_file_label?: string
  legacy_file_only?: boolean
}

const props = withDefaults(defineProps<{
  open?: boolean
  courseId?: number | null
  canManage?: boolean
}>(), {
  open: false,
  courseId: null,
  canManage: false,
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  success: []
}>()

const authStore = useAuthStore()
const canCreateCourse = computed(() => authStore.hasPermission('CREATE_COURSE'))
const canManageCourse = computed(() => props.canManage)
const categoryOptions = COURSE_CATEGORIES.filter((item) => item.key !== 'all')
const loading = ref(false)
const submitting = ref(false)
const resourceLoading = ref(false)
const instructorOptions = ref<SelectOption[]>([])
const resourceOptions = ref<SelectOption[]>([])
const chapterFileOptions = reactive<Record<string, SelectOption[]>>({})
const chapterFileLoading = reactive<Record<string, boolean>>({})
const resourceDetailCache = new Map<number, LibraryItemResponse>()
let chapterSeed = 0

const form = reactive({
  title: '',
  category: '',
  description: '',
  instructor_id: undefined as number | undefined,
  is_required: false,
  scope_type: 'all',
  scope_target_ids: [] as number[],
  tags: [] as string[],
  chapters: [] as EditableChapter[],
})

const {
  tagSearching,
  mergedTagOptions,
  normalizeTags,
  fetchTagOptions,
  handleTagSearch,
  handleTagChange,
} = useCreatableTagSelect(toRef(form, 'tags'), {
  fetchTags: listCourseTags,
  createTag: createCourseTag,
})

watch(() => props.open, async (open) => {
  if (!open) {
    resetForm()
    return
  }
  if (props.courseId ? !canManageCourse.value : !canCreateCourse.value) {
    message.warning(props.courseId ? '您没有编辑该课程的权限' : '您没有创建课程权限')
    emit('update:open', false)
    return
  }

  loading.value = true
  try {
    await Promise.all([
      fetchTagOptions(),
      loadInstructors(),
      loadResources(),
    ])
    if (props.courseId) {
      await loadCourse(props.courseId)
    }
  } finally {
    loading.value = false
  }
}, { immediate: true })

function createChapter(overrides: Partial<EditableChapter> = {}): EditableChapter {
  chapterSeed += 1
  return {
    local_key: `chapter-${chapterSeed}`,
    title: '',
    sort_order: form.chapters.length,
    resource_id: null,
    legacy_resource_id: null,
    file_id: null,
    content_type: null,
    resource_title: '',
    resource_file_name: '',
    resource_file_label: '',
    legacy_file_only: false,
    ...overrides,
  }
}

function resetForm() {
  form.title = ''
  form.category = ''
  form.description = ''
  form.instructor_id = undefined
  form.is_required = false
  form.scope_type = 'all'
  form.scope_target_ids = []
  form.tags = []
  form.chapters = []
  for (const key of Object.keys(chapterFileOptions)) {
    delete chapterFileOptions[key]
  }
  for (const key of Object.keys(chapterFileLoading)) {
    delete chapterFileLoading[key]
  }
  resourceDetailCache.clear()
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

async function loadResources() {
  resourceLoading.value = true
  try {
    const response = await listLibraryItems({ page: 1, size: -1, scope: 'private' })
    resourceOptions.value = (response.items || []).map((item) => ({
      value: item.id,
      label: [item.title, getContentTypeLabel(item.content_type)].filter(Boolean).join(' · '),
    }))
  } finally {
    resourceLoading.value = false
  }
}

async function loadCourse(courseId: number) {
  const course = await getCourseDetail(courseId)
  form.title = course.title
  form.category = course.category
  form.description = course.description || ''
  form.instructor_id = course.instructor_id || undefined
  form.is_required = !!course.is_required
  form.scope_type = course.scope_type || 'all'
  form.scope_target_ids = [...(course.scope_target_ids || [])]
  form.tags = [...(course.tags || [])]
  form.chapters = (course.chapters || []).map((chapter, index) => createChapter({
    id: chapter.id,
    title: chapter.title,
    sort_order: chapter.sort_order ?? index,
    resource_id: chapter.library_item_id || null,
    legacy_resource_id: chapter.resource_id || null,
    file_id: chapter.file_id || null,
    content_type: chapter.content_type,
    resource_title: chapter.resource_title || '',
    resource_file_name: chapter.resource_file_name || '',
    resource_file_label: chapter.resource_file_label || '',
    legacy_file_only: !!chapter.file_id && !chapter.library_item_id,
  }))

  for (let index = 0; index < form.chapters.length; index += 1) {
    const chapter = form.chapters[index]
    if (chapter.resource_id) {
      await loadResourceFiles(chapter)
    }
  }
}

async function loadResourceFiles(chapter: EditableChapter) {
  if (!chapter.resource_id) {
    chapterFileOptions[chapter.local_key] = []
    return
  }
  chapterFileLoading[chapter.local_key] = true
  try {
    let detail = resourceDetailCache.get(chapter.resource_id)
    if (!detail) {
      detail = await getLibraryItemDetail(chapter.resource_id)
      resourceDetailCache.set(chapter.resource_id, detail)
    }
    chapter.resource_title = detail.title
    chapter.content_type = detail.content_type
    chapterFileOptions[chapter.local_key] = detail.media_file_id ? [{
      value: detail.media_file_id,
      label: ['原始文件', detail.file_name].filter(Boolean).join(' · '),
    }] : []
    if (!chapter.file_id && detail.media_file_id) {
      chapter.file_id = detail.media_file_id
      chapter.resource_file_name = detail.file_name || ''
      chapter.resource_file_label = '原始文件'
      chapter.content_type = detail.content_type
    }
    if (!detail.media_file_id && detail.content_type === 'knowledge') {
      chapter.file_id = null
      chapter.resource_file_name = ''
      chapter.resource_file_label = '知识点卡片'
      chapter.content_type = 'knowledge'
    }
  } finally {
    chapterFileLoading[chapter.local_key] = false
  }
}

function addChapter() {
  form.chapters.push(createChapter())
}

function removeChapter(index: number) {
  form.chapters.splice(index, 1)
}

function canRemoveChapter(chapter?: EditableChapter) {
  return form.chapters.length > 1 || !chapter?.id
}

async function handleChapterResourceChange(index: number, value: number | null) {
  const chapter = form.chapters[index]
  chapter.resource_id = value
  chapter.legacy_resource_id = value ? null : chapter.legacy_resource_id
  chapter.file_id = null
  chapter.resource_file_name = ''
  chapter.resource_file_label = ''
  chapter.content_type = null
  if (!value) {
    if (chapter.legacy_file_only) {
      return
    }
    chapter.legacy_resource_id = null
    chapter.resource_title = ''
    chapterFileOptions[chapter.local_key] = []
    return
  }
  await loadResourceFiles(chapter)
}

function handleChapterFileChange(index: number, value: number | null) {
  const chapter = form.chapters[index]
  chapter.file_id = value
  const selected = (chapterFileOptions[chapter.local_key] || []).find((item) => item.value === value)
  chapter.resource_file_label = selected?.label || ''
}

function getContentTypeLabel(contentType?: string | null) {
  const map: Record<string, string> = {
    video: '视频',
    document: '文档',
    image: '图片',
    audio: '音频',
    knowledge: '知识点',
  }
  return map[contentType || ''] || ''
}

function computeFileType() {
  if (!form.chapters.length) {
    return 'pending'
  }
  const types = new Set(form.chapters.map((item) => item.content_type).filter(Boolean))
  if (!types.size) {
    return 'document'
  }
  if (types.size > 1) {
    return 'mixed'
  }
  return Array.from(types)[0] as string
}

function buildPayload(): CourseCreate | CourseUpdate | null {
  if (!form.title.trim()) {
    message.warning('请输入课程名称')
    return null
  }
  if (!form.category) {
    message.warning('请选择课程分类')
    return null
  }
  for (const [index, chapter] of form.chapters.entries()) {
    if (!chapter.title.trim()) {
      message.warning(`请填写第 ${index + 1} 章的标题`)
      return null
    }
    if (!chapter.resource_id && !chapter.legacy_resource_id && !chapter.legacy_file_only) {
      message.warning(`第 ${index + 1} 章请从资源库选择资源`)
      return null
    }
  }

  return {
    title: form.title.trim(),
    category: form.category,
    description: form.description || undefined,
    instructor_id: form.instructor_id,
    is_required: form.is_required,
    file_type: computeFileType(),
    scope_type: form.scope_type,
    scope_target_ids: form.scope_target_ids,
    tags: normalizeTags(form.tags),
    chapters: form.chapters.map((chapter, index) => ({
      id: chapter.id,
      title: chapter.title.trim(),
      sort_order: index,
      resource_id: chapter.legacy_resource_id || undefined,
      library_item_id: chapter.resource_id || undefined,
      file_id: chapter.resource_id
        ? (chapter.content_type === 'knowledge' ? undefined : (chapter.file_id || undefined))
        : ((chapter.legacy_resource_id || chapter.legacy_file_only) ? (chapter.file_id || undefined) : undefined),
    })),
  }
}

async function submitForm() {
  if (submitting.value) {
    return
  }
  if (props.courseId ? !canManageCourse.value : !canCreateCourse.value) {
    message.warning(props.courseId ? '您没有编辑该课程的权限' : '您没有创建课程权限')
    return
  }
  const payload = buildPayload()
  if (!payload) {
    return
  }
  submitting.value = true
  try {
    let result: CourseResponse
    if (props.courseId) {
      result = await updateCourse(props.courseId, payload as CourseUpdate)
      message.success(`课程《${result.title}》已更新`)
    } else {
      result = await createCourse(payload as CourseCreate)
      message.success(`课程《${result.title}》已创建`)
    }
    emit('success')
    emit('update:open', false)
  } catch (error) {
    message.error(error instanceof Error ? error.message : '保存失败')
  } finally {
    submitting.value = false
  }
}

function closeModal() {
  emit('update:open', false)
}
</script>

<style scoped>
.chapter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.chapter-header h3 {
  font-size: 18px;
  margin-bottom: 4px;
}

.chapter-header p {
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.chapter-empty-state {
  border: 1px dashed var(--v2-border);
  border-radius: var(--v2-radius);
  background: rgba(29, 78, 216, 0.02);
  padding: 12px 0;
  margin-bottom: 12px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}
</style>
