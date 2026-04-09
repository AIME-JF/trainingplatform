<template>
  <div class="review-queue-page">
    <div class="page-header">
      <h2>知识审核</h2>
    </div>

    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="tasks" tab="审核任务">
        <a-card :bordered="false">
          <template #extra><a-button size="small" @click="fetchTasks">刷新</a-button></template>
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
                  <permissions-tooltip :allowed="canReviewTask" tips="需要审核权限" v-slot="{ disabled }">
                    <a-button size="small" type="primary" :disabled="disabled" @click="approve(record)">通过</a-button>
                  </permissions-tooltip>
                  <permissions-tooltip :allowed="canReviewTask" tips="需要审核权限" v-slot="{ disabled }">
                    <a-button size="small" danger :disabled="disabled" @click="openReject(record)">驳回</a-button>
                  </permissions-tooltip>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-tab-pane>
      <a-tab-pane key="history" tab="审核记录">
        <ReviewHistoryPanel business-type="library" />
      </a-tab-pane>
    </a-tabs>

    <a-modal v-model:open="rejectVisible" title="驳回原因" @ok="doReject">
      <a-textarea v-model:value="rejectComment" :rows="4" placeholder="请输入驳回意见" />
    </a-modal>

    <a-modal v-model:open="aiInfoVisible" title="审核详情" :footer="null" width="700px">
      <template v-if="aiInfoTask">
        <a-alert v-if="isAiFallback(aiInfoTask)" type="warning" show-icon style="margin-bottom: 16px">
          <template #message>AI 审核已降级到人工审核</template>
          <template #description>请参考以下 AI 审核信息做出最终判断。</template>
        </a-alert>
        <a-descriptions :column="1" bordered size="small">
          <a-descriptions-item label="知识名称">{{ aiInfoTask.businessTitle || '-' }}</a-descriptions-item>
          <a-descriptions-item label="审核阶段">第 {{ aiInfoTask.stageOrder }} 级</a-descriptions-item>
          <a-descriptions-item label="状态">{{ statusLabel(aiInfoTask.status) }}</a-descriptions-item>
          <a-descriptions-item v-if="isAiFallback(aiInfoTask)" label="AI 审核摘要">
            <div style="white-space: pre-wrap; word-break: break-all;">{{ getAiSummary(aiInfoTask) }}</div>
          </a-descriptions-item>
        </a-descriptions>

        <a-spin :spinning="detailLoading" style="margin-top: 16px">
          <template v-if="libraryDetail">
            <a-divider orientation="left">内容预览</a-divider>
            <!-- 知识卡片：直接显示 HTML 内容 -->
            <div v-if="libraryDetail.sourceKind === 'knowledge' && libraryDetail.knowledgeContentHtml" class="knowledge-preview" v-html="libraryDetail.knowledgeContentHtml" />
            <!-- 纯文本内容 -->
            <div v-else-if="libraryDetail.plainTextContent" class="text-preview">{{ libraryDetail.plainTextContent }}</div>
            <!-- 文件类型：显示文件信息和下载按钮 -->
            <div v-else-if="libraryDetail.fileUrl" class="file-preview">
              <a-descriptions :column="1" size="small">
                <a-descriptions-item label="文件名">{{ libraryDetail.fileName || '-' }}</a-descriptions-item>
                <a-descriptions-item label="文件类型">{{ libraryDetail.contentType || '-' }}</a-descriptions-item>
                <a-descriptions-item label="文件大小">{{ formatFileSize(libraryDetail.size) }}</a-descriptions-item>
              </a-descriptions>
              <a-button type="primary" :href="libraryDetail.fileUrl" target="_blank" style="margin-top: 8px">下载文件</a-button>
            </div>
            <a-empty v-else description="暂无可预览内容" />
          </template>
        </a-spin>
      </template>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import { getReviewTasks, approveReviewTask, rejectReviewTask } from '@/api/review'
import { getLibraryItem } from '@/api/library'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'
import ReviewHistoryPanel from './ReviewHistoryPanel.vue'

const authStore = useAuthStore()
const tasks = ref([])
const activeTab = ref('tasks')
const canReviewTask = computed(() => authStore.hasAnyPermission(['REVIEW_RESOURCE_STAGE1', 'REVIEW_RESOURCE_STAGE2', 'VIEW_RESOURCE_ALL']))

const columns = [
  { title: '知识名称', dataIndex: 'businessTitle', key: 'businessTitle' },
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
const detailLoading = ref(false)
const libraryDetail = ref(null)

onMounted(fetchTasks)

function statusLabel(status) {
  const map = { pending: '待处理', approved: '已通过', rejected: '已驳回', skipped: '已跳过' }
  return map[status] || status
}

function isAiFallback(task) {
  return task.comment && task.comment.startsWith('AI 审核降级到人工')
}

function getAiSummary(task) {
  if (!isAiFallback(task)) return ''
  const prefix = 'AI 审核降级到人工: '
  return task.comment.startsWith(prefix) ? task.comment.slice(prefix.length) : task.comment
}

async function viewDetail(task) {
  aiInfoTask.value = task
  libraryDetail.value = null
  aiInfoVisible.value = true
  detailLoading.value = true
  try {
    libraryDetail.value = await getLibraryItem(task.businessId)
  } catch {
    libraryDetail.value = null
  } finally {
    detailLoading.value = false
  }
}

async function fetchTasks() {
  try {
    tasks.value = await getReviewTasks({ status: 'pending', businessType: 'library' }) || []
  } catch (e) {
    message.error(e.message || '加载任务失败')
  }
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
  if (!canReviewTask.value || !currentTask.value) return
  try {
    await rejectReviewTask(currentTask.value.id, { comment: rejectComment.value || '不符合发布要求' })
    message.success('已驳回')
    rejectVisible.value = false
    fetchTasks()
  } catch (e) {
    message.error(e.message || '操作失败')
  }
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++ }
  return `${size.toFixed(i ? 1 : 0)} ${units[i]}`
}
</script>

<style scoped>
.review-queue-page { padding: 0; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #001234; }
.knowledge-preview {
  padding: 16px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  max-height: 400px;
  overflow-y: auto;
  line-height: 1.8;
}
.text-preview {
  padding: 16px;
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  max-height: 400px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 13px;
  line-height: 1.6;
  color: #333;
}
</style>
