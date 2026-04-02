<template>
  <div class="gesture-pattern" :style="{ width: size + 'px', height: size + 'px' }">
    <canvas ref="canvasRef" :width="size" :height="size" class="gesture-canvas" />
    <div
      v-for="(dot, idx) in 9"
      :key="idx"
      class="gesture-dot"
      :class="{ active: modelValue.includes(idx) }"
      :style="getDotStyle(idx)"
      @mousedown.prevent="onDotStart(idx)"
      @touchstart.prevent="onDotStart(idx)"
    >
      <div class="dot-inner" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onBeforeUnmount, nextTick } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: number[]
    readonly?: boolean
    size?: number
    theme?: 'dark' | 'light'
  }>(),
  {
    readonly: false,
    size: 240,
    theme: 'dark',
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: number[]]
  complete: [value: number[]]
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const drawing = ref(false)
const currentPos = ref<{ x: number; y: number } | null>(null)

const dotSize = computed(() => props.size * 0.16)
const gap = computed(() => props.size / 3)

function getDotCenter(idx: number): { x: number; y: number } {
  const col = idx % 3
  const row = Math.floor(idx / 3)
  return {
    x: gap.value * col + gap.value / 2,
    y: gap.value * row + gap.value / 2,
  }
}

function getDotStyle(idx: number) {
  const center = getDotCenter(idx)
  const s = dotSize.value
  return {
    width: s + 'px',
    height: s + 'px',
    left: center.x - s / 2 + 'px',
    top: center.y - s / 2 + 'px',
  }
}

const colors = computed(() => {
  if (props.theme === 'light') {
    return {
      dotOuter: '#d0d5dd',
      dotInner: '#f0f2f5',
      activeBorder: '#1677ff',
      activeInner: '#1677ff',
      line: 'rgba(22, 119, 255, 0.5)',
    }
  }
  return {
    dotOuter: '#2a3a5c',
    dotInner: '#8899bb',
    activeBorder: '#4fc3f7',
    activeInner: '#ffffff',
    line: 'rgba(79, 195, 247, 0.6)',
  }
})

function drawCanvas() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  ctx.clearRect(0, 0, props.size, props.size)

  const path = props.modelValue
  if (path.length < 1) return

  ctx.strokeStyle = colors.value.line
  ctx.lineWidth = 3
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'

  ctx.beginPath()
  for (let i = 0; i < path.length; i++) {
    const c = getDotCenter(path[i])
    if (i === 0) ctx.moveTo(c.x, c.y)
    else ctx.lineTo(c.x, c.y)
  }

  // Draw trailing line to current mouse/touch position while drawing
  if (drawing.value && currentPos.value) {
    ctx.lineTo(currentPos.value.x, currentPos.value.y)
  }

  ctx.stroke()
}

watch(
  () => [props.modelValue, props.size, props.theme, currentPos.value],
  () => {
    nextTick(drawCanvas)
  },
  { deep: true, immediate: true }
)

function getCanvasPos(e: MouseEvent | Touch): { x: number; y: number } | null {
  const canvas = canvasRef.value
  if (!canvas) return null
  const rect = canvas.getBoundingClientRect()
  return {
    x: (e.clientX - rect.left) * (props.size / rect.width),
    y: (e.clientY - rect.top) * (props.size / rect.height),
  }
}

function hitTest(pos: { x: number; y: number }): number | null {
  const radius = dotSize.value * 0.7
  for (let i = 0; i < 9; i++) {
    const c = getDotCenter(i)
    const dx = pos.x - c.x
    const dy = pos.y - c.y
    if (dx * dx + dy * dy <= radius * radius) return i
  }
  return null
}

function onDotStart(idx: number) {
  if (props.readonly) return
  drawing.value = true
  emit('update:modelValue', [idx])

  window.addEventListener('mousemove', onMove)
  window.addEventListener('mouseup', onEnd)
  window.addEventListener('touchmove', onTouchMove, { passive: false })
  window.addEventListener('touchend', onEnd)
  window.addEventListener('touchcancel', onEnd)
}

function onMove(e: MouseEvent) {
  if (!drawing.value) return
  const pos = getCanvasPos(e)
  if (!pos) return
  currentPos.value = pos
  const hit = hitTest(pos)
  if (hit !== null && !props.modelValue.includes(hit)) {
    emit('update:modelValue', [...props.modelValue, hit])
  }
}

function onTouchMove(e: TouchEvent) {
  e.preventDefault()
  if (!drawing.value || !e.touches.length) return
  const pos = getCanvasPos(e.touches[0])
  if (!pos) return
  currentPos.value = pos
  const hit = hitTest(pos)
  if (hit !== null && !props.modelValue.includes(hit)) {
    emit('update:modelValue', [...props.modelValue, hit])
  }
}

function onEnd() {
  if (!drawing.value) return
  drawing.value = false
  currentPos.value = null

  window.removeEventListener('mousemove', onMove)
  window.removeEventListener('mouseup', onEnd)
  window.removeEventListener('touchmove', onTouchMove)
  window.removeEventListener('touchend', onEnd)
  window.removeEventListener('touchcancel', onEnd)

  nextTick(drawCanvas)

  if (props.modelValue.length >= 2) {
    emit('complete', [...props.modelValue])
  }
}

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', onMove)
  window.removeEventListener('mouseup', onEnd)
  window.removeEventListener('touchmove', onTouchMove)
  window.removeEventListener('touchend', onEnd)
  window.removeEventListener('touchcancel', onEnd)
})
</script>

<style scoped>
.gesture-pattern {
  position: relative;
  user-select: none;
  touch-action: none;
}

.gesture-canvas {
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.gesture-dot {
  position: absolute;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.gesture-pattern[style] .gesture-dot {
  background: v-bind('colors.dotOuter');
  border: 2px solid transparent;
}

.gesture-pattern[style] .gesture-dot.active {
  border-color: v-bind('colors.activeBorder');
  box-shadow: 0 0 8px v-bind('colors.activeBorder');
}

.dot-inner {
  width: 36%;
  height: 36%;
  border-radius: 50%;
  background: v-bind('colors.dotInner');
  transition: background 0.15s;
}

.gesture-dot.active .dot-inner {
  background: v-bind('colors.activeInner');
}
</style>
