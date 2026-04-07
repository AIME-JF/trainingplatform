<template>
  <div class="review-flow-chart">
    <div class="flow-node flow-node--start">
      <div class="flow-node__badge">开始</div>
      <div class="flow-node__label">提交审核</div>
    </div>
    <div class="flow-arrow" />
    <template v-for="(stage, idx) in sortedStages" :key="idx">
      <div class="flow-node flow-node--stage">
        <div class="flow-node__badge">第 {{ stage.stageOrder }} 级</div>
        <div class="flow-node__label">{{ formatStageLabel(stage) }}</div>
        <div class="flow-node__sub">至少 {{ stage.minApprovals || 1 }} 人通过</div>
      </div>
      <div class="flow-arrow" />
    </template>
    <div class="flow-node flow-node--end">
      <div class="flow-node__badge">结束</div>
      <div class="flow-node__label">审核完成</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  stages: { type: Array, default: () => [] },
  reviewerTypeLabels: { type: Object, default: () => ({ user: '用户', role: '角色', department: '部门' }) },
  getReviewerLabel: { type: Function, default: null },
})

const sortedStages = computed(() =>
  (props.stages || [])
    .slice()
    .sort((a, b) => Number(a.stageOrder || 0) - Number(b.stageOrder || 0))
)

function formatStageLabel(stage) {
  const typeLabel = props.reviewerTypeLabels[stage.reviewerType] || stage.reviewerType || '角色'
  if (props.getReviewerLabel) {
    return `${typeLabel}：${props.getReviewerLabel(stage)}`
  }
  return `${typeLabel}审核`
}
</script>

<style scoped>
.review-flow-chart {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 16px 8px;
  overflow-x: auto;
}

.flow-node {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 100px;
  padding: 10px 14px;
  border-radius: 8px;
  border: 2px solid #d9d9d9;
  background: #fff;
  text-align: center;
}

.flow-node--start {
  border-color: #52c41a;
  background: #f6ffed;
}

.flow-node--end {
  border-color: #1890ff;
  background: #e6f7ff;
}

.flow-node--stage {
  border-color: #faad14;
  background: #fffbe6;
}

.flow-node__badge {
  font-size: 12px;
  font-weight: 600;
  color: #595959;
  margin-bottom: 4px;
}

.flow-node--start .flow-node__badge { color: #52c41a; }
.flow-node--end .flow-node__badge { color: #1890ff; }
.flow-node--stage .flow-node__badge { color: #faad14; }

.flow-node__label {
  font-size: 13px;
  font-weight: 500;
  color: #1f1f1f;
  white-space: nowrap;
}

.flow-node__sub {
  font-size: 11px;
  color: #8c8c8c;
  margin-top: 2px;
}

.flow-arrow {
  flex-shrink: 0;
  width: 36px;
  height: 2px;
  background: #d9d9d9;
  position: relative;
}

.flow-arrow::after {
  content: '';
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 0;
  height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-left: 7px solid #d9d9d9;
}
</style>
