<template>
  <div class="resource-library-page">
    <div class="page-header">
      <h2>资源库</h2>
      <a-space>
        <a-button @click="$router.push('/resource/my')">我的空间</a-button>
        <permissions-tooltip
          v-if="!isStudentOnly"
          :allowed="canUploadResource"
          tips="需要 CREATE_RESOURCE 或 VIEW_RESOURCE_ALL 权限"
          v-slot="{ disabled }"
        >
          <a-button type="primary" :disabled="disabled" @click="uploadModalOpen = true">上传资源</a-button>
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
      </a-row>
    </a-card>

    <a-row :gutter="16">
      <a-col :span="8" v-for="item in resources" :key="item.id">
        <a-card
          class="resource-card"
          :bordered="false"
          style="margin-bottom:16px"
          role="link"
          tabindex="0"
          @click="goDetail(item.id)"
          @keydown.enter.prevent="goDetail(item.id)"
          @keydown.space.prevent="goDetail(item.id)"
        >
          <template #title>
            <div class="title-line">
              <span class="title-text">{{ item.title }}</span>
            </div>
          </template>
          <p class="summary">{{ item.summary || '暂无摘要' }}</p>
          <div class="meta">类型：{{ contentTypeLabel(item.contentType) }} · 上传者：{{ item.uploaderName || '-' }}</div>
          <div class="meta">标签：{{ (item.tags || []).join(' / ') || '-' }}</div>
          <div v-if="canManage(item)" class="actions" @click.stop>
            <permissions-tooltip
              v-if="item.status === 'published'"
              :allowed="canManage(item)"
              tips="仅资源上传者或具备 UPDATE_RESOURCE / VIEW_RESOURCE_ALL 权限可执行该操作"
              v-slot="{ disabled }"
            >
              <a-button size="small" danger ghost :disabled="disabled" @click="offline(item.id)">下线</a-button>
            </permissions-tooltip>
            <permissions-tooltip
              :allowed="canManage(item)"
              tips="仅资源上传者或具备 UPDATE_RESOURCE / VIEW_RESOURCE_ALL 权限可执行该操作"
              v-slot="{ disabled }"
            >
              <a-popconfirm
                v-if="!disabled"
                title="确认删除该资源吗？"
                ok-text="删除"
                cancel-text="取消"
                @confirm="removeResource(item.id)"
              >
                <a-button size="small" danger>删除</a-button>
              </a-popconfirm>
              <a-button v-else size="small" danger :disabled="disabled">删除</a-button>
            </permissions-tooltip>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-empty v-if="!resources.length && !loading" description="暂无已发布的资源" />

    <a-pagination
      v-if="total > 0"
      :current="query.page"
      :page-size="query.size"
      :total="total"
      show-size-changer
      :page-size-options="['10','20','50']"
      @change="onPageChange"
      @showSizeChange="onSizeChange"
    />

    <resource-upload-modal v-model:open="uploadModalOpen" @success="handleUploadSuccess" />
  </div>
</template>

<script setup>
import { computed, ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getResources, offlineResource, deleteResource } from '@/api/resource'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'
import ResourceUploadModal from './components/ResourceUploadModal.vue'

const router = useRouter()
const authStore = useAuthStore()

const query = reactive({ page: 1, size: 10, search: '', contentType: '' })
const resources = ref([])
const total = ref(0)
const loading = ref(false)
const uploadModalOpen = ref(false)
const canUploadResource = computed(() => authStore.hasAnyPermission(['CREATE_RESOURCE', 'VIEW_RESOURCE_ALL']))
const canManageAnyResource = computed(() => authStore.hasAnyPermission(['UPDATE_RESOURCE', 'VIEW_RESOURCE_ALL']))
const isStudentOnly = computed(() => {
  const roleCodes = (authStore.currentUser?.roleCodes || []).length
    ? authStore.currentUser.roleCodes
    : [authStore.role].filter(Boolean)
  return roleCodes.length > 0 && roleCodes.every((code) => code === 'student')
})

onMounted(async () => {
  await fetchResources()
})

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
  loading.value = true
  try {
    const res = await getResources({ ...query, status: 'published' })
    resources.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    message.error(e.message || '加载资源失败')
  } finally {
    loading.value = false
  }
}

function canManage(item) {
  if (isStudentOnly.value) return false
  return item?.uploaderId === authStore.currentUser?.id || canManageAnyResource.value
}

async function offline(id) {
  try {
    await offlineResource(id)
    message.success('下线成功')
    fetchResources()
  } catch (e) {
    message.error(e.message || '下线失败')
  }
}

async function removeResource(id) {
  try {
    await deleteResource(id)
    message.success('删除成功')
    fetchResources()
  } catch (e) {
    message.error(e.message || '删除失败')
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

function handleUploadSuccess() {
  query.page = 1
  fetchResources()
}
</script>

<style scoped>
.resource-library-page { padding: 0; }
.page-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.resource-card { cursor:pointer; }
.resource-card:focus-visible { outline:2px solid rgba(22, 119, 255, 0.45); outline-offset:2px; }
.title-line { display:flex; justify-content:space-between; align-items:center; gap:8px; }
.title-text { font-weight:600; }
.summary { color:#666; min-height:40px; }
.meta { font-size:12px; color:#888; margin-bottom:6px; }
.actions { margin-top:10px; display:flex; gap:8px; flex-wrap:wrap; }
</style>
