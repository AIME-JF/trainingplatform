<template>
  <div class="my-resources-page">
    <div class="page-header">
      <h2>我的资源</h2>
      <a-space>
        <a-button @click="$router.push('/resource/library')">资源库</a-button>
        <a-button type="primary" @click="$router.push('/resource/upload')">上传资源</a-button>
      </a-space>
    </div>

    <a-card :bordered="false" style="margin-bottom:16px">
      <a-space class="resource-filter-bar">
        <a-select v-model:value="query.status" class="resource-status-select" @change="fetchMine">
          <a-select-option value="">全部状态</a-select-option>
          <a-select-option value="draft">草稿</a-select-option>
          <a-select-option value="pending_review">待审核</a-select-option>
          <a-select-option value="reviewing">审核中</a-select-option>
          <a-select-option value="published">已发布</a-select-option>
          <a-select-option value="rejected">已驳回</a-select-option>
          <a-select-option value="offline">已下线</a-select-option>
        </a-select>
        <a-input-search v-model:value="query.search" class="resource-search-input" placeholder="搜索我的资源" @search="fetchMine" />
      </a-space>
    </a-card>

    <a-table :data-source="rows" :columns="columns" :pagination="false" row-key="id" :scroll="tableScroll">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
        </template>
        <template v-if="column.key === 'tags'">
          <a-space wrap>
            <a-tag v-for="tag in (record.tags || [])" :key="tag">{{ tag }}</a-tag>
          </a-space>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button size="small" @click="viewWorkflow(record)">轨迹</a-button>
            <a-button size="small" type="primary" ghost v-if="canSubmit(record)" @click="submitReview(record.id)">提交审核</a-button>
            <a-button size="small" v-if="canRepublish(record)" @click="publish(record.id)">重新发布</a-button>
            <a-button size="small" danger ghost v-if="record.status === 'published'" @click="offline(record.id)">下线</a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <div style="margin-top:16px; display:flex; justify-content:flex-end">
      <a-pagination
        :current="query.page"
        :page-size="query.size"
        :total="total"
        @change="onPageChange"
      />
    </div>

    <a-modal v-model:open="workflowVisible" title="审核轨迹" :footer="null">
      <a-empty v-if="!workflow || !workflow.tasks?.length" description="暂无审核记录" />
      <a-timeline v-else>
        <a-timeline-item v-for="task in workflow.tasks" :key="task.id">
          阶段 {{ task.stageOrder }} · {{ task.assigneeName || task.assigneeUserId }}
          <div>状态：{{ statusLabel(task.status) }}</div>
          <div v-if="task.comment">意见：{{ task.comment }}</div>
        </a-timeline-item>
      </a-timeline>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import { getResources, publishResource, offlineResource } from '@/api/resource'
import { submitResource, getReviewWorkflow } from '@/api/review'

const query = reactive({ page: 1, size: 10, search: '', status: '' })
const rows = ref([])
const total = ref(0)

const workflowVisible = ref(false)
const workflow = ref(null)
const isMobile = ref(window.innerWidth <= 768)

const columns = [
  { title: '标题', dataIndex: 'title', key: 'title' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 120 },
  { title: '类型', dataIndex: 'contentType', key: 'contentType', width: 120 },
  { title: '标签', dataIndex: 'tags', key: 'tags' },
  { title: '操作', key: 'action', width: 340 },
]

const tableScroll = ref(undefined)

function updateMobileState() {
  isMobile.value = window.innerWidth <= 768
  tableScroll.value = isMobile.value ? { x: 680 } : undefined
}

onMounted(() => {
  updateMobileState()
  window.addEventListener('resize', updateMobileState)
  fetchMine()
})

onUnmounted(() => {
  window.removeEventListener('resize', updateMobileState)
})

function statusLabel(status) {
  const map = {
    draft: '草稿', pendingReview: '待审核', pending_review: '待审核', reviewing: '审核中',
    published: '已发布', rejected: '已驳回', offline: '已下线',
    approved: '已通过', pending: '待处理'
  }
  return map[status] || status
}

function statusColor(status) {
  const map = {
    draft: 'default', pendingReview: 'gold', pending_review: 'gold', reviewing: 'blue',
    published: 'green', rejected: 'red', offline: 'orange'
  }
  return map[status] || 'default'
}

function canSubmit(record) {
  return ['draft', 'rejected'].includes(record.status)
}

function canRepublish(record) {
  return ['offline', 'rejected'].includes(record.status)
}

async function fetchMine() {
  try {
    const res = await getResources({ ...query, myOnly: true })
    rows.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    message.error(e.message || '加载失败')
  }
}

async function submitReview(id) {
  try {
    await submitResource(id)
    message.success('已提交审核')
    fetchMine()
  } catch (e) {
    message.error(e.message || '提交失败')
  }
}

async function publish(id) {
  try {
    await publishResource(id)
    message.success('发布成功')
    fetchMine()
  } catch (e) {
    message.error(e.message || '发布失败')
  }
}

async function offline(id) {
  try {
    await offlineResource(id)
    message.success('下线成功')
    fetchMine()
  } catch (e) {
    message.error(e.message || '下线失败')
  }
}

async function viewWorkflow(record) {
  try {
    workflow.value = await getReviewWorkflow(record.id)
    workflowVisible.value = true
  } catch {
    workflow.value = null
    workflowVisible.value = true
  }
}

function onPageChange(page, size) {
  query.page = page
  query.size = size
  fetchMine()
}
</script>

<style scoped>
.my-resources-page { padding: 0; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.resource-filter-bar {
  width: 100%;
}
.resource-status-select {
  width: 140px;
}
.resource-search-input {
  width: 280px;
}

@media (max-width: 768px) {
  .page-header {
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
  }
  .resource-filter-bar {
    display: flex;
    width: 100%;
    gap: 8px;
    flex-wrap: wrap;
  }
  .resource-status-select,
  .resource-search-input {
    width: 100%;
  }
}
</style>
