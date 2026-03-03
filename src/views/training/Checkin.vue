<template>
  <div class="checkin-page">
    <div class="page-header">
      <div>
        <h2>扫码签到</h2>
        <p class="page-desc">{{ training.name }}</p>
      </div>
      <div class="checkin-stats">
        <span class="cs-item"><span class="cs-num green">{{ onTimeCount }}</span>已签到</span>
        <span class="cs-item"><span class="cs-num orange">{{ lateCount }}</span>迟到</span>
        <span class="cs-item"><span class="cs-num red">{{ absentCount }}</span>缺席</span>
      </div>
    </div>

    <a-row :gutter="20">
      <!-- QR码区 -->
      <a-col :span="10">
        <a-card :bordered="false" class="qr-card">
          <div class="qr-container">
            <div class="qr-label">扫描二维码签到</div>
            <div class="qr-wrap">
              <canvas ref="qrCanvas" class="qr-canvas"></canvas>
              <div class="qr-overlay" v-if="refreshing">
                <div class="refresh-icon">🔄</div>
                <div>更新中...</div>
              </div>
            </div>
            <div class="qr-timer">
              <ClockCircleOutlined />
              {{ qrCountdown }}s 后自动刷新
            </div>
            <a-button @click="refreshQR" :loading="refreshing" style="margin-top:12px">
              立即刷新
            </a-button>
          </div>

          <a-divider>也可手动输入工号签到</a-divider>
          <a-input-search
            v-model:value="manualId"
            placeholder="输入工号..."
            enter-button="签到"
            @search="manualCheckin"
          />
        </a-card>
      </a-col>

      <!-- 签到名单 -->
      <a-col :span="14">
        <a-card title="签到记录" :bordered="false">
          <template #extra>
            <a-space>
              <a-tag color="green">{{ onTimeCount }} 准时</a-tag>
              <a-tag color="orange">{{ lateCount }} 迟到</a-tag>
              <a-button size="small">导出</a-button>
            </a-space>
          </template>

          <!-- 最新到达动画区 -->
          <div class="arrival-feed" v-if="recentArrivals.length > 0">
            <transition-group name="arrival">
              <div v-for="arrival in recentArrivals" :key="arrival.id" class="arrival-item">
                <a-avatar :style="{ background: '#003087' }">{{ arrival.name.charAt(0) }}</a-avatar>
                <div class="arrival-info">
                  <span class="arrival-name">{{ arrival.name }}</span>
                  <span class="arrival-time">{{ arrival.time }}</span>
                </div>
                <a-tag :color="arrival.status === 'on_time' ? 'green' : 'orange'" size="small">
                  {{ arrival.status === 'on_time' ? '准时' : '迟到' }}
                </a-tag>
              </div>
            </transition-group>
          </div>

          <!-- 完整名单 -->
          <a-table
            :dataSource="checkinRecords"
            :columns="columns"
            size="small"
            :pagination="{ pageSize: 8 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="statusColors[record.status]" size="small">{{ statusLabels[record.status] }}</a-tag>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { ClockCircleOutlined } from '@ant-design/icons-vue'
import QRCode from 'qrcode'
import { MOCK_TRAININGS } from '@/mock/trainings'

const route = useRoute()
const trainingId = route.params.id
const training = MOCK_TRAININGS.find(t => t.id === trainingId) || MOCK_TRAININGS[0]

const qrCanvas = ref(null)
const qrCountdown = ref(60)
const refreshing = ref(false)
const manualId = ref('')

const checkinRecords = ref([...training.checkinRecords])

const onTimeCount = computed(() => checkinRecords.value.filter(r => r.status === 'on_time').length)
const lateCount = computed(() => checkinRecords.value.filter(r => r.status === 'late').length)
const absentCount = computed(() => checkinRecords.value.filter(r => r.status === 'absent').length)

const recentArrivals = computed(() =>
  checkinRecords.value.filter(r => r.status !== 'absent').slice(-3).reverse()
)

const statusColors = { on_time: 'green', late: 'orange', absent: 'red' }
const statusLabels = { on_time: '准时', late: '迟到', absent: '缺席' }

const columns = [
  { title: '姓名', dataIndex: 'name', key: 'name' },
  { title: '工号', dataIndex: 'studentId', key: 'studentId' },
  { title: '签到时间', dataIndex: 'time', key: 'time' },
  { title: '状态', key: 'status' },
]

const generateQR = async () => {
  if (!qrCanvas.value) return
  try {
    await QRCode.toCanvas(qrCanvas.value, `checkin:${training.id}:${Date.now()}`, {
      width: 200,
      color: { dark: '#003087', light: '#ffffff' }
    })
  } catch (e) {}
}

const refreshQR = async () => {
  refreshing.value = true
  qrCountdown.value = 60
  await generateQR()
  setTimeout(() => { refreshing.value = false }, 500)
}

const manualCheckin = (id) => {
  if (!id) return
  message.success(`工号 ${id} 签到成功！`)
  manualId.value = ''
}

let timer = null
onMounted(() => {
  generateQR()
  timer = setInterval(() => {
    qrCountdown.value--
    if (qrCountdown.value <= 0) refreshQR()
  }, 1000)
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.checkin-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.page-desc { color: #888; font-size: 13px; margin-top: 4px; }
.checkin-stats { display: flex; gap: 24px; }
.cs-item { text-align: center; font-size: 12px; color: #888; }
.cs-num { display: block; font-size: 28px; font-weight: 700; }
.cs-num.green { color: #52c41a; }
.cs-num.orange { color: #faad14; }
.cs-num.red { color: #ff4d4f; }
.qr-card { }
.qr-container { display: flex; flex-direction: column; align-items: center; padding: 20px; }
.qr-label { font-size: 14px; color: #555; margin-bottom: 16px; }
.qr-wrap { position: relative; }
.qr-canvas { border: 4px solid var(--police-primary); border-radius: 8px; display: block; }
.qr-overlay { position: absolute; inset: 0; background: rgba(255,255,255,0.85); display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 4px; }
.refresh-icon { font-size: 32px; margin-bottom: 8px; }
.qr-timer { margin-top: 12px; color: #888; font-size: 13px; display: flex; align-items: center; gap: 6px; }
.arrival-feed { margin-bottom: 16px; }
.arrival-item { display: flex; align-items: center; gap: 12px; padding: 8px; background: #f6ffed; border-radius: 6px; margin-bottom: 6px; border-left: 3px solid #52c41a; }
.arrival-info { flex: 1; }
.arrival-name { font-weight: 600; color: #1a1a1a; margin-right: 8px; }
.arrival-time { font-size: 12px; color: #888; }
.arrival-enter-active { transition: all 0.4s; }
.arrival-enter-from { opacity: 0; transform: translateY(-20px); }
</style>
