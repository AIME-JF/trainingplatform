<template>
  <a-modal
    :open="open"
    title="导入课表"
    :width="800"
    :destroy-on-close="true"
    :mask-closable="false"
    centered
    @cancel="handleCancel"
  >
    <a-steps :current="currentStepIndex" size="small" style="margin-bottom: 24px">
      <a-step title="上传文件" />
      <a-step title="检查错误" />
      <a-step title="确认导入" />
    </a-steps>

    <!-- Step 1: Upload -->
    <div v-if="step === 'upload'">
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
        <p class="upload-hint">或点击选择 Excel 文件（仅支持 .xlsx）</p>
      </a-upload-dragger>
    </div>

    <!-- Step 2: Errors -->
    <div v-if="step === 'errors'">
      <a-alert
        v-if="hasBlockingErrors"
        type="error"
        message="存在阻断性错误，请修正文件后重新上传"
        show-icon
        style="margin-bottom: 16px"
      />
      <a-table
        :data-source="allErrors"
        :pagination="false"
        row-key="key"
        size="small"
        :scroll="{ y: 400 }"
      >
        <a-table-column title="行号" data-index="row" key="row" width="80" />
        <a-table-column title="错误信息" data-index="message" key="message" />
        <a-table-column title="类型" key="type" width="100">
          <template #default="{ record }">
            <a-tag v-if="!record.skippable" color="red">阻断</a-tag>
            <a-tag v-else color="orange">可跳过</a-tag>
          </template>
        </a-table-column>
        <a-table-column title="操作" key="action" width="100">
          <template #default="{ record }">
            <a-checkbox
              v-if="record.skippable"
              :checked="skipRows.has(record.row)"
              @change="(e) => toggleSkipRow(record.row, e.target.checked)"
            >
              跳过
            </a-checkbox>
          </template>
        </a-table-column>
      </a-table>
    </div>

    <!-- Step 3: Preview -->
    <div v-if="step === 'preview'">
      <a-alert
        v-if="instructorsToCreate.length > 0"
        type="warning"
        show-icon
        style="margin-bottom: 16px"
      >
        <template #message>
          以下教官不存在，确认后将自动创建账号（默认密码 Police@123456）：{{ instructorsToCreate.join('、') }}
        </template>
      </a-alert>

      <div style="margin-bottom: 16px; color: #666">
        共 <strong>{{ previewData.courses?.length || 0 }}</strong> 门课程，<strong>{{ totalSessionCount }}</strong> 个课次
        <template v-if="skipRows.size > 0">，跳过 <strong>{{ skipRows.size }}</strong> 行</template>
      </div>

      <div class="preview-course-list" style="max-height: 450px; overflow-y: auto">
        <a-card
          v-for="(course, idx) in previewData.courses"
          :key="idx"
          size="small"
          style="margin-bottom: 12px"
        >
          <template #title>
            <span>{{ course.name }}</span>
            <a-tag v-if="course.courseResourceMatched" color="green" style="margin-left: 8px">已关联课程资源</a-tag>
            <a-tag v-else color="blue" style="margin-left: 8px">自定义课程</a-tag>
          </template>
          <a-descriptions :column="1" size="small" :bordered="false">
            <a-descriptions-item label="主讲教官">
              {{ course.primaryInstructorName || '未指定' }}
              <template v-if="course.primaryInstructorName">
                <a-tag v-if="course.primaryInstructorExists" color="green" size="small" style="margin-left: 4px">已有账号</a-tag>
                <a-tag v-else color="orange" size="small" style="margin-left: 4px">将自动创建</a-tag>
              </template>
            </a-descriptions-item>
            <a-descriptions-item v-if="course.assistantInstructorNames?.length" label="带教教官">
              <template v-for="(aname, aiIdx) in course.assistantInstructorNames" :key="aiIdx">
                <span v-if="aiIdx > 0">、</span>
                {{ aname }}
                <a-tag v-if="!course.assistantsToCreate?.includes(aname)" color="green" size="small" style="margin-left: 2px">已有账号</a-tag>
                <a-tag v-else color="orange" size="small" style="margin-left: 2px">将自动创建</a-tag>
              </template>
            </a-descriptions-item>
            <a-descriptions-item label="课次">
              {{ course.sessions?.length || 0 }} 个课次
              <div v-if="course.sessions?.length" style="margin-top: 4px">
                <a-tag v-for="(s, sIdx) in course.sessions" :key="sIdx" style="margin-bottom: 4px">
                  {{ s.date }} {{ s.timeRange }}
                </a-tag>
              </div>
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
      </div>
    </div>

    <template #footer>
      <div class="import-modal-footer">
        <!-- Step 1 footer -->
        <template v-if="step === 'upload'">
          <PermissionsTooltip :allowed="canDownloadTemplate" :tips="downloadTemplateTooltip">
            <template #default="{ disabled }">
              <a-button type="link" :disabled="disabled" @click="handleDownloadTemplate">
                下载模板
              </a-button>
            </template>
          </PermissionsTooltip>
          <a-space>
            <a-button @click="handleCancel">取消</a-button>
            <PermissionsTooltip :allowed="canSubmit" :tips="submitTooltip">
              <template #default="{ disabled }">
                <a-button type="primary" :loading="loading" :disabled="disabled" @click="handleParse">
                  开始解析
                </a-button>
              </template>
            </PermissionsTooltip>
          </a-space>
        </template>

        <!-- Step 2 footer -->
        <template v-if="step === 'errors'">
          <div></div>
          <a-space>
            <a-button @click="goBackToUpload">返回上传</a-button>
            <a-button
              type="primary"
              :disabled="hasBlockingErrors"
              @click="goToPreviewFromErrors"
            >
              跳过选中并继续
            </a-button>
          </a-space>
        </template>

        <!-- Step 3 footer -->
        <template v-if="step === 'preview'">
          <div></div>
          <a-space>
            <a-button @click="goBack">返回</a-button>
            <a-button type="primary" :loading="loading" @click="handleConfirm">
              确认导入
            </a-button>
          </a-space>
        </template>
      </div>
    </template>
  </a-modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { InboxOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'
import { previewScheduleImport, confirmScheduleImport, downloadScheduleImportTemplate } from '@/api/training'
import { downloadBlob } from '@/utils/download'

const props = defineProps({
  open: { type: Boolean, default: false },
  trainingId: { type: [Number, String], required: true },
  canSubmit: { type: Boolean, default: true },
  canDownloadTemplate: { type: Boolean, default: true },
  submitTooltip: { type: String, default: '您没有权限执行导入操作' },
  downloadTemplateTooltip: { type: String, default: '您没有权限下载导入模板' },
})

const emit = defineEmits(['update:open', 'import-success'])

const step = ref('upload')
const fileList = ref([])
const file = ref(null)
const previewData = ref({})
const loading = ref(false)
const skipRows = ref(new Set())
const allErrors = ref([])
const hasBlockingErrors = ref(false)
const hadErrors = ref(false)

const currentStepIndex = computed(() => {
  if (step.value === 'upload') return 0
  if (step.value === 'errors') return 1
  if (step.value === 'preview') return 2
  return 0
})

const instructorsToCreate = computed(() => {
  return previewData.value.instructorsToCreate || []
})

const totalSessionCount = computed(() => {
  return (previewData.value.courses || []).reduce((sum, c) => sum + (c.sessions?.length || 0), 0)
})

watch(
  () => props.open,
  (val) => {
    if (!val) {
      resetState()
    }
  }
)

function resetState() {
  step.value = 'upload'
  fileList.value = []
  file.value = null
  previewData.value = {}
  loading.value = false
  skipRows.value = new Set()
  allErrors.value = []
  hasBlockingErrors.value = false
  hadErrors.value = false
}

function beforeUpload() {
  return false
}

function handleCancel() {
  emit('update:open', false)
}

function toggleSkipRow(row, checked) {
  const newSet = new Set(skipRows.value)
  if (checked) {
    newSet.add(row)
  } else {
    newSet.delete(row)
  }
  skipRows.value = newSet
}

async function handleDownloadTemplate() {
  try {
    const blob = await downloadScheduleImportTemplate(props.trainingId)
    downloadBlob(blob, '培训班课表导入模板.xlsx')
  } catch (error) {
    message.error(error?.message || '下载模板失败')
  }
}

async function handleParse() {
  const selected = fileList.value[0]
  const rawFile = selected?.originFileObj || selected
  if (!rawFile) {
    message.warning('请先选择导入文件')
    return
  }
  file.value = rawFile
  loading.value = true
  try {
    const result = await previewScheduleImport(props.trainingId, rawFile)
    previewData.value = result

    const errors = result.errors || []
    const blocking = errors.filter((e) => !e.skippable)
    const skippable = errors.filter((e) => e.skippable)
    const mappedErrors = errors.map((e, idx) => ({
      key: idx,
      row: e.row,
      message: e.message,
      skippable: e.skippable,
    }))

    if (blocking.length > 0 || skippable.length > 0) {
      allErrors.value = mappedErrors
      hasBlockingErrors.value = blocking.length > 0
      hadErrors.value = true
      step.value = 'errors'
    } else {
      step.value = 'preview'
    }
  } catch (error) {
    message.error(error?.message || '解析文件失败')
  } finally {
    loading.value = false
  }
}

function goBackToUpload() {
  step.value = 'upload'
  skipRows.value = new Set()
}

function goToPreviewFromErrors() {
  step.value = 'preview'
}

function goBack() {
  if (hadErrors.value) {
    step.value = 'errors'
  } else {
    step.value = 'upload'
  }
}

async function handleConfirm() {
  loading.value = true
  try {
    const skipArray = Array.from(skipRows.value)
    await confirmScheduleImport(props.trainingId, file.value, skipArray)
    message.success('课表导入成功')
    emit('update:open', false)
    emit('import-success')
  } catch (error) {
    message.error(error?.message || '导入失败')
  } finally {
    loading.value = false
  }
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
