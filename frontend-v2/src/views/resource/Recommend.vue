<template>
  <div
    class="page-content community-page resource-page"
    @touchstart.capture="onTouchStart"
    @touchmove.capture="onTouchMove"
    @touchend.capture="onTouchEnd"
  >
    <LearningResourceTabs />

    <div class="community-header">
      <div class="community-heading">
        <h1 class="page-title">资源社区</h1>
        <p class="page-subtitle">
          按推荐流连续浏览优先资源，支持鼠标滚轮或键盘上下键切换。
          <span v-if="isMobile">移动端支持上下滑切换资源。</span>
        </p>
        <div v-if="currentResource" class="community-meta-line">
          <span>当前第 {{ currentIndex + 1 }} 条 / {{ currentDisplayTotal }}</span>
          <span v-if="currentFeedItem">推荐分 {{ formatScore(currentFeedItem.score) }}</span>
          <span v-if="activeFeedTab === 'featured'">精选内容当前先复用推荐流</span>
        </div>
      </div>

      <div class="community-search">
        <a-input-search
          v-model:value="searchKeyword"
          allow-clear
          size="large"
          :loading="searching"
          placeholder="搜索标题、简介、作者或标签"
          enter-button="搜索"
          @search="handleSearch"
        />
      </div>

      <div class="community-channel-switch" role="tablist" aria-label="资源社区频道">
        <button
          type="button"
          class="channel-tab"
          :class="{ active: activeFeedTab === 'recommended' }"
          @click="activeFeedTab = 'recommended'"
        >
          推荐
        </button>
        <button
          type="button"
          class="channel-tab"
          :class="{ active: activeFeedTab === 'featured' }"
          @click="activeFeedTab = 'featured'"
        >
          精选
        </button>
      </div>
    </div>

    <div class="community-shell">
      <a-spin :spinning="loadingResource || loadingFeed" class="community-spin">
        <a-empty v-if="!currentResource && !loadingResource" description="暂无社区内容" class="community-empty" />

        <template v-else-if="currentResource">
          <div class="community-player-shell">
            <div
              ref="communityViewerRef"
              class="community-viewer"
              @mouseleave="handleViewerMouseLeave"
              @mousedown.capture="handleViewerMouseDown"
            >
              <ResourceViewer
                :resource="currentResource"
                mode="recommend"
                @click="recordCurrentEvent('click')"
                @play="recordCurrentEvent('play')"
                @complete="recordCurrentEvent('complete')"
              />
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
      </a-spin>
    </div>

    <a-drawer
      v-model:open="commentDrawerOpen"
      class="community-comments-drawer"
      placement="right"
      :width="commentDrawerWidth"
      :body-style="{ padding: 0 }"
      title="资源评论"
    >
      <div class="comment-drawer-body">
        <div v-if="currentResource" class="comment-drawer-head">
          <strong>{{ currentResource.title }}</strong>
          <span>{{ formatCount(currentResource.comment_count) }} 条评论</span>
        </div>

        <div class="comment-list-wrapper">
          <a-spin :spinning="commentLoading">
            <a-empty v-if="!comments.length && !commentLoading" description="还没有评论，先说点什么吧" />

            <div v-else class="comment-list">
              <div v-for="item in comments" :key="item.id" class="comment-card">
                <div class="comment-card-head">
                  <div class="comment-user-meta">
                    <strong>{{ item.user_name || `用户#${item.user_id}` }}</strong>
                    <span>{{ formatDateTime(item.created_at) }}</span>
                  </div>
                  <a-popconfirm
                    v-if="item.can_delete"
                    title="确认删除这条评论吗？"
                    ok-text="删除"
                    cancel-text="取消"
                    @confirm="handleDeleteComment(item.id)"
                  >
                    <a-button type="link" danger size="small">删除</a-button>
                  </a-popconfirm>
                </div>
                <p class="comment-card-content">{{ item.content }}</p>
              </div>
            </div>
          </a-spin>
        </div>

        <div class="comment-editor">
          <a-textarea
            v-model:value="commentDraft"
            :rows="4"
            :maxlength="1000"
            show-count
            placeholder="写下你的评论"
          />
          <div class="comment-editor-actions">
            <span>当前支持查看评论、发表评论、删除自己的评论。</span>
            <a-button type="primary" :loading="commentSubmitting" @click="handleSubmitComment">发表评论</a-button>
          </div>
        </div>
      </div>
    </a-drawer>
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
  ResourceCommentResponse,
  ResourceDetailResponse,
  ResourceRecommendationItem,
} from '@/api/learning-resource'
import {
  createResourceComment,
  deleteResourceComment,
  getResourceDetail,
  likeResource,
  listRecommendationFeed,
  listResourceComments,
  listResources,
  recordResourceEvent,
  shareResource,
  unlikeResource,
} from '@/api/learning-resource'
import { useMobile } from '@/composables/useMobile'
import LearningResourceTabs from '@/components/resource/LearningResourceTabs.vue'
import ResourceViewer from '@/components/resource/ResourceViewer.vue'
import { formatDateTime } from '@/utils/learning-resource'

const PAGE_SIZE = 10
const NAVIGATION_COOLDOWN = 420

const router = useRouter()
const { isMobile } = useMobile()

const activeFeedTab = ref<'recommended' | 'featured'>('recommended')
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
const liking = ref(false)
const sharing = ref(false)
const commentDrawerOpen = ref(false)
const commentLoading = ref(false)
const commentSubmitting = ref(false)
const comments = ref<ResourceCommentResponse[]>([])
const commentDraft = ref('')
const navigationLockedUntil = ref(0)
const communityViewerRef = ref<HTMLElement | null>(null)
const wheelNavigationArmed = ref(false)
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
const currentDisplayTotal = computed(() => {
  if (total.value > 0) {
    return Math.max(total.value, feedItems.value.length)
  }
  return feedItems.value.length
})
const commentDrawerWidth = computed(() => isMobile.value ? '100%' : 420)

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

watch(() => currentFeedItem.value?.resource_id, async (resourceId, previousResourceId) => {
  if (!resourceId) {
    currentResource.value = null
    comments.value = []
    return
  }

  await loadCurrentResource(resourceId)
  await recordImpression(resourceId)
  void maybePreloadNextPage()

  if (commentDrawerOpen.value && resourceId !== previousResourceId) {
    await loadComments(resourceId)
  }
}, { immediate: true })

watch(commentDrawerOpen, async (open) => {
  if (!open) {
    commentDraft.value = ''
    return
  }

  if (currentResource.value?.id) {
    await loadComments(currentResource.value.id)
  }
})

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

function lockNavigation() {
  navigationLockedUntil.value = Date.now() + NAVIGATION_COOLDOWN
}

function canNavigate() {
  return Date.now() >= navigationLockedUntil.value
}

async function navigateNext() {
  if (!canNavigate()) {
    return
  }
  lockNavigation()
  await nextRecommendation()
}

function navigatePrev() {
  if (!canNavigate()) {
    return
  }
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

function isViewerTarget(target: EventTarget | null) {
  return target instanceof Element && Boolean(target.closest('.community-viewer'))
}

function handleViewerMouseLeave() {
  wheelNavigationArmed.value = false
}

function handleViewerMouseDown(event: MouseEvent) {
  if (event.button !== 0) {
    return
  }
  wheelNavigationArmed.value = true
}

function handleDocumentClick(event: MouseEvent) {
  if (!communityViewerRef.value) {
    return
  }

  if (event.target instanceof Node && communityViewerRef.value.contains(event.target)) {
    return
  }

  wheelNavigationArmed.value = false
}

function handleWheel(event: WheelEvent) {
  if (!feedItems.value.length || isInteractiveTarget(event.target)) {
    return
  }

  if (!wheelNavigationArmed.value || !isViewerTarget(event.target)) {
    return
  }

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

function formatScore(score?: number | null) {
  if (typeof score !== 'number' || Number.isNaN(score)) {
    return '-'
  }
  return score.toFixed(2)
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

function patchResource(resourceId: number, patch: Partial<ResourceDetailResponse>) {
  const cached = resourceCache.get(resourceId)
  if (cached) {
    resourceCache.set(resourceId, { ...cached, ...patch })
  }
  if (currentResource.value?.id === resourceId) {
    currentResource.value = { ...currentResource.value, ...patch }
  }
}

async function handleToggleLike() {
  if (!currentResource.value?.id || liking.value) {
    return
  }

  liking.value = true
  try {
    const response = currentResource.value.current_user_liked
      ? await unlikeResource(currentResource.value.id)
      : await likeResource(currentResource.value.id)

    patchResource(currentResource.value.id, {
      current_user_liked: response.liked,
      like_count: response.like_count,
    })
  } catch (error) {
    message.error(error instanceof Error ? error.message : '点赞操作失败')
  } finally {
    liking.value = false
  }
}

async function handleShare() {
  if (!currentResource.value?.id || sharing.value) {
    return
  }

  sharing.value = true
  try {
    const resourceId = currentResource.value.id
    const response = await shareResource(resourceId)
    patchResource(resourceId, { share_count: response.share_count })

    const copied = await copyShareLink(resourceId)
    message.success(copied ? '已复制链接并记录转发' : '已记录转发')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '转发失败')
  } finally {
    sharing.value = false
  }
}

async function copyShareLink(resourceId: number) {
  const shareUrl = new URL(`/resource/detail/${resourceId}`, window.location.origin).toString()

  if (isMobile.value && typeof navigator !== 'undefined' && 'share' in navigator) {
    try {
      await navigator.share({
        title: currentResource.value?.title,
        text: currentResource.value?.summary || currentResource.value?.title,
        url: shareUrl,
      })
      return true
    } catch {
      // fallback to clipboard
    }
  }

  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(shareUrl)
    return true
  }

  const textarea = document.createElement('textarea')
  textarea.value = shareUrl
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.focus()
  textarea.select()
  const copied = document.execCommand('copy')
  document.body.removeChild(textarea)
  return copied
}

function openComments() {
  if (!currentResource.value?.id) {
    return
  }
  commentDrawerOpen.value = true
}

async function loadComments(resourceId: number) {
  commentLoading.value = true
  try {
    comments.value = await listResourceComments(resourceId)
    patchResource(resourceId, { comment_count: comments.value.length })
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载评论失败')
  } finally {
    commentLoading.value = false
  }
}

async function handleSubmitComment() {
  if (!currentResource.value?.id || commentSubmitting.value) {
    return
  }

  const content = commentDraft.value.trim()
  if (!content) {
    message.warning('请输入评论内容')
    return
  }

  commentSubmitting.value = true
  try {
    const created = await createResourceComment(currentResource.value.id, { content })
    comments.value = [created, ...comments.value]
    commentDraft.value = ''
    patchResource(currentResource.value.id, { comment_count: comments.value.length })
    message.success('评论已发布')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '发表评论失败')
  } finally {
    commentSubmitting.value = false
  }
}

async function handleDeleteComment(commentId: number) {
  if (!currentResource.value?.id) {
    return
  }

  try {
    await deleteResourceComment(currentResource.value.id, commentId)
    comments.value = comments.value.filter((item) => item.id !== commentId)
    patchResource(currentResource.value.id, { comment_count: comments.value.length })
    message.success('评论已删除')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '删除评论失败')
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

    if (!resourceCache.has(target.id)) {
      const detail = await getResourceDetail(target.id)
      resourceCache.set(target.id, detail)
    }

    const existingIndex = feedItems.value.findIndex((item) => item.resource_id === target.id)
    if (existingIndex >= 0) {
      currentIndex.value = existingIndex
    } else {
      const insertIndex = feedItems.value.length ? Math.min(currentIndex.value + 1, feedItems.value.length) : 0
      const inheritedScore = currentFeedItem.value?.score ?? 0
      feedItems.value.splice(insertIndex, 0, { resource_id: target.id, score: inheritedScore })
      total.value = Math.max(total.value, feedItems.value.length)
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
  min-height: 100vh;
}

.community-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 520px) auto;
  align-items: start;
  gap: 20px;
  margin-bottom: 22px;
}

.community-heading {
  min-width: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 6px;
}

.page-subtitle {
  color: var(--v2-text-secondary);
  line-height: 1.7;
}

.community-meta-line {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  margin-top: 10px;
  color: rgba(49, 62, 73, 0.74);
  font-size: 13px;
}

.community-search {
  align-self: center;
}

.community-channel-switch {
  display: inline-flex;
  align-items: center;
  justify-content: flex-end;
  gap: 18px;
  padding-top: 6px;
}

.channel-tab {
  border: none;
  background: transparent;
  padding: 0;
  color: rgba(17, 17, 17, 0.45);
  font-family: SimHei, 'Microsoft YaHei', sans-serif;
  font-size: 26px;
  font-weight: 700;
  cursor: pointer;
  transition:
    color 0.2s ease,
    transform 0.2s ease;
}

.channel-tab:hover,
.channel-tab.active {
  color: #111;
  transform: translateY(-1px);
}

.community-shell {
  position: relative;
}

.community-spin,
.community-spin :deep(.ant-spin-nested-loading),
.community-spin :deep(.ant-spin-container) {
  display: block;
  min-height: calc(100vh - 228px);
}

.community-empty {
  padding: 84px 0;
}

.community-player-shell {
  position: relative;
}

.community-viewer {
  overflow: hidden;
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(208, 218, 226, 0.68), transparent 30%),
    linear-gradient(180deg, rgba(245, 247, 249, 0.98), rgba(231, 236, 240, 0.92));
  box-shadow: 0 20px 42px rgba(65, 79, 92, 0.14);
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

.community-comments-drawer :deep(.ant-drawer-header) {
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.comment-drawer-body {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.comment-drawer-head {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 18px 20px 14px;
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(248, 250, 252, 0.9);
}

.comment-drawer-head span {
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.comment-list-wrapper {
  flex: 1;
  min-height: 0;
  padding: 18px 20px;
  overflow-y: auto;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.comment-card {
  padding: 14px 14px 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  background: #fff;
}

.comment-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.comment-user-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.comment-user-meta span {
  color: var(--v2-text-secondary);
  font-size: 12px;
}

.comment-card-content {
  margin: 0;
  color: #111;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.comment-editor {
  padding: 18px 20px 20px;
  border-top: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(248, 250, 252, 0.96);
}

.comment-editor-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
  color: var(--v2-text-secondary);
  font-size: 12px;
}

@media (max-width: 1024px) {
  .community-header {
    grid-template-columns: 1fr;
  }

  .community-search {
    width: 100%;
  }

  .community-channel-switch {
    justify-content: flex-start;
    padding-top: 0;
  }
}

@media (max-width: 768px) {
  .community-spin,
  .community-spin :deep(.ant-spin-nested-loading),
  .community-spin :deep(.ant-spin-container) {
    min-height: calc(100vh - 286px);
  }

  .community-viewer {
    border-radius: 24px;
  }

  .community-side-actions {
    top: auto;
    right: 10px;
    bottom: 16px;
    transform: none;
  }

  .community-action-btn {
    width: 68px;
    padding: 10px 7px 9px;
    border-radius: 18px;
  }

  .community-action-icon {
    font-size: 19px;
  }

  .channel-tab {
    font-size: 22px;
  }

  .comment-list-wrapper,
  .comment-editor,
  .comment-drawer-head {
    padding-left: 16px;
    padding-right: 16px;
  }

  .comment-editor-actions {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
