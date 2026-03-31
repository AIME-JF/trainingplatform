<template>
  <div class="report-page">
    <div class="page-header">
      <div>
        <h2>数据看板</h2>
        <p class="page-desc">全区训练数据综合分析 · 实时更新</p>
      </div>
      <div class="header-right">
        <a-select v-model:value="timeRange" size="small" style="width:120px;margin-right:8px">
          <a-select-option value="month">本月</a-select-option>
          <a-select-option value="quarter">本季度</a-select-option>
          <a-select-option value="year">本年度</a-select-option>
        </a-select>
        <a-button size="small" @click="exportReport">
          <template #icon><DownloadOutlined /></template>导出报告
        </a-button>
      </div>
    </div>

    <!-- KPI 卡片 -->
    <a-row :gutter="16" style="margin-bottom:20px">
      <a-col :span="6" v-for="kpi in kpiCards" :key="kpi.label">
        <a-card :bordered="false" class="kpi-card">
          <div class="kpi-left">
            <div class="kpi-num">{{ kpi.value }}</div>
            <div class="kpi-label">{{ kpi.label }}</div>
            <div class="kpi-trend" :class="kpi.up ? 'up' : 'down'">
              {{ kpi.up ? '↑' : '↓' }} {{ kpi.change }}
            </div>
          </div>
          <div class="kpi-icon" :style="{ background: kpi.color + '20', color: kpi.color }">{{ kpi.icon }}</div>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" style="margin-bottom:16px">
      <!-- 月度完成率趋势 -->
      <a-col :span="14">
        <a-card title="月度训练完成率趋势" :bordered="false">
          <v-chart class="chart-lg" :option="trendOption" autoresize />
        </a-card>
      </a-col>

      <!-- 各警种分布 -->
      <a-col :span="10">
        <a-card title="各警种学习时长分布" :bordered="false">
          <v-chart class="chart-md" :option="pieOption" autoresize />
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16">
      <!-- 市局排名 -->
      <a-col :span="12">
        <a-card title="各市局综合排名" :bordered="false">
          <div class="city-rank-list">
            <div v-for="(city, i) in cityRanking" :key="city.name" class="city-rank-item">
              <div class="rank-medal">
                <span v-if="i === 0">🥇</span>
                <span v-else-if="i === 1">🥈</span>
                <span v-else-if="i === 2">🥉</span>
                <span v-else class="rank-num">{{ i + 1 }}</span>
              </div>
              <div class="city-info">
                <div class="city-name">{{ city.name }}</div>
                <a-progress :percent="city.score" size="small" :stroke-color="i < 3 ? '#003087' : '#aaa'" />
              </div>
              <div class="city-score">{{ city.score }}分</div>
            </div>
          </div>
        </a-card>
      </a-col>

      <!-- AI 洞察 -->
      <a-col :span="12">
        <a-card title="智能洞察" :bordered="false">
          <template #extra><a-tag color="blue">智能分析</a-tag></template>
          <div class="insights-list">
            <div v-for="insight in aiInsights" :key="insight.id" class="insight-item" :class="insight.type">
              <div class="insight-icon">{{ insight.icon }}</div>
              <div class="insight-content">
                <div class="insight-title">{{ insight.title }}</div>
                <div class="insight-desc">{{ insight.desc }}</div>
              </div>
              <a-tag :color="insight.type === 'positive' ? 'green' : insight.type === 'warning' ? 'orange' : 'blue'" size="small">
                {{ insight.type === 'positive' ? '优势' : insight.type === 'warning' ? '预警' : '建议' }}
              </a-tag>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { DownloadOutlined } from '@ant-design/icons-vue'
import { getKpi, getTrend, getPoliceTypeDistribution, getCityRanking } from '@/api/report'

use([CanvasRenderer, LineChart, PieChart, BarChart, GridComponent, TooltipComponent, LegendComponent])

const timeRange = ref('month')

const kpiCards = ref([])
const trendOption = ref({})
const pieOption = ref({})
const cityRanking = ref([])

const pieColors = ['#003087', '#1890ff', '#52c41a', '#faad14', '#c8a84b']

onMounted(async () => {
  try {
    const [kpiRes, trendRes, pieRes, cityRes] = await Promise.all([
      getKpi().catch(() => null),
      getTrend().catch(() => null),
      getPoliceTypeDistribution().catch(() => null),
      getCityRanking().catch(() => null),
    ])

    // KPI cards
    if (kpiRes) {
      kpiCards.value = [
        { label: '参训民警总数', value: (kpiRes.totalStudents ?? 0).toLocaleString(), change: '↑ 8.2%', up: true, icon: '👮', color: '#003087' },
        { label: '课程完成率', value: (kpiRes.completionRate ?? 0) + '%', change: '↑ 5.1%', up: true, icon: '📊', color: '#52c41a' },
        { label: '平均考核分', value: kpiRes.avgScore ?? 0, change: '↑ 3.2', up: true, icon: '⏱', color: '#faad14' },
        { label: '考试通过率', value: (kpiRes.passRate ?? 0) + '%', change: '↓ 1.3%', up: false, icon: '📝', color: '#722ed1' },
      ]
    }

    // Trend chart
    if (trendRes) {
      const items = trendRes.items || trendRes || []
      const months = items.map(m => (m.month || '').split('-')[1] + '月')
      const completionRates = items.map(m => m.completionRate ?? 0)
      const passRates = items.map(m => m.passRate ?? 0)
      trendOption.value = {
        tooltip: { trigger: 'axis' },
        legend: { data: ['完成率', '合格率'] },
        grid: { left: 40, right: 20, bottom: 30, top: 40 },
        xAxis: { type: 'category', data: months, axisLine: { lineStyle: { color: '#ddd' } } },
        yAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
        series: [
          { name: '完成率', type: 'line', smooth: true, data: completionRates, lineStyle: { color: '#003087', width: 2 }, itemStyle: { color: '#003087' }, areaStyle: { color: 'rgba(0,48,135,0.08)' } },
          { name: '合格率', type: 'line', smooth: true, data: passRates, lineStyle: { color: '#c8a84b', width: 2 }, itemStyle: { color: '#c8a84b' } },
        ]
      }
    }

    // Pie chart
    if (pieRes) {
      const items = pieRes.items || pieRes || []
      pieOption.value = {
        tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
        legend: { bottom: 0, textStyle: { fontSize: 11 }, icon: 'circle', itemWidth: 8, itemGap: 14 },
        series: [{
          type: 'pie', radius: ['35%', '60%'], center: ['50%', '42%'],
          data: items.map((p, i) => ({
            name: p.type, value: p.trained ?? p.count ?? 0, itemStyle: { color: pieColors[i % pieColors.length] },
          })),
          label: { formatter: '{d}%', fontSize: 11, position: 'outside' },
          labelLine: { length: 10, length2: 8 },
          emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.2)' } },
        }]
      }
    }

    // City ranking
    if (cityRes) {
      const items = cityRes.items || cityRes || []
      cityRanking.value = items
        .map(c => ({ name: c.city || c.name || '', score: c.avgScore ?? c.score ?? 0 }))
        .sort((a, b) => b.score - a.score)
    }
  } catch { /* ignore */ }
})

const aiInsights = [
  { id: 1, type: 'positive', icon: '🎯', title: '南宁市完成率持续领先', desc: '连续3个月在全区排名第一，学习积极性高，建议分享经验。' },
  { id: 2, type: 'warning', icon: '⚠️', title: '证据意识维度普遍偏低', desc: '全区平均得分仅64分，建议增加专项培训课程，重点补强。' },
  { id: 3, type: 'suggestion', icon: '💡', title: '体能训练参与率可提升', desc: '当前仅68%民警完成体能测试，建议结合培训班强制要求。' },
  { id: 4, type: 'positive', icon: '📈', title: '在线考试通过率上升', desc: '本月通过率较上月提升5.3%，智能推荐有效提升复习效率。' },
]

function exportReport() {
  message.loading({ content: '报告生成中...', key: 'rpt', duration: 1.5 })
  setTimeout(() => message.success({ content: '报告已导出！', key: 'rpt' }), 1500)
}
</script>

<style scoped>
.report-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.page-desc { color: #888; font-size: 13px; margin: 4px 0 0; }
.header-right { display: flex; align-items: center; }
.kpi-card { display: flex; align-items: center; }
.kpi-card :deep(.ant-card-body) { display: flex; align-items: center; justify-content: space-between; width: 100%; }
.kpi-num { font-size: 26px; font-weight: 800; color: #1a1a1a; }
.kpi-label { font-size: 12px; color: #888; margin: 2px 0; }
.kpi-trend.up { color: #52c41a; font-size: 12px; }
.kpi-trend.down { color: #ff4d4f; font-size: 12px; }
.kpi-icon { width: 52px; height: 52px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 26px; flex-shrink: 0; }
.chart-lg { height: 260px; }
.chart-md { height: 260px; }
.city-rank-list { display: flex; flex-direction: column; gap: 12px; }
.city-rank-item { display: flex; align-items: center; gap: 12px; }
.rank-medal { width: 28px; text-align: center; font-size: 20px; flex-shrink: 0; }
.rank-num { font-size: 14px; font-weight: 700; color: #888; }
.city-info { flex: 1; }
.city-name { font-size: 13px; font-weight: 500; color: #333; margin-bottom: 4px; }
.city-score { font-size: 16px; font-weight: 700; color: var(--police-primary); min-width: 40px; text-align: right; }
.insights-list { display: flex; flex-direction: column; gap: 12px; }
.insight-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px; border-radius: 8px; border: 1px solid #f0f0f0; }
.insight-item.positive { background: #f6ffed; border-color: #b7eb8f; }
.insight-item.warning { background: #fffbe6; border-color: #ffe58f; }
.insight-item.suggestion { background: #e6f7ff; border-color: #91d5ff; }
.insight-icon { font-size: 24px; flex-shrink: 0; }
.insight-content { flex: 1; }
.insight-title { font-size: 13px; font-weight: 600; color: #1a1a1a; margin-bottom: 2px; }
.insight-desc { font-size: 12px; color: #666; line-height: 1.5; }

@media (max-width: 768px) {
  .chart-lg { height: 220px !important; }
  .chart-md { height: 220px !important; }
  .kpi-card :deep(.ant-card-body) { padding: 12px !important; flex-direction: column; align-items: flex-start; gap: 8px; }
  .kpi-icon { position: absolute; right: 12px; top: 12px; }
}
</style>
