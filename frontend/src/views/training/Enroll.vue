<template>
  <div class="enroll-page">
    <div v-if="training" class="training-header">
      <a-tag :color="training.publishStatus === 'published' ? 'blue' : 'default'">
        {{ training.publishStatus === 'published' ? '报名开放中' : '未发布' }}
      </a-tag>
      <h2>{{ training.name }}</h2>
      <div class="meta-row">
        <span><CalendarOutlined /> {{ training.startDate }} 至 {{ training.endDate }}</span>
        <span><EnvironmentOutlined /> {{ training.location }}</span>
        <span><UserOutlined /> {{ training.instructorName || '未指定' }}</span>
      </div>
      <div class="rule-panel">
        <div>报名窗口：{{ formatWindow(training.enrollmentStartAt, training.enrollmentEndAt) }}</div>
        <div>报名方式：{{ training.enrollmentRequiresApproval === false ? '直接通过' : '申请审核' }}</div>
        <div>准入考试：{{ training.admissionExamTitle || '无' }}</div>
        <div>名单状态：{{ training.isLocked ? '已锁定' : '未锁定' }}</div>
      </div>
    </div>

    <a-result
      v-if="submitted"
      :status="submitStatus"
      :title="submitTitle"
      :sub-title="submitSubtitle"
    >
      <template #extra>
        <a-button type="primary" @click="$router.push('/training')">返回培训列表</a-button>
      </template>
    </a-result>

    <div v-else class="enroll-form-card">
      <a-alert v-if="training?.admissionExamTitle" type="info" show-icon style="margin-bottom:16px" :message="`该培训班要求先通过：${training.admissionExamTitle}`" />
      <a-form :model="formData" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="姓名">
              <a-input v-model:value="formData.name" disabled />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="警号">
              <a-input v-model:value="formData.policeId" disabled />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="所属单位">
              <a-input v-model:value="formData.unit" disabled />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="联系电话" required>
              <a-input v-model:value="formData.phone" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="参训说明">
              <a-textarea v-model:value="formData.note" :rows="3" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="住宿需求">
              <a-radio-group v-model:value="formData.needAccommodation">
                <a-radio :value="true">需要住宿</a-radio>
                <a-radio :value="false">不需要</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-col>
        </a-row>

        <div class="actions">
          <a-button @click="$router.back()">返回</a-button>
          <a-button type="primary" :loading="submitting" :disabled="!canSubmit" @click="handleSubmit">
            {{ disabledReason || (training?.enrollmentRequiresApproval === false ? '提交并加入培训班' : '提交报名申请') }}
          </a-button>
        </div>
      </a-form>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { CalendarOutlined, EnvironmentOutlined, UserOutlined } from '@ant-design/icons-vue'
import { enroll, getEnrollments, getTraining } from '@/api/training'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const trainingId = route.params.id

const training = ref(null)
const submitted = ref(false)
const submitting = ref(false)
const submitStatus = ref('info')
const submitTitle = ref('')
const submitSubtitle = ref('')

const formData = ref({
  name: authStore.currentUser?.name || '',
  policeId: authStore.currentUser?.username || '',
  unit: authStore.currentUser?.unit || '',
  phone: authStore.currentUser?.phone || '',
  note: '',
  needAccommodation: false,
})

const canSubmit = computed(() => !disabledReason.value)
const disabledReason = computed(() => {
  if (!training.value) return '加载中'
  if (training.value.publishStatus !== 'published') return '未发布'
  if (training.value.isLocked) return '名单已锁定'
  return ''
})

function formatWindow(start, end) {
  if (!start && !end) return '未设置'
  return `${start ? String(start).replace('T', ' ').slice(0, 16) : '即时'} ~ ${end ? String(end).replace('T', ' ').slice(0, 16) : '长期'}`
}

function applyEnrollmentStatus(current) {
  submitted.value = true

  if (current.status === 'approved') {
    submitStatus.value = 'success'
    submitTitle.value = '您已被录取到该培训班'
    submitSubtitle.value = '可直接进入培训班完成签到、签退和评课。'
    return
  }

  if (current.status === 'rejected') {
    submitStatus.value = 'warning'
    submitTitle.value = '报名申请未通过'
    submitSubtitle.value = current.note || '当前报名未通过，如需处理请联系管理员。'
    return
  }

  submitStatus.value = 'info'
  submitTitle.value = '报名申请已提交'
  submitSubtitle.value = '审核结果请在报名管理或培训列表中查看。'
}

async function loadData() {
  try {
    const [trainingDetail, enrollmentResult] = await Promise.all([
      getTraining(trainingId),
      getEnrollments(trainingId, { size: -1 }),
    ])
    training.value = trainingDetail
    const rows = enrollmentResult.items || []
    const current = rows.find(item => String(item.userId) === String(authStore.currentUser?.id))
    if (current) {
      applyEnrollmentStatus(current)
    }
  } catch (error) {
    message.error(error.message || '加载报名信息失败')
  }
}

async function handleSubmit() {
  if (!formData.value.phone) {
    message.warning('请填写联系电话')
    return
  }
  submitting.value = true
  try {
    const result = await enroll(trainingId, {
      note: formData.value.note || undefined,
      phone: formData.value.phone,
      needAccommodation: formData.value.needAccommodation,
    })
    applyEnrollmentStatus(result)
  } catch (error) {
    message.error(error.message || '报名失败')
  } finally {
    submitting.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.enroll-page { max-width: 780px; margin: 0 auto; }
.training-header { background: #fff; border-radius: 10px; padding: 24px; margin-bottom: 16px; box-shadow: 0 4px 18px rgba(0, 32, 96, 0.06); }
.training-header h2 { margin: 12px 0; color: #001234; }
.meta-row { display: flex; flex-wrap: wrap; gap: 16px; color: #666; font-size: 13px; }
.rule-panel { margin-top: 16px; padding: 14px 16px; background: #f7f9fc; border-radius: 8px; color: #555; display: flex; flex-direction: column; gap: 6px; }
.enroll-form-card { background: #fff; border-radius: 10px; padding: 24px; box-shadow: 0 4px 18px rgba(0, 32, 96, 0.06); }
.actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 8px; }
</style>
