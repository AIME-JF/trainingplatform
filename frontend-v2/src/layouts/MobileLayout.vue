<template>
  <div class="app-layout">
    <!-- 图标侧栏：桌面端显示 -->
    <aside class="icon-sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">GA</div>
      </div>

      <div class="sidebar-nav">
        <div
          v-for="item in sidebarItems"
          :key="item.path"
          class="sidebar-item"
          :class="{ active: isSidebarActive(item.path) }"
          @click="navigateTo(item.path)"
        >
          <component :is="item.icon" class="sidebar-item-icon" />
          <span class="sidebar-item-label">{{ item.label }}</span>
        </div>
      </div>

      <!-- 底部用户信息 -->
      <a-dropdown placement="topLeft" :trigger="['click']">
        <div class="sidebar-user">
          <a-avatar :size="34" class="sidebar-avatar">
            {{ avatarText }}
          </a-avatar>
          <div class="sidebar-user-meta">
            <span class="sidebar-user-name">{{ displayName }}</span>
            <DownOutlined class="sidebar-user-arrow" />
          </div>
        </div>
        <template #overlay>
          <div class="sidebar-user-dropdown">
            <button type="button" class="sidebar-user-dropdown-item danger" @click="handleLogout">
              <LogoutOutlined />
              <span>退出登录</span>
            </button>
          </div>
        </template>
      </a-dropdown>
    </aside>

    <!-- 主体 -->
    <div class="layout-body">
      <router-view />
    </div>

    <!-- 底部导航栏：移动端显示 -->
    <nav v-if="isMobile" class="bottom-nav">
      <div
        v-for="tab in bottomTabs"
        :key="tab.path"
        class="bottom-nav-item"
        :class="{ active: isTabActive(tab.path) }"
        @click="navigateTo(tab.path)"
      >
        <component :is="tab.icon" class="nav-icon" />
        <span>{{ tab.label }}</span>
      </div>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  HomeOutlined,
  CalendarOutlined,
  ReadOutlined,
  DatabaseOutlined,
  UserOutlined,
  DownOutlined,
  LogoutOutlined,
} from '@ant-design/icons-vue'
import { useMobile } from '@/composables/useMobile'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const currentRoute = useRoute()
const authStore = useAuthStore()
const { isMobile } = useMobile()

const displayName = computed(() => authStore.currentUser?.name || authStore.currentUser?.username || '用户')
const avatarText = computed(() => (displayName.value || '').slice(0, 1))

const sidebarItems = [
  { path: '/', label: '首页', icon: HomeOutlined },
  { path: '/classes/schedule', label: '日历', icon: CalendarOutlined },
  { path: '/classes', label: '班级', icon: ReadOutlined },
  { path: '/resource/courses', label: '学习资源', icon: DatabaseOutlined },
]

const bottomTabs = [
  { path: '/', label: '首页', icon: HomeOutlined },
  { path: '/classes', label: '班级', icon: ReadOutlined },
  { path: '/resource/courses', label: '资源', icon: DatabaseOutlined },
  { path: '/profile', label: '我的', icon: UserOutlined },
]

const activeSidebarPath = computed(() => {
  const sortedItems = [...sidebarItems].sort((left, right) => right.path.length - left.path.length)
  return sortedItems.find((item) => isRouteMatch(item.path))?.path || ''
})

function isRouteMatch(path: string): boolean {
  if (path === '/') return currentRoute.path === '/'
  return currentRoute.path === path || currentRoute.path.startsWith(`${path}/`)
}

function isSidebarActive(path: string): boolean {
  return activeSidebarPath.value === path
}

function isTabActive(path: string): boolean {
  return isRouteMatch(path)
}

function navigateTo(path: string) {
  router.push(path)
}

function handleLogout() {
  authStore.logout()
  router.replace('/login')
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}

/* -- 品牌图标 -- */
.sidebar-brand {
  margin-bottom: 12px;
  padding: 8px 0 4px;
}

.brand-icon {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: linear-gradient(135deg, #183B8C 0%, var(--v2-primary) 100%);
  box-shadow: 0 12px 24px rgba(75, 110, 245, 0.22);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

/* -- 导航区域（占满中间空间） -- */
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

/* -- 侧栏项 -- */
.sidebar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: calc(var(--v2-sidebar-width) - 16px);
  min-height: 64px;
  border-radius: 18px;
  cursor: pointer;
  color: var(--v2-text-muted);
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
  gap: 6px;
  padding: 10px 0;
}

.sidebar-item:hover {
  background: var(--v2-bg);
  color: var(--v2-text-secondary);
  transform: translateY(-1px);
}

.sidebar-item.active {
  background: var(--v2-primary-light);
  color: var(--v2-primary);
  box-shadow: inset 0 0 0 1px rgba(75, 110, 245, 0.08);
}

.sidebar-item-icon {
  font-size: 24px;
  line-height: 1;
}

.sidebar-item-label {
  font-size: 12px;
  line-height: 1.2;
  font-weight: 500;
  white-space: nowrap;
  letter-spacing: 0.01em;
}

/* -- 底部用户区域 -- */
.sidebar-user {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: calc(var(--v2-sidebar-width) - 16px);
  padding: 10px 6px 12px;
  border-radius: 18px;
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.2s ease;
}

.sidebar-user:hover {
  background: var(--v2-bg);
  transform: translateY(-1px);
}

.sidebar-avatar {
  background: linear-gradient(135deg, #003087 0%, var(--v2-primary) 100%);
  box-shadow: 0 10px 24px rgba(24, 59, 140, 0.22);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.sidebar-user-meta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
}

.sidebar-user-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--v2-text-primary);
  max-width: 46px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
}

.sidebar-user-arrow {
  font-size: 10px;
  color: var(--v2-text-secondary);
  flex-shrink: 0;
}

.sidebar-user-dropdown {
  min-width: 140px;
  padding: 6px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(229, 229, 234, 0.92);
  box-shadow: var(--v2-shadow-lg);
  backdrop-filter: blur(14px);
}

.sidebar-user-dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  border: 0;
  background: transparent;
  padding: 10px 12px;
  border-radius: 10px;
  font: inherit;
  font-size: 13px;
  color: var(--v2-text-primary);
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.sidebar-user-dropdown-item:hover {
  background: var(--v2-bg);
}

.sidebar-user-dropdown-item.danger {
  color: var(--v2-danger);
}

/* -- 主体 -- */
.layout-body {
  min-height: 100vh;
}

@media (min-width: 769px) {
  .layout-body {
    margin-left: var(--v2-sidebar-width);
  }
}
</style>
