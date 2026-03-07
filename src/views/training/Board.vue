<template>
  <div class="board-page">
    <!-- 看板标题 -->
    <div class="board-header">
      <div class="board-title-area">
        <div class="board-icon">📊</div>
        <div>
          <h1 class="board-title">智慧教育培训实时看板</h1>
          <div class="board-sub">培训处 · 数据实时统计（{{ currentDate }}）</div>
        </div>
      </div>
      <div class="board-actions">
        <a-button type="primary" ghost @click="handleExportReport"><DownloadOutlined /> 导出报告</a-button>
      </div>
    </div>

    <!-- KPI 卡片 -->
    <div class="kpi-row">
      <div class="kpi-card" v-for="kpi in kpiData" :key="kpi.label">
        <div class="kpi-icon" :style="{ background: kpi.bgColor }">{{ kpi.icon }}</div>
        <div class="kpi-info">
          <a-statistic :value="kpi.value" :suffix="kpi.suffix" :value-style="{ fontSize: '28px', fontWeight: 700, color: kpi.color }" />
          <div class="kpi-label">{{ kpi.label }}</div>
        </div>
      </div>
    </div>

    <!-- 图表行 -->
    <div class="chart-row" v-if="isMounted">
      <!-- 各市局参训人数 -->
      <div class="chart-card chart-large">
        <div class="chart-title">各市局本月参训人数</div>
        <v-chart class="chart" :option="barOption" autoresize />
      </div>
      <!-- 近6月完成率趋势 -->
      <div class="chart-card chart-medium">
        <div class="chart-title">近6月培训完成率趋势</div>
        <v-chart class="chart" :option="lineOption" autoresize />
      </div>
    </div>

    <!-- 预警 + 排名 -->
    <div class="bottom-row">
      <!-- 异常预警 -->
      <div class="warning-card">
        <div class="card-title"><ExclamationCircleOutlined style="color:#fa8c16" /> 异常预警（{{ warnings.length }}条）</div>
        <div class="warning-list">
          <div class="warning-item" v-for="w in warnings" :key="w.id" :class="w.level">
            <div class="warn-dot" />
            <div class="warn-content">
              <div class="warn-text">{{ w.text }}</div>
              <div class="warn-time">{{ w.time }}</div>
            </div>
            <a-tag :color="w.level === 'high' ? 'red' : 'orange'" size="small">{{ w.level === 'high' ? '紧急' : '提醒' }}</a-tag>
          </div>
        </div>
      </div>

      <!-- 完成率排名 -->
      <div class="rank-card">
        <div class="card-title"><TrophyOutlined style="color:#c8a84b" /> 各市完成率排名</div>
        <div class="rank-list">
          <div class="rank-item" v-for="(city, idx) in cityRanks" :key="city.city">
            <div class="rank-num" :class="idx < 3 ? `rank-${idx+1}` : ''">{{ idx + 1 }}</div>
            <div class="rank-name">{{ city.city }}</div>
            <div class="rank-bar-wrap">
              <div class="rank-bar" :style="{ width: city.rate + '%', background: idx === 0 ? '#c8a84b' : idx === 1 ? '#8c8c8c' : idx === 2 ? '#cd7f32' : '#003087' }" />
            </div>
            <div class="rank-rate">{{ city.rate }}%</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { DownloadOutlined, ExclamationCircleOutlined, TrophyOutlined } from '@ant-design/icons-vue'

import { getKpi, getTrainingTrend, getCityAttendance, getCityCompletion, exportReport } from '@/api/report'

use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent])

const currentDate = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })

const isMounted = ref(false)

// 真实数据
const kpiRaw = ref(null)
const cityAttendanceData = ref([])
const trainingTrendData = ref([])
const cityCompletionData = ref([])

onMounted(async () => {
  // 延迟图表渲染以避免 Ant Design submenu 过渡冲突
  setTimeout(() => { isMounted.value = true }, 200)

  // 并行调用 4 个 report API
  try {
    const [kpiRes, attendanceRes, trendRes, completionRes] = await Promise.all([
      getKpi(),
      getCityAttendance(),
      getTrainingTrend(),
      getCityCompletion()
    ])
    kpiRaw.value = kpiRes
    cityAttendanceData.value = attendanceRes || []
    trainingTrendData.value = trendRes || []
    cityCompletionData.value = completionRes || []
  } catch (e) {
    message.error('加载看板数据失败')
  }
})

const kpiData = computed(() => {
  const k = kpiRaw.value || {}
  return [
    {
      label: '进行中培训班',
      value: k.activeTrainings || 0,
      suffix: '个', icon: '🏫', bgColor: '#e6f0ff', color: '#003087'
    },
    {
      label: '本月参训人数',
      value: k.monthlyTrainees || 0,
      suffix: '人', icon: '👮', bgColor: '#e6fff0', color: '#52c41a'
    },
    {
      label: '本月培训完成率',
      value: k.monthlyCompletionRate || 0,
      suffix: '%', icon: '✅', bgColor: '#fff7e6', color: '#fa8c16'
    },
    {
      label: '待审核学员',
      value: k.pendingEnrollments || 0,
      suffix: '人', icon: '⚠️', bgColor: '#fff1f0', color: '#ff4d4f'
    },
  ]
})

const barOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 80, right: 30, top: 20, bottom: 20 },
  xAxis: { type: 'value', axisLabel: { fontSize: 11 } },
  yAxis: {
    type: 'category',
    data: cityAttendanceData.value.map(c => c.city),
    axisLabel: { fontSize: 11 }
  },
  series: [{
    type: 'bar',
    data: cityAttendanceData.value.map(c => c.count),
    itemStyle: { color: '#003087', borderRadius: [0, 4, 4, 0] },
    barMaxWidth: 20
  }],
}))

const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 20, bottom: 30 },
  xAxis: { type: 'category', data: trainingTrendData.value.map(t => t.month) },
  yAxis: { type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value}%' } },
  series: [{
    type: 'line',
    data: trainingTrendData.value.map(t => t.completionRate),
    smooth: true,
    lineStyle: { color: '#003087', width: 3 },
    itemStyle: { color: '#003087' },
    areaStyle: { color: 'rgba(0,48,135,0.08)' }
  }],
}))

// 异常预警（暂保留前端 Mock，可后续接入后端预警模块）
const warnings = computed(() => [
  { id: 1, text: '当前暂无异常预警', time: '系统实时监测中', level: 'medium' },
])

const cityRanks = computed(() => cityCompletionData.value)

// 导出报告
async function handleExportReport() {
  message.loading({ content: '正在生成报告...', key: 'export', duration: 0 })
  try {
    const blob = await exportReport()
    const url = window.URL.createObjectURL(new Blob([blob]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `培训看板报告_${new Date().toISOString().split('T')[0]}.xlsx`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    message.success({ content: '报告已生成并开始下载！', key: 'export' })
  } catch (e) {
    message.error({ content: '导出报告失败，请重试', key: 'export' })
  }
}
</script>

<style scoped>
.board-page { }
.board-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.board-title-area { display: flex; align-items: center; gap: 12px; }
.board-icon { font-size: 28px; }
.board-title { font-size: 20px; font-weight: 700; color: #001234; margin: 0; }
.board-sub { font-size: 13px; color: #8c8c8c; margin-top: 2px; }
.board-actions { display: flex; gap: 8px; align-items: center; }

.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.kpi-card { background: white; border-radius: 10px; padding: 20px; display: flex; align-items: center; gap: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.kpi-icon { width: 52px; height: 52px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; }
.kpi-label { font-size: 12px; color: #8c8c8c; margin-top: 2px; }

.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
.chart-card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.chart-title { font-size: 14px; font-weight: 600; color: #001234; margin-bottom: 12px; }
.chart { height: 300px; }

.bottom-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.warning-card, .rank-card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.card-title { font-size: 14px; font-weight: 600; color: #001234; margin-bottom: 16px; display: flex; align-items: center; gap: 6px; }
.warning-list { display: flex; flex-direction: column; gap: 10px; }
.warning-item { display: flex; align-items: flex-start; gap: 8px; padding: 10px; border-radius: 6px; background: #fafafa; }
.warning-item.high { background: #fff2f0; }
.warning-item.medium { background: #fffbe6; }
.warn-dot { width: 8px; height: 8px; border-radius: 50%; background: #fa8c16; margin-top: 4px; flex-shrink: 0; }
.high .warn-dot { background: #ff4d4f; }
.warn-content { flex: 1; }
.warn-text { font-size: 13px; color: #262626; line-height: 1.5; }
.warn-time { font-size: 11px; color: #8c8c8c; margin-top: 2px; }

.rank-list { display: flex; flex-direction: column; gap: 10px; }
.rank-item { display: flex; align-items: center; gap: 10px; }
.rank-num { width: 24px; height: 24px; border-radius: 50%; background: #f0f0f0; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; }
.rank-1 { background: #c8a84b; color: white; }
.rank-2 { background: #8c8c8c; color: white; }
.rank-3 { background: #cd7f32; color: white; }
.rank-name { width: 60px; font-size: 13px; color: #262626; flex-shrink: 0; }
.rank-bar-wrap { flex: 1; height: 8px; background: #f0f0f0; border-radius: 4px; overflow: hidden; }
.rank-bar { height: 100%; border-radius: 4px; transition: width 0.6s; }
.rank-rate { width: 40px; text-align: right; font-size: 13px; font-weight: 600; color: #262626; flex-shrink: 0; }

@media (max-width: 768px) {
  .kpi-row { grid-template-columns: 1fr 1fr; }
  .chart-row, .bottom-row { grid-template-columns: 1fr; }
}
</style>
