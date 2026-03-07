<template>
  <div class="enroll-page">
    <!-- 培训班信息头部 -->
    <div class="training-header" v-if="training">
      <div class="header-badge">
        <a-tag color="green">报名中</a-tag>
      </div>
      <h2 class="training-title">{{ training.name }}</h2>
      <div class="training-meta-row">
        <span><CalendarOutlined /> {{ training.startDate }} 至 {{ training.endDate }}</span>
        <span><EnvironmentOutlined /> {{ training.location }}</span>
        <span><UserOutlined /> 主讲教官：{{ training.instructorName }}</span>
      </div>
      <!-- 名额进度 -->
      <div class="quota-section">
        <div class="quota-label">
          <span>名额情况</span>
          <span class="quota-nums"><b>{{ training.enrolled }}</b> / {{ training.capacity }} 人已录取</span>
        </div>
        <a-progress :percent="Math.round(training.enrolled / training.capacity * 100)" :show-info="false" stroke-color="#003087" />
        <div class="quota-tags">
          <a-tag color="green">已录取 {{ training.enrolled }}</a-tag>
          <a-tag color="default">剩余名额 {{ Math.max(0, training.capacity - training.enrolled) }}</a-tag>
        </div>
      </div>
    </div>

    <!-- 已提交或已在班级状态 -->
    <div v-if="submitted || isAlreadyInClass || hasEnrolled" class="submit-success">
      <a-result
        :status="isAlreadyInClass ? 'success' : 'info'"
        :title="isAlreadyInClass ? '您已是该班级成员' : '报名申请已提交或正在审核中！'"
        :sub-title="isAlreadyInClass ? '您已无需重复报名，快去看看课程日程吧！' : '您的报名申请正在处理中，审核结果将通过系统消息通知您，并且可以在我的培训中查看，请耐心等待。'"
      >
        <template #extra>
          <a-button type="primary" @click="$router.push('/training')">返回培训列表</a-button>
          <a-button @click="$router.push('/')">回到首页</a-button>
        </template>
      </a-result>
    </div>

    <!-- 报名表单 -->
    <div v-else class="enroll-form-card">
      <h3 class="form-title">填写报名信息</h3>
      <a-form :model="formData" layout="vertical" :label-col="{ span: 24 }">
        <a-row :gutter="16">
          <a-col :xs="24" :sm="12">
            <a-form-item label="姓名">
              <a-input v-model:value="formData.name" disabled />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="警号">
              <a-input v-model:value="formData.policeId" disabled />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="所属单位">
              <a-input v-model:value="formData.unit" disabled />
            </a-form-item>
          </a-col>
          <a-col :xs="24" :sm="12">
            <a-form-item label="联系电话">
              <a-input v-model:value="formData.phone" placeholder="请输入联系电话" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="参训目的（选填）">
              <a-textarea v-model:value="formData.reason" :rows="3" placeholder="请简要说明参训原因或目标..." :maxlength="200" show-count />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="是否有住宿需求">
              <a-radio-group v-model:value="formData.needAccom">
                <a-radio value="yes">需要住宿</a-radio>
                <a-radio value="no">不需要（自行解决）</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-col>
        </a-row>

        <div class="form-agreement">
          <a-checkbox v-model:checked="agreed">
            我已阅读并同意<a>《培训班报名须知》</a>，确认参训期间遵守培训纪律
          </a-checkbox>
        </div>

        <div class="form-actions">
          <a-button @click="$router.back()">返回</a-button>
          <a-button type="primary" :loading="submitting" :disabled="!agreed || isFull" @click="handleSubmit">
            {{ isFull ? '名额已满' : '提交报名申请' }}
          </a-button>
        </div>
      </a-form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { CalendarOutlined, EnvironmentOutlined, UserOutlined } from '@ant-design/icons-vue'
import { getTraining, enroll as apiEnroll } from '@/api/training'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const trainingId = route.params.id
const training = ref(null)

const submitted = ref(false)
const submitting = ref(false)
const agreed = ref(false)

const u = authStore.currentUser || {}

onMounted(async () => {
  try {
    training.value = await getTraining(trainingId)
    if (isAlreadyInClass.value || hasEnrolled.value) {
      submitted.value = true
    }
  } catch { /* ignore */ }
})

const isAlreadyInClass = computed(() => training.value?.students?.includes(u.id))
const hasEnrolled = computed(() => false) // Will be determined by backend
const isFull = computed(() => training.value?.enrolled >= training.value?.capacity)
const formData = ref({
  name: u.name || '',
  policeId: u.username || '',
  unit: u.unit || '',
  phone: u.phone || '',
  reason: '',
  needAccom: 'no',
})

async function handleSubmit() {
  if (!agreed.value) { message.warning('请先同意报名须知'); return }
  if (isFull.value) { message.error('该班级名额已满，无法申请'); return }
  
  submitting.value = true
  try {
    await apiEnroll(trainingId, {
      note: formData.value.reason,
      phone: formData.value.phone,
      needAccom: formData.value.needAccom,
    })
    submitted.value = true
    message.success('报名申请已提交，等待审核')
  } catch (e) {
    message.error(e.message || '报名失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.enroll-page { max-width: 760px; margin: 0 auto; }
.training-header {
  background: white;
  border-radius: 10px;
  padding: 24px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.header-badge { margin-bottom: 10px; }
.training-title { font-size: 18px; font-weight: 700; color: #001234; margin-bottom: 12px; }
.training-meta-row {
  display: flex; flex-wrap: wrap; gap: 16px;
  font-size: 13px; color: #595959; margin-bottom: 16px;
}
.quota-section { margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f0f0; }
.quota-label { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 13px; color: #595959; }
.quota-nums b { color: #003087; font-size: 16px; }
.quota-tags { display: flex; gap: 8px; margin-top: 8px; }
.enroll-form-card {
  background: white; border-radius: 10px; padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.form-title { font-size: 16px; font-weight: 700; margin-bottom: 20px; color: #001234; }
.form-agreement { margin-bottom: 20px; }
.form-actions { display: flex; justify-content: flex-end; gap: 12px; padding-top: 16px; border-top: 1px solid #f0f0f0; }
.submit-success { background: white; border-radius: 10px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
</style>
