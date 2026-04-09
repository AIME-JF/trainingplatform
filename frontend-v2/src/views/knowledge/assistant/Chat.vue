<template>
  <KnowledgeCardModal
    v-model:open="saveModalOpen"
    :folder-options="folderOptions"
    :initial-title="saveDraft.title"
    :initial-content="saveDraft.contentHtml"
    @success="handleSaveSuccess"
  />

  <div class="page-content knowledge-chat-page">
    <div class="chat-header">
      <a-button @click="router.push(backTarget)">返回</a-button>
      <h1 class="chat-title">{{ pageTitle }}</h1>
    </div>

    <div class="chat-toolbar">
      <KnowledgeItemSelector
        v-model="selectedKnowledgeItemIds"
        placeholder="可多选知识点或资料，不选择则为通识问答"
      />
      <div class="toolbar-hint">
        {{ selectedKnowledgeItemIds.length ? `已选择 ${selectedKnowledgeItemIds.length} 个知识点/资料` : '当前为通识问答' }}
      </div>
    </div>

    <a-alert
      v-if="knowledgeWarning"
      class="knowledge-warning"
      type="warning"
      show-icon
      :message="knowledgeWarning"
    />

    <div ref="chatBodyRef" class="chat-body">
      <div v-if="!messages.length" class="chat-welcome">
        <div class="welcome-icon">
          <RobotOutlined />
        </div>
        <h2>{{ welcomeTitle }}</h2>
        <p>{{ welcomeDesc }}</p>
        <div class="quick-prompts">
          <a-tag
            v-for="(prompt, idx) in quickPrompts"
            :key="idx"
            class="quick-prompt-tag"
            @click="sendMessage(prompt)"
          >
            {{ prompt }}
          </a-tag>
        </div>
      </div>

      <div v-for="(msg, idx) in messages" :key="idx" class="chat-message" :class="msg.role">
        <div class="message-avatar">
          <a-avatar v-if="msg.role === 'user'" :size="32">{{ avatarText }}</a-avatar>
          <a-avatar v-else :size="32" style="background: var(--v2-primary)">AI</a-avatar>
        </div>
        <div class="message-bubble">
          <div class="message-content" v-html="msg.content" />
          <div class="message-footer">
            <span class="message-time">{{ msg.time }}</span>
            <a-button
              v-if="isCaseMode && msg.role === 'assistant'"
              type="link"
              size="small"
              class="save-result-btn"
              @click="openSaveResult(msg, idx)"
            >
              保存结果
            </a-button>
          </div>
        </div>
      </div>

      <div v-if="generating" class="chat-message assistant">
        <div class="message-avatar">
          <a-avatar :size="32" style="background: var(--v2-primary)">AI</a-avatar>
        </div>
        <div class="message-bubble">
          <a-spin size="small" />
          <span class="generating-text">正在思考中...</span>
        </div>
      </div>
    </div>

    <div class="chat-input-bar">
      <a-textarea
        v-model:value="inputText"
        class="chat-input"
        :auto-size="{ minRows: 1, maxRows: 4 }"
        placeholder="输入你的问题..."
        @pressEnter.prevent="handleEnter"
      />
      <a-button
        type="primary"
        class="send-btn"
        :disabled="!inputText.trim() || generating || loadingSession"
        @click="sendMessage(inputText)"
      >
        发送
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { RobotOutlined } from '@ant-design/icons-vue'
import { createChatSession, getChatSession, sendChatMessage } from '@/api/knowledge'
import { listLibraryFolders, type LibraryFolderResponse } from '@/api/library'
import KnowledgeCardModal from '@/components/library/KnowledgeCardModal.vue'
import KnowledgeItemSelector from '@/components/library/KnowledgeItemSelector.vue'
import { useAuthStore } from '@/stores/auth'
import { flattenLibraryFolders } from '@/utils/library-browser'
import {
  getAssistantModeMeta,
  getKnowledgeChatModeLabel,
  isAssistantMode,
  type AssistantMode,
} from './modeConfig'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  time: string
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const generating = ref(false)
const loadingSession = ref(false)
const chatBodyRef = ref<HTMLElement>()
const sessionId = ref<number | null>(null)
const selectedKnowledgeItemIds = ref<number[]>([])
const knowledgeWarning = ref('')
const libraryFolders = ref<LibraryFolderResponse[]>([])
const saveModalOpen = ref(false)
const saveDraft = ref({
  title: '',
  contentHtml: '',
})
const syncingRoute = ref(false)
const suppressSelectionWatcher = ref(true)
const restoringSession = ref(false)

const avatarText = computed(() => (authStore.currentUser?.name || '').slice(0, 1))
const rawMode = computed(() => String(route.query.mode || 'qa'))
const mode = computed<AssistantMode>(() => (isAssistantMode(rawMode.value) ? rawMode.value : 'qa'))
const modeMeta = computed(() => getAssistantModeMeta(mode.value))
const isCaseMode = computed(() => mode.value === 'case')
const backTarget = computed(() => (route.query.source === 'records' ? '/knowledge/records' : '/knowledge/assistant'))

const folderOptions = computed(() => flattenLibraryFolders(libraryFolders.value))
const pageTitle = computed(() => (isCaseMode.value ? '知识问答' : modeMeta.value.pageTitle))
const welcomeTitle = computed(() => (isCaseMode.value ? '知识问答助手' : modeMeta.value.welcomeTitle))
const welcomeDesc = computed(() => (
  isCaseMode.value
    ? '可直接发起通识问答；若选择知识点，我会优先基于这些知识点回答。'
    : modeMeta.value.welcomeDesc
))
const quickPrompts = computed(() => (
  isCaseMode.value
    ? [
        '什么情况下可以使用警械？',
        '治安调解的适用条件有哪些？',
        '询问未成年人有哪些特殊规定？',
      ]
    : modeMeta.value.quickPrompts
))

watch(
  rawMode,
  (nextMode) => {
    if (nextMode === 'generate') {
      if (route.query.sessionId) {
        return
      }
      void router.replace('/knowledge/teaching-generate')
      return
    }
    if (nextMode && !isAssistantMode(nextMode) && nextMode !== 'qa') {
      const nextQuery = { ...route.query }
      delete nextQuery.mode
      void router.replace({ path: route.path, query: nextQuery })
    }
  },
  { immediate: true },
)

watch(
  () => route.query.knowledgeItemIds,
  (value) => {
    if (syncingRoute.value || route.query.sessionId) {
      return
    }
    suppressSelectionWatcher.value = true
    selectedKnowledgeItemIds.value = parseKnowledgeItemIds(value)
    suppressSelectionWatcher.value = false
  },
  { immediate: true },
)

watch(
  selectedKnowledgeItemIds,
  (value) => {
    if (suppressSelectionWatcher.value || restoringSession.value) {
      return
    }
    if (route.query.sessionId) {
      resetConversation()
      void router.replace({
        path: '/knowledge/assistant/chat',
        query: {
          ...(route.query.source ? { source: String(route.query.source) } : {}),
          ...(mode.value !== 'qa' ? { mode: mode.value } : {}),
          ...(value.length ? { knowledgeItemIds: value.join(',') } : {}),
        },
      })
      return
    }
    void syncSelectionToRoute(value)
    resetConversation()
  },
  { deep: true },
)

watch(
  () => route.query.sessionId,
  (value) => {
    if (value) {
      void loadSession(Number(value))
      return
    }
    sessionId.value = null
  },
  { immediate: true },
)

onMounted(() => {
  suppressSelectionWatcher.value = false
})

async function loadSession(rawSessionId: number) {
  if (!Number.isFinite(rawSessionId) || rawSessionId <= 0) {
    return
  }
  loadingSession.value = true
  restoringSession.value = true
  try {
    const detail = await getChatSession(rawSessionId)
    suppressSelectionWatcher.value = true
    selectedKnowledgeItemIds.value = detail.knowledgeItemIds || []
    suppressSelectionWatcher.value = false
    sessionId.value = detail.id
    messages.value = (detail.messages || []).map((item: { role: string; content: string }) => ({
      role: item.role === 'user' ? 'user' : 'assistant',
      content: item.content || '',
      time: '',
    }))
    knowledgeWarning.value = ''
    if (detail.mode && detail.mode !== rawMode.value && (detail.mode === 'qa' || isAssistantMode(detail.mode))) {
      syncingRoute.value = true
      await router.replace({
        path: '/knowledge/assistant/chat',
        query: {
          sessionId: String(rawSessionId),
          ...(route.query.source ? { source: String(route.query.source) } : {}),
          ...(detail.mode !== 'qa' ? { mode: detail.mode } : {}),
        },
      })
      syncingRoute.value = false
    }
    await nextTick()
    scrollToBottom()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载会话失败')
  } finally {
    restoringSession.value = false
    loadingSession.value = false
  }
}

async function syncSelectionToRoute(value: number[]) {
  syncingRoute.value = true
  await router.replace({
    path: '/knowledge/assistant/chat',
    query: {
      ...(route.query.source ? { source: String(route.query.source) } : {}),
      ...(mode.value !== 'qa' ? { mode: mode.value } : {}),
      ...(value.length ? { knowledgeItemIds: value.join(',') } : {}),
    },
  })
  syncingRoute.value = false
}

function handleEnter(e: KeyboardEvent) {
  if (e.shiftKey) return
  if (inputText.value.trim()) {
    void sendMessage(inputText.value)
  }
}

async function sendMessage(text: string) {
  const content = text.trim()
  if (!content) return

  const now = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  messages.value.push({ role: 'user', content, time: now })
  inputText.value = ''
  generating.value = true

  await nextTick()
  scrollToBottom()

  try {
    if (!sessionId.value) {
      const createRes = await createChatSession({
        knowledge_item_ids: selectedKnowledgeItemIds.value,
        mode: mode.value,
      })
      sessionId.value = createRes.id
    }

    const currentSessionId = sessionId.value
    if (!currentSessionId) {
      throw new Error('创建会话失败')
    }

    const res = await sendChatMessage(currentSessionId, content)
    const replyTime = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    messages.value.push({
      role: 'assistant',
      content: res.reply || '',
      time: replyTime,
    })
    knowledgeWarning.value = selectedKnowledgeItemIds.value.length && res.knowledgeMatched === false
      ? '当前问题与所选知识点未直接匹配，建议更换关键词、调整知识点，或清空后改为通识问答。'
      : ''
  } catch (error) {
    const replyTime = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    const errorMessage = error instanceof Error ? error.message : '发送消息失败'
    messages.value.push({
      role: 'assistant',
      content: `<p>${escapeHtml(errorMessage)}</p>`,
      time: replyTime,
    })
    message.error(errorMessage)
  } finally {
    generating.value = false
    await nextTick()
    scrollToBottom()
  }
}

async function openSaveResult(messageItem: ChatMessage, index: number) {
  try {
    if (!libraryFolders.value.length) {
      libraryFolders.value = await listLibraryFolders()
    }
    saveDraft.value = {
      title: buildDefaultResultTitle(index),
      contentHtml: buildKnowledgeContentHtml(messageItem.content),
    }
    saveModalOpen.value = true
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载知识库文件夹失败')
  }
}

function handleSaveSuccess() {
  saveModalOpen.value = false
}

function resetConversation() {
  messages.value = []
  sessionId.value = null
  knowledgeWarning.value = ''
}

function scrollToBottom() {
  if (chatBodyRef.value) {
    chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
  }
}

function parseKnowledgeItemIds(value: unknown) {
  const raw = Array.isArray(value) ? value.join(',') : String(value || '')
  return raw
    .split(',')
    .map((item) => Number(item.trim()))
    .filter((item) => Number.isFinite(item) && item > 0)
}

function buildDefaultResultTitle(messageIndex: number) {
  const previousUserMessage = [...messages.value.slice(0, messageIndex)]
    .reverse()
    .find((item) => item.role === 'user')
  const base = stripHtml(previousUserMessage?.content || '').replace(/\s+/g, ' ').trim()
  const fallback = isCaseMode.value ? '问答记录' : getKnowledgeChatModeLabel(mode.value)
  return base ? `${fallback}-${base.slice(0, 24)}` : `${fallback}-保存结果`
}

function buildKnowledgeContentHtml(content: string) {
  const normalized = String(content || '').replace(/\r\n?/g, '\n').trim()
  if (!normalized) {
    return '<p>暂无内容</p>'
  }
  if (/<[a-z][\s\S]*>/i.test(normalized)) {
    return normalized
  }
  return normalized
    .split(/\n{2,}/)
    .map((block) => `<p>${escapeHtml(block).replace(/\n/g, '<br>')}</p>`)
    .join('')
}

function stripHtml(content: string) {
  return String(content || '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/gi, ' ')
    .trim()
}

function escapeHtml(content: string) {
  return content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}
</script>

<style scoped>
.knowledge-chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 900px;
  margin: 0 auto;
  padding-bottom: 0 !important;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(229, 229, 234, 0.6);
  flex-shrink: 0;
}

.chat-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.chat-toolbar {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 16px;
}

.toolbar-hint {
  font-size: 13px;
  color: var(--v2-text-muted);
}

.knowledge-warning {
  margin-top: 16px;
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chat-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.welcome-icon {
  font-size: 48px;
  color: var(--v2-primary);
  margin-bottom: 16px;
}

.chat-welcome h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 8px;
}

.chat-welcome p {
  font-size: 14px;
  color: var(--v2-text-muted);
  margin: 0 0 24px;
  max-width: 420px;
}

.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.quick-prompt-tag {
  cursor: pointer;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  transition: all 0.2s;
}

.quick-prompt-tag:hover {
  color: var(--v2-primary);
  border-color: var(--v2-primary);
}

.chat-message {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.chat-message.user {
  flex-direction: row-reverse;
}

.message-bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  position: relative;
}

.chat-message.user .message-bubble {
  background: var(--v2-primary);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.chat-message.assistant .message-bubble {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(229, 229, 234, 0.6);
  border-bottom-left-radius: 4px;
}

.message-content :deep(p) {
  margin: 0 0 8px;
}

.message-content :deep(p:last-child) {
  margin: 0;
}

.message-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 6px;
}

.chat-message.user .message-footer {
  justify-content: flex-end;
}

.message-time {
  font-size: 11px;
  color: rgba(0, 0, 0, 0.3);
}

.chat-message.user .message-time {
  color: rgba(255, 255, 255, 0.6);
  text-align: right;
}

.save-result-btn {
  padding: 0;
  height: auto;
}

.generating-text {
  margin-left: 8px;
  color: var(--v2-text-muted);
}

.chat-input-bar {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 16px 0;
  border-top: 1px solid rgba(229, 229, 234, 0.6);
  flex-shrink: 0;
}

.chat-input {
  flex: 1;
  border-radius: 12px !important;
}

.send-btn {
  border-radius: 12px;
  height: 40px;
  min-width: 72px;
}

@media (max-width: 768px) {
  .knowledge-chat-page {
    height: calc(100vh - var(--v2-bottomnav-height));
  }

  .message-bubble {
    max-width: 85%;
  }
}
</style>
