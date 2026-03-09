<template>
  <div class="resource-library-page">
    <div class="page-header">
      <h2>资源库</h2>
      <a-space>
        <a-button @click="$router.push('/resource/my')">我的资源</a-button>
        <a-button type="primary" v-if="!authStore.isStudent" @click="$router.push('/resource/upload')">上传资源</a-button>
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
            <a-select-option value="image_text">图文</a-select-option>
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
          <div class="meta">类型：{{ item.contentType }} · 上传者：{{ item.uploaderName || '-' }}</div>
          <div class="meta">标签：{{ (item.tags || []).join(' / ') || '-' }}</div>
          <div class="actions">
            <a-space>
              <a-button size="small" @click="goDetail(item.id)">查看</a-button>
              <a-button size="small" type="primary" ghost v-if="canPublish(item)" @click="publish(item.id)">发布</a-button>
              <a-button size="small" danger ghost v-if="canOffline(item)" @click="offline(item.id)">下线</a-button>
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
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getResources, publishResource, offlineResource } from '@/api/resource'

const router = useRouter()
const authStore = useAuthStore()

const query = reactive({ page: 1, size: 10, search: '', status: '', contentType: '' })
const resources = ref([])
const total = ref(0)

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

async function fetchResources() {
  try {
    const res = await getResources(query)
    resources.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    message.error(e.message || '加载资源失败')
  }
}

function canPublish(item) {
  return (authStore.isAdmin || authStore.isInstructor) && ['draft', 'rejected', 'offline'].includes(item.status)
}

function canOffline(item) {
  return (authStore.isAdmin || authStore.isInstructor) && item.status === 'published'
}

async function publish(id) {
  try {
    await publishResource(id)
    message.success('发布成功')
    fetchResources()
  } catch (e) {
    message.error(e.message || '发布失败')
  }
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
