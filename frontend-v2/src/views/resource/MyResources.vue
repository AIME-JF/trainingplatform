<template>
  <div class="page-content resource-page">
    <LearningResourceTabs />

    <div class="page-header">
      <div>
        <h1 class="page-title">我的空间</h1>
        <p class="page-subtitle">管理自己上传的资源和审核状态。</p>
      </div>
      <a-space wrap>
        <a-button v-if="showLibraryAction" @click="router.push('/resource/library')">资源库</a-button>
        <PermissionsTooltip v-if="showTeachingGenerationAction" :allowed="canUseTeachingGeneration" tips="需要 USE_TEACHING_RESOURCE_GENERATION 权限">
          <template #default="{ disabled }">
            <a-button :disabled="disabled" @click="router.push('/resource/teaching-generate')">教学资源生成</a-button>
          </template>
        </PermissionsTooltip>
        <PermissionsTooltip :allowed="canUploadResource" tips="需要 CREATE_RESOURCE 或 VIEW_RESOURCE_ALL 权限">
          <template #default="{ disabled }">
            <a-button type="primary" :disabled="disabled" @click="uploadModalOpen = true">上传资源</a-button>
          </template>
        </PermissionsTooltip>
      </a-space>
    </div>

    <a-card :bordered="false" class="filter-card">
      <a-space wrap class="filter-toolbar">
        <a-select v-model:value="query.status" style="width: 180px" @change="fetchMine">
          <a-select-option value="">全部状态</a-select-option>
          <a-select-option value="draft">草稿</a-select-option>
          <a-select-option value="pending_review">待审核</a-select-option>
          <a-select-option value="reviewing">审核中</a-select-option>
          <a-select-option value="published">已发布</a-select-option>
          <a-select-option value="rejected">已驳回</a-select-option>
          <a-select-option value="offline">已下线</a-select-option>
        </a-select>
        <ResourceSearchInput v-model:value="query.search" style="width: 320px" placeholder="搜索我的空间资源" @search="fetchMine" />
      </a-space>
    </a-card>

    <a-table
      :data-source="rows"
      :columns="columns"
      :loading="loading"
      :pagination="false"
      row-key="id"
      :scroll="{ x: 1040 }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'status'">
          <a-tag :color="getResourceStatusColor(record.status)">{{ getResourceStatusLabel(record.status) }}</a-tag>
        </template>
        <template v-else-if="column.key === 'content_type'">
          {{ getResourceContentTypeLabel(record.content_type) }}
        </template>
        <template v-else-if="column.key === 'tags'">
          <a-space wrap>
            <a-tag v-for="tag in record.tags || []" :key="tag">{{ tag }}</a-tag>
          </a-space>
        </template>
        <template v-else-if="column.key === 'action'">
          <a-space wrap>
            <a-button size="small" @click="router.push(`/resource/detail/${record.id}`)">查看</a-button>
            <a-button size="small" @click="viewWorkflow(record.id)">轨迹</a-button>
            <PermissionsTooltip
              v-if="['draft', 'rejected'].includes(record.status)"
              :allowed="canSubmitReview"
              tips="需要同时具备 CREATE_RESOURCE 和 SUBMIT_RESOURCE_REVIEW 权限"
            >
              <template #default="{ disabled }">
                <a-button size="small" type="primary" ghost :disabled="disabled" @click="submitReview(record.id)">
                  提交审核
                </a-button>
              </template>
            </PermissionsTooltip>
            <PermissionsTooltip
              v-if="['offline', 'rejected'].includes(record.status)"
              :allowed="canManage(record)"
              tips="仅资源上传者或具备 UPDATE_RESOURCE / VIEW_RESOURCE_ALL 权限可执行该操作"
            >
              <template #default="{ disabled }">
                <a-button size="small" :disabled="disabled" @click="handlePublish(record.id)">重新发布</a-button>
              </template>
            </PermissionsTooltip>
            <PermissionsTooltip
              v-if="record.status === 'published'"
              :allowed="canManage(record)"
              tips="仅资源上传者或具备 UPDATE_RESOURCE / VIEW_RESOURCE_ALL 权限可执行该操作"
            >
              <template #default="{ disabled }">
                <a-button size="small" danger ghost :disabled="disabled" @click="handleOffline(record.id)">下线</a-button>
              </template>
            </PermissionsTooltip>
            <PermissionsTooltip
              :allowed="canManage(record)"
              tips="仅资源上传者或具备 UPDATE_RESOURCE / VIEW_RESOURCE_ALL 权限可执行该操作"
            >
              <template #default="{ disabled }">
                <a-popconfirm v-if="!disabled" title="确认删除该资源吗？" @confirm="handleDelete(record.id)">
                  <a-button size="small" danger>删除</a-button>
                </a-popconfirm>
                <a-button v-else size="small" danger :disabled="disabled">删除</a-button>
              </template>
            </PermissionsTooltip>
          </a-space>
        </template>
      </template>
    </a-table>

    <div class="pagination-wrapper">
      <a-pagination :current="query.page" :page-size="query.size" :total="total" @change="onPageChange" />
    </div>

    <a-modal v-model:open="workflowVisible" title="审核轨迹" :footer="null">
      <a-empty v-if="!workflow?.tasks?.length" description="暂无审核记录" />
      <a-timeline v-else>
        <a-timeline-item v-for="task in workflow.tasks" :key="task.id">
          阶段 {{ task.stage_order }} · {{ task.assignee_name || task.assignee_user_id }}
          <div>状态：{{ getResourceStatusLabel(task.status) }}</div>
          <div v-if="task.comment">意见：{{ task.comment }}</div>
        </a-timeline-item>
      </a-timeline>
    </a-modal>

    <ResourceUploadModal v-model:open="uploadModalOpen" @success="handleUploadSuccess" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { ResourceListItemResponse, ReviewWorkflowResponse } from '@/api/learning-resource'
import {
  getReviewWorkflow,
  listResources,
  offlineResource,
  publishResource,
  removeResource,
  submitResourceReview,
} from '@/api/learning-resource'
import { useMobile } from '@/composables/useMobile'
import { useAuthStore } from '@/stores/auth'
import LearningResourceTabs from '@/components/resource/LearningResourceTabs.vue'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'
import ResourceSearchInput from '@/components/resource/ResourceSearchInput.vue'
import ResourceUploadModal from '@/components/resource/ResourceUploadModal.vue'
import { getResourceContentTypeLabel, getResourceStatusColor, getResourceStatusLabel } from '@/utils/learning-resource'

const router = useRouter()
const authStore = useAuthStore()
const { isMobile } = useMobile()

const query = reactive({
  page: 1,
  size: 10,
  search: '',
  status: '',
})

const rows = ref<ResourceListItemResponse[]>([])
const total = ref(0)
const loading = ref(false)
const uploadModalOpen = ref(false)
const workflowVisible = ref(false)
const workflow = ref<ReviewWorkflowResponse | null>(null)

const canUploadResource = computed(() => authStore.hasAnyPermission(['CREATE_RESOURCE', 'VIEW_RESOURCE_ALL']))
const canUseTeachingGeneration = computed(() => authStore.hasPermission('USE_TEACHING_RESOURCE_GENERATION'))
const canSubmitReview = computed(() => authStore.hasAllPermissions(['CREATE_RESOURCE', 'SUBMIT_RESOURCE_REVIEW']))
const canManageAnyResource = computed(() => authStore.hasAnyPermission(['UPDATE_RESOURCE', 'VIEW_RESOURCE_ALL']))
const showLibraryAction = computed(() => !isMobile.value)
const showTeachingGenerationAction = computed(() => !isMobile.value || canUseTeachingGeneration.value)

const columns = [
  { title: '标题', dataIndex: 'title', key: 'title', width: 260 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 120 },
  { title: '类型', dataIndex: 'content_type', key: 'content_type', width: 120 },
  { title: '标签', dataIndex: 'tags', key: 'tags' },
  { title: '操作', key: 'action', width: 420 },
]

onMounted(() => {
  void fetchMine()
})

function canManage(record: ResourceListItemResponse) {
  return record.uploader_id === authStore.currentUser?.id || canManageAnyResource.value
}

async function fetchMine() {
  loading.value = true
  try {
    const response = await listResources({
      page: query.page,
      size: query.size,
      search: query.search || undefined,
      status: query.status || undefined,
      my_only: true,
    })
    rows.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载失败')
  } finally {
    loading.value = false
  }
}

async function submitReview(resourceId: number) {
  try {
    await submitResourceReview(resourceId)
    message.success('已提交审核')
    await fetchMine()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '提交失败')
  }
}

async function handlePublish(resourceId: number) {
  try {
    await publishResource(resourceId)
    message.success('发布成功')
    await fetchMine()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '发布失败')
  }
}

async function handleOffline(resourceId: number) {
  try {
    await offlineResource(resourceId)
    message.success('下线成功')
    await fetchMine()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '下线失败')
  }
}

async function handleDelete(resourceId: number) {
  try {
    await removeResource(resourceId)
    message.success('删除成功')
    await fetchMine()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '删除失败')
  }
}

async function viewWorkflow(resourceId: number) {
  try {
    workflow.value = await getReviewWorkflow(resourceId)
    workflowVisible.value = true
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载审核轨迹失败')
  }
}

function onPageChange(page: number, size: number) {
  query.page = page
  query.size = size
  void fetchMine()
}

function handleUploadSuccess() {
  query.page = 1
  void fetchMine()
}
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 6px;
}

.page-subtitle {
  color: var(--v2-text-secondary);
}

.filter-card {
  margin-bottom: 20px;
  border-radius: var(--v2-radius-lg);
}

.filter-toolbar {
  gap: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
