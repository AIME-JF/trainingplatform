<template>
  <div class="page-content scenarios-page" :class="{ 'embedded-scenarios-page': embedded }">
    <div v-if="!embedded" class="page-header">
      <div>
        <h1 class="page-title">场景模板管理</h1>
        <p class="page-subtitle">创建和管理场景模拟模板，发布给学员进行训练。</p>
      </div>
      <a-button type="primary" @click="router.push('/knowledge/scenarios/create')">
        创建场景模板
      </a-button>
    </div>

    <div v-else class="embedded-toolbar">
      <a-button type="primary" @click="router.push('/knowledge/scenarios/create')">
        创建场景模板
      </a-button>
    </div>

    <a-card :bordered="false" class="filter-card">
      <div class="filter-toolbar">
        <a-select v-model:value="query.category" placeholder="场景分类" allow-clear class="filter-select" @change="fetchScenarios">
          <a-select-option value="law_enforcement">执法场景对话</a-select-option>
          <a-select-option value="record_taking">笔录模拟训练</a-select-option>
          <a-select-option value="law_application">法律适用推演</a-select-option>
        </a-select>
        <a-select v-model:value="query.status" placeholder="状态" allow-clear class="filter-select" @change="fetchScenarios">
          <a-select-option value="draft">草稿</a-select-option>
          <a-select-option value="published">已发布</a-select-option>
          <a-select-option value="archived">已归档</a-select-option>
        </a-select>
      </div>
    </a-card>

    <a-card :bordered="false" class="content-card">
      <a-table
        :columns="columns"
        :data-source="scenarios"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'category'">
            <a-tag :color="getCategoryColor(record.category)">
              {{ getCategoryLabel(record.category) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'difficulty'">
            <a-rate :value="record.difficulty" disabled :count="5" style="font-size: 12px" />
          </template>
          <template v-if="column.key === 'status'">
            <a-badge :status="getStatusBadge(record.status)" :text="getStatusLabel(record.status)" />
          </template>
          <template v-if="column.key === 'usageCount'">
            {{ record.usageCount }} 次
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a @click="router.push(`/knowledge/scenarios/${record.id}/edit`)">编辑</a>
              <a @click="router.push(`/knowledge/scenarios/${record.id}/records`)">模拟记录</a>
              <a-popconfirm
                v-if="record.status === 'draft'"
                title="确认发布该场景模板？"
                @confirm="publishScenario(record.id)"
              >
                <a style="color: var(--v2-primary)">发布</a>
              </a-popconfirm>
              <a-popconfirm title="确认删除？" @confirm="deleteScenario(record.id)">
                <a style="color: var(--v2-danger)">删除</a>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { getScenarioTemplates, publishScenarioTemplate, deleteScenarioTemplate } from '@/api/knowledge'

const props = withDefaults(defineProps<{
  embedded?: boolean
}>(), {
  embedded: false,
})

const router = useRouter()
const embedded = props.embedded
const loading = ref(false)

const query = reactive({
  category: undefined as string | undefined,
  status: undefined as string | undefined,
})

const pagination = reactive({ current: 1, pageSize: 20, total: 0 })

interface ScenarioTemplate {
  id: number
  title: string
  category: string
  difficulty: number
  status: string
  usageCount: number
  createdAt: string
}

const scenarios = ref<ScenarioTemplate[]>([])

const columns = [
  { title: '场景名称', dataIndex: 'title', key: 'title' },
  { title: '分类', key: 'category', width: 120 },
  { title: '难度', key: 'difficulty', width: 160 },
  { title: '状态', key: 'status', width: 100 },
  { title: '使用次数', key: 'usageCount', width: 100 },
  { title: '操作', key: 'actions', width: 240 },
]

onMounted(() => {
  void fetchScenarios()
})

async function fetchScenarios() {
  loading.value = true
  try {
    const data = await getScenarioTemplates({
      page: pagination.current,
      size: pagination.pageSize,
      category: query.category,
      status: query.status,
    })
    scenarios.value = data.items || []
    pagination.total = data.total || 0
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag: any) {
  pagination.current = pag.current
  void fetchScenarios()
}

function getCategoryLabel(category: string) {
  const map: Record<string, string> = { law_enforcement: '执法场景', record_taking: '笔录训练', law_application: '法律推演' }
  return map[category] || '未知'
}

function getCategoryColor(category: string) {
  const map: Record<string, string> = { law_enforcement: 'blue', record_taking: 'green', law_application: 'orange' }
  return map[category] || 'default'
}

function getStatusLabel(status: string) {
  const map: Record<string, string> = { draft: '草稿', published: '已发布', archived: '已归档' }
  return map[status] || status
}

function getStatusBadge(status: string) {
  const map: Record<string, string> = { draft: 'default', published: 'success', archived: 'warning' }
  return map[status] || 'default'
}

async function publishScenario(id: number) {
  try {
    await publishScenarioTemplate(id)
    message.success('发布成功')
    void fetchScenarios()
  } catch {
    message.error('发布失败')
  }
}

async function deleteScenario(id: number) {
  try {
    await deleteScenarioTemplate(id)
    message.success('删除成功')
    void fetchScenarios()
  } catch {
    message.error('删除失败')
  }
}
</script>

<style scoped>
.scenarios-page {
  max-width: 1200px;
  margin: 0 auto;
}

.embedded-scenarios-page {
  max-width: none;
  margin: 0 !important;
  margin-left: 0 !important;
  padding: 0 !important;
  min-height: auto !important;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.embedded-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
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

.filter-card {
  border-radius: var(--v2-radius-lg);
  margin-bottom: 16px;
}

.filter-toolbar {
  display: flex;
  gap: 12px;
}

.filter-select {
  min-width: 160px;
}

.content-card {
  border-radius: var(--v2-radius-lg);
}

@media (max-width: 768px) {
  .embedded-toolbar {
    justify-content: flex-start;
  }
}
</style>
