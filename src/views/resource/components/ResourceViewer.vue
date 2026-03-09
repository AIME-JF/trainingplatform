<template>
  <a-card :bordered="false" class="resource-viewer-card" v-if="resource">
    <div class="resource-viewer-header">
      <div>
        <h2 class="resource-title">{{ resource.title }}</h2>
        <p class="resource-summary">{{ resource.summary || '暂无摘要' }}</p>
      </div>
      <a-tag color="blue">{{ contentTypeLabel(resource.contentType) }}</a-tag>
    </div>

    <div class="resource-viewer-media">
      <div
        class="resource-viewer-media-stage"
        @touchstart="onMediaTouchStart"
        @touchend="onMediaTouchEnd"
      >
        <video
          v-if="currentMedia && currentMediaKind === 'video'"
          class="media-video"
          :src="currentMedia.fileUrl"
          controls
          preload="metadata"
          @play="$emit('play')"
          @ended="$emit('complete')"
        />

        <img
          v-else-if="currentMedia && currentMediaKind === 'image'"
          class="media-image"
          :src="currentMedia.fileUrl"
          :alt="resource.title"
          @click="$emit('click')"
        />

        <div v-else-if="currentMedia && currentMediaKind === 'document'" class="media-document">
          <iframe class="doc-frame" :src="currentMedia.fileUrl" title="资源文档预览" />
          <a-button type="link" @click="openCurrentMedia">新窗口打开文档</a-button>
        </div>

        <a-empty v-else description="暂无可预览文件" />
      </div>

      <div class="media-nav" v-if="mediaList.length > 1">
        <a-button size="small" @click="prevMedia">上一个文件</a-button>
        <span>{{ mediaIndex + 1 }} / {{ mediaList.length }}</span>
        <a-button size="small" @click="nextMedia">下一个文件</a-button>
      </div>
    </div>

    <div class="resource-meta">
      <div>上传者：{{ resource.uploaderName || '-' }}</div>
      <div>标签：{{ (resource.tags || []).join(' / ') || '-' }}</div>
    </div>
  </a-card>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  resource: {
    type: Object,
    default: null,
  },
})

defineEmits(['play', 'complete', 'click'])

const mediaIndex = ref(0)
const mediaTouch = ref({ startX: 0, startY: 0 })

const mediaList = computed(() => props.resource?.mediaLinks || [])
const currentMedia = computed(() => mediaList.value[mediaIndex.value] || null)

watch(
  () => props.resource?.id,
  () => {
    mediaIndex.value = 0
  }
)

const currentMediaKind = computed(() => getMediaKind(currentMedia.value?.fileUrl))

function contentTypeLabel(contentType) {
  const map = {
    video: '视频',
    document: '文档',
    image_text: '图文',
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
  if (['pdf', 'doc', 'docx', 'ppt', 'pptx'].includes(ext)) return 'document'
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

function openCurrentMedia() {
  if (!currentMedia.value?.fileUrl) return
  window.open(currentMedia.value.fileUrl, '_blank', 'noopener,noreferrer')
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
</script>

<style scoped>
.resource-viewer-card { margin-bottom: 16px; }
.resource-viewer-header { display: flex; justify-content: space-between; gap: 16px; margin-bottom: 12px; }
.resource-title { margin: 0 0 8px; }
.resource-summary { margin: 0; color: #666; }
.resource-viewer-media { background: #f8f9fc; border-radius: 8px; padding: 12px; }
.resource-viewer-media-stage { min-height: 320px; display: flex; align-items: center; justify-content: center; }
.media-video, .media-image { max-width: 100%; max-height: 520px; border-radius: 6px; }
.media-document { width: 100%; }
.doc-frame { width: 100%; min-height: 520px; border: 1px solid #eee; border-radius: 6px; }
.media-nav { margin-top: 10px; display: flex; justify-content: center; gap: 12px; align-items: center; }
.resource-meta { margin-top: 12px; color: #666; font-size: 13px; display: grid; gap: 6px; }

@media (max-width: 768px) {
  .resource-viewer-header { flex-direction: column; }
  .resource-viewer-media-stage { min-height: 220px; }
  .doc-frame { min-height: 360px; }
}
</style>
