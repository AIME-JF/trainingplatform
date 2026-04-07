<template>
  <div class="community-assistant-page">
    <div class="page-header">
      <div>
        <h2>{{ COMMUNITY_ASSISTANT_TITLE }}</h2>
        <p class="page-sub">AI 预审社区上传视频，优先拦截高风险内容，并把待人工复核任务集中到一个工作台。</p>
      </div>
      <a-space wrap>
        <a-button @click="$router.push('/resource/library')">{{ COMMUNITY_MANAGEMENT_TITLE }}</a-button>
        <a-button @click="handlePendingFeature('我的上传')">我的上传</a-button>
        <a-button @click="handlePendingFeature('提交审核')">提交审核</a-button>
        <a-button @click="handlePendingFeature('审核轨迹')">审核轨迹</a-button>
        <a-button type="primary" :loading="loading" @click="loadDashboard">刷新助手</a-button>
      </a-space>
    </div>

    <a-spin :spinning="loading">
      <a-row :gutter="[16, 16]" class="metric-row">
        <a-col v-for="card in summaryCards" :key="card.key" :xs="24" :sm="12" :xl="6">
          <a-card :bordered="false" class="metric-card-shell">
            <div class="metric-card">
              <div class="metric-icon" :class="card.theme">
                <component :is="card.icon" />
              </div>
              <div class="metric-content">
                <div class="metric-label">{{ card.label }}</div>
                <div class="metric-value">
                  {{ card.value }}
                  <span v-if="card.suffix" class="metric-suffix">{{ card.suffix }}</span>
                </div>
                <div class="metric-hint">{{ card.hint }}</div>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>

      <a-row :gutter="[16, 16]">
        <a-col :xs="24" :xl="15">
          <a-card :bordered="false" class="module-card">
            <template #title>审核吞吐趋势</template>
            <v-chart :option="reviewTrendOption" autoresize class="chart-lg" />
          </a-card>
        </a-col>
        <a-col :xs="24" :xl="9">
          <a-card :bordered="false" class="module-card">
            <template #title>审核状态分布</template>
            <v-chart :option="statusDistributionOption" autoresize class="chart-md" />
            <div class="rule-panel">
              <div class="panel-title">高频命中规则</div>
              <div v-for="rule in dashboard.ruleHits" :key="rule.name" class="rule-row">
                <span class="rule-name">{{ rule.name }}</span>
                <a-tag :color="ruleTagColor(rule.level)">{{ rule.count }} 次</a-tag>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>

      <a-card :bordered="false" class="table-card">
        <template #title>待审核视频队列</template>
        <template #extra>
          <span class="table-extra">当前展示 {{ dashboard.queue.length }} 条近期待处理视频</span>
        </template>
        <a-table :data-source="dashboard.queue" :columns="queueColumns" :pagination="false" row-key="id">
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'riskLevel'">
              <a-tag :color="riskTagColor(record.riskLevel)">{{ riskLevelLabel(record.riskLevel) }}</a-tag>
            </template>
            <template v-else-if="column.key === 'status'">
              <a-tag :color="statusTagColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
            </template>
            <template v-else-if="column.key === 'hitRules'">
              <a-space wrap>
                <a-tag v-for="rule in record.hitRules" :key="rule" color="gold">{{ rule }}</a-tag>
              </a-space>
            </template>
            <template v-else-if="column.key === 'aiScore'">
              <span class="score-text">{{ record.aiScore }}</span>
            </template>
            <template v-else-if="column.key === 'action'">
              <a-space wrap>
                <a-button type="link" size="small" @click="openDetail(record)">查看建议</a-button>
                <a-button type="link" size="small" @click="handlePendingFeature('人工复核')">人工复核</a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>
    </a-spin>

    <a-drawer v-model:open="drawerVisible" title="AI审核详情" :width="460">
      <a-empty v-if="!activeVideo" description="请选择待审核视频" />
      <template v-else>
        <div class="drawer-head">
          <div class="drawer-title">{{ activeVideo.title }}</div>
          <a-space wrap>
            <a-tag :color="statusTagColor(activeVideo.status)">{{ statusLabel(activeVideo.status) }}</a-tag>
            <a-tag :color="riskTagColor(activeVideo.riskLevel)">{{ riskLevelLabel(activeVideo.riskLevel) }}</a-tag>
          </a-space>
        </div>

        <a-descriptions :column="1" size="small" bordered>
          <a-descriptions-item label="上传单位">{{ activeVideo.uploaderName }}</a-descriptions-item>
          <a-descriptions-item label="提交时间">{{ activeVideo.submittedAt }}</a-descriptions-item>
          <a-descriptions-item label="视频时长">{{ activeVideo.duration }}</a-descriptions-item>
          <a-descriptions-item label="AI 风险分">{{ activeVideo.aiScore }}</a-descriptions-item>
          <a-descriptions-item label="审核摘要">{{ activeVideo.summary }}</a-descriptions-item>
        </a-descriptions>

        <div class="drawer-section">
          <div class="drawer-section-title">命中规则</div>
          <a-space wrap>
            <a-tag v-for="rule in activeVideo.hitRules" :key="rule" color="orange">{{ rule }}</a-tag>
          </a-space>
        </div>

        <div class="drawer-section">
          <div class="drawer-section-title">AI 建议动作</div>
          <ul class="suggestion-list">
            <li v-for="item in activeVideo.recommendation" :key="item">{{ item }}</li>
          </ul>
        </div>
      </template>
    </a-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  SafetyCertificateOutlined,
  WarningOutlined,
} from '@ant-design/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { getCommunityAssistantDashboard } from '@/api/community'
import { COMMUNITY_ASSISTANT_TITLE, COMMUNITY_MANAGEMENT_TITLE } from '@/constants/navigationTitles'

use([CanvasRenderer, LineChart, PieChart, GridComponent, LegendComponent, TooltipComponent])

const loading = ref(false)
const drawerVisible = ref(false)
const activeVideo = ref(null)
const dashboard = ref({
  summary: {},
  reviewTrend: [],
  statusDistribution: [],
  ruleHits: [],
  queue: [],
})

const queueColumns = [
  { title: '视频标题', dataIndex: 'title', key: 'title' },
  { title: '上传单位', dataIndex: 'uploaderName', key: 'uploaderName', width: 170 },
  { title: '风险等级', dataIndex: 'riskLevel', key: 'riskLevel', width: 110 },
  { title: '审核状态', dataIndex: 'status', key: 'status', width: 120 },
  { title: '命中规则', dataIndex: 'hitRules', key: 'hitRules', width: 220 },
  { title: 'AI分数', dataIndex: 'aiScore', key: 'aiScore', width: 90 },
  { title: '操作', key: 'action', width: 150 },
]

const summaryCards = computed(() => [
  {
    key: 'pending',
    label: '待处理视频',
    value: dashboard.value.summary.pendingCount || 0,
    hint: '当前在 AI 审核链路中的视频数',
    icon: ClockCircleOutlined,
    theme: 'blue',
  },
  {
    key: 'manual',
    label: '待人工复核',
    value: dashboard.value.summary.manualReviewCount || 0,
    hint: 'AI 已识别为需人工复核',
    icon: SafetyCertificateOutlined,
    theme: 'gold',
  },
  {
    key: 'approved',
    label: '自动通过',
    value: dashboard.value.summary.autoApprovedCount || 0,
    hint: '本周期 AI 自动放行的视频',
    icon: CheckCircleOutlined,
    theme: 'green',
  },
  {
    key: 'risk',
    label: '高风险视频',
    value: dashboard.value.summary.highRiskCount || 0,
    hint: `平均审核 ${dashboard.value.summary.avgReviewMinutes || 0} 分钟`,
    icon: WarningOutlined,
    theme: 'red',
  },
])

const reviewTrendOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { top: 0 },
  grid: { top: 42, right: 20, bottom: 30, left: 44 },
  xAxis: {
    type: 'category',
    data: dashboard.value.reviewTrend.map((item) => item.date),
    boundaryGap: false,
  },
  yAxis: { type: 'value' },
  series: [
    {
      name: '完成审核',
      type: 'line',
      smooth: true,
      data: dashboard.value.reviewTrend.map((item) => item.reviewed),
      areaStyle: { opacity: 0.12 },
      itemStyle: { color: '#0f52ba' },
      lineStyle: { width: 3 },
    },
    {
      name: '拦截数量',
      type: 'line',
      smooth: true,
      data: dashboard.value.reviewTrend.map((item) => item.intercepted),
      itemStyle: { color: '#d4380d' },
      lineStyle: { width: 3 },
    },
  ],
}))

const statusDistributionOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [
    {
      type: 'pie',
      radius: ['42%', '68%'],
      center: ['50%', '42%'],
      label: { formatter: '{b}\n{c}' },
      data: dashboard.value.statusDistribution.map((item) => ({
        name: item.name,
        value: item.value,
      })),
    },
  ],
}))

function handlePendingFeature(label) {
  message.info(`${label}功能入口已预留，后续会并入社区助手或社区管理。`)
}

function riskLevelLabel(level) {
  const map = {
    low: '低风险',
    medium: '中风险',
    high: '高风险',
  }
  return map[level] || level || '-'
}

function riskTagColor(level) {
  const map = {
    low: 'blue',
    medium: 'gold',
    high: 'red',
  }
  return map[level] || 'default'
}

function statusLabel(status) {
  const map = {
    queued: '排队中',
    ai_reviewing: 'AI审核中',
    manual_review: '待人工复核',
    approved: '自动通过',
    rejected: '已拦截',
  }
  return map[status] || status || '-'
}

function statusTagColor(status) {
  const map = {
    queued: 'default',
    ai_reviewing: 'processing',
    manual_review: 'gold',
    approved: 'success',
    rejected: 'error',
  }
  return map[status] || 'default'
}

function ruleTagColor(level) {
  const map = {
    low: 'blue',
    medium: 'gold',
    high: 'red',
  }
  return map[level] || 'default'
}

function openDetail(record) {
  activeVideo.value = record
  drawerVisible.value = true
}

async function loadDashboard() {
  loading.value = true
  try {
    dashboard.value = await getCommunityAssistantDashboard()
  } catch (error) {
    message.error(error.message || '加载社区助手数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped>
.community-assistant-page {
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

.metric-row {
  margin-bottom: 16px;
}

.metric-card-shell,
.module-card,
.table-card {
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
  background: rgba(15, 82, 186, 0.12);
  color: #0f52ba;
}

.metric-icon.gold {
  background: rgba(217, 119, 6, 0.12);
  color: #d97706;
}

.metric-icon.green {
  background: rgba(22, 163, 74, 0.12);
  color: #15803d;
}

.metric-icon.red {
  background: rgba(220, 38, 38, 0.12);
  color: #dc2626;
}

.metric-content {
  min-width: 0;
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

.metric-suffix {
  margin-left: 4px;
  font-size: 14px;
  font-weight: 500;
  color: #8c8c8c;
}

.metric-hint {
  margin-top: 6px;
  font-size: 12px;
  color: #8c8c8c;
}

.chart-lg {
  height: 320px;
}

.chart-md {
  height: 250px;
}

.rule-panel {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.panel-title {
  margin-bottom: 10px;
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}

.rule-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.rule-row:last-child {
  margin-bottom: 0;
}

.rule-name {
  color: #475569;
}

.table-card {
  margin-top: 16px;
}

.table-extra {
  font-size: 12px;
  color: #8c8c8c;
}

.score-text {
  font-weight: 600;
  color: #0f52ba;
}

.drawer-head {
  margin-bottom: 16px;
}

.drawer-title {
  margin-bottom: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.drawer-section {
  margin-top: 20px;
}

.drawer-section-title {
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.suggestion-list {
  margin: 0;
  padding-left: 18px;
  color: #334155;
  line-height: 1.8;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }
}
</style>
