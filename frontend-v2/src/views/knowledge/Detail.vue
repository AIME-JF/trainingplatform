<template>
  <div class="page-content resource-page detail-shell" :class="{ 'featured-detail-page': isFeaturedDetail }">
    <div class="detail-actions">
      <template v-if="isFeaturedDetail">
        <a-button class="detail-back-btn" @click="router.push('/resource/library')">返回</a-button>
      </template>
      <template v-else>
        <a-button @click="router.push('/resource/community')">返回推荐</a-button>
        <a-button @click="router.push('/resource/library')">返回精选</a-button>
        <a-button @click="router.push('/resource/my')">我的空间</a-button>
      </template>
    </div>

    <a-spin v-if="loading" size="large" class="loading-block" />
    <a-empty v-else-if="!resource" description="资源不存在或无权限查看" class="loading-block" />

    <div v-else class="detail-stack">
      <ResourceViewer
        :resource="resource"
        :autoplay="isFeaturedDetail"
        :compact="isFeaturedDetail"
        :theme="isFeaturedDetail ? 'dark' : 'default'"
        @click="recordEvent('click')"
        @play="recordEvent('play')"
        @complete="recordEvent('complete')"
      >
        <template #actions>
          <ResourceActionBar
            :liked="!!resource.current_user_liked"
            :like-count="resource.like_count"
            :comment-count="resource.comment_count"
            :share-count="resource.share_count"
            :liking="liking"
            :sharing="sharing"
            :theme="isFeaturedDetail ? 'dark' : 'default'"
            @like="handleToggleLike"
            @comment="openComments"
            @share="handleShare"
          />
        </template>
      </ResourceViewer>

      <a-card :bordered="false" class="detail-card" :class="{ dark: isFeaturedDetail }">
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
    </div>

    <ResourceCommentsDrawer
      v-model:open="commentDrawerOpen"
      v-model:draft="commentDraft"
      :resource-title="resource?.title"
      :comment-count="resource?.comment_count || comments.length"
      :comments="comments"
      :loading="commentLoading"
      :submitting="commentSubmitting"
      @submit="handleSubmitComment"
      @delete="handleDeleteComment"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { ResourceBehaviorEventCreateEventType, ResourceDetailResponse } from '@/api/learning-resource'
import { getResourceDetail, recordResourceEvent } from '@/api/learning-resource'
import ResourceActionBar from '@/components/knowledge/ResourceActionBar.vue'
import ResourceCommentsDrawer from '@/components/knowledge/ResourceCommentsDrawer.vue'
import ResourceViewer from '@/components/knowledge/ResourceViewer.vue'
import { useMobile } from '@/composables/useMobile'
import { useResourceInteractions } from '@/composables/useResourceInteractions'
import {
  formatDateTime,
  formatTagList,
  getResourceContentTypeLabel,
  getResourceStatusLabel,
  getScopeTypeLabel,
} from '@/utils/learning-resource'

const route = useRoute()
const router = useRouter()
const { isMobile } = useMobile()
const loading = ref(false)
const resource = ref<ResourceDetailResponse | null>(null)
const isFeaturedDetail = computed(() => String(route.query.from || '') === 'featured')
const {
  liking,
  sharing,
  commentDrawerOpen,
  commentLoading,
  commentSubmitting,
  comments,
  commentDraft,
  handleToggleLike,
  handleShare,
  openComments,
  handleSubmitComment,
  handleDeleteComment,
} = useResourceInteractions({
  resource,
  isMobile,
  patchResource,
})

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

async function recordEvent(eventType: ResourceBehaviorEventCreateEventType) {
  if (!resource.value?.id) {
    return
  }
  try {
    await recordResourceEvent(resource.value.id, eventType)
  } catch {
    // ignore
  }
}

function patchResource(resourceId: number, patch: Partial<ResourceDetailResponse>) {
  if (resource.value?.id !== resourceId) {
    return
  }
  resource.value = { ...resource.value, ...patch }
}
</script>

<style scoped>
.detail-shell {
  min-height: 100vh;
}

.detail-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.detail-back-btn {
  min-width: 92px;
}

.loading-block {
  display: block;
  padding: 80px 0;
  text-align: center;
}

.detail-card {
  border-radius: var(--v2-radius-lg);
}

.featured-detail-page {
  background:
    radial-gradient(circle at top center, rgba(46, 46, 46, 0.34), transparent 24%),
    linear-gradient(180deg, #060606 0%, #0b0b0c 36%, #040404 100%);
  color: #fff;
}

.featured-detail-page .detail-stack {
  gap: 10px;
}

.featured-detail-page .detail-actions {
  margin-bottom: 12px !important;
}

.featured-detail-page .detail-back-btn {
  border-color: rgba(255, 255, 255, 0.12) !important;
  background: rgba(255, 255, 255, 0.06) !important;
  color: rgba(255, 255, 255, 0.96) !important;
  box-shadow: none !important;
}

.featured-detail-page .detail-back-btn:hover,
.featured-detail-page .detail-back-btn:focus {
  border-color: rgba(255, 255, 255, 0.18) !important;
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
}

.featured-detail-page .loading-block {
  color: rgba(255, 255, 255, 0.72);
}

.featured-detail-page :deep(.ant-empty-description) {
  color: rgba(255, 255, 255, 0.58);
}

.featured-detail-page :deep(.detail-card.ant-card) {
  background: linear-gradient(180deg, rgba(18, 18, 20, 0.96) 0%, rgba(10, 10, 11, 0.94) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 20px 42px rgba(0, 0, 0, 0.28) !important;
}

.featured-detail-page :deep(.detail-card .ant-card-body) {
  padding: 18px !important;
}

.featured-detail-page :deep(.ant-descriptions-item-label) {
  color: rgba(255, 255, 255, 0.58) !important;
}

.featured-detail-page :deep(.ant-descriptions-item-content) {
  color: rgba(255, 255, 255, 0.92) !important;
}

@media (max-width: 768px) {
  .featured-detail-page {
    padding-top: 12px;
    padding-bottom: calc(var(--v2-bottomnav-height) + 10px);
  }

  .featured-detail-page .detail-actions {
    margin-bottom: 10px !important;
  }

  .featured-detail-page :deep(.detail-card .ant-card-body) {
    padding: 14px !important;
  }
}
</style>
