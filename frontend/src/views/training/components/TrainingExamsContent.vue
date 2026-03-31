<template>
  <div>
    <div class="section-header" style="margin-bottom:16px">
      <h4>考试安排</h4>
      <a-space v-if="!isStudent">
        <permissions-tooltip
          :allowed="canQuickCreateExam"
          :tips="quickCreateExamTooltip"
          v-slot="{ disabled }"
        >
          <a-button size="small" type="primary" :disabled="disabled" @click="$emit('quick-create')">
            快捷添加考试
          </a-button>
        </permissions-tooltip>
        <a-button size="small" @click="$emit('go-manage')">
          前往考试管理
        </a-button>
      </a-space>
    </div>

    <a-empty v-if="!trainingExamSessions.length" description="当前培训班暂无考试安排" />
    <div v-else class="exam-plan-list">
      <div class="exam-plan-card" v-for="exam in trainingExamSessions" :key="exam.id">
        <div class="exam-plan-main">
          <div class="exam-plan-name">{{ exam.title }}</div>
          <div class="exam-plan-meta">
            <span>用途：{{ examPurposeLabelMap[exam.purpose] || exam.purpose }}</span>
            <span>题目数：{{ exam.questionCount || 0 }}</span>
            <span>及格分：{{ exam.passingScore || 60 }}</span>
            <span>开始：{{ formatDateTime(exam.startTime) }}</span>
            <span>结束：{{ formatDateTime(exam.endTime) }}</span>
          </div>
        </div>
        <a-space wrap>
          <a-tag :color="examStatusColorMap[exam.status] || 'default'">
            {{ examStatusLabelMap[exam.status] || exam.status }}
          </a-tag>
          <a-button size="small" type="link" @click="$emit('go-manage')">
            前往管理
          </a-button>
        </a-space>
      </div>
    </div>
  </div>
</template>

<script setup>
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

defineProps({
  isStudent: { type: Boolean, default: false },
  canQuickCreateExam: { type: Boolean, default: false },
  quickCreateExamTooltip: { type: String, default: '' },
  trainingExamSessions: { type: Array, default: () => [] },
  examPurposeLabelMap: { type: Object, default: () => ({}) },
  examStatusColorMap: { type: Object, default: () => ({}) },
  examStatusLabelMap: { type: Object, default: () => ({}) },
  formatDateTime: { type: Function, required: true },
})

defineEmits(['quick-create', 'go-manage'])
</script>

<style scoped>
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-header h4 { margin: 0; color: #333; }
.exam-plan-list { display: flex; flex-direction: column; gap: 12px; }
.exam-plan-card { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; padding: 16px; border: 1px solid #eef2f7; border-radius: 10px; background: #fafcff; }
.exam-plan-main { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.exam-plan-name { font-size: 15px; font-weight: 600; color: #111827; }
.exam-plan-meta { display: flex; flex-wrap: wrap; gap: 8px 16px; color: #6b7280; font-size: 13px; }
</style>
