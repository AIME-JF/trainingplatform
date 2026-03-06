<template>
  <div class="mobile-checkin">
    <!-- 顶部状态栏区域 -->
    <div class="checkin-header">
      <img src="../../assets/logo.png" class="header-emblem" alt="Logo" />
      <div class="header-title">智慧教育训练平台</div>
      <div class="header-sub">扫码签到确认</div>
    </div>

    <!-- 培训信息卡 -->
    <div class="training-info-card" v-if="!checkedIn">
      <div class="training-name">{{ trainingName }}</div>
      <div class="training-meta">
        <div class="meta-item">
          <span class="meta-icon">📅</span>
          <span>{{ checkinDate }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-icon">⏰</span>
          <span>{{ checkinTime }}</span>
        </div>
        <div class="meta-item">
          <span class="meta-icon">📍</span>
          <span>南宁市公安局培训基地</span>
        </div>
      </div>

      <!-- 用户信息 -->
      <div class="user-confirm">
        <div class="user-avatar">{{ userName.charAt(0) }}</div>
        <div class="user-detail">
          <div class="user-name">{{ userName }}</div>
          <div class="user-id">{{ userPoliceId }}</div>
        </div>
        <div class="confirm-mark">已识别</div>
      </div>

      <!-- 签到按钮 -->
      <button class="checkin-btn" :class="{ loading: signing }" @click="handleCheckin" :disabled="signing">
        <span v-if="!signing">确认签到</span>
        <span v-else>签到中...</span>
      </button>

      <div class="checkin-note">点击确认即完成本次签到记录</div>
    </div>

    <!-- 签到成功状态 -->
    <div class="checkin-success" v-else>
      <div class="success-icon">✓</div>
      <div class="success-title">签到成功！</div>
      <div class="success-name">{{ userName }} 已完成签到</div>
      <div class="success-time">{{ successTime }}</div>
      <div class="success-training">{{ trainingName }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// 从 URL params 或 localStorage 获取用户信息（Demo 用 mock）
const userName = ref('张伟')
const userPoliceId = ref('GX-NN-2056')
const trainingName = ref('2025年南宁市基层民警执法规范化培训（第3期）')

const now = new Date()
const checkinDate = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
const checkinTime = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`

const signing = ref(false)
const checkedIn = ref(false)
const successTime = ref('')

async function handleCheckin() {
  signing.value = true
  await new Promise(r => setTimeout(r, 1200))
  signing.value = false
  checkedIn.value = true
  const t = new Date()
  successTime.value = `${t.getFullYear()}-${String(t.getMonth()+1).padStart(2,'0')}-${String(t.getDate()).padStart(2,'0')} ${String(t.getHours()).padStart(2,'0')}:${String(t.getMinutes()).padStart(2,'0')}:${String(t.getSeconds()).padStart(2,'0')}`
}
</script>

<style scoped>
.mobile-checkin {
  min-height: 100vh;
  background: linear-gradient(160deg, #001234 0%, #003087 60%, #001849 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 20px 40px;
}

.checkin-header {
  text-align: center;
  padding: 48px 0 24px;
  color: white;
}

.header-emblem {
  width: 100px;
  height: 100px;
  margin: 0 auto 12px;
  object-fit: contain;
}

.header-title {
  font-size: 14px;
  color: rgba(255,255,255,0.7);
  margin-bottom: 4px;
}

.header-sub {
  font-size: 18px;
  font-weight: 700;
  color: white;
  letter-spacing: 1px;
}

.training-info-card {
  width: 100%;
  background: white;
  border-radius: 16px;
  padding: 24px 20px;
  margin-top: 8px;
}

.training-name {
  font-size: 15px;
  font-weight: 700;
  color: #001234;
  margin-bottom: 16px;
  line-height: 1.5;
}

.training-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #595959;
}

.meta-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.user-confirm {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f0f4ff;
  border-radius: 10px;
  padding: 12px 16px;
  margin-bottom: 24px;
}

.user-avatar {
  width: 44px;
  height: 44px;
  background: #003087;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #c8a84b;
  font-size: 20px;
  font-weight: 700;
  flex-shrink: 0;
}

.user-detail {
  flex: 1;
}

.user-name {
  font-size: 16px;
  font-weight: 700;
  color: #001234;
}

.user-id {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 2px;
}

.confirm-mark {
  background: #52c41a;
  color: white;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 20px;
}

.checkin-btn {
  width: 100%;
  height: 56px;
  background: #003087;
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 3px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 12px;
}

.checkin-btn:active {
  transform: scale(0.97);
  background: #002070;
}

.checkin-btn.loading {
  background: #6b8cc4;
  cursor: not-allowed;
}

.checkin-note {
  text-align: center;
  font-size: 12px;
  color: #8c8c8c;
}

/* 签到成功 */
.checkin-success {
  width: 100%;
  background: white;
  border-radius: 16px;
  padding: 40px 24px;
  text-align: center;
  margin-top: 8px;
}

.success-icon {
  width: 80px;
  height: 80px;
  background: #52c41a;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  color: white;
  margin: 0 auto 20px;
  animation: pop-in 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes pop-in {
  from { transform: scale(0); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.success-title {
  font-size: 24px;
  font-weight: 700;
  color: #001234;
  margin-bottom: 8px;
}

.success-name {
  font-size: 15px;
  color: #595959;
  margin-bottom: 16px;
}

.success-time {
  font-size: 13px;
  color: #8c8c8c;
  background: #f5f5f5;
  display: inline-block;
  padding: 6px 16px;
  border-radius: 20px;
  margin-bottom: 12px;
  font-family: monospace;
}

.success-training {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 8px;
  padding: 0 16px;
}
</style>
