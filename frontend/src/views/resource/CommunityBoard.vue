<template>
  <div class="community-board-page">
    <div class="page-header">
      <div>
        <h2>{{ COMMUNITY_BOARD_TITLE }}</h2>
        <p class="page-sub">按播放、点赞、评论、转发等维度分析社区视频表现，辅助管理员判断内容热度与传播质量。</p>
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
        <a-col v-for="card in overviewCards" :key="card.key" :xs="24" :sm="12" :xl="8">
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

      <a-row :gutter="[16, 16]">
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
                    <span>{{ item.engagementRate.toFixed(2) }}% 互动率</span>
                  </div>
                </div>
                <a-button type="link" size="small" @click="goDetail(item.id)">详情</a-button>
              </div>
            </div>
          </a-card>
        </a-col>
        <a-col :xs="24" :xl="15">
          <a-card :bordered="false" class="module-card">
            <template #title>视频表现明细</template>
            <a-table :data-source="dashboard.latestVideos" :columns="videoColumns" :pagination="false" row-key="id">
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'plays' || column.key === 'likes' || column.key === 'comments' || column.key === 'shares'">
                  {{ formatNumber(record[column.key]) }}
                </template>
                <template v-else-if="column.key === 'engagementRate' || column.key === 'completionRate'">
                  {{ record[column.key].toFixed(2) }}%
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
  LikeOutlined,
  MessageOutlined,
  PlayCircleOutlined,
  ShareAltOutlined,
  RiseOutlined,
  FundOutlined,
} from '@ant-design/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { useRouter } from 'vue-router'
import { getCommunityBoardDashboard } from '@/api/community'
import { COMMUNITY_ASSISTANT_TITLE, COMMUNITY_BOARD_TITLE, COMMUNITY_MANAGEMENT_TITLE } from '@/constants/navigationTitles'

use([CanvasRenderer, BarChart, LineChart, PieChart, GridComponent, LegendComponent, TooltipComponent])

const router = useRouter()
const loading = ref(false)
const range = ref('7d')
const dashboard = ref({
  overview: {},
  trend: [],
  interactionDistribution: [],
  topVideos: [],
  latestVideos: [],
})

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
    key: 'plays',
    label: '总播放量',
    value: formatNumber(dashboard.value.overview.totalPlays || 0),
    hint: `${dashboard.value.overview.totalVideos || 0} 条视频参与统计`,
    icon: PlayCircleOutlined,
    theme: 'blue',
  },
  {
    key: 'likes',
    label: '总点赞量',
    value: formatNumber(dashboard.value.overview.totalLikes || 0),
    hint: `${formatNumber(dashboard.value.overview.totalComments || 0)} 条评论`,
    icon: LikeOutlined,
    theme: 'red',
  },
  {
    key: 'shares',
    label: '总转发量',
    value: formatNumber(dashboard.value.overview.totalShares || 0),
    hint: `${(dashboard.value.overview.engagementRate || 0).toFixed(2)}% 综合互动率`,
    icon: ShareAltOutlined,
    theme: 'gold',
  },
  {
    key: 'comments',
    label: '评论活跃度',
    value: formatNumber(dashboard.value.overview.totalComments || 0),
    hint: `${(dashboard.value.overview.completionRate || 0).toFixed(2)}% 平均完播率`,
    icon: MessageOutlined,
    theme: 'green',
  },
  {
    key: 'engagement',
    label: '互动率',
    value: `${(dashboard.value.overview.engagementRate || 0).toFixed(2)}%`,
    hint: '点赞、评论、转发综合换算',
    icon: RiseOutlined,
    theme: 'violet',
  },
  {
    key: 'completion',
    label: '完播率',
    value: `${(dashboard.value.overview.completionRate || 0).toFixed(2)}%`,
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

function formatNumber(value) {
  return new Intl.NumberFormat('zh-CN').format(Number(value) || 0)
}

function goDetail(id) {
  router.push(`/resource/detail/${id}`)
}

async function loadDashboard() {
  loading.value = true
  try {
    dashboard.value = await getCommunityBoardDashboard({ range: range.value })
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
.content-row {
  margin-top: 16px;
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

.trend-chart,
.pie-chart {
  height: 340px;
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
}

.ranking-meta {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 12px;
  color: #64748b;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }
}
</style>
