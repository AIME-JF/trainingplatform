<template>
  <div class="review-history-page">
    <div class="page-header">
      <h2>审核记录</h2>
    </div>

    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-space wrap>
        <a-select v-model:value="filters.businessType" allow-clear placeholder="业务类型" style="width: 140px" @change="fetchWorkflows">
          <a-select-option value="resource">资源审核</a-select-option>
          <a-select-option value="training">培训审核</a-select-option>
          <a-select-option value="exam">考试审核</a-select-option>
        </a-select>
        <a-select v-model:value="filters.status" allow-clear placeholder="审核状态" style="width: 140px" @change="fetchWorkflows">
          <a-select-option value="pending">待审核</a-select-option>
          <a-select-option value="reviewing">审核中</a-select-option>
          <a-select-option value="approved">已通过</a-select-option>
          <a-select-option value="rejected">已驳回</a-select-option>
        </a-select>
        <a-input-search
          v-model:value="filters.search"
          placeholder="搜索资源名称"
          allow-clear
          style="width: 220px"
          @search="fetchWorkflows"
        />
      </a-space>
    </a-card>

    <a-card :bordered="false">
      <a-table
        :data-source="workflows"
        :columns="columns"
        :pagination="pagination"
        row-key="id"
        :loading="loading"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'businessType'">
            <a-tag :color="businessTypeColor[record.businessType]">{{ businessTypeLabel[record.businessType] || record.businessType }}</a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColor[record.status]">{{ statusLabel[record.status] || record.status }}</a-tag>
          </template>
          <template v-if="column.key === 'stage'">
            {{ record.currentStage }} / {{ record.totalStages || '?' }}
          </template>
          <template v-if="column.key === 'startedAt'">
            {{ formatTime(record.startedAt) }}
          </template>
          <template v-if="column.key === 'finishedAt'">
            {{ record.finishedAt ? formatTime(record.finishedAt) : '-' }}
          </template>
          <template v-if="column.key === 'action'">
            <a-button type="link" size="small" @click="openLogs(record)">详情</a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="logVisible"
      :title="logTitle"
      :footer="null"
      width="700px"
    >
      <a-spin :spinning="logLoading">
        <a-timeline v-if="logs.length" style="margin-top: 16px">
          <a-timeline-item
            v-for="log in logs"
            :key="log.id"
            :color="actionColor[log.action] || 'blue'"
          >
            <div class="log-item">
              <div class="log-header">
                <span class="log-action">
                  <a-tag :color="actionColor[log.action] || 'blue'" size="small">{{ actionLabel[log.action] || log.action }}</a-tag>
                </span>
                <span class="log-actor">{{ log.actorName || '系统' }}</span>
                <span class="log-time">{{ formatTime(log.createdAt) }}</span>
              </div>
              <div v-if="log.detailJson" class="log-detail">
                <template v-if="log.action === 'ai_review'">
                  <div class="log-comment" :class="{ 'ai-passed': log.detailJson.result === 'passed', 'ai-rejected': log.detailJson.result === 'rejected', 'ai-fallback': log.detailJson.result === 'fallback' || log.detailJson.result === 'error' }">
                    <span v-if="log.detailJson.result === 'passed'">✓ AI 审核通过</span>
                    <span v-else-if="log.detailJson.result === 'rejected'">✗ AI 审核不通过</span>
                    <span v-else-if="log.detailJson.result === 'fallback'">⚠ AI 审核需人工确认</span>
                    <span v-else-if="log.detailJson.result === 'error'">⚠ AI 审核异常</span>
                    <div v-if="log.detailJson.summary" class="log-summary">{{ log.detailJson.summary }}</div>
                  </div>
                </template>
                <template v-else-if="log.action === 'ai_fallback'">
                  <div class="log-comment ai-fallback">已降级到人工审核</div>
                  <div v-if="log.detailJson.reason" class="log-summary">原因：{{ log.detailJson.reason }}</div>
                </template>
                <template v-else-if="log.action === 'workflow_approved'">
                  <div class="log-comment ai-passed">{{ log.detailJson.message || '所有审核阶段已通过' }}</div>
                </template>
                <template v-else-if="log.action === 'workflow_rejected'">
                  <div class="log-comment ai-rejected">{{ log.detailJson.message || '审核已驳回' }}</div>
                </template>
                <template v-else>
                  <div v-if="log.detailJson.comment" class="log-comment">{{ log.detailJson.comment }}</div>
                  <div v-if="log.detailJson.reason" class="log-comment">{{ log.detailJson.reason }}</div>
                  <div v-if="log.detailJson.ai_review" class="log-comment">AI 审核摘要：{{ log.detailJson.ai_review }}</div>
                </template>
              </div>
            </div>
          </a-timeline-item>
        </a-timeline>
        <a-empty v-else description="暂无审核日志" />
      </a-spin>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getReviewWorkflows, getReviewWorkflowLogs } from '@/api/review'
import dayjs from 'dayjs'

const loading = ref(false)
const workflows = ref([])
const filters = reactive({
  businessType: undefined,
  status: undefined,
  search: '',
})
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 条`,
})

const logVisible = ref(false)
const logLoading = ref(false)
const logTitle = ref('审核详情')
const logs = ref([])

const businessTypeLabel = {
  resource: '资源',
  training: '培训',
  exam: '考试',
}
const businessTypeColor = {
  resource: 'blue',
  training: 'green',
  exam: 'orange',
}
const statusLabel = {
  pending: '待审核',
  reviewing: '审核中',
  approved: '已通过',
  rejected: '已驳回',
  cancelled: '已取消',
}
const statusColor = {
  pending: 'default',
  reviewing: 'processing',
  approved: 'success',
  rejected: 'error',
  cancelled: 'default',
}
const actionLabel = {
  submit: '提交审核',
  approve: '通过',
  reject: '驳回',
  revoke: '撤销',
  reassign: '重新分派',
  ai_review: 'AI 审核',
  ai_fallback: 'AI 降级人工',
  workflow_approved: '审核通过',
  workflow_rejected: '审核驳回',
}
const actionColor = {
  submit: 'blue',
  approve: 'green',
  reject: 'red',
  revoke: 'orange',
  reassign: 'cyan',
  ai_review: 'purple',
  ai_fallback: 'orange',
  workflow_approved: 'green',
  workflow_rejected: 'red',
}

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 70 },
  { title: '业务类型', key: 'businessType', width: 100 },
  { title: '业务对象', dataIndex: 'businessTitle', key: 'businessTitle', width: 200, ellipsis: true },
  { title: '提交人', dataIndex: 'submitterName', key: 'submitterName', width: 100 },
  { title: '策略', dataIndex: 'policyName', key: 'policyName', width: 150, ellipsis: true },
  { title: '阶段', key: 'stage', width: 80 },
  { title: '状态', key: 'status', width: 100 },
  { title: '提交时间', key: 'startedAt', width: 170 },
  { title: '完成时间', key: 'finishedAt', width: 170 },
  { title: '操作', key: 'action', width: 80, fixed: 'right' },
]

function formatTime(val) {
  if (!val) return ''
  return dayjs(val).format('YYYY-MM-DD HH:mm:ss')
}

async function fetchWorkflows() {
  loading.value = true
  try {
    const result = await getReviewWorkflows({
      businessType: filters.businessType || undefined,
      status: filters.status || undefined,
      search: filters.search || undefined,
      page: pagination.current,
      size: pagination.pageSize,
    })
    workflows.value = result.items || []
    pagination.total = result.total || 0
  } catch (error) {
    message.error(error.message || '加载审核记录失败')
  } finally {
    loading.value = false
  }
}

function onTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchWorkflows()
}

async function openLogs(record) {
  logTitle.value = `审核详情 — ${record.businessTitle || `#${record.businessId}`}`
  logVisible.value = true
  logLoading.value = true
  logs.value = []
  try {
    logs.value = await getReviewWorkflowLogs(record.id) || []
  } catch (error) {
    message.error(error.message || '加载审核日志失败')
  } finally {
    logLoading.value = false
  }
}

onMounted(() => {
  fetchWorkflows()
})
</script>

<style scoped>
.review-history-page { padding: 0; }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h2 { margin: 0; font-size: 22px; color: #001234; }

.log-item { margin-bottom: 4px; }
.log-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.log-actor { font-weight: 500; color: #1f1f1f; }
.log-time { color: #8c8c8c; font-size: 12px; }
.log-detail { margin-top: 6px; }
.log-comment {
  color: #595959;
  font-size: 13px;
  line-height: 1.6;
  padding: 6px 10px;
  background: #fafafa;
  border-radius: 4px;
  margin-top: 4px;
}
.log-comment.ai-passed {
  background: #f6ffed;
  color: #389e0d;
}
.log-comment.ai-rejected {
  background: #fff2f0;
  color: #cf1322;
}
.log-comment.ai-fallback {
  background: #f9f0ff;
  color: #722ed1;
}
.log-summary {
  margin-top: 4px;
  color: #595959;
  font-size: 12px;
  line-height: 1.5;
}
</style>
