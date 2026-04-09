<template>
  <div class="review-queue-page">
    <div class="page-header">
      <h2>审核工作台</h2>
      <a-button @click="fetchTasks">刷新</a-button>
    </div>

    <a-card :bordered="false">
      <a-table :data-source="tasks" :columns="columns" row-key="id" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'source'">
            <a-tag v-if="isAiFallback(record)" color="purple">AI 降级</a-tag>
            <a-tag v-else color="default">人工</a-tag>
          </template>
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'pending' ? 'gold' : (record.status === 'approved' ? 'green' : 'red')">
              {{ statusLabel(record.status) }}
            </a-tag>
          </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button size="small" @click="viewDetail(record)">查看</a-button>
            <permissions-tooltip
              :allowed="canReviewTask"
              tips="需要 REVIEW_RESOURCE_STAGE1、REVIEW_RESOURCE_STAGE2 或 VIEW_RESOURCE_ALL 权限"
              v-slot="{ disabled }"
            >
              <a-button size="small" type="primary" :disabled="disabled" @click="approve(record)">通过</a-button>
            </permissions-tooltip>
            <permissions-tooltip
              :allowed="canReviewTask"
              tips="需要 REVIEW_RESOURCE_STAGE1、REVIEW_RESOURCE_STAGE2 或 VIEW_RESOURCE_ALL 权限"
              v-slot="{ disabled }"
            >
              <a-button size="small" danger :disabled="disabled" @click="openReject(record)">驳回</a-button>
            </permissions-tooltip>
          </a-space>
        </template>
      </template>
      </a-table>
    </a-card>

    <a-modal v-model:open="rejectVisible" title="驳回原因" @ok="doReject">
      <a-textarea v-model:value="rejectComment" :rows="4" placeholder="请输入驳回意见" />
    </a-modal>

    <a-modal v-model:open="aiInfoVisible" title="AI 审核信息" :footer="null" width="600px">
      <template v-if="aiInfoTask">
        <a-alert type="warning" show-icon style="margin-bottom: 16px">
          <template #message>AI 审核已降级到人工审核</template>
          <template #description>
            该任务由 AI 自动审核后降级到人工确认，请参考以下 AI 审核信息做出最终判断。
          </template>
        </a-alert>
        <a-descriptions :column="1" bordered size="small">
          <a-descriptions-item label="资源">{{ aiInfoTask.resourceTitle || '-' }}</a-descriptions-item>
          <a-descriptions-item label="审核阶段">第 {{ aiInfoTask.stageOrder }} 级</a-descriptions-item>
          <a-descriptions-item label="AI 审核摘要">
            <div style="white-space: pre-wrap; word-break: break-all;">{{ getAiSummary(aiInfoTask) || '无摘要信息' }}</div>
          </a-descriptions-item>
        </a-descriptions>
        <div style="margin-top: 16px; text-align: right;">
          <a-space>
            <a-button @click="() => { aiInfoVisible = false; if (aiInfoTask?.resourceId) router.push('/resource/detail/' + aiInfoTask.resourceId) }">
              查看资源
            </a-button>
          </a-space>
        </div>
      </template>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import { getReviewTasks, approveReviewTask, rejectReviewTask } from '@/api/review'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

const router = useRouter()
const authStore = useAuthStore()
const tasks = ref([])
const canReviewTask = computed(() => authStore.hasAnyPermission(['REVIEW_RESOURCE_STAGE1', 'REVIEW_RESOURCE_STAGE2', 'VIEW_RESOURCE_ALL']))
const columns = [
  { title: '资源', dataIndex: 'resourceTitle', key: 'resourceTitle' },
  { title: '阶段', dataIndex: 'stageOrder', key: 'stageOrder', width: 100 },
  { title: '来源', key: 'source', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 120 },
  { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt', width: 180 },
  { title: '操作', key: 'action', width: 220 },
]

const rejectVisible = ref(false)
const rejectComment = ref('')
const currentTask = ref(null)
const aiInfoVisible = ref(false)
const aiInfoTask = ref(null)

onMounted(fetchTasks)

function statusLabel(status) {
  const map = { pending: '待处理', approved: '已通过', rejected: '已驳回', skipped: '已跳过' }
  return map[status] || status
}

async function fetchTasks() {
  try {
    tasks.value = await getReviewTasks({ status: 'pending' }) || []
  } catch (e) {
    message.error(e.message || '加载任务失败')
  }
}

function isAiFallback(task) {
  return task.comment && task.comment.startsWith('AI 审核降级到人工')
}

function getAiSummary(task) {
  if (!isAiFallback(task)) return ''
  const prefix = 'AI 审核降级到人工: '
  return task.comment.startsWith(prefix) ? task.comment.slice(prefix.length) : task.comment
}

function viewDetail(task) {
  if (isAiFallback(task)) {
    aiInfoTask.value = task
    aiInfoVisible.value = true
    return
  }
  if (!task?.resourceId) {
    message.warning('未找到对应资源')
    return
  }
  router.push(`/resource/detail/${task.resourceId}`)
}

async function approve(task) {
  if (!canReviewTask.value) return
  try {
    await approveReviewTask(task.id, { comment: '审核通过' })
    message.success('已通过')
    fetchTasks()
  } catch (e) {
    message.error(e.message || '操作失败')
  }
}

function openReject(task) {
  if (!canReviewTask.value) return
  currentTask.value = task
  rejectComment.value = ''
  rejectVisible.value = true
}

async function doReject() {
  if (!canReviewTask.value) return
  if (!currentTask.value) return
  try {
    await rejectReviewTask(currentTask.value.id, { comment: rejectComment.value || '不符合发布要求' })
    message.success('已驳回')
    rejectVisible.value = false
    fetchTasks()
  } catch (e) {
    message.error(e.message || '操作失败')
  }
}
</script>

<style scoped>
.review-queue-page { padding: 0; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
</style>
