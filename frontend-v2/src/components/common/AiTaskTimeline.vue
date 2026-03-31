<template>
  <div class="ai-task-timeline">
    <a-steps :current="currentStep" size="small" :status="status === 'failed' ? 'error' : 'process'">
      <a-step v-for="step in stepTitles" :key="step" :title="step" />
    </a-steps>
    <div class="timeline-status">
      <a-tag :color="currentStatusColor">{{ currentStatusLabel }}</a-tag>
      <span v-if="confirmedAt" class="timeline-time">完成时间：{{ formatDateTime(confirmedAt) }}</span>
      <span v-else-if="completedAt" class="timeline-time">处理完成：{{ formatDateTime(completedAt) }}</span>
      <span v-else-if="createdAt" class="timeline-time">创建时间：{{ formatDateTime(createdAt) }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatDateTime } from '@/utils/learning-resource'

const props = withDefaults(defineProps<{
  status?: string
  stage?: string
  mode?: 'default' | 'schedule' | 'resource-generation'
  activeStep?: number
  createdAt?: string
  completedAt?: string
  confirmedAt?: string
}>(), {
  status: 'pending',
  stage: '',
  mode: 'default',
  activeStep: -1,
  createdAt: '',
  completedAt: '',
  confirmedAt: '',
})

const currentStatusLabel = computed(() => {
  if (props.mode === 'resource-generation') {
    if (props.status === 'failed') return '生成失败'
    if (props.status === 'confirmed') return '已保存草稿'
    if (props.status === 'completed') return '生成完成'
    if (props.status === 'processing') return '智能生成中'
    if (props.status === 'pending') return '排队中'
  }
  return props.status || '处理中'
})

const currentStatusColor = computed(() => {
  if (props.status === 'failed') return 'red'
  if (props.status === 'confirmed') return 'green'
  if (props.status === 'completed') return 'blue'
  if (props.status === 'processing') return 'processing'
  return 'default'
})

const stepTitles = computed(() => {
  if (props.mode === 'resource-generation') {
    return ['创建任务', '智能生成', '查看结果', '预览', '确认完成']
  }
  return ['创建任务', '处理', '完成']
})

const currentStep = computed(() => {
  if (props.mode === 'resource-generation') {
    if (props.activeStep >= 0) return props.activeStep
    if (props.status === 'confirmed') return 4
    if (props.status === 'completed') return 2
    if (props.status === 'processing' || props.status === 'failed') return 1
    return 0
  }
  if (props.status === 'confirmed') return 2
  if (props.status === 'completed') return 2
  if (props.status === 'processing' || props.status === 'failed') return 1
  return 0
})
</script>

<style scoped>
.ai-task-timeline {
  padding: 16px 18px;
  border-radius: var(--v2-radius);
  background: linear-gradient(135deg, rgba(75, 110, 245, 0.07), rgba(90, 200, 250, 0.08));
  border: 1px solid rgba(75, 110, 245, 0.08);
}

.timeline-status {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  color: var(--v2-text-secondary);
  font-size: 12px;
}

.timeline-time {
  color: var(--v2-text-secondary);
}
</style>
