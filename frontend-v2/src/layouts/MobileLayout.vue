<template>
  <div class="app-layout">
    <!-- 图标侧栏：桌面端显示 -->
    <aside class="icon-sidebar">
      <div class="sidebar-brand">
        <div class="brand-icon">AI</div>
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
      <div class="sidebar-user" @click="navigateTo('/profile')">
        <a-avatar :size="32" class="sidebar-avatar">
          {{ avatarText }}
        </a-avatar>
        <span class="sidebar-user-name">{{ displayName }}</span>
      </div>
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
  { path: '/calendar', label: '日历', icon: CalendarOutlined },
  { path: '/classes', label: '班级', icon: ReadOutlined },
  { path: '/resource/library', label: '学习资源', icon: DatabaseOutlined },
]

const bottomTabs = [
  { path: '/', label: '首页', icon: HomeOutlined },
  { path: '/classes', label: '班级', icon: ReadOutlined },
  { path: '/resource/library', label: '资源', icon: DatabaseOutlined },
  { path: '/profile', label: '我的', icon: UserOutlined },
]

function isSidebarActive(path: string): boolean {
  if (path === '/') return currentRoute.path === '/'
  return currentRoute.path.startsWith(path)
}

function isTabActive(path: string): boolean {
  if (path === '/') return currentRoute.path === '/'
  return currentRoute.path.startsWith(path)
}

function navigateTo(path: string) {
  router.push(path)
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}

/* -- 品牌图标 -- */
.sidebar-brand {
  margin-bottom: 8px;
  padding: 8px 0;
}

.brand-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--v2-radius-sm);
  background: linear-gradient(135deg, var(--v2-primary) 0%, #7B8FF7 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
}

/* -- 导航区域（占满中间空间） -- */
.sidebar-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

/* -- 侧栏项 -- */
.sidebar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: var(--v2-radius);
  cursor: pointer;
  color: var(--v2-text-muted);
  transition: all 0.15s;
  gap: 2px;
}

.sidebar-item:hover {
  background: var(--v2-bg);
  color: var(--v2-text-secondary);
}

.sidebar-item.active {
  background: var(--v2-primary-light);
  color: var(--v2-primary);
}

.sidebar-item-icon {
  font-size: 20px;
}

.sidebar-item-label {
  font-size: 10px;
  line-height: 1;
  white-space: nowrap;
}

/* -- 底部用户区域 -- */
.sidebar-user {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 0;
  cursor: pointer;
  transition: opacity 0.15s;
}

.sidebar-user:hover {
  opacity: 0.8;
}

.sidebar-avatar {
  background: var(--v2-primary);
  color: #fff;
  font-size: 14px;
}

.sidebar-user-name {
  font-size: 10px;
  color: var(--v2-text-muted);
  max-width: 60px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
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
