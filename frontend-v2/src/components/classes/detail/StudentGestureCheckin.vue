<template>
  <a-modal
    :open="open"
    :footer="null"
    :width="420"
    @cancel="$emit('update:open', false)"
    class="gesture-checkin-modal"
  >
    <div class="gesture-checkin-content">
      <div class="gesture-header">
        <h3>{{ isCheckout ? '手势签退' : '手势签到' }}</h3>
        <div class="session-info">
          <div>{{ trainingName }}</div>
          <div class="session-detail">{{ session?.course_name }} · {{ session?.date }} {{ session?.time_range }}</div>
        </div>
      </div>

      <div class="gesture-area">
        <GesturePattern v-model="drawnPattern" theme="light" :size="260" @complete="onGestureComplete" />
        <a-button type="text" size="small" class="gesture-clear-btn" @click="drawnPattern = []">
          <ReloadOutlined /> 清空重绘
        </a-button>
      </div>

      <div class="gesture-result" v-if="errorMsg">
        <a-alert :message="errorMsg" type="error" show-icon />
      </div>

      <a-button
        type="primary"
        block
        size="large"
        :loading="submitting"
        :disabled="drawnPattern.length < 3"
        @click="handleSubmit"
      >
        {{ isCheckout ? '确认签退' : '确认签到' }}
      </a-button>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import GesturePattern from './GesturePattern.vue'
import {
  checkinApiV1TrainingsTrainingIdCheckinPost,
  checkoutApiV1TrainingsTrainingIdCheckoutPost,
} from '@/api/generated/training-management/training-management'

interface Session {
  session_id: number | string
  course_name: string
  date: string
  time_range: string
}

const props = withDefaults(defineProps<{
  open: boolean
  trainingId: number | string
  trainingName: string
  session: Session | null
  gesturePattern?: number[]
  isCheckout?: boolean
}>(), {
  gesturePattern: () => [],
  isCheckout: false,
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  success: []
}>()

const drawnPattern = ref<number[]>([])
const errorMsg = ref('')
const submitting = ref(false)

watch(
  () => props.open,
  (val) => {
    if (val && props.session) {
      drawnPattern.value = []
      errorMsg.value = ''
    }
  },
)

function onGestureComplete() {
  errorMsg.value = ''
}

async function handleSubmit() {
  if (!props.session) return

  const expected = props.gesturePattern
  const patternMatch =
    drawnPattern.value.length === expected.length &&
    drawnPattern.value.every((v, i) => v === expected[i])

  if (!patternMatch) {
    errorMsg.value = '手势不正确，请重试'
    drawnPattern.value = []
    return
  }

  submitting.value = true
  try {
    if (props.isCheckout) {
      await checkoutApiV1TrainingsTrainingIdCheckoutPost(Number(props.trainingId), {
        session_key: String(props.session.session_id),
      })
    } else {
      await checkinApiV1TrainingsTrainingIdCheckinPost(Number(props.trainingId), {
        session_key: String(props.session.session_id),
      })
    }
    message.success(props.isCheckout ? '签退成功' : '签到成功')
    emit('update:open', false)
    emit('success')
  } catch {
    errorMsg.value = props.isCheckout ? '签退失败，请重试' : '签到失败，请重试'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.gesture-checkin-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
}

.gesture-header {
  text-align: center;
  margin-bottom: 16px;
}

.gesture-header h3 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
}

.session-info {
  color: rgba(0, 0, 0, 0.65);
  font-size: 14px;
}

.session-detail {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-top: 4px;
}

.gesture-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  width: 100%;
}

.gesture-clear-btn {
  color: #999;
  font-size: 13px;
  margin-top: 8px;
}
.gesture-clear-btn:hover {
  color: #1677ff;
}

.gesture-result {
  width: 100%;
  margin-bottom: 12px;
}
</style>
