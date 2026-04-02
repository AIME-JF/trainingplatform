<template>
  <a-modal
    :open="open"
    wrap-class-name="resource-modal"
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
            <a-select v-model:value="form.content_type">
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
          v-model:file-list="fileList"
          :before-upload="beforeUpload"
          :accept="currentAccept"
          :multiple="true"
        >
          <p class="upload-title">点击或拖拽上传资源文件</p>
          <p class="upload-hint">当前类型允许：{{ currentAccept || '无' }}</p>
        </a-upload-dragger>
      </a-form-item>

      <div class="modal-actions">
        <a-button :disabled="submitting" @click="handleCancel">取消</a-button>
        <a-button type="primary" ghost :loading="submitting" @click="submitDraft">
          保存草稿
        </a-button>
        <a-button type="primary" :loading="submitting" @click="submitAndSubmitReview">
          提交审核
        </a-button>
      </div>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { computed, reactive, ref, toRef, watch } from 'vue'
import { message, Upload } from 'ant-design-vue'
import type { UploadFile } from 'ant-design-vue'
import { createResource, createResourceTag, listResourceTags, submitResourceReview, uploadMediaFile } from '@/api/learning-resource'
import { useCreatableTagSelect } from '@/composables/useCreatableTagSelect'
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
.upload-title {
  font-size: 15px;
  color: var(--v2-text-primary);
}

.upload-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
