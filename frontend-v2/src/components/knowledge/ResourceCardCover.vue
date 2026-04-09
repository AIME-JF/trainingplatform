<template>
  <div
    class="resource-card-cover"
    :class="[
      `type-${normalizedType}`,
      { 'media-ready': mediaReady, 'video-cover': isVideo, 'image-cover': isImage },
    ]"
  >
    <img
      v-if="isImage && coverUrl"
      class="cover-media"
      :src="coverUrl"
      :alt="`${title}封面`"
      @load="handleMediaReady"
      @error="handleMediaError"
    />

    <video
      v-else-if="isVideo && coverUrl"
      ref="videoRef"
      class="cover-media cover-video"
      :src="coverUrl"
      :aria-label="`${title}视频封面`"
      muted
      playsinline
      preload="metadata"
      disablepictureinpicture
      @loadedmetadata="handleVideoLoadedMetadata"
      @loadeddata="handleVideoLoadedData"
      @seeked="handleMediaReady"
      @error="handleMediaError"
    />

    <div class="cover-fallback">
      <div class="fallback-glow" />
      <div class="fallback-content">
        <component :is="fallbackIcon" class="fallback-icon" />
        <span class="fallback-label">{{ contentTypeLabel }}</span>
      </div>
    </div>

    <div class="cover-shade" />

    <div v-if="!props.minimal" class="cover-head">
      <span class="cover-type-pill">{{ contentTypeLabel }}</span>
      <a-tag class="cover-status-tag" color="blue">{{ statusLabel }}</a-tag>
    </div>

    <div v-if="isVideo" class="video-indicator">
      <PlayCircleFilled class="video-indicator-icon" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { FileTextOutlined, PictureOutlined, PlayCircleFilled, VideoCameraOutlined } from '@ant-design/icons-vue'
import { detectMediaKind, getResourceContentTypeLabel } from '@/utils/learning-resource'

const props = withDefaults(defineProps<{
  title: string
  contentType?: string | null
  coverUrl?: string | null
  statusLabel?: string
  minimal?: boolean
}>(), {
  contentType: '',
  coverUrl: '',
  statusLabel: '已发布',
  minimal: false,
})

const videoRef = ref<HTMLVideoElement | null>(null)
const mediaReady = ref(false)

const normalizedType = computed(() => {
  if (props.contentType === 'image_text') {
    return 'image'
  }
  if (props.contentType) {
    return props.contentType
  }
  return detectMediaKind(props.coverUrl)
})

const contentTypeLabel = computed(() => getResourceContentTypeLabel(normalizedType.value))
const isVideo = computed(() => normalizedType.value === 'video')
const isImage = computed(() => normalizedType.value === 'image')
const fallbackIcon = computed(() => {
  if (isVideo.value) {
    return VideoCameraOutlined
  }
  if (isImage.value) {
    return PictureOutlined
  }
  return FileTextOutlined
})

watch(
  () => [props.coverUrl, props.contentType],
  () => {
    mediaReady.value = false
  },
  { immediate: true },
)

function handleMediaReady() {
  mediaReady.value = true
}

function handleMediaError() {
  mediaReady.value = false
}

function handleVideoLoadedData() {
  mediaReady.value = true
}

function handleVideoLoadedMetadata(event: Event) {
  const video = (event.target as HTMLVideoElement | null) || videoRef.value
  if (!video) {
    return
  }

  const duration = Number.isFinite(video.duration) ? Number(video.duration) : 0
  const targetTime = duration > 0.3 ? Math.min(duration * 0.08, 0.8) : 0.01

  if (targetTime <= 0) {
    mediaReady.value = true
    return
  }

  try {
    video.currentTime = targetTime
  } catch {
    mediaReady.value = true
  }
}
</script>

<style scoped>
.resource-card-cover {
  position: relative;
  isolation: isolate;
  height: 164px;
  overflow: hidden;
  background: var(--v2-cover-blue);
}

.cover-media,
.cover-fallback,
.cover-shade {
  position: absolute;
  inset: 0;
}

.cover-media {
  z-index: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  background: #d8dfed;
  transition:
    opacity 0.24s ease,
    transform 0.35s ease;
}

.resource-card-cover.media-ready .cover-media {
  opacity: 1;
}

.resource-card-cover:hover .cover-media {
  transform: scale(1.03);
}

.cover-fallback {
  z-index: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--v2-cover-blue);
  transition: opacity 0.24s ease;
}

.resource-card-cover.media-ready .cover-fallback {
  opacity: 0;
}

.fallback-glow {
  position: absolute;
  inset: auto auto -32px -26px;
  width: 140px;
  height: 140px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  filter: blur(18px);
}

.fallback-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.88);
}

.fallback-icon {
  font-size: 34px;
}

.fallback-label {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.cover-shade {
  z-index: 1;
  background: linear-gradient(180deg, rgba(10, 18, 30, 0.12), rgba(10, 18, 30, 0.28));
  pointer-events: none;
}

.cover-head {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
}

.cover-type-pill {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.84);
  color: #1f2937;
  font-size: 13px;
  font-weight: 700;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(10px);
}

:deep(.cover-status-tag.ant-tag) {
  margin: 0;
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: 700;
  box-shadow: 0 8px 18px rgba(59, 130, 246, 0.14);
  backdrop-filter: blur(10px);
}

.video-indicator {
  position: absolute;
  right: 14px;
  bottom: 14px;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.52);
  color: #fff;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.18);
  backdrop-filter: blur(10px);
  pointer-events: none;
}

.video-indicator-icon {
  font-size: 22px;
}

.type-video .cover-fallback {
  background: linear-gradient(145deg, #465a7f, #293757 58%, #182338);
}

.type-image .cover-fallback {
  background: linear-gradient(145deg, #4a7d6a, #275545 58%, #173d31);
}

.type-document .cover-fallback,
.type-unknown .cover-fallback {
  background: linear-gradient(145deg, #5e6786, #39425d 58%, #242d44);
}
</style>
