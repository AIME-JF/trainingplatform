<template>
  <div class="ai-task-timeline">
    <a-steps :current="currentStep" size="small" :status="status === 'failed' ? 'error' : 'process'">
      <a-step v-for="step in stepTitles" :key="step" :title="step" />
    </a-steps>
    <div class="timeline-status">
      <a-tag :color="currentStatusColor">{{ currentStatusLabel }}</a-tag>
      <span v-if="confirmedAt" class="timeline-time">完成时间：{{ formatTime(confirmedAt) }}</span>
      <span v-else-if="completedAt" class="timeline-time">处理完成：{{ formatTime(completedAt) }}</span>
      <span v-else-if="createdAt" class="timeline-time">创建时间：{{ formatTime(createdAt) }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, default: 'pending' },
  stage: { type: String, default: '' },
  mode: { type: String, default: 'default' },
  activeStep: { type: Number, default: -1 },
  createdAt: { type: String, default: '' },
  completedAt: { type: String, default: '' },
  confirmedAt: { type: String, default: '' },
})

const statusLabels = {
  pending: '待处理',
  processing: '处理中',
  completed: '已完成',
  confirmed: '已确认',
  failed: '处理失败',
}

const statusColors = {
  pending: 'default',
  processing: 'processing',
  completed: 'blue',
  confirmed: 'green',
  failed: 'red',
}

const currentStatusLabel = computed(() => {
  if (props.mode === 'schedule') {
    if (props.status === 'failed') return '处理失败'
    if (props.status === 'confirmed') return '已确认'
    if (props.stage === 'rule_parsing') return props.status === 'processing' ? '解析规则中' : '待解析规则'
    if (props.stage === 'rule_confirmation') return '待确认规则'
    if (props.stage === 'schedule_generation') return props.status === 'processing' ? '生成课表中' : '待生成课表'
    if (props.stage === 'schedule_confirmation') return '待确认课表'
  }
  if (props.mode === 'resource-generation') {
    if (props.status === 'failed') return '生成失败'
    if (props.status === 'confirmed') return '已保存草稿'
    if (props.status === 'completed') return '生成完成'
    if (props.status === 'processing') return '智能生成中'
    if (props.status === 'pending') return '排队中'
  }
  return statusLabels[props.status] || props.status
})

const currentStatusColor = computed(() => {
  if (props.mode === 'schedule') {
    if (props.status === 'failed') return 'red'
    if (props.status === 'confirmed') return 'green'
    if (props.stage === 'rule_confirmation') return 'gold'
    if (props.stage === 'schedule_confirmation') return 'blue'
    if (props.status === 'processing') return 'processing'
  }
  if (props.mode === 'resource-generation') {
    if (props.status === 'failed') return 'red'
    if (props.status === 'confirmed') return 'green'
    if (props.status === 'completed') return 'blue'
    if (props.status === 'processing') return 'processing'
  }
  return statusColors[props.status] || 'default'
})

const stepTitles = computed(() => {
  if (props.mode === 'schedule') {
    return ['创建任务', '解析规则', '确认规则', '生成课表', '确认应用']
  }
  if (props.mode === 'resource-generation') {
    return ['创建任务', '智能生成', '查看结果', '预览', '确认完成']
  }
  return ['创建任务', '后端处理', '查看结果', '确认完成']
})

const currentStep = computed(() => {
  if (props.mode === 'schedule') {
    if (props.status === 'confirmed') return 4
    if (props.stage === 'schedule_confirmation' && props.status === 'completed') return 3
    if (props.stage === 'schedule_generation') return 3
    if (props.stage === 'rule_confirmation' && props.status === 'completed') return 2
    if (props.stage === 'rule_parsing') return 1
    if (props.status === 'failed') {
      return props.stage === 'schedule_generation' ? 3 : 1
    }
    return 0
  }
  if (props.mode === 'resource-generation') {
    if (props.activeStep >= 0) return props.activeStep
    if (props.status === 'confirmed') return 4
    if (props.status === 'completed') return 2
    if (props.status === 'processing') return 1
    if (props.status === 'failed') return 1
    return 0
  }
  if (props.status === 'failed') return 1
  if (props.status === 'confirmed') return 3
  if (props.status === 'completed') return 2
  if (props.status === 'processing') return 1
  return 0
})

function formatTime(value) {
  if (!value) return ''
  return String(value).replace('T', ' ').slice(0, 16)
}
</script>

<style scoped>
.ai-task-timeline {
  padding: 14px 16px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(0, 48, 135, 0.05), rgba(200, 168, 75, 0.08));
  border: 1px solid rgba(0, 48, 135, 0.08);
}

.timeline-status {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  color: #8c8c8c;
  font-size: 12px;
}

.timeline-time {
  color: #595959;
}
</style>
