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
          <a-textarea v-model:value="form.summary" :rows="4" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="8">
            <a-form-item label="内容类型">
              <a-select v-model:value="form.contentType">
                <a-select-option value="video">视频</a-select-option>
                <a-select-option value="document">文档</a-select-option>
                <a-select-option value="image_text">图文</a-select-option>
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
              <a-select v-model:value="form.tags" mode="tags" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="上传文件" required>
          <a-upload-dragger
            v-model:fileList="fileList"
            :before-upload="beforeUpload"
            :max-count="1"
            :accept="currentAccept"
          >
            <p class="ant-upload-drag-icon">📁</p>
            <p>点击或拖拽上传资源文件</p>
          </a-upload-dragger>
        </a-form-item>

        <a-space>
          <a-button type="primary" :loading="submitting" @click="submit">保存草稿</a-button>
          <a-button :loading="submitting" @click="submitAndPublish">保存并发布</a-button>
        </a-space>
      </a-form>
    </a-card>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message, Upload } from 'ant-design-vue'
import { uploadFile } from '@/api/media'
import { createResource, publishResource } from '@/api/resource'

const router = useRouter()
const submitting = ref(false)
const fileList = ref([])

const ALLOWED_EXTENSIONS = {
  video: ['mp4'],
  document: ['pdf', 'doc', 'docx', 'ppt', 'pptx'],
  image_text: ['jpg', 'jpeg', 'png', 'webp'],
}

const form = reactive({
  title: '',
  summary: '',
  contentType: 'video',
  visibilityType: 'public',
  tags: [],
  visibilityScopes: [],
})

const currentAccept = computed(() => {
  const extList = ALLOWED_EXTENSIONS[form.contentType] || []
  return extList.map((ext) => `.${ext}`).join(',')
})

watch(
  () => form.contentType,
  () => {
    if (!fileList.value.length) return
    const file = fileList.value[0].originFileObj || fileList.value[0]
    if (!isAllowedFile(file, form.contentType)) {
      fileList.value = []
      message.warning('已清空不匹配当前内容类型的文件，请重新上传')
    }
  }
)

function getExt(filename = '') {
  const dot = filename.lastIndexOf('.')
  return dot >= 0 ? filename.slice(dot + 1).toLowerCase() : ''
}

function isAllowedFile(file, contentType) {
  const ext = getExt(file?.name || file?.filename || '')
  return (ALLOWED_EXTENSIONS[contentType] || []).includes(ext)
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

  const rawFile = fileList.value[0].originFileObj || fileList.value[0]
  if (!isAllowedFile(rawFile, form.contentType)) {
    message.warning(`文件类型不匹配当前内容类型（允许：${currentAccept.value}）`)
    return null
  }

  const uploadRes = await uploadFile(rawFile)
  const payload = {
    title: form.title,
    summary: form.summary,
    contentType: form.contentType,
    visibilityType: form.visibilityType,
    tags: form.tags,
    visibilityScopes: form.visibilityScopes,
    mediaLinks: [{ mediaFileId: uploadRes.id, mediaRole: 'main', sortOrder: 0 }],
    coverMediaFileId: uploadRes.id,
  }
  return createResource(payload)
}

async function submit() {
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

async function submitAndPublish() {
  submitting.value = true
  try {
    const res = await createDraft()
    if (!res) return
    await publishResource(res.id)
    message.success('资源创建并发布成功')
    router.push('/resource/library')
  } catch (e) {
    message.error(e.message || '发布失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.resource-upload-page { padding: 0; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
</style>
