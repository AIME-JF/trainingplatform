<template>
  <div class="page-content resource-page">
    <LearningResourceTabs />

    <div class="page-header">
      <div>
        <h1 class="page-title">资源库</h1>
        <p class="page-subtitle">浏览平台内已发布的学习资源。</p>
      </div>
      <a-space>
        <a-button @click="router.push('/resource/my')">我的空间</a-button>
        <PermissionsTooltip v-if="!isStudentOnly" :allowed="canUploadResource" tips="需要 CREATE_RESOURCE 或 VIEW_RESOURCE_ALL 权限">
          <template #default="{ disabled }">
            <a-button type="primary" :disabled="disabled" @click="uploadModalOpen = true">上传资源</a-button>
          </template>
        </PermissionsTooltip>
      </a-space>
    </div>

    <a-card :bordered="false" class="filter-card">
      <a-row :gutter="[12, 12]">
        <a-col :xs="24" :md="10">
          <ResourceSearchInput v-model:value="query.search" placeholder="搜索资源标题" @search="fetchResources" />
        </a-col>
        <a-col :xs="24" :md="6">
          <a-select v-model:value="query.content_type" style="width: 100%" @change="fetchResources">
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="video">视频</a-select-option>
            <a-select-option value="document">文档</a-select-option>
            <a-select-option value="image">图片</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" />
    </div>

    <a-empty v-else-if="!resources.length" description="暂无已发布的资源" class="empty-block" />

    <div v-else class="resource-grid">
      <div
        v-for="item in resources"
        :key="item.id"
        class="resource-card"
        role="link"
        tabindex="0"
        @click="goToDetail(item.id)"
        @keydown.enter.prevent="goToDetail(item.id)"
        @keydown.space.prevent="goToDetail(item.id)"
      >
        <ResourceCardCover
          :title="item.title"
          :content-type="item.content_type"
          :cover-url="item.cover_url"
          :status-label="getResourceStatusLabel(item.status)"
        />
        <div class="resource-body">
          <h3>{{ item.title }}</h3>
          <p>{{ item.summary || '暂无摘要' }}</p>
          <div class="resource-meta">
            <span>上传者：{{ item.uploader_name || '-' }}</span>
            <span>{{ formatDateTime(item.created_at) }}</span>
          </div>
          <div class="resource-tags">
            <a-tag v-for="tag in (item.tags || []).slice(0, 4)" :key="tag">{{ tag }}</a-tag>
          </div>
          <div v-if="canManage(item)" class="resource-actions" @click.stop>
            <PermissionsTooltip
              v-if="item.status === 'published'"
              :allowed="canManage(item)"
              tips="仅资源上传者或具备 UPDATE_RESOURCE / VIEW_RESOURCE_ALL 权限可执行该操作"
            >
              <template #default="{ disabled }">
                <a-button size="small" danger ghost :disabled="disabled" @click="handleOffline(item.id)">下线</a-button>
              </template>
            </PermissionsTooltip>
            <PermissionsTooltip
              :allowed="canManage(item)"
              tips="仅资源上传者或具备 UPDATE_RESOURCE / VIEW_RESOURCE_ALL 权限可执行该操作"
            >
              <template #default="{ disabled }">
                <a-popconfirm v-if="!disabled" title="确认删除该资源吗？" @confirm="handleDelete(item.id)">
                  <a-button size="small" danger>删除</a-button>
                </a-popconfirm>
                <a-button v-else size="small" danger :disabled="disabled">删除</a-button>
              </template>
            </PermissionsTooltip>
          </div>
        </div>
      </div>
    </div>

    <div v-if="total > 0" class="pagination-wrapper">
      <a-pagination
        :current="query.page"
        :page-size="query.size"
        :total="total"
        show-size-changer
        :page-size-options="['10', '20', '50']"
        @change="onPageChange"
      />
    </div>

    <ResourceUploadModal v-model:open="uploadModalOpen" @success="handleUploadSuccess" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { ResourceListItemResponse } from '@/api/learning-resource'
import { listResources, offlineResource, removeResource } from '@/api/learning-resource'
import { useAuthStore } from '@/stores/auth'
import LearningResourceTabs from '@/components/resource/LearningResourceTabs.vue'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'
import ResourceCardCover from '@/components/resource/ResourceCardCover.vue'
import ResourceSearchInput from '@/components/resource/ResourceSearchInput.vue'
import ResourceUploadModal from '@/components/resource/ResourceUploadModal.vue'
import { formatDateTime, getResourceStatusLabel } from '@/utils/learning-resource'

const router = useRouter()
const authStore = useAuthStore()

const query = reactive({
  page: 1,
  size: 10,
  search: '',
  content_type: '',
})

const resources = ref<ResourceListItemResponse[]>([])
const total = ref(0)
const loading = ref(false)
const uploadModalOpen = ref(false)

const canUploadResource = computed(() => authStore.hasAnyPermission(['CREATE_RESOURCE', 'VIEW_RESOURCE_ALL']))
const canManageAnyResource = computed(() => authStore.hasAnyPermission(['UPDATE_RESOURCE', 'VIEW_RESOURCE_ALL']))
const isStudentOnly = computed(() => {
  const roleCodes = authStore.roleCodes.length ? authStore.roleCodes : [authStore.role].filter(Boolean)
  return roleCodes.length > 0 && roleCodes.every((code) => code === 'student')
})

onMounted(() => {
  void fetchResources()
})

function canManage(item: ResourceListItemResponse) {
  if (isStudentOnly.value) {
    return false
  }
  return item.uploader_id === authStore.currentUser?.id || canManageAnyResource.value
}

async function fetchResources() {
  loading.value = true
  try {
    const response = await listResources({
      page: query.page,
      size: query.size,
      search: query.search || undefined,
      content_type: query.content_type || undefined,
      status: 'published',
    })
    resources.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载资源失败')
  } finally {
    loading.value = false
  }
}

function goToDetail(resourceId: number) {
  void router.push({ path: `/resource/detail/${resourceId}`, query: { from: 'library' } })
}

async function handleOffline(resourceId: number) {
  try {
    await offlineResource(resourceId)
    message.success('资源已下线')
    await fetchResources()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '下线失败')
  }
}

async function handleDelete(resourceId: number) {
  try {
    await removeResource(resourceId)
    message.success('删除成功')
    await fetchResources()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '删除失败')
  }
}

function onPageChange(page: number, size: number) {
  query.page = page
  query.size = size
  void fetchResources()
}

function handleUploadSuccess() {
  query.page = 1
  void fetchResources()
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

.loading-wrapper,
.empty-block {
  padding: 80px 0;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 18px;
}

.resource-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  cursor: pointer;
  border-radius: var(--v2-radius-lg);
  background: var(--v2-bg-card);
  border: 1px solid rgba(15, 23, 42, 0.06);
  box-shadow: var(--v2-shadow-sm);
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease,
    border-color 0.22s ease;
}

.resource-card:hover {
  transform: translateY(-4px);
  border-color: rgba(59, 130, 246, 0.12);
  box-shadow: 0 18px 38px rgba(15, 23, 42, 0.1);
}

.resource-card:focus-visible {
  outline: 2px solid rgba(59, 130, 246, 0.45);
  outline-offset: 2px;
}

.resource-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  padding: 18px;
}

.resource-body h3 {
  font-size: 18px;
  line-height: 1.4;
  margin: 0 0 8px;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  min-height: 50px;
}

.resource-body p {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  min-height: 48px;
  margin: 0 0 12px;
  color: var(--v2-text-secondary);
  line-height: 1.7;
}

.resource-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.resource-meta {
  flex-wrap: wrap;
  align-items: flex-start;
  color: var(--v2-text-secondary);
  font-size: 12px;
  margin-bottom: 8px;
}

.resource-meta span {
  flex: 1 1 120px;
}

.resource-tags {
  margin-bottom: 12px;
}

.resource-actions {
  display: flex;
  gap: 8px;
  margin-top: auto;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .page-header,
  .resource-meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .resource-actions {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
