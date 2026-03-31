<template>
  <section class="page-content dashboard-page">
    <template v-if="isDashboardRoute">
      <section class="hero-card">
        <div class="hero-copy">
          <span class="hero-badge">{{ greetingText }}</span>
          <h1 class="hero-title">欢迎回来，{{ displayName }}</h1>
          <p class="hero-subtitle">{{ heroSubtitle }}</p>

          <div class="hero-pills">
            <span class="hero-pill">
              <TeamOutlined />
              {{ roleLabel }}
            </span>
            <span class="hero-pill">
              <CalendarOutlined />
              {{ todayText }}
            </span>
            <span v-if="authStore.currentUser?.unit" class="hero-pill">
              <HomeOutlined />
              {{ authStore.currentUser.unit }}
            </span>
          </div>
        </div>

        <div class="hero-summary">
          <div v-for="item in overviewStats" :key="item.label" class="summary-card">
            <span class="summary-label">{{ item.label }}</span>
            <strong class="summary-value">
              {{ item.value }}
              <small v-if="item.suffix">{{ item.suffix }}</small>
            </strong>
          </div>
        </div>
      </section>

      <section class="dashboard-grid">
        <article class="surface-card">
          <div class="section-head">
            <div>
              <h2>快捷入口</h2>
              <p>按当前权限进入常用功能模块。</p>
            </div>
          </div>

          <div class="quick-grid">
            <button
              v-for="action in quickActions"
              :key="action.path"
              type="button"
              class="quick-item"
              @click="navigateTo(action.path)"
            >
              <span class="quick-icon" :style="{ background: action.background }">
                <component :is="action.icon" />
              </span>
              <span class="quick-text">
                <strong>{{ action.title }}</strong>
                <span>{{ action.description }}</span>
              </span>
              <RightOutlined class="quick-arrow" />
            </button>
          </div>
        </article>

        <article class="surface-card">
          <div class="section-head">
            <div>
              <h2>账号概览</h2>
              <p>当前登录账号的基础信息。</p>
            </div>
          </div>

          <div class="info-list">
            <div v-for="item in profileItems" :key="item.label" class="info-row">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </article>
      </section>

      <section class="dashboard-grid dashboard-grid-secondary">
        <article class="surface-card">
          <div class="section-head">
            <div>
              <h2>当前可用模块</h2>
              <p>和侧边栏保持一致的模块入口视图。</p>
            </div>
          </div>

          <div class="module-list">
            <div v-for="item in quickActions" :key="`${item.path}-module`" class="module-item">
              <span class="module-icon" :style="{ background: item.background }">
                <component :is="item.icon" />
              </span>
              <div class="module-copy">
                <strong>{{ item.title }}</strong>
                <span>{{ item.description }}</span>
              </div>
            </div>
          </div>
        </article>

        <article class="surface-card tips-card">
          <div class="section-head">
            <div>
              <h2>使用提示</h2>
              <p>首页只展示工作台，其他占位页面不再复用这一版面。</p>
            </div>
          </div>

          <div class="tips-list">
            <div v-for="tip in tips" :key="tip.title" class="tip-item">
              <span class="tip-index">{{ tip.index }}</span>
              <div class="tip-copy">
                <strong>{{ tip.title }}</strong>
                <span>{{ tip.description }}</span>
              </div>
            </div>
          </div>
        </article>
      </section>
    </template>

    <section v-else class="surface-card placeholder-card">
      <span class="hero-badge placeholder-badge">模块建设中</span>
      <h1 class="placeholder-title">{{ currentTitle }}</h1>
      <p class="placeholder-text">
        当前页面已接入整体布局与权限控制，后续业务内容可以在这里继续补充。为了避免首页样式污染其它占位页，这里改成了独立的占位外观。
      </p>
      <div class="placeholder-actions">
        <a-button type="primary" @click="navigateTo('/')">返回工作台</a-button>
        <a-button v-if="quickActions[0]" @click="navigateTo(quickActions[0].path)">
          前往{{ quickActions[0].title }}
        </a-button>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  CalendarOutlined,
  DatabaseOutlined,
  HomeOutlined,
  ReadOutlined,
  RightOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  COURSE_PERMISSIONS,
  PROFILE_PERMISSIONS,
  TRAINING_PERMISSIONS,
  TRAINING_SCHEDULE_PERMISSIONS,
} from '@/constants/permissions'

interface MetricItem {
  label: string
  value: string
  suffix?: string
}

interface QuickAction {
  title: string
  description: string
  path: string
  icon: Component
  background: string
  permissions: string[]
}

const router = useRouter()
const currentRoute = useRoute()
const authStore = useAuthStore()

const displayName = computed(() => authStore.currentUser?.name || authStore.currentUser?.username || '用户')
const isDashboardRoute = computed(() => currentRoute.path === '/')
const currentTitle = computed(() => currentRoute.meta.title || '当前页面')

const roleLabel = computed(() => {
  if (authStore.isInstructor) return '教官'
  if (authStore.isStudent) return '学员'
  return authStore.role || '已登录用户'
})

const now = new Date()
const hour = now.getHours()
const greetingText = hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好'
const todayText = new Intl.DateTimeFormat('zh-CN', {
  month: 'long',
  day: 'numeric',
  weekday: 'long',
}).format(now)

const heroSubtitle = computed(() => {
  const unit = authStore.currentUser?.unit || '当前单位待完善'
  return `当前以${roleLabel.value}身份登录，已接入班级、日历与资源模块。所属单位：${unit}。`
})

const overviewStats = computed<MetricItem[]>(() => [
  { label: '权限项', value: String(authStore.permissions.length), suffix: '项' },
  { label: '角色数', value: String(Math.max(authStore.roleCodes.length, authStore.role ? 1 : 0)), suffix: '个' },
  { label: '学习时长', value: formatMetric(authStore.currentUser?.study_hours), suffix: 'h' },
  { label: '考试次数', value: formatMetric(authStore.currentUser?.exam_count), suffix: '次' },
])

const quickActionConfigs: QuickAction[] = [
  {
    title: '班级列表',
    description: '查看训练班、时间安排与详情。',
    path: '/classes',
    icon: ReadOutlined,
    background: 'var(--v2-cover-blue)',
    permissions: TRAINING_PERMISSIONS,
  },
  {
    title: '训练日历',
    description: '进入周训练计划与课程排期。',
    path: '/classes/schedule',
    icon: CalendarOutlined,
    background: 'var(--v2-cover-green)',
    permissions: TRAINING_SCHEDULE_PERMISSIONS,
  },
  {
    title: '学习资源',
    description: '继续课程学习与资源浏览。',
    path: '/resource/courses',
    icon: DatabaseOutlined,
    background: 'var(--v2-cover-purple)',
    permissions: COURSE_PERMISSIONS,
  },
  {
    title: '个人中心',
    description: '查看和维护当前登录账号信息。',
    path: '/profile',
    icon: UserOutlined,
    background: 'var(--v2-cover-orange)',
    permissions: PROFILE_PERMISSIONS,
  },
]

const quickActions = computed(() => quickActionConfigs.filter((item) => authStore.hasAnyPermission(item.permissions)))

const profileItems = computed(() => [
  { label: '显示名称', value: displayName.value },
  { label: '登录账号', value: authStore.currentUser?.username || '-' },
  { label: '当前角色', value: roleLabel.value },
  { label: '所属单位', value: authStore.currentUser?.unit || '未设置' },
  { label: '警号', value: authStore.currentUser?.police_id || '未设置' },
])

const tips = [
  { index: '01', title: '首页和占位页解耦', description: '真正的工作台只在 `/` 展示，避免其它页面复用后出现语义错位。' },
  { index: '02', title: '侧边栏入口统一', description: '日历入口已指向实际存在的周训练计划路由，并保留 `/calendar` 兼容跳转。' },
  { index: '03', title: '视觉语言保持一致', description: '继续沿用 v2 的低饱和渐变、圆角卡片和轻阴影体系。' },
]

function formatMetric(value: number | undefined) {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function navigateTo(path: string) {
  router.push(path)
}
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  background:
    radial-gradient(circle at top right, rgba(75, 110, 245, 0.1), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.78) 0%, rgba(245, 246, 250, 0.92) 100%);
}

.hero-card {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(280px, 1fr);
  gap: 24px;
  padding: 28px;
  border-radius: 28px;
  overflow: hidden;
  background: var(--v2-bg-header);
  color: var(--v2-text-white);
  box-shadow: 0 24px 40px rgba(15, 52, 96, 0.18);
}

.hero-card::before,
.hero-card::after {
  content: '';
  position: absolute;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
}

.hero-card::before {
  width: 220px;
  height: 220px;
  top: -110px;
  right: -50px;
}

.hero-card::after {
  width: 160px;
  height: 160px;
  right: 180px;
  bottom: -90px;
}

.hero-copy,
.hero-summary {
  position: relative;
  z-index: 1;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 14px;
  justify-content: center;
}

.hero-badge {
  display: inline-flex;
  width: fit-content;
  align-items: center;
  padding: 6px 12px;
  border-radius: var(--v2-radius-full);
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.14);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.hero-title {
  font-size: clamp(28px, 3vw, 40px);
  line-height: 1.1;
  margin: 0;
}

.hero-subtitle {
  max-width: 640px;
  font-size: 15px;
  line-height: 1.75;
  color: rgba(255, 255, 255, 0.78);
  margin: 0;
}

.hero-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.hero-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: var(--v2-radius-full);
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.92);
  font-size: 13px;
}

.hero-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.summary-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 116px;
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(16px);
}

.summary-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.66);
  letter-spacing: 0.06em;
}

.summary-value {
  font-size: 30px;
  line-height: 1;
  font-weight: 700;
}

.summary-value small {
  font-size: 14px;
  margin-left: 4px;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.95fr);
  gap: 20px;
}

.dashboard-grid-secondary {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.surface-card {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 24px;
  padding: 24px;
  box-shadow: var(--v2-shadow);
  backdrop-filter: blur(16px);
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.section-head h2 {
  font-size: 18px;
  line-height: 1.2;
  margin-bottom: 6px;
}

.section-head p {
  color: var(--v2-text-secondary);
  line-height: 1.7;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.quick-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  border: 1px solid rgba(229, 229, 234, 0.9);
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(245, 246, 250, 0.92) 100%);
  text-align: left;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.quick-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--v2-shadow-lg);
  border-color: rgba(75, 110, 245, 0.18);
}

.quick-icon,
.module-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 16px;
  color: var(--v2-text-primary);
  font-size: 22px;
  flex-shrink: 0;
}

.quick-text {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.quick-text strong,
.module-copy strong,
.tip-copy strong {
  font-size: 15px;
  color: var(--v2-text-primary);
}

.quick-text span,
.module-copy span,
.tip-copy span {
  font-size: 13px;
  color: var(--v2-text-secondary);
  line-height: 1.6;
}

.quick-arrow {
  color: var(--v2-text-muted);
  font-size: 13px;
  flex-shrink: 0;
}

.info-list,
.module-list,
.tips-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row,
.module-item,
.tip-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(245, 246, 250, 0.88) 0%, rgba(255, 255, 255, 0.94) 100%);
}

.info-row {
  justify-content: space-between;
  gap: 20px;
}

.info-row span {
  color: var(--v2-text-secondary);
}

.info-row strong {
  color: var(--v2-text-primary);
  text-align: right;
}

.module-copy,
.tip-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tip-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: var(--v2-primary-light);
  color: var(--v2-primary);
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.tips-card {
  position: relative;
  overflow: hidden;
}

.tips-card::after {
  content: '';
  position: absolute;
  inset: auto -50px -70px auto;
  width: 180px;
  height: 180px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(75, 110, 245, 0.12), transparent 65%);
}

.placeholder-card {
  min-height: 320px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 18px;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(240, 243, 255, 0.92) 100%),
    var(--v2-bg-card);
}

.placeholder-badge {
  background: var(--v2-primary-light);
  border-color: transparent;
  color: var(--v2-primary);
}

.placeholder-title {
  font-size: clamp(28px, 3vw, 40px);
  line-height: 1.1;
}

.placeholder-text {
  max-width: 760px;
  color: var(--v2-text-secondary);
  line-height: 1.8;
}

.placeholder-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

@media (max-width: 1200px) {
  .hero-card,
  .dashboard-grid,
  .dashboard-grid-secondary {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .dashboard-page {
    gap: 16px;
  }

  .hero-card,
  .surface-card {
    padding: 18px;
    border-radius: 20px;
  }

  .hero-summary,
  .quick-grid {
    grid-template-columns: 1fr;
  }

  .summary-card {
    min-height: 96px;
  }

  .quick-item,
  .info-row,
  .module-item,
  .tip-item {
    padding: 14px;
  }

  .info-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .placeholder-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
