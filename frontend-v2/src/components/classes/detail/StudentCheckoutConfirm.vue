<template>
  <a-modal
    :open="visible"
    title="确认签退"
    :ok-text="'确认签退'"
    :confirm-loading="loading"
    @ok="handleCheckout"
    @update:open="(val: boolean) => emit('update:visible', val)"
    centered
    width="360px"
  >
    <div class="student-checkin-confirm">
      <CheckCircleOutlined class="student-checkin-icon" />
      <p>确认为当前课次进行签退？</p>
      <p class="student-checkin-session-info" v-if="session">
        {{ session.course_name }} · {{ session.time_range?.replace('~', ' - ') }}
      </p>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { CheckCircleOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { checkoutApiV1TrainingsTrainingIdCheckoutPost } from '@/api/generated/training-management/training-management'
import type { CurrentSession } from './types'

const props = defineProps<{
  visible: boolean
  trainingId: number | string
  session: CurrentSession | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'refresh'): void
}>()

const loading = ref(false)

async function handleCheckout() {
  const sess = props.session
  if (!sess) return
  loading.value = true
  try {
    await checkoutApiV1TrainingsTrainingIdCheckoutPost(
      Number(props.trainingId),
      { session_key: sess.session_id },
    )
    message.success('签退成功')
    emit('update:visible', false)
    emit('refresh')
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '签退失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.student-checkin-confirm {
  text-align: center;
  padding: 16px 0;
}

.student-checkin-icon {
  font-size: 48px;
  color: var(--v2-primary);
  margin-bottom: 16px;
}

.student-checkin-confirm p {
  font-size: 15px;
  color: var(--v2-text-primary);
  margin: 0 0 8px;
}

.student-checkin-session-info {
  font-size: 13px;
  color: var(--v2-text-muted);
}

@media (max-width: 768px) {
  .student-checkin-confirm .ant-btn {
    min-height: 44px;
  }
}
</style>
