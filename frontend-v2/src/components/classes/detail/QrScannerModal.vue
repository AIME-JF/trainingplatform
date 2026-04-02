<template>
  <a-modal
    :open="visible"
    :title="title"
    :footer="null"
    width="400px"
    centered
    @update:open="(val: boolean) => emit('update:visible', val)"
  >
    <div class="qr-scanner">
      <!-- Submitting state -->
      <template v-if="submitting">
        <a-spin size="large" />
        <p class="scanner-hint">正在提交...</p>
      </template>

      <!-- Success state -->
      <template v-else-if="success">
        <CheckCircleOutlined class="scanner-icon scanner-icon--success" />
        <p class="scanner-title">{{ action === 'checkout' ? '签退成功' : '签到成功' }}</p>
      </template>

      <!-- Error state -->
      <template v-else-if="errorMsg">
        <CloseCircleOutlined class="scanner-icon scanner-icon--error" />
        <p class="scanner-title">操作失败</p>
        <p class="scanner-hint">{{ errorMsg }}</p>
        <a-button type="primary" size="small" @click="resetAndRetry">重新扫码</a-button>
      </template>

      <!-- Camera state -->
      <template v-else>
        <div class="scanner-video-container">
          <video ref="videoEl" autoplay playsinline muted class="scanner-video" />
          <canvas ref="canvasEl" class="scanner-canvas" />
          <div class="scanner-overlay">
            <div class="scanner-frame" />
          </div>
        </div>
        <p class="scanner-hint">将二维码置于框内自动识别</p>
        <p v-if="cameraError" class="scanner-error">{{ cameraError }}</p>
      </template>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted, nextTick } from 'vue'
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons-vue'
import jsQR from 'jsqr'
import { submitAttendanceByQr } from '@/services/attendance'

const props = defineProps<{
  visible: boolean
  action: 'checkin' | 'checkout'
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'refresh'): void
}>()

const videoEl = ref<HTMLVideoElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)
const cameraError = ref('')
const submitting = ref(false)
const success = ref(false)
const errorMsg = ref('')

let stream: MediaStream | null = null
let animFrameId = 0
let wasSuccess = false

const title = computed(() => props.action === 'checkout' ? '扫码签退' : '扫码签到')

watch(() => props.visible, (open) => {
  if (open) {
    resetState()
    // Wait for modal DOM to render before starting camera
    nextTick(() => {
      setTimeout(() => startCamera(), 150)
    })
  } else {
    stopCamera()
    if (wasSuccess) {
      wasSuccess = false
      emit('refresh')
    }
  }
})

function resetState() {
  submitting.value = false
  success.value = false
  errorMsg.value = ''
  cameraError.value = ''
}

function resetAndRetry() {
  resetState()
  nextTick(() => startCamera())
}

async function startCamera() {
  const video = videoEl.value
  if (!video) {
    // DOM not ready yet, retry
    if (props.visible) setTimeout(() => startCamera(), 100)
    return
  }
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 640 }, height: { ideal: 480 } },
    })
    video.srcObject = stream
    await video.play()
    scanLoop()
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === 'NotAllowedError') {
      cameraError.value = '请允许使用摄像头权限'
    } else {
      cameraError.value = '无法打开摄像头，请检查设备是否有摄像头或尝试使用 HTTPS 访问'
    }
  }
}

function stopCamera() {
  cancelAnimationFrame(animFrameId)
  animFrameId = 0
  if (stream) {
    stream.getTracks().forEach((t) => t.stop())
    stream = null
  }
  if (videoEl.value) {
    videoEl.value.srcObject = null
  }
}

function scanLoop() {
  const video = videoEl.value
  const canvas = canvasEl.value
  if (!video || !canvas || video.readyState < 2) {
    animFrameId = requestAnimationFrame(scanLoop)
    return
  }

  const ctx = canvas.getContext('2d', { willReadFrequently: true })
  if (!ctx) return

  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  ctx.drawImage(video, 0, 0)

  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
  const code = jsQR(imageData.data, imageData.width, imageData.height, {
    inversionAttempts: 'dontInvert',
  })

  if (code?.data) {
    handleQrResult(code.data)
    return
  }

  animFrameId = requestAnimationFrame(scanLoop)
}

async function handleQrResult(rawUrl: string) {
  stopCamera()

  // Extract token from URL like /attendance/{token}/{sessionKey?}
  const match = rawUrl.match(/\/attendance\/([^/]+)/)
  if (!match) {
    errorMsg.value = '无效的二维码，请扫描教官展示的出勤二维码'
    return
  }

  const token = match[1]
  submitting.value = true
  try {
    await submitAttendanceByQr(token)
    success.value = true
    wasSuccess = true
  } catch (err: unknown) {
    errorMsg.value = err instanceof Error ? err.message : '操作失败'
  } finally {
    submitting.value = false
  }
}

onUnmounted(() => {
  stopCamera()
})
</script>

<style scoped>
.qr-scanner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  min-height: 300px;
  justify-content: center;
}

.scanner-video-container {
  position: relative;
  width: 100%;
  max-width: 320px;
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: var(--v2-radius, 12px);
  background: #000;
}

.scanner-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.scanner-canvas {
  display: none;
}

.scanner-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.scanner-frame {
  width: 200px;
  height: 200px;
  border: 2px solid rgba(255, 255, 255, 0.7);
  border-radius: 12px;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.3);
}

.scanner-hint {
  font-size: 13px;
  color: var(--v2-text-muted, #AEAEB2);
  margin: 0;
  text-align: center;
}

.scanner-error {
  font-size: 13px;
  color: var(--v2-danger, #FF3B30);
  margin: 0;
  text-align: center;
}

.scanner-icon {
  font-size: 48px;
}

.scanner-icon--success {
  color: var(--v2-success, #34C759);
}

.scanner-icon--error {
  color: var(--v2-danger, #FF3B30);
}

.scanner-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--v2-text-primary, #1D1D1F);
  margin: 0;
}
</style>
