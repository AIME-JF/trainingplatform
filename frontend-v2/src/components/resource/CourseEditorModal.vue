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
            <p>每章从资源库选择当前用户已发布的资源；不选具体文件时默认使用该资源的首个文件。</p>
          </div>
          <a-button type="dashed" @click="addChapter">添加章节</a-button>
        </div>

        <CourseChapterResourceSelector
          v-for="(chapter, index) in form.chapters"
          :key="chapter.local_key"
          :chapter="chapter"
          :index="index"
          :can-remove="form.chapters.length > 1"
          :resource-options="resourceOptions"
          :file-options="chapterFileOptions[chapter.local_key] || []"
          :resource-loading="resourceLoading"
          :file-loading="chapterFileLoading[chapter.local_key] || false"
          @remove="removeChapter(index)"
          @change-resource="(value) => handleChapterResourceChange(index, value)"
          @change-file="(value) => handleChapterFileChange(index, value)"
        />

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
import type { CourseCreate, CourseResponse, CourseUpdate, ResourceDetailResponse, ResourceListItemResponse } from '@/api/learning-resource'
import {
  createCourse,
  createCourseTag,
  getCourseDetail,
  getResourceDetail,
  listCourseTags,
  listResources,
  listUsers,
  updateCourse,
} from '@/api/learning-resource'
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
  file_id: number | null
  content_type?: string | null
  resource_title?: string
  resource_file_name?: string
  resource_file_label?: string
}

const props = withDefaults(defineProps<{
  open?: boolean
  courseId?: number | null
}>(), {
  open: false,
  courseId: null,
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  success: []
}>()

const authStore = useAuthStore()
const canCreateCourse = computed(() => authStore.hasPermission('CREATE_COURSE'))
const canManageCourse = computed(() => authStore.role === 'admin' || authStore.roleCodes.includes('admin'))
const categoryOptions = COURSE_CATEGORIES.filter((item) => item.key !== 'all')
const loading = ref(false)
const submitting = ref(false)
const resourceLoading = ref(false)
const instructorOptions = ref<SelectOption[]>([])
const resourceOptions = ref<SelectOption[]>([])
const chapterFileOptions = reactive<Record<string, SelectOption[]>>({})
const chapterFileLoading = reactive<Record<string, boolean>>({})
const resourceDetailCache = new Map<number, ResourceDetailResponse>()
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
    message.warning(props.courseId ? '仅管理员可编辑课程' : '您没有创建课程权限')
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
    } else if (!form.chapters.length) {
      addChapter()
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
    file_id: null,
    content_type: null,
    resource_title: '',
    resource_file_name: '',
    resource_file_label: '',
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
    const response = await listResources({ page: 1, size: -1, my_only: true, status: 'published' })
    resourceOptions.value = (response.items || []).map((item: ResourceListItemResponse) => ({
      value: item.id,
      label: item.title,
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
    resource_id: chapter.resource_id || null,
    file_id: chapter.file_id || null,
    content_type: chapter.content_type,
    resource_title: chapter.resource_title || '',
    resource_file_name: chapter.resource_file_name || '',
    resource_file_label: chapter.resource_file_label || '',
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
      detail = await getResourceDetail(chapter.resource_id)
      resourceDetailCache.set(chapter.resource_id, detail)
    }
    chapter.resource_title = detail.title
    chapterFileOptions[chapter.local_key] = (detail.media_links || []).map((item, index) => ({
      value: item.media_file_id,
      label: [item.display_label || `文件${index + 1}`, item.file_name].filter(Boolean).join(' · '),
    }))
    if (!chapter.file_id && detail.media_links?.[0]) {
      const first = detail.media_links[0]
      chapter.file_id = first.media_file_id
      chapter.resource_file_name = first.file_name || ''
      chapter.resource_file_label = first.display_label || '文件1'
      chapter.content_type = first.content_type || detail.content_type
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

async function handleChapterResourceChange(index: number, value: number | null) {
  const chapter = form.chapters[index]
  chapter.resource_id = value
  chapter.file_id = null
  chapter.resource_file_name = ''
  chapter.resource_file_label = ''
  chapter.content_type = null
  if (!value) {
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

function computeFileType() {
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
  if (!form.chapters.length) {
    message.warning('请至少保留一个章节')
    return null
  }
  for (const [index, chapter] of form.chapters.entries()) {
    if (!chapter.title.trim()) {
      message.warning(`请填写第 ${index + 1} 章的标题`)
      return null
    }
    if (!chapter.resource_id) {
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
      resource_id: chapter.resource_id || undefined,
      file_id: chapter.file_id || undefined,
    })),
  }
}

async function submitForm() {
  if (props.courseId ? !canManageCourse.value : !canCreateCourse.value) {
    message.warning(props.courseId ? '仅管理员可编辑课程' : '您没有创建课程权限')
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

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 20px;
}
</style>
