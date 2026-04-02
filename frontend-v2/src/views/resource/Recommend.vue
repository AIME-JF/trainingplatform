<template>
  <div
    class="community-page"
    @touchstart.capture="onTouchStart"
    @touchmove.capture="onTouchMove"
    @touchend.capture="onTouchEnd"
  >
    <div class="community-shell">
      <div class="community-stage">
        <a-empty v-if="!currentResource && !loadingResource" description="暂无社区内容" class="community-empty" />

        <template v-else-if="currentResource">
          <div class="community-player-shell">
            <div class="community-overlay-bar">
              <ResourceCommunityTopBar
                active-tab="recommended"
                v-model:keyword="searchKeyword"
                :searching="searching"
                @search="handleSearch"
                @tab-change="handleTabChange"
              >
                <template #actions>
                  <ResourceCommunityUploadEntry />
                </template>
              </ResourceCommunityTopBar>
            </div>

            <div
              ref="communityViewerRef"
              class="community-viewer"
              @mouseenter="handleViewerMouseEnter"
              @mouseleave="handleViewerMouseLeave"
              @mousedown.capture="handleViewerMouseDown"
            >
              <Transition :name="viewerTransitionName || undefined">
                <div :key="currentResource.id" class="community-viewer-slide">
                  <ResourceViewer
                    class="community-viewer-frame"
                    :resource="currentResource"
                    mode="recommend"
                    @click="recordCurrentEvent('click')"
                    @play="recordCurrentEvent('play')"
                    @complete="recordCurrentEvent('complete')"
                  />
                </div>
              </Transition>
            </div>

            <div class="community-side-actions" :class="{ mobile: isMobile }">
              <button
                type="button"
                class="community-action-btn"
                :class="{ active: !!currentResource.current_user_liked }"
                :disabled="liking"
                @click.stop="handleToggleLike"
              >
                <component :is="currentResource.current_user_liked ? HeartFilled : HeartOutlined" class="community-action-icon" />
                <span class="community-action-label">{{ currentResource.current_user_liked ? '已点赞' : '点赞' }}</span>
                <span class="community-action-count">{{ formatCount(currentResource.like_count) }}</span>
              </button>

              <button
                type="button"
                class="community-action-btn"
                @click.stop="openComments"
              >
                <MessageOutlined class="community-action-icon" />
                <span class="community-action-label">评论</span>
                <span class="community-action-count">{{ formatCount(currentResource.comment_count) }}</span>
              </button>

              <button
                type="button"
                class="community-action-btn"
                :disabled="sharing"
                @click.stop="handleShare"
              >
                <ShareAltOutlined class="community-action-icon" />
                <span class="community-action-label">转发</span>
                <span class="community-action-count">{{ formatCount(currentResource.share_count) }}</span>
              </button>

              <button
                type="button"
                class="community-action-btn secondary"
                @click.stop="goDetail"
              >
                <ProfileOutlined class="community-action-icon" />
                <span class="community-action-label">详情</span>
              </button>
            </div>
          </div>
        </template>

        <div v-if="shouldShowCommunityLoading" class="community-loading-overlay">
          <a-spin size="large" />
        </div>
      </div>
    </div>

    <ResourceCommentsDrawer
      v-model:open="commentDrawerOpen"
      v-model:draft="commentDraft"
      :resource-title="currentResource?.title"
      :comment-count="currentResource?.comment_count || comments.length"
      :comments="comments"
      :loading="commentLoading"
      :submitting="commentSubmitting"
      @submit="handleSubmitComment"
      @delete="handleDeleteComment"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  HeartFilled,
  HeartOutlined,
  MessageOutlined,
  ProfileOutlined,
  ShareAltOutlined,
} from '@ant-design/icons-vue'
import type {
  ResourceBehaviorEventCreateEventType,
  ResourceDetailResponse,
  ResourceRecommendationItem,
} from '@/api/learning-resource'
import {
  getResourceDetail,
  listRecommendationFeed,
  listResources,
  recordResourceEvent,
} from '@/api/learning-resource'
import { useMobile } from '@/composables/useMobile'
import ResourceCommentsDrawer from '@/components/resource/ResourceCommentsDrawer.vue'
import ResourceCommunityTopBar from '@/components/resource/ResourceCommunityTopBar.vue'
import ResourceCommunityUploadEntry from '@/components/resource/ResourceCommunityUploadEntry.vue'
import ResourceViewer from '@/components/resource/ResourceViewer.vue'
import { useResourceInteractions } from '@/composables/useResourceInteractions'

const PAGE_SIZE = 10
const NAVIGATION_COOLDOWN = 420

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
const searching = ref(false)
const searchKeyword = ref('')
const navigationLockedUntil = ref(0)
const communityViewerRef = ref<HTMLElement | null>(null)
const wheelNavigationArmed = ref(false)
const viewerPointerInside = ref(false)
const viewerTransitionDirection = ref<'next' | 'prev'>('next')
const resourceCache = new Map<number, ResourceDetailResponse>()
const resourcePending = new Map<number, Promise<ResourceDetailResponse>>()
const impressionRecorded = new Set<number>()
const gesture = ref({
  startX: 0,
  startY: 0,
  axis: '',
  triggered: false,
  ignore: false,
})

const currentFeedItem = computed(() => feedItems.value[currentIndex.value] || null)
const shouldShowCommunityLoading = computed(() => !currentResource.value && (loadingResource.value || loadingFeed.value))
const viewerTransitionName = computed(() => {
  if (!isMobile.value) {
    return ''
  }
  return viewerTransitionDirection.value === 'prev' ? 'community-viewer-swipe-prev' : 'community-viewer-swipe-next'
})
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
  resource: currentResource,
  isMobile,
  patchResource,
})

onMounted(() => {
  window.addEventListener('wheel', handleWheel, { passive: false })
  window.addEventListener('keydown', handleKeydown)
  document.addEventListener('click', handleDocumentClick, true)
  void fetchFeedPage(1)
})

onUnmounted(() => {
  window.removeEventListener('wheel', handleWheel)
  window.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('click', handleDocumentClick, true)
})

watch(() => currentFeedItem.value?.resource_id, async (resourceId) => {
  if (!resourceId) {
    currentResource.value = null
    comments.value = []
    return
  }

  await loadCurrentResource(resourceId)
  await recordImpression(resourceId)
  void maybePreloadNextPage()
  void preloadAdjacentResources()
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

async function ensureResourceDetail(resourceId: number) {
  const cached = resourceCache.get(resourceId)
  if (cached) {
    return cached
  }

  const pending = resourcePending.get(resourceId)
  if (pending) {
    return pending
  }

  const request = getResourceDetail(resourceId)
    .then((detail) => {
      resourceCache.set(resourceId, detail)
      return detail
    })
    .finally(() => {
      resourcePending.delete(resourceId)
    })

  resourcePending.set(resourceId, request)
  return request
}

async function loadCurrentResource(resourceId: number) {
  const shouldShowLoading = !resourceCache.has(resourceId) && !resourcePending.has(resourceId)
  if (shouldShowLoading) {
    loadingResource.value = true
  }
  try {
    currentResource.value = await ensureResourceDetail(resourceId)
  } catch (error) {
    currentResource.value = null
    message.error(error instanceof Error ? error.message : '加载资源详情失败')
  } finally {
    if (shouldShowLoading) {
      loadingResource.value = false
    }
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

function preloadResource(resourceId?: number | null) {
  if (!resourceId || resourceCache.has(resourceId) || resourcePending.has(resourceId)) {
    return
  }

  void ensureResourceDetail(resourceId).catch(() => {
    // ignore preload errors
  })
}

function preloadAdjacentResources() {
  preloadResource(feedItems.value[currentIndex.value + 1]?.resource_id)
  preloadResource(feedItems.value[currentIndex.value - 1]?.resource_id)
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

function handleTabChange(tab: 'recommended' | 'featured') {
  if (tab === 'featured') {
    void router.push('/resource/library')
  }
}

function lockNavigation() {
  navigationLockedUntil.value = Date.now() + NAVIGATION_COOLDOWN
}

function canNavigate() {
  return Date.now() >= navigationLockedUntil.value
}

function setViewerTransitionDirection(direction: 'next' | 'prev') {
  viewerTransitionDirection.value = direction
}

async function navigateNext() {
  if (!canNavigate()) {
    return
  }
  setViewerTransitionDirection('next')
  lockNavigation()
  await nextRecommendation()
}

function navigatePrev() {
  if (!canNavigate()) {
    return
  }
  setViewerTransitionDirection('prev')
  lockNavigation()
  prevRecommendation()
}

function isInteractiveTarget(target: EventTarget | null) {
  if (!(target instanceof Element)) {
    return false
  }

  return Boolean(target.closest(
    '.community-search, .community-channel-switch, .community-side-actions, .community-comments-drawer, .ant-drawer, .ant-drawer-content-wrapper, input, textarea, select, button, a, [contenteditable="true"], .ant-input, .ant-select, .ant-btn',
  ))
}

function isPointerInsideViewer(clientX: number, clientY: number) {
  if (!communityViewerRef.value) {
    return false
  }

  const rect = communityViewerRef.value.getBoundingClientRect()
  return (
    clientX >= rect.left &&
    clientX <= rect.right &&
    clientY >= rect.top &&
    clientY <= rect.bottom
  )
}

function handleViewerMouseEnter() {
  viewerPointerInside.value = true
}

function handleViewerMouseLeave() {
  viewerPointerInside.value = false
  wheelNavigationArmed.value = false
}

function handleViewerMouseDown(event: MouseEvent) {
  if (event.button !== 0) {
    return
  }
  viewerPointerInside.value = true
  wheelNavigationArmed.value = true
}

function handleDocumentClick(event: MouseEvent) {
  if (!communityViewerRef.value) {
    return
  }

  if (event.target instanceof Node && communityViewerRef.value.contains(event.target)) {
    return
  }

  viewerPointerInside.value = false
  wheelNavigationArmed.value = false
}

function handleWheel(event: WheelEvent) {
  if (!feedItems.value.length || isInteractiveTarget(event.target)) {
    return
  }

  const pointerInsideViewer = viewerPointerInside.value || isPointerInsideViewer(event.clientX, event.clientY)
  if (!wheelNavigationArmed.value || !pointerInsideViewer) {
    return
  }
  viewerPointerInside.value = pointerInsideViewer

  if (Math.abs(event.deltaY) < 48) {
    return
  }

  if (event.cancelable) {
    event.preventDefault()
  }

  if (event.deltaY > 0) {
    void navigateNext()
    return
  }

  navigatePrev()
}

function handleKeydown(event: KeyboardEvent) {
  if (isInteractiveTarget(event.target)) {
    return
  }

  if (event.key === 'ArrowDown') {
    event.preventDefault()
    void navigateNext()
    return
  }

  if (event.key === 'ArrowUp') {
    event.preventDefault()
    navigatePrev()
  }
}

function formatCount(value?: number | null) {
  const count = Number(value || 0)
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}w`
  }
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k`
  }
  return String(count)
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

async function recordCurrentEvent(eventType: ResourceBehaviorEventCreateEventType) {
  if (!currentResource.value?.id) {
    return
  }
  try {
    await recordResourceEvent(currentResource.value.id, eventType)
  } catch {
    // ignore
  }
}

function patchResource(resourceId: number, patch: Partial<ResourceDetailResponse>) {
  const cached = resourceCache.get(resourceId)
  if (cached) {
    resourceCache.set(resourceId, { ...cached, ...patch })
  }
  if (currentResource.value?.id === resourceId) {
    currentResource.value = { ...currentResource.value, ...patch }
  }
}

function matchesResource(resource: ResourceDetailResponse | undefined, keyword: string) {
  if (!resource) {
    return false
  }

  const needle = keyword.trim().toLowerCase()
  if (!needle) {
    return false
  }

  const candidateFields = [
    resource.title,
    resource.summary,
    resource.uploader_name,
    ...(resource.tags || []),
  ]

  return candidateFields.some((value) => String(value || '').toLowerCase().includes(needle))
}

async function handleSearch() {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    message.warning('请输入搜索关键词')
    return
  }

  const matchedIndex = feedItems.value.findIndex((item) => matchesResource(resourceCache.get(item.resource_id), keyword))
  if (matchedIndex >= 0) {
    setViewerTransitionDirection(matchedIndex >= currentIndex.value ? 'next' : 'prev')
    currentIndex.value = matchedIndex
    message.success('已定位到匹配资源')
    return
  }

  searching.value = true
  try {
    const result = await listResources({
      page: 1,
      size: 10,
      search: keyword,
      status: 'published',
    })

    const target = result.items?.[0]
    if (!target?.id) {
      message.info('未找到匹配资源')
      return
    }

    await ensureResourceDetail(target.id)

    const existingIndex = feedItems.value.findIndex((item) => item.resource_id === target.id)
    if (existingIndex >= 0) {
      setViewerTransitionDirection(existingIndex >= currentIndex.value ? 'next' : 'prev')
      currentIndex.value = existingIndex
    } else {
      const insertIndex = feedItems.value.length ? Math.min(currentIndex.value + 1, feedItems.value.length) : 0
      const inheritedScore = currentFeedItem.value?.score ?? 0
      feedItems.value.splice(insertIndex, 0, { resource_id: target.id, score: inheritedScore })
      total.value = Math.max(total.value, feedItems.value.length)
      setViewerTransitionDirection(insertIndex >= currentIndex.value ? 'next' : 'prev')
      currentIndex.value = insertIndex
    }

    message.success('已跳转到搜索结果')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '搜索资源失败')
  } finally {
    searching.value = false
  }
}

function onTouchStart(event: TouchEvent) {
  if (!isMobile.value) {
    return
  }

  const target = event.target
  const ignore = target instanceof Element && Boolean(target.closest(
    '.community-side-actions, .community-comments-drawer, .community-search, button, textarea, input',
  ))
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
    void navigateNext()
    return
  }

  if (deltaY > 80) {
    gesture.value.triggered = true
    navigatePrev()
  }
}
</script>

<style scoped>
.community-page {
  --community-stage-height: calc(100dvh - var(--v2-bottomnav-height));
  position: fixed;
  inset: 0 0 var(--v2-bottomnav-height) 0;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: var(--community-stage-height);
  padding: 0 !important;
  background: #000;
  overflow: hidden;
  z-index: 1;
}

.community-overlay-bar {
  position: absolute;
  top: 18px;
  left: 18px;
  right: 18px;
  z-index: 22;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  pointer-events: none;
}

.community-overlay-bar > * {
  pointer-events: auto;
}

.community-shell {
  position: relative;
  display: flex;
  flex: 1 1 auto;
  min-width: 0;
  min-height: var(--community-stage-height);
  width: 100%;
  height: var(--community-stage-height);
  padding: 0 !important;
  overflow: hidden;
}

.community-stage {
  position: relative;
  display: flex;
  flex: 1 1 auto;
  min-width: 0;
  min-height: var(--community-stage-height);
  height: var(--community-stage-height);
  width: 100%;
  overflow: hidden;
}

.community-empty {
  display: flex;
  flex: 1 1 auto;
  align-items: center;
  justify-content: center;
  min-width: 0;
  min-height: var(--community-stage-height);
  width: 100%;
  height: var(--community-stage-height);
  padding: 0;
  background: #000;
}

.community-player-shell {
  position: relative;
  display: flex;
  align-items: stretch;
  align-self: stretch;
  flex: 1 1 auto;
  min-width: 0;
  min-height: var(--community-stage-height);
  height: var(--community-stage-height);
  width: 100%;
  max-width: none;
  margin: 0;
}

.community-loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 26;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.22);
  pointer-events: none;
}

.community-loading-overlay :deep(.ant-spin-dot-item) {
  background-color: rgba(255, 255, 255, 0.92);
}

.community-viewer {
  position: relative;
  display: flex;
  flex: 1 1 auto;
  align-items: stretch;
  justify-content: stretch;
  min-width: 0;
  min-height: var(--community-stage-height);
  width: 100%;
  height: var(--community-stage-height);
  border-radius: 0;
  background: #000;
  box-shadow: none;
  color: #fff;
  overflow: hidden;
  isolation: isolate;
}

.community-viewer-slide {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: stretch;
  justify-content: stretch;
  width: 100%;
  height: 100%;
  will-change: transform, opacity;
}

.community-viewer-frame,
.community-viewer :deep(.resource-viewer) {
  display: flex;
  flex: 1 1 auto;
  align-self: stretch;
  min-width: 0;
  min-height: var(--community-stage-height);
  width: 100%;
  height: var(--community-stage-height);
}

.community-side-actions {
  position: absolute;
  top: 50%;
  right: 14px;
  z-index: 18;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transform: translateY(-50%);
}

.community-action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 7px;
  width: 76px;
  padding: 12px 8px 10px;
  border: 1px solid rgba(74, 87, 98, 0.12);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.78);
  color: #27313a;
  box-shadow: 0 10px 24px rgba(65, 79, 92, 0.1);
  cursor: pointer;
  backdrop-filter: blur(10px);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease;
}

.community-action-btn:hover:not(:disabled),
.community-action-btn.active {
  background: rgba(39, 49, 58, 0.92);
  border-color: rgba(39, 49, 58, 0.92);
  color: #fff;
  transform: translateX(-2px);
  box-shadow: 0 14px 32px rgba(39, 49, 58, 0.2);
}

.community-action-btn.secondary {
  background: rgba(241, 244, 246, 0.84);
  color: #27313a;
}

.community-action-btn.secondary:hover:not(:disabled) {
  background: rgba(39, 49, 58, 0.92);
}

.community-action-btn:disabled {
  cursor: not-allowed;
  opacity: 0.68;
}

.community-action-icon {
  font-size: 20px;
}

.community-action-label {
  font-size: 12px;
  font-weight: 700;
}

.community-action-count {
  font-size: 12px;
  opacity: 0.72;
}

@media (max-width: 768px) {
  .community-viewer-swipe-next-enter-active,
  .community-viewer-swipe-next-leave-active,
  .community-viewer-swipe-prev-enter-active,
  .community-viewer-swipe-prev-leave-active {
    transition:
      transform 0.4s cubic-bezier(0.22, 0.82, 0.24, 1),
      opacity 0.36s ease;
  }

  .community-viewer-swipe-next-enter-active,
  .community-viewer-swipe-prev-enter-active {
    z-index: 2;
  }

  .community-viewer-swipe-next-leave-active,
  .community-viewer-swipe-prev-leave-active {
    z-index: 1;
  }

  .community-viewer-swipe-next-enter-from {
    transform: translate3d(0, 18%, 0);
    opacity: 0.78;
  }

  .community-viewer-swipe-next-leave-to {
    transform: translate3d(0, -14%, 0);
    opacity: 0;
  }

  .community-viewer-swipe-prev-enter-from {
    transform: translate3d(0, -18%, 0);
    opacity: 0.78;
  }

  .community-viewer-swipe-prev-leave-to {
    transform: translate3d(0, 14%, 0);
    opacity: 0;
  }

  .community-page {
    --community-stage-height: calc(100dvh - var(--v2-bottomnav-height));
    inset: 0 0 var(--v2-bottomnav-height) 0;
    padding-bottom: 0 !important;
  }

  .community-overlay-bar {
    top: 12px;
    left: 12px;
    right: 12px;
  }

  .community-viewer {
    border-radius: 0;
  }

  .community-side-actions {
    top: auto;
    right: 12px;
    bottom: 88px;
    gap: 16px;
    transform: none;
  }

  .community-side-actions.mobile .community-action-btn {
    width: 56px;
    padding: 0;
    border: none;
    border-radius: 0;
    background: transparent;
    box-shadow: none;
    backdrop-filter: none;
    color: rgba(255, 255, 255, 0.96);
  }

  .community-side-actions.mobile .community-action-btn:hover:not(:disabled),
  .community-side-actions.mobile .community-action-btn.active,
  .community-side-actions.mobile .community-action-btn.secondary,
  .community-side-actions.mobile .community-action-btn.secondary:hover:not(:disabled) {
    background: transparent;
    border-color: transparent;
    box-shadow: none;
    transform: none;
  }

  .community-side-actions.mobile .community-action-btn.active {
    color: #ff8fa3;
  }

  .community-side-actions.mobile .community-action-icon {
    font-size: 22px;
    text-shadow: 0 4px 16px rgba(0, 0, 0, 0.42);
  }

  .community-side-actions.mobile .community-action-label,
  .community-side-actions.mobile .community-action-count {
    color: currentColor;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.54);
  }

  .community-side-actions.mobile .community-action-count {
    opacity: 0.84;
  }
}

@media (min-width: 769px) {
  .community-page {
    --community-stage-height: 100dvh;
    inset: 0 0 0 var(--v2-sidebar-width);
    padding-bottom: 0 !important;
  }
}
</style>
