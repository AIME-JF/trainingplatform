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
          <p>请选择角色登录体验</p>
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

        <!-- 选中角色预览 -->
        <div class="role-preview" v-if="selectedRoleInfo">
          <a-tag color="blue">{{ selectedRoleInfo.unit }}</a-tag>
          <span class="preview-name">{{ selectedRoleInfo.name }} · {{ selectedRoleInfo.policeId }}</span>
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
          <span>演示版本 v1.0</span>
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
import { useAuthStore } from '../../stores/auth.js'
import { MOCK_USERS } from '../../mock/users.js'

const router = useRouter()
const authStore = useAuthStore()

const selectedRole = ref('student')
const loading = ref(false)

const roles = [
  {
    key: 'admin',
    name: '系统管理员',
    desc: '全平台管理·数据看板·人才库',
    icon: '管',
    color: '#003087',
  },
  {
    key: 'instructor',
    name: '教官',
    desc: '课程管理·AI组卷·学情分析',
    icon: '教',
    color: '#1a7a3e',
  },
  {
    key: 'student',
    name: '学员（民警）',
    desc: '在线学习·考试·个人档案',
    icon: '警',
    color: '#8b1a1a',
  },
]

const selectedRoleInfo = computed(() => {
  const user = MOCK_USERS[selectedRole.value]
  return user ? { name: user.name, policeId: user.policeId, unit: user.unit } : null
})

async function handleLogin() {
  loading.value = true
  await new Promise(r => setTimeout(r, 800))
  authStore.login(selectedRole.value)
  message.success(`欢迎回来，${authStore.currentUser.name}`)
  loading.value = false
  router.push('/')
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
  margin-bottom: 32px;
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
  gap: 10px;
  margin-bottom: 16px;
}

.role-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
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
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
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

.role-preview {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f0f4ff;
  border-radius: 6px;
  padding: 8px 12px;
  margin-bottom: 16px;
  font-size: 12px;
  color: var(--police-text-secondary);
}

.preview-name {
  font-size: 13px;
  color: var(--police-text-primary);
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
