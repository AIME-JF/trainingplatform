<template>
  <div
    class="resource-recommend-page"
    @touchstart.capture="onTouchStart"
    @touchmove.capture="onTouchMove"
    @touchend.capture="onTouchEnd"
  >
    <div class="recommend-top-actions">
      <a-button size="small" @click="$router.push('/resource/library')">{{ COMMUNITY_RESOURCE_MANAGE_TITLE }}</a-button>
      <a-button v-if="!isMobile" size="small" type="primary" @click="nextRecommendation">下一个</a-button>
    </div>

    <div class="recommend-body">
      <a-spin :spinning="loadingResource">
        <a-empty v-if="!currentResource && !loadingResource" description="暂无推荐内容" />
        <ResourceViewer
          v-else
          class="recommend-viewer"
          mode="recommend"
          :resource="currentResource"
          @click="recordCurrentEvent('click')"
          @play="recordCurrentEvent('play')"
          @complete="recordCurrentEvent('complete')"
        />
      </a-spin>
    </div>

    <div class="recommend-mobile-actions" v-if="currentResource">
      <div class="recommend-index">{{ currentIndex + 1 }} / {{ feedItems.length }}</div>
      <a-button class="action-detail" @click="goDetail">详情</a-button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { getRecommendationFeed, recordResourceEvent } from '@/api/recommendation'
import { getResource } from '@/api/resource'
import { COMMUNITY_RESOURCE_MANAGE_TITLE } from '@/constants/navigationTitles'
import ResourceViewer from './components/ResourceViewer.vue'

const router = useRouter()

const PAGE_SIZE = 10

const feedItems = ref([])
const currentIndex = ref(0)
const currentPage = ref(0)
const total = ref(0)
const feedFinished = ref(false)
const loadingFeed = ref(false)
const loadingResource = ref(false)
const currentResource = ref(null)
const isMobile = ref(window.innerWidth <= 768)

const resourceCache = new Map()
const impressionRecorded = new Set()
const gesture = ref({
  startX: 0,
  startY: 0,
  axis: '',
  triggered: false,
  ignore: false,
})

const currentFeedItem = computed(() => feedItems.value[currentIndex.value] || null)

onMounted(async () => {
  window.addEventListener('resize', onResize)
  await fetchFeedPage(1)
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})

watch(
  () => currentFeedItem.value?.resourceId,
  async (resourceId) => {
    if (!resourceId) {
      currentResource.value = null
      return
    }

    await loadCurrentResource(resourceId)
    await recordImpression(resourceId)
    maybePreloadNextPage()
  },
  { immediate: true }
)

function onResize() {
  isMobile.value = window.innerWidth <= 768
}

async function fetchFeedPage(page) {
  if (loadingFeed.value || feedFinished.value) return
  loadingFeed.value = true
  try {
    const res = await getRecommendationFeed({ page, size: PAGE_SIZE })
    const items = res.items || []
    total.value = res.total || 0

    const existingIds = new Set(feedItems.value.map((item) => item.resourceId))
    const newItems = items.filter((item) => !existingIds.has(item.resourceId))
    feedItems.value.push(...newItems)

    currentPage.value = page
    if (!items.length || (total.value > 0 && feedItems.value.length >= total.value)) {
      feedFinished.value = true
    }
  } catch (e) {
    message.error(e.message || '加载推荐失败')
  } finally {
    loadingFeed.value = false
  }
}

async function loadCurrentResource(resourceId) {
  loadingResource.value = true
  try {
    if (!resourceCache.has(resourceId)) {
      const detail = await getResource(resourceId)
      resourceCache.set(resourceId, detail)
    }
    currentResource.value = resourceCache.get(resourceId) || null
  } catch (e) {
    currentResource.value = null
    message.error(e.message || '加载资源详情失败')
  } finally {
    loadingResource.value = false
  }
}

async function nextRecommendation() {
  if (!feedItems.value.length) return

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
  if (!feedItems.value.length) return
  if (currentIndex.value > 0) {
    currentIndex.value -= 1
  }
}

function maybePreloadNextPage() {
  if (feedFinished.value || loadingFeed.value) return
  if (feedItems.value.length - currentIndex.value <= 3) {
    fetchFeedPage(currentPage.value + 1)
  }
}

function goDetail() {
  if (!currentResource.value?.id) return
  router.push(`/resource/detail/${currentResource.value.id}`)
}

async function recordImpression(resourceId) {
  if (impressionRecorded.has(resourceId)) return
  impressionRecorded.add(resourceId)
  try {
    await recordResourceEvent(resourceId, { eventType: 'impression' })
  } catch {
    // ignore
  }
}

async function recordCurrentEvent(eventType) {
  if (!currentResource.value?.id) return
  try {
    await recordResourceEvent(currentResource.value.id, { eventType })
  } catch {
    // ignore
  }
}

function onTouchStart(event) {
  if (!isMobile.value) return

  const target = event.target
  const ignore = target instanceof Element && !!target.closest('.recommend-mobile-actions .ant-btn')
  const touch = event.touches?.[0]
  if (!touch) return

  gesture.value = {
    startX: touch.clientX,
    startY: touch.clientY,
    axis: '',
    triggered: false,
    ignore,
  }
}

function onTouchMove(event) {
  if (!isMobile.value || gesture.value.ignore) return

  const touch = event.touches?.[0]
  if (!touch || gesture.value.triggered) return

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

function onTouchEnd(event) {
  if (!isMobile.value || gesture.value.ignore) return
  if (gesture.value.axis !== 'y' || gesture.value.triggered) return

  const touch = event.changedTouches?.[0]
  if (!touch) return

  const deltaX = touch.clientX - gesture.value.startX
  const deltaY = touch.clientY - gesture.value.startY
  if (Math.abs(deltaY) <= Math.abs(deltaX)) return

  if (deltaY < -80) {
    gesture.value.triggered = true
    nextRecommendation()
    return
  }

  if (deltaY > 80) {
    gesture.value.triggered = true
    prevRecommendation()
  }
}
</script>

<style scoped>
.resource-recommend-page {
  --player-control-safe-offset: 56px;
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  background: #000;
  border-radius: 24px;
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.18);
  overflow: hidden;
}

.recommend-top-actions {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 35;
  display: flex;
  gap: 8px;
}

.recommend-body {
  flex: 1;
  width: 100%;
  min-height: 0;
}

.recommend-body :deep(.ant-spin),
.recommend-body :deep(.ant-spin-nested-loading),
.recommend-body :deep(.ant-spin-container) {
  width: 100%;
  height: 100%;
}

.recommend-viewer {
  width: 100%;
  height: 100%;
}

.recommend-mobile-actions {
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: calc(16px + var(--player-control-safe-offset));
  z-index: 36;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.action-detail {
  flex: 0 0 auto;
}

.recommend-index {
  flex: 1;
  text-align: center;
  font-weight: 500;
  color: #fff;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.55);
}

@media (max-width: 768px) {
  .resource-recommend-page {
    border-radius: 18px;
  }

  .recommend-top-actions {
    top: 10px;
    right: 10px;
  }

  .recommend-mobile-actions {
    bottom: calc(8px + env(safe-area-inset-bottom) + var(--player-control-safe-offset));
  }
}
</style>
