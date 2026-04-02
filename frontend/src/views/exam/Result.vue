<template>
  <div class="result-page" v-if="result">
    <div class="score-card" :class="{ failed: result.result !== 'pass' }">
      <div class="score-main">
        <div class="score-value">{{ result.score }}</div>
        <div class="score-label">本次得分</div>
        <div class="score-sub">及格线 {{ result.passingScore || 60 }} 分</div>
      </div>
      <div class="score-stats">
        <div class="stat-item">
          <div class="stat-value">{{ result.result === 'pass' ? '通过' : '未通过' }}</div>
          <div class="stat-label">考试结果</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ result.correctCount }}</div>
          <div class="stat-label">答对题数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ result.wrongCount }}</div>
          <div class="stat-label">答错题数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ result.duration }} 分钟</div>
          <div class="stat-label">用时</div>
        </div>
      </div>
    </div>

    <a-card :bordered="false" style="margin-top:20px">
      <div class="summary-grid">
        <div class="summary-item">
          <div class="summary-label">考试名称</div>
          <div class="summary-value">{{ result.examTitle || '未命名考试' }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">考试类型</div>
          <div class="summary-value">{{ result.kind === 'admission' ? '准入考试' : '培训班考试' }}</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">作答次数</div>
          <div class="summary-value">第 {{ result.attemptNo || 1 }} 次</div>
        </div>
        <div class="summary-item">
          <div class="summary-label">交卷时间</div>
          <div class="summary-value">{{ formatDate(result.endTime) }}</div>
        </div>
      </div>
    </a-card>

    <a-row :gutter="20" style="margin-top:20px">
      <a-col :span="10">
        <a-card title="能力维度" :bordered="false">
          <div v-for="item in dimensionList" :key="item.key" class="dimension-item">
            <span>{{ item.label }}</span>
            <a-progress :percent="item.score" size="small" />
          </div>
        </a-card>
      </a-col>

      <a-col :span="14">
        <a-card title="错题回顾" :bordered="false">
          <a-empty v-if="!result.wrongQuestionDetails?.length" description="本次考试没有错题" />
          <div v-else class="wrong-list">
            <div v-for="(item, index) in result.wrongQuestionDetails" :key="`${item.questionId}-${index}`" class="wrong-item">
              <div class="wrong-title">{{ index + 1 }}. {{ item.content }}</div>
              <div class="wrong-meta">我的答案：{{ displayAnswer(item.myAnswer) }}</div>
              <div class="wrong-meta">正确答案：{{ displayAnswer(item.answer) }}</div>
              <div class="wrong-explanation">{{ item.explanation || '暂无解析' }}</div>
            </div>
          </div>
        </a-card>

        <div class="result-actions">
          <a-button @click="$router.push('/exam/list')">返回考试列表</a-button>
        </div>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { getAdmissionExamResult, getExamResult } from '@/api/exam'

const route = useRoute()
const result = ref(null)
const resolvedKind = ref(route.query.kind === 'admission' ? 'admission' : 'training')

const dimensionList = computed(() => {
  const dimensions = result.value?.dimensionScores || {}
  return [
    { key: 'law', label: '法律知识', score: dimensions.law || 0 },
    { key: 'enforce', label: '执法程序', score: dimensions.enforce || 0 },
    { key: 'evidence', label: '证据规则', score: dimensions.evidence || 0 },
    { key: 'physical', label: '体能技能', score: dimensions.physical || 0 },
    { key: 'ethic', label: '职业道德', score: dimensions.ethic || 0 },
  ]
})

function displayAnswer(value) {
  if (Array.isArray(value)) return value.join('、')
  return value ?? '未作答'
}

function formatDate(value) {
  return value ? String(value).replace('T', ' ').slice(0, 16) : '未记录'
}

async function loadResult() {
  try {
    if (resolvedKind.value === 'admission') {
      try {
        result.value = await getAdmissionExamResult(route.params.id)
      } catch {
        result.value = await getExamResult(route.params.id)
        resolvedKind.value = 'training'
      }
      return
    }
    try {
      result.value = await getExamResult(route.params.id)
    } catch {
      result.value = await getAdmissionExamResult(route.params.id)
      resolvedKind.value = 'admission'
    }
  } catch (error) {
    message.error(error.message || '加载考试结果失败')
  }
}

onMounted(loadResult)
</script>

<style scoped>
.result-page { padding: 0; }
.score-card { background: linear-gradient(135deg, #003087, #0050c8); border-radius: 12px; padding: 28px; color: #fff; display: flex; justify-content: space-between; gap: 24px; }
.score-card.failed { background: linear-gradient(135deg, #8b1e1e, #d4380d); }
.score-main { min-width: 160px; text-align: center; }
.score-value { font-size: 64px; font-weight: 800; line-height: 1; }
.score-label { margin-top: 10px; color: rgba(255,255,255,0.75); }
.score-sub { margin-top: 6px; color: rgba(255,255,255,0.75); font-size: 12px; }
.score-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; flex: 1; }
.stat-item { background: rgba(255,255,255,0.12); border-radius: 10px; padding: 16px; text-align: center; }
.stat-value { font-size: 22px; font-weight: 700; }
.stat-label { font-size: 12px; color: rgba(255,255,255,0.75); margin-top: 4px; }
.summary-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.summary-item { background: #f7f9fc; border-radius: 10px; padding: 14px 16px; }
.summary-label { font-size: 12px; color: #8c8c8c; margin-bottom: 6px; }
.summary-value { color: #1f1f1f; font-weight: 600; }
.dimension-item { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.dimension-item span { width: 72px; font-size: 12px; color: #555; }
.wrong-list { display: flex; flex-direction: column; gap: 12px; }
.wrong-item { border: 1px solid #ffd6d6; background: #fff8f8; border-radius: 8px; padding: 14px; }
.wrong-title { font-weight: 600; color: #1f1f1f; margin-bottom: 8px; }
.wrong-meta { font-size: 13px; color: #666; margin-bottom: 4px; }
.wrong-explanation { margin-top: 8px; font-size: 13px; color: #555; }
.result-actions { display: flex; justify-content: flex-end; margin-top: 16px; }

@media (max-width: 768px) {
  .score-card { flex-direction: column; }
  .score-stats { grid-template-columns: 1fr 1fr; }
  .summary-grid { grid-template-columns: 1fr 1fr; }
}
</style>
