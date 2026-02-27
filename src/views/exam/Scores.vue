<template>
  <div class="scores-page">
    <!-- 页头 -->
    <div class="page-header-bar">
      <div>
        <h2 class="page-h2">成绩管理</h2>
        <p class="page-sub">查看考试场次成绩汇总与能力分析</p>
      </div>
      <div class="header-actions">
        <a-select v-model:value="selectedExam" style="width: 300px" @change="loadExamData">
          <a-select-option v-for="exam in examList" :key="exam.id" :value="exam.id">
            {{ exam.title }}
          </a-select-option>
        </a-select>
        <a-button type="primary" ghost><DownloadOutlined /> 导出成绩</a-button>
      </div>
    </div>

    <!-- KPI 卡片 -->
    <div class="score-kpis">
      <div class="skpi-card" v-for="kpi in kpiCards" :key="kpi.label">
        <div class="skpi-value" :style="{ color: kpi.color }">{{ kpi.value }}<span class="skpi-unit">{{ kpi.unit }}</span></div>
        <div class="skpi-label">{{ kpi.label }}</div>
      </div>
    </div>

    <!-- 图表区 -->
    <div class="chart-row">
      <!-- 成绩分布 -->
      <div class="chart-card">
        <div class="chart-title">成绩分布</div>
        <v-chart class="chart-mid" :option="barOption" autoresize />
      </div>
      <!-- 能力维度雷达 -->
      <div class="chart-card">
        <div class="chart-title">班级平均能力画像（五维）</div>
        <v-chart class="chart-mid" :option="radarOption" autoresize />
      </div>
    </div>

    <!-- 薄弱点提示 -->
    <div class="weak-alert">
      <ExclamationCircleOutlined style="color:#fa8c16;margin-right:8px" />
      <span>本场薄弱环节：<b>证据规则</b>（班级均分 68分）和<b>执法程序</b>（72分）低于合格线，建议增加专项训练</span>
    </div>

    <!-- 明细表 -->
    <div class="detail-table-card">
      <div class="table-header">
        <h3 class="table-title">学员成绩明细</h3>
        <a-input-search v-model:value="searchText" placeholder="搜索姓名" style="width:200px" allow-clear />
      </div>
      <a-table
        :columns="columns"
        :data-source="filteredStudents"
        row-key="id"
        :pagination="{ pageSize: 10 }"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'score'">
            <span :class="record.score >= 80 ? 'score-good' : record.score >= 60 ? 'score-ok' : 'score-fail'">
              {{ record.score }}
            </span>
          </template>
          <template v-if="column.key === 'pass'">
            <a-tag :color="record.score >= 60 ? 'green' : 'red'">
              {{ record.score >= 60 ? '通过' : '不合格' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-button type="link" size="small">查看详情</a-button>
          </template>
        </template>
      </a-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, RadarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, RadarComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { DownloadOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue'

use([CanvasRenderer, BarChart, RadarChart, GridComponent, TooltipComponent, RadarComponent, LegendComponent])

const selectedExam = ref('exam001')
const searchText = ref('')

const examList = [
  { id: 'exam001', title: '2025年Q1执法规范化综合考试' },
  { id: 'exam002', title: '2024年年度基础法律知识考核' },
  { id: 'exam003', title: '证据收集专项考试（2月场）' },
]

const kpiCards = [
  { label: '参考人数', value: 48, unit: '人', color: '#003087' },
  { label: '班级平均分', value: 78.5, unit: '分', color: '#52c41a' },
  { label: '最高分', value: 96, unit: '分', color: '#c8a84b' },
  { label: '通过率', value: '87.5', unit: '%', color: '#fa8c16' },
]

const barOption = {
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, top: 20, bottom: 30 },
  xAxis: { type: 'category', data: ['60分以下', '60-69', '70-79', '80-89', '90分以上'] },
  yAxis: { type: 'value', name: '人数' },
  series: [{
    type: 'bar', data: [6, 8, 14, 13, 7],
    itemStyle: { color: (p) => ['#ff4d4f','#fa8c16','#1677ff','#52c41a','#c8a84b'][p.dataIndex], borderRadius: [4,4,0,0] },
    barMaxWidth: 48,
    label: { show: true, position: 'top', formatter: '{c}人' },
  }],
}

const radarOption = {
  tooltip: {},
  radar: {
    indicator: [
      { name: '法律法规', max: 100 },
      { name: '执法程序', max: 100 },
      { name: '证据规则', max: 100 },
      { name: '体能技能', max: 100 },
      { name: '职业道德', max: 100 },
    ],
    shape: 'polygon',
    splitNumber: 4,
    axisName: { color: '#595959', fontSize: 12 },
    splitArea: { areaStyle: { color: ['rgba(0,48,135,0.04)', 'rgba(0,48,135,0.02)'] } },
  },
  series: [{
    type: 'radar',
    data: [{
      value: [84, 72, 68, 91, 87],
      name: '班级平均',
      itemStyle: { color: '#003087' },
      areaStyle: { color: 'rgba(0,48,135,0.15)' },
      lineStyle: { color: '#003087', width: 2 },
    }],
  }],
}

const students = [
  { id: 's1', name: '张伟', policeId: 'GX-NN-2056', unit: '青秀区刑警大队', score: 89, law: 92, enforce: 81, evidence: 85, physical: 95, ethic: 90, time: '1小时23分' },
  { id: 's2', name: '陈小明', policeId: 'GX-NN-2101', unit: '江南区派出所', score: 76, law: 80, enforce: 70, evidence: 72, physical: 85, ethic: 80, time: '1小时45分' },
  { id: 's3', name: '刘芳', policeId: 'GX-NN-2234', unit: '西乡塘交警大队', score: 62, law: 65, enforce: 60, evidence: 55, physical: 72, ethic: 68, time: '2小时' },
  { id: 's4', name: '黄志远', policeId: 'GX-GL-1045', unit: '秀峰区派出所', score: 93, law: 96, enforce: 90, evidence: 92, physical: 98, ethic: 94, time: '1小时05分' },
  { id: 's5', name: '梁美华', policeId: 'GX-ZZ-0892', unit: '城中区刑警队', score: 55, law: 58, enforce: 50, evidence: 48, physical: 65, ethic: 60, time: '2小时' },
  { id: 's6', name: '覃建军', policeId: 'GX-GL-2156', unit: '灵川县公安局', score: 84, law: 88, enforce: 82, evidence: 78, physical: 90, ethic: 88, time: '1小时32分' },
  { id: 's7', name: '韦国强', policeId: 'GX-BS-0334', unit: '右江区派出所', score: 71, law: 75, enforce: 68, evidence: 65, physical: 80, ethic: 72, time: '1小时50分' },
  { id: 's8', name: '李建华', policeId: 'GX-NN-3012', unit: '兴宁区派出所', score: 88, law: 90, enforce: 85, evidence: 84, physical: 92, ethic: 90, time: '1小时18分' },
]

const columns = [
  { title: '姓名', dataIndex: 'name', key: 'name', width: 80, sorter: (a, b) => a.name.localeCompare(b.name) },
  { title: '警号', dataIndex: 'policeId', key: 'policeId', width: 120 },
  { title: '所属单位', dataIndex: 'unit', key: 'unit' },
  { title: '总分', key: 'score', width: 80, sorter: (a, b) => a.score - b.score },
  { title: '法律法规', dataIndex: 'law', key: 'law', width: 90 },
  { title: '执法程序', dataIndex: 'enforce', key: 'enforce', width: 90 },
  { title: '证据规则', dataIndex: 'evidence', key: 'evidence', width: 90 },
  { title: '体能技能', dataIndex: 'physical', key: 'physical', width: 90 },
  { title: '用时', dataIndex: 'time', key: 'time', width: 100 },
  { title: '结果', key: 'pass', width: 80 },
  { title: '操作', key: 'action', width: 90, fixed: 'right' },
]

const filteredStudents = computed(() => {
  if (!searchText.value) return students
  return students.filter(s => s.name.includes(searchText.value) || s.policeId.includes(searchText.value))
})

function loadExamData() {
  // Demo: 数据不变，实际接入 API 时替换
}
</script>

<style scoped>
.scores-page { }
.page-header-bar { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.page-h2 { font-size: 20px; font-weight: 700; color: #001234; margin: 0 0 4px; }
.page-sub { font-size: 13px; color: #8c8c8c; margin: 0; }
.header-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }

.score-kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.skpi-card { background: white; border-radius: 10px; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.skpi-value { font-size: 32px; font-weight: 700; }
.skpi-unit { font-size: 14px; margin-left: 2px; }
.skpi-label { font-size: 12px; color: #8c8c8c; margin-top: 6px; }

.chart-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
.chart-card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.chart-title { font-size: 14px; font-weight: 600; color: #001234; margin-bottom: 12px; }
.chart-mid { height: 260px; }

.weak-alert { background: #fffbe6; border: 1px solid #ffe58f; border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; font-size: 13px; color: #595959; display: flex; align-items: flex-start; }
.weak-alert b { color: #d46b08; }

.detail-table-card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.table-title { font-size: 15px; font-weight: 600; margin: 0; color: #001234; }
.score-good { color: #52c41a; font-weight: 700; font-size: 16px; }
.score-ok { color: #fa8c16; font-weight: 700; font-size: 16px; }
.score-fail { color: #ff4d4f; font-weight: 700; font-size: 16px; }

@media (max-width: 768px) {
  .score-kpis { grid-template-columns: 1fr 1fr; }
  .chart-row { grid-template-columns: 1fr; }
}
</style>
