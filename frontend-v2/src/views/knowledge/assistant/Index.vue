<template>
  <div class="page-content knowledge-assistant-workbench">
    <div class="assistant-workbench-layout">
      <aside class="assistant-workbench-sidebar">
        <AssistantWorkbenchNav
          :groups="workbenchGroups"
          :active-key="activePanel"
          @select="selectPanel"
        />
      </aside>

      <section class="assistant-workbench-main">
        <div class="assistant-main-header">
          <div class="assistant-main-copy">
            <span class="assistant-main-badge">{{ activeGroupTitle }}</span>
            <h2>{{ activeItem.title }}</h2>
            <p>{{ activeItem.description }}</p>
          </div>
        </div>

        <div class="assistant-main-surface">
          <component :is="activeComponent" embedded />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AssistantWorkbenchNav from '@/components/knowledge/assistant/AssistantWorkbenchNav.vue'
import {
  getAssistantWorkbenchGroups,
  getAssistantWorkbenchItem,
  isAssistantPanelKey,
  type AssistantPanelKey,
} from '@/components/knowledge/assistant/assistantWorkbench'
import { useAuthStore } from '@/stores/auth'
import RecordsView from '../records/Index.vue'
import TeachingResourceGenerationTaskView from '../TeachingResourceGenerationTask.vue'
import ScenarioTemplatesView from '../scenarios/Index.vue'
import ChatView from './Chat.vue'
import ScenarioSimView from './ScenarioSim.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const panelComponentMap = {
  qa: ChatView,
  scenario: ScenarioSimView,
  generate: TeachingResourceGenerationTaskView,
  records: RecordsView,
  templates: ScenarioTemplatesView,
} satisfies Record<AssistantPanelKey, unknown>

const isAdmin = computed(() => authStore.role === 'admin' || authStore.roleCodes.includes('admin'))
const isInstructor = computed(() => authStore.role === 'instructor' || authStore.roleCodes.includes('instructor'))
const isStudent = computed(() => authStore.role === 'student' || authStore.roleCodes.includes('student'))

const workbenchGroups = computed(() => getAssistantWorkbenchGroups({
  isAdmin: isAdmin.value,
  isInstructor: isInstructor.value,
  isStudent: isStudent.value,
}))

const availableKeys = computed(() => workbenchGroups.value.flatMap((group) => group.items.map((item) => item.key)))

const rawPanel = computed(() => String(route.query.panel || 'qa'))

const activePanel = computed<AssistantPanelKey>(() => {
  if (isAssistantPanelKey(rawPanel.value) && availableKeys.value.includes(rawPanel.value)) {
    return rawPanel.value
  }
  return availableKeys.value[0] || 'qa'
})

const activeItem = computed(() => getAssistantWorkbenchItem(activePanel.value))
const activeGroupTitle = computed(() => (
  workbenchGroups.value.find((group) => group.items.some((item) => item.key === activePanel.value))?.title || '智能训练'
))
const activeComponent = computed(() => panelComponentMap[activePanel.value])

watch(
  [availableKeys, rawPanel],
  () => {
    if (!availableKeys.value.length) {
      return
    }
    if (activePanel.value === rawPanel.value) {
      return
    }
    void router.replace({
      path: '/knowledge/assistant',
      query: buildPanelQuery(activePanel.value, true),
    })
  },
  { immediate: true },
)

function selectPanel(key: AssistantPanelKey) {
  if (key === activePanel.value) {
    return
  }
  void router.replace({
    path: '/knowledge/assistant',
    query: buildPanelQuery(key, false),
  })
}

function buildPanelQuery(key: AssistantPanelKey, keepExistingState: boolean) {
  const nextQuery: Record<string, string> = { panel: key }
  const current = route.query

  if ((keepExistingState || activePanel.value === 'qa') && key === 'qa') {
    copyStringQuery(current, nextQuery, ['sessionId', 'knowledgeItemIds', 'mode', 'source'])
  }

  if ((keepExistingState || activePanel.value === 'scenario') && key === 'scenario') {
    copyStringQuery(current, nextQuery, ['sessionId', 'source', 'templateId'])
    if (route.params.scenarioId) {
      nextQuery.scenarioId = String(route.params.scenarioId)
    }
  }

  if ((keepExistingState || activePanel.value === 'records') && key === 'records') {
    copyStringQuery(current, nextQuery, ['tab'])
  }

  return nextQuery
}

function copyStringQuery(
  source: Record<string, unknown>,
  target: Record<string, string>,
  keys: string[],
) {
  keys.forEach((key) => {
    const value = source[key]
    if (Array.isArray(value)) {
      target[key] = value.join(',')
      return
    }
    if (value !== undefined && value !== null && value !== '') {
      target[key] = String(value)
    }
  })
}
</script>

<style scoped>
.knowledge-assistant-workbench {
  display: flex;
  flex-direction: column;
  gap: 0;
  background:
    radial-gradient(circle at top right, rgba(75, 110, 245, 0.1), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.82) 0%, rgba(245, 246, 250, 0.94) 100%);
}

.assistant-workbench-layout {
  display: grid;
  grid-template-columns: minmax(260px, 300px) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
  padding-top: 4px;
}

.assistant-workbench-sidebar,
.assistant-workbench-main {
  min-width: 0;
}

.assistant-workbench-sidebar {
  position: sticky;
  top: 20px;
  padding: 18px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.74);
  box-shadow: 0 16px 34px rgba(48, 71, 122, 0.08);
  backdrop-filter: blur(18px);
}

.assistant-workbench-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.assistant-main-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 22px 24px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.76);
  box-shadow: 0 16px 34px rgba(48, 71, 122, 0.08);
  backdrop-filter: blur(18px);
}

.assistant-main-copy {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.assistant-main-badge {
  display: inline-flex;
  width: fit-content;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(75, 110, 245, 0.1);
  color: var(--v2-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.assistant-main-copy h2 {
  margin: 0;
  font-size: 28px;
  line-height: 1.15;
  color: #12234d;
}

.assistant-main-copy p {
  margin: 0;
  color: #6f7b99;
  font-size: 14px;
  line-height: 1.8;
}

.assistant-main-surface {
  min-height: 780px;
  padding: 22px 24px 24px;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 18px 36px rgba(48, 71, 122, 0.08);
  backdrop-filter: blur(18px);
}

@media (max-width: 1200px) {
  .assistant-workbench-layout {
    grid-template-columns: 1fr;
  }

  .assistant-workbench-sidebar {
    position: static;
  }
}

@media (max-width: 768px) {
  .knowledge-assistant-workbench {
    gap: 0;
  }

  .assistant-main-header,
  .assistant-main-surface {
    padding: 18px;
    border-radius: 24px;
  }

  .assistant-main-header {
    flex-direction: column;
  }

  .assistant-main-copy h2 {
    font-size: 24px;
  }

  .assistant-main-surface {
    min-height: auto;
  }
}
</style>
