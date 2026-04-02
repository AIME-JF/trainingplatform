<template>
  <a-modal
    :open="visible"
    title="签退管理"
    :footer="null"
    width="640px"
    :class="{ 'checkin-mgr-modal-mobile': isMobile }"
    :style="isMobile ? { top: 0, maxWidth: '100vw', margin: 0, paddingBottom: 0 } : {}"
    :bodyStyle="isMobile ? { height: 'calc(100vh - 55px)', overflow: 'auto' } : {}"
    @update:open="(val: boolean) => emit('update:visible', val)"
  >
    <!-- 上部：签退配置区 -->
    <div class="checkin-config">
      <div class="config-row">
        <span class="config-label">签退途径</span>
        <a-radio-group
          :value="checkoutMode"
          :disabled="isCheckoutOngoing"
          @change="(e: any) => { checkoutMode = e.target.value }"
        >
          <a-radio value="direct">直接签退</a-radio>
          <a-radio value="gesture">手势签退</a-radio>
        </a-radio-group>
      </div>
      <!-- 手势签退设置 -->
      <div v-if="checkoutMode === 'gesture'" class="gesture-setting">
        <div class="gesture-title">设置签退手势</div>
        <div class="gesture-card">
          <GesturePattern theme="light" v-model="gesturePattern" />
          <div class="gesture-clear-row">
            <a-button size="small" type="text" class="gesture-clear-btn" @click="gesturePattern = []">
              <ReloadOutlined /> 清空重绘
            </a-button>
          </div>
        </div>
        <div class="gesture-hint">学生签退时需要绘制相同的手势</div>
      </div>
      <div class="config-row">
        <span class="config-label">签退限时</span>
        <a-select
          :value="checkoutDurationMin"
          style="width: 120px"
          :disabled="isCheckoutOngoing"
          @change="(val: number) => { checkoutDurationMin = val }"
        >
          <a-select-option :value="5">5 分钟</a-select-option>
          <a-select-option :value="10">10 分钟</a-select-option>
          <a-select-option :value="15">15 分钟</a-select-option>
          <a-select-option :value="30">30 分钟</a-select-option>
        </a-select>
      </div>
      <div v-if="checkoutMode === 'gesture' && gesturePattern.length > 0 && isCheckoutOngoing" class="gesture-active-hint">
        <span>手势签退进行中，学生需绘制相同手势完成签退</span>
      </div>
    </div>

    <!-- 中部：签退统计 -->
    <div class="checkin-stats">
      <div class="stat-progress">
        <span>已签退 {{ checkedOutList.length }} / {{ totalStudents }} 人</span>
        <a-progress :percent="checkoutPercent" size="small" :show-info="false" />
      </div>
    </div>

    <!-- 下部：签退名单 -->
    <a-tabs v-model:activeKey="checkoutTab" size="small" style="margin-top: 8px">
      <a-tab-pane key="checked" :tab="`已签退 (${checkedOutList.length})`">
        <a-empty v-if="!checkedOutList.length" description="暂无签退记录" />
        <div v-else class="checkin-list">
          <div v-for="r in checkedOutList" :key="r.user_id" class="checkin-row">
            <a-avatar :size="28" class="checkin-avatar">{{ (r.user_nickname || r.user_name || '').slice(0, 1) }}</a-avatar>
            <div class="checkin-info">
              <span class="checkin-name">{{ r.user_nickname || r.user_name }}</span>
              <span class="checkin-time">{{ r.checkout_time || '' }}</span>
            </div>
          </div>
        </div>
      </a-tab-pane>
      <a-tab-pane key="unchecked" :tab="`未签退 (${notCheckedOutList.length})`">
        <a-empty v-if="!notCheckedOutList.length" description="全部已签退" />
        <div v-else class="checkin-list">
          <div v-for="s in notCheckedOutList" :key="s.user_id" class="checkin-row">
            <a-avatar :size="28" class="checkin-avatar absent">{{ (s.user_nickname || s.user_name || '').slice(0, 1) }}</a-avatar>
            <div class="checkin-info">
              <span class="checkin-name">{{ s.user_nickname || s.user_name }}</span>
              <span class="checkin-absent-label">未签退</span>
            </div>
            <a-button
              v-if="canManageCheckin"
              size="small"
              type="primary"
              @click="toggleCheckout(s.user_id)"
              :loading="checkoutToggleLoading === s.user_id"
            >
              标记已签退
            </a-button>
          </div>
        </div>
      </a-tab-pane>
    </a-tabs>

    <!-- 底部按钮区 -->
    <div class="checkin-mgr-footer">
      <a-button
        v-if="session?.action_permissions?.can_start_checkout && !isCheckoutOngoing"
        type="primary"
        :loading="sessionActionLoading"
        @click="doStartCheckout"
      >
        开始签退
      </a-button>
      <a-button
        v-if="session?.action_permissions?.can_end_checkout"
        danger
        :loading="sessionActionLoading"
        @click="doEndCheckout"
      >
        结束签退
      </a-button>
      <a-button v-if="session?.status === 'completed'" @click="emit('update:visible', false)">
        关闭
      </a-button>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import GesturePattern from './GesturePattern.vue'
import { useAuthStore } from '@/stores/auth'
import {
  getCheckinRecordsApiV1TrainingsTrainingIdCheckinRecordsGet,
  startSessionCheckoutApiV1TrainingsTrainingIdSessionsSessionKeyCheckoutStartPost,
  endSessionCheckoutApiV1TrainingsTrainingIdSessionsSessionKeyCheckoutEndPost,
  checkoutApiV1TrainingsTrainingIdCheckoutPost,
} from '@/api/generated/training-management/training-management'
import type { CheckinResponse, TrainingCheckinQrResponse, TrainingResponse } from '@/api/generated/model'
import type { CurrentSession, StudentItem } from './types'
import { useAttendanceManager } from './useAttendanceManager'
import { getAttendanceQr } from '@/services/attendance'

const props = defineProps<{
  visible: boolean
  trainingId: number | string
  session: CurrentSession | null
  students: StudentItem[]
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'detail-updated', val: TrainingResponse): void
  (e: 'gesture-pattern-set', pattern: number[]): void
}>()

const authStore = useAuthStore()

const sessionActionLoading = ref(false)
const checkoutTab = ref('checked')
const checkoutRecords = ref<CheckinResponse[]>([])
const checkoutToggleLoading = ref<number | null>(null)
const gesturePattern = ref<number[]>([])
const isMobile = ref(window.innerWidth <= 768)

function handleResize() {
  isMobile.value = window.innerWidth <= 768
}
window.addEventListener('resize', handleResize)
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const {
  mode: checkoutMode,
  duration: checkoutDurationMin,
  qrUrl: checkoutQrUrl,
  syncFromSession,
} = useAttendanceManager({
  action: 'checkout',
  visible: computed(() => props.visible),
  session: computed(() => props.session),
  fetchQrPayload: (sessionId: string, action: 'checkin' | 'checkout'): Promise<TrainingCheckinQrResponse> =>
    getAttendanceQr(
      Number(props.trainingId),
      { session_key: sessionId, action },
    ),
})

const isCheckoutOngoing = computed(() => props.session?.status === 'checkout_open')

const canManageCheckin = computed(() => {
  return authStore.isInstructor && props.session?.action_permissions != null
})

const checkedOutList = computed(() =>
  checkoutRecords.value.filter((r) => r.checkout_status === 'completed'),
)

const notCheckedOutList = computed(() => {
  const outIds = new Set(checkedOutList.value.map((r) => r.user_id))
  return props.students
    .filter((s) => !outIds.has(s.user_id))
    .map((s) => ({ user_id: s.user_id, user_name: s.user_name, user_nickname: s.user_nickname, status: '', time: '' }))
})

const totalStudents = computed(() => props.students.length || 0)

const checkoutPercent = computed(() => {
  if (!totalStudents.value) return 0
  return Math.round((checkedOutList.value.length / totalStudents.value) * 100)
})

watch(
  [() => props.visible, () => props.session?.session_id],
  async ([visible, sessionId]) => {
    if (!visible || !sessionId) {
      checkoutRecords.value = []
      return
    }
    checkoutTab.value = 'checked'
    await fetchCheckoutRecords(sessionId)
  },
  { immediate: true },
)

async function fetchCheckoutRecords(sessionId = props.session?.session_id) {
  if (!sessionId) return
  try {
    const data = await getCheckinRecordsApiV1TrainingsTrainingIdCheckinRecordsGet(
      Number(props.trainingId),
      { session_key: sessionId },
    )
    checkoutRecords.value = data || []
  } catch {
    checkoutRecords.value = []
  }
}

async function doStartCheckout() {
  const sess = props.session
  if (!sess) return
  if (checkoutMode.value === 'gesture' && gesturePattern.value.length < 3) {
    message.warning('请至少连接3个点来设置签退手势')
    return
  }
  sessionActionLoading.value = true
  try {
    const apiMode = checkoutMode.value === 'gesture' ? 'direct' : checkoutMode.value
    const params: Record<string, any> = { checkout_mode: apiMode, checkout_duration_minutes: checkoutDurationMin.value }
    if (checkoutMode.value === 'gesture') {
      params.checkout_gesture_pattern = JSON.stringify(gesturePattern.value)
    }
    const detail = await startSessionCheckoutApiV1TrainingsTrainingIdSessionsSessionKeyCheckoutStartPost(
      Number(props.trainingId),
      sess.session_id,
      params,
    )
    if (checkoutMode.value === 'gesture') {
      emit('gesture-pattern-set', gesturePattern.value)
    }
    message.success('签退已开始')
    if (detail) emit('detail-updated', detail)
    await syncFromSession((detail?.current_session as CurrentSession | null) ?? sess)
    await fetchCheckoutRecords(sess.session_id)
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    sessionActionLoading.value = false
  }
}

async function doEndCheckout() {
  const sess = props.session
  if (!sess) return
  sessionActionLoading.value = true
  try {
    const detail = await endSessionCheckoutApiV1TrainingsTrainingIdSessionsSessionKeyCheckoutEndPost(
      Number(props.trainingId),
      sess.session_id,
    )
    message.success('签退已结束')
    if (detail) emit('detail-updated', detail)
    await syncFromSession((detail?.current_session as CurrentSession | null) ?? null)
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    sessionActionLoading.value = false
  }
}

async function toggleCheckout(userId: number) {
  const sess = props.session
  if (!sess) return
  checkoutToggleLoading.value = userId
  try {
    await checkoutApiV1TrainingsTrainingIdCheckoutPost(
      Number(props.trainingId),
      { user_id: userId, session_key: sess.session_id },
    )
    await fetchCheckoutRecords(sess.session_id)
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    checkoutToggleLoading.value = null
  }
}
</script>

<style scoped>
.checkin-config {
  padding: 16px;
  background: var(--v2-bg);
  border-radius: var(--v2-radius-sm);
  margin-bottom: 16px;
}

.config-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.config-row:last-child { margin-bottom: 0; }

.gesture-setting {
  margin: 12px 0;
}

.gesture-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--v2-text-primary);
  margin-bottom: 10px;
}

.gesture-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.gesture-clear-row {
  margin-top: 12px;
  text-align: center;
}
.gesture-clear-btn {
  color: #999;
  font-size: 13px;
}
.gesture-clear-btn:hover {
  color: #1677ff;
}

.gesture-hint {
  font-size: 12px;
  color: var(--v2-text-muted);
  margin-top: 8px;
}

.gesture-active-hint {
  margin-top: 12px;
  padding: 10px 14px;
  background: var(--v2-bg);
  border-radius: var(--v2-radius-sm);
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.config-label {
  font-size: 14px;
  color: var(--v2-text-secondary);
  min-width: 70px;
  flex-shrink: 0;
}

.qr-display {
  margin-top: 16px;
  padding: 24px;
  background: #fff;
  border: 1px solid var(--v2-border-light);
  border-radius: var(--v2-radius);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.qr-hint {
  font-size: 13px;
  color: var(--v2-text-muted);
}

.checkin-stats {
  padding: 12px 16px;
  background: var(--v2-bg);
  border-radius: var(--v2-radius-sm);
  margin-bottom: 12px;
}

.stat-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--v2-text-primary);
}

.stat-progress span { white-space: nowrap; flex-shrink: 0; }
.stat-progress .ant-progress { flex: 1; }

.checkin-list {
  display: flex;
  flex-direction: column;
}

.checkin-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 4px;
  border-bottom: 1px solid var(--v2-border-light);
}

.checkin-row:last-child { border-bottom: none; }

.checkin-avatar {
  background: var(--v2-success);
  color: #fff;
  font-size: 12px;
  flex-shrink: 0;
}

.checkin-avatar.absent {
  background: var(--v2-text-muted);
}

.checkin-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.checkin-name {
  font-size: 14px;
  color: var(--v2-text-primary);
}

.checkin-time {
  font-size: 12px;
  color: var(--v2-text-muted);
}

.checkin-absent-label {
  font-size: 12px;
  color: var(--v2-danger);
}

.checkin-mgr-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--v2-border-light);
}

@media (max-width: 768px) {
  .checkin-config {
    padding: 12px;
  }

  .config-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .checkin-list .checkin-row {
    padding: 8px 2px;
    gap: 8px;
  }

  .checkin-mgr-footer {
    flex-direction: column;
  }

  .checkin-mgr-footer .ant-btn {
    min-height: 44px;
    width: 100%;
  }
}
</style>
