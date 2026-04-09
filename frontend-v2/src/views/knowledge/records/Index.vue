<template>
  <div class="page-content knowledge-records-page" :class="{ 'embedded-records-page': embedded }">
    <div v-if="!embedded" class="page-header">
      <h1 class="page-title">学习记录</h1>
      <p class="page-subtitle">查看知识问答和场景模拟的历史记录。</p>
    </div>

    <a-tabs v-model:activeKey="activeTab" class="records-tabs">
      <a-tab-pane key="chat" tab="问答记录">
        <a-card :bordered="false" class="content-card">
          <a-table
            :columns="chatColumns"
            :data-source="chatRecords"
            :loading="loadingChat"
            :pagination="chatPagination"
            row-key="id"
            @change="handleChatTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'mode'">
                <a-tag>{{ getModeLabel(record.mode) }}</a-tag>
              </template>
              <template v-if="column.key === 'actions'">
                <a @click="viewChatDetail(record.id)">查看对话</a>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>

      <a-tab-pane key="scenario" tab="场景模拟记录">
        <a-card :bordered="false" class="content-card">
          <a-table
            :columns="scenarioColumns"
            :data-source="scenarioRecords"
            :loading="loadingScenario"
            :pagination="scenarioPagination"
            row-key="id"
            @change="handleScenarioTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'score'">
                <a-progress
                  :percent="record.score || 0"
                  :stroke-color="getScoreColor(record.score || 0)"
                  size="small"
                  style="width: 120px"
                />
              </template>
              <template v-if="column.key === 'category'">
                <a-tag :color="getCategoryColor(record.category)">
                  {{ getCategoryLabel(record.category) }}
                </a-tag>
              </template>
              <template v-if="column.key === 'status'">
                <a-badge :status="getStatusBadge(record.status)" :text="getStatusLabel(record.status)" />
              </template>
              <template v-if="column.key === 'actions'">
                <a @click="viewScenarioDetail(record.id)">查看详情</a>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getChatSessions, getMyScenarioSessions } from '@/api/knowledge'

const props = withDefaults(defineProps<{
  embedded?: boolean
}>(), {
  embedded: false,
})

const router = useRouter()
const embedded = props.embedded
const activeTab = ref('chat')
const loadingChat = ref(false)
const loadingScenario = ref(false)

const chatPagination = reactive({ current: 1, pageSize: 20, total: 0 })
const scenarioPagination = reactive({ current: 1, pageSize: 20, total: 0 })

const chatColumns = [
  { title: '知识点范围', dataIndex: 'knowledgeSummary', key: 'knowledgeSummary' },
  { title: '模式', key: 'mode', width: 140 },
  { title: '对话轮数', dataIndex: 'messageCount', key: 'messageCount', width: 100 },
  { title: '时间', dataIndex: 'createdAt', key: 'createdAt', width: 180 },
  { title: '操作', key: 'actions', width: 100 },
]

const scenarioColumns = [
  { title: '场景名称', dataIndex: 'scenarioTitle', key: 'scenarioTitle' },
  { title: '分类', key: 'category', width: 120 },
  { title: '状态', key: 'status', width: 110 },
  { title: '评分', key: 'score', width: 160 },
  { title: '用时', dataIndex: 'durationMinutes', key: 'durationMinutes', width: 100 },
  { title: '时间', dataIndex: 'createdAt', key: 'createdAt', width: 180 },
  { title: '操作', key: 'actions', width: 100 },
]

const chatRecords = ref<any[]>([])
const scenarioRecords = ref<any[]>([])

onMounted(() => {
  void fetchChatRecords()
  void fetchScenarioRecords()
})

async function fetchChatRecords() {
  loadingChat.value = true
  try {
    const data = await getChatSessions({ page: chatPagination.current, size: chatPagination.pageSize })
    chatRecords.value = data.items || []
    chatPagination.total = data.total || 0
  } finally {
    loadingChat.value = false
  }
}

async function fetchScenarioRecords() {
  loadingScenario.value = true
  try {
    const data = await getMyScenarioSessions({ page: scenarioPagination.current, size: scenarioPagination.pageSize })
    scenarioRecords.value = data.items || []
    scenarioPagination.total = data.total || 0
  } finally {
    loadingScenario.value = false
  }
}

function handleChatTableChange(pag: { current?: number; pageSize?: number }) {
  chatPagination.current = pag.current || 1
  chatPagination.pageSize = pag.pageSize || 20
  void fetchChatRecords()
}

function handleScenarioTableChange(pag: { current?: number; pageSize?: number }) {
  scenarioPagination.current = pag.current || 1
  scenarioPagination.pageSize = pag.pageSize || 20
  void fetchScenarioRecords()
}

function getModeLabel(mode: string) {
  if (mode === 'case') {
    return '问答记录'
  }
  if (mode === 'qa') {
    return '知识问答'
  }
  return mode || '-'
}

function getCategoryLabel(category: string) {
  const map: Record<string, string> = {
    law_enforcement: '执法场景',
    record_taking: '笔录训练',
    law_application: '法律推演',
  }
  return map[category] || '未知'
}

function getCategoryColor(category: string) {
  const map: Record<string, string> = {
    law_enforcement: 'blue',
    record_taking: 'green',
    law_application: 'orange',
  }
  return map[category] || 'default'
}

function getStatusLabel(status: string) {
  const map: Record<string, string> = {
    in_progress: '进行中',
    completed: '已完成',
  }
  return map[status] || status || '未知'
}

function getStatusBadge(status: string) {
  const map: Record<string, string> = {
    in_progress: 'processing',
    completed: 'success',
  }
  return map[status] || 'default'
}

function getScoreColor(score: number) {
  if (score >= 80) return '#52c41a'
  if (score >= 60) return '#faad14'
  return '#ff4d4f'
}

function viewChatDetail(id: number) {
  if (embedded) {
    void router.push(`/knowledge/assistant?panel=qa&sessionId=${id}&source=records`)
    return
  }
  void router.push(`/knowledge/assistant/chat?sessionId=${id}&source=records`)
}

function viewScenarioDetail(id: number) {
  if (embedded) {
    void router.push(`/knowledge/assistant?panel=scenario&sessionId=${id}&source=records`)
    return
  }
  void router.push(`/knowledge/assistant/scenario-sim?sessionId=${id}&source=records`)
}
</script>

<style scoped>
.knowledge-records-page {
  max-width: 1100px;
  margin: 0 auto;
}

.embedded-records-page {
  max-width: none;
  margin: 0 !important;
  margin-left: 0 !important;
  padding: 0 !important;
  min-height: auto !important;
}

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 6px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--v2-text-muted);
  margin: 0;
}

.content-card {
  border-radius: var(--v2-radius-lg);
}
</style>
