<template>
  <div class="data-board-page">
    <div class="page-header">
      <div>
        <h2>数据看板</h2>
        <p class="page-sub">根据角色权限展示可见的数据模块</p>
      </div>
      <a-space>
        <a-select v-model:value="activeCategory" style="width: 160px" @change="onCategoryChange">
          <a-select-option value="all">全部模块</a-select-option>
          <a-select-option value="general">综合数据</a-select-option>
          <a-select-option value="training">培训运营</a-select-option>
          <a-select-option value="exam">考试统计</a-select-option>
        </a-select>
        <a-button @click="handleExport" :loading="exporting">导出报表</a-button>
      </a-space>
    </div>

    <a-spin :spinning="loading">
      <a-empty v-if="!loading && !visibleModules.length" description="暂无可查看的看板模块" />

      <a-row :gutter="[16, 16]">
        <!-- 核心指标概览 -->
        <a-col :span="24" v-if="hasModule('kpi_overview')">
          <a-card :bordered="false" class="module-card">
            <template #title>核心指标概览</template>
            <a-row :gutter="16">
              <a-col :span="6" v-for="item in kpiCards" :key="item.label">
                <a-statistic :title="item.label" :value="item.value" :suffix="item.suffix" :value-style="{ color: item.color }" />
              </a-col>
            </a-row>
          </a-card>
        </a-col>

        <!-- 培训运营指标 -->
        <a-col :span="24" v-if="hasModule('training_kpi')">
          <a-card :bordered="false" class="module-card">
            <template #title>培训运营指标</template>
            <a-row :gutter="16">
              <a-col :span="6" v-for="item in trainingKpiCards" :key="item.label">
                <a-statistic :title="item.label" :value="item.value" :suffix="item.suffix" :value-style="{ color: item.color }" />
              </a-col>
            </a-row>
          </a-card>
        </a-col>

        <!-- 完成率趋势 -->
        <a-col :span="12" v-if="hasModule('completion_trend')">
          <a-card :bordered="false" class="module-card chart-card">
            <template #title>完成率趋势</template>
            <v-chart :option="completionTrendOption" autoresize style="height: 320px" />
          </a-card>
        </a-col>

        <!-- 培训趋势 -->
        <a-col :span="12" v-if="hasModule('training_trend')">
          <a-card :bordered="false" class="module-card chart-card">
            <template #title>培训完成率趋势</template>
            <v-chart :option="trainingTrendOption" autoresize style="height: 320px" />
          </a-card>
        </a-col>

        <!-- 警种分布 -->
        <a-col :span="12" v-if="hasModule('police_type_dist')">
          <a-card :bordered="false" class="module-card chart-card">
            <template #title>警种学习分布</template>
            <v-chart :option="policeTypeOption" autoresize style="height: 320px" />
          </a-card>
        </a-col>

        <!-- 各单位参训人数 -->
        <a-col :span="12" v-if="hasModule('city_attendance')">
          <a-card :bordered="false" class="module-card chart-card">
            <template #title>各单位参训人数</template>
            <v-chart :option="cityAttendanceOption" autoresize style="height: 320px" />
          </a-card>
        </a-col>

        <!-- 各单位考核排名 -->
        <a-col :span="12" v-if="hasModule('city_ranking')">
          <a-card :bordered="false" class="module-card">
            <template #title>各单位考核排名</template>
            <div class="ranking-list">
              <div v-for="(item, idx) in cityRankingData" :key="item.city" class="ranking-item">
                <span class="ranking-medal" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</span>
                <span class="ranking-name">{{ item.city }}</span>
                <a-progress :percent="Math.round(item.score)" size="small" :stroke-color="idx < 3 ? '#003087' : '#8c8c8c'" style="flex:1" />
                <span class="ranking-score">{{ item.score.toFixed(1) }}分</span>
              </div>
            </div>
          </a-card>
        </a-col>

        <!-- 各单位完成率排名 -->
        <a-col :span="12" v-if="hasModule('city_completion')">
          <a-card :bordered="false" class="module-card">
            <template #title>各单位培训完成率</template>
            <div class="ranking-list">
              <div v-for="(item, idx) in cityCompletionData" :key="item.city" class="ranking-item">
                <span class="ranking-medal" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</span>
                <span class="ranking-name">{{ item.city }}</span>
                <a-progress :percent="Math.round(item.rate)" size="small" :stroke-color="idx < 3 ? '#1a7a3e' : '#8c8c8c'" style="flex:1" />
                <span class="ranking-score">{{ item.rate.toFixed(1) }}%</span>
              </div>
            </div>
          </a-card>
        </a-col>

        <!-- 考试统计模块 -->
        <a-col :span="24" v-if="hasModule('exam_statistics')">
          <a-card :bordered="false" class="module-card">
            <template #title>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>考试统计</span>
                <a-select v-model:value="examTimeRange" style="width: 120px" @change="loadExamStatistics">
                  <a-select-option value="7d">近7天</a-select-option>
                  <a-select-option value="30d">近30天</a-select-option>
                  <a-select-option value="month">本月</a-select-option>
                  <a-select-option value="year">本年</a-select-option>
                </a-select>
              </div>
            </template>
            <a-row :gutter="16">
              <a-col :span="6" v-for="item in examKpiCards" :key="item.label">
                <a-statistic :title="item.label" :value="item.value" :suffix="item.suffix" :value-style="{ color: item.color }" />
              </a-col>
            </a-row>
          </a-card>
        </a-col>

        <!-- 考试月度趋势 -->
        <a-col :span="12" v-if="hasModule('exam_statistics')">
          <a-card :bordered="false" class="module-card chart-card">
            <template #title>考试月度趋势</template>
            <v-chart :option="examTrendOption" autoresize style="height: 320px" />
          </a-card>
        </a-col>

        <!-- 分数段分布 -->
        <a-col :span="12" v-if="hasModule('exam_statistics')">
          <a-card :bordered="false" class="module-card chart-card">
            <template #title>分数段分布</template>
            <v-chart :option="scoreDistributionOption" autoresize style="height: 320px" />
          </a-card>
        </a-col>

        <!-- 各单位考试排名 -->
        <a-col :span="12" v-if="hasModule('exam_statistics')">
          <a-card :bordered="false" class="module-card">
            <template #title>各单位考试排名</template>
            <div class="ranking-list">
              <div v-for="(item, idx) in cityExamRankingData" :key="item.city" class="ranking-item">
                <span class="ranking-medal" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</span>
                <span class="ranking-name">{{ item.city }}</span>
                <a-progress :percent="Math.round(item.avgScore)" size="small" :stroke-color="idx < 3 ? '#003087' : '#8c8c8c'" style="flex:1" />
                <span class="ranking-score">{{ item.avgScore.toFixed(1) }}分</span>
              </div>
            </div>
          </a-card>
        </a-col>

        <!-- 各维度平均得分 -->
        <a-col :span="12" v-if="hasModule('exam_statistics')">
          <a-card :bordered="false" class="module-card chart-card">
            <template #title>各维度平均得分</template>
            <v-chart :option="dimensionScoreOption" autoresize style="height: 320px" />
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart, RadarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, RadarComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { useAuthStore } from '@/stores/auth'

use([CanvasRenderer, LineChart, PieChart, BarChart, RadarChart, GridComponent, TooltipComponent, LegendComponent, RadarComponent])
import { getDashboardModules } from '@/api/system'
import {
  getKpi, getTrend, getTrainingTrend,
  getCityAttendance, getCityCompletion,
  getPoliceTypeDistribution, getCityRanking,
  exportReport,
} from '@/api/report'
import { getExamStatistics } from '@/api/exam'
import { downloadBlob } from '@/utils/download'

const authStore = useAuthStore()
const loading = ref(true)
const exporting = ref(false)
const activeCategory = ref('all')
const modules = ref([])

// data
const kpiData = ref({})
const trendData = ref([])
const trainingTrendData = ref([])
const policeTypeData = ref([])
const cityAttendanceData = ref([])
const cityRankingData = ref([])
const cityCompletionData = ref([])

// 考试统计数据
const examTimeRange = ref('30d')
const examStatisticsData = ref({})

const visibleModules = computed(() => {
  if (activeCategory.value === 'all') return modules.value
  return modules.value.filter(m => m.category === activeCategory.value)
})

function hasModule(key) {
  return visibleModules.value.some(m => m.moduleKey === key)
}

const kpiCards = computed(() => [
  { label: '参训民警总数', value: kpiData.value.totalStudents || 0, suffix: '人', color: '#003087' },
  { label: '课程完成率', value: kpiData.value.completionRate || 0, suffix: '%', color: '#1a7a3e' },
  { label: '平均考核分', value: kpiData.value.avgScore || 0, suffix: '分', color: '#d48806' },
  { label: '考试通过率', value: kpiData.value.passRate || 0, suffix: '%', color: '#0958d9' },
])

const trainingKpiCards = computed(() => [
  { label: '进行中培训班', value: kpiData.value.activeTrainings || 0, suffix: '个', color: '#003087' },
  { label: '本月参训人数', value: kpiData.value.monthlyTrainees || 0, suffix: '人', color: '#1a7a3e' },
  { label: '本月完成率', value: kpiData.value.monthlyCompletionRate || 0, suffix: '%', color: '#d48806' },
  { label: '待审核学员', value: kpiData.value.pendingEnrollments || 0, suffix: '人', color: '#cf1322' },
])

// 考试统计 KPI 卡片
const examKpiCards = computed(() => [
  { label: '总考试数', value: examStatisticsData.value.totalExams || 0, suffix: '场', color: '#003087' },
  { label: '参考人次', value: examStatisticsData.value.totalSubmitted || 0, suffix: '人', color: '#1a7a3e' },
  { label: '平均分', value: examStatisticsData.value.avgScore || 0, suffix: '分', color: '#d48806' },
  { label: '及格率', value: examStatisticsData.value.passRate || 0, suffix: '%', color: '#0958d9' },
])

// 考试月度趋势图
const examTrendOption = computed(() => {
  const data = examStatisticsData.value.monthlyTrend || []
  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 20, right: 20, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: data.map(d => d.month) },
    yAxis: { type: 'value' },
    series: [
      {
        name: '平均分',
        type: 'line',
        data: data.map(d => d.avgScore),
        smooth: true,
        areaStyle: { opacity: 0.15 },
        itemStyle: { color: '#003087' },
      },
      {
        name: '及格率',
        type: 'line',
        data: data.map(d => d.passRate),
        smooth: true,
        yAxisIndex: 0,
        itemStyle: { color: '#1a7a3e' },
      },
    ],
  }
})

// 分数段分布饼图
const scoreDistributionOption = computed(() => {
  const dist = examStatisticsData.value.scoreDistribution || {}
  const data = [
    { name: '优秀(90+)', value: dist.excellent || 0 },
    { name: '良好(80-89)', value: dist.good || 0 },
    { name: '及格(60-79)', value: dist.pass || 0 },
    { name: '不及格(<60)', value: dist.fail || 0 },
  ]
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
    legend: { bottom: 10, left: 'center' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data,
      label: { formatter: '{b}: {c}' },
      itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
      color: ['#003087', '#1a7a3e', '#d48806', '#cf1322'],
    }],
  }
})

// 各单位考试排名数据
const cityExamRankingData = computed(() => {
  return examStatisticsData.value.cityRanking || []
})

// 各维度平均得分雷达图
const dimensionScoreOption = computed(() => {
  const dimScores = examStatisticsData.value.dimensionAvgScores || {}
  const dimensions = [
    { name: '法律法规', value: dimScores.law || 0 },
    { name: '执法能力', value: dimScores.enforce || 0 },
    { name: '证据运用', value: dimScores.evidence || 0 },
    { name: '体能测试', value: dimScores.physical || 0 },
    { name: '职业道德', value: dimScores.ethic || 0 },
  ]
  return {
    tooltip: {},
    radar: {
      indicator: dimensions.map(d => ({ name: d.name, max: 100 })),
      radius: '65%',
    },
    series: [{
      type: 'radar',
      data: [{ value: dimensions.map(d => d.value), name: '各维度得分' }],
      areaStyle: { opacity: 0.3 },
      itemStyle: { color: '#003087' },
    }],
  }
})

async function loadExamStatistics() {
  try {
    const data = await getExamStatistics({ time_range: examTimeRange.value })
    examStatisticsData.value = data || {}
  } catch (e) {
    console.error('加载考试统计失败', e)
  }
}

function buildLineOption(data, xKey, yKey, name, color) {
  return {
    tooltip: { trigger: 'axis' },
    grid: { top: 20, right: 20, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: data.map(d => d[xKey]) },
    yAxis: { type: 'value' },
    series: [{ name, type: 'line', data: data.map(d => d[yKey]), smooth: true, areaStyle: { opacity: 0.15 }, itemStyle: { color } }],
  }
}

const completionTrendOption = computed(() =>
  buildLineOption(trendData.value, 'month', 'avgScore', '平均分', '#003087')
)

const trainingTrendOption = computed(() =>
  buildLineOption(trainingTrendData.value, 'month', 'completionRate', '完成率', '#1a7a3e')
)

const policeTypeOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [{
    type: 'pie', radius: ['40%', '70%'],
    data: policeTypeData.value.map(d => ({ name: d.name, value: d.value })),
    label: { formatter: '{b}: {c}人' },
  }],
}))

const cityAttendanceOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { top: 10, right: 20, bottom: 30, left: 100 },
  xAxis: { type: 'value' },
  yAxis: { type: 'category', data: cityAttendanceData.value.map(d => d.city).reverse() },
  series: [{
    type: 'bar',
    data: cityAttendanceData.value.map(d => d.count).reverse(),
    itemStyle: { color: '#003087', borderRadius: [0, 4, 4, 0] },
  }],
}))

async function loadModules() {
  try {
    modules.value = await getDashboardModules()
  } catch {
    modules.value = []
  }
}

async function loadData() {
  loading.value = true
  try {
    const moduleKeys = new Set(modules.value.map(m => m.moduleKey))
    const tasks = []

    if (moduleKeys.has('kpi_overview') || moduleKeys.has('training_kpi')) {
      tasks.push(getKpi().then(d => { kpiData.value = d }).catch(() => {}))
    }
    if (moduleKeys.has('completion_trend')) {
      tasks.push(getTrend().then(d => { trendData.value = d || [] }).catch(() => {}))
    }
    if (moduleKeys.has('training_trend')) {
      tasks.push(getTrainingTrend().then(d => { trainingTrendData.value = d || [] }).catch(() => {}))
    }
    if (moduleKeys.has('police_type_dist')) {
      tasks.push(getPoliceTypeDistribution().then(d => { policeTypeData.value = d || [] }).catch(() => {}))
    }
    if (moduleKeys.has('city_attendance')) {
      tasks.push(getCityAttendance().then(d => { cityAttendanceData.value = d || [] }).catch(() => {}))
    }
    if (moduleKeys.has('city_ranking')) {
      tasks.push(getCityRanking().then(d => { cityRankingData.value = d || [] }).catch(() => {}))
    }
    if (moduleKeys.has('city_completion')) {
      tasks.push(getCityCompletion().then(d => { cityCompletionData.value = d || [] }).catch(() => {}))
    }
    if (moduleKeys.has('exam_statistics')) {
      tasks.push(loadExamStatistics())
    }

    await Promise.all(tasks)
  } finally {
    loading.value = false
  }
}

async function handleExport() {
  exporting.value = true
  try {
    const blob = await exportReport()
    downloadBlob(blob, '数据看板报表.xlsx')
  } catch (e) {
    message.error(e.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

function onCategoryChange() {
  // 仅切换过滤，数据已全部加载
}

onMounted(async () => {
  await loadModules()
  await loadData()
})
</script>

<style scoped>
.data-board-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-header h2 { margin: 0; color: #001234; }
.page-sub { margin: 4px 0 0; color: #8c8c8c; font-size: 13px; }
.module-card { border-radius: 12px; }
.chart-card { min-height: 380px; }
.ranking-list { display: flex; flex-direction: column; gap: 12px; max-height: 320px; overflow-y: auto; }
.ranking-item { display: flex; align-items: center; gap: 10px; }
.ranking-medal {
  width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; background: #f0f0f0; color: #8c8c8c; flex-shrink: 0;
}
.ranking-medal.rank-1 { background: #ffd700; color: #fff; }
.ranking-medal.rank-2 { background: #c0c0c0; color: #fff; }
.ranking-medal.rank-3 { background: #cd7f32; color: #fff; }
.ranking-name { min-width: 80px; font-size: 13px; color: #333; }
.ranking-score { min-width: 50px; text-align: right; font-size: 13px; font-weight: 600; color: #1f1f1f; }
</style>
