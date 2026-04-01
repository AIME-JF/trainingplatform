<template>
  <div v-if="resource" class="resource-viewer" :class="`mode-${mode}`">
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
            :src="currentMedia.file_url || undefined"
            class="media-video"
            controls
            autoplay
            muted
            playsinline
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
        <div v-else-if="currentMedia && currentMediaKind === 'document'" class="media-document full">
          <iframe :src="currentMedia.file_url || undefined" class="doc-frame" title="资源文档预览" />
        </div>
        <a-empty v-else description="暂无可预览文件" />

        <div class="recommend-info-card" :class="{ 'is-video': currentMediaKind === 'video' }">
          <h3 class="recommend-title">{{ resource.title }}</h3>
          <p class="recommend-author">作者：{{ resource.uploader_name || '平台资源' }}</p>
          <p class="recommend-summary">简介：{{ resource.summary || '暂无简介' }}</p>
          <p v-if="resource.tags?.length" class="recommend-tags"># {{ resource.tags.join(' # ') }}</p>
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
import { detectMediaKind, formatTagList, getResourceContentTypeLabel } from '@/utils/learning-resource'

const props = withDefaults(defineProps<{
  resource: ResourceDetailResponse | null
  mode?: 'detail' | 'recommend'
}>(), {
  resource: null,
  mode: 'detail',
})

defineEmits<{
  click: []
  play: []
  complete: []
}>()

const mediaIndex = ref(0)
const mediaTouch = ref({ startX: 0, startY: 0 })

const mediaList = computed(() => props.resource?.media_links || [])
const currentMedia = computed(() => mediaList.value[mediaIndex.value] || null)
const currentMediaKind = computed(() => detectMediaKind(currentMedia.value?.file_url))

watch(() => props.resource?.id, () => {
  mediaIndex.value = 0
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
.viewer-card {
  border-radius: var(--v2-radius-lg);
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

.viewer-stage,
.recommend-stage {
  position: relative;
  border-radius: var(--v2-radius);
  overflow: hidden;
  background: transparent;
  min-height: 320px;
}

.media-video,
.media-image {
  width: 100%;
  max-height: 70vh;
  display: block;
  object-fit: contain;
  background: transparent;
}

.media-document {
  background: #fff;
  padding: 12px;
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

.recommend-shell {
  min-height: auto;
}

.recommend-stage {
  display: flex;
  align-items: stretch;
  justify-content: center;
  min-height: clamp(520px, calc(100vh - 260px), 840px);
}

.recommend-info-card {
  position: absolute;
  left: 18px;
  right: 118px;
  bottom: 18px;
  z-index: 12;
  width: min(620px, calc(100% - 168px));
  padding: 0;
  background: transparent;
  box-shadow: none;
  color: #fff;
  pointer-events: none;
}

.recommend-info-card.is-video {
  bottom: 92px;
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
  height: 100%;
  max-height: none;
}

.mode-recommend .media-document.full {
  width: 100%;
  height: clamp(520px, calc(100vh - 260px), 840px);
}

.mode-recommend .doc-frame {
  min-height: clamp(520px, calc(100vh - 260px), 840px);
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
    min-height: clamp(460px, calc(100vh - 310px), 720px);
  }

  .recommend-info-card {
    left: 14px;
    right: 86px;
    bottom: 10px;
    width: auto;
  }

  .recommend-info-card.is-video {
    bottom: 72px;
  }

  .recommend-title {
    font-size: 20px;
  }

  .recommend-author,
  .recommend-summary,
  .recommend-tags {
    font-size: 13px;
  }
}
</style>
