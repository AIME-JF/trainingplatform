<template>
  <div class="page-content recommend-page resource-page">
    <LearningResourceTabs />

    <div class="recommend-header">
      <div>
        <h1 class="page-title">资源推荐</h1>
        <p class="page-subtitle">根据你的学习画像推荐可优先浏览的资源。</p>
      </div>
      <a-space>
        <a-button @click="router.push('/resource/library')">资源库</a-button>
        <a-button @click="prevRecommendation">上一个</a-button>
        <a-button type="primary" @click="nextRecommendation">下一个</a-button>
      </a-space>
    </div>

    <a-spin :spinning="loadingResource || loadingFeed" class="recommend-spin">
      <a-empty v-if="!currentResource && !loadingResource" description="暂无推荐内容" />
      <template v-else-if="currentResource">
        <ResourceViewer
          :resource="currentResource"
          mode="recommend"
          @click="recordCurrentEvent('click')"
          @play="recordCurrentEvent('play')"
          @complete="recordCurrentEvent('complete')"
        />
        <div class="recommend-footer">
          <span>{{ currentIndex + 1 }} / {{ feedItems.length }}</span>
          <a-button @click="router.push(`/resource/detail/${currentResource.id}`)">查看详情</a-button>
        </div>
      </template>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { ResourceDetailResponse, ResourceRecommendationItem } from '@/api/learning-resource'
import { getResourceDetail, listRecommendationFeed, recordResourceEvent } from '@/api/learning-resource'
import LearningResourceTabs from '@/components/resource/LearningResourceTabs.vue'
import ResourceViewer from '@/components/resource/ResourceViewer.vue'

const router = useRouter()

const PAGE_SIZE = 10
const feedItems = ref<ResourceRecommendationItem[]>([])
const currentIndex = ref(0)
const currentPage = ref(0)
const total = ref(0)
const feedFinished = ref(false)
const loadingFeed = ref(false)
const loadingResource = ref(false)
const currentResource = ref<ResourceDetailResponse | null>(null)
const resourceCache = new Map<number, ResourceDetailResponse>()
const impressionRecorded = new Set<number>()

const currentFeedItem = computed(() => feedItems.value[currentIndex.value] || null)

onMounted(async () => {
  await fetchFeedPage(1)
})

watch(() => currentFeedItem.value?.resource_id, async (resourceId) => {
  if (!resourceId) {
    currentResource.value = null
    return
  }
  await loadCurrentResource(resourceId)
  await recordImpression(resourceId)
  void maybePreloadNextPage()
}, { immediate: true })

async function fetchFeedPage(page: number) {
  if (loadingFeed.value || feedFinished.value) {
    return
  }
  loadingFeed.value = true
  try {
    const response = await listRecommendationFeed({ page, size: PAGE_SIZE })
    const items = response.items || []
    total.value = response.total || 0
    const existingIds = new Set(feedItems.value.map((item) => item.resource_id))
    const newItems = items.filter((item) => !existingIds.has(item.resource_id))
    feedItems.value.push(...newItems)
    currentPage.value = page
    if (!items.length || (total.value > 0 && feedItems.value.length >= total.value)) {
      feedFinished.value = true
    }
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载推荐失败')
  } finally {
    loadingFeed.value = false
  }
}

async function loadCurrentResource(resourceId: number) {
  loadingResource.value = true
  try {
    if (!resourceCache.has(resourceId)) {
      const detail = await getResourceDetail(resourceId)
      resourceCache.set(resourceId, detail)
    }
    currentResource.value = resourceCache.get(resourceId) || null
  } catch (error) {
    currentResource.value = null
    message.error(error instanceof Error ? error.message : '加载资源详情失败')
  } finally {
    loadingResource.value = false
  }
}

async function nextRecommendation() {
  if (!feedItems.value.length) {
    return
  }
  if (currentIndex.value < feedItems.value.length - 1) {
    currentIndex.value += 1
    return
  }
  await fetchFeedPage(currentPage.value + 1)
  if (currentIndex.value < feedItems.value.length - 1) {
    currentIndex.value += 1
  } else {
    message.info('已没有更多推荐')
  }
}

function prevRecommendation() {
  if (currentIndex.value > 0) {
    currentIndex.value -= 1
  }
}

function maybePreloadNextPage() {
  if (feedFinished.value || loadingFeed.value) {
    return
  }
  if (feedItems.value.length - currentIndex.value <= 3) {
    void fetchFeedPage(currentPage.value + 1)
  }
}

async function recordImpression(resourceId: number) {
  if (impressionRecorded.has(resourceId)) {
    return
  }
  impressionRecorded.add(resourceId)
  try {
    await recordResourceEvent(resourceId, 'impression')
  } catch {
    // ignore
  }
}

async function recordCurrentEvent(eventType: string) {
  if (!currentResource.value?.id) {
    return
  }
  try {
    await recordResourceEvent(currentResource.value.id, eventType)
  } catch {
    // ignore
  }
}
</script>

<style scoped>
.recommend-page {
  min-height: 100vh;
}

.recommend-header {
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

.recommend-spin {
  display: block;
}

.recommend-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
}

@media (max-width: 768px) {
  .recommend-header,
  .recommend-footer {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
