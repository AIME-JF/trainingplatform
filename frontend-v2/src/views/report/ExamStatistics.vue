<template>
  <section class="page-content exam-stat-page">
    <div class="exam-stat-shell">
      <header class="exam-stat-hero">
        <div class="hero-grid">
          <div class="hero-copy">
            <div class="hero-eyebrow">数据中心</div>
            <h1>考试统计</h1>
            <p>面向考试运营场景的统计驾驶舱，聚焦考试规模、分数结构、趋势变化与单位表现。</p>

            <div class="hero-summary">
              <article v-for="item in summaryCards" :key="item.label" class="hero-summary-card">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </article>
            </div>
          </div>

          <aside class="hero-side">
            <div class="hero-actions">
              <div class="hero-filter">
                <span class="hero-filter-label">统计范围</span>
                <a-select v-model:value="timeRange" class="hero-range-select" @change="loadData">
                  <a-select-option v-for="option in rangeOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </a-select-option>
                </a-select>
              </div>
              <a-button class="hero-refresh-btn" type="primary" :loading="loading" @click="loadData">
                刷新数据
              </a-button>
            </div>

            <div class="hero-brief">
              <span class="hero-brief-label">当前观察</span>
              <strong class="hero-brief-value">{{ selectedRangeLabel }}</strong>
              <p>{{ heroBrief }}</p>

              <div class="hero-brief-metrics">
                <div>
                  <span>成绩记录</span>
                  <strong>{{ scoreDistributionTotal }} 条</strong>
                </div>
                <div>
                  <span>达标人数</span>
                  <strong>{{ passCount }} 人</strong>
                </div>
              </div>
            </div>
          </aside>
        </div>

        <div class="kpi-grid">
          <article
            v-for="(card, index) in kpiCards"
            :key="card.label"
            class="kpi-card"
            :style="{ '--accent-color': card.color }"
          >
            <div class="kpi-topline">
              <span class="kpi-index">0{{ index + 1 }}</span>
              <span class="kpi-accent"></span>
            </div>
            <span class="kpi-label">{{ card.label }}</span>
            <strong class="kpi-value">
              {{ card.value }}
              <small v-if="card.suffix">{{ card.suffix }}</small>
            </strong>
            <p class="kpi-caption">{{ card.caption }}</p>
          </article>
        </div>
      </header>

      <a-spin :spinning="loading">
        <!-- 主内容区 - 统一大容器 -->
        <div class="main-content">
          <div class="dashboard-grid">

            <section class="surface-panel trend-panel">
              <header class="panel-head">
                <div>
                  <span class="panel-kicker">主趋势</span>
                  <h2>月度趋势</h2>
                  <p>{{ trendDescription }}</p>
                </div>
                <div v-if="trendHighlight" class="panel-badge">
                  <span>月度高点</span>
                  <strong>{{ trendHighlight.month }}</strong>
                </div>
              </header>
              <div v-if="monthlyTrend.length" class="trend-board">
                <article v-if="trendHighlight" class="trend-highlight-card">
                  <span>趋势焦点</span>
                  <strong>{{ trendHighlight.month }}</strong>
                  <p>平均分 {{ formatNumber(trendHighlight.avgScore, 1) }} 分，及格率 {{ formatPercent(trendHighlight.passRate) }}</p>
                </article>
                <div class="trend-list">
                  <article v-for="item in monthlyTrend" :key="item.month" class="trend-row">
                    <div class="trend-row-head">
                      <span class="trend-month">{{ item.month }}</span>
                      <strong class="trend-score">{{ formatNumber(item.avgScore, 1) }} 分</strong>
                    </div>
                    <div class="trend-track">
                      <span class="trend-fill trend-fill-score" :style="{ width: `${normalizePercent(item.avgScore)}%` }"></span>
                    </div>
                    <div class="trend-track trend-track-secondary">
                      <span class="trend-fill trend-fill-pass" :style="{ width: `${normalizePercent(item.passRate)}%` }"></span>
                    </div>
                    <div class="trend-meta">
                      <span>均分走势</span>
                      <span>及格率 {{ formatPercent(item.passRate) }}</span>
                    </div>
                  </article>
                </div>
              </div>
              <div v-else class="empty-block">
                <strong>暂无月度趋势数据</strong>
                <p>当前时间范围内还没有形成趋势样本，完成考试后这里会自动汇总每个月的平均分和及格率变化。</p>
              </div>
            </section>

            <section class="surface-panel distribution-panel">
              <header class="panel-head">
                <div>
                  <span class="panel-kicker">结构分布</span>
                  <h2>分数段分布</h2>
                  <p>{{ distributionDescription }}</p>
                </div>
                <div class="panel-badge light">
                  <span>主力分段</span>
                  <strong>{{ dominantScoreBand?.label || '暂无' }}</strong>
                </div>
              </header>
              <div class="score-dist">
                <article
                  v-for="item in scoreDistributionCards"
                  :key="item.label"
                  class="score-dist-item"
                  :style="{ '--band-color': item.color }"
                >
                  <div class="score-dist-head">
                    <div>
                      <span class="score-dist-label">{{ item.label }}</span>
                      <small>{{ item.percent }}%</small>
                    </div>
                    <strong>{{ item.value }}<em>人</em></strong>
                  </div>
                  <div class="score-dist-track">
                    <span class="score-dist-fill" :style="{ width: `${item.percent}%` }"></span>
                  </div>
                </article>
              </div>
            </section>

            <section class="surface-panel ranking-panel">
              <header class="panel-head">
                <div>
                  <span class="panel-kicker">单位表现</span>
                  <h2>各单位考试排名</h2>
                  <p>{{ rankingDescription }}</p>
                </div>
                <div class="panel-badge light">
                  <span>领先单位</span>
                  <strong>{{ topRankingCity || '暂无' }}</strong>
                </div>
              </header>
              <div v-if="cityRanking.length" class="ranking-list">
                <article v-for="(item, index) in cityRanking" :key="`${item.city}-${index}`" class="ranking-row">
                  <span class="rank-badge" :class="`rank-${toRank(index)}`">{{ toRank(index) }}</span>
                  <div class="ranking-main">
                    <div class="ranking-headline">
                      <span class="ranking-name">{{ item.city }}</span>
                      <strong class="ranking-value">{{ formatNumber(item.avgScore, 1) }} 分</strong>
                    </div>
                    <div class="ranking-track">
                      <span class="ranking-fill" :style="{ width: `${normalizePercent(item.avgScore)}%` }"></span>
                    </div>
                  </div>
                </article>
              </div>
              <div v-else class="empty-block compact">
                <strong>暂无单位排名数据</strong>
                <p>当不同单位产生考试成绩后，这里会展示平均分对比与排名变化。</p>
              </div>
            </section>

            <section class="surface-panel dimension-panel">
              <header class="panel-head">
                <div>
                  <span class="panel-kicker">能力画像</span>
                  <h2>维度平均得分</h2>
                  <p>{{ dimensionDescription }}</p>
                </div>
                <div class="panel-badge light">
                  <span>优势维度</span>
                  <strong>{{ strongestDimension?.label || '暂无' }}</strong>
                </div>
              </header>
              <div class="dimension-list">
                <article
                  v-for="item in dimensionScores"
                  :key="item.label"
                  class="dimension-row"
                  :style="{ '--dimension-color': item.color }"
                >
                  <div class="dimension-meta">
                    <span>{{ item.label }}</span>
                    <strong>{{ item.value }} 分</strong>
                  </div>
                  <div class="dimension-track">
                    <span class="dimension-fill" :style="{ width: `${normalizePercent(item.value)}%` }"></span>
                  </div>
                </article>
              </div>
            </section>

          </div>
        </div>
      </a-spin>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { getExamStatistics } from '@/api/report'

type TimeRange = '7d' | '30d' | 'month' | 'year'

const rangeOptions: Array<{ label: string; value: TimeRange }> = [
  { label: '近7天', value: '7d' },
  { label: '近30天', value: '30d' },
  { label: '本月', value: 'month' },
  { label: '本年', value: 'year' },
]

const loading = ref(false)
const timeRange = ref<TimeRange>('30d')
const stats = ref<Record<string, any>>({})

const kpiCards = computed(() => [
  {
    label: '总考试数',
    value: stats.value.totalExams || 0,
    suffix: '场',
    color: '#3f63dd',
    caption: '统计窗口内累计排考场次',
  },
  {
    label: '参考人次',
    value: stats.value.totalSubmitted || 0,
    suffix: '人',
    color: '#1f8f72',
    caption: '已提交答卷的人次规模',
  },
  {
    label: '平均分',
    value: formatNumber(stats.value.avgScore || 0, 1),
    suffix: '分',
    color: '#da8b20',
    caption: '整体考试成绩中位表现',
  },
  {
    label: '及格率',
    value: formatPercent(stats.value.passRate || 0),
    suffix: '',
    color: '#c6475e',
    caption: '达到及格线的人次占比',
  },
])

const monthlyTrend = computed(() => stats.value.monthlyTrend || [])
const cityRanking = computed(() => stats.value.cityRanking || [])

const scoreDistributionCards = computed(() => {
  const dist = stats.value.scoreDistribution || {}
  const excellent = Number(dist.excellent || 0)
  const good = Number(dist.good || 0)
  const pass = Number(dist.pass || 0)
  const fail = Number(dist.fail || 0)
  const total = excellent + good + pass + fail
  const buildPercent = (value: number) => (total ? Math.round((value / total) * 100) : 0)

  return [
    { label: '优秀(90+)', value: excellent, percent: buildPercent(excellent), color: '#3154c8' },
    { label: '良好(80-89)', value: good, percent: buildPercent(good), color: '#278065' },
    { label: '及格(60-79)', value: pass, percent: buildPercent(pass), color: '#d38b2f' },
    { label: '不及格(<60)', value: fail, percent: buildPercent(fail), color: '#cf4a5b' },
  ]
})

const scoreDistributionTotal = computed(() => scoreDistributionCards.value.reduce((sum, item) => sum + item.value, 0))
const passCount = computed(() => {
  const [excellent, good, pass] = scoreDistributionCards.value
  return excellent.value + good.value + pass.value
})

const dimensionScores = computed(() => {
  const dim = stats.value.dimensionAvgScores || {}
  return [
    { label: '法律法规', value: Math.round(Number(dim.law || 0)), color: '#3154c8' },
    { label: '执法能力', value: Math.round(Number(dim.enforce || 0)), color: '#278065' },
    { label: '证据运用', value: Math.round(Number(dim.evidence || 0)), color: '#7c5cff' },
    { label: '体能测试', value: Math.round(Number(dim.physical || 0)), color: '#ff9752' },
    { label: '职业道德', value: Math.round(Number(dim.ethic || 0)), color: '#d1548f' },
  ]
})

const selectedRangeLabel = computed(() => rangeOptions.find((option) => option.value === timeRange.value)?.label || '近30天')

const trendHighlight = computed(() => {
  if (!monthlyTrend.value.length) {
    return null
  }
  return [...monthlyTrend.value].sort((a, b) => Number(b.avgScore || 0) - Number(a.avgScore || 0))[0]
})

const dominantScoreBand = computed(() => {
  return [...scoreDistributionCards.value].sort((a, b) => b.value - a.value)[0]
})

const strongestDimension = computed(() => {
  return [...dimensionScores.value].sort((a, b) => b.value - a.value)[0]
})

const topRankingCity = computed(() => cityRanking.value[0]?.city || '')

const summaryCards = computed(() => [
  { label: '统计窗口', value: selectedRangeLabel.value },
  { label: '主力分段', value: dominantScoreBand.value?.label || '暂无' },
  { label: '领先单位', value: topRankingCity.value || '暂无' },
  { label: '优势维度', value: strongestDimension.value?.label || '暂无' },
])

const heroBrief = computed(() => {
  if (!scoreDistributionTotal.value) {
    return '当前窗口内暂未形成有效成绩样本，建议切换统计范围或等待考试完成后再查看。'
  }

  return `已沉淀 ${scoreDistributionTotal.value} 条成绩记录，整体及格率 ${formatPercent(stats.value.passRate || 0)}，可快速观察结构变化与单位差异。`
})

const trendDescription = computed(() => {
  if (!trendHighlight.value) {
    return '对比不同月份的平均分与及格率变化。'
  }

  return `当前高点出现在 ${trendHighlight.value.month}，适合继续对比不同月份的成绩起伏。`
})

const distributionDescription = computed(() => {
  if (!scoreDistributionTotal.value) {
    return '当前暂无成绩样本，分数段会在有成绩后自动聚合。'
  }

  return `共覆盖 ${scoreDistributionTotal.value} 条成绩记录，主力人群集中在 ${dominantScoreBand.value?.label || '暂无'}。`
})

const rankingDescription = computed(() => {
  if (!cityRanking.value.length) {
    return '用于观察不同单位的平均成绩表现。'
  }

  return `${cityRanking.value.length} 个单位进入统计，当前领先单位为 ${topRankingCity.value}。`
})

const dimensionDescription = computed(() => {
  if (!strongestDimension.value || strongestDimension.value.value === 0) {
    return '展示法律法规、执法能力等关键维度的平均得分。'
  }

  return `当前表现最突出的维度是 ${strongestDimension.value.label}，适合继续对照薄弱项做训练安排。`
})

async function loadData() {
  loading.value = true
  try {
    stats.value = (await getExamStatistics({ time_range: timeRange.value })) || {}
  } catch (error: any) {
    message.error(error?.message || '加载考试统计失败')
  } finally {
    loading.value = false
  }
}

function formatNumber(value: number, digits = 0) {
  return Number(value || 0).toFixed(digits)
}

function formatPercent(value: number) {
  return `${Math.round(Number(value || 0))}%`
}

function normalizePercent(value: number) {
  return Math.max(0, Math.min(100, Math.round(Number(value || 0))))
}

function toRank(value: string | number) {
  return Number(value) + 1
}

onMounted(() => {
  void loadData()
})
</script>

<style scoped>
.exam-stat-page {
  position: relative;
}

.exam-stat-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.exam-stat-hero {
  position: relative;
  overflow: hidden;
  padding: 28px;
  border-radius: 32px;
  background:
    radial-gradient(circle at 12% 18%, rgba(136, 166, 255, 0.34), transparent 28%),
    radial-gradient(circle at 86% 22%, rgba(255, 255, 255, 0.16), transparent 26%),
    linear-gradient(135deg, #143072 0%, #2147a1 45%, #3159c6 100%);
  box-shadow: 0 22px 48px rgba(24, 49, 112, 0.22);
}

.exam-stat-hero::before,
.exam-stat-hero::after {
  content: '';
  position: absolute;
  border-radius: 999px;
  pointer-events: none;
}

.exam-stat-hero::before {
  top: -80px;
  right: -40px;
  width: 240px;
  height: 240px;
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.exam-stat-hero::after {
  bottom: -110px;
  left: 42%;
  width: 320px;
  height: 320px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.hero-grid,
.kpi-grid {
  position: relative;
  z-index: 1;
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.82fr);
  gap: 20px;
  align-items: start;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.hero-eyebrow {
  display: inline-flex;
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.82);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.hero-copy h1 {
  margin: 0;
  font-size: 38px;
  line-height: 1.04;
  color: #fff;
  letter-spacing: 0.01em;
}

.hero-copy p {
  max-width: 720px;
  margin: 0;
  color: rgba(240, 245, 255, 0.82);
  font-size: 15px;
  line-height: 1.8;
}

.hero-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.hero-summary-card {
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(10, 25, 66, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(12px);
}

.hero-summary-card span,
.hero-brief-label,
.hero-filter-label {
  display: block;
  color: rgba(230, 236, 252, 0.66);
  font-size: 12px;
  letter-spacing: 0.06em;
}

.hero-summary-card strong {
  display: block;
  margin-top: 10px;
  color: #fff;
  font-size: 16px;
  font-weight: 700;
}

.hero-side {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.hero-actions,
.hero-brief {
  padding: 16px 18px;
  border-radius: 22px;
  background: rgba(10, 25, 66, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(12px);
}

.hero-actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: end;
}

.hero-filter {
  min-width: 0;
}

.hero-actions :deep(.hero-range-select) {
  width: 100%;
}

.hero-actions :deep(.hero-range-select .ant-select-selector) {
  height: 44px !important;
  padding: 0 14px !important;
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
  border-radius: 14px !important;
  background: rgba(255, 255, 255, 0.08) !important;
  box-shadow: none !important;
}

.hero-actions :deep(.hero-range-select .ant-select-selection-item),
.hero-actions :deep(.hero-range-select .ant-select-selection-placeholder),
.hero-actions :deep(.hero-range-select .ant-select-arrow) {
  color: #fff !important;
  line-height: 42px !important;
}

.hero-actions :deep(.hero-range-select .ant-select-selection-placeholder) {
  color: rgba(255, 255, 255, 0.58) !important;
}

.hero-refresh-btn {
  height: 44px;
  padding: 0 18px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg, #ffffff 0%, #dfe9ff 100%);
  color: #173d96;
  font-weight: 700;
  box-shadow: 0 14px 26px rgba(13, 30, 79, 0.2);
}

.hero-refresh-btn:hover,
.hero-refresh-btn:focus {
  color: #173d96 !important;
  background: linear-gradient(135deg, #ffffff 0%, #e8efff 100%) !important;
}

.hero-brief-value {
  display: block;
  margin-top: 8px;
  color: #fff;
  font-size: 26px;
  line-height: 1;
}

.hero-brief p {
  margin: 12px 0 0;
  color: rgba(240, 245, 255, 0.76);
  font-size: 13px;
  line-height: 1.8;
}

.hero-brief-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.hero-brief-metrics div {
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}

.hero-brief-metrics strong {
  display: block;
  margin-top: 8px;
  color: #fff;
  font-size: 18px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-top: 22px;
}

.kpi-card {
  padding: 20px 20px 18px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.78);
  box-shadow: 0 16px 28px rgba(10, 26, 62, 0.1);
}

.kpi-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.kpi-index {
  color: rgba(40, 62, 115, 0.48);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.kpi-accent {
  flex: 1;
  height: 4px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--accent-color), rgba(255, 255, 255, 0));
}

.kpi-label {
  display: block;
  margin-top: 14px;
  color: #6d7892;
  font-size: 13px;
}

.kpi-value {
  display: block;
  margin-top: 12px;
  color: #172548;
  font-size: 34px;
  line-height: 1;
  letter-spacing: -0.03em;
}

.kpi-value small {
  margin-left: 6px;
  color: #8c95aa;
  font-size: 14px;
  font-weight: 600;
}

.kpi-caption {
  margin-top: 14px;
  color: #7d869b;
  font-size: 12px;
  line-height: 1.65;
}

/* 主内容区 - 统一大容器 */
.main-content {
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 14px 28px rgba(29, 45, 84, 0.08);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.95fr);
  grid-template-areas:
    'trend distribution'
    'ranking dimension';
  gap: 18px;
  padding: 0;
}

.surface-panel {
  position: relative;
  overflow: hidden;
  padding: 22px;
  border-radius: 28px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 255, 0.98) 100%);
  border: 1px solid rgba(225, 232, 248, 0.9);
  box-shadow: 0 14px 28px rgba(29, 45, 84, 0.08);
}

.surface-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at top right, rgba(76, 112, 242, 0.08), transparent 32%);
  pointer-events: none;
}

.trend-panel { grid-area: trend; }
.distribution-panel { grid-area: distribution; }
.ranking-panel { grid-area: ranking; }
.dimension-panel { grid-area: dimension; }

.panel-head {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-kicker {
  display: inline-flex;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(49, 84, 200, 0.08);
  color: #3154c8;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.panel-head h2 {
  margin: 12px 0 0;
  color: #172548;
  font-size: 22px;
  line-height: 1.15;
}

.panel-head p {
  margin: 8px 0 0;
  color: #76809a;
  font-size: 13px;
  line-height: 1.75;
}

.panel-badge {
  min-width: 104px;
  padding: 12px 14px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(37, 72, 179, 0.92), rgba(49, 89, 198, 0.84));
  color: rgba(255, 255, 255, 0.74);
  text-align: right;
}

.panel-badge.light {
  background: rgba(49, 84, 200, 0.08);
  color: #6f7c99;
}

.panel-badge span {
  display: block;
  font-size: 11px;
  letter-spacing: 0.06em;
}

.panel-badge strong {
  display: block;
  margin-top: 8px;
  color: #fff;
  font-size: 16px;
  line-height: 1.3;
}

.panel-badge.light strong {
  color: #1c315e;
}

.trend-board,
.score-dist,
.ranking-list,
.dimension-list {
  position: relative;
  z-index: 1;
}

.trend-board {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.trend-highlight-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 100%;
  padding: 18px;
  border-radius: 22px;
  background:
    linear-gradient(180deg, rgba(27, 58, 150, 0.96) 0%, rgba(48, 84, 197, 0.92) 100%);
  color: rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 28px rgba(34, 63, 148, 0.18);
}

.trend-highlight-card strong {
  margin-top: 8px;
  color: #fff;
  font-size: 28px;
  line-height: 1.1;
}

.trend-highlight-card p {
  margin-top: 28px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  line-height: 1.75;
}

.trend-list,
.score-dist,
.dimension-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.trend-row,
.score-dist-item,
.dimension-row {
  padding: 16px;
  border-radius: 18px;
  background: rgba(244, 247, 253, 0.96);
  border: 1px solid rgba(227, 233, 246, 0.96);
}

.trend-row-head,
.score-dist-head,
.dimension-meta,
.ranking-headline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.trend-month,
.score-dist-label,
.ranking-name,
.dimension-meta span {
  color: #1d2b4f;
  font-size: 14px;
  font-weight: 700;
}

.trend-score,
.ranking-value,
.dimension-meta strong,
.score-dist-head strong {
  color: #1a2646;
  font-size: 14px;
}

.score-dist-head small {
  display: block;
  margin-top: 4px;
  color: #8a94aa;
  font-size: 12px;
}

.score-dist-head em {
  margin-left: 2px;
  font-style: normal;
  color: #8a94aa;
  font-size: 12px;
  font-weight: 600;
}

.trend-track,
.score-dist-track,
.ranking-track,
.dimension-track {
  position: relative;
  overflow: hidden;
  height: 8px;
  margin-top: 12px;
  border-radius: 999px;
  background: rgba(187, 198, 224, 0.34);
}

.trend-track-secondary {
  height: 6px;
  margin-top: 8px;
  background: rgba(186, 205, 197, 0.34);
}

.trend-fill,
.score-dist-fill,
.ranking-fill,
.dimension-fill {
  position: absolute;
  inset: 0 auto 0 0;
  border-radius: inherit;
}

.trend-fill-score {
  background: linear-gradient(90deg, #3154c8 0%, #6d87e4 100%);
}

.trend-fill-pass {
  background: linear-gradient(90deg, #2b8f71 0%, #6cc7ac 100%);
}

.score-dist-fill {
  background: linear-gradient(90deg, var(--band-color) 0%, color-mix(in srgb, var(--band-color) 58%, white 42%) 100%);
}

.ranking-fill {
  background: linear-gradient(90deg, #2746aa 0%, #6e8ee9 100%);
}

.dimension-fill {
  background: linear-gradient(90deg, var(--dimension-color) 0%, color-mix(in srgb, var(--dimension-color) 58%, white 42%) 100%);
}

.trend-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
  color: #7d879c;
  font-size: 12px;
}

.ranking-main {
  flex: 1;
  min-width: 0;
}

.empty-inline {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 200px;
  padding: 30px 22px;
  text-align: center;
  border-radius: 18px;
  background: rgba(244, 247, 253, 0.6);
  border: 1px dashed rgba(181, 194, 224, 0.78);
}

.empty-block {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 270px;
  padding: 30px 22px;
  text-align: center;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(244, 247, 253, 0.9), rgba(248, 250, 255, 0.96));
  border: 1px dashed rgba(181, 194, 224, 0.78);
}

.empty-block.compact {
  min-height: 220px;
}

.empty-block strong {
  color: #1c2d57;
  font-size: 16px;
}

.empty-block p {
  max-width: 420px;
  color: #7d879c;
  font-size: 13px;
  line-height: 1.8;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ranking-row {
  display: flex;
  gap: 14px;
  align-items: flex-start;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(244, 247, 253, 0.96);
  border: 1px solid rgba(227, 233, 246, 0.96);
}

.rank-badge {
  width: 30px;
  height: 30px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: #dfe5f2;
  color: #40506e;
  font-size: 12px;
  font-weight: 800;
}

.rank-badge.rank-1 {
  background: linear-gradient(135deg, #ffe7a8 0%, #ffc95b 100%);
  color: #7d4a00;
}

.rank-badge.rank-2 {
  background: linear-gradient(135deg, #f2f3f8 0%, #d3d8e5 100%);
  color: #565e73;
}

.rank-badge.rank-3 {
  background: linear-gradient(135deg, #ffd8c0 0%, #f6b27f 100%);
  color: #7e4918;
}

.ranking-main {
  flex: 1;
  min-width: 0;
}

@media (max-width: 1400px) {
  .hero-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .dashboard-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .trend-board {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1180px) {
  .hero-grid,
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .dashboard-grid {
    grid-template-areas:
      'trend trend'
      'distribution ranking'
      'dimension dimension';
  }

  .hero-copy h1 {
    font-size: 34px;
  }
}

@media (max-width: 768px) {
  .exam-stat-shell {
    gap: 16px;
  }

  .exam-stat-hero {
    padding: 20px;
    border-radius: 24px;
  }

  .hero-grid,
  .hero-summary,
  .hero-actions,
  .hero-brief-metrics,
  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .main-content {
    border-radius: 16px;
  }

  .dashboard-grid {
    grid-template-areas:
      'trend'
      'distribution'
      'ranking'
      'dimension';
    grid-template-columns: 1fr;
  }

  .hero-copy h1 {
    font-size: 30px;
  }

  .hero-copy p {
    font-size: 14px;
  }

  .hero-actions {
    align-items: stretch;
  }

  .hero-refresh-btn {
    width: 100%;
  }

  .surface-panel {
    padding: 18px;
    border-radius: 22px;
  }

  .panel-head {
    flex-direction: column;
  }

  .panel-badge {
    width: 100%;
    text-align: left;
  }

  .trend-board {
    grid-template-columns: 1fr;
  }

  .trend-row-head,
  .trend-meta,
  .score-dist-head,
  .ranking-headline,
  .dimension-meta {
    align-items: flex-start;
    flex-direction: column;
  }

  .ranking-row {
    flex-direction: column;
  }
}
</style>
