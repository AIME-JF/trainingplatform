<template>
  <a-modal
    :open="open"
    wrap-class-name="resource-modal"
    title="上传资源"
    :width="isMobile ? 'calc(100vw - 24px)' : 920"
    :footer="null"
    :destroy-on-close="false"
    :mask-closable="!submitting"
    :keyboard="!submitting"
    :closable="!submitting"
    @update:open="handleOpenChange"
    @cancel="handleCancel"
  >
    <a-form layout="vertical" class="upload-form">
      <a-form-item label="资源标题" required>
        <a-input v-model:value="form.title" placeholder="请输入标题" />
      </a-form-item>

      <a-form-item label="资源摘要">
        <a-textarea v-model:value="form.summary" :rows="4" placeholder="图片资源请在此填写文字说明" />
      </a-form-item>

      <a-row :gutter="[12, 0]" class="upload-meta-row">
        <a-col :xs="24" :sm="8">
          <a-form-item label="内容类型">
            <a-select v-model:value="form.content_type" popup-class-name="resource-modal-dropdown">
              <a-select-option value="video">视频</a-select-option>
              <a-select-option value="image">图片</a-select-option>
              <a-select-option value="document">文档</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>

        <a-col :xs="24" :sm="16">
          <a-form-item label="标签">
            <a-select
              v-model:value="form.tags"
              mode="tags"
              show-search
              :options="mergedTagOptions"
              :filter-option="false"
              :loading="tagSearching"
              placeholder="支持搜索已有标签，输入后回车可直接创建新标签"
              popup-class-name="resource-modal-dropdown"
              style="width: 100%"
              @search="handleTagSearch"
              @change="handleTagChange"
            />
          </a-form-item>
        </a-col>
      </a-row>

      <a-form-item label="可见范围">
        <AdmissionScopeSelector
          v-model:scope-type="form.scope_type"
          v-model:scope-target-ids="form.scope_target_ids"
          user-role=""
          all-hint="全部用户都可以查看该资源。"
          user-placeholder="请选择可查看资源的用户"
          department-placeholder="请选择可查看资源的部门"
          role-placeholder="请选择可查看资源的角色"
          user-hint="仅选中的用户可以查看该资源。"
          department-hint="选中部门下的用户可以查看该资源。"
          role-hint="拥有选中角色的用户可以查看该资源。"
        />
      </a-form-item>

      <a-form-item label="上传文件" required>
        <a-upload-dragger
          class="upload-dragger"
          v-model:file-list="fileList"
          :before-upload="beforeUpload"
          :accept="currentAccept"
          :multiple="true"
        >
          <InboxOutlined class="upload-icon" />
          <p class="upload-title">点击或拖拽上传资源文件</p>
          <p class="upload-hint">当前类型允许：{{ currentAccept || '无' }}</p>
        </a-upload-dragger>
      </a-form-item>

      <div class="modal-actions">
        <a-button class="modal-btn secondary-btn" :disabled="submitting" @click="handleCancel">取消</a-button>
        <a-button class="modal-btn subtle-btn" type="primary" ghost :loading="submitting" @click="submitDraft">
          保存草稿
        </a-button>
        <a-button class="modal-btn primary-btn" type="primary" :loading="submitting" @click="submitAndSubmitReview">
          提交审核
        </a-button>
      </div>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, reactive, ref, toRef, watch } from 'vue'
import { InboxOutlined } from '@ant-design/icons-vue'
import { message, Upload } from 'ant-design-vue'
import type { UploadFile } from 'ant-design-vue'
import { createResource, createResourceTag, listResourceTags, submitResourceReview, uploadMediaFile } from '@/api/learning-resource'
import { useCreatableTagSelect } from '@/composables/useCreatableTagSelect'
import { useMobile } from '@/composables/useMobile'
import AdmissionScopeSelector from '@/components/common/AdmissionScopeSelector.vue'
import { extractMediaDurationSeconds } from '@/utils/learning-resource'

const props = withDefaults(defineProps<{
  open?: boolean
}>(), {
  open: false,
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  success: []
}>()

const { isMobile } = useMobile()
const submitting = ref(false)
const fileList = ref<UploadFile[]>([])

const ALLOWED_EXTENSIONS: Record<string, string[]> = {
  video: ['mp4'],
  document: ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'html', 'htm'],
  image: ['jpg', 'jpeg', 'png', 'webp', 'gif'],
}

const form = reactive({
  title: '',
  summary: '',
  content_type: 'video',
  scope_type: 'all',
  scope_target_ids: [] as number[],
  tags: [] as string[],
})

const {
  tagSearching,
  mergedTagOptions,
  normalizeTags,
  fetchTagOptions,
  handleTagSearch,
  handleTagChange,
} = useCreatableTagSelect(toRef(form, 'tags'), {
  fetchTags: listResourceTags,
  createTag: createResourceTag,
})

const currentAccept = computed(() => (ALLOWED_EXTENSIONS[form.content_type] || []).map((ext) => `.${ext}`).join(','))

watch(() => props.open, (open) => {
  if (open) {
    void fetchTagOptions()
  }
  if (!open && !submitting.value) {
    resetForm()
  }
}, { immediate: true })

watch(() => form.content_type, () => {
  if (!fileList.value.length) {
    return
  }
  fileList.value = fileList.value.filter((item) => isAllowedFile(item.name || ''))
})

function handleOpenChange(value: boolean) {
  if (!submitting.value) {
    emit('update:open', value)
  }
}

function handleCancel() {
  if (!submitting.value) {
    closeModal()
  }
}

function closeModal() {
  resetForm()
  emit('update:open', false)
}

function resetForm() {
  form.title = ''
  form.summary = ''
  form.content_type = 'video'
  form.scope_type = 'all'
  form.scope_target_ids = []
  form.tags = []
  fileList.value = []
}

function getFileExt(name: string) {
  const dot = name.lastIndexOf('.')
  return dot >= 0 ? name.slice(dot + 1).toLowerCase() : ''
}

function isAllowedFile(name: string) {
  return (ALLOWED_EXTENSIONS[form.content_type] || []).includes(getFileExt(name))
}

function beforeUpload(file: File) {
  if (!isAllowedFile(file.name)) {
    message.error(`文件类型不匹配当前内容类型（允许：${currentAccept.value}）`)
    return Upload.LIST_IGNORE
  }
  return false
}

async function createDraft() {
  if (!form.title.trim()) {
    message.warning('请输入资源标题')
    return null
  }
  if (!fileList.value.length) {
    message.warning('请上传文件')
    return null
  }
  if (form.scope_type !== 'all' && !form.scope_target_ids.length) {
    message.warning('请选择可见范围目标')
    return null
  }

  const uploadedFiles = []
  for (const item of fileList.value) {
    const file = item.originFileObj
    if (!(file instanceof File)) {
      continue
    }
    const durationSeconds = await extractMediaDurationSeconds(file)
    const uploaded = await uploadMediaFile(file, durationSeconds || undefined)
    uploadedFiles.push(uploaded)
  }

  return createResource({
    title: form.title.trim(),
    summary: form.summary || undefined,
    content_type: form.content_type,
    scope_type: form.scope_type,
    scope_target_ids: form.scope_target_ids,
    tags: normalizeTags(form.tags),
    media_links: uploadedFiles.map((file, index) => ({
      media_file_id: file.id,
      media_role: 'main',
      sort_order: index,
    })),
    cover_media_file_id: uploadedFiles[0]?.id,
  })
}

async function submitDraft() {
  submitting.value = true
  try {
    const resource = await createDraft()
    if (!resource) {
      return
    }
    message.success(`资源《${resource.title}》已保存为草稿`)
    emit('success')
    closeModal()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '保存失败')
  } finally {
    submitting.value = false
  }
}

async function submitAndSubmitReview() {
  submitting.value = true
  try {
    const resource = await createDraft()
    if (!resource) {
      return
    }
    await submitResourceReview(resource.id)
    message.success('资源已提交审核')
    emit('success')
    closeModal()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '提交审核失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.upload-form {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.upload-icon {
  display: block;
  margin-bottom: 12px;
  font-size: 28px;
  color: var(--resource-upload-text-secondary);
}

.upload-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--resource-upload-text-primary);
}

.upload-hint {
  margin-top: 8px;
  font-size: 13px;
  color: var(--resource-upload-text-tertiary);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.modal-btn {
  min-width: 112px;
}

:deep(.resource-modal .ant-modal-mask) {
  backdrop-filter: blur(12px);
  background: rgba(16, 17, 20, 0.58);
}

:deep(.resource-modal .ant-modal-content) {
  border-radius: 32px !important;
  background:
    linear-gradient(180deg, var(--resource-upload-surface-top) 0%, var(--resource-upload-surface-bottom) 100%) !important;
  border: 1px solid var(--resource-upload-border);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    var(--resource-upload-shadow-strong) !important;
}

:deep(.resource-modal .ant-modal-header) {
  padding: 24px 28px 0 !important;
  background: transparent !important;
}

:deep(.resource-modal .ant-modal-title) {
  color: var(--resource-upload-text-primary) !important;
  font-size: 24px !important;
  font-weight: 700 !important;
  letter-spacing: -0.02em;
}

:deep(.resource-modal .ant-modal-close) {
  color: var(--resource-upload-text-secondary);
}

:deep(.resource-modal .ant-modal-close:hover) {
  color: var(--resource-upload-text-primary);
}

:deep(.resource-modal .ant-modal-body) {
  padding: 22px 28px 28px !important;
}

:deep(.resource-modal .ant-form-item) {
  margin-bottom: 18px !important;
}

:deep(.resource-modal .ant-form-item-label > label) {
  color: var(--resource-upload-text-primary) !important;
  font-size: 14px !important;
  font-weight: 600 !important;
}

:deep(.resource-modal .ant-input),
:deep(.resource-modal .ant-input-affix-wrapper),
:deep(.resource-modal .ant-select-selector),
:deep(.resource-modal .ant-input-textarea textarea) {
  border-radius: 16px !important;
  border-color: var(--resource-upload-border) !important;
  background: rgba(255, 255, 255, 0.04) !important;
  color: var(--resource-upload-text-primary) !important;
  box-shadow: none !important;
  transition: border-color 0.2s ease, background-color 0.2s ease !important;
}

:deep(.resource-modal .ant-input),
:deep(.resource-modal .ant-input-affix-wrapper),
:deep(.resource-modal .ant-select-selector) {
  min-height: 48px !important;
}

:deep(.resource-modal .ant-input::placeholder),
:deep(.resource-modal .ant-input-textarea textarea::placeholder),
:deep(.resource-modal .ant-select-selection-placeholder),
:deep(.resource-modal .scope-hint),
:deep(.resource-modal .scope-permission-tip) {
  color: var(--resource-upload-text-quiet) !important;
}

:deep(.resource-modal .ant-input:focus),
:deep(.resource-modal .ant-input-focused),
:deep(.resource-modal .ant-input-affix-wrapper:hover),
:deep(.resource-modal .ant-input-affix-wrapper-focused),
:deep(.resource-modal .ant-select-focused .ant-select-selector),
:deep(.resource-modal .ant-select:not(.ant-select-disabled):hover .ant-select-selector),
:deep(.resource-modal .ant-input-textarea textarea:focus) {
  border-color: var(--resource-upload-border-strong) !important;
  background: var(--resource-upload-surface-hover) !important;
}

:deep(.resource-modal .ant-select-selection-item),
:deep(.resource-modal .ant-select-arrow),
:deep(.resource-modal .ant-select-clear),
:deep(.resource-modal .ant-input-show-count-suffix) {
  color: var(--resource-upload-text-primary) !important;
}

:deep(.resource-modal .ant-input-textarea-show-count::after) {
  color: var(--resource-upload-text-quiet) !important;
}

:deep(.resource-modal .ant-select-selection-overflow-item .ant-select-selection-item) {
  border: 1px solid var(--resource-upload-border) !important;
  background: rgba(255, 255, 255, 0.07) !important;
  color: var(--resource-upload-text-primary) !important;
}

:deep(.resource-modal .admission-scope-selector) {
  gap: 14px;
}

:deep(.resource-modal .scope-type-group) {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

:deep(.resource-modal .scope-type-group .ant-radio-button-wrapper) {
  height: 42px !important;
  border-radius: 999px !important;
  border: 1px solid var(--resource-upload-border) !important;
  background: rgba(255, 255, 255, 0.04) !important;
  color: var(--resource-upload-text-secondary) !important;
  line-height: 40px !important;
  text-align: center;
}

:deep(.resource-modal .scope-type-group .ant-radio-button-wrapper::before) {
  display: none !important;
}

:deep(.resource-modal .scope-type-group .ant-radio-button-wrapper-checked:not(.ant-radio-button-wrapper-disabled)) {
  border-color: rgba(255, 255, 255, 0.24) !important;
  background: var(--resource-upload-primary-bg) !important;
  color: var(--resource-upload-primary-text) !important;
  box-shadow: none !important;
}

:deep(.resource-modal .scope-content) {
  padding: 16px;
  border-radius: 20px;
  border: 1px solid var(--resource-upload-border);
  background: rgba(255, 255, 255, 0.035);
}

:deep(.resource-modal .scope-hint) {
  line-height: 1.7;
}

:deep(.resource-modal .ant-upload-wrapper .ant-upload-drag) {
  border-radius: 24px !important;
  border: 1px dashed rgba(255, 255, 255, 0.18) !important;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.035) 100%) !important;
  padding: 28px 16px !important;
}

:deep(.resource-modal .ant-upload-wrapper .ant-upload-drag:hover) {
  border-color: rgba(255, 255, 255, 0.24) !important;
  background: rgba(255, 255, 255, 0.06) !important;
}

:deep(.resource-modal .ant-upload-list-item) {
  border-radius: 14px !important;
  border-color: var(--resource-upload-border) !important;
  background: rgba(255, 255, 255, 0.04) !important;
  color: var(--resource-upload-text-primary) !important;
}

:deep(.resource-modal .ant-upload-list-item .ant-upload-list-item-name),
:deep(.resource-modal .ant-upload-list-item .ant-upload-list-item-card-actions-btn),
:deep(.resource-modal .ant-upload-list-item .anticon) {
  color: var(--resource-upload-text-primary) !important;
}

:deep(.resource-modal .ant-btn) {
  height: 46px !important;
  border-radius: 999px !important;
  font-weight: 600 !important;
  box-shadow: none !important;
}

:deep(.resource-modal .secondary-btn) {
  border-color: var(--resource-upload-border) !important;
  background: var(--resource-upload-surface-soft) !important;
  color: var(--resource-upload-text-primary) !important;
}

:deep(.resource-modal .secondary-btn:hover:not(:disabled)),
:deep(.resource-modal .secondary-btn:focus:not(:disabled)) {
  border-color: var(--resource-upload-border-strong) !important;
  background: var(--resource-upload-surface-hover) !important;
  color: var(--resource-upload-text-primary) !important;
}

:deep(.resource-modal .subtle-btn) {
  border-color: var(--resource-upload-border) !important;
  background: transparent !important;
  color: var(--resource-upload-text-primary) !important;
}

:deep(.resource-modal .subtle-btn:hover:not(:disabled)),
:deep(.resource-modal .subtle-btn:focus:not(:disabled)) {
  border-color: var(--resource-upload-border-strong) !important;
  background: var(--resource-upload-surface-soft) !important;
}

:deep(.resource-modal .primary-btn) {
  border-color: rgba(255, 255, 255, 0.24) !important;
  background: var(--resource-upload-primary-bg) !important;
  color: var(--resource-upload-primary-text) !important;
}

:deep(.resource-modal .primary-btn:hover:not(:disabled)),
:deep(.resource-modal .primary-btn:focus:not(:disabled)) {
  border-color: rgba(255, 255, 255, 0.3) !important;
  background: var(--resource-upload-primary-bg-hover) !important;
  color: var(--resource-upload-primary-text) !important;
}

:deep(.resource-modal-dropdown) {
  padding: 6px !important;
  border-radius: 18px !important;
  border: 1px solid var(--resource-upload-border);
  background: rgba(37, 38, 43, 0.98) !important;
  box-shadow: var(--resource-upload-shadow) !important;
}

:deep(.resource-modal-dropdown .ant-select-item-option) {
  min-height: 40px;
  border-radius: 12px;
  color: var(--resource-upload-text-primary) !important;
}

:deep(.resource-modal-dropdown .ant-select-item-option-active:not(.ant-select-item-option-disabled)) {
  background: rgba(255, 255, 255, 0.07) !important;
}

:deep(.resource-modal-dropdown .ant-select-item-option-selected:not(.ant-select-item-option-disabled)) {
  background: var(--resource-upload-primary-bg) !important;
  color: var(--resource-upload-primary-text) !important;
  font-weight: 600;
}

@media (max-width: 768px) {
  .modal-actions {
    flex-direction: column-reverse;
    align-items: stretch;
  }

  .modal-btn {
    width: 100%;
  }

  :deep(.resource-modal .ant-modal-content) {
    border-radius: 26px !important;
  }

  :deep(.resource-modal .ant-modal-header) {
    padding: 20px 18px 0 !important;
  }

  :deep(.resource-modal .ant-modal-title) {
    font-size: 20px !important;
  }

  :deep(.resource-modal .ant-modal-body) {
    padding: 18px 18px 22px !important;
  }

  :deep(.resource-modal .ant-form-item) {
    margin-bottom: 16px !important;
  }

  :deep(.resource-modal .scope-type-group) {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  :deep(.resource-modal .scope-content) {
    padding: 14px;
    border-radius: 18px;
  }

  :deep(.resource-modal .ant-upload-wrapper .ant-upload-drag) {
    border-radius: 20px !important;
    padding: 22px 14px !important;
  }
}
</style>
