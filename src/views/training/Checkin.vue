<template>
  <div class="checkin-page">
    <template v-if="!authStore.isStudent">
      <div class="header-bar">
        <div>
          <a-button type="link" @click="router.push(`/training/${trainingId}`)" style="padding:0">返回培训班详情</a-button>
          <h2>{{ training.name }}</h2>
          <p>{{ currentSessionLabel }}</p>
        </div>
        <a-space>
          <a-select v-model:value="currentSessionKey" style="width:320px" @change="handleSessionChange">
            <a-select-option v-for="session in sessionOptions" :key="session.value" :value="session.value">
              {{ session.label }}
            </a-select-option>
          </a-select>
          <a-button type="primary" ghost :loading="qrLoading" @click="openQrModal">生成扫码签到</a-button>
        </a-space>
      </div>

      <a-row :gutter="20">
        <a-col :span="8">
          <a-card title="签到统计" :bordered="false">
            <div class="summary-grid">
              <div class="summary-item"><span>总人数</span><strong>{{ summary.totalStudents || 0 }}</strong></div>
              <div class="summary-item"><span>准时</span><strong>{{ summary.onTimeCount || 0 }}</strong></div>
              <div class="summary-item"><span>迟到</span><strong>{{ summary.lateCount || 0 }}</strong></div>
              <div class="summary-item"><span>缺勤</span><strong>{{ summary.absentCount || 0 }}</strong></div>
            </div>
            <a-divider />
            <a-input-search v-model:value="manualUserId" placeholder="输入学员用户ID手动签到" enter-button="签到" @search="manualCheckin" />
            <a-button style="margin-top:12px" block @click="loadAttendance">刷新统计</a-button>
          </a-card>
        </a-col>

        <a-col :span="16">
          <a-card title="签到记录" :bordered="false">
            <a-table :columns="columns" :data-source="records" row-key="id" :pagination="{ pageSize: 8 }">
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'status'">
                  <a-tag :color="statusColors[record.status]">{{ statusLabels[record.status] }}</a-tag>
                </template>
                <template v-if="column.key === 'checkoutStatus'">
                  <a-tag :color="record.checkoutStatus === 'completed' ? 'green' : 'default'">
                    {{ record.checkoutStatus === 'completed' ? '已签退' : '未签退' }}
                  </a-tag>
                </template>
              </template>
            </a-table>
          </a-card>
        </a-col>
      </a-row>
    </template>

    <template v-else>
      <div class="student-box">
        <h2>{{ training.name }}</h2>
        <p>{{ currentSessionLabel }}</p>
        <a-result
          v-if="checkedIn"
          status="success"
          title="签到成功"
          sub-title="可继续前往签退评课页面完成课后反馈。"
        >
          <template #extra>
            <a-button type="primary" @click="router.push({ name: 'Checkout', params: { id: trainingId, sessionKey: currentSessionKey } })">去签退评课</a-button>
          </template>
        </a-result>
        <a-card v-else :bordered="false">
          <a-button type="primary" block size="large" :loading="submitting" @click="submitCheckin">确认签到</a-button>
        </a-card>
      </div>
    </template>

    <a-modal
      v-model:open="qrModalOpen"
      title="扫码签到"
      :footer="null"
      width="420px"
    >
      <div class="qr-modal-body">
        <a-spin :spinning="qrLoading">
          <img v-if="qrImageUrl" :src="qrImageUrl" alt="签到二维码" class="qr-image" />
          <a-empty v-else description="二维码生成中" />
        </a-spin>
        <div class="qr-meta" v-if="qrInfo">
          <div>场次：{{ qrInfo.sessionLabel }}</div>
          <div>签到日期：{{ qrInfo.date || '当天' }}</div>
          <div>失效时间：{{ formatDateTime(qrInfo.expireAt) }}</div>
        </div>
        <a-input :value="qrAbsoluteUrl" readonly />
        <a-button type="primary" block style="margin-top:12px" @click="copyQrLink">复制签到链接</a-button>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import QRCode from 'qrcode'
import { checkin, getAttendanceSummary, getCheckinQR, getCheckinRecords, getTraining } from '@/api/training'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const trainingId = route.params.id
const currentSessionKey = ref(route.params.sessionKey || '')

const training = ref({ name: '', courses: [], currentSession: null })
const summary = ref({})
const records = ref([])
const checkedIn = ref(false)
const submitting = ref(false)
const manualUserId = ref('')
const qrModalOpen = ref(false)
const qrLoading = ref(false)
const qrInfo = ref(null)
const qrImageUrl = ref('')

const statusLabels = { onTime: '准时', late: '迟到', absent: '缺勤', on_time: '准时' }
const statusColors = { onTime: 'green', late: 'orange', absent: 'red', on_time: 'green' }

const columns = [
  { title: '姓名', dataIndex: 'userNickname', key: 'userNickname' },
  { title: '签到时间', dataIndex: 'time', key: 'time' },
  { title: '状态', key: 'status', width: 100 },
  { title: '签退', key: 'checkoutStatus', width: 100 },
  { title: '评课', dataIndex: 'evaluationScore', key: 'evaluationScore', width: 100, customRender: ({ text }) => text ? `${text}分` : '-' },
]

const sessionOptions = computed(() => {
  const options = []
  ;(training.value.courses || []).forEach((course) => {
    ;(course.schedules || []).forEach((schedule) => {
      options.push({
        value: schedule.sessionId,
        label: `${course.name} (${schedule.date} ${schedule.timeRange})`,
      })
    })
  })
  return options
})

const currentSessionLabel = computed(() => {
  return sessionOptions.value.find(item => item.value === currentSessionKey.value)?.label || '未选择课次'
})
const qrAbsoluteUrl = computed(() => {
  if (!qrInfo.value?.url) return ''
  try {
    return new URL(qrInfo.value.url, window.location.origin).toString()
  } catch {
    return qrInfo.value.url
  }
})

async function loadTraining() {
  try {
    training.value = await getTraining(trainingId)
    const optionKeys = sessionOptions.value.map((item) => item.value)
    if (!currentSessionKey.value || !optionKeys.includes(currentSessionKey.value)) {
      currentSessionKey.value = training.value.currentSession?.sessionId || sessionOptions.value[0]?.value || ''
    }
  } catch (error) {
    message.error(error.message || '加载培训班失败')
  }
}

async function loadAttendance() {
  if (!currentSessionKey.value) {
    summary.value = {}
    records.value = []
    return
  }
  try {
    const [summaryResult, recordResult] = await Promise.all([
      getAttendanceSummary(trainingId, { sessionKey: currentSessionKey.value }),
      getCheckinRecords(trainingId, { sessionKey: currentSessionKey.value }),
    ])
    summary.value = summaryResult
    records.value = recordResult || []
  } catch (error) {
    message.error(error.message || '加载签到数据失败')
  }
}

function handleSessionChange() {
  router.replace({ name: 'Checkin', params: { id: trainingId, sessionKey: currentSessionKey.value } })
  loadAttendance()
}

function formatDateTime(value) {
  if (!value) return '未设置'
  return String(value).replace('T', ' ').slice(0, 19)
}

async function openQrModal() {
  if (!currentSessionKey.value) {
    message.warning('当前没有可签到课次')
    return
  }
  qrLoading.value = true
  try {
    qrInfo.value = await getCheckinQR(trainingId, { sessionKey: currentSessionKey.value })
    qrImageUrl.value = await QRCode.toDataURL(qrAbsoluteUrl.value, {
      width: 320,
      margin: 1,
    })
    qrModalOpen.value = true
  } catch (error) {
    message.error(error.message || '生成二维码失败')
  } finally {
    qrLoading.value = false
  }
}

async function copyQrLink() {
  if (!qrAbsoluteUrl.value) return
  try {
    await navigator.clipboard.writeText(qrAbsoluteUrl.value)
    message.success('签到链接已复制')
  } catch {
    message.error('复制失败，请手动复制')
  }
}

async function manualCheckin(value) {
  if (!value || !currentSessionKey.value) return
  try {
    await checkin(trainingId, { sessionKey: currentSessionKey.value, userId: Number(value) || value })
    manualUserId.value = ''
    message.success('签到成功')
    loadAttendance()
  } catch (error) {
    message.error(error.message || '签到失败')
  }
}

async function submitCheckin() {
  if (!currentSessionKey.value) {
    message.warning('当前没有可签到课次')
    return
  }
  submitting.value = true
  try {
    await checkin(trainingId, { sessionKey: currentSessionKey.value })
    checkedIn.value = true
    message.success('签到成功')
  } catch (error) {
    message.error(error.message || '签到失败')
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await loadTraining()
  if (!authStore.isStudent) {
    await loadAttendance()
  }
})
</script>

<style scoped>
.checkin-page { padding: 0; }
.header-bar { background: #fff; border-radius: 10px; padding: 20px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.header-bar h2 { margin: 8px 0 4px; color: #001234; }
.header-bar p { margin: 0; color: #8c8c8c; }
.summary-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.summary-item { background: #f7f9fc; border-radius: 8px; padding: 12px; display: flex; flex-direction: column; gap: 6px; }
.summary-item span { color: #8c8c8c; font-size: 12px; }
.summary-item strong { font-size: 24px; color: #001234; }
.student-box { max-width: 520px; margin: 0 auto; }
.student-box h2 { margin: 0 0 8px; color: #001234; }
.student-box p { color: #8c8c8c; margin-bottom: 16px; }
.qr-modal-body { display: flex; flex-direction: column; gap: 12px; }
.qr-image { width: 100%; max-width: 320px; margin: 0 auto; display: block; }
.qr-meta { color: #595959; line-height: 1.8; }
</style>
