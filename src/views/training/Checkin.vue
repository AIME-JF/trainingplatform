<template>
  <div class="checkin-page">
    <!-- ========================
         管理员/教官视图：生成二维码 + 签到名单
         ======================== -->
    <template v-if="!isStudent">
      <div class="unified-header">
        <div class="uh-top">
          <a-button type="link" @click="router.push(`/training/${trainingId}`)" style="padding: 0; font-size: 15px;">
            ← 返回培训班详情
          </a-button>
        </div>
        
        <div class="uh-main">
          <!-- 左侧：签到项选择 -->
          <div class="uh-left">
            <div class="uh-session-control">
              <span class="uh-label">当前签到项</span>
              <a-select
                v-model:value="currentSessionKey"
                class="uh-select"
                @change="handleSessionChange"
              >
                <a-select-option value="start">开班报到</a-select-option>
                <template v-for="(c, cIdx) in training.courses" :key="`c-${cIdx}`">
                  <a-select-option 
                    v-for="(sch, sIdx) in c.schedules" 
                    :key="`course-${cIdx}-${sIdx}`" 
                    :value="`course-${cIdx}-${sIdx}`"
                  >
                    {{ c.name }} ({{ sch.date }} {{ sch.timeRange }})
                  </a-select-option>
                </template>
              </a-select>
            </div>
            <div class="uh-training-name">{{ training.name }}</div>
          </div>
          
          <!-- 右侧：统一的签到数据展示区 -->
          <div class="uh-right">
            <div class="uh-stat-group">
              <div class="uh-stat-item">
                <span class="uh-stat-label">已签到</span>
                <span class="uh-stat-val green">{{ onTimeCount }}</span>
              </div>
              <div class="uh-divider"></div>
              <div class="uh-stat-item">
                <span class="uh-stat-label">迟到</span>
                <span class="uh-stat-val orange">{{ lateCount }}</span>
              </div>
              <div class="uh-divider"></div>
              <div class="uh-stat-item">
                <span class="uh-stat-label">缺席</span>
                <span class="uh-stat-val red">{{ absentCount }}</span>
              </div>
            </div>
            
            <div class="uh-rate-box">
              <div class="uh-rate-texts">
                <span class="uh-rate-title">签到完成率</span>
                <span class="uh-rate-subtitle">实时更新</span>
              </div>
              <a-progress type="circle" :percent="checkinRate" :width="56" :strokeWidth="8" :stroke-color="checkinRate >= 80 ? '#52c41a' : (checkinRate >= 60 ? '#faad14' : '#ff4d4f')" />
            </div>
          </div>
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
                <a-button size="small" @click="exportCheckinRecords">导出</a-button>
              </a-space>
            </template>



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
          <button class="back-btn" @click="router.push(`/training/${trainingId}`)">← 返回</button>
          <h2>{{ sessionName }} 扫码签到</h2>
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

        <!-- 扮码成功：确认签到 / 签到成功 -->
        <div v-else class="scan-result-card">
          <!-- 签到过程中 / 签到前 -->
          <template v-if="!checkedIn">
            <div class="result-check">✓ 识别成功</div>
            <div class="result-training">{{ sessionName }}</div>
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
              :disabled="signing"
            >
              <span v-if="signing">签到中...</span>
              <span v-else>确认签到</span>
            </button>
            <button class="back-link" @click="scanSuccess = false">重新扮码</button>
          </template>

          <!-- 签到成功页 -->
          <template v-else>
            <div class="success-icon-wrap">✓</div>
            <div class="success-title">签到成功！</div>
            <div class="success-name">{{ authStore.currentUser?.name || '张伟' }} 已完成签到</div>
            <div class="success-time">{{ successTime }}</div>
            <div class="success-training">{{ sessionName }}</div>
            <div class="redirect-tip">{{ redirectCount }}秒后自动返回培训班页面...</div>
            <button class="confirm-btn" @click="goTraining">返回培训班页面</button>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { ClockCircleOutlined } from '@ant-design/icons-vue'
import QRCode from 'qrcode'
import { getTraining, checkin as apiCheckin, getCheckinRecords as apiGetCheckinRecords } from '@/api/training'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const trainingId = route.params.id
const currentSessionKey = ref(route.params.sessionKey || 'start')
const training = ref({ id: trainingId, name: '', courses: [], checkinRecords: [], enrolled: 0 })

onMounted(async () => {
  try {
    const data = await getTraining(trainingId)
    training.value = data
  } catch { /* ignore */ }
})

const handleSessionChange = (newKey) => {
  router.replace(`/training/${trainingId}/checkin/${newKey}`)
}

const sessionName = computed(() => {
  if (currentSessionKey.value === 'start') return '开班报到'
  if (currentSessionKey.value.startsWith('course-')) {
    const parts = currentSessionKey.value.split('-')
    const cIdx = parseInt(parts[1], 10)
    const sIdx = parseInt(parts[2], 10)
    if (!isNaN(cIdx) && !isNaN(sIdx) && training.value.courses[cIdx]) {
      const c = training.value.courses[cIdx]
      const sch = c.schedules ? c.schedules[sIdx] : null
      if (sch) {
        return `${c.name} (${sch.date} ${sch.timeRange})`
      }
      return c.name
    }
  }
  return '未命名阶段'
})

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

const checkinRecords = computed(() => {
  if (!training.value.checkinRecords) return []
  return training.value.checkinRecords.filter(r => r.sessionKey === currentSessionKey.value)
})

const onTimeCount = computed(() => checkinRecords.value.filter(r => r.status === 'on_time').length)
const lateCount = computed(() => checkinRecords.value.filter(r => r.status === 'late').length)
const absentCount = computed(() => checkinRecords.value.filter(r => r.status === 'absent').length)
const totalCheckedIn = computed(() => onTimeCount.value + lateCount.value)
const checkinRate = computed(() => {
  if (training.value.enrolled === 0) return 0
  return Math.round((totalCheckedIn.value / training.value.enrolled) * 100)
})
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
    await QRCode.toCanvas(qrCanvas.value, `checkin:${training.value.id}:${currentSessionKey.value}:${Date.now()}`, {
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

const exportCheckinRecords = () => {
  if (checkinRecords.value.length === 0) {
    message.warning('暂无签到记录可导出')
    return
  }
  
  // 构造 CSV 内容
  const headers = ['姓名', '警号/工号', '签到时间', '状态']
  const rows = checkinRecords.value.map(r => [
    r.name, 
    `\t${r.studentId}`, 
    r.time, 
    statusLabels[r.status]
  ])
  
  const csvContent = [headers, ...rows].map(e => e.join(",")).join("\n")
  const blob = new Blob(["\ufeff" + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement("a")
  const url = URL.createObjectURL(blob)
  link.setAttribute("href", url)
  link.setAttribute("download", `${training.value.name}_${sessionName.value}_签到记录.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  message.success(`${sessionName.value} 签到记录已导出下载`)
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

const redirectCount = ref(3)
let redirectTimer = null

async function confirmCheckin() {
  signing.value = true
  await new Promise(r => setTimeout(r, 1200))
  signing.value = false
  checkedIn.value = true
  const t = new Date()
  successTime.value = `${t.getFullYear()}-${String(t.getMonth()+1).padStart(2,'0')}-${String(t.getDate()).padStart(2,'0')} ${String(t.getHours()).padStart(2,'0')}:${String(t.getMinutes()).padStart(2,'0')}:${String(t.getSeconds()).padStart(2,'0')}`
  message.success('签到成功！')
  // 3秒后自动返回培训班
  redirectCount.value = 3
  redirectTimer = setInterval(() => {
    redirectCount.value--
    if (redirectCount.value <= 0) {
      clearInterval(redirectTimer)
      goTraining()
    }
  }, 1000)
}

function goTraining() {
  clearInterval(redirectTimer)
  router.push(`/training/${trainingId}`)
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
  clearInterval(redirectTimer)
  // 释放摄像头
  if (videoRef.value?.srcObject) {
    videoRef.value.srcObject.getTracks().forEach(t => t.stop())
  }
})
</script>

<style scoped>
.checkin-page { padding: 0; }
.unified-header {
  background: white;
  padding: 16px 24px;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  margin-bottom: 24px;
}
.uh-top { margin-bottom: 12px; }
.uh-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}
.uh-left { display: flex; flex-direction: column; gap: 8px; }
.uh-session-control { display: flex; align-items: center; gap: 12px; }
.uh-label { font-size: 14px; color: #64748b; font-weight: 500; }
.uh-select { width: 340px; }
:deep(.uh-select .ant-select-selector) { font-size: 16px; font-weight: 600; color: #0f172a; height: 40px; padding: 4px 11px; }
.uh-training-name { font-size: 13px; color: #94a3b8; }

.uh-right {
  display: flex;
  align-items: center;
  background: #f8fafc;
  padding: 12px 24px;
  border-radius: 10px;
  border: 1px solid #f1f5f9;
  gap: 32px;
}
.uh-stat-group { display: flex; align-items: center; gap: 24px; }
.uh-stat-item { display: flex; flex-direction: column; align-items: center; }
.uh-stat-label { font-size: 12px; color: #64748b; margin-bottom: 4px; }
.uh-stat-val { font-size: 22px; font-weight: 700; font-family: 'Helvetica Neue', Arial, sans-serif; }
.uh-stat-val.green { color: #52c41a; }
.uh-stat-val.orange { color: #faad14; }
.uh-stat-val.red { color: #ff4d4f; }
.uh-divider { width: 1px; height: 32px; background: #e2e8f0; }

.uh-rate-box { display: flex; align-items: center; gap: 16px; }
.uh-rate-texts { display: flex; flex-direction: column; align-items: flex-end; }
.uh-rate-title { font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 2px; }
.uh-rate-subtitle { font-size: 11px; color: #94a3b8; }
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
.back-btn {
  background: none;
  border: none;
  color: var(--police-primary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  margin-bottom: 8px;
  display: block;
}
.back-link {
  display: block;
  width: 100%;
  margin-top: 12px;
  background: none;
  border: none;
  color: #8c8c8c;
  font-size: 13px;
  cursor: pointer;
  text-decoration: underline;
}
.success-icon-wrap {
  width: 72px;
  height: 72px;
  background: #52c41a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  color: white;
  margin: 0 auto 16px;
  animation: pop-in 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes pop-in {
  from { transform: scale(0); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.success-title { font-size: 22px; font-weight: 700; color: #001234; margin-bottom: 6px; }
.success-name { font-size: 14px; color: #595959; margin-bottom: 12px; }
.success-training { font-size: 12px; color: #8c8c8c; margin-bottom: 16px; padding: 0 8px; }
.redirect-tip { font-size: 12px; color: #aaa; margin-bottom: 16px; }
</style>
