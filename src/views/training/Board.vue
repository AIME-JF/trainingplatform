<template>
  <div class="board-page">
    <!-- 看板标题 -->
    <div class="board-header">
      <div class="board-title-area">
        <div class="board-icon">📊</div>
        <div>
          <h1 class="board-title">广西公安警务培训实时看板</h1>
          <div class="board-sub">厅政治部训练处 · 数据实时统计（{{ currentDate }}）</div>
        </div>
      </div>
      <div class="board-actions">
        <a-select v-model:value="timeRange" style="width:120px">
          <a-select-option value="month">本月</a-select-option>
          <a-select-option value="quarter">本季度</a-select-option>
          <a-select-option value="year">本年度</a-select-option>
        </a-select>
        <a-button type="primary" ghost><DownloadOutlined /> 导出报告</a-button>
      </div>
    </div>

    <!-- KPI 卡片 -->
    <div class="kpi-row">
      <div class="kpi-card" v-for="kpi in kpiData" :key="kpi.label">
        <div class="kpi-icon" :style="{ background: kpi.bgColor }">{{ kpi.icon }}</div>
        <div class="kpi-info">
          <a-statistic :value="kpi.value" :suffix="kpi.suffix" :value-style="{ fontSize: '28px', fontWeight: 700, color: kpi.color }" />
          <div class="kpi-label">{{ kpi.label }}</div>
          <div class="kpi-trend" :class="kpi.trend > 0 ? 'up' : 'down'">
            {{ kpi.trend > 0 ? '↑' : '↓' }} {{ Math.abs(kpi.trend) }}% 较上月
          </div>
        </div>
      </div>
    </div>

    <!-- 图表行 -->
    <div class="chart-row">
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
          <div class="rank-item" v-for="(city, idx) in cityRanks" :key="city.name">
            <div class="rank-num" :class="idx < 3 ? `rank-${idx+1}` : ''">{{ idx + 1 }}</div>
            <div class="rank-name">{{ city.name }}</div>
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
import { ref } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { DownloadOutlined, ExclamationCircleOutlined, TrophyOutlined } from '@ant-design/icons-vue'

use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent])

const timeRange = ref('month')
const currentDate = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })

const kpiData = [
  { label: '进行中培训班', value: 8, suffix: '个', icon: '🏫', bgColor: '#e6f0ff', color: '#003087', trend: 14 },
  { label: '本月参训人数', value: 1248, suffix: '人', icon: '👮', bgColor: '#e6fff0', color: '#52c41a', trend: 8 },
  { label: '本月培训完成率', value: 84, suffix: '%', icon: '✅', bgColor: '#fff7e6', color: '#fa8c16', trend: 3 },
  { label: '待审核事项', value: 23, suffix: '项', icon: '⚠️', bgColor: '#fff1f0', color: '#ff4d4f', trend: -12 },
]

const cities = ['南宁市', '柳州市', '桂林市', '梧州市', '北海市', '防城港', '钦州市', '贵港市', '玉林市', '百色市', '贺州市', '河池市', '来宾市', '崇左市']
const cityValues = [342, 286, 254, 198, 176, 142, 168, 154, 188, 134, 112, 128, 118, 98]

const barOption = {
  tooltip: { trigger: 'axis' },
  grid: { left: 80, right: 20, top: 20, bottom: 20 },
  xAxis: { type: 'value', axisLabel: { fontSize: 11 } },
  yAxis: { type: 'category', data: cities, axisLabel: { fontSize: 11 } },
  series: [{ type: 'bar', data: cityValues, itemStyle: { color: '#003087', borderRadius: [0, 4, 4, 0] }, barMaxWidth: 20 }],
}

const lineOption = {
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 20, bottom: 30 },
  xAxis: { type: 'category', data: ['9月', '10月', '11月', '12月', '1月', '2月'] },
  yAxis: { type: 'value', min: 60, max: 100, axisLabel: { formatter: '{value}%' } },
  series: [{ type: 'line', data: [72, 76, 78, 81, 82, 84], smooth: true, lineStyle: { color: '#003087', width: 3 }, itemStyle: { color: '#003087' }, areaStyle: { color: 'rgba(0,48,135,0.08)' } }],
}

const warnings = [
  { id: 1, text: '南宁市青秀区25名学员签到率低于60%，连续3天未完成课时', time: '今日 09:32', level: 'high' },
  { id: 2, text: '桂林市刑警支队培训班第4天缺勤率超过20%', time: '今日 08:15', level: 'high' },
  { id: 3, text: '柳州市城中区培训班8名学员请假未返，超出允许天数', time: '昨日 16:40', level: 'medium' },
  { id: 4, text: '梧州市第2期培训班课时进度落后计划3天', time: '昨日 14:20', level: 'medium' },
  { id: 5, text: '百色市右江区有4名学员结业考试不合格，需安排补考', time: '2天前', level: 'medium' },
]

const cityRanks = [
  { name: '南宁市', rate: 94 },
  { name: '桂林市', rate: 91 },
  { name: '柳州市', rate: 88 },
  { name: '北海市', rate: 85 },
  { name: '梧州市', rate: 82 },
  { name: '玉林市', rate: 79 },
  { name: '贵港市', rate: 76 },
  { name: '钦州市', rate: 73 },
]
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
.kpi-trend { font-size: 11px; margin-top: 4px; }
.kpi-trend.up { color: #52c41a; }
.kpi-trend.down { color: #ff4d4f; }

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
