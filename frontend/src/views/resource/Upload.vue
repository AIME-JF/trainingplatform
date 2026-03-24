<template>
  <div class="resource-upload-page">
    <div class="page-header">
      <h2>上传资源</h2>
      <a-button @click="$router.push('/resource/library')">返回资源库</a-button>
    </div>

    <a-card :bordered="false">
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

          <a-col :span="8">
            <a-form-item label="可见范围">
              <a-select v-model:value="form.visibilityType">
                <a-select-option value="public">全员</a-select-option>
                <a-select-option value="department">部门</a-select-option>
                <a-select-option value="police_type">警种</a-select-option>
                <a-select-option value="custom">自定义</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>

          <a-col :span="8">
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

        <a-space>
          <permissions-tooltip
            :allowed="canSaveDraft"
            tips="需要 CREATE_RESOURCE 或 VIEW_RESOURCE_ALL 权限"
            v-slot="{ disabled }"
          >
            <a-button type="primary" :loading="submitting" :disabled="disabled" @click="submit">保存草稿</a-button>
          </permissions-tooltip>
          <permissions-tooltip
            :allowed="canSubmitReview"
            tips="需要同时具备 CREATE_RESOURCE 和 SUBMIT_RESOURCE_REVIEW 权限"
            v-slot="{ disabled }"
          >
            <a-button :loading="submitting" :disabled="disabled" @click="submitAndSubmitReview">提交审核</a-button>
          </permissions-tooltip>
        </a-space>
      </a-form>
    </a-card>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, toRef, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message, Upload } from 'ant-design-vue'
import { uploadFile } from '@/api/media'
import { createResource, createResourceTag, getResourceTags } from '@/api/resource'
import { submitResource } from '@/api/review'
import { useAuthStore } from '@/stores/auth'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'
import { useCreatableTagSelect } from '@/utils/creatableTagSelect'

const router = useRouter()
const authStore = useAuthStore()
const submitting = ref(false)
const fileList = ref([])
const canSaveDraft = computed(() => authStore.hasAnyPermission(['CREATE_RESOURCE', 'VIEW_RESOURCE_ALL']))
const canSubmitReview = computed(() => authStore.hasAllPermissions(['CREATE_RESOURCE', 'SUBMIT_RESOURCE_REVIEW']))

const ALLOWED_EXTENSIONS = {
  video: ['mp4'],
  document: ['pdf', 'doc', 'docx', 'ppt', 'pptx'],
  image: ['jpg', 'jpeg', 'png', 'webp'],
}

const form = reactive({
  title: '',
  summary: '',
  contentType: 'video',
  visibilityType: 'public',
  tags: [],
  visibilityScopes: [],
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

onMounted(() => {
  loadTagOptions().catch(() => {})
})


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
    } catch (e) {
      patchFileListItem(selected.key, { status: 'error' })
      throw e
    }
  }

  const payload = {
    title: form.title,
    summary: form.summary,
    contentType: form.contentType,
    visibilityType: form.visibilityType,
    tags: normalizeTags(form.tags),
    visibilityScopes: form.visibilityScopes,
    mediaLinks: uploadedFiles.map((file, index) => ({
      mediaFileId: file.id,
      mediaRole: 'main',
      sortOrder: index,
    })),
    coverMediaFileId: uploadedFiles[0]?.id || null,
  }
  return createResource(payload)
}

async function submit() {
  if (!canSaveDraft.value) return
  submitting.value = true
  try {
    const res = await createDraft()
    if (!res) return
    message.success('资源已保存为草稿')
    router.push('/resource/my')
  } catch (e) {
    message.error(e.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

async function submitAndSubmitReview() {
  if (!canSubmitReview.value) return
  submitting.value = true
  try {
    const res = await createDraft()
    if (!res) return
    await submitResource(res.id)
    message.success('资源已提交审核')
    router.push('/resource/my')
  } catch (e) {
    message.error(e.message || '提交审核失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.resource-upload-page { padding: 0; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.upload-hint { margin-top: 6px; font-size: 12px; color: #8c8c8c; }
</style>

