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
    radial-gradient(circle at top center, var(--resource-upload-bg-radial), transparent 34%),
    linear-gradient(180deg, var(--resource-upload-bg-top) 0%, #17181c 38%, var(--resource-upload-bg-bottom) 100%);
  color: var(--resource-upload-text-primary);
}

.my-space-shell {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: calc(100vh - var(--v2-bottomnav-height));
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
}

.page-header-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 12px;
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
  color: var(--resource-upload-text-primary);
}

.page-subtitle {
  margin: 0;
  color: var(--resource-upload-text-secondary);
  font-size: 15px;
  line-height: 1.6;
}

.header-btn {
  height: 46px !important;
  padding: 0 20px !important;
  border-radius: 999px !important;
  font-weight: 700 !important;
  font-size: 15px !important;
  letter-spacing: -0.01em;
  box-shadow: none !important;
}

.secondary-btn {
  border-color: var(--resource-upload-border) !important;
  background: var(--resource-upload-surface-soft) !important;
  color: var(--resource-upload-text-primary) !important;
}

.secondary-btn:hover:not(:disabled),
.secondary-btn:focus:not(:disabled) {
  border-color: var(--resource-upload-border-strong) !important;
  background: var(--resource-upload-surface-hover) !important;
  color: var(--resource-upload-text-primary) !important;
}

.upload-btn {
  border-color: rgba(255, 255, 255, 0.24) !important;
  background: var(--resource-upload-primary-bg) !important;
  color: var(--resource-upload-primary-text) !important;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.16) !important;
}

.upload-btn:hover:not(:disabled),
.upload-btn:focus:not(:disabled) {
  border-color: rgba(255, 255, 255, 0.3) !important;
  background: var(--resource-upload-primary-bg-hover) !important;
  color: var(--resource-upload-primary-text) !important;
}

.filter-card,
.content-card {
  border-radius: 30px;
  background:
    linear-gradient(180deg, var(--resource-upload-surface-top) 0%, var(--resource-upload-surface-bottom) 100%);
  border: 1px solid var(--resource-upload-border);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    var(--resource-upload-shadow);
}

.filter-toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
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
  min-height: 280px;
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
  gap: 16px;
  padding: 16px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid var(--resource-upload-border);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.03),
    0 10px 22px rgba(0, 0, 0, 0.16);
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
  line-height: 1.4;
  font-weight: 700;
  color: var(--resource-upload-text-primary);
  word-break: break-word;
}

.mobile-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 10px;
  color: var(--resource-upload-text-secondary);
  font-size: 12px;
}

.mobile-card-summary {
  margin: 10px 0 0;
  color: var(--resource-upload-text-secondary);
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
  margin-top: 4px;
}

.pagination-wrapper.mobile {
  justify-content: center;
}

.my-space-page :deep(.ant-empty-description) {
  color: var(--resource-upload-text-tertiary);
}

.my-space-page :deep(.ant-empty-image) {
  opacity: 0.78;
  filter: grayscale(1);
}

.my-space-page :deep(.ant-tag) {
  margin: 0;
  border-radius: 999px;
  border-color: var(--resource-upload-border);
  background: var(--resource-upload-surface-soft);
  color: var(--resource-upload-text-secondary);
}

.my-space-page :deep(.filter-card .ant-card-body),
.my-space-page :deep(.content-card .ant-card-body) {
  padding: 20px !important;
}

.my-space-page :deep(.ant-select-selector),
.my-space-page :deep(.resource-search-input.ant-input-affix-wrapper) {
  border-color: var(--resource-upload-border) !important;
  border-radius: 18px !important;
  background: rgba(12, 13, 16, 0.88) !important;
  color: var(--resource-upload-text-primary) !important;
  box-shadow: none !important;
  transition: border-color 0.2s ease, background-color 0.2s ease !important;
}

.my-space-page :deep(.ant-select-selector) {
  min-height: 48px !important;
  padding-top: 6px !important;
  padding-bottom: 6px !important;
}

.my-space-page :deep(.ant-select-focused .ant-select-selector),
.my-space-page :deep(.resource-search-input.ant-input-affix-wrapper:hover),
.my-space-page :deep(.resource-search-input.ant-input-affix-wrapper:focus),
.my-space-page :deep(.resource-search-input.ant-input-affix-wrapper-focused),
.my-space-page :deep(.ant-select:not(.ant-select-disabled):hover .ant-select-selector) {
  border-color: var(--resource-upload-border-strong) !important;
  background: rgba(16, 18, 22, 0.92) !important;
}

.my-space-page :deep(.ant-select-selection-placeholder),
.my-space-page :deep(.resource-search-input .ant-input::placeholder),
.my-space-page :deep(.resource-search-input .ant-input-prefix) {
  color: var(--resource-upload-text-quiet) !important;
}

.my-space-page :deep(.resource-search-input .ant-input),
.my-space-page :deep(.ant-select-selection-item),
.my-space-page :deep(.ant-select-arrow),
.my-space-page :deep(.resource-search-input .ant-input-prefix .anticon),
.my-space-page :deep(.resource-search-input .ant-input-clear-icon) {
  color: var(--resource-upload-text-primary) !important;
}

.my-space-page :deep(.resource-search-input .ant-input) {
  background: transparent !important;
  color: #fff !important;
  -webkit-text-fill-color: #fff !important;
}

.my-space-page :deep(.ant-spin-dot-item) {
  background-color: rgba(255, 255, 255, 0.72);
}

.my-space-page :deep(.my-space-table .ant-table) {
  background: transparent !important;
  color: var(--resource-upload-text-primary);
}

.my-space-page :deep(.my-space-table .ant-table-container) {
  border-inline: 1px solid var(--resource-upload-border);
  border-top: 1px solid var(--resource-upload-border);
  border-radius: 24px;
  overflow: hidden;
}

.my-space-page :deep(.my-space-table .ant-table-thead > tr > th) {
  background: rgba(255, 255, 255, 0.045) !important;
  border-bottom-color: var(--resource-upload-border) !important;
  color: var(--resource-upload-text-secondary) !important;
  font-weight: 600 !important;
}

.my-space-page :deep(.my-space-table .ant-table-tbody > tr > td) {
  background: transparent !important;
  border-bottom-color: var(--resource-upload-border) !important;
  color: var(--resource-upload-text-primary) !important;
}

.my-space-page :deep(.my-space-table .ant-table-tbody > tr.ant-table-row:hover > td) {
  background: rgba(255, 255, 255, 0.04) !important;
}

.my-space-page :deep(.resource-action-group .action-btn) {
  border-color: var(--resource-upload-border) !important;
  background: var(--resource-upload-surface-soft) !important;
  color: var(--resource-upload-text-primary) !important;
}

.my-space-page :deep(.resource-action-group .action-btn:hover:not(:disabled)),
.my-space-page :deep(.resource-action-group .action-btn:focus:not(:disabled)) {
  border-color: var(--resource-upload-border-strong) !important;
  background: var(--resource-upload-surface-hover) !important;
  color: var(--resource-upload-text-primary) !important;
}

.my-space-page :deep(.resource-action-group .primary-btn) {
  border-color: rgba(255, 255, 255, 0.24) !important;
  background: var(--resource-upload-primary-bg) !important;
  color: var(--resource-upload-primary-text) !important;
}

.my-space-page :deep(.resource-action-group .primary-btn:hover:not(:disabled)),
.my-space-page :deep(.resource-action-group .primary-btn:focus:not(:disabled)) {
  border-color: rgba(255, 255, 255, 0.3) !important;
  background: var(--resource-upload-primary-bg-hover) !important;
  color: var(--resource-upload-primary-text) !important;
}

.my-space-page :deep(.resource-action-group .danger-btn) {
  border-color: rgba(255, 113, 113, 0.22) !important;
  background: rgba(255, 113, 113, 0.08) !important;
  color: #ffb5b5 !important;
}

.my-space-page :deep(.resource-action-group .danger-btn:hover:not(:disabled)),
.my-space-page :deep(.resource-action-group .danger-btn:focus:not(:disabled)) {
  border-color: rgba(255, 132, 132, 0.3) !important;
  background: rgba(255, 113, 113, 0.14) !important;
  color: #ffd0d0 !important;
}

.my-space-page :deep(.ant-pagination .ant-pagination-item),
.my-space-page :deep(.ant-pagination .ant-pagination-prev),
.my-space-page :deep(.ant-pagination .ant-pagination-next) {
  background: var(--resource-upload-surface-soft);
  border-color: var(--resource-upload-border);
  border-radius: 12px;
}

.my-space-page :deep(.ant-pagination .ant-pagination-item a),
.my-space-page :deep(.ant-pagination .ant-pagination-prev .anticon),
.my-space-page :deep(.ant-pagination .ant-pagination-next .anticon) {
  color: var(--resource-upload-text-primary);
}

.my-space-page :deep(.ant-pagination .ant-pagination-item-active) {
  border-color: rgba(255, 255, 255, 0.24);
  background: var(--resource-upload-primary-bg);
}

.my-space-page :deep(.ant-pagination .ant-pagination-item-active a) {
  color: var(--resource-upload-primary-text) !important;
}

@media (max-width: 768px) {
  .my-space-shell {
    gap: 16px;
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

  .page-title {
    font-size: 32px;
  }

  .page-subtitle {
    font-size: 14px;
  }

  .page-header-actions :deep(.permission-tooltip-wrapper) {
    flex: 1 1 0;
    width: 100%;
  }

  .header-btn {
    width: 100%;
    height: 44px !important;
  }

  .status-select,
  .search-input {
    width: 100%;
    flex: 1 1 auto;
  }

  .filter-card,
  .content-card {
    border-radius: 24px;
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
