<template>
  <div class="page-content scenario-records-page">
    <div class="page-header">
      <a-button @click="router.push('/knowledge/scenarios')">返回</a-button>
      <h1 class="page-title">模拟记录</h1>
    </div>

    <a-card :bordered="false" class="content-card">
      <a-table
        :columns="columns"
        :data-source="records"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'score'">
            <a-progress
              :percent="record.score || 0"
              :stroke-color="getScoreColor(record.score || 0)"
              :show-info="true"
              size="small"
              style="width: 120px"
            />
          </template>
          <template v-if="column.key === 'duration'">
            {{ record.durationMinutes || 0 }} 分钟
          </template>
          <template v-if="column.key === 'status'">
            <a-badge :status="getStatusBadge(record.status)" :text="getStatusLabel(record.status)" />
          </template>
          <template v-if="column.key === 'actions'">
            <a @click="viewDetail(record.id)">查看详情</a>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTemplateScenarioSessions } from '@/api/knowledge'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const scenarioId = Number(route.params.id)

const pagination = reactive({ current: 1, pageSize: 20, total: 0 })

const columns = [
  { title: '学员', dataIndex: 'studentName', key: 'studentName' },
  { title: '状态', key: 'status', width: 120 },
  { title: '评分', key: 'score', width: 160 },
  { title: '用时', key: 'duration', width: 100 },
  { title: '模拟时间', dataIndex: 'createdAt', key: 'createdAt', width: 180 },
  { title: '操作', key: 'actions', width: 100 },
]

const records = ref<any[]>([])

onMounted(() => {
  void fetchRecords()
})

async function fetchRecords() {
  if (!Number.isFinite(scenarioId) || scenarioId <= 0) {
    records.value = []
    pagination.total = 0
    return
  }

  loading.value = true
  try {
    const data = await getTemplateScenarioSessions(scenarioId, {
      page: pagination.current,
      size: pagination.pageSize,
    })
    records.value = data.items || []
    pagination.total = data.total || 0
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag: { current?: number; pageSize?: number }) {
  pagination.current = pag.current || 1
  pagination.pageSize = pag.pageSize || 20
  void fetchRecords()
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

function viewDetail(recordId: number) {
  void router.push(`/knowledge/assistant/scenario-sim?sessionId=${recordId}&source=template-records&templateId=${scenarioId}`)
}
</script>

<style scoped>
.scenario-records-page {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.content-card {
  border-radius: var(--v2-radius-lg);
}
</style>
