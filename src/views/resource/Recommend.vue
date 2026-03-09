<template>
  <div
    class="resource-recommend-page"
    @touchstart.passive="onTouchStart"
    @touchmove.passive="onTouchMove"
    @touchend.passive="onTouchEnd"
  >
    <div class="page-header">
      <h2>资源推荐</h2>
      <a-space>
        <a-button @click="$router.push('/resource/library')">资源库</a-button>
        <a-button v-if="!isMobile" type="primary" @click="nextRecommendation">下一个</a-button>
      </a-space>
    </div>

    <a-spin :spinning="loadingResource">
      <a-empty v-if="!currentResource && !loadingResource" description="暂无推荐内容" />
      <ResourceViewer
        v-else
        :resource="currentResource"
        @click="recordCurrentEvent('click')"
        @play="recordCurrentEvent('play')"
        @complete="recordCurrentEvent('complete')"
      />
    </a-spin>

    <div class="recommend-footer" v-if="currentResource">
      <a-space>
        <a-button @click="goDetail">查看详情</a-button>
        <a-button v-if="isMobile" type="primary" @click="nextRecommendation">下一条</a-button>
      </a-space>
      <span class="recommend-index">{{ currentIndex + 1 }} / {{ feedItems.length }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { getRecommendationFeed, recordResourceEvent } from '@/api/recommendation'
import { getResource } from '@/api/resource'
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
const gesture = ref({ startX: 0, startY: 0, axis: '', triggered: false })

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
  const touch = event.touches?.[0]
  if (!touch) return
  gesture.value = {
    startX: touch.clientX,
    startY: touch.clientY,
    axis: '',
    triggered: false,
  }
}

function onTouchMove(event) {
  const touch = event.touches?.[0]
  if (!touch || gesture.value.triggered) return

  const deltaX = touch.clientX - gesture.value.startX
  const deltaY = touch.clientY - gesture.value.startY
  const absX = Math.abs(deltaX)
  const absY = Math.abs(deltaY)

  if (!gesture.value.axis && (absX > 12 || absY > 12)) {
    gesture.value.axis = absY > absX ? 'y' : 'x'
  }
}

function onTouchEnd(event) {
  if (gesture.value.axis !== 'y' || gesture.value.triggered) return

  const touch = event.changedTouches?.[0]
  if (!touch) return

  const deltaY = touch.clientY - gesture.value.startY
  if (deltaY > 90) {
    gesture.value.triggered = true
    nextRecommendation()
  }
}
</script>

<style scoped>
.resource-recommend-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.recommend-footer { display: flex; justify-content: space-between; align-items: center; }
.recommend-index { color: #666; font-size: 13px; }

@media (max-width: 768px) {
  .recommend-footer { gap: 8px; flex-direction: column; align-items: flex-start; }
}
</style>
