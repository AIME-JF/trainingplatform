<template>
  <a-modal
    :open="open"
    :title="title"
    :ok-text="okText"
    cancel-text="取消"
    :confirm-loading="confirmLoading"
    :destroy-on-close="true"
    centered
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <a-upload-dragger
      v-model:fileList="fileList"
      :before-upload="beforeUpload"
      :max-count="1"
      accept=".xlsx"
    >
      <p class="ant-upload-drag-icon">
        <InboxOutlined class="upload-icon" />
      </p>
      <p>拖拽到此上传</p>
      <p class="upload-hint">{{ hint }}</p>
    </a-upload-dragger>

    <div class="import-modal-actions">
      <a-button type="link" @click="emit('download-template')">{{ templateButtonText }}</a-button>
    </div>
  </a-modal>
</template>

<script setup>
import { InboxOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { ref, watch } from 'vue'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '导入数据',
  },
  okText: {
    type: String,
    default: '开始导入',
  },
  confirmLoading: {
    type: Boolean,
    default: false,
  },
  templateButtonText: {
    type: String,
    default: '下载模板',
  },
  hint: {
    type: String,
    default: '或点击选择 Excel 文件（仅支持 .xlsx）',
  },
})

const emit = defineEmits(['update:open', 'submit', 'download-template'])

const fileList = ref([])

watch(
  () => props.open,
  (open) => {
    if (!open) {
      fileList.value = []
    }
  }
)

function beforeUpload() {
  return false
}

function handleCancel() {
  emit('update:open', false)
}

function handleSubmit() {
  const selected = fileList.value[0]
  const file = selected?.originFileObj || selected
  if (!file) {
    message.warning('请先选择导入文件')
    return
  }
  emit('submit', file)
}
</script>

<style scoped>
.upload-icon {
  font-size: 24px;
  color: #003087;
}

.upload-hint {
  font-size: 12px;
  color: #999;
}

.import-modal-actions {
  margin-top: 12px;
  text-align: left;
}
</style>
