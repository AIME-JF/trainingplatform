<template>
  <div class="result-page">
    <!-- 成绩卡 -->
    <div class="score-card" :class="passed ? 'passed' : 'failed'">
      <div class="score-main">
        <div class="score-icon">{{ passed ? '🎉' : '📚' }}</div>
        <div class="score-value">{{ score }}</div>
        <div class="score-label">得分 / 100</div>
      </div>
      <div class="score-detail">
        <div class="sd-item">
          <div class="sd-val">{{ passed ? '通过' : '未通过' }}</div>
          <div class="sd-key">考试结果</div>
        </div>
        <div class="sd-divider"></div>
        <div class="sd-item">
          <div class="sd-val">{{ correctCount }}</div>
          <div class="sd-key">答对题数</div>
        </div>
        <div class="sd-divider"></div>
        <div class="sd-item">
          <div class="sd-val">{{ totalQuestions - correctCount }}</div>
          <div class="sd-key">答错题数</div>
        </div>
        <div class="sd-divider"></div>
        <div class="sd-item">
          <div class="sd-val">42:18</div>
          <div class="sd-key">用时</div>
        </div>
      </div>
    </div>

    <a-row :gutter="20" style="margin-top:20px">
      <!-- 维度雷达图 -->
      <a-col :span="10">
        <a-card title="能力维度分析" :bordered="false">
          <v-chart class="radar-chart" :option="radarOption" autoresize />
          <div class="dimension-legend">
            <div v-for="dim in dimensions" :key="dim.key" class="dim-item">
              <div class="dim-bar-wrap">
                <span class="dim-label">{{ dim.label }}</span>
                <a-progress :percent="dim.score" :stroke-color="dim.score >= 80 ? '#52c41a' : dim.score >= 60 ? '#faad14' : '#ff4d4f'" size="small" />
              </div>
            </div>
          </div>
        </a-card>
      </a-col>

      <!-- 错题回顾 + 推荐 -->
      <a-col :span="14">
        <a-card :bordered="false">
          <a-tabs v-model:activeKey="resultTab">
            <a-tab-pane key="wrong" tab="错题回顾">
              <div class="wrong-list">
                <div v-for="(q, i) in wrongQuestions" :key="i" class="wrong-item">
                  <div class="wrong-q-header">
                    <a-tag :color="typeColors[q.type]" size="small">{{ typeLabels[q.type] }}</a-tag>
                    <span class="wrong-q-num">第 {{ q.num }} 题</span>
                    <a-tag color="red" size="small">✗ 答错</a-tag>
                  </div>
                  <div class="wrong-q-stem">{{ q.stem }}</div>
                  <div class="wrong-answers">
                    <div class="my-ans">我的答案：<span class="ans-wrong">{{ q.myAnswer }}</span></div>
                    <div class="correct-ans">正确答案：<span class="ans-correct">{{ q.answer }}</span></div>
                  </div>
                  <div class="wrong-explain">{{ q.explanation }}</div>
                </div>
              </div>
            </a-tab-pane>
            <a-tab-pane key="recommend" tab="推荐学习">
              <div class="recommend-section">
                <p class="rec-tip">📌 根据您的薄弱维度，AI 为您推荐以下学习资源：</p>
                <div class="rec-list">
                  <div v-for="r in weakResources" :key="r.id" class="rec-item">
                    <div class="rec-icon">{{ r.type === 'course' ? '📺' : '📝' }}</div>
                    <div class="rec-info">
                      <div class="rec-title">{{ r.title }}</div>
                      <div class="rec-meta">{{ r.meta }}</div>
                    </div>
                    <a-button size="small" type="link">去学习 →</a-button>
                  </div>
                </div>
              </div>
            </a-tab-pane>
          </a-tabs>
        </a-card>

        <div class="result-actions">
          <a-button @click="$router.push('/courses')">返回课程</a-button>
          <a-button type="primary" @click="$router.push('/exam/1')">重新考试</a-button>
        </div>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { MOCK_EXAM_RECORDS, WEAK_POINT_RESOURCES } from '@/mock/exam-records'
import { MOCK_QUESTIONS } from '@/mock/exams'

use([CanvasRenderer, RadarChart, TooltipComponent, LegendComponent])

const score = 78
const passed = score >= 60
const totalQuestions = 8
const correctCount = 6

const resultTab = ref('wrong')
const typeColors = { single: 'blue', multi: 'purple', judge: 'orange' }
const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }

const dims = MOCK_EXAM_RECORDS[0].dimensionScores
const dimensions = [
  { key: 'law', label: '法律知识', score: dims.law },
  { key: 'enforce', label: '执法规范', score: dims.enforce },
  { key: 'evidence', label: '证据意识', score: dims.evidence },
  { key: 'physical', label: '体能标准', score: dims.physical },
  { key: 'ethic', label: '警察素养', score: dims.ethic },
]

const radarOption = computed(() => ({
  radar: {
    indicator: dimensions.map(d => ({ name: d.label, max: 100 })),
    splitNumber: 4,
    axisName: { color: '#555', fontSize: 12 },
    splitArea: { areaStyle: { color: ['#f8f9ff', '#eef2ff', '#e3eaff', '#d8e3ff'] } },
  },
  series: [{
    type: 'radar',
    data: [{
      value: dimensions.map(d => d.score),
      name: '本次成绩',
      areaStyle: { color: 'rgba(0,48,135,0.15)' },
      lineStyle: { color: '#003087', width: 2 },
      itemStyle: { color: '#003087' },
    }]
  }]
}))

const wrongQuestions = [
  { num: 3, type: 'single', stem: '下列哪种情形不属于逮捕条件的"社会危险性"？', myAnswer: 'B', answer: 'D', explanation: '逮捕的"社会危险性"包括可能逃跑、毁灭证据等，一般违法行为不符合此条件。' },
  { num: 7, type: 'judge', stem: '对醉酒的人在醉酒状态中实施的违法行为，公安机关可以对其采取保护性措施约束至酒醒。', myAnswer: 'F', answer: 'T', explanation: '《治安管理处罚法》第15条明确规定了该情形。' },
]

const weakResources = Object.entries(WEAK_POINT_RESOURCES).flatMap(([key, val]) =>
  val.courses.map((c, i) => ({
    id: `${key}-${i}`,
    type: 'course',
    title: c.title,
    meta: val.tip,
  }))
)
</script>

<style scoped>
.result-page { padding: 0; }
.score-card { background: linear-gradient(135deg, #003087, #0050c8); border-radius: 12px; padding: 32px; display: flex; align-items: center; gap: 48px; }
.score-card.failed { background: linear-gradient(135deg, #8b0000, #c41230); }
.score-main { text-align: center; }
.score-icon { font-size: 48px; margin-bottom: 8px; }
.score-value { font-size: 72px; font-weight: 900; color: #fff; line-height: 1; }
.score-label { color: rgba(255,255,255,0.7); font-size: 14px; margin-top: 4px; }
.score-detail { display: flex; align-items: center; gap: 24px; flex: 1; justify-content: center; }
.sd-item { text-align: center; }
.sd-val { font-size: 24px; font-weight: 700; color: #fff; }
.sd-key { font-size: 12px; color: rgba(255,255,255,0.6); margin-top: 4px; }
.sd-divider { width: 1px; height: 40px; background: rgba(255,255,255,0.2); }
.radar-chart { height: 220px; }
.dimension-legend { margin-top: 12px; display: flex; flex-direction: column; gap: 8px; }
.dim-item { }
.dim-bar-wrap { display: flex; align-items: center; gap: 8px; }
.dim-label { font-size: 12px; color: #555; white-space: nowrap; min-width: 56px; }
.wrong-list { display: flex; flex-direction: column; gap: 16px; max-height: 400px; overflow-y: auto; }
.wrong-item { border: 1px solid #ffd6d6; border-radius: 8px; padding: 14px; background: #fff8f8; }
.wrong-q-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.wrong-q-num { font-size: 12px; color: #888; }
.wrong-q-stem { font-size: 14px; color: #333; margin-bottom: 10px; line-height: 1.5; }
.wrong-answers { display: flex; gap: 16px; margin-bottom: 8px; font-size: 13px; }
.my-ans, .correct-ans { }
.ans-wrong { color: #ff4d4f; font-weight: 700; }
.ans-correct { color: #52c41a; font-weight: 700; }
.wrong-explain { font-size: 13px; color: #666; background: #fff; padding: 8px 10px; border-radius: 4px; border-left: 3px solid var(--police-primary); }
.recommend-section { }
.rec-tip { color: #666; font-size: 13px; margin-bottom: 16px; }
.rec-list { display: flex; flex-direction: column; gap: 12px; }
.rec-item { display: flex; align-items: center; gap: 12px; padding: 10px; border: 1px solid #f0f0f0; border-radius: 6px; }
.rec-icon { font-size: 24px; }
.rec-info { flex: 1; }
.rec-title { font-size: 14px; font-weight: 500; color: #333; }
.rec-meta { font-size: 12px; color: #888; }
.result-actions { margin-top: 16px; display: flex; justify-content: flex-end; gap: 12px; }
</style>
