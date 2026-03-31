<template>
  <a-modal
    :open="open"
    :title="title"
    :confirm-loading="confirmLoading"
    :destroy-on-close="true"
    centered
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

    <template #footer>
      <div class="import-modal-footer">
        <PermissionsTooltip
          :allowed="canDownloadTemplate"
          :tips="downloadTemplateTooltip"
        >
          <template #default="{ disabled }">
            <a-button type="link" :disabled="disabled" @click="emit('download-template')">
              {{ templateButtonText }}
            </a-button>
          </template>
        </PermissionsTooltip>

        <a-space>
          <a-button @click="handleCancel">取消</a-button>
          <PermissionsTooltip
            :allowed="canSubmit"
            :tips="submitTooltip"
          >
            <template #default="{ disabled }">
              <a-button
                type="primary"
                :loading="confirmLoading"
                :disabled="disabled"
                @click="handleSubmit"
              >
                {{ okText }}
              </a-button>
            </template>
          </PermissionsTooltip>
        </a-space>
      </div>
    </template>
  </a-modal>
</template>

<script setup>
import { InboxOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { ref, watch } from 'vue'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

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
  canSubmit: {
    type: Boolean,
    default: true,
  },
  submitTooltip: {
    type: String,
    default: '您没有权限执行导入操作',
  },
  canDownloadTemplate: {
    type: Boolean,
    default: true,
  },
  downloadTemplateTooltip: {
    type: String,
    default: '您没有权限下载导入模板',
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

.import-modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
