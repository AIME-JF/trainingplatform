<template>
  <a-modal
    :open="open"
    :title="isAdmission ? '快捷创建准入考试' : '快捷创建考试'"
    width="900px"
    :footer="null"
    @cancel="$emit('update:open', false)"
  >
    <a-steps :current="step" size="small" style="margin-bottom: 24px">
      <a-step title="选择试卷" />
      <a-step title="考试配置" />
    </a-steps>

    <!-- Step 1: 选择试卷 -->
    <div v-show="step === 0">
      <div style="margin-bottom: 12px; display: flex; gap: 12px">
        <a-input-search
          v-model:value="paperSearch"
          placeholder="搜索试卷名称..."
          style="width: 300px"
          allow-clear
        />
        <a-select v-model:value="paperTypeFilter" style="width: 140px" allow-clear placeholder="试卷类型">
          <a-select-option value="formal">正式考核</a-select-option>
          <a-select-option value="quiz">测验</a-select-option>
        </a-select>
      </div>
      <a-table
        :data-source="filteredPapers"
        :columns="paperColumns"
        size="small"
        :loading="papersLoading"
        :pagination="{ pageSize: 8 }"
        :row-selection="{ type: 'radio', selectedRowKeys: selectedPaperKeys, onChange: onPaperSelect }"
        :custom-row="(record) => ({ onClick: () => onPaperSelect([record.id]) })"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'title'">
            <span style="font-weight: 500">{{ record.title }}</span>
          </template>
          <template v-if="column.key === 'type'">
            <a-tag :color="record.type === 'formal' ? 'blue' : 'green'">{{ record.type === 'formal' ? '正式' : '测验' }}</a-tag>
          </template>
          <template v-if="column.key === 'info'">
            {{ record.questionCount || 0 }}题 / {{ record.totalScore || 0 }}分 / {{ record.duration || 0 }}分钟
          </template>
          <template v-if="column.key === 'createdAt'">
            {{ formatTime(record.createdAt) }}
          </template>
          <template v-if="column.key === 'preview'">
            <a-button type="link" size="small" @click.stop="previewPaper(record)">预览</a-button>
          </template>
        </template>
      </a-table>
      <div style="text-align: right; margin-top: 16px">
        <a-button type="primary" :disabled="!selectedPaperId" @click="goToConfig">
          下一步
        </a-button>
      </div>
    </div>

    <!-- Step 2: 考试配置 -->
    <div v-show="step === 1">
      <div class="selected-paper-info" v-if="selectedPaper">
        <span>已选试卷：</span>
        <strong>{{ selectedPaper.title }}</strong>
        <span class="paper-meta">（{{ selectedPaper.questionCount || 0 }}题 / {{ selectedPaper.totalScore || 0 }}分）</span>
        <a-button type="link" size="small" @click="step = 0">重新选择</a-button>
      </div>

      <a-form layout="vertical" style="margin-top: 16px; max-width: 600px">
        <a-form-item label="考试名称" required>
          <a-input v-model:value="examForm.title" placeholder="例：第一单元结课测验" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="考试状态">
              <a-select v-model:value="examForm.status">
                <a-select-option value="upcoming">未开始</a-select-option>
                <a-select-option value="active">进行中</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="考试时长（分钟）">
              <a-input-number v-model:value="examForm.duration" :min="5" :max="480" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="考试开放时间" required>
          <a-range-picker
            v-model:value="examDateRange"
            show-time
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
            :placeholder="['开始时间', '结束时间']"
          />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="及格分数">
              <a-input-number v-model:value="examForm.passingScore" :min="0" :max="999" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="最大考试次数">
              <a-input-number v-model:value="examForm.maxAttempts" :min="1" :max="99" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="考试说明">
          <a-textarea v-model:value="examForm.description" :rows="3" placeholder="可选" />
        </a-form-item>
      </a-form>

      <div style="display: flex; justify-content: space-between; margin-top: 16px">
        <a-button @click="step = 0">上一步</a-button>
        <a-button type="primary" :loading="submitting" @click="handleSubmit">创建考试</a-button>
      </div>
    </div>
  </a-modal>

  <!-- 试卷预览弹窗 -->
  <a-modal
    v-model:open="showPaperPreview"
    :title="previewPaperData?.title || '试卷预览'"
    width="800px"
    :footer="null"
  >
    <div v-if="previewLoading" style="text-align: center; padding: 40px">
      <a-spin />
    </div>
    <template v-else-if="previewPaperData">
      <div class="preview-meta">
        <a-tag>{{ previewPaperData.type === 'formal' ? '正式考核' : '测验' }}</a-tag>
        <span>{{ previewPaperData.questionCount || 0 }} 题</span>
        <span>总分 {{ previewPaperData.totalScore || 0 }}</span>
        <span>时长 {{ previewPaperData.duration || 0 }} 分钟</span>
      </div>
      <a-divider style="margin: 12px 0" />
      <div v-if="previewPaperData.questions?.length" class="preview-questions">
        <div v-for="(q, idx) in previewPaperData.questions" :key="q.id || idx" class="preview-q-item">
          <div class="preview-q-header">
            <span class="preview-q-index">{{ idx + 1 }}.</span>
            <a-tag size="small">{{ { single_choice: '单选', multiple_choice: '多选', true_false: '判断', fill_blank: '填空', essay: '简答' }[q.type] || q.type }}</a-tag>
            <span class="preview-q-score">{{ q.score || 0 }}分</span>
          </div>
          <div class="preview-q-content">{{ q.content || q.title || '-' }}</div>
        </div>
      </div>
      <a-empty v-else description="暂无题目信息" />
    </template>
  </a-modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { getExamPapers, getExamPaperDetail, createExam, createAdmissionExam } from '@/api/exam'

const props = defineProps({
  open: { type: Boolean, default: false },
  trainingId: { type: [Number, String], default: 0 },
  isAdmission: { type: Boolean, default: false },
})

const emit = defineEmits(['update:open', 'success'])

const step = ref(0)
const papersLoading = ref(false)
const papers = ref([])
const paperSearch = ref('')
const paperTypeFilter = ref(undefined)
const selectedPaperKeys = ref([])
const submitting = ref(false)
const examDateRange = ref([])
const showPaperPreview = ref(false)
const previewPaperData = ref(null)
const previewLoading = ref(false)

const examForm = ref({
  title: '',
  status: 'upcoming',
  duration: 60,
  passingScore: 60,
  maxAttempts: 1,
  description: '',
})

const selectedPaperId = computed(() => selectedPaperKeys.value[0] || null)
const selectedPaper = computed(() => papers.value.find(p => p.id === selectedPaperId.value))

const filteredPapers = computed(() => {
  return papers.value.filter(p => {
    if (paperSearch.value && !p.title?.toLowerCase().includes(paperSearch.value.toLowerCase())) return false
    if (paperTypeFilter.value && p.type !== paperTypeFilter.value) return false
    return true
  })
})

const paperColumns = [
  { title: '试卷名称', key: 'title', ellipsis: true },
  { title: '类型', key: 'type', width: 80 },
  { title: '题量 / 总分 / 时长', key: 'info', width: 200 },
  { title: '创建时间', key: 'createdAt', width: 160 },
  { title: '', key: 'preview', width: 70 },
]

function formatTime(value) {
  if (!value) return '-'
  return String(value).replace('T', ' ').replace(/\+.*$/, '').slice(0, 16)
}

function onPaperSelect(keys) {
  selectedPaperKeys.value = keys
}

function goToConfig() {
  if (!selectedPaper.value) return
  const p = selectedPaper.value
  examForm.value.title = p.title ? `${p.title} - 考试` : ''
  examForm.value.duration = p.duration || 60
  examForm.value.passingScore = Math.floor((p.totalScore || 100) * 0.6)
  step.value = 1
}

async function previewPaper(record) {
  showPaperPreview.value = true
  previewLoading.value = true
  previewPaperData.value = null
  try {
    const detail = await getExamPaperDetail(record.id)
    previewPaperData.value = detail
  } catch {
    previewPaperData.value = record
  } finally {
    previewLoading.value = false
  }
}

async function fetchPapers() {
  papersLoading.value = true
  try {
    const res = await getExamPapers({ size: -1, status: 'published' })
    papers.value = res?.items || res || []
  } catch {
    papers.value = []
  } finally {
    papersLoading.value = false
  }
}

async function handleSubmit() {
  if (!selectedPaperId.value) { message.warning('请先选择试卷'); return }
  if (!examForm.value.title) { message.warning('请填写考试名称'); return }
  if (!examDateRange.value?.length) { message.warning('请选择考试开放时间'); return }

  submitting.value = true
  try {
    const payload = {
      title: examForm.value.title,
      paperId: selectedPaperId.value,
      description: examForm.value.description || undefined,
      type: selectedPaper.value?.type || 'formal',
      status: examForm.value.status,
      duration: examForm.value.duration,
      passingScore: examForm.value.passingScore,
      maxAttempts: examForm.value.maxAttempts,
      startTime: examDateRange.value[0],
      endTime: examDateRange.value[1],
    }
    if (props.isAdmission) {
      await createAdmissionExam(payload)
    } else {
      payload.trainingId = Number(props.trainingId)
      await createExam(payload)
    }
    message.success(props.isAdmission ? '准入考试创建成功' : '考试创建成功')
    emit('update:open', false)
    emit('success')
  } catch (error) {
    message.error(error?.message || '创建考试失败')
  } finally {
    submitting.value = false
  }
}

function resetState() {
  step.value = 0
  selectedPaperKeys.value = []
  paperSearch.value = ''
  paperTypeFilter.value = undefined
  examDateRange.value = []
  showPaperPreview.value = false
  previewPaperData.value = null
  examForm.value = {
    title: '',
    status: 'upcoming',
    duration: 60,
    passingScore: 60,
    maxAttempts: 1,
    description: '',
  }
}

watch(() => props.open, (val) => {
  if (val) {
    resetState()
    fetchPapers()
  }
})
</script>

<style scoped>
.selected-paper-info {
  padding: 12px 16px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 8px;
  font-size: 14px;
}
.paper-meta {
  color: #888;
  font-size: 13px;
}

/* 点击行可选择 */
:deep(.ant-table-row) {
  cursor: pointer;
}

/* 试卷预览 */
.preview-meta {
  display: flex; align-items: center; gap: 16px; font-size: 13px; color: #666;
}
.preview-questions {
  max-height: 500px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px;
}
.preview-q-item {
  padding: 10px 12px; border: 1px solid #f0f0f0; border-radius: 6px; background: #fafafa;
}
.preview-q-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 6px;
}
.preview-q-index { font-weight: 600; color: #333; }
.preview-q-score { font-size: 12px; color: #1677ff; margin-left: auto; }
.preview-q-content { font-size: 14px; color: #333; line-height: 1.6; }
</style>
