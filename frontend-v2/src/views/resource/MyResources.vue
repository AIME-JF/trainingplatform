<template>
  <div class="page-content resource-page my-space-page">
    <section class="my-space-shell">
      <div class="page-header">
        <div>
          <h1 class="page-title">我的空间</h1>
          <p class="page-subtitle">管理自己上传的资源和审核状态。</p>
        </div>

        <div class="page-header-actions">
          <PermissionsTooltip
            v-if="showTeachingGenerationAction"
            :allowed="canUseTeachingGeneration"
            :block="isMobile"
            tips="需要 USE_TEACHING_RESOURCE_GENERATION 权限"
          >
            <template #default="{ disabled }">
              <a-button class="header-btn secondary-btn" :disabled="disabled" @click="router.push('/resource/teaching-generate')">
                教学资源生成
              </a-button>
            </template>
          </PermissionsTooltip>

          <a-button class="header-btn upload-btn" type="primary" @click="uploadModalOpen = true">
            上传资源
          </a-button>
        </div>
      </div>

      <a-card :bordered="false" class="filter-card">
        <div class="filter-toolbar" :class="{ mobile: isMobile }">
          <a-select v-model:value="query.status" class="status-select" @change="handleFilterChange">
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="pending_review">待审核</a-select-option>
            <a-select-option value="reviewing">审核中</a-select-option>
            <a-select-option value="published">已发布</a-select-option>
            <a-select-option value="rejected">已驳回</a-select-option>
            <a-select-option value="offline">已下线</a-select-option>
          </a-select>
          <ResourceSearchInput
            v-model:value="query.search"
            class="search-input"
            placeholder="搜索我的空间资源"
            @search="handleSearch"
          />
        </div>
      </a-card>

      <a-card :bordered="false" class="content-card">
        <a-spin :spinning="loading">
          <template v-if="isMobile">
            <div v-if="!rows.length && !loading" class="mobile-empty-state">
              <a-empty description="暂无资源" />
            </div>

            <div v-else class="mobile-resource-list">
              <article v-for="record in rows" :key="record.id" class="mobile-resource-card">
                <div class="mobile-card-top">
                  <ResourceCardCover
                    class="mobile-resource-cover"
                    :title="record.title"
                    :content-type="record.content_type"
                    :cover-url="record.cover_url"
                    :status-label="getResourceStatusLabel(record.status)"
                    minimal
                  />

                  <div class="mobile-card-main">
                    <div class="mobile-card-head">
                      <h3 class="mobile-card-title">{{ record.title }}</h3>
                      <a-tag :color="getResourceStatusColor(record.status)">{{ getResourceStatusLabel(record.status) }}</a-tag>
                    </div>

                    <div class="mobile-card-meta">
                      <span>{{ getResourceContentTypeLabel(record.content_type) }}</span>
                      <span>{{ formatDateTime(record.updated_at || record.created_at) }}</span>
                    </div>

                    <p class="mobile-card-summary">{{ record.summary || '暂无摘要' }}</p>

                    <div v-if="record.tags?.length" class="mobile-card-tags">
                      <a-tag v-for="tag in record.tags" :key="tag">{{ tag }}</a-tag>
                    </div>
                  </div>
                </div>

                <MyResourceActionGroup
                  compact
                  :record="record"
                  :can-submit-review="canSubmitReview"
                  :can-manage="canManage(record)"
                  @view="goDetail"
                  @workflow="viewWorkflow"
                  @submit-review="submitReview"
                  @publish="handlePublish"
                  @offline="handleOffline"
                  @delete="handleDelete"
                />
              </article>
            </div>
          </template>

          <a-table
            v-else
            class="my-space-table"
            :data-source="rows"
            :columns="columns"
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
                <MyResourceActionGroup
                  :record="record"
                  :can-submit-review="canSubmitReview"
                  :can-manage="canManage(record)"
                  @view="goDetail"
                  @workflow="viewWorkflow"
                  @submit-review="submitReview"
                  @publish="handlePublish"
                  @offline="handleOffline"
                  @delete="handleDelete"
                />
              </template>
            </template>
          </a-table>
        </a-spin>
      </a-card>

      <div class="pagination-wrapper" :class="{ mobile: isMobile }">
        <a-pagination :current="query.page" :page-size="query.size" :total="total" @change="onPageChange" />
      </div>
    </section>

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
import MyResourceActionGroup from '@/components/resource/MyResourceActionGroup.vue'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'
import ResourceCardCover from '@/components/resource/ResourceCardCover.vue'
import ResourceSearchInput from '@/components/resource/ResourceSearchInput.vue'
import ResourceUploadModal from '@/components/resource/ResourceUploadModal.vue'
import {
  formatDateTime,
  getResourceContentTypeLabel,
  getResourceStatusColor,
  getResourceStatusLabel,
} from '@/utils/learning-resource'

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

const canUseTeachingGeneration = computed(() => authStore.hasPermission('USE_TEACHING_RESOURCE_GENERATION'))
const canSubmitReview = computed(() => true)
const canManageAnyResource = computed(() => authStore.hasAnyPermission(['UPDATE_RESOURCE', 'VIEW_RESOURCE_ALL']))
const showTeachingGenerationAction = computed(() => !isMobile.value || canUseTeachingGeneration.value)

const columns = [
  { title: '标题', dataIndex: 'title', key: 'title', width: 260 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 120 },
  { title: '类型', dataIndex: 'content_type', key: 'content_type', width: 120 },
  { title: '标签', dataIndex: 'tags', key: 'tags' },
  { title: '操作', key: 'action', width: 480 },
]

onMounted(() => {
  void fetchMine()
})

function canManage(record: ResourceListItemResponse) {
  return record.uploader_id === authStore.currentUser?.id || canManageAnyResource.value
}

function goDetail(resourceId: number) {
  void router.push({
    path: `/resource/detail/${resourceId}`,
    query: { from: 'my' },
  })
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

function handleFilterChange() {
  query.page = 1
  void fetchMine()
}

function handleSearch() {
  query.page = 1
  void fetchMine()
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
.my-space-page {
  background:
    radial-gradient(circle at top center, rgba(48, 48, 50, 0.34), transparent 24%),
    linear-gradient(180deg, #060606 0%, #0b0b0c 36%, #040404 100%);
  color: #fff;
}

.my-space-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: calc(100vh - var(--v2-bottomnav-height));
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-header-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.page-header-actions :deep(.permission-tooltip-wrapper) {
  max-width: 100%;
}

.page-title {
  margin: 0 0 8px;
  font-size: clamp(28px, 3vw, 38px);
  line-height: 1.08;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #fff;
}

.page-subtitle {
  margin: 0;
  color: rgba(255, 255, 255, 0.62);
  font-size: 15px;
}

.header-btn {
  height: 44px !important;
  padding: 0 18px !important;
  border-radius: 999px !important;
  font-weight: 700 !important;
  box-shadow: none !important;
}

.secondary-btn {
  border-color: rgba(255, 255, 255, 0.14) !important;
  background: rgba(255, 255, 255, 0.05) !important;
  color: rgba(255, 255, 255, 0.92) !important;
}

.secondary-btn:hover:not(:disabled),
.secondary-btn:focus:not(:disabled) {
  border-color: rgba(255, 255, 255, 0.2) !important;
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
}

.upload-btn {
  border: none !important;
  background: linear-gradient(135deg, #4b6ef5 0%, #6c82ff 100%) !important;
  box-shadow: 0 16px 34px rgba(76, 110, 245, 0.22) !important;
}

.filter-card,
.content-card {
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(18, 18, 20, 0.96) 0%, rgba(10, 10, 11, 0.94) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 20px 44px rgba(0, 0, 0, 0.26);
}

.filter-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-toolbar.mobile {
  flex-direction: column;
  align-items: stretch;
}

.status-select {
  width: 180px;
  flex: 0 0 auto;
}

.search-input {
  width: 320px;
  flex: 0 1 320px;
}

.mobile-empty-state {
  display: flex;
  min-height: 240px;
  align-items: center;
  justify-content: center;
}

.mobile-resource-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.mobile-resource-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.mobile-card-top {
  display: grid;
  grid-template-columns: 108px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

.mobile-resource-cover :deep(.resource-card-cover) {
  height: 132px;
  border-radius: 18px;
}

.mobile-card-main {
  min-width: 0;
}

.mobile-card-head {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.mobile-card-title {
  margin: 0;
  font-size: 17px;
  line-height: 1.45;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.94);
  word-break: break-word;
}

.mobile-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 10px;
  color: rgba(255, 255, 255, 0.58);
  font-size: 12px;
}

.mobile-card-summary {
  margin: 10px 0 0;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  line-height: 1.6;
}

.mobile-card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 2px;
}

.pagination-wrapper.mobile {
  justify-content: center;
}

.my-space-page :deep(.ant-empty-description) {
  color: rgba(255, 255, 255, 0.56);
}

.my-space-page :deep(.ant-tag) {
  margin: 0;
  border-radius: 999px;
}

.my-space-page :deep(.filter-card .ant-card-body),
.my-space-page :deep(.content-card .ant-card-body) {
  padding: 18px !important;
}

.my-space-page :deep(.ant-select-selector),
.my-space-page :deep(.resource-search-input .ant-input-affix-wrapper) {
  border-color: rgba(255, 255, 255, 0.1) !important;
  border-radius: 18px !important;
  background: rgba(255, 255, 255, 0.04) !important;
  color: rgba(255, 255, 255, 0.92) !important;
  box-shadow: none !important;
}

.my-space-page :deep(.ant-select-selector) {
  min-height: 46px !important;
  padding-top: 6px !important;
  padding-bottom: 6px !important;
}

.my-space-page :deep(.ant-select-selection-placeholder),
.my-space-page :deep(.resource-search-input .ant-input::placeholder),
.my-space-page :deep(.resource-search-input .ant-input-prefix) {
  color: rgba(255, 255, 255, 0.48) !important;
}

.my-space-page :deep(.resource-search-input .ant-input),
.my-space-page :deep(.ant-select-selection-item),
.my-space-page :deep(.ant-select-arrow),
.my-space-page :deep(.resource-search-input .ant-input-prefix .anticon),
.my-space-page :deep(.resource-search-input .ant-input-clear-icon) {
  color: rgba(255, 255, 255, 0.88) !important;
}

.my-space-page :deep(.my-space-table .ant-table) {
  background: transparent !important;
  color: rgba(255, 255, 255, 0.9);
}

.my-space-page :deep(.my-space-table .ant-table-container) {
  border-inline: 1px solid rgba(255, 255, 255, 0.06);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 20px;
  overflow: hidden;
}

.my-space-page :deep(.my-space-table .ant-table-thead > tr > th) {
  background: rgba(255, 255, 255, 0.04) !important;
  border-bottom-color: rgba(255, 255, 255, 0.08) !important;
  color: rgba(255, 255, 255, 0.7) !important;
}

.my-space-page :deep(.my-space-table .ant-table-tbody > tr > td) {
  background: transparent !important;
  border-bottom-color: rgba(255, 255, 255, 0.06) !important;
  color: rgba(255, 255, 255, 0.9) !important;
}

.my-space-page :deep(.my-space-table .ant-table-tbody > tr.ant-table-row:hover > td) {
  background: rgba(255, 255, 255, 0.03) !important;
}

.my-space-page :deep(.ant-pagination .ant-pagination-item),
.my-space-page :deep(.ant-pagination .ant-pagination-prev),
.my-space-page :deep(.ant-pagination .ant-pagination-next) {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.1);
}

.my-space-page :deep(.ant-pagination .ant-pagination-item a),
.my-space-page :deep(.ant-pagination .ant-pagination-prev .anticon),
.my-space-page :deep(.ant-pagination .ant-pagination-next .anticon) {
  color: rgba(255, 255, 255, 0.82);
}

.my-space-page :deep(.ant-pagination .ant-pagination-item-active) {
  border-color: rgba(108, 130, 255, 0.42);
  background: rgba(108, 130, 255, 0.16);
}

@media (max-width: 768px) {
  .my-space-shell {
    gap: 14px;
    min-height: calc(100vh - var(--v2-bottomnav-height) - 8px);
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
  }

  .page-header-actions {
    justify-content: stretch;
  }

  .page-header-actions :deep(.permission-tooltip-wrapper) {
    flex: 1 1 0;
    width: 100%;
  }

  .header-btn {
    width: 100%;
    height: 42px !important;
  }

  .status-select,
  .search-input {
    width: 100%;
    flex: 1 1 auto;
  }

  .mobile-card-top {
    grid-template-columns: 92px minmax(0, 1fr);
    gap: 12px;
  }

  .mobile-resource-cover :deep(.resource-card-cover) {
    height: 116px;
    border-radius: 16px;
  }

  .my-space-page :deep(.filter-card .ant-card-body),
  .my-space-page :deep(.content-card .ant-card-body) {
    padding: 14px !important;
  }
}
</style>
