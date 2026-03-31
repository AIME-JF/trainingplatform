<template>
  <div v-if="resource" class="resource-viewer" :class="`mode-${mode}`">
    <a-card v-if="!isRecommend" :bordered="false" class="resource-viewer-card" :class="{ 'media-only-card': isMediaOnly }">
      <div v-if="!isMediaOnly" class="resource-viewer-header">
        <div>
          <h2 class="resource-title">{{ resource.title }}</h2>
          <p class="resource-summary">{{ resource.summary || '暂无摘要' }}</p>
        </div>
        <a-tag color="blue">{{ contentTypeLabel(resource.contentType) }}</a-tag>
      </div>

      <div class="resource-viewer-media" :class="{ 'media-only-view': isMediaOnly }">
        <div
          class="resource-viewer-media-stage"
          @touchstart="onMediaTouchStart"
          @touchend="onMediaTouchEnd"
          @click="$emit('click')"
        >
          <div
            v-if="currentMedia && currentMediaKind === 'video'"
            ref="videoContainer"
            class="xgplayer-container"
          />

          <img
            v-else-if="currentMedia && currentMediaKind === 'image'"
            class="media-image"
            :src="currentMedia.fileUrl"
            :alt="resource.title"
          />

          <div v-else-if="currentMedia && currentMediaKind === 'document'" class="media-document">
            <iframe class="doc-frame" :src="currentMedia.fileUrl" title="资源文档预览" />
            <a-button type="link" @click="downloadCurrentMedia">下载文档</a-button>
          </div>

          <a-empty v-else description="暂无可预览文件" />
        </div>

        <div class="media-nav" v-if="mediaList.length > 1 && !isMediaOnly">
          <a-button size="small" @click="prevMedia">上一个文件</a-button>
          <span>{{ mediaIndex + 1 }} / {{ mediaList.length }}</span>
          <a-button size="small" @click="nextMedia">下一个文件</a-button>
        </div>
      </div>

      <div v-if="!isMediaOnly" class="resource-meta">
        <div>上传者：{{ resource.uploaderName || '-' }}</div>
        <div>标签：{{ (resource.tags || []).join(' / ') || '-' }}</div>
      </div>
    </a-card>

    <div v-else class="recommend-viewer-shell" @click="$emit('click')">
      <div
        class="recommend-media-stage"
        @touchstart="onMediaTouchStart"
        @touchend="onMediaTouchEnd"
      >
        <div
          v-if="currentMedia && currentMediaKind === 'video'"
          ref="videoContainer"
          class="xgplayer-container"
        />

        <img
          v-else-if="currentMedia && currentMediaKind === 'image'"
          class="media-image"
          :src="currentMedia.fileUrl"
          :alt="resource.title"
        />

        <div v-else-if="currentMedia && currentMediaKind === 'document'" class="media-document">
          <iframe class="doc-frame" :src="currentMedia.fileUrl" title="资源文档预览" />
          <a-button type="link" @click.stop="downloadCurrentMedia">下载文档</a-button>
        </div>

        <a-empty v-else description="暂无可预览文件" />

        <div class="recommend-topbar">
          <a-tag color="blue">{{ contentTypeLabel(resource.contentType) }}</a-tag>
          <span v-if="mediaList.length > 1" class="recommend-media-index">{{ mediaIndex + 1 }} / {{ mediaList.length }}</span>
        </div>

        <div class="recommend-info">
          <h3 class="recommend-title">{{ resource.title }}</h3>
          <p class="recommend-summary">{{ resource.summary || '暂无摘要' }}</p>
          <p class="recommend-meta">上传者：{{ resource.uploaderName || '-' }}</p>
          <p class="recommend-tags" v-if="resource.tags?.length"># {{ resource.tags.join(' # ') }}</p>
        </div>

        <div class="recommend-media-nav" v-if="mediaList.length > 1">
          <button class="media-nav-btn" type="button" @click.stop="prevMedia">‹</button>
          <button class="media-nav-btn" type="button" @click.stop="nextMedia">›</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import Player from 'xgplayer'
import 'xgplayer/dist/index.min.css'

const props = defineProps({
  resource: {
    type: Object,
    default: null,
  },
  mode: {
    type: String,
    default: 'detail',
  },
  mediaOnly: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['play', 'complete', 'click'])

const mediaIndex = ref(0)
const mediaTouch = ref({ startX: 0, startY: 0 })
const videoContainer = ref(null)

let player = null

const isRecommend = computed(() => props.mode === 'recommend')
const isMediaOnly = computed(() => props.mediaOnly && !isRecommend.value)
const mediaList = computed(() => props.resource?.mediaLinks || [])
const currentMedia = computed(() => mediaList.value[mediaIndex.value] || null)
const currentMediaKind = computed(() => getMediaKind(currentMedia.value?.fileUrl))

watch(
  () => props.resource?.id,
  () => {
    mediaIndex.value = 0
  }
)

watch(
  () => [currentMedia.value?.fileUrl, currentMediaKind.value, props.mode],
  async () => {
    await nextTick()
    setupPlayer()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  destroyPlayer()
})

function setupPlayer() {
  destroyPlayer()

  if (currentMediaKind.value !== 'video' || !currentMedia.value?.fileUrl || !videoContainer.value) {
    return
  }

  player = new Player({
    el: videoContainer.value,
    url: currentMedia.value.fileUrl,
    fluid: !isRecommend.value,
    autoplay: isRecommend.value,
    autoplayMuted: isRecommend.value,
    playsinline: true,
    videoInit: true,
    download: false,
    pip: true,
    cssFullscreen: true,
    screenShot: false,
    width: '100%',
    height: '100%',
    playbackRate: [0.75, 1, 1.25, 1.5],
    ignores: ['poster', 'fullscreen'],
  })

  player.on('play', () => {
    emit('play')
  })

  player.on('ended', () => {
    emit('complete')
  })

  if (isRecommend.value) {
    void tryAutoPlay(player)
  }
}

function destroyPlayer() {
  if (!player) return
  player.destroy()
  player = null
}

function contentTypeLabel(contentType) {
  const map = {
    video: '视频',
    document: '文档',
    image: '图片',
    image_text: '图片',
  }
  return map[contentType] || contentType || '-'
}

function getExtension(url) {
  if (!url) return ''
  const cleanUrl = url.split('?')[0].split('#')[0]
  const dot = cleanUrl.lastIndexOf('.')
  return dot >= 0 ? cleanUrl.slice(dot + 1).toLowerCase() : ''
}

function getMediaKind(url) {
  const ext = getExtension(url)
  if (ext === 'mp4') return 'video'
  if (['jpg', 'jpeg', 'png', 'webp'].includes(ext)) return 'image'
  if (['pdf', 'doc', 'docx', 'ppt', 'pptx', 'html', 'htm'].includes(ext)) return 'document'
  return 'unknown'
}

function prevMedia() {
  if (!mediaList.value.length) return
  mediaIndex.value = (mediaIndex.value - 1 + mediaList.value.length) % mediaList.value.length
}

function nextMedia() {
  if (!mediaList.value.length) return
  mediaIndex.value = (mediaIndex.value + 1) % mediaList.value.length
}

async function tryAutoPlay(targetPlayer) {
  if (!targetPlayer) return
  try {
    const playResult = targetPlayer.play?.()
    if (playResult && typeof playResult.then === 'function') {
      await playResult
    }
  } catch {
    // Browser may block autoplay until user interaction.
  }
}

function downloadCurrentMedia() {
  if (!currentMedia.value?.fileUrl) return
  const url = currentMedia.value.fileUrl
  const link = document.createElement('a')
  link.href = url
  link.download = ''
  link.target = '_blank'
  link.rel = 'noopener noreferrer'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function onMediaTouchStart(event) {
  const touch = event.touches?.[0]
  if (!touch) return
  mediaTouch.value = { startX: touch.clientX, startY: touch.clientY }
}

function onMediaTouchEnd(event) {
  const touch = event.changedTouches?.[0]
  if (!touch) return

  const deltaX = touch.clientX - mediaTouch.value.startX
  const deltaY = touch.clientY - mediaTouch.value.startY
  if (Math.abs(deltaX) < 60 || Math.abs(deltaX) <= Math.abs(deltaY)) return

  if (deltaX < 0) {
    nextMedia()
  } else {
    prevMedia()
  }
}

defineExpose({
  nextMedia,
  prevMedia,
})
</script>

<style scoped>
.resource-viewer {
  width: 100%;
}

.resource-viewer-card {
  margin-bottom: 16px;
}

.resource-viewer-card.media-only-card {
  margin-bottom: 0;
}

.resource-viewer-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.resource-title {
  margin: 0 0 8px;
}

.resource-summary {
  margin: 0;
  color: #666;
}

.resource-viewer-media {
  background: #f8f9fc;
  border-radius: 8px;
  padding: 12px;
}

.resource-viewer-media.media-only-view {
  background: #000;
  border-radius: 10px;
  padding: 0;
}

.resource-viewer-media-stage {
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  touch-action: pan-y;
}

.xgplayer-container,
.media-image {
  width: 100%;
  max-height: 520px;
  border-radius: 6px;
  overflow: hidden;
}

.media-image {
  object-fit: contain;
}

.media-document {
  width: 100%;
}

.doc-frame {
  width: 100%;
  min-height: 520px;
  border: 1px solid #eee;
  border-radius: 6px;
}

.media-nav {
  margin-top: 10px;
  display: flex;
  justify-content: center;
  gap: 12px;
  align-items: center;
}

.resource-meta {
  margin-top: 12px;
  color: #666;
  font-size: 13px;
  display: grid;
  gap: 6px;
}

.mode-recommend .recommend-viewer-shell {
  width: 100%;
  height: 100%;
  min-height: 0;
}

.mode-recommend .recommend-media-stage {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  overflow: hidden;
  touch-action: pan-y;
}

.mode-recommend .xgplayer-container,
.mode-recommend .media-image,
.mode-recommend .media-document,
.mode-recommend .doc-frame {
  width: 100%;
  height: 100%;
  max-height: none;
  max-width: 100%;
  border: 0;
  border-radius: 0;
}

.mode-recommend .xgplayer-container :deep(.xgplayer),
.mode-recommend .xgplayer-container :deep(video) {
  width: 100% !important;
  height: 100% !important;
  max-height: 100% !important;
}

.mode-recommend .xgplayer-container :deep(video) {
  object-fit: contain !important;
}

.mode-recommend .media-image {
  object-fit: contain;
}

.recommend-topbar {
  position: absolute;
  top: 14px;
  left: 14px;
  right: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  pointer-events: none;
}

.recommend-media-index {
  color: #fff;
  font-size: 13px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.55);
}

.recommend-info {
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: calc(14px + var(--player-control-safe-offset, 56px));
  color: #fff;
  z-index: 2;
  padding: 48px 12px 10px;
  border-radius: 8px;
  pointer-events: none;
}

.recommend-title {
  margin: 0;
  font-size: 18px;
  line-height: 1.4;
}

.recommend-summary {
  margin: 8px 0 0;
  font-size: 13px;
  line-height: 1.5;
  opacity: 0.95;
}

.recommend-meta,
.recommend-tags {
  margin: 6px 0 0;
  font-size: 12px;
  opacity: 0.9;
}

.recommend-media-nav {
  position: absolute;
  top: 50%;
  left: 8px;
  right: 8px;
  transform: translateY(-50%);
  display: flex;
  justify-content: space-between;
  pointer-events: none;
}

.media-nav-btn {
  pointer-events: auto;
  width: 34px;
  height: 34px;
  border: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 22px;
  line-height: 34px;
  text-align: center;
}

@media (max-width: 768px) {
  .resource-viewer-header {
    flex-direction: column;
  }

  .resource-viewer-media-stage {
    min-height: 220px;
  }

  .doc-frame {
    min-height: 360px;
  }

  .recommend-title {
    font-size: 16px;
  }

  .recommend-summary {
    font-size: 12px;
  }
}
</style>
