import { onUnmounted, ref, watch, type Ref } from 'vue'
import dayjs from 'dayjs'
import type { TrainingCheckinQrResponse } from '@/api/generated/model'
import type { CurrentSession } from './types'

type AttendanceAction = 'checkin' | 'checkout'
type AttendanceMode = 'direct' | 'qr' | 'gesture'

interface UseAttendanceManagerOptions {
  action: AttendanceAction
  visible: Ref<boolean>
  session: Ref<CurrentSession | null>
  fetchQrPayload: (sessionId: string, action: AttendanceAction) => Promise<TrainingCheckinQrResponse>
}

function buildQrUrl(token: string, sessionId: string): string {
  return `${window.location.origin}/attendance/${token}/${sessionId}`
}

export function useAttendanceManager(options: UseAttendanceManagerOptions) {
  const mode = ref<AttendanceMode>('direct')
  const duration = ref(10)
  const qrUrl = ref('')
  const countdownText = ref('')
  const countdownTimer = ref<ReturnType<typeof setInterval> | null>(null)

  const modeKey = options.action === 'checkin' ? 'checkin_mode' : 'checkout_mode'
  const durationKey = options.action === 'checkin' ? 'checkin_duration_minutes' : 'checkout_duration_minutes'
  const deadlineKey = options.action === 'checkin' ? 'checkin_deadline' : 'checkout_deadline'
  const activeStatus = options.action === 'checkin' ? 'checkin_open' : 'checkout_open'

  function applySession(session: CurrentSession | null) {
    if (!session) {
      return
    }

    const nextMode = session[modeKey]
    if (nextMode === 'direct' || nextMode === 'qr') {
      mode.value = nextMode
    }

    const nextDuration = session[durationKey]
    if (typeof nextDuration === 'number' && nextDuration > 0) {
      duration.value = nextDuration
    }
  }

  async function refreshQrToken(session: CurrentSession | null = options.session.value) {
    if (!session || session.status !== activeStatus || mode.value !== 'qr') {
      qrUrl.value = ''
      return
    }

    try {
      const data = await options.fetchQrPayload(session.session_id, options.action)
      qrUrl.value = data.token ? buildQrUrl(data.token, session.session_id) : ''
    } catch {
      qrUrl.value = ''
    }
  }

  function stopCountdown() {
    if (countdownTimer.value) {
      clearInterval(countdownTimer.value)
      countdownTimer.value = null
    }
    countdownText.value = ''
  }

  function updateCountdown() {
    const deadline = options.session.value?.[deadlineKey]
    if (!deadline) {
      countdownText.value = ''
      return
    }

    const remaining = dayjs(deadline).diff(dayjs(), 'second')
    if (remaining <= 0) {
      countdownText.value = '已截止'
      stopCountdown()
      return
    }

    const mins = Math.floor(remaining / 60)
    const secs = remaining % 60
    countdownText.value = `${mins}:${String(secs).padStart(2, '0')}`
  }

  function startCountdown() {
    stopCountdown()
    updateCountdown()
    if (!options.session.value?.[deadlineKey]) {
      return
    }
    countdownTimer.value = setInterval(updateCountdown, 1000)
  }

  async function syncFromSession(session: CurrentSession | null = options.session.value) {
    applySession(session)

    if (!options.visible.value) {
      qrUrl.value = ''
      stopCountdown()
      return
    }

    if (session?.status === activeStatus && mode.value === 'qr') {
      await refreshQrToken(session)
    } else {
      qrUrl.value = ''
    }

    startCountdown()
  }

  watch(
    [options.visible, options.session],
    async ([visible, session]) => {
      if (!visible) {
        qrUrl.value = ''
        stopCountdown()
        return
      }

      await syncFromSession(session)
    },
    { immediate: true },
  )

  onUnmounted(() => {
    stopCountdown()
  })

  return {
    mode,
    duration,
    qrUrl,
    countdownText,
    refreshQrToken,
    syncFromSession,
    startCountdown,
    stopCountdown,
  }
}
