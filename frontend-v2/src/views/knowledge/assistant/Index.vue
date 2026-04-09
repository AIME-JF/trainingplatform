<template>
  <div class="page-content knowledge-assistant-page">
    <div class="page-header">
      <h1 class="page-title">知识助手</h1>
      <p class="page-subtitle">从知识库中选择知识点或可解析资料后发起定向问答；不选择时则进入通识问答。</p>
    </div>

    <section class="assistant-section selector-section">
      <h2 class="section-title">选择知识点或资料</h2>
      <a-card class="selector-card" :bordered="false">
        <KnowledgeItemSelector
          v-model="selectedKnowledgeItemIds"
          placeholder="可多选知识点或可解析资料，不选择则为通识问答"
        />
        <div class="selector-summary">
          <span>{{ selectedKnowledgeItemIds.length ? `已选择 ${selectedKnowledgeItemIds.length} 个知识点/资料` : '当前未选择知识点或资料，将进入通识问答' }}</span>
          <a-space>
            <a-button @click="clearSelection">清空选择</a-button>
            <a-button type="primary" @click="enterQaChat">开始问答</a-button>
          </a-space>
        </div>
      </a-card>
    </section>

    <section class="assistant-section">
      <h2 class="section-title">智能功能</h2>
      <div class="feature-grid">
        <div class="feature-card" @click="enterQaChat">
          <MessageOutlined class="feature-icon" />
          <div class="feature-info">
            <h3>知识问答</h3>
            <p>围绕已选知识点或资料进行问答；不选择时自动切换为通识问答。</p>
          </div>
        </div>

        <div v-if="isInstructor || isAdmin" class="feature-card" @click="router.push('/knowledge/teaching-generate')">
          <FileTextOutlined class="feature-icon" />
          <div class="feature-info">
            <h3>教案/课件生成</h3>
            <p>进入教学资源生成任务页，支持任务管理、预览和保存结果。</p>
          </div>
        </div>

        <div class="feature-card" @click="router.push('/knowledge/assistant/scenario-sim')">
          <TeamOutlined class="feature-icon" />
          <div class="feature-info">
            <h3>场景模拟训练</h3>
            <p>进行执法场景模拟、笔录训练等实战演练。</p>
          </div>
        </div>

        <div v-if="isInstructor || isAdmin" class="feature-card" @click="router.push('/knowledge/scenarios')">
          <SettingOutlined class="feature-icon" />
          <div class="feature-info">
            <h3>场景模板管理</h3>
            <p>创建和管理场景模板，可关联知识点或资料作为模拟依据。</p>
          </div>
        </div>

        <div class="feature-card" @click="router.push('/knowledge/records')">
          <HistoryOutlined class="feature-icon" />
          <div class="feature-info">
            <h3>学习记录</h3>
            <p>查看知识问答和场景模拟的历史记录。</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  MessageOutlined,
  FileTextOutlined,
  TeamOutlined,
  SettingOutlined,
  HistoryOutlined,
} from '@ant-design/icons-vue'
import KnowledgeItemSelector from '@/components/library/KnowledgeItemSelector.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const selectedKnowledgeItemIds = ref<number[]>([])

const isAdmin = computed(() => authStore.role === 'admin' || authStore.roleCodes.includes('admin'))
const isInstructor = computed(() => authStore.role === 'instructor' || authStore.roleCodes.includes('instructor'))

function clearSelection() {
  selectedKnowledgeItemIds.value = []
}

function enterQaChat() {
  void router.push({
    path: '/knowledge/assistant/chat',
    query: buildKnowledgeItemQuery(),
  })
}

function buildKnowledgeItemQuery() {
  return selectedKnowledgeItemIds.value.length
    ? { knowledgeItemIds: selectedKnowledgeItemIds.value.join(',') }
    : {}
}
</script>

<style scoped>
.knowledge-assistant-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--v2-text-primary);
  margin: 0 0 8px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--v2-text-muted);
  margin: 0;
}

.assistant-section {
  margin-bottom: 40px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin: 0 0 20px;
}

.selector-card {
  border-radius: var(--v2-radius-lg);
}

.selector-summary {
  margin-top: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  color: var(--v2-text-secondary);
  flex-wrap: wrap;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.feature-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(229, 229, 234, 0.6);
  border-radius: var(--v2-radius-lg);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.feature-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--v2-shadow-lg);
  border-color: var(--v2-primary);
}

.feature-icon {
  flex-shrink: 0;
  font-size: 28px;
  color: var(--v2-primary);
  margin-top: 2px;
}

.feature-info h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin: 0 0 6px;
}

.feature-info p {
  font-size: 13px;
  color: var(--v2-text-muted);
  margin: 0;
  line-height: 1.5;
}
</style>
