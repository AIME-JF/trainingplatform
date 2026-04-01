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

        <div class="recommend-top">
          <a-tag color="blue">{{ getResourceContentTypeLabel(resource.content_type) }}</a-tag>
          <span v-if="mediaList.length > 1">{{ mediaIndex + 1 }} / {{ mediaList.length }}</span>
        </div>

        <div class="recommend-info">
          <h3>{{ resource.title }}</h3>
          <p>{{ resource.summary || '暂无摘要' }}</p>
          <span>上传者：{{ resource.uploader_name || '-' }}</span>
          <p v-if="resource.tags?.length" class="recommend-tags"># {{ resource.tags.join(' # ') }}</p>
          <div v-if="currentMediaKind === 'document' && currentMedia?.file_url" class="recommend-actions">
            <a-button size="small" @click.stop="openCurrentMedia">打开文档</a-button>
          </div>
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
  background: #000;
  min-height: 320px;
}

.media-video,
.media-image {
  width: 100%;
  max-height: 70vh;
  display: block;
  object-fit: contain;
  background: #000;
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
  min-height: calc(100vh - 140px);
}

.recommend-stage {
  min-height: calc(100vh - 140px);
}

.recommend-top {
  position: absolute;
  top: 16px;
  left: 16px;
  right: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #fff;
}

.recommend-info {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 28px 20px 22px;
  color: #fff;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0) 0%, rgba(0, 0, 0, 0.78) 100%);
}

.recommend-info h3 {
  font-size: 22px;
  margin-bottom: 8px;
}

.recommend-info p {
  margin-bottom: 8px;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.6;
}

.recommend-tags {
  margin: 10px 0 0;
  color: rgba(255, 255, 255, 0.92);
}

.recommend-actions {
  margin-top: 12px;
}

.recommend-nav {
  position: absolute;
  top: 50%;
  left: 16px;
  right: 16px;
  display: flex;
  justify-content: space-between;
  transform: translateY(-50%);
}

.nav-btn {
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 22px;
  cursor: pointer;
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
    min-height: calc(100vh - 170px);
  }
}
</style>
