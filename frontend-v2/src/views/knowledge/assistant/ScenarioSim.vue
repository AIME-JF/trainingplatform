<template>
  <div class="page-content scenario-sim-page">
    <div class="sim-header">
      <a-button @click="router.push(backTarget)">返回</a-button>
      <h1 class="sim-title">场景模拟训练</h1>
    </div>

    <div v-if="loadingHistory" class="loading-state">
      <a-spin />
    </div>

    <template v-else>
      <div v-if="!activeScenario" class="scenario-selection">
        <h2 class="section-title">选择训练场景</h2>

        <div class="scenario-filters">
          <a-select v-model:value="filterCategory" placeholder="场景分类" allow-clear class="filter-select">
            <a-select-option value="law_enforcement">执法场景对话</a-select-option>
            <a-select-option value="record_taking">笔录模拟训练</a-select-option>
            <a-select-option value="law_application">法律适用推演</a-select-option>
          </a-select>
        </div>

        <div class="scenario-grid">
          <a-card
            v-for="scenario in filteredScenarios"
            :key="scenario.id"
            hoverable
            class="scenario-card"
            @click="startScenario(scenario)"
          >
            <template #cover>
              <div class="scenario-card-cover" :class="scenario.category">
                <component :is="getCategoryIcon(scenario.category)" class="scenario-cover-icon" />
              </div>
            </template>
            <a-card-meta :title="scenario.title" :description="scenario.description" />
            <div class="scenario-card-meta">
              <a-tag :color="getDifficultyColor(scenario.difficulty)">
                {{ getDifficultyLabel(scenario.difficulty) }}
              </a-tag>
              <span class="scenario-duration">{{ scenario.estimatedMinutes }} 分钟</span>
            </div>
          </a-card>

          <a-empty v-if="!filteredScenarios.length" description="暂无可用训练场景" />
        </div>
      </div>

      <div v-else class="sim-active">
        <div v-if="isHistorySession" class="history-banner">
          <a-alert show-icon type="info" :message="historyBannerText" />
        </div>

        <div class="sim-info-bar">
          <div class="sim-scenario-name">
            <a-tag :color="getCategoryColor(activeScenario.category)">
              {{ getCategoryLabel(activeScenario.category) }}
            </a-tag>
            {{ activeScenario.title }}
          </div>
          <div class="sim-actions">
            <a-button size="small" @click="hintDrawerOpen = true">查看提示</a-button>
            <a-button v-if="simResult" size="small" @click="showResult = true">查看评估</a-button>
            <a-button
              v-if="!isHistorySession && !isSessionCompleted"
              danger
              size="small"
              :loading="endingScenario"
              @click="endScenario"
            >
              结束并评估
            </a-button>
          </div>
        </div>

        <div
          v-if="sessionGuideVisible"
          class="sim-guide-card"
          :class="{ 'sim-guide-card-ready': hasReachedRecommendedRounds }"
        >
          <div class="sim-guide-stats">
            <div class="guide-stat">
              <span class="guide-stat-label">预计时长</span>
              <strong class="guide-stat-value">{{ estimatedDurationText }}</strong>
            </div>
            <div class="guide-stat">
              <span class="guide-stat-label">已对话轮次</span>
              <strong class="guide-stat-value">{{ conversationRounds }}</strong>
            </div>
            <div class="guide-stat">
              <span class="guide-stat-label">考察要点</span>
              <strong class="guide-stat-value">{{ checkpointCount }}</strong>
            </div>
            <div class="guide-stat">
              <span class="guide-stat-label">建议轮次</span>
              <strong class="guide-stat-value">{{ recommendedRoundsText }}</strong>
            </div>
          </div>
          <div class="sim-guide-tip">{{ sessionGuideText }}</div>
          <div v-if="checkpointLabels.length" class="sim-checkpoints">
            <span class="sim-checkpoints-label">本次重点：</span>
            <a-tag v-for="label in checkpointLabels" :key="label" class="sim-checkpoint-tag">
              {{ label }}
            </a-tag>
          </div>
        </div>

        <a-alert
          v-if="endingScenario"
          class="report-generating-alert"
          type="info"
          show-icon
          message="报告生成中，当前会话已锁定，请稍候..."
        />

        <div class="sim-background">
          <strong>场景背景：</strong>{{ activeScenario.background }}
        </div>

        <div class="sim-chat-body" ref="simChatRef">
          <div v-for="(msg, idx) in simMessages" :key="idx" class="sim-message" :class="msg.role">
            <div class="sim-message-avatar">
              <a-avatar v-if="msg.role === 'user'" :size="32">{{ avatarText }}</a-avatar>
              <a-avatar v-else-if="msg.role === 'npc'" :size="32" style="background: #faad14">
                {{ msg.npcName?.slice(0, 1) || 'NPC' }}
              </a-avatar>
              <a-avatar v-else :size="32" style="background: var(--v2-primary)">AI</a-avatar>
            </div>
            <div class="sim-message-bubble" :class="msg.role">
              <div class="sim-message-sender" v-if="msg.role === 'npc'">{{ msg.npcName }}</div>
              <div class="sim-message-content">{{ msg.content }}</div>
            </div>
          </div>

          <div v-if="simGenerating" class="sim-message npc">
            <div class="sim-message-avatar">
              <a-avatar :size="32" style="background: #faad14">...</a-avatar>
            </div>
            <div class="sim-message-bubble npc">
              <a-spin size="small" />
              <span class="generating-text">对方正在回复...</span>
            </div>
          </div>
        </div>

        <div class="sim-input-bar">
          <a-textarea
            v-model:value="simInput"
            class="sim-input"
            :auto-size="{ minRows: 1, maxRows: 3 }"
            :placeholder="inputPlaceholder"
            :disabled="isSessionReadonly"
            @pressEnter.prevent="handleSimEnter"
          />
          <a-button
            type="primary"
            :disabled="isSessionReadonly || !simInput.trim() || simGenerating"
            @click="sendSimMessage"
          >
            回应
          </a-button>
        </div>
      </div>
    </template>

    <a-drawer
      v-model:open="hintDrawerOpen"
      title="模拟提示"
      placement="right"
      width="420"
      class="scenario-hint-drawer"
    >
      <div class="hint-section">
        <h4>当前阶段提示</h4>
        <p>{{ phaseHintText }}</p>
      </div>

      <div class="hint-section">
        <h4>场景背景摘要</h4>
        <p>{{ backgroundSummary }}</p>
      </div>

      <div class="hint-section">
        <h4>考察要点</h4>
        <div v-if="checkpointLabels.length" class="hint-tags">
          <a-tag v-for="label in checkpointLabels" :key="label">{{ label }}</a-tag>
        </div>
        <a-empty v-else description="当前场景未配置考察要点" />
      </div>

      <div class="hint-section">
        <h4>关联知识点/资料</h4>
        <div v-if="knowledgeItemTitles.length" class="hint-tags">
          <a-tag v-for="title in knowledgeItemTitles" :key="title" color="blue">{{ title }}</a-tag>
        </div>
        <a-empty v-else description="当前场景未关联知识点或资料" />
      </div>
    </a-drawer>

    <a-modal v-model:open="showResult" title="模拟评估报告" :footer="null" width="760px">
      <div v-if="endingScenario" class="report-loading-state">
        <a-spin size="large" />
        <p class="report-loading-title">报告生成中</p>
        <p class="report-loading-desc">正在根据本次对话生成评估结果，请稍候...</p>
      </div>

      <div v-else-if="simResult" class="sim-result">
        <div class="result-hero">
          <div class="result-score">
            <a-progress type="circle" :percent="simResult.score" :stroke-color="getScoreColor(simResult.score)" />
            <span class="result-score-label">综合评分</span>
          </div>

          <div class="result-summary">
            <div class="summary-metric">
              <span class="summary-label">通过要点</span>
              <strong class="summary-value">{{ passedCheckpointCount }}</strong>
            </div>
            <div class="summary-metric">
              <span class="summary-label">待加强要点</span>
              <strong class="summary-value">{{ pendingCheckpointCount }}</strong>
            </div>
            <div class="summary-metric">
              <span class="summary-label">完成率</span>
              <strong class="summary-value">{{ completionRate }}%</strong>
            </div>
          </div>
        </div>

        <div v-if="showRadarChart" class="result-radar-card">
          <h4>能力覆盖雷达图</h4>
          <div class="radar-chart-wrap">
            <svg viewBox="0 0 320 320" class="radar-chart">
              <polygon
                v-for="(polygon, idx) in radarGridPolygons"
                :key="`grid-${idx}`"
                :points="polygon"
                class="radar-grid"
              />
              <line
                v-for="(line, idx) in radarAxisLines"
                :key="`axis-${idx}`"
                :x1="RADAR_CENTER"
                :y1="RADAR_CENTER"
                :x2="line.x"
                :y2="line.y"
                class="radar-axis"
              />
              <polygon :points="radarDataPolygon" class="radar-data" />
              <circle
                v-for="(point, idx) in radarDataPoints"
                :key="`point-${idx}`"
                :cx="point.x"
                :cy="point.y"
                r="4"
                class="radar-point"
              />
              <text
                v-for="(label, idx) in radarLabelPoints"
                :key="`label-${idx}`"
                :x="label.x"
                :y="label.y"
                class="radar-label"
                text-anchor="middle"
              >
                {{ label.label }}
              </text>
            </svg>
          </div>
        </div>

        <a-divider />

        <div class="result-details">
          <h4>评估要点</h4>
          <div v-for="(item, idx) in simResult.checkpoints" :key="idx" class="result-checkpoint">
            <CheckCircleOutlined v-if="item.passed" style="color: #52c41a" />
            <CloseCircleOutlined v-else style="color: #ff4d4f" />
            <span>{{ item.label }}</span>
          </div>
        </div>

        <a-divider />

        <div class="result-feedback">
          <h4>AI 反馈</h4>
          <p>{{ simResult.feedback }}</p>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  MessageOutlined,
  FormOutlined,
  AuditOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import {
  endScenarioSession,
  getAvailableScenarioTemplates,
  getScenarioSession,
  sendScenarioMessage,
  startScenarioSession,
} from '@/api/knowledge'

const RADAR_CENTER = 160
const RADAR_RADIUS = 98
const RADAR_LABEL_RADIUS = 126
const RADAR_GRID_LEVELS = [0.25, 0.5, 0.75, 1]

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const avatarText = computed(() => (authStore.currentUser?.name || '').slice(0, 1))

const filterCategory = ref<string>()

interface ScenarioCheckpoint {
  label: string
  score?: number
}

interface Scenario {
  id: number
  title: string
  description: string
  category: string
  difficulty: number
  estimatedMinutes: number
  background: string
  checkpoints?: ScenarioCheckpoint[]
  knowledgeItemTitles?: string[]
}

interface SimMessage {
  role: 'user' | 'npc' | 'system'
  content: string
  npcName?: string
}

interface SimResult {
  score: number
  checkpoints: { label: string; passed: boolean }[]
  feedback: string
}

const scenarios = ref<Scenario[]>([])
const loadingHistory = ref(false)

const activeScenario = ref<Scenario | null>(null)
const activeSessionId = ref<number | null>(null)
const simMessages = ref<SimMessage[]>([])
const simInput = ref('')
const simGenerating = ref(false)
const endingScenario = ref(false)
const hintDrawerOpen = ref(false)
const sessionStatus = ref<'in_progress' | 'completed'>('in_progress')
const simChatRef = ref<HTMLElement>()
const showResult = ref(false)
const simResult = ref<SimResult | null>(null)

const isHistorySession = computed(() => {
  const sessionId = Number(route.query.sessionId)
  return Number.isFinite(sessionId) && sessionId > 0
})

const isSessionCompleted = computed(() => sessionStatus.value === 'completed')
const isSessionReadonly = computed(() => isHistorySession.value || endingScenario.value || isSessionCompleted.value)

const backTarget = computed(() => {
  if (route.query.source === 'template-records' && route.query.templateId) {
    return `/knowledge/scenarios/${route.query.templateId}/records`
  }
  if (route.query.source === 'records') {
    return '/knowledge/records'
  }
  return '/knowledge/assistant'
})

const historyBannerText = computed(() => {
  if (!activeScenario.value || !activeSessionId.value) {
    return '正在查看历史模拟记录'
  }
  if (simResult.value) {
    return `正在查看历史模拟记录 #${activeSessionId.value}，可查看完整对话与评估结果。`
  }
  return `正在查看历史模拟记录 #${activeSessionId.value}，该记录尚未生成评估结果。`
})

const checkpointLabels = computed(() =>
  (activeScenario.value?.checkpoints || [])
    .map((item) => String(item.label || '').trim())
    .filter(Boolean),
)

const checkpointCount = computed(() => checkpointLabels.value.length)

const conversationRounds = computed(() => (
  simMessages.value.filter((item) => item.role === 'user').length
))

const estimatedDurationText = computed(() => {
  const minutes = activeScenario.value?.estimatedMinutes || 0
  return minutes > 0 ? `${minutes} 分钟` : '未设置'
})

const estimatedRoundTarget = computed(() => {
  const minutes = activeScenario.value?.estimatedMinutes || 0
  return minutes > 0 ? Math.ceil(minutes / 3) : 0
})

const checkpointRoundTarget = computed(() => (
  checkpointCount.value > 0 ? checkpointCount.value * 2 : 0
))

const recommendedRounds = computed(() => Math.max(checkpointRoundTarget.value, estimatedRoundTarget.value))

const recommendedRoundsText = computed(() => (
  recommendedRounds.value > 0 ? `${recommendedRounds.value} 轮` : '未设置'
))

const hasReachedRecommendedRounds = computed(() => (
  !isHistorySession.value
  && recommendedRounds.value > 0
  && conversationRounds.value >= recommendedRounds.value
))

const sessionGuideVisible = computed(() => !!activeScenario.value)

const sessionGuideText = computed(() => {
  if (isHistorySession.value) {
    return '当前为历史记录查看模式，可回看完整对话和评估结果。'
  }
  if (hasReachedRecommendedRounds.value) {
    return `当前已达到建议轮次（${recommendedRounds.value} 轮），如果主要考察要点已经覆盖，可以直接点击“结束并评估”。`
  }
  if (!checkpointCount.value) {
    return '当前场景未配置考察要点。建议完成关键问答后，点击“结束并评估”获取结果。'
  }
  return `当前已进行 ${conversationRounds.value} 轮，建议轮次为 ${recommendedRounds.value} 轮；当你认为主要考察要点已经覆盖后，就可以点击“结束并评估”。`
})

const knowledgeItemTitles = computed(() => activeScenario.value?.knowledgeItemTitles || [])

const backgroundSummary = computed(() => (
  summarizeText(activeScenario.value?.background || '暂无场景背景')
))

const phaseHintText = computed(() => {
  if (endingScenario.value) {
    return '系统正在生成评估报告，当前会话已锁定，请耐心等待。'
  }
  if (isHistorySession.value) {
    return '当前为历史记录，可结合评估结果回看自己在关键环节中的应对表现。'
  }
  if (!checkpointCount.value) {
    return '先围绕场景背景完成关键问答，确认主要处理步骤后即可结束并评估。'
  }
  if (hasReachedRecommendedRounds.value) {
    return '建议轮次已达标，优先检查考察要点是否都已覆盖；若已覆盖，可以结束并评估。'
  }
  return `当前优先围绕考察要点展开对话，建议至少完成 ${recommendedRounds.value} 轮，再决定是否结束并评估。`
})

const inputPlaceholder = computed(() => {
  if (isHistorySession.value) {
    return '历史记录为只读模式'
  }
  if (endingScenario.value) {
    return '报告生成中，暂不可继续对话'
  }
  if (isSessionCompleted.value) {
    return '当前场景已完成评估，不能继续对话'
  }
  return '请输入你的回应...'
})

const passedCheckpointCount = computed(() => (
  (simResult.value?.checkpoints || []).filter((item) => item.passed).length
))

const pendingCheckpointCount = computed(() => (
  Math.max((simResult.value?.checkpoints || []).length - passedCheckpointCount.value, 0)
))

const completionRate = computed(() => {
  const total = simResult.value?.checkpoints?.length || 0
  if (!total) {
    return simResult.value?.score || 0
  }
  return Math.round((passedCheckpointCount.value / total) * 100)
})

const radarMetrics = computed(() =>
  (simResult.value?.checkpoints || []).map((item) => ({
    label: truncateLabel(item.label),
    value: item.passed ? 100 : 35,
  })),
)

const showRadarChart = computed(() => radarMetrics.value.length >= 3)

const radarGridPolygons = computed(() =>
  RADAR_GRID_LEVELS.map((level) => buildRadarPolygon(radarMetrics.value.map((_, index, array) => {
    const point = toRadarPoint(index, array.length, level * RADAR_RADIUS)
    return `${point.x},${point.y}`
  }))),
)

const radarAxisLines = computed(() =>
  radarMetrics.value.map((_, index, array) => toRadarPoint(index, array.length, RADAR_RADIUS)),
)

const radarLabelPoints = computed(() =>
  radarMetrics.value.map((item, index, array) => ({
    ...toRadarPoint(index, array.length, RADAR_LABEL_RADIUS),
    label: item.label,
  })),
)

const radarDataPoints = computed(() =>
  radarMetrics.value.map((item, index, array) => toRadarPoint(index, array.length, (item.value / 100) * RADAR_RADIUS)),
)

const radarDataPolygon = computed(() =>
  buildRadarPolygon(radarDataPoints.value.map((point) => `${point.x},${point.y}`)),
)

onMounted(() => {
  if (isHistorySession.value) {
    void loadScenarioSession(Number(route.query.sessionId))
    return
  }
  void fetchScenarios()
})

watch(filterCategory, () => {
  if (!isHistorySession.value) {
    void fetchScenarios()
  }
})

watch(
  () => route.query.sessionId,
  (value) => {
    const sessionId = Number(value)
    if (Number.isFinite(sessionId) && sessionId > 0) {
      void loadScenarioSession(sessionId)
      return
    }
    if (!activeScenario.value) {
      void fetchScenarios()
    }
  },
)

async function fetchScenarios() {
  try {
    const data = await getAvailableScenarioTemplates({ category: filterCategory.value })
    scenarios.value = data || []
  } catch {
    scenarios.value = []
  }
}

async function loadScenarioSession(sessionId: number) {
  if (!Number.isFinite(sessionId) || sessionId <= 0) {
    return
  }
  loadingHistory.value = true
  try {
    const detail = await getScenarioSession(sessionId)
    activeSessionId.value = detail.id
    sessionStatus.value = detail.status === 'completed' ? 'completed' : 'in_progress'
    activeScenario.value = {
      id: detail.scenarioTemplateId,
      title: detail.scenarioTitle || '场景模拟',
      description: '',
      category: detail.category || 'law_enforcement',
      difficulty: 3,
      estimatedMinutes: detail.estimatedMinutes || 0,
      background: detail.background || '暂无场景背景',
      checkpoints: detail.checkpoints || [],
      knowledgeItemTitles: detail.knowledgeItemTitles || [],
    }
    simMessages.value = detail.messages || []
    simResult.value = detail.status === 'completed'
      ? {
          score: detail.score || 0,
          checkpoints: detail.checkpointResults || [],
          feedback: detail.feedback || '',
        }
      : null
    await nextTick()
    scrollSimToBottom()
  } catch (error) {
    activeScenario.value = null
    activeSessionId.value = null
    sessionStatus.value = 'in_progress'
    simMessages.value = []
    simResult.value = null
    message.error(error instanceof Error ? error.message : '加载模拟记录失败')
  } finally {
    loadingHistory.value = false
  }
}

const filteredScenarios = computed(() => scenarios.value)

function getCategoryIcon(category: string) {
  switch (category) {
    case 'law_enforcement':
      return MessageOutlined
    case 'record_taking':
      return FormOutlined
    case 'law_application':
      return AuditOutlined
    default:
      return MessageOutlined
  }
}

function getCategoryLabel(category: string) {
  switch (category) {
    case 'law_enforcement':
      return '执法场景'
    case 'record_taking':
      return '笔录训练'
    case 'law_application':
      return '法律推演'
    default:
      return '未知'
  }
}

function getCategoryColor(category: string) {
  switch (category) {
    case 'law_enforcement':
      return 'blue'
    case 'record_taking':
      return 'green'
    case 'law_application':
      return 'orange'
    default:
      return 'default'
  }
}

function getDifficultyLabel(level: number) {
  const labels = ['', '入门', '基础', '进阶', '高级', '专家']
  return labels[level] || '未知'
}

function getDifficultyColor(level: number) {
  const colors = ['', 'green', 'blue', 'orange', 'red', 'purple']
  return colors[level] || 'default'
}

function getScoreColor(score: number) {
  if (score >= 80) return '#52c41a'
  if (score >= 60) return '#faad14'
  return '#ff4d4f'
}

async function startScenario(scenario: Scenario) {
  activeScenario.value = scenario
  activeSessionId.value = null
  sessionStatus.value = 'in_progress'
  simResult.value = null
  simMessages.value = []
  hintDrawerOpen.value = false
  showResult.value = false

  try {
    const session = await startScenarioSession(scenario.id)
    activeSessionId.value = session.id
    sessionStatus.value = session.status === 'completed' ? 'completed' : 'in_progress'
    simMessages.value = session.messages || []
    if (activeScenario.value) {
      activeScenario.value = {
        ...activeScenario.value,
        checkpoints: session.checkpoints || activeScenario.value.checkpoints || [],
        estimatedMinutes: session.estimatedMinutes || activeScenario.value.estimatedMinutes,
        background: session.background || activeScenario.value.background,
        knowledgeItemTitles: session.knowledgeItemTitles || activeScenario.value.knowledgeItemTitles || [],
      }
    }
  } catch (error) {
    message.error(error instanceof Error ? error.message : '开始模拟失败')
    activeScenario.value = null
  }
}

function handleSimEnter(e: KeyboardEvent) {
  if (e.shiftKey || isSessionReadonly.value) return
  if (simInput.value.trim()) {
    void sendSimMessage()
  }
}

async function sendSimMessage() {
  const content = simInput.value.trim()
  if (!content || !activeSessionId.value || isSessionReadonly.value) return

  simMessages.value.push({ role: 'user', content })
  simInput.value = ''
  simGenerating.value = true

  await nextTick()
  scrollSimToBottom()

  try {
    const data = await sendScenarioMessage(activeSessionId.value, content)
    simMessages.value.push({
      role: 'npc',
      content: data.reply,
      npcName: data.npcName || '当事人',
    })
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : '发送消息失败'
    simMessages.value.push({
      role: 'npc',
      content: errorMessage,
      npcName: '系统',
    })
    message.error(errorMessage)
  } finally {
    simGenerating.value = false
    await nextTick()
    scrollSimToBottom()
  }
}

async function endScenario() {
  if (!activeSessionId.value || isSessionReadonly.value) return

  endingScenario.value = true
  hintDrawerOpen.value = false
  showResult.value = true

  try {
    const data = await endScenarioSession(activeSessionId.value)
    sessionStatus.value = 'completed'
    simResult.value = {
      score: data.score || 0,
      checkpoints: data.checkpointResults || [],
      feedback: data.feedback || '',
    }
  } catch (error) {
    showResult.value = false
    message.error(error instanceof Error ? error.message : '获取评估结果失败')
  } finally {
    endingScenario.value = false
  }
}

function scrollSimToBottom() {
  if (simChatRef.value) {
    simChatRef.value.scrollTop = simChatRef.value.scrollHeight
  }
}

function summarizeText(content: string, maxLength = 96) {
  const normalized = String(content || '').replace(/\s+/g, ' ').trim()
  if (!normalized) {
    return '暂无背景摘要'
  }
  return normalized.length > maxLength ? `${normalized.slice(0, maxLength)}...` : normalized
}

function truncateLabel(label: string, maxLength = 6) {
  const normalized = String(label || '').trim()
  if (!normalized) {
    return '未命名'
  }
  return normalized.length > maxLength ? `${normalized.slice(0, maxLength)}…` : normalized
}

function toRadarPoint(index: number, total: number, radius: number) {
  const safeTotal = Math.max(total, 3)
  const angle = (Math.PI * 2 * index) / safeTotal - Math.PI / 2
  return {
    x: Number((RADAR_CENTER + Math.cos(angle) * radius).toFixed(2)),
    y: Number((RADAR_CENTER + Math.sin(angle) * radius).toFixed(2)),
  }
}

function buildRadarPolygon(points: string[]) {
  return points.join(' ')
}
</script>

<style scoped>
.scenario-sim-page {
  max-width: 1000px;
  margin: 0 auto;
}

.sim-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.sim-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.loading-state {
  min-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px;
}

.scenario-filters {
  margin-bottom: 16px;
}

.filter-select {
  min-width: 160px;
}

.scenario-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.scenario-card {
  border-radius: var(--v2-radius-lg);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.scenario-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--v2-shadow-lg);
}

.scenario-card-cover {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 72px;
  font-size: 28px;
  color: #fff;
}

.scenario-card-cover.law_enforcement {
  background: linear-gradient(135deg, #1890ff, #096dd9);
}

.scenario-card-cover.record_taking {
  background: linear-gradient(135deg, #52c41a, #389e0d);
}

.scenario-card-cover.law_application {
  background: linear-gradient(135deg, #faad14, #d48806);
}

.scenario-card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.scenario-duration {
  font-size: 12px;
  color: var(--v2-text-muted);
}

.sim-active {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 160px);
}

.history-banner {
  margin-bottom: 12px;
}

.sim-info-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(229, 229, 234, 0.6);
  border-radius: var(--v2-radius-lg);
  margin-bottom: 12px;
}

.sim-scenario-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.sim-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sim-guide-card {
  padding: 14px 16px;
  background: rgba(82, 196, 26, 0.06);
  border: 1px solid rgba(82, 196, 26, 0.18);
  border-radius: var(--v2-radius-lg);
  margin-bottom: 12px;
}

.sim-guide-card-ready {
  background: rgba(250, 173, 20, 0.1);
  border-color: rgba(250, 173, 20, 0.28);
}

.sim-guide-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 10px;
}

.guide-stat {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.guide-stat-label {
  font-size: 12px;
  color: var(--v2-text-muted);
}

.guide-stat-value {
  font-size: 16px;
  color: var(--v2-text-primary);
}

.sim-guide-tip {
  font-size: 13px;
  line-height: 1.6;
  color: var(--v2-text-secondary);
}

.sim-checkpoints {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.sim-checkpoints-label {
  font-size: 12px;
  color: var(--v2-text-muted);
}

.sim-checkpoint-tag {
  margin-inline-end: 0;
}

.report-generating-alert {
  margin-bottom: 12px;
}

.sim-background {
  padding: 12px 16px;
  background: rgba(24, 144, 255, 0.06);
  border: 1px solid rgba(24, 144, 255, 0.15);
  border-radius: var(--v2-radius-lg);
  font-size: 13px;
  line-height: 1.6;
  color: var(--v2-text-secondary);
  margin-bottom: 12px;
  flex-shrink: 0;
}

.sim-chat-body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 12px 0;
}

.sim-message {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.sim-message.user {
  flex-direction: row-reverse;
}

.sim-message.system {
  justify-content: center;
}

.sim-message.system .sim-message-bubble {
  background: rgba(0, 0, 0, 0.04);
  color: var(--v2-text-muted);
  font-size: 13px;
  text-align: center;
  border-radius: 12px;
  max-width: 90%;
}

.sim-message-bubble {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.6;
}

.sim-message-bubble.user {
  background: var(--v2-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.sim-message-bubble.npc {
  background: #fff7e6;
  border: 1px solid #ffe7ba;
  border-bottom-left-radius: 4px;
}

.sim-message-sender {
  font-size: 12px;
  font-weight: 600;
  color: #d48806;
  margin-bottom: 4px;
}

.generating-text {
  margin-left: 8px;
  color: var(--v2-text-muted);
}

.sim-input-bar {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 12px 0;
  border-top: 1px solid rgba(229, 229, 234, 0.6);
  flex-shrink: 0;
}

.sim-input {
  flex: 1;
  border-radius: 12px !important;
}

.hint-section + .hint-section {
  margin-top: 24px;
}

.hint-section h4 {
  margin: 0 0 10px;
  font-size: 15px;
}

.hint-section p {
  margin: 0;
  line-height: 1.7;
  color: var(--v2-text-secondary);
}

.hint-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.report-loading-state {
  min-height: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.report-loading-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.report-loading-desc {
  margin: 0;
  color: var(--v2-text-muted);
}

.sim-result {
  padding: 8px 0;
}

.result-hero {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 20px;
  align-items: center;
}

.result-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.result-score-label {
  font-size: 14px;
  color: var(--v2-text-muted);
}

.result-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.summary-metric {
  padding: 14px;
  border-radius: 16px;
  background: rgba(24, 144, 255, 0.06);
  border: 1px solid rgba(24, 144, 255, 0.12);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-label {
  font-size: 12px;
  color: var(--v2-text-muted);
}

.summary-value {
  font-size: 24px;
  color: var(--v2-text-primary);
}

.result-radar-card {
  margin-top: 24px;
  padding: 18px;
  border-radius: var(--v2-radius-lg);
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(229, 229, 234, 0.6);
}

.result-radar-card h4 {
  margin: 0 0 14px;
  font-size: 15px;
}

.radar-chart-wrap {
  display: flex;
  justify-content: center;
}

.radar-chart {
  width: 320px;
  height: 320px;
}

.radar-grid {
  fill: rgba(24, 144, 255, 0.04);
  stroke: rgba(24, 144, 255, 0.12);
  stroke-width: 1;
}

.radar-axis {
  stroke: rgba(24, 144, 255, 0.14);
  stroke-width: 1;
}

.radar-data {
  fill: rgba(24, 144, 255, 0.2);
  stroke: rgba(24, 144, 255, 0.88);
  stroke-width: 2;
}

.radar-point {
  fill: #1890ff;
}

.radar-label {
  fill: var(--v2-text-secondary);
  font-size: 12px;
}

.result-details h4,
.result-feedback h4 {
  font-size: 15px;
  margin-bottom: 12px;
}

.result-checkpoint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.result-feedback p {
  color: var(--v2-text-secondary);
  line-height: 1.7;
  margin: 0;
}

@media (max-width: 768px) {
  .sim-active {
    height: calc(100vh - 140px);
  }

  .sim-info-bar {
    align-items: flex-start;
    flex-direction: column;
    gap: 8px;
  }

  .sim-guide-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .sim-actions {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: wrap;
  }

  .sim-message-bubble {
    max-width: calc(100% - 42px);
  }

  .result-hero {
    grid-template-columns: 1fr;
  }

  .result-summary {
    grid-template-columns: 1fr;
  }

  .radar-chart {
    width: 100%;
    height: auto;
  }
}
</style>
