<template>
  <a-modal
    :open="open"
    title="移动到文件夹"
    :footer="null"
    :destroy-on-close="true"
    @cancel="handleClose"
  >
    <a-form layout="vertical">
      <a-form-item label="目标文件夹">
        <a-select v-model:value="targetFolderId" allow-clear placeholder="移动到根目录">
          <a-select-option :value="null">根目录</a-select-option>
          <a-select-option v-for="folder in folderOptions" :key="folder.value" :value="folder.value">
            {{ folder.label }}
          </a-select-option>
        </a-select>
      </a-form-item>
    </a-form>

    <div class="modal-footer">
      <a-button @click="handleClose">取消</a-button>
      <a-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ submitting ? '移动中' : '确认移动' }}
      </a-button>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { moveLibraryItem } from '@/api/library'

interface FolderOption {
  value: number
  label: string
}

const props = withDefaults(defineProps<{
  open?: boolean
  itemId?: number | null
  currentFolderId?: number | null
  folderOptions?: FolderOption[]
}>(), {
  open: false,
  itemId: null,
  currentFolderId: null,
  folderOptions: () => [],
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  success: []
}>()

const targetFolderId = ref<number | null>(null)
const submitting = ref(false)

watch(() => props.open, (visible) => {
  if (!visible) {
    return
  }
  targetFolderId.value = props.currentFolderId ?? null
})

async function handleSubmit() {
  if (!props.itemId) {
    return
  }
  submitting.value = true
  try {
    await moveLibraryItem(props.itemId, { folder_id: targetFolderId.value })
    message.success('资源已移动')
    emit('success')
    emit('update:open', false)
  } catch (error) {
    message.error(error instanceof Error ? error.message : '移动失败')
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
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
