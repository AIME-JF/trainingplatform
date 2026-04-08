<template>
  <a-modal
    :open="visible"
    title="手动点名"
    width="680px"
    :confirm-loading="submitting"
    ok-text="提交"
    cancel-text="取消"
    @ok="handleSubmit"
    @update:open="(val: boolean) => emit('update:visible', val)"
  >
    <div v-if="sessionLabel" class="ma-session-info">
      <span>课次：{{ sessionLabel }}</span>
    </div>

    <div class="ma-toolbar">
      <a-space>
        <a-button size="small" @click="setAllStatus('on_time')">全部出勤</a-button>
        <a-button size="small" @click="setAllStatus('absent')">全部缺勤</a-button>
      </a-space>
      <span class="ma-summary">
        出勤 {{ onTimeCount }} / 迟到 {{ lateCount }} / 缺勤 {{ absentCount }}
      </span>
    </div>

    <div class="ma-list">
      <div v-for="item in attendanceItems" :key="item.userId" class="ma-row">
        <div class="ma-student">
          <a-avatar :size="28" class="ma-avatar">{{ (item.nickname || item.name || '').slice(0, 1) }}</a-avatar>
          <span class="ma-name">{{ item.nickname || item.name }}</span>
        </div>
        <div class="ma-controls">
          <a-radio-group v-model:value="item.status" size="small">
            <a-radio-button value="on_time">出勤</a-radio-button>
            <a-radio-button value="late">迟到</a-radio-button>
            <a-radio-button value="absent">缺勤</a-radio-button>
          </a-radio-group>
          <a-input
            v-if="item.status === 'absent'"
            v-model:value="item.absenceReason"
            size="small"
            placeholder="缺勤原因（选填）"
            style="width: 140px; margin-left: 8px"
          />
        </div>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import type { StudentItem } from './types'

const props = defineProps<{
  visible: boolean
  trainingId: number | string
  sessionId: string
  sessionLabel: string
  students: StudentItem[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'submitted'): void
}>()

interface AttendanceItem {
  userId: number
  name: string
  nickname: string
  status: 'on_time' | 'late' | 'absent'
  absenceReason: string
}

const attendanceItems = ref<AttendanceItem[]>([])
const submitting = ref(false)

const onTimeCount = computed(() => attendanceItems.value.filter(i => i.status === 'on_time').length)
const lateCount = computed(() => attendanceItems.value.filter(i => i.status === 'late').length)
const absentCount = computed(() => attendanceItems.value.filter(i => i.status === 'absent').length)

watch(
  () => props.visible,
  (val) => {
    if (val) {
      attendanceItems.value = props.students.map(s => ({
        userId: s.user_id,
        name: s.user_name || '',
        nickname: s.user_nickname || '',
        status: 'on_time',
        absenceReason: '',
      }))
    }
  },
)

function setAllStatus(status: 'on_time' | 'absent') {
  attendanceItems.value.forEach(item => {
    item.status = status
    if (status !== 'absent') item.absenceReason = ''
  })
}

async function handleSubmit() {
  if (!attendanceItems.value.length) return
  submitting.value = true
  try {
    const axiosInstance = (await import('@/api/custom-instance')).default
    await axiosInstance.post(`/trainings/${props.trainingId}/checkin/batch-manual`, {
      session_key: props.sessionId,
      items: attendanceItems.value.map(item => ({
        user_id: item.userId,
        status: item.status,
        absence_reason: item.status === 'absent' ? (item.absenceReason || undefined) : undefined,
      })),
    })
    message.success('点名记录已保存')
    emit('update:visible', false)
    emit('submitted')
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '提交失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.ma-session-info {
  padding: 8px 12px;
  background: var(--v2-bg);
  border-radius: var(--v2-radius-sm);
  font-size: 13px;
  color: var(--v2-text-secondary);
  margin-bottom: 12px;
}

.ma-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.ma-summary {
  font-size: 13px;
  color: var(--v2-text-muted);
}

.ma-list {
  max-height: 400px;
  overflow-y: auto;
}

.ma-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 4px;
  border-bottom: 1px solid var(--v2-border-light);
}

.ma-row:last-child { border-bottom: none; }

.ma-student {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}

.ma-avatar {
  background: var(--v2-primary);
  color: #fff;
  font-size: 12px;
  flex-shrink: 0;
}

.ma-name {
  font-size: 14px;
  color: var(--v2-text-primary);
}

.ma-controls {
  display: flex;
  align-items: center;
}
</style>
