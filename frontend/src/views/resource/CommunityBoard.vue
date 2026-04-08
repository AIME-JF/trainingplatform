<template>
  <div class="community-board-page">
    <div class="page-header">
      <div>
        <h2>{{ COMMUNITY_BOARD_TITLE }}</h2>
        <p class="page-sub">按播放、点赞、评论、转发等维度分析社区视频表现，帮助管理员判断内容热度与传播质量。</p>
      </div>
      <a-space wrap>
        <a-select v-model:value="range" style="width: 140px" @change="loadDashboard">
          <a-select-option value="7d">近7天</a-select-option>
          <a-select-option value="30d">近30天</a-select-option>
        </a-select>
        <a-button @click="$router.push('/resource/assistant')">{{ COMMUNITY_ASSISTANT_TITLE }}</a-button>
        <a-button @click="$router.push('/resource/library')">{{ COMMUNITY_MANAGEMENT_TITLE }}</a-button>
        <a-button type="primary" :loading="loading" @click="loadDashboard">刷新看板</a-button>
      </a-space>
    </div>

    <a-spin :spinning="loading">
      <a-row :gutter="[16, 16]" class="metric-row">
        <a-col v-for="card in overviewCards" :key="card.key" :xs="24" :sm="12" :lg="8" :xl="6">
          <a-card :bordered="false" class="metric-card-shell">
            <div class="metric-card">
              <div class="metric-icon" :class="card.theme">
                <component :is="card.icon" />
              </div>
              <div class="metric-content">
                <div class="metric-label">{{ card.label }}</div>
                <div class="metric-value">{{ card.value }}</div>
                <div class="metric-hint">{{ card.hint }}</div>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
      <div class="metric-note">
        除累计投稿量外，其他指标均按当前时间范围统计；底部明细表仅展示最新 5 条已发布视频。
      </div>

      <a-row :gutter="[16, 16]" class="chart-row">
        <a-col :xs="24" :xl="16">
          <a-card :bordered="false" class="module-card">
            <template #title>互动趋势</template>
            <v-chart :option="trendOption" autoresize class="trend-chart" />
          </a-card>
        </a-col>
        <a-col :xs="24" :xl="8">
          <a-card :bordered="false" class="module-card">
            <template #title>互动结构</template>
            <v-chart :option="interactionOption" autoresize class="pie-chart" />
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="[16, 16]" class="radar-row">
        <a-col :span="24">
          <a-card :bordered="false" class="module-card radar-module">
            <template #title>创作表现雷达</template>
            <template #extra>
              <span class="card-extra">{{ rangeLabel }}真实视频数据</span>
            </template>
            <div class="radar-layout">
              <v-chart :option="radarOption" autoresize class="radar-chart" />
              <div class="radar-metric-grid">
                <div
                  v-for="metric in radarMetrics"
                  :key="metric.key"
                  class="radar-metric"
                  :style="{ '--metric-accent': metric.color }"
                >
                  <div class="radar-metric-label">{{ metric.name }}</div>
                  <div class="radar-metric-value">{{ metric.display }}</div>
                  <div class="radar-metric-hint">{{ metric.hint }}</div>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="[16, 16]" class="content-row">
        <a-col :xs="24" :xl="9">
          <a-card :bordered="false" class="module-card">
            <template #title>热视频榜</template>
            <div class="ranking-list">
              <div v-for="(item, index) in dashboard.topVideos" :key="item.id" class="ranking-item">
                <span class="ranking-index" :class="`rank-${index + 1}`">{{ index + 1 }}</span>
                <div class="ranking-main">
                  <div class="ranking-title">{{ item.title }}</div>
                  <div class="ranking-meta">
                    <span>{{ item.category }}</span>
                    <span>{{ formatNumber(item.plays) }} 播放</span>
                    <span>{{ formatPercent(item.engagementRate) }} 互动率</span>
                  </div>
                </div>
                <a-button type="link" size="small" @click="goDetail(item.id)">详情</a-button>
              </div>
            </div>
          </a-card>
        </a-col>
        <a-col :xs="24" :xl="15">
          <a-card :bordered="false" class="module-card">
            <template #title>最新发布视频表现</template>
            <template #extra>
              <span class="card-extra">仅展示最新 5 条</span>
            </template>
            <a-table :data-source="dashboard.latestVideos" :columns="videoColumns" :pagination="false" row-key="id">
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'plays' || column.key === 'likes' || column.key === 'comments' || column.key === 'shares'">
                  {{ formatNumber(record[column.key]) }}
                </template>
                <template v-else-if="column.key === 'engagementRate' || column.key === 'completionRate'">
                  {{ formatPercent(record[column.key]) }}
                </template>
                <template v-else-if="column.key === 'action'">
                  <a-button type="link" size="small" @click="goDetail(record.id)">查看详情</a-button>
                </template>
              </template>
            </a-table>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  FundOutlined,
  LikeOutlined,
  MessageOutlined,
  PlayCircleOutlined,
  RiseOutlined,
  ShareAltOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart, RadarChart } from 'echarts/charts'
import { GridComponent, LegendComponent, RadarComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { useRouter } from 'vue-router'
import { getCommunityBoardDashboard } from '@/api/community'
import { COMMUNITY_ASSISTANT_TITLE, COMMUNITY_BOARD_TITLE, COMMUNITY_MANAGEMENT_TITLE } from '@/constants/navigationTitles'

use([CanvasRenderer, BarChart, LineChart, PieChart, RadarChart, GridComponent, LegendComponent, RadarComponent, TooltipComponent])

const router = useRouter()
const loading = ref(false)
const range = ref('7d')
const dashboard = ref(createEmptyDashboard())

const overview = computed(() => dashboard.value.overview || {})
const rangeLabel = computed(() => (range.value === '30d' ? '近30天' : '近7天'))
const submissionCount = computed(() => Number(overview.value.submissionCount ?? overview.value.totalVideos ?? 0))

const videoColumns = [
  { title: '视频标题', dataIndex: 'title', key: 'title' },
  { title: '上传单位', dataIndex: 'uploaderName', key: 'uploaderName', width: 130 },
  { title: '播放', dataIndex: 'plays', key: 'plays', width: 100 },
  { title: '点赞', dataIndex: 'likes', key: 'likes', width: 90 },
  { title: '评论', dataIndex: 'comments', key: 'comments', width: 90 },
  { title: '转发', dataIndex: 'shares', key: 'shares', width: 90 },
  { title: '互动率', dataIndex: 'engagementRate', key: 'engagementRate', width: 90 },
  { title: '完播率', dataIndex: 'completionRate', key: 'completionRate', width: 90 },
  { title: '操作', key: 'action', width: 90 },
]

const overviewCards = computed(() => [
  {
    key: 'submission',
    label: '累计投稿量',
    value: formatNumber(submissionCount.value),
    hint: '累计已发布视频总数',
    icon: VideoCameraOutlined,
    theme: 'coral',
  },
  {
    key: 'plays',
    label: '总播放量',
    value: formatNumber(overview.value.totalPlays || 0),
    hint: `${submissionCount.value} 条视频参与统计`,
    icon: PlayCircleOutlined,
    theme: 'blue',
  },
  {
    key: 'likes',
    label: '总点赞量',
    value: formatNumber(overview.value.totalLikes || 0),
    hint: `${formatNumber(overview.value.totalComments || 0)} 条评论`,
    icon: LikeOutlined,
    theme: 'red',
  },
  {
    key: 'shares',
    label: '总转发量',
    value: formatNumber(overview.value.totalShares || 0),
    hint: `${formatPercent(overview.value.engagementRate || 0)} 综合互动率`,
    icon: ShareAltOutlined,
    theme: 'gold',
  },
  {
    key: 'comments',
    label: '周期评论量',
    value: formatNumber(overview.value.totalComments || 0),
    hint: `${rangeLabel.value}内视频评论次数`,
    icon: MessageOutlined,
    theme: 'green',
  },
  {
    key: 'engagement',
    label: '互动率',
    value: formatPercent(overview.value.engagementRate || 0),
    hint: '点赞、评论、转发综合换算',
    icon: RiseOutlined,
    theme: 'violet',
  },
  {
    key: 'completion',
    label: '完播率',
    value: formatPercent(overview.value.completionRate || 0),
    hint: '衡量内容观看深度',
    icon: FundOutlined,
    theme: 'teal',
  },
])

const trendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { top: 0 },
  grid: { top: 40, right: 30, bottom: 30, left: 48 },
  xAxis: {
    type: 'category',
    data: dashboard.value.trend.map((item) => item.date),
  },
  yAxis: [
    { type: 'value', name: '播放量' },
    { type: 'value', name: '互动量' },
  ],
  series: [
    {
      name: '播放量',
      type: 'bar',
      data: dashboard.value.trend.map((item) => item.plays),
      itemStyle: { color: '#1d4ed8', borderRadius: [4, 4, 0, 0] },
    },
    {
      name: '点赞',
      type: 'line',
      yAxisIndex: 1,
      smooth: true,
      data: dashboard.value.trend.map((item) => item.likes),
      itemStyle: { color: '#dc2626' },
    },
    {
      name: '评论',
      type: 'line',
      yAxisIndex: 1,
      smooth: true,
      data: dashboard.value.trend.map((item) => item.comments),
      itemStyle: { color: '#0f766e' },
    },
    {
      name: '转发',
      type: 'line',
      yAxisIndex: 1,
      smooth: true,
      data: dashboard.value.trend.map((item) => item.shares),
      itemStyle: { color: '#d97706' },
    },
  ],
}))

const interactionOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  color: ['#3b82f6', '#fb7185', '#f59e0b'],
  series: [
    {
      type: 'pie',
      radius: ['38%', '66%'],
      center: ['50%', '42%'],
      label: { formatter: '{b}\n{d}%' },
      data: dashboard.value.interactionDistribution.map((item) => ({
        name: item.name,
        value: item.value,
      })),
    },
  ],
}))

const radarMetrics = computed(() => [
  {
    key: 'submission',
    name: '投稿量',
    value: submissionCount.value,
    score: getRadarScore(submissionCount.value, 40),
    display: formatNumber(submissionCount.value),
    hint: '累计已发布视频',
    color: '#fb7185',
  },
  {
    key: 'plays',
    name: '播放量',
    value: Number(overview.value.totalPlays || 0),
    score: getRadarScore(overview.value.totalPlays, 1000),
    display: formatNumber(overview.value.totalPlays || 0),
    hint: `${rangeLabel.value}真实播放`,
    color: '#3b82f6',
  },
  {
    key: 'engagement',
    name: '互动指数',
    value: Number((overview.value.engagementRate || 0).toFixed(2)),
    score: getRadarScore(overview.value.engagementRate, 10),
    display: formatPercent(overview.value.engagementRate || 0),
    hint: '点赞评论转发综合表现',
    color: '#8b5cf6',
  },
  {
    key: 'completion',
    name: '完播率',
    value: Number((overview.value.completionRate || 0).toFixed(2)),
    score: getRadarScore(overview.value.completionRate, 100),
    display: formatPercent(overview.value.completionRate || 0),
    hint: '播放到完播的转化效率',
    color: '#14b8a6',
  },
])

const radarOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: () =>
      radarMetrics.value
        .map((metric) => `${metric.name}：${metric.display}`)
        .join('<br/>'),
  },
  radar: {
    radius: '66%',
    center: ['50%', '52%'],
    splitNumber: 4,
    axisLabel: {
      show: false,
    },
    axisName: {
      color: '#12233d',
      fontSize: 14,
      fontWeight: 600,
    },
    axisNameGap: 16,
    splitLine: {
      lineStyle: {
        color: 'rgba(148, 163, 184, 0.28)',
      },
    },
    axisLine: {
      lineStyle: {
        color: 'rgba(148, 163, 184, 0.24)',
      },
    },
    splitArea: {
      areaStyle: {
        color: ['rgba(15, 23, 42, 0.02)', 'rgba(15, 23, 42, 0.05)'],
      },
    },
    indicator: radarMetrics.value.map((metric) => ({
      name: metric.name,
      min: 0,
      max: 100,
      interval: 25,
      alignTicks: false,
    })),
  },
  series: [
    {
      type: 'radar',
      symbol: 'circle',
      symbolSize: 10,
      lineStyle: {
        color: '#ff4d6d',
        width: 3,
      },
      itemStyle: {
        color: '#ffffff',
        borderColor: '#ff4d6d',
        borderWidth: 3,
      },
      areaStyle: {
        color: 'rgba(255, 77, 109, 0.24)',
      },
      data: [
        {
          value: radarMetrics.value.map((metric) => metric.score),
          name: rangeLabel.value,
        },
      ],
    },
  ],
}))

function createEmptyDashboard() {
  return {
    overview: {
      submissionCount: 0,
      totalVideos: 0,
      totalPlays: 0,
      totalLikes: 0,
      totalComments: 0,
      totalShares: 0,
      engagementRate: 0,
      completionRate: 0,
    },
    trend: [],
    interactionDistribution: [],
    topVideos: [],
    latestVideos: [],
  }
}

function normalizeDashboard(data = {}) {
  const base = createEmptyDashboard()
  return {
    ...base,
    ...data,
    overview: {
      ...base.overview,
      ...(data.overview || {}),
    },
    trend: Array.isArray(data.trend) ? data.trend : [],
    interactionDistribution: Array.isArray(data.interactionDistribution) ? data.interactionDistribution : [],
    topVideos: Array.isArray(data.topVideos) ? data.topVideos : [],
    latestVideos: Array.isArray(data.latestVideos) ? data.latestVideos : [],
  }
}

function formatNumber(value) {
  return new Intl.NumberFormat('zh-CN').format(Number(value) || 0)
}

function formatPercent(value) {
  return `${(Number(value) || 0).toFixed(2)}%`
}

function getRadarScore(value, benchmark) {
  const numeric = Number(value) || 0
  const normalizedBenchmark = Number(benchmark) || 1
  return Math.min(100, Number(((numeric / normalizedBenchmark) * 100).toFixed(2)))
}

function goDetail(id) {
  router.push(`/resource/detail/${id}`)
}

async function loadDashboard() {
  loading.value = true
  try {
    const data = await getCommunityBoardDashboard({ range: range.value })
    dashboard.value = normalizeDashboard(data)
  } catch (error) {
    message.error(error.message || '加载社区看板失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped>
.community-board-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #001234;
}

.page-sub {
  margin: 6px 0 0;
  color: #8c8c8c;
  font-size: 13px;
}

.metric-row,
.chart-row,
.radar-row,
.content-row {
  margin-top: 16px;
}

.metric-note {
  margin-top: 10px;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(241, 245, 249, 0.9);
  color: #64748b;
  font-size: 12px;
}

.metric-card-shell,
.module-card {
  border-radius: 14px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 14px;
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}

.metric-icon.coral {
  background: rgba(251, 113, 133, 0.14);
  color: #e11d48;
}

.metric-icon.blue {
  background: rgba(29, 78, 216, 0.12);
  color: #1d4ed8;
}

.metric-icon.red {
  background: rgba(220, 38, 38, 0.12);
  color: #dc2626;
}

.metric-icon.gold {
  background: rgba(217, 119, 6, 0.12);
  color: #d97706;
}

.metric-icon.green {
  background: rgba(22, 163, 74, 0.12);
  color: #15803d;
}

.metric-icon.violet {
  background: rgba(109, 40, 217, 0.12);
  color: #6d28d9;
}

.metric-icon.teal {
  background: rgba(15, 118, 110, 0.12);
  color: #0f766e;
}

.metric-label {
  font-size: 13px;
  color: #8c8c8c;
}

.metric-value {
  margin-top: 4px;
  font-size: 28px;
  font-weight: 700;
  color: #12233d;
  line-height: 1;
}

.metric-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #8c8c8c;
}

.card-extra {
  font-size: 12px;
  color: #94a3b8;
}

.trend-chart,
.pie-chart {
  height: 340px;
}

.radar-layout {
  display: flex;
  align-items: center;
  gap: 24px;
}

.radar-chart {
  flex: 1.3;
  min-height: 360px;
}

.radar-metric-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.radar-metric {
  padding: 18px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.96), rgba(241, 245, 249, 0.86));
  border: 1px solid rgba(148, 163, 184, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55);
}

.radar-metric-label {
  font-size: 13px;
  color: #64748b;
}

.radar-metric-value {
  margin-top: 10px;
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  color: var(--metric-accent);
}

.radar-metric-hint {
  margin-top: 10px;
  font-size: 12px;
  color: #94a3b8;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  background: #f8fafc;
}

.ranking-index {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  background: #e2e8f0;
  color: #475569;
  flex-shrink: 0;
}

.ranking-index.rank-1 {
  background: #f59e0b;
  color: #fff;
}

.ranking-index.rank-2 {
  background: #94a3b8;
  color: #fff;
}

.ranking-index.rank-3 {
  background: #b45309;
  color: #fff;
}

.ranking-main {
  flex: 1;
  min-width: 0;
}

.ranking-title {
  font-weight: 600;
  color: #0f172a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ranking-meta {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 12px;
  color: #64748b;
}

@media (max-width: 992px) {
  .radar-layout {
    flex-direction: column;
    align-items: stretch;
  }

  .radar-chart {
    min-height: 320px;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }
}

@media (max-width: 576px) {
  .radar-metric-grid {
    grid-template-columns: 1fr;
  }
}
</style>
