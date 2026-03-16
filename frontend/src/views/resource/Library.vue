<template>
  <div class="resource-library-page">
    <div class="page-header">
      <h2>资源库</h2>
      <a-space>
        <a-button @click="$router.push('/resource/my')">我的资源</a-button>
        <permissions-tooltip
          v-if="!authStore.isStudent"
          :allowed="canUploadResource"
          tips="需要 CREATE_RESOURCE 或 VIEW_RESOURCE_ALL 权限"
          v-slot="{ disabled }"
        >
          <a-button type="primary" :disabled="disabled" @click="$router.push('/resource/upload')">上传资源</a-button>
        </permissions-tooltip>
      </a-space>
    </div>

    <a-card :bordered="false" style="margin-bottom:16px">
      <a-row :gutter="12">
        <a-col :span="8">
          <a-input-search v-model:value="query.search" placeholder="搜索资源标题" @search="fetchResources" />
        </a-col>
        <a-col :span="6">
          <a-select v-model:value="query.contentType" style="width:100%" @change="fetchResources">
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="video">视频</a-select-option>
            <a-select-option value="document">文档</a-select-option>
            <a-select-option value="image">图片</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select v-model:value="query.status" style="width:100%" @change="fetchResources">
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="published">已发布</a-select-option>
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="pending_review">待审核</a-select-option>
            <a-select-option value="reviewing">审核中</a-select-option>
            <a-select-option value="rejected">已驳回</a-select-option>
            <a-select-option value="offline">已下线</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <a-row :gutter="16">
      <a-col :span="8" v-for="item in resources" :key="item.id">
        <a-card class="resource-card" :bordered="false" style="margin-bottom:16px">
          <template #title>
            <div class="title-line">
              <span class="title-text">{{ item.title }}</span>
              <a-tag>{{ statusLabel(item.status) }}</a-tag>
            </div>
          </template>
          <p class="summary">{{ item.summary || '暂无摘要' }}</p>
          <div class="meta">类型：{{ contentTypeLabel(item.contentType) }} · 上传者：{{ item.uploaderName || '-' }}</div>
          <div class="meta">标签：{{ (item.tags || []).join(' / ') || '-' }}</div>
          <div class="actions">
            <a-space>
              <a-button size="small" @click="goDetail(item.id)">查看</a-button>
              <permissions-tooltip
                v-if="showPublish(item)"
                :allowed="canPublish(item)"
                tips="仅资源上传者或具备 UPDATE_RESOURCE / VIEW_RESOURCE_ALL 权限可执行该操作"
                v-slot="{ disabled }"
              >
                <a-button size="small" type="primary" ghost :disabled="disabled" @click="publish(item.id)">发布</a-button>
              </permissions-tooltip>
              <permissions-tooltip
                v-if="showOffline(item)"
                :allowed="canOffline(item)"
                tips="仅资源上传者或具备 UPDATE_RESOURCE / VIEW_RESOURCE_ALL 权限可执行该操作"
                v-slot="{ disabled }"
              >
                <a-button size="small" danger ghost :disabled="disabled" @click="offline(item.id)">下线</a-button>
              </permissions-tooltip>
            </a-space>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-pagination
      :current="query.page"
      :page-size="query.size"
      :total="total"
      show-size-changer
      :page-size-options="['10','20','50']"
      @change="onPageChange"
      @showSizeChange="onSizeChange"
    />
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getResources, publishResource, offlineResource } from '@/api/resource'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

const router = useRouter()
const authStore = useAuthStore()

const query = reactive({ page: 1, size: 10, search: '', status: '', contentType: '' })
const resources = ref([])
const total = ref(0)
const canUploadResource = computed(() => authStore.hasAnyPermission(['CREATE_RESOURCE', 'VIEW_RESOURCE_ALL']))
const canManageAnyResource = computed(() => authStore.hasAnyPermission(['UPDATE_RESOURCE', 'VIEW_RESOURCE_ALL']))

onMounted(async () => {
  await fetchResources()
})

function statusLabel(status) {
  const map = {
    draft: '草稿', pendingReview: '待审核', pending_review: '待审核', reviewing: '审核中',
    published: '已发布', rejected: '已驳回', offline: '已下线'
  }
  return map[status] || status
}

function contentTypeLabel(type) {
  const map = {
    video: '视频',
    image: '图片',
    image_text: '图片',
    document: '文档',
  }
  return map[type] || type || '-'
}

async function fetchResources() {
  try {
    const res = await getResources(query)
    resources.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    message.error(e.message || '加载资源失败')
  }
}

function canEditResource(item) {
  return item?.uploaderId === authStore.currentUser?.id || canManageAnyResource.value
}

function showPublish(item) {
  return ['draft', 'rejected', 'offline'].includes(item.status)
}

function showOffline(item) {
  return item.status === 'published'
}

function canPublish(item) {
  return showPublish(item) && canEditResource(item)
}

function canOffline(item) {
  return showOffline(item) && canEditResource(item)
}

async function publish(id) {
  const item = resources.value.find((resource) => resource.id === id)
  if (item && !canPublish(item)) return
  try {
    await publishResource(id)
    message.success('发布成功')
    fetchResources()
  } catch (e) {
    message.error(e.message || '发布失败')
  }
}

async function offline(id) {
  const item = resources.value.find((resource) => resource.id === id)
  if (item && !canOffline(item)) return
  try {
    await offlineResource(id)
    message.success('下线成功')
    fetchResources()
  } catch (e) {
    message.error(e.message || '下线失败')
  }
}

function goDetail(id) {
  router.push(`/resource/detail/${id}`)
}

function onPageChange(page, size) {
  query.page = page
  query.size = size
  fetchResources()
}

function onSizeChange(_, size) {
  query.page = 1
  query.size = size
  fetchResources()
}
</script>

<style scoped>
.resource-library-page { padding: 0; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.title-line { display:flex; justify-content:space-between; align-items:center; gap:8px; }
.title-text { font-weight:600; }
.summary { color:#666; min-height:40px; }
.meta { font-size:12px; color:#888; margin-bottom:6px; }
.actions { margin-top:10px; }
</style>
