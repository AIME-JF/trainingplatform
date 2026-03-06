<template>
  <div class="checkin-page">
    <!-- ========================
         管理员/教官视图：生成二维码 + 签到名单
         ======================== -->
    <template v-if="!isStudent">
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
              <div class="qr-label">让学员扫描下方二维码签到</div>
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
                <a-button size="small" @click="message.success('签到记录已导出')">导出</a-button>
              </a-space>
            </template>

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
    </template>

    <!-- ========================
         学员视图：根据设备区分
         ======================== -->
    <template v-else>
      <!-- PC 端提示 -->
      <div v-if="!isMobile" class="student-pc-hint">
        <div class="hint-icon">📱</div>
        <h2 class="hint-title">请使用手机扫码签到</h2>
        <p class="hint-desc">该功能需要在手机上使用摄像头扫描教官出示的二维码完成签到</p>
        <p class="hint-training">{{ training.name }}</p>
        <a-tag color="blue" style="margin-top: 12px;">请用手机打开本页面后扫码</a-tag>
      </div>

      <!-- 移动端：摄像头扫码 -->
      <div v-else class="student-scanner">
        <div class="scanner-header">
          <h2>扫码签到</h2>
          <p class="page-desc">{{ training.name }}</p>
        </div>

        <div v-if="!scanSuccess">
          <!-- 摄像头预览区 -->
          <div class="camera-wrap">
            <video ref="videoRef" class="camera-video" autoplay playsinline></video>
            <div class="scan-frame">
              <div class="scan-corner tl"></div>
              <div class="scan-corner tr"></div>
              <div class="scan-corner bl"></div>
              <div class="scan-corner br"></div>
              <div class="scan-line"></div>
            </div>
            <div v-if="cameraError" class="camera-error">
              <div style="font-size: 32px; margin-bottom: 8px;">📷</div>
              <div>{{ cameraError }}</div>
              <a-button type="primary" @click="startCamera" style="margin-top: 12px;">重试</a-button>
            </div>
          </div>
          <p class="scan-tip">将教官出示的二维码对准框内</p>
          <a-button type="primary" size="large" @click="simulateScan" block style="margin-top: 16px;">
            模拟扫码成功（演示）
          </a-button>
        </div>

        <!-- 扫码成功：确认签到 -->
        <div v-else class="scan-result-card">
          <div class="result-check">✓ 识别成功</div>
          <div class="result-training">{{ training.name }}</div>
          <div class="result-user">
            <div class="result-avatar">{{ authStore.currentUser?.name?.charAt(0) }}</div>
            <div>
              <div class="result-name">{{ authStore.currentUser?.name || '张伟' }}</div>
              <div class="result-id">{{ authStore.currentUser?.username || 'GX-NN-2056' }}</div>
            </div>
          </div>
          <button
            class="confirm-btn"
            :class="{ loading: signing }"
            @click="confirmCheckin"
            :disabled="signing || checkedIn"
          >
            <span v-if="checkedIn">✓ 签到成功</span>
            <span v-else-if="signing">签到中...</span>
            <span v-else>确认签到</span>
          </button>
          <div v-if="checkedIn" class="success-time">{{ successTime }}</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { ClockCircleOutlined } from '@ant-design/icons-vue'
import QRCode from 'qrcode'
import { MOCK_TRAININGS } from '@/mock/trainings'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const trainingId = route.params.id
const training = MOCK_TRAININGS.find(t => t.id === trainingId) || MOCK_TRAININGS[0]

const isStudent = computed(() => authStore.isStudent)
const isMobile = ref(window.innerWidth <= 768)
function onResize() { isMobile.value = window.innerWidth <= 768 }
onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))

// ===== 管理员/教官端逻辑 =====
const qrCanvas = ref(null)
const qrCountdown = ref(60)
const refreshing = ref(false)
const manualId = ref('')
const checkinRecords = ref([...training.checkinRecords])

const onTimeCount = computed(() => checkinRecords.value.filter(r => r.status === 'on_time').length)
const lateCount = computed(() => checkinRecords.value.filter(r => r.status === 'late').length)
const absentCount = computed(() => checkinRecords.value.filter(r => r.status === 'absent').length)
const recentArrivals = computed(() => checkinRecords.value.filter(r => r.status !== 'absent').slice(-3).reverse())

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

// ===== 学员移动端扫码逻辑 =====
const videoRef = ref(null)
const cameraError = ref('')
const scanSuccess = ref(false)
const signing = ref(false)
const checkedIn = ref(false)
const successTime = ref('')

async function startCamera() {
  cameraError.value = ''
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    if (videoRef.value) {
      videoRef.value.srcObject = stream
    }
  } catch (e) {
    cameraError.value = '无法访问摄像头，请检查权限设置'
  }
}

function simulateScan() {
  scanSuccess.value = true
}

async function confirmCheckin() {
  signing.value = true
  await new Promise(r => setTimeout(r, 1200))
  signing.value = false
  checkedIn.value = true
  const t = new Date()
  successTime.value = `${t.getFullYear()}-${String(t.getMonth()+1).padStart(2,'0')}-${String(t.getDate()).padStart(2,'0')} ${String(t.getHours()).padStart(2,'0')}:${String(t.getMinutes()).padStart(2,'0')}:${String(t.getSeconds()).padStart(2,'0')}`
  message.success('签到成功！')
}

let timer = null
onMounted(() => {
  if (!isStudent.value) {
    generateQR()
    timer = setInterval(() => {
      qrCountdown.value--
      if (qrCountdown.value <= 0) refreshQR()
    }, 1000)
  } else if (isMobile.value) {
    startCamera()
  }
})
onUnmounted(() => {
  clearInterval(timer)
  // 释放摄像头
  if (videoRef.value?.srcObject) {
    videoRef.value.srcObject.getTracks().forEach(t => t.stop())
  }
})
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

/* 学员 PC 端提示 */
.student-pc-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  padding: 40px;
}
.hint-icon { font-size: 80px; margin-bottom: 24px; }
.hint-title { font-size: 24px; font-weight: 700; color: var(--police-primary); margin-bottom: 12px; }
.hint-desc { font-size: 15px; color: #666; max-width: 400px; line-height: 1.7; }
.hint-training { font-size: 13px; color: #999; margin-top: 16px; }

/* 学员移动端扫码 */
.student-scanner { max-width: 480px; margin: 0 auto; }
.scanner-header { text-align: center; margin-bottom: 20px; }
.scanner-header h2 { margin: 0; font-size: 20px; font-weight: 700; color: var(--police-primary); }
.camera-wrap {
  position: relative;
  width: 100%;
  max-width: 320px;
  height: 320px;
  margin: 0 auto;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
}
.camera-video { width: 100%; height: 100%; object-fit: cover; }
.scan-frame {
  position: absolute;
  inset: 20px;
  pointer-events: none;
}
.scan-corner {
  position: absolute;
  width: 24px;
  height: 24px;
  border-color: #c8a84b;
  border-style: solid;
}
.scan-corner.tl { top: 0; left: 0; border-width: 3px 0 0 3px; }
.scan-corner.tr { top: 0; right: 0; border-width: 3px 3px 0 0; }
.scan-corner.bl { bottom: 0; left: 0; border-width: 0 0 3px 3px; }
.scan-corner.br { bottom: 0; right: 0; border-width: 0 3px 3px 0; }
.scan-line {
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(to right, transparent, #c8a84b, transparent);
  animation: scan-move 2s ease-in-out infinite;
}
@keyframes scan-move {
  0%, 100% { top: 10%; }
  50% { top: 90%; }
}
.camera-error {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.7);
  color: white;
  font-size: 14px;
  text-align: center;
  padding: 16px;
}
.scan-tip { text-align: center; color: #888; font-size: 13px; margin-top: 12px; }

/* 扫码成功确认卡片 */
.scan-result-card {
  background: white;
  border-radius: 16px;
  padding: 28px 20px;
  border: 1px solid #e8e8e8;
  text-align: center;
}
.result-check { font-size: 14px; color: #52c41a; font-weight: 600; margin-bottom: 8px; }
.result-training { font-size: 14px; color: #333; font-weight: 600; margin-bottom: 20px; }
.result-user {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f0f4ff;
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 24px;
  text-align: left;
}
.result-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #003087;
  color: #c8a84b;
  font-size: 20px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.result-name { font-size: 16px; font-weight: 700; color: #001234; }
.result-id { font-size: 12px; color: #8c8c8c; margin-top: 2px; }
.confirm-btn {
  width: 100%;
  height: 52px;
  background: #003087;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 2px;
  cursor: pointer;
  transition: all 0.2s;
}
.confirm-btn:active { transform: scale(0.97); }
.confirm-btn.loading { background: #6b8cc4; cursor: not-allowed; }
.success-time { margin-top: 12px; font-size: 12px; color: #8c8c8c; font-family: monospace; }
</style>
