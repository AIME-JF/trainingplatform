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
          <a-select-option
            v-for="folder in folderOptions"
            :key="folder.value"
            :value="folder.value"
          >
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

<script setup>
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { moveLibraryItem } from '@/api/library'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  itemId: {
    type: [Number, null],
    default: null,
  },
  currentFolderId: {
    type: [Number, null],
    default: null,
  },
  folderOptions: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:open', 'success'])

const targetFolderId = ref(null)
const submitting = ref(false)

watch(
  () => props.open,
  (visible) => {
    if (!visible) {
      return
    }
    targetFolderId.value = props.currentFolderId ?? null
  },
)

async function handleSubmit() {
  if (!props.itemId) {
    return
  }
  submitting.value = true
  try {
    await moveLibraryItem(props.itemId, {
      folderId: targetFolderId.value,
    })
    message.success('资源已移动')
    emit('success')
    emit('update:open', false)
  } catch (error) {
    message.error(error?.message || '移动失败')
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
