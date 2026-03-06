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
        <a-button type="primary" ghost @click="exportCSV"><DownloadOutlined /> 导出成绩</a-button>
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
            <a-button type="link" size="small" @click.stop="showDetail(record)">查看详情</a-button>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 学员详情弹窗 -->
    <a-modal v-model:open="detailVisible" :title="detailStudent ? detailStudent.name + '·成绩详情' : ''" :footer="null" :width="480">
      <div v-if="detailStudent" style="padding:8px 0">
        <a-descriptions :column="2" bordered size="small">
          <a-descriptions-item label="姓名">{{ detailStudent.name }}</a-descriptions-item>
          <a-descriptions-item label="警号">{{ detailStudent.policeId }}</a-descriptions-item>
          <a-descriptions-item label="单位" :span="2">{{ detailStudent.unit }}</a-descriptions-item>
          <a-descriptions-item label="总分"><span style="font-size:18px;font-weight:700" :style="{color: detailStudent.score >= 80 ? '#52c41a' : detailStudent.score >= 60 ? '#fa8c16' : '#ff4d4f'}">{{ detailStudent.score }}</span></a-descriptions-item>
          <a-descriptions-item label="用时">{{ detailStudent.time }}</a-descriptions-item>
          <a-descriptions-item label="法律法规">{{ detailStudent.law }}分</a-descriptions-item>
          <a-descriptions-item label="执法程序">{{ detailStudent.enforce }}分</a-descriptions-item>
          <a-descriptions-item label="证据规则">{{ detailStudent.evidence }}分</a-descriptions-item>
          <a-descriptions-item label="体能技能">{{ detailStudent.physical }}分</a-descriptions-item>
          <a-descriptions-item label="职业道德">{{ detailStudent.ethic }}分</a-descriptions-item>
          <a-descriptions-item label="结果"><a-tag :color="detailStudent.score >= 60 ? 'green' : 'red'">{{ detailStudent.score >= 60 ? '通过' : '不合格' }}</a-tag></a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, RadarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, RadarComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { DownloadOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue'
import { MOCK_EXAM_LIST, MOCK_SCORE_STUDENTS, computeScoreKPI } from '@/mock/scores'

use([CanvasRenderer, BarChart, RadarChart, GridComponent, TooltipComponent, RadarComponent, LegendComponent])

const selectedExam = ref('exam001')
const searchText = ref('')

const examList = MOCK_EXAM_LIST

const students = MOCK_SCORE_STUDENTS
const kpiCards = computed(() => computeScoreKPI(filteredStudents.value))

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
  message.info('已切换考试场次（Demo数据不变）')
}

// 导出 CSV
function exportCSV() {
  const header = ['姓名', '警号', '所属单位', '总分', '法律法规', '执法程序', '证据规则', '体能技能', '职业道德', '用时', '结果']
  const rows = filteredStudents.value.map(s => [
    s.name, s.policeId, s.unit, s.score, s.law, s.enforce, s.evidence, s.physical, s.ethic, s.time, s.score >= 60 ? '通过' : '不合格'
  ])
  const csv = '\uFEFF' + [header, ...rows].map(r => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `成绩导出_${new Date().toLocaleDateString('zh-CN')}.csv`
  a.click()
  URL.revokeObjectURL(url)
  message.success('成绩已导出！')
}

// 查看详情
const detailVisible = ref(false)
const detailStudent = ref(null)
function showDetail(record) {
  detailStudent.value = record
  detailVisible.value = true
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
