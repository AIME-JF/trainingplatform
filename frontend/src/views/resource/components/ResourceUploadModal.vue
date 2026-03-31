<template>
  <a-modal
    :open="open"
    title="上传资源"
    :width="920"
    :footer="null"
    :destroy-on-close="false"
    :mask-closable="!submitting"
    :keyboard="!submitting"
    :closable="!submitting"
    @update:open="handleOpenChange"
    @cancel="handleCancel"
  >
    <a-form layout="vertical">
      <a-form-item label="资源标题" required>
        <a-input v-model:value="form.title" placeholder="请输入标题" />
      </a-form-item>

      <a-form-item label="资源摘要">
        <a-textarea v-model:value="form.summary" :rows="4" placeholder="图片资源请在此填写文字说明" />
      </a-form-item>

      <a-row :gutter="12">
        <a-col :span="8">
          <a-form-item label="内容类型">
            <a-select v-model:value="form.contentType">
              <a-select-option value="video">视频</a-select-option>
              <a-select-option value="image">图片</a-select-option>
              <a-select-option value="document">文档</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>

        <a-col :span="16">
          <a-form-item label="标签">
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
        </a-col>
      </a-row>

      <a-form-item label="可见范围">
        <AdmissionScopeSelector
          v-model:scope-type="form.scopeType"
          v-model:scope-target-ids="form.scopeTargetIds"
          :user-role="''"
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
          v-model:fileList="fileList"
          :before-upload="beforeUpload"
          :accept="currentAccept"
          :multiple="true"
          :progress="{ strokeWidth: 2, showInfo: true }"
        >
          <p class="ant-upload-drag-icon">📁</p>
          <p>点击或拖拽上传资源文件（可多选）</p>
          <p class="upload-hint">当前类型允许：{{ currentAccept || '无' }}</p>
        </a-upload-dragger>
      </a-form-item>

      <div class="modal-actions">
        <a-button :disabled="submitting" @click="handleCancel">取消</a-button>
        <permissions-tooltip
          :allowed="canSaveDraft"
          tips="需要 CREATE_RESOURCE 或 VIEW_RESOURCE_ALL 权限"
          v-slot="{ disabled }"
        >
          <a-button type="primary" ghost :loading="submitting" :disabled="disabled" @click="submitDraft">
            保存草稿
          </a-button>
        </permissions-tooltip>
        <permissions-tooltip
          :allowed="canSubmitReview"
          tips="需要同时具备 CREATE_RESOURCE 和 SUBMIT_RESOURCE_REVIEW 权限"
          v-slot="{ disabled }"
        >
          <a-button type="primary" :loading="submitting" :disabled="disabled" @click="submitAndSubmitReview">
            提交审核
          </a-button>
        </permissions-tooltip>
      </div>
    </a-form>
  </a-modal>
</template>

<script setup>
import { computed, reactive, ref, toRef, watch } from 'vue'
import { message, Upload } from 'ant-design-vue'
import { uploadFile } from '@/api/media'
import { createResource, createResourceTag, getResourceTags } from '@/api/resource'
import { submitResource } from '@/api/review'
import { useAuthStore } from '@/stores/auth'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'
import AdmissionScopeSelector from '@/views/exam/components/AdmissionScopeSelector.vue'
import { useCreatableTagSelect } from '@/utils/creatableTagSelect'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:open', 'success'])

const authStore = useAuthStore()
const submitting = ref(false)
const fileList = ref([])
const canSaveDraft = computed(() => authStore.hasAnyPermission(['CREATE_RESOURCE', 'VIEW_RESOURCE_ALL']))
const canSubmitReview = computed(() => authStore.hasAllPermissions(['CREATE_RESOURCE', 'SUBMIT_RESOURCE_REVIEW']))

const ALLOWED_EXTENSIONS = {
  video: ['mp4'],
  document: ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'html', 'htm'],
  image: ['jpg', 'jpeg', 'png', 'webp'],
}

const form = reactive({
  title: '',
  summary: '',
  contentType: 'video',
  scopeType: 'all',
  tags: [],
  scopeTargetIds: [],
})

const {
  tagSearching,
  mergedTagOptions,
  normalizeTags,
  fetchTagOptions: loadTagOptions,
  handleTagSearch,
  handleTagChange,
} = useCreatableTagSelect(toRef(form, 'tags'), {
  fetchTags: getResourceTags,
  createTag: createResourceTag,
  createErrorMessage: (tagName, error) => error?.message || `标签“${tagName}”创建失败`,
})

const currentAccept = computed(() => {
  const extList = ALLOWED_EXTENSIONS[form.contentType] || []
  return extList.map((ext) => `.${ext}`).join(',')
})

watch(
  () => props.open,
  (open) => {
    if (!open) {
      if (!submitting.value) {
        resetForm()
      }
      return
    }
    loadTagOptions().catch(() => {})
  },
  { immediate: true }
)

watch(
  () => form.contentType,
  () => {
    if (!fileList.value.length) return

    const nextList = fileList.value.filter((item) => {
      const rawFile = item.originFileObj || item
      return isAllowedFile(rawFile, form.contentType)
    })

    if (nextList.length !== fileList.value.length) {
      const removedCount = fileList.value.length - nextList.length
      fileList.value = nextList
      message.warning(`已移除 ${removedCount} 个不匹配当前内容类型的文件`)
    }
  }
)

function resetForm() {
  Object.assign(form, {
    title: '',
    summary: '',
    contentType: 'video',
    scopeType: 'all',
    tags: [],
    scopeTargetIds: [],
  })
  fileList.value = []
}

function handleOpenChange(value) {
  if (submitting.value) return
  emit('update:open', value)
}

function handleCancel() {
  if (submitting.value) return
  closeModal()
}

function closeModal() {
  resetForm()
  emit('update:open', false)
}

function getExt(filename = '') {
  const dot = filename.lastIndexOf('.')
  return dot >= 0 ? filename.slice(dot + 1).toLowerCase() : ''
}

function getFileKey(item, index) {
  return item.uid || `${item.name || item.originFileObj?.name || 'file'}-${index}`
}

function isAllowedFile(file, contentType) {
  const ext = getExt(file?.name || file?.filename || '')
  return (ALLOWED_EXTENSIONS[contentType] || []).includes(ext)
}

function patchFileListItem(fileKey, patch) {
  fileList.value = fileList.value.map((item, index) => {
    if (getFileKey(item, index) !== fileKey) return item
    return { ...item, ...patch }
  })
}

function beforeUpload(file) {
  if (!isAllowedFile(file, form.contentType)) {
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
  if (form.scopeType !== 'all' && !form.scopeTargetIds.length) {
    message.warning('请选择可见范围目标')
    return null
  }

  const selectedFiles = fileList.value.map((item, index) => ({
    key: getFileKey(item, index),
    file: item.originFileObj || item,
  }))

  for (const selected of selectedFiles) {
    if (!isAllowedFile(selected.file, form.contentType)) {
      message.warning(`文件类型不匹配当前内容类型（允许：${currentAccept.value}）`)
      return null
    }
  }

  const uploadedFiles = []
  for (const selected of selectedFiles) {
    try {
      patchFileListItem(selected.key, { status: 'uploading', percent: 0 })
      const uploadRes = await uploadFile(selected.file, (percent) => {
        patchFileListItem(selected.key, { status: 'uploading', percent })
      })
      patchFileListItem(selected.key, { status: 'done', percent: 100 })
      uploadedFiles.push(uploadRes)
    } catch (error) {
      patchFileListItem(selected.key, { status: 'error' })
      throw error
    }
  }

  const payload = {
    title: form.title,
    summary: form.summary,
    contentType: form.contentType,
    scopeType: form.scopeType,
    scopeTargetIds: form.scopeTargetIds,
    tags: normalizeTags(form.tags),
    mediaLinks: uploadedFiles.map((file, index) => ({
      mediaFileId: file.id,
      mediaRole: 'main',
      sortOrder: index,
    })),
    coverMediaFileId: uploadedFiles[0]?.id || null,
  }
  return createResource(payload)
}

async function submitDraft() {
  if (!canSaveDraft.value) return
  submitting.value = true
  try {
    const resource = await createDraft()
    if (!resource) return
    message.success('资源已保存为草稿')
    emit('success', { resource, action: 'draft' })
    closeModal()
  } catch (error) {
    message.error(error.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

async function submitAndSubmitReview() {
  if (!canSubmitReview.value) return
  submitting.value = true
  try {
    const resource = await createDraft()
    if (!resource) return
    await submitResource(resource.id)
    message.success('资源已提交审核')
    emit('success', { resource, action: 'submit_review' })
    closeModal()
  } catch (error) {
    message.error(error.message || '提交审核失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.upload-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #8c8c8c;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
