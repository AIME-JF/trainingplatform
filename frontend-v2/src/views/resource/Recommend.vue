<template>
  <div
    class="page-content community-page resource-page"
    @touchstart.capture="onTouchStart"
    @touchmove.capture="onTouchMove"
    @touchend.capture="onTouchEnd"
  >
    <LearningResourceTabs />

    <div class="community-header">
      <div>
        <h1 class="page-title">资源社区</h1>
        <p class="page-subtitle">
          按推荐流连续浏览优先资源。
          <span v-if="isMobile">移动端支持上下滑切换资源。</span>
        </p>
      </div>
      <a-space>
        <a-button @click="router.push('/resource/library')">资源库</a-button>
        <a-button v-if="!isMobile" @click="prevRecommendation">上一个</a-button>
        <a-button v-if="!isMobile" type="primary" @click="nextRecommendation">下一个</a-button>
      </a-space>
    </div>

    <div class="community-shell">
      <a-spin :spinning="loadingResource || loadingFeed" class="community-spin">
        <a-empty v-if="!currentResource && !loadingResource" description="暂无社区内容" class="community-empty" />
        <template v-else-if="currentResource">
          <div class="community-viewer">
            <ResourceViewer
              :resource="currentResource"
              mode="recommend"
              @click="recordCurrentEvent('click')"
              @play="recordCurrentEvent('play')"
              @complete="recordCurrentEvent('complete')"
            />
          </div>

          <div v-if="!isMobile" class="community-footer">
            <div class="community-footer-meta">
              <span>{{ currentIndex + 1 }} / {{ feedItems.length }}</span>
              <span v-if="currentFeedItem">推荐分 {{ formatScore(currentFeedItem.score) }}</span>
              <span>{{ currentResource.uploader_name || '平台资源' }}</span>
            </div>
            <a-space>
              <a-button @click="prevRecommendation">上一个</a-button>
              <a-button type="primary" @click="goDetail">查看详情</a-button>
              <a-button @click="nextRecommendation">下一个</a-button>
            </a-space>
          </div>
        </template>
      </a-spin>
    </div>

    <div v-if="currentResource && isMobile" class="community-mobile-actions">
      <div class="community-index">
        <span>{{ currentIndex + 1 }} / {{ feedItems.length }}</span>
        <span v-if="currentFeedItem">推荐分 {{ formatScore(currentFeedItem.score) }}</span>
      </div>
      <a-button type="primary" @click="goDetail">查看详情</a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { ResourceDetailResponse, ResourceRecommendationItem } from '@/api/learning-resource'
import { getResourceDetail, listRecommendationFeed, recordResourceEvent } from '@/api/learning-resource'
import { useMobile } from '@/composables/useMobile'
import LearningResourceTabs from '@/components/resource/LearningResourceTabs.vue'
import ResourceViewer from '@/components/resource/ResourceViewer.vue'

const PAGE_SIZE = 10

const router = useRouter()
const { isMobile } = useMobile()

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
const gesture = ref({
  startX: 0,
  startY: 0,
  axis: '',
  triggered: false,
  ignore: false,
})

const currentFeedItem = computed(() => feedItems.value[currentIndex.value] || null)

onMounted(() => {
  void fetchFeedPage(1)
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
  if (loadingFeed.value || feedFinished.value || page <= 0) {
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
    message.error(error instanceof Error ? error.message : '加载社区内容失败')
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
    message.info('已没有更多资源')
  }
}

function prevRecommendation() {
  if (!feedItems.value.length) {
    return
  }
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

function goDetail() {
  if (!currentResource.value?.id) {
    return
  }
  router.push({
    path: `/resource/detail/${currentResource.value.id}`,
    query: { from: 'community' },
  })
}

function formatScore(score?: number | null) {
  if (typeof score !== 'number' || Number.isNaN(score)) {
    return '-'
  }
  return score.toFixed(2)
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

function onTouchStart(event: TouchEvent) {
  if (!isMobile.value) {
    return
  }

  const target = event.target
  const ignore = target instanceof Element && !!target.closest('.community-mobile-actions .ant-btn')
  const touch = event.touches?.[0]
  if (!touch) {
    return
  }

  gesture.value = {
    startX: touch.clientX,
    startY: touch.clientY,
    axis: '',
    triggered: false,
    ignore,
  }
}

function onTouchMove(event: TouchEvent) {
  if (!isMobile.value || gesture.value.ignore || gesture.value.triggered) {
    return
  }

  const touch = event.touches?.[0]
  if (!touch) {
    return
  }

  const deltaX = touch.clientX - gesture.value.startX
  const deltaY = touch.clientY - gesture.value.startY
  const absX = Math.abs(deltaX)
  const absY = Math.abs(deltaY)

  if (!gesture.value.axis && (absX > 12 || absY > 12)) {
    gesture.value.axis = absY > absX ? 'y' : 'x'
  }

  if (gesture.value.axis === 'y' && event.cancelable) {
    event.preventDefault()
  }
}

function onTouchEnd(event: TouchEvent) {
  if (!isMobile.value || gesture.value.ignore || gesture.value.axis !== 'y' || gesture.value.triggered) {
    return
  }

  const touch = event.changedTouches?.[0]
  if (!touch) {
    return
  }

  const deltaX = touch.clientX - gesture.value.startX
  const deltaY = touch.clientY - gesture.value.startY
  if (Math.abs(deltaY) <= Math.abs(deltaX)) {
    return
  }

  if (deltaY < -80) {
    gesture.value.triggered = true
    void nextRecommendation()
    return
  }

  if (deltaY > 80) {
    gesture.value.triggered = true
    prevRecommendation()
  }
}
</script>

<style scoped>
.community-page {
  min-height: 100vh;
}

.community-header {
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

.community-shell {
  position: relative;
}

.community-spin,
.community-spin :deep(.ant-spin-nested-loading),
.community-spin :deep(.ant-spin-container) {
  display: block;
  min-height: calc(100vh - 260px);
}

.community-empty {
  padding: 80px 0;
}

.community-viewer {
  overflow: hidden;
  border-radius: 28px;
  background: #000;
  box-shadow: 0 28px 60px rgba(10, 21, 66, 0.24);
}

.community-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 16px;
}

.community-footer-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.community-mobile-actions {
  position: sticky;
  bottom: 10px;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(8, 15, 38, 0.78);
  backdrop-filter: blur(12px);
}

.community-index {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: #fff;
  font-size: 13px;
}

@media (max-width: 768px) {
  .community-header,
  .community-footer {
    flex-direction: column;
    align-items: flex-start;
  }

  .community-spin,
  .community-spin :deep(.ant-spin-nested-loading),
  .community-spin :deep(.ant-spin-container) {
    min-height: calc(100vh - 300px);
  }

  .community-viewer {
    border-radius: 24px;
  }
}
</style>
