<template>
  <div class="page-content knowledge-review-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">知识审核</h1>
        <p class="page-subtitle">审核用户提交的知识内容，支持AI辅助审核。</p>
      </div>
    </div>

    <a-card :bordered="false" class="filter-card">
      <div class="filter-toolbar">
        <a-select v-model:value="query.status" placeholder="审核状态" allow-clear class="filter-select" @change="fetchList">
          <a-select-option value="pending_review">待审核</a-select-option>
          <a-select-option value="reviewing">审核中</a-select-option>
          <a-select-option value="published">已通过</a-select-option>
          <a-select-option value="rejected">已驳回</a-select-option>
        </a-select>
        <a-input-search
          v-model:value="query.search"
          placeholder="搜索知识标题"
          class="search-input"
          allow-clear
          @search="fetchList"
        />
      </div>
    </a-card>

    <a-card :bordered="false" class="content-card">
      <a-table
        :columns="columns"
        :data-source="items"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-badge :status="getStatusBadge(record.status)" :text="getStatusLabel(record.status)" />
          </template>
          <template v-if="column.key === 'aiResult'">
            <a-tag v-if="record.aiResult === 'pass'" color="green">AI通过</a-tag>
            <a-tag v-else-if="record.aiResult === 'reject'" color="red">AI驳回</a-tag>
            <a-tag v-else-if="record.aiResult === 'uncertain'" color="orange">AI不确定</a-tag>
            <span v-else class="text-muted">未审核</span>
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a @click="viewDetail(record.id)">查看</a>
              <a-popconfirm
                v-if="record.status === 'pending_review' || record.status === 'reviewing'"
                title="确认通过审核？"
                @confirm="approveItem(record.id)"
              >
                <a style="color: #52c41a">通过</a>
              </a-popconfirm>
              <a
                v-if="record.status === 'pending_review' || record.status === 'reviewing'"
                style="color: var(--v2-danger)"
                @click="rejectItem(record.id)"
              >
                驳回
              </a>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'

const loading = ref(false)
const query = reactive({ status: undefined as string | undefined, search: '' })
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })

const columns = [
  { title: '知识标题', dataIndex: 'title', key: 'title' },
  { title: '提交人', dataIndex: 'submitter', key: 'submitter', width: 120 },
  { title: '状态', key: 'status', width: 100 },
  { title: 'AI审核', key: 'aiResult', width: 120 },
  { title: '提交时间', dataIndex: 'submittedAt', key: 'submittedAt', width: 180 },
  { title: '操作', key: 'actions', width: 180 },
]

const items = ref<any[]>([])

onMounted(() => {
  void fetchList()
})

async function fetchList() {
  loading.value = true
  try {
    // TODO: 对接后端审核列表接口
    items.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag: any) {
  pagination.current = pag.current
  void fetchList()
}

function getStatusLabel(status: string) {
  const map: Record<string, string> = { pending_review: '待审核', reviewing: '审核中', published: '已通过', rejected: '已驳回' }
  return map[status] || status
}

function getStatusBadge(status: string) {
  const map: Record<string, string> = { pending_review: 'warning', reviewing: 'processing', published: 'success', rejected: 'error' }
  return map[status] || 'default'
}

function viewDetail(id: number) {
  // TODO: 查看详情
}

async function approveItem(id: number) {
  // TODO: 对接后端通过审核接口
  message.success('审核通过')
  void fetchList()
}

function rejectItem(id: number) {
  // TODO: 弹窗输入驳回原因，对接后端驳回接口
}
</script>

<style scoped>
.knowledge-review-page {
  max-width: 1200px;
  margin: 0 auto;
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

.filter-card {
  border-radius: var(--v2-radius-lg);
  margin-bottom: 16px;
}

.filter-toolbar {
  display: flex;
  gap: 12px;
}

.filter-select {
  min-width: 140px;
}

.search-input {
  max-width: 280px;
}

.content-card {
  border-radius: var(--v2-radius-lg);
}

.text-muted {
  color: var(--v2-text-muted);
  font-size: 13px;
}
</style>
