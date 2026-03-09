<template>
  <div class="review-queue-page">
    <div class="page-header">
      <h2>审核工作台</h2>
      <a-button @click="fetchTasks">刷新</a-button>
    </div>

    <a-card :bordered="false">
      <a-table :data-source="tasks" :columns="columns" row-key="id" :pagination="false">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'pending' ? 'gold' : (record.status === 'approved' ? 'green' : 'red')">
              {{ statusLabel(record.status) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" type="primary" @click="approve(record)">通过</a-button>
              <a-button size="small" danger @click="openReject(record)">驳回</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal v-model:open="rejectVisible" title="驳回原因" @ok="doReject">
      <a-textarea v-model:value="rejectComment" :rows="4" placeholder="请输入驳回意见" />
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getReviewTasks, approveReviewTask, rejectReviewTask } from '@/api/review'

const tasks = ref([])
const columns = [
  { title: '资源', dataIndex: 'resourceTitle', key: 'resourceTitle' },
  { title: '阶段', dataIndex: 'stageOrder', key: 'stageOrder', width: 100 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 120 },
  { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt', width: 180 },
  { title: '操作', key: 'action', width: 160 },
]

const rejectVisible = ref(false)
const rejectComment = ref('')
const currentTask = ref(null)

onMounted(fetchTasks)

function statusLabel(status) {
  const map = { pending: '待处理', approved: '已通过', rejected: '已驳回' }
  return map[status] || status
}

async function fetchTasks() {
  try {
    tasks.value = await getReviewTasks({ status: 'pending' }) || []
  } catch (e) {
    message.error(e.message || '加载任务失败')
  }
}

async function approve(task) {
  try {
    await approveReviewTask(task.id, { comment: '审核通过' })
    message.success('已通过')
    fetchTasks()
  } catch (e) {
    message.error(e.message || '操作失败')
  }
}

function openReject(task) {
  currentTask.value = task
  rejectComment.value = ''
  rejectVisible.value = true
}

async function doReject() {
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
