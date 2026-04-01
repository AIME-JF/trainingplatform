<template>
  <div class="attendance-page">
    <div class="attendance-card">
      <!-- Loading -->
      <template v-if="loading">
        <a-spin size="large" />
        <p class="attendance-hint">正在加载出勤信息...</p>
      </template>

      <!-- Error -->
      <template v-else-if="errorMsg">
        <CloseCircleOutlined class="attendance-icon attendance-icon--error" />
        <p class="attendance-title">出勤失败</p>
        <p class="attendance-hint">{{ errorMsg }}</p>
        <a-button type="primary" @click="$router.push('/')">返回首页</a-button>
      </template>

      <!-- Success -->
      <template v-else-if="success">
        <CheckCircleOutlined class="attendance-icon attendance-icon--success" />
        <p class="attendance-title">{{ isCheckout ? '签退成功' : '签到成功' }}</p>
        <div class="attendance-info">
          <p v-if="qrPayload?.training_name">{{ qrPayload.training_name }}</p>
          <p v-if="qrPayload?.session_label" class="attendance-hint">{{ qrPayload.session_label }}</p>
        </div>
        <a-button type="primary" @click="$router.push('/')">返回首页</a-button>
      </template>

      <!-- Confirm -->
      <template v-else-if="qrPayload">
        <div class="attendance-icon-wrapper" :class="isCheckout ? 'checkout' : 'checkin'">
          <LoginOutlined v-if="!isCheckout" class="attendance-icon attendance-icon--confirm" />
          <LogoutOutlined v-else class="attendance-icon attendance-icon--confirm" />
        </div>
        <p class="attendance-title">{{ isCheckout ? '确认签退' : '确认签到' }}</p>
        <div class="attendance-info">
          <p class="attendance-training">{{ qrPayload.training_name }}</p>
          <p v-if="qrPayload.session_label" class="attendance-hint">{{ qrPayload.session_label }}</p>
          <p v-if="qrPayload.date" class="attendance-hint">{{ qrPayload.date }}</p>
        </div>
        <div v-if="currentUser" class="attendance-user">
          <a-avatar :size="36" class="attendance-user-avatar">{{ (currentUser.nickname || currentUser.username || '').slice(0, 1) }}</a-avatar>
          <span>{{ currentUser.nickname || currentUser.username }}</span>
        </div>
        <a-button
          type="primary"
          size="large"
          block
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ isCheckout ? '确认签退' : '确认签到' }}
        </a-button>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoginOutlined,
  LogoutOutlined,
} from '@ant-design/icons-vue'
import {
  getAttendanceQrPayloadApiV1TrainingsAttendanceQrTokenGet,
  attendanceByQrApiV1TrainingsAttendanceQrTokenPost,
  getCheckinQrPayloadApiV1TrainingsCheckinQrTokenGet,
} from '@/api/generated/training-management/training-management'
import type { TrainingCheckinQrResponse } from '@/api/generated/model'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const errorMsg = ref('')
const success = ref(false)
const submitting = ref(false)
const qrPayload = ref<TrainingCheckinQrResponse | null>(null)

const isCheckout = computed(() => qrPayload.value?.action === 'checkout')

const currentUser = ref<{ username?: string; nickname?: string } | null>(null)

onMounted(async () => {
  // Read user info from localStorage
  try {
    const raw = localStorage.getItem('userInfo')
    if (raw) {
      const info = JSON.parse(raw)
      currentUser.value = { username: info.username, nickname: info.nickname || info.name }
    }
  } catch { /* ignore */ }

  const token = route.params.token as string
  if (!token) {
    errorMsg.value = '无效的二维码链接'
    loading.value = false
    return
  }

  // Check auth
  const authToken = localStorage.getItem('token')
  if (!authToken) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }

  try {
    // Try unified attendance endpoint first, fallback to legacy checkin endpoint
    let data: TrainingCheckinQrResponse
    try {
      data = await getAttendanceQrPayloadApiV1TrainingsAttendanceQrTokenGet(token)
    } catch {
      data = await getCheckinQrPayloadApiV1TrainingsCheckinQrTokenGet(token)
      if (!data.action) data.action = 'checkin'
    }
    qrPayload.value = data
  } catch (err: unknown) {
    errorMsg.value = err instanceof Error ? err.message : '二维码不存在或已失效'
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  const payload = qrPayload.value
  if (!payload) return
  submitting.value = true
  try {
    await attendanceByQrApiV1TrainingsAttendanceQrTokenPost(payload.token)
    success.value = true
  } catch (err: unknown) {
    errorMsg.value = err instanceof Error ? err.message : '操作失败'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.attendance-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--v2-bg, #F5F6FA);
}

.attendance-card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 16px;
  padding: 40px 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  text-align: center;
}

.attendance-icon {
  font-size: 56px;
}

.attendance-icon--success {
  color: var(--v2-success, #34C759);
}

.attendance-icon--error {
  color: var(--v2-danger, #FF3B30);
}

.attendance-icon--confirm {
  font-size: 32px;
  color: #fff;
}

.attendance-icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.attendance-icon-wrapper.checkin {
  background: var(--v2-success, #34C759);
}

.attendance-icon-wrapper.checkout {
  background: var(--v2-primary, #4B6EF5);
}

.attendance-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--v2-text-primary, #1D1D1F);
  margin: 0;
}

.attendance-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.attendance-training {
  font-size: 15px;
  color: var(--v2-text-primary, #1D1D1F);
  font-weight: 500;
  margin: 0;
}

.attendance-hint {
  font-size: 13px;
  color: var(--v2-text-muted, #AEAEB2);
  margin: 0;
}

.attendance-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: var(--v2-bg, #F5F6FA);
  border-radius: 8px;
  font-size: 14px;
  color: var(--v2-text-primary, #1D1D1F);
  width: 100%;
  justify-content: center;
}

.attendance-user-avatar {
  background: var(--v2-primary, #4B6EF5);
  color: #fff;
  font-size: 14px;
}

@media (max-width: 768px) {
  .attendance-page {
    padding: 16px;
    align-items: flex-start;
    padding-top: 60px;
  }

  .attendance-card {
    padding: 32px 24px;
  }
}
</style>
