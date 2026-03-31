<template>
  <div class="page-content">
    <div class="detail-actions">
      <a-button @click="router.push('/resource/library')">返回资源库</a-button>
      <a-button @click="router.push('/resource/my')">我的资源</a-button>
    </div>

    <a-spin v-if="loading" size="large" class="loading-block" />
    <a-empty v-else-if="!resource" description="资源不存在或无权限查看" class="loading-block" />

    <template v-else>
      <ResourceViewer
        :resource="resource"
        @click="recordEvent('click')"
        @play="recordEvent('play')"
        @complete="recordEvent('complete')"
      />

      <a-card :bordered="false" class="detail-card">
        <a-descriptions :column="{ xs: 1, md: 2 }" size="small">
          <a-descriptions-item label="内容类型">{{ getResourceContentTypeLabel(resource.content_type) }}</a-descriptions-item>
          <a-descriptions-item label="上传者">{{ resource.uploader_name || '-' }}</a-descriptions-item>
          <a-descriptions-item label="可见范围">{{ resource.scope || getScopeTypeLabel(resource.scope_type || resource.visibility_type) }}</a-descriptions-item>
          <a-descriptions-item label="状态">{{ getResourceStatusLabel(resource.status) }}</a-descriptions-item>
          <a-descriptions-item label="创建时间">{{ formatDateTime(resource.created_at) }}</a-descriptions-item>
          <a-descriptions-item label="更新时间">{{ formatDateTime(resource.updated_at) }}</a-descriptions-item>
          <a-descriptions-item label="标签" :span="2">{{ formatTagList(resource.tags) }}</a-descriptions-item>
          <a-descriptions-item label="资源摘要" :span="2">{{ resource.summary || '暂无摘要' }}</a-descriptions-item>
        </a-descriptions>
      </a-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { ResourceDetailResponse } from '@/api/learning-resource'
import { getResourceDetail, recordResourceEvent } from '@/api/learning-resource'
import ResourceViewer from '@/components/resource/ResourceViewer.vue'
import {
  formatDateTime,
  formatTagList,
  getResourceContentTypeLabel,
  getResourceStatusLabel,
  getScopeTypeLabel,
} from '@/utils/learning-resource'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const resource = ref<ResourceDetailResponse | null>(null)

onMounted(() => {
  void fetchDetail()
})

async function fetchDetail() {
  const resourceId = Number(route.params.id)
  if (!resourceId) {
    return
  }
  loading.value = true
  try {
    resource.value = await getResourceDetail(resourceId)
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载资源详情失败')
  } finally {
    loading.value = false
  }
}

async function recordEvent(eventType: string) {
  if (!resource.value?.id) {
    return
  }
  try {
    await recordResourceEvent(resource.value.id, eventType)
  } catch {
    // ignore
  }
}
</script>

<style scoped>
.detail-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.loading-block {
  display: block;
  padding: 80px 0;
  text-align: center;
}

.detail-card {
  margin-top: 16px;
  border-radius: var(--v2-radius-lg);
}
</style>
