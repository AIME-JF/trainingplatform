<template>
  <div class="resource-detail-page">
    <div class="page-header">
      <div>
        <h2>资源详情</h2>
        <p class="header-subtitle">左侧查看资源，右侧查看资源信息</p>
      </div>
      <a-space>
        <a-button @click="$router.push('/resource/recommend')">返回推荐</a-button>
        <a-button @click="$router.push('/resource/library')">返回资源库</a-button>
      </a-space>
    </div>

    <a-spin :spinning="loading" class="detail-spin">
      <a-empty v-if="!resource && !loading" description="资源不存在或无访问权限" />

      <div v-else-if="resource" class="detail-layout">
        <section class="detail-main">
          <ResourceViewer
            mode="detail"
            :media-only="true"
            :resource="resource"
            @click="recordCurrentEvent('click')"
            @play="recordCurrentEvent('play')"
            @complete="recordCurrentEvent('complete')"
          />
        </section>

        <aside class="detail-side">
          <a-card :bordered="false" class="info-card">
            <h3 class="side-title">资源信息</h3>

            <div class="info-item">
              <span class="label">标题</span>
              <p class="value strong">{{ resource.title || '-' }}</p>
            </div>

            <div class="info-item two-col">
              <div>
                <span class="label">类型</span>
                <p class="value">{{ contentTypeLabel(resource.contentType) }}</p>
              </div>
              <div>
                <span class="label">状态</span>
                <p class="value">{{ statusLabel(resource.status) }}</p>
              </div>
            </div>

            <div class="info-item two-col">
              <div>
                <span class="label">上传者</span>
                <p class="value">{{ resource.uploaderName || '-' }}</p>
              </div>
              <div>
                <span class="label">部门</span>
                <p class="value">{{ resource.ownerDepartmentName || '-' }}</p>
              </div>
            </div>

            <div class="info-item">
              <span class="label">可见范围</span>
              <p class="value">{{ visibilityLabel(resource.visibilityType) }}</p>
            </div>

            <div class="info-item">
              <span class="label">标签</span>
              <div class="tags" v-if="resource.tags?.length">
                <a-tag v-for="tag in resource.tags" :key="tag" color="blue">{{ tag }}</a-tag>
              </div>
              <p v-else class="value">-</p>
            </div>

            <div class="info-item">
              <span class="label">摘要</span>
              <p class="value text-block">{{ resource.summary || '暂无摘要' }}</p>
            </div>

            <div class="info-item two-col">
              <div>
                <span class="label">创建时间</span>
                <p class="value">{{ formatDateTime(resource.createdAt) }}</p>
              </div>
              <div>
                <span class="label">更新时间</span>
                <p class="value">{{ formatDateTime(resource.updatedAt) }}</p>
              </div>
            </div>
          </a-card>
        </aside>
      </div>
    </a-spin>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { onMounted, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useRoute } from 'vue-router'
import { getResource } from '@/api/resource'
import { recordResourceEvent } from '@/api/recommendation'
import ResourceViewer from './components/ResourceViewer.vue'

const route = useRoute()
const loading = ref(false)
const resource = ref(null)

onMounted(() => {
  fetchResource()
})

watch(
  () => route.params.id,
  () => fetchResource()
)

function contentTypeLabel(contentType) {
  const map = {
    video: '视频',
    document: '文档',
    image_text: '图文',
  }
  return map[contentType] || contentType || '-'
}

function statusLabel(status) {
  const map = {
    draft: '草稿',
    pending_review: '待审核',
    reviewing: '审核中',
    published: '已发布',
    rejected: '已驳回',
    offline: '已下线',
  }
  return map[status] || status || '-'
}

function visibilityLabel(type) {
  const map = {
    public: '全员可见',
    department: '部门可见',
    police_type: '警种可见',
    custom: '自定义范围',
  }
  return map[type] || type || '-'
}

function formatDateTime(value) {
  if (!value) return '-'
  return dayjs(value).format('YYYY-MM-DD HH:mm')
}

async function fetchResource() {
  const id = Number(route.params.id)
  if (!id) {
    resource.value = null
    return
  }

  loading.value = true
  try {
    resource.value = await getResource(id)
  } catch (e) {
    resource.value = null
    message.error(e.message || '加载资源失败')
  } finally {
    loading.value = false
  }
}

async function recordCurrentEvent(eventType) {
  if (!resource.value?.id) return
  try {
    await recordResourceEvent(resource.value.id, { eventType })
  } catch {
    // ignore
  }
}
</script>

<style scoped>
.resource-detail-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-subtitle {
  margin-top: 4px;
  color: #8c8c8c;
  font-size: 13px;
}

.detail-spin :deep(.ant-spin-container) {
  min-height: 420px;
}

.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: start;
}

.detail-main {
  min-width: 0;
}

.detail-side {
  position: sticky;
  top: 76px;
}

.info-card {
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 48, 135, 0.08);
}

.side-title {
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2a44;
}

.info-item {
  margin-bottom: 14px;
}

.info-item:last-child {
  margin-bottom: 0;
}

.info-item.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.label {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  color: #8c8c8c;
}

.value {
  margin: 0;
  color: #2f3b52;
  font-size: 13px;
  line-height: 1.5;
}

.value.strong {
  font-weight: 600;
  color: #1a2438;
}

.text-block {
  white-space: pre-wrap;
  word-break: break-word;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

@media (max-width: 1024px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }

  .detail-side {
    position: static;
  }
}
</style>
