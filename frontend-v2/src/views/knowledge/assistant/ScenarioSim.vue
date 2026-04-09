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
          <a-alert
            show-icon
            type="info"
            :message="historyBannerText"
          />
        </div>

        <div class="sim-info-bar">
          <div class="sim-scenario-name">
            <a-tag :color="getCategoryColor(activeScenario.category)">
              {{ getCategoryLabel(activeScenario.category) }}
            </a-tag>
            {{ activeScenario.title }}
          </div>
          <div class="sim-actions">
            <a-button v-if="simResult" size="small" @click="showResult = true">查看评估</a-button>
            <a-button v-if="!isHistorySession" danger size="small" @click="endScenario">结束模拟</a-button>
          </div>
        </div>

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
            :placeholder="isHistorySession ? '历史记录为只读模式' : '请输入你的回应...'"
            :disabled="isHistorySession"
            @pressEnter.prevent="handleSimEnter"
          />
          <a-button
            type="primary"
            :disabled="isHistorySession || !simInput.trim() || simGenerating"
            @click="sendSimMessage"
          >
            回应
          </a-button>
        </div>
      </div>
    </template>

    <a-modal v-model:open="showResult" title="模拟评估报告" :footer="null" width="600px">
      <div v-if="simResult" class="sim-result">
        <div class="result-score">
          <a-progress type="circle" :percent="simResult.score" :stroke-color="getScoreColor(simResult.score)" />
          <span class="result-score-label">综合评分</span>
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

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const avatarText = computed(() => (authStore.currentUser?.name || '').slice(0, 1))

const filterCategory = ref<string>()

interface Scenario {
  id: number
  title: string
  description: string
  category: string
  difficulty: number
  estimatedMinutes: number
  background: string
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
const loadingScenarios = ref(false)
const loadingHistory = ref(false)

const activeScenario = ref<Scenario | null>(null)
const activeSessionId = ref<number | null>(null)
const simMessages = ref<SimMessage[]>([])
const simInput = ref('')
const simGenerating = ref(false)
const simChatRef = ref<HTMLElement>()
const showResult = ref(false)
const simResult = ref<SimResult | null>(null)

const isHistorySession = computed(() => {
  const sessionId = Number(route.query.sessionId)
  return Number.isFinite(sessionId) && sessionId > 0
})

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
  loadingScenarios.value = true
  try {
    const res = await getAvailableScenarioTemplates({ category: filterCategory.value })
    scenarios.value = res.data || res || []
  } catch {
    scenarios.value = []
  } finally {
    loadingScenarios.value = false
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
    activeScenario.value = {
      id: detail.scenarioTemplateId,
      title: detail.scenarioTitle || '场景模拟',
      description: '',
      category: detail.category || 'law_enforcement',
      difficulty: 3,
      estimatedMinutes: detail.estimatedMinutes || 0,
      background: detail.background || '暂无场景背景',
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
  simResult.value = null
  try {
    const res = await startScenarioSession(scenario.id)
    const session = res.data || res
    activeSessionId.value = session.id
    simMessages.value = session.messages || []
  } catch {
    message.error('开始模拟失败')
    activeScenario.value = null
  }
}

function handleSimEnter(e: KeyboardEvent) {
  if (e.shiftKey || isHistorySession.value) return
  if (simInput.value.trim()) {
    void sendSimMessage()
  }
}

async function sendSimMessage() {
  const content = simInput.value.trim()
  if (!content || !activeSessionId.value || isHistorySession.value) return

  simMessages.value.push({ role: 'user', content })
  simInput.value = ''
  simGenerating.value = true

  await nextTick()
  scrollSimToBottom()

  try {
    const res = await sendScenarioMessage(activeSessionId.value, content)
    const data = res.data || res
    simMessages.value.push({
      role: 'npc',
      content: data.reply,
      npcName: data.npcName || '当事人',
    })
  } catch {
    simMessages.value.push({
      role: 'npc',
      content: 'AI 服务暂时不可用，请稍后再试。',
      npcName: '系统',
    })
  } finally {
    simGenerating.value = false
    await nextTick()
    scrollSimToBottom()
  }
}

async function endScenario() {
  if (!activeSessionId.value || isHistorySession.value) return
  try {
    const res = await endScenarioSession(activeSessionId.value)
    const data = res.data || res
    simResult.value = {
      score: data.score || 0,
      checkpoints: data.checkpointResults || [],
      feedback: data.feedback || '',
    }
    showResult.value = true
  } catch {
    message.error('获取评估结果失败')
  }
  activeScenario.value = null
  activeSessionId.value = null
  simMessages.value = []
}

function scrollSimToBottom() {
  if (simChatRef.value) {
    simChatRef.value.scrollTop = simChatRef.value.scrollHeight
  }
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

.sim-result {
  padding: 8px 0;
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

  .sim-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .sim-message-bubble {
    max-width: calc(100% - 42px);
  }
}
</style>
