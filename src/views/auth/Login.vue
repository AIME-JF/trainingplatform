<template>
  <div class="login-page">
    <!-- 左侧背景 -->
    <div class="login-bg">
      <div class="bg-overlay">
        <div class="bg-content">
          <div class="emblem">警</div>
          <h1>广西壮族自治区公安厅</h1>
          <h2>警务训练综合管理平台</h2>
          <p>Guangxi Police Training Management System</p>
          <div class="bg-stats">
            <div class="stat-item">
              <span class="stat-num">12,486</span>
              <span class="stat-label">注册民警</span>
            </div>
            <div class="stat-divider" />
            <div class="stat-item">
              <span class="stat-num">1,356</span>
              <span class="stat-label">课程资源</span>
            </div>
            <div class="stat-divider" />
            <div class="stat-item">
              <span class="stat-num">20</span>
              <span class="stat-label">AI智能体</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录卡片 -->
    <div class="login-form-area">
      <div class="login-card">
        <div class="login-header">
          <div class="login-logo">
            <div class="login-logo-icon">警</div>
          </div>
          <h3>警务训练平台</h3>
          <p>请选择角色并输入手机号登录</p>
        </div>

        <!-- 角色选择卡片 -->
        <div class="role-cards">
          <div
            v-for="role in roles"
            :key="role.key"
            class="role-card"
            :class="{ active: selectedRole === role.key }"
            @click="selectedRole = role.key"
          >
            <div class="role-icon" :style="{ background: role.color }">
              {{ role.icon }}
            </div>
            <div class="role-info">
              <div class="role-name">{{ role.name }}</div>
              <div class="role-desc">{{ role.desc }}</div>
            </div>
            <div class="role-check" v-if="selectedRole === role.key">✓</div>
          </div>
        </div>

        <!-- 手机号 + 验证码 -->
        <div class="form-fields">
          <a-input
            v-model:value="phone"
            size="large"
            placeholder="请输入手机号"
            maxlength="11"
            allow-clear
          >
            <template #prefix><MobileOutlined /></template>
          </a-input>

          <div class="code-row">
            <a-input
              v-model:value="code"
              size="large"
              placeholder="请输入验证码"
              maxlength="6"
              @press-enter="handleLogin"
              style="flex: 1"
            >
              <template #prefix><SafetyOutlined /></template>
            </a-input>
            <a-button
              size="large"
              :disabled="countdown > 0 || !isPhoneValid"
              :loading="sendingCode"
              class="send-btn"
              @click="sendCode"
            >
              {{ countdown > 0 ? `${countdown}s后重发` : '获取验证码' }}
            </a-button>
          </div>

          <div class="demo-hint">
            验证码将发送至您的手机，5分钟内有效
          </div>
        </div>

        <a-button
          type="primary"
          block
          size="large"
          :loading="loading"
          class="login-btn"
          @click="handleLogin"
        >
          进入系统
        </a-button>

        <div class="login-footer">
          <span>演示版本 v2.0</span>
          <span>广西公安厅训练处</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { MobileOutlined, SafetyOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '../../stores/auth.js'

const router = useRouter()
const authStore = useAuthStore()

const phone = ref('')
const code = ref('')
const selectedRole = ref('student')
const loading = ref(false)
const sendingCode = ref(false)
const countdown = ref(0)

const roles = [
  { key: 'admin', name: '系统管理员', desc: '全平台管理·数据看板·人才库', icon: '管', color: '#003087' },
  { key: 'instructor', name: '教官', desc: '课程管理·AI组卷·学情分析', icon: '教', color: '#1a7a3e' },
  { key: 'student', name: '学员（民警）', desc: '在线学习·考试·个人档案', icon: '警', color: '#8b1a1a' },
]

const isPhoneValid = computed(() => /^1[3-9]\d{9}$/.test(phone.value))

// 发送验证码
async function sendCode() {
  if (!isPhoneValid.value) { message.warning('请输入正确的手机号'); return }
  sendingCode.value = true
  try {
    const res = await fetch('http://118.145.115.139:3950/api/sms/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: phone.value }),
    })
    const data = await res.json()
    if (data.success) {
      message.success('验证码已发送（演示固定：123456）')
      startCountdown()
    } else {
      message.error(data.message || '发送失败')
    }
  } catch {
    message.error('网络异常，请稍后重试')
  } finally {
    sendingCode.value = false
  }
}

function startCountdown() {
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(timer)
  }, 1000)
}

// 登录
async function handleLogin() {
  if (!isPhoneValid.value) { message.warning('请输入正确的手机号'); return }
  if (!code.value.trim()) { message.warning('请输入验证码'); return }
  loading.value = true
  try {
    const result = await authStore.loginWithPhone(phone.value, code.value.trim(), selectedRole.value)
    if (result.success) {
      message.success(`欢迎，${authStore.currentUser.name}`)
      router.push('/')
    } else {
      message.error(result.error || '验证码错误')
    }
  } catch {
    message.error('网络异常，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 左侧背景 */
.login-bg {
  flex: 1.2;
  background: linear-gradient(135deg, #001234 0%, #003087 50%, #001849 100%);
  position: relative;
  overflow: hidden;
}

.login-bg::before {
  content: '';
  position: absolute;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: rgba(200, 168, 75, 0.05);
  top: -100px;
  right: -100px;
}

.login-bg::after {
  content: '';
  position: absolute;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: rgba(0, 48, 135, 0.3);
  bottom: -80px;
  left: -80px;
}

.bg-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.bg-content {
  text-align: center;
  color: white;
  z-index: 1;
}

.emblem {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: var(--police-gold);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 52px;
  font-weight: 900;
  color: #001234;
  margin: 0 auto 28px;
  box-shadow: 0 0 40px rgba(200, 168, 75, 0.4);
}

.bg-content h1 {
  font-size: 26px;
  font-weight: 700;
  margin-bottom: 8px;
  letter-spacing: 2px;
  color: white;
}

.bg-content h2 {
  font-size: 18px;
  font-weight: 500;
  margin-bottom: 8px;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 1px;
}

.bg-content p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 40px;
  letter-spacing: 1px;
}

.bg-stats {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 20px 32px;
  backdrop-filter: blur(10px);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-num {
  font-size: 24px;
  font-weight: 700;
  color: var(--police-gold);
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
}

/* 右侧表单 */
.login-form-area {
  width: 460px;
  background: #f5f7fb;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.login-card {
  width: 100%;
  background: white;
  border-radius: 12px;
  padding: 40px 36px;
  box-shadow: 0 4px 24px rgba(0, 48, 135, 0.12);
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-logo {
  margin-bottom: 12px;
}

.login-logo-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--police-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 900;
  color: var(--police-gold);
  margin: 0 auto;
}

.login-header h3 {
  font-size: 20px;
  font-weight: 700;
  color: var(--police-text-primary);
  margin: 8px 0 4px;
}

.login-header p {
  font-size: 13px;
  color: var(--police-text-muted);
}

/* 角色卡片 */
.role-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.role-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border: 2px solid var(--police-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.role-card:hover {
  border-color: var(--police-primary);
  background: var(--police-primary-light);
}

.role-card.active {
  border-color: var(--police-primary);
  background: var(--police-primary-light);
  box-shadow: 0 0 0 2px rgba(0, 48, 135, 0.12);
}

.role-icon {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 17px;
  font-weight: 700;
  flex-shrink: 0;
}

.role-info {
  flex: 1;
}

.role-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--police-text-primary);
}

.role-desc {
  font-size: 12px;
  color: var(--police-text-muted);
  margin-top: 2px;
}

.role-check {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--police-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

/* 表单 */
.form-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.code-row {
  display: flex;
  gap: 8px;
}

.send-btn {
  flex-shrink: 0;
  width: 120px;
  font-size: 13px;
}

.demo-hint {
  font-size: 12px;
  color: #8c8c8c;
  text-align: center;
}

.hint-code {
  font-family: monospace;
  color: #003087;
  font-weight: 700;
  background: #f0f4ff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 14px;
}

.login-btn {
  height: 46px;
  font-size: 15px;
  font-weight: 600;
  background: var(--police-primary);
  border-color: var(--police-primary);
  border-radius: 8px;
  letter-spacing: 2px;
}

.login-btn:hover {
  background: var(--police-primary-hover) !important;
  border-color: var(--police-primary-hover) !important;
}

.login-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  font-size: 12px;
  color: var(--police-text-muted);
}
</style>
