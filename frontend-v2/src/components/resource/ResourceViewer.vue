<template>
  <div
    v-if="resource"
    class="resource-viewer"
    :class="[
      `mode-${mode}`,
      `theme-${theme}`,
      { compact },
    ]"
  >
    <a-card v-if="mode !== 'recommend'" :bordered="false" class="viewer-card">
      <div class="viewer-head">
        <div>
          <h2 class="viewer-title">{{ resource.title }}</h2>
          <p class="viewer-summary">{{ resource.summary || '暂无摘要' }}</p>
        </div>
        <a-tag color="blue">{{ getResourceContentTypeLabel(resource.content_type) }}</a-tag>
      </div>

      <div class="viewer-stage" @click="$emit('click')" @touchstart="onMediaTouchStart" @touchend="onMediaTouchEnd">
        <template v-if="currentMedia && currentMediaKind === 'video'">
          <video
            :src="currentMedia.file_url || undefined"
            class="media-video"
            controls
            :autoplay="autoplay"
            :muted="autoplay"
            playsinline
            preload="metadata"
            @play="$emit('play')"
            @ended="$emit('complete')"
          />
        </template>
        <img
          v-else-if="currentMedia && currentMediaKind === 'image'"
          :src="currentMedia.file_url || undefined"
          :alt="resource.title"
          class="media-image"
        />
        <div v-else-if="currentMedia && currentMediaKind === 'document'" class="media-document">
          <iframe :src="currentMedia.file_url || undefined" class="doc-frame" title="资源文档预览" />
          <a-button type="link" @click.stop="openCurrentMedia">打开文档</a-button>
        </div>
        <a-empty v-else description="暂无可预览文件" />
      </div>

      <div v-if="$slots.actions" class="viewer-actions-slot">
        <slot name="actions" />
      </div>

      <div v-if="mediaList.length > 1" class="viewer-nav">
        <a-button size="small" @click="prevMedia">上一个文件</a-button>
        <span>{{ mediaIndex + 1 }} / {{ mediaList.length }}</span>
        <a-button size="small" @click="nextMedia">下一个文件</a-button>
      </div>

      <div class="viewer-meta">
        <span>上传者：{{ resource.uploader_name || '-' }}</span>
        <span>标签：{{ formatTagList(resource.tags) }}</span>
      </div>
    </a-card>

    <div v-else class="recommend-shell" @click="$emit('click')">
      <div class="recommend-stage" @touchstart="onMediaTouchStart" @touchend="onMediaTouchEnd">
        <template v-if="currentMedia && currentMediaKind === 'video'">
          <video
            ref="recommendVideoRef"
            :src="currentMedia.file_url || undefined"
            class="media-video"
            controls
            autoplay
            muted
            playsinline
            @play="$emit('play')"
            @ended="$emit('complete')"
          />
          <button
            v-if="isMobile"
            type="button"
            class="recommend-playback-toggle"
            aria-label="切换视频播放状态"
            @click.stop="toggleRecommendPlayback"
          />
        </template>
        <img
          v-else-if="currentMedia && currentMediaKind === 'image'"
          :src="currentMedia.file_url || undefined"
          :alt="resource.title"
          class="media-image static-preview-media"
        />
        <div v-else-if="currentMedia && currentMediaKind === 'document'" class="media-document full static-preview-media">
          <iframe :src="currentMedia.file_url || undefined" class="doc-frame static-preview-frame" title="资源文档预览" />
        </div>
        <a-empty v-else description="暂无可预览文件" />

        <div class="recommend-info-card" :class="{ 'is-video': currentMediaKind === 'video' }">
          <h3 class="recommend-title">{{ resource.title }}</h3>
          <p class="recommend-author">作者：{{ resource.uploader_name || '平台资源' }}</p>
          <p class="recommend-summary">简介：{{ resource.summary || '暂无简介' }}</p>
          <p v-if="resource.tags?.length" class="recommend-tags"># {{ resource.tags.join(' # ') }}</p>
          <p v-if="recommendPreviewTip" class="recommend-preview-tip">{{ recommendPreviewTip }}</p>
        </div>

        <div v-if="mediaList.length > 1" class="recommend-nav">
          <button type="button" class="nav-btn" @click.stop="prevMedia">‹</button>
          <button type="button" class="nav-btn" @click.stop="nextMedia">›</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ResourceDetailResponse } from '@/api/learning-resource'
import { useMobile } from '@/composables/useMobile'
import { detectMediaKind, formatTagList, getResourceContentTypeLabel } from '@/utils/learning-resource'

const props = withDefaults(defineProps<{
  resource: ResourceDetailResponse | null
  mode?: 'detail' | 'recommend'
  autoplay?: boolean
  compact?: boolean
  theme?: 'default' | 'dark'
}>(), {
  resource: null,
  mode: 'detail',
  autoplay: false,
  compact: false,
  theme: 'default',
})

defineEmits<{
  click: []
  play: []
  complete: []
}>()

const mediaIndex = ref(0)
const mediaTouch = ref({ startX: 0, startY: 0 })
const recommendVideoRef = ref<HTMLVideoElement | null>(null)
const { isMobile } = useMobile()

const mediaList = computed(() => props.resource?.media_links || [])
const currentMedia = computed(() => mediaList.value[mediaIndex.value] || null)
const currentMediaKind = computed(() => detectMediaKind(currentMedia.value?.file_url))
const recommendPreviewTip = computed(() => {
  if (props.mode !== 'recommend' || !currentMedia.value || currentMediaKind.value === 'video') {
    return ''
  }

  if (currentMediaKind.value === 'document') {
    return '社区内仅展示单屏课件预览，更多页数请点详情查看'
  }

  return '社区内仅展示单屏内容预览，完整内容请点详情查看'
})

watch(() => props.resource?.id, () => {
  mediaIndex.value = 0
  recommendVideoRef.value = null
})

function prevMedia() {
  if (!mediaList.value.length) {
    return
  }
  mediaIndex.value = (mediaIndex.value - 1 + mediaList.value.length) % mediaList.value.length
}

function nextMedia() {
  if (!mediaList.value.length) {
    return
  }
  mediaIndex.value = (mediaIndex.value + 1) % mediaList.value.length
}

function openCurrentMedia() {
  if (!currentMedia.value?.file_url) {
    return
  }
  window.open(currentMedia.value.file_url, '_blank', 'noopener,noreferrer')
}

async function toggleRecommendPlayback() {
  const video = recommendVideoRef.value
  if (!video) {
    return
  }

  if (video.paused) {
    try {
      await video.play()
    } catch {
      // ignore autoplay/play interruption
    }
    return
  }

  video.pause()
}

function onMediaTouchStart(event: TouchEvent) {
  const touch = event.touches?.[0]
  if (!touch) {
    return
  }
  mediaTouch.value = {
    startX: touch.clientX,
    startY: touch.clientY,
  }
}

function onMediaTouchEnd(event: TouchEvent) {
  const touch = event.changedTouches?.[0]
  if (!touch) {
    return
  }

  const deltaX = touch.clientX - mediaTouch.value.startX
  const deltaY = touch.clientY - mediaTouch.value.startY
  if (Math.abs(deltaX) < 60 || Math.abs(deltaX) <= Math.abs(deltaY)) {
    return
  }

  if (deltaX < 0) {
    nextMedia()
    return
  }
  prevMedia()
}
</script>

<style scoped>
.resource-viewer.mode-recommend {
  display: flex;
  flex: 1 1 auto;
  width: 100%;
  height: var(--community-stage-height, 100%);
  min-width: 0;
  min-height: var(--community-stage-height, 100%);
}

.viewer-card {
  border-radius: var(--v2-radius-lg);
}

.resource-viewer.compact .viewer-card :deep(.ant-card-body) {
  padding: 18px !important;
}

.viewer-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.viewer-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 8px;
}

.viewer-summary {
  color: var(--v2-text-secondary);
  line-height: 1.7;
}

.resource-viewer.compact .viewer-head {
  gap: 12px;
  margin-bottom: 12px;
}

.resource-viewer.compact .viewer-title {
  margin-bottom: 4px;
  font-size: 20px;
}

.resource-viewer.compact .viewer-summary {
  line-height: 1.6;
}

.viewer-stage,
.recommend-stage {
  position: relative;
  border-radius: var(--v2-radius);
  overflow: hidden;
  background: transparent;
}

.viewer-stage {
  min-height: 320px;
}

.resource-viewer.compact .viewer-stage {
  min-height: 240px;
}

.viewer-actions-slot {
  margin-top: 12px;
}

.resource-viewer.compact .viewer-actions-slot {
  margin-top: 10px;
}

.media-video,
.media-image {
  width: 100%;
  max-height: 70vh;
  display: block;
  object-fit: contain;
  background: transparent;
}

.resource-viewer.compact .media-video,
.resource-viewer.compact .media-image {
  max-height: min(54vh, 460px);
}

.media-document {
  background: #fff;
  padding: 12px;
}

.resource-viewer.compact .media-document {
  padding: 0;
}

.media-document.full {
  height: 100%;
}

.doc-frame {
  width: 100%;
  min-height: 70vh;
  border: 0;
  background: #fff;
}

.viewer-nav,
.viewer-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.resource-viewer.compact .viewer-nav,
.resource-viewer.compact .viewer-meta {
  margin-top: 10px;
}

.resource-viewer.theme-dark .viewer-card {
  background: linear-gradient(180deg, rgba(18, 18, 20, 0.96) 0%, rgba(10, 10, 11, 0.94) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 20px 42px rgba(0, 0, 0, 0.32);
}

.resource-viewer.theme-dark .viewer-title {
  color: #fff;
}

.resource-viewer.theme-dark .viewer-summary,
.resource-viewer.theme-dark .viewer-meta,
.resource-viewer.theme-dark .viewer-nav {
  color: rgba(255, 255, 255, 0.7);
}

.resource-viewer.theme-dark .viewer-stage {
  background: #000;
}

.resource-viewer.theme-dark .media-video,
.resource-viewer.theme-dark .media-image {
  background: #000;
}

.resource-viewer.theme-dark .media-document {
  background: #0b0b0c;
}

.resource-viewer.theme-dark .doc-frame {
  background: #fff;
}

.resource-viewer.theme-dark .viewer-card :deep(.ant-tag) {
  color: rgba(255, 255, 255, 0.92);
  border-color: rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.08);
}

.recommend-shell {
  display: flex;
  flex: 1 1 auto;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
}

.recommend-stage {
  display: flex;
  flex: 1 1 auto;
  align-items: stretch;
  align-self: stretch;
  justify-content: stretch;
  height: var(--community-stage-height, 100%);
  width: 100%;
  min-width: 0;
  min-height: var(--community-stage-height, 100%);
  background: #000;
}

.recommend-info-card {
  position: absolute;
  left: 16px;
  right: 110px;
  bottom: 14px;
  z-index: 12;
  width: min(620px, calc(100% - 168px));
  padding: 0;
  background: transparent;
  box-shadow: none;
  color: #fff;
  pointer-events: none;
}

.recommend-info-card.is-video {
  bottom: 74px;
}

.recommend-title {
  margin-bottom: 8px;
  font-size: 27px;
  line-height: 1.22;
  color: #fff;
  text-shadow:
    0 2px 6px rgba(0, 0, 0, 0.88),
    0 0 20px rgba(0, 0, 0, 0.42);
}

.recommend-author,
.recommend-summary,
.recommend-tags {
  margin-bottom: 6px;
  line-height: 1.65;
  color: rgba(255, 255, 255, 0.94);
  text-shadow:
    0 1px 4px rgba(0, 0, 0, 0.84),
    0 0 16px rgba(0, 0, 0, 0.34);
}

.recommend-author {
  font-weight: 700;
}

.recommend-tags {
  margin-bottom: 0;
  color: rgba(255, 255, 255, 0.84);
}

.recommend-preview-tip {
  display: inline-flex;
  margin-top: 10px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.42);
  color: rgba(255, 255, 255, 0.96);
  font-size: 12px;
  line-height: 1.5;
  letter-spacing: 0.01em;
  backdrop-filter: blur(10px);
}

.recommend-nav {
  position: absolute;
  top: 50%;
  left: 16px;
  right: 16px;
  display: flex;
  justify-content: space-between;
  transform: translateY(-50%);
  pointer-events: none;
}

.recommend-playback-toggle {
  position: absolute;
  top: 50%;
  left: 50%;
  z-index: 8;
  width: min(44vw, 220px);
  height: min(44vw, 220px);
  transform: translate(-50%, -50%);
  border: 0;
  border-radius: 999px;
  background: transparent;
  cursor: pointer;
}

.nav-btn {
  width: 40px;
  height: 40px;
  border: 0;
  border-radius: 50%;
  background: rgba(39, 49, 58, 0.48);
  color: #fff;
  font-size: 24px;
  cursor: pointer;
  backdrop-filter: blur(8px);
  pointer-events: auto;
}

.mode-recommend .media-video,
.mode-recommend .media-image {
  flex: 1;
  display: block;
  height: var(--community-stage-height, 100%);
  width: 100%;
  align-self: stretch;
  min-width: 0;
  min-height: var(--community-stage-height, 100%);
  max-width: none;
  max-height: none;
  object-fit: contain;
  background: #000;
}

.mode-recommend .media-document.full {
  display: flex;
  flex: 1 1 auto;
  width: 100%;
  height: var(--community-stage-height, 100%);
  align-self: stretch;
  min-width: 0;
  min-height: var(--community-stage-height, 100%);
}

.mode-recommend .doc-frame {
  min-height: var(--community-stage-height, 100%);
  height: var(--community-stage-height, 100%);
  width: 100%;
}

.mode-recommend .static-preview-media,
.mode-recommend .static-preview-frame {
  pointer-events: none;
  user-select: none;
  -webkit-user-select: none;
}

.mode-recommend .static-preview-media {
  touch-action: none;
}

.mode-recommend .media-document.full.static-preview-media {
  padding: 0;
  overflow: hidden;
}

.mode-recommend .recommend-stage,
.mode-recommend .media-video,
.mode-recommend .media-image,
.mode-recommend .media-document.full,
.mode-recommend .doc-frame {
  border-radius: 0;
}

@media (max-width: 768px) {
  .viewer-head,
  .viewer-nav,
  .viewer-meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .recommend-shell,
  .recommend-stage {
    height: 100%;
    min-height: 0;
  }

  .recommend-info-card {
    left: 14px;
    right: 86px;
    bottom: 8px;
    width: auto;
  }

  .recommend-info-card.is-video {
    bottom: 62px;
  }

  .recommend-title {
    font-size: 20px;
  }

  .recommend-playback-toggle {
    width: min(48vw, 180px);
    height: min(48vw, 180px);
  }

  .recommend-author,
  .recommend-summary,
  .recommend-tags {
    font-size: 13px;
  }

  .resource-viewer.compact .viewer-card :deep(.ant-card-body) {
    padding: 14px !important;
  }

  .resource-viewer.compact .viewer-title {
    font-size: 18px;
  }

  .resource-viewer.compact .viewer-stage {
    min-height: 210px;
  }

  .viewer-actions-slot {
    margin-top: 10px;
  }

  .resource-viewer.compact .media-video,
  .resource-viewer.compact .media-image {
    max-height: 38vh;
  }
}
</style>
