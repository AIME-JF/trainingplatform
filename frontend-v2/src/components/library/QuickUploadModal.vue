<template>
  <a-modal
    :open="open"
    title="批量导入资源"
    :footer="null"
    :destroy-on-close="true"
    @cancel="handleClose"
  >
    <div class="upload-panel">
      <div class="upload-tip">
        支持 `mp4 / mp3 / wav / m4a / pdf / docx / pptx / xlsx / txt / md / csv / html / htm / json / xml / log / jpg / jpeg / png / bmp / tiff / webp / gif`
      </div>

      <a-form layout="vertical">
        <a-form-item label="目标文件夹">
          <a-select v-model:value="targetFolderId" allow-clear placeholder="默认保存到根目录">
            <a-select-option :value="null">根目录</a-select-option>
            <a-select-option v-for="folder in folderOptions" :key="folder.value" :value="folder.value">
              {{ folder.label }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="选择文件">
          <div class="picker-box">
            <a-button type="primary" @click="triggerFilePicker">选择文件</a-button>
            <span class="picker-hint">系统会自动识别文件类型，并以文件名创建资源条目。</span>
            <input
              ref="fileInputRef"
              type="file"
              multiple
              class="hidden-input"
              @change="handleFileChange"
            />
          </div>
        </a-form-item>
      </a-form>

      <div v-if="selectedFiles.length" class="file-list">
        <div v-for="file in selectedFiles" :key="`${file.name}_${file.size}_${file.lastModified}`" class="file-item">
          <div>
            <div class="file-name">{{ file.name }}</div>
            <div class="file-meta">{{ formatFileSize(file.size) }}</div>
          </div>
          <a-button type="text" danger size="small" @click="removeFile(file)">移除</a-button>
        </div>
      </div>
      <a-empty v-else description="尚未选择文件" />

      <div class="modal-footer">
        <a-button @click="handleClose">取消</a-button>
        <a-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ submitting ? '导入中' : '开始导入' }}
        </a-button>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { createLibraryItemsFromFiles, uploadLibraryFile } from '@/api/library'

interface FolderOption {
  value: number
  label: string
}

const props = withDefaults(defineProps<{
  open?: boolean
  folderOptions?: FolderOption[]
  defaultFolderId?: number | null
}>(), {
  open: false,
  folderOptions: () => [],
  defaultFolderId: null,
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  success: []
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)
const selectedFiles = ref<File[]>([])
const targetFolderId = ref<number | null>(null)
const submitting = ref(false)

watch(() => props.open, (visible) => {
  if (!visible) {
    selectedFiles.value = []
    targetFolderId.value = null
    return
  }
  targetFolderId.value = props.defaultFolderId ?? null
})

function triggerFilePicker() {
  fileInputRef.value?.click()
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement | null
  const files = Array.from(input?.files || [])
  const existingKeys = new Set(selectedFiles.value.map((item) => `${item.name}_${item.size}_${item.lastModified}`))
  files.forEach((file) => {
    const key = `${file.name}_${file.size}_${file.lastModified}`
    if (!existingKeys.has(key)) {
      existingKeys.add(key)
      selectedFiles.value.push(file)
    }
  })
  if (input) {
    input.value = ''
  }
}

function removeFile(target: File) {
  selectedFiles.value = selectedFiles.value.filter(
    (file) => `${file.name}_${file.size}_${file.lastModified}` !== `${target.name}_${target.size}_${target.lastModified}`,
  )
}

function formatFileSize(size: number) {
  if (size >= 1024 * 1024) {
    return `${(size / 1024 / 1024).toFixed(1)} MB`
  }
  if (size >= 1024) {
    return `${Math.round(size / 1024)} KB`
  }
  return `${size} B`
}

async function handleSubmit() {
  if (!selectedFiles.value.length) {
    message.warning('请先选择文件')
    return
  }
  submitting.value = true
  try {
    const uploadedIds: number[] = []
    for (const file of selectedFiles.value) {
      const result = await uploadLibraryFile(file)
      uploadedIds.push(result.id)
    }
    await createLibraryItemsFromFiles({
      folder_id: targetFolderId.value,
      media_file_ids: uploadedIds,
    })
    message.success(`已成功导入 ${uploadedIds.length} 个文件`)
    emit('success')
    emit('update:open', false)
  } catch (error) {
    message.error(error instanceof Error ? error.message : '导入失败')
  } finally {
    submitting.value = false
  }
}

function handleClose() {
  if (submitting.value) {
    return
  }
  emit('update:open', false)
}
</script>

<style scoped>
.upload-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-tip {
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--v2-primary-light);
  color: var(--v2-text-secondary);
  font-size: 12px;
  line-height: 1.6;
}

.picker-box {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.picker-hint {
  color: var(--v2-text-secondary);
  font-size: 12px;
}

.hidden-input {
  display: none;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 260px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--v2-border);
  border-radius: 14px;
  background: var(--v2-bg-card);
}

.file-name {
  color: var(--v2-text-primary);
  font-weight: 600;
}

.file-meta {
  margin-top: 4px;
  color: var(--v2-text-secondary);
  font-size: 12px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
