<template>
  <a-layout class="main-layout">
    <!-- 侧边栏 -->
    <a-layout-sider
      v-model:collapsed="collapsed"
      :trigger="null"
      collapsible
      :width="SIDEBAR_WIDTH"
      :collapsed-width="COLLAPSED_SIDEBAR_WIDTH"
      class="sidebar"
    >
      <!-- Logo区域 -->
      <div class="sidebar-logo">
        <img src="../assets/logo.png" class="logo-icon" alt="Logo" />
        <span v-if="!collapsed" class="logo-text">智慧教育训练平台</span>
      </div>

      <!-- 菜单 -->
      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        mode="inline"
        :inline-collapsed="collapsed"
        class="sidebar-menu"
        @click="handleMenuClick"
      >
        <template v-for="item in visibleMenuItems" :key="item.key">
          <a-sub-menu v-if="item.children?.length" :key="item.key">
            <template #icon><component :is="item.icon" /></template>
            <template #title>{{ item.label }}</template>
            <a-menu-item v-for="child in item.children" :key="child.key">
              {{ child.label }}
            </a-menu-item>
          </a-sub-menu>
          <a-menu-item v-else :key="item.key">
            <template #icon><component :is="item.icon" /></template>
            {{ item.label }}
          </a-menu-item>
        </template>
      </a-menu>
    </a-layout-sider>

    <!-- 移动端抽屉菜单 -->
    <a-drawer
      v-model:open="mobileDrawerOpen"
      placement="left"
      :width="220"
      :closable="false"
      :bodyStyle="{ padding: 0, background: 'var(--police-sidebar-bg)' }"
      :headerStyle="{ display: 'none' }"
    >
      <div class="sidebar-logo" style="border-bottom: 1px solid rgba(255,255,255,0.1);">
        <img src="../assets/logo.png" class="logo-icon" alt="Logo" />
        <span class="logo-text">智慧教育训练平台</span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        mode="inline"
        class="sidebar-menu"
        @click="handleDrawerMenuClick"
      >
        <template v-for="item in visibleMenuItems" :key="item.key">
          <a-sub-menu v-if="item.children?.length" :key="item.key">
            <template #icon><component :is="item.icon" /></template>
            <template #title>{{ item.label }}</template>
            <a-menu-item v-for="child in item.children" :key="child.key">
              {{ child.label }}
            </a-menu-item>
          </a-sub-menu>
          <a-menu-item v-else :key="item.key">
            <template #icon><component :is="item.icon" /></template>
            {{ item.label }}
          </a-menu-item>
        </template>
      </a-menu>
    </a-drawer>

    <a-layout class="main-shell" :style="mainShellStyle">
      <!-- 顶部导航栏 -->
      <a-layout-header class="topbar">
        <div class="topbar-left">
          <!-- 移动端：打开抽屉；PC端：折叠侧边栏 -->
          <menu-unfold-outlined
            v-if="collapsed || isMobile"
            class="collapse-trigger"
            @click="isMobile ? (mobileDrawerOpen = true) : (collapsed = false)"
          />
          <menu-fold-outlined
            v-else
            class="collapse-trigger"
            @click="collapsed = true"
          />
          <span class="page-title">{{ currentPageTitle }}</span>
        </div>

        <div class="topbar-right">
          <!-- 用户信息 -->
          <a-dropdown :trigger="['click']">
            <div class="user-info">
              <a-avatar :size="32" :style="{ background: '#003087' }">
                {{ authStore.currentUser?.name?.charAt(0) }}
              </a-avatar>
              <span class="user-name">{{ authStore.currentUser?.name }}</span>
              <down-outlined class="user-arrow" />
            </div>
            <template #overlay>
              <div class="user-dropdown-menu">
                <div class="user-dropdown-item" @click="$router.push('/profile')">
                  <UserOutlined /> 个人中心
                </div>
                <div class="user-dropdown-divider"></div>
                <div class="user-dropdown-item danger" @click="handleLogout">
                  <LogoutOutlined /> 退出登录
                </div>
              </div>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <!-- 内容区 -->
      <a-layout-content class="content-area" :class="{ 'immersive-content': isImmersiveRoute }">
        <router-view v-if="isMounted" />
      </a-layout-content>
    </a-layout>

    <!-- 移动端底部导航栏 -->
    <nav class="mobile-bottom-nav">
      <a
        v-if="showDashboardNav"
        class="mobile-nav-item"
        :class="{ active: $route.path === '/' }"
        @click="$router.push('/')"
      >
        <span class="nav-icon"><HomeOutlined /></span>
        <span class="nav-label">首页</span>
      </a>
      <a
        v-if="primaryTrainingRoute"
        class="mobile-nav-item"
        :class="{ active: $route.path.startsWith('/training') }"
        @click="$router.push(primaryTrainingRoute)"
      >
        <span class="nav-icon"><TeamOutlined /></span>
        <span class="nav-label">培训</span>
      </a>
      <a
        v-if="primaryExamRoute"
        class="mobile-nav-item"
        :class="{ active: $route.path.startsWith('/exam') || $route.path.startsWith('/question') || $route.path.startsWith('/paper') }"
        @click="$router.push(primaryExamRoute)"
      >
        <span class="nav-icon"><FormOutlined /></span>
        <span class="nav-label">考试</span>
      </a>
      <a class="mobile-nav-item" :class="{ active: $route.path === '/profile' }" @click="$router.push('/profile')">
        <span class="nav-icon"><UserOutlined /></span>
        <span class="nav-label">我的</span>
      </a>
    </nav>
  </a-layout>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { appMenuConfig } from './menuConfig'
import {
  HomeOutlined, FormOutlined,
  TeamOutlined, UserOutlined,
  MenuUnfoldOutlined, MenuFoldOutlined, DownOutlined, LogoutOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const SIDEBAR_WIDTH = 220
const COLLAPSED_SIDEBAR_WIDTH = 80

const collapsed = ref(false)
const mobileDrawerOpen = ref(false)
const selectedKeys = ref([])
const openKeys = ref([])

// 检测是否为移动端
const isMobile = ref(window.innerWidth <= 768)
const isMounted = ref(false)

const isImmersiveRoute = computed(() => route.path.startsWith('/resource/recommend'))
const desktopSidebarWidth = computed(() => {
  if (isMobile.value) {
    return 0
  }
  return collapsed.value ? COLLAPSED_SIDEBAR_WIDTH : SIDEBAR_WIDTH
})
const mainShellStyle = computed(() => ({
  marginLeft: `${desktopSidebarWidth.value}px`,
  width: `calc(100% - ${desktopSidebarWidth.value}px)`,
}))

function updateAppVh() {
  const vh = window.innerHeight * 0.01
  document.documentElement.style.setProperty('--app-vh', `${vh}px`)
}

function onResize() {
  isMobile.value = window.innerWidth <= 768
  updateAppVh()
}

onMounted(() => {
  updateAppVh()
  window.addEventListener('resize', onResize)
  setTimeout(() => { isMounted.value = true }, 50)
})

onUnmounted(() => window.removeEventListener('resize', onResize))


const currentPageTitle = computed(() => {
  return route.meta?.title || '智慧教育训练平台'
})

function hasMenuAccess(item) {
  const anyPermissions = item.anyPermissions || []
  const allPermissions = item.allPermissions || []
  const roleList = Array.isArray(item.roles) ? item.roles.filter(Boolean) : []
  const currentRoleCodes = Array.isArray(authStore.currentUser?.roleCodes)
    ? authStore.currentUser.roleCodes
    : []
  const activeRoles = [authStore.currentUser?.role, ...currentRoleCodes].filter(Boolean)
  const roleAllowed = !roleList.length || roleList.some((role) => activeRoles.includes(role))
  return roleAllowed && authStore.hasAnyPermission(anyPermissions) && authStore.hasAllPermissions(allPermissions)
}

function filterMenuItems(items) {
  return items
    .map((item) => {
      if (item.children?.length) {
        const children = filterMenuItems(item.children)
        if (!children.length) return null
        return { ...item, children }
      }
      return hasMenuAccess(item) ? { ...item } : null
    })
    .filter(Boolean)
}

function flattenMenuKeys(items) {
  return items.flatMap((item) => item.children?.length ? flattenMenuKeys(item.children) : [item.key])
}

const visibleMenuItems = computed(() => filterMenuItems(appMenuConfig))
const visibleMenuKeys = computed(() => flattenMenuKeys(visibleMenuItems.value))
const showDashboardNav = computed(() => visibleMenuKeys.value.includes('/'))
const primaryTrainingRoute = computed(() => {
  const preferredRoutes = [
    '/training',
    '/training/base',
    '/training/schedule',
    '/training/board',
  ]
  return preferredRoutes.find((item) => visibleMenuKeys.value.includes(item)) || ''
})
const primaryExamRoute = computed(() => {
  const preferredRoutes = [
    '/exam/manage',
    '/exam/list',
    '/question/repository',
    '/paper/repository',
    '/question/ai',
    '/paper/ai-assemble',
  ]
  return preferredRoutes.find((item) => visibleMenuKeys.value.includes(item)) || ''
})

function getSelectedMenuKeyByPath(path) {
  if (path === '/') return '/'
  if (path.startsWith('/courses')) return '/courses'
  if (path.startsWith('/exam/list')) return '/exam/list'
  if (path.startsWith('/exam/manage')) return '/exam/manage'
  if (path.startsWith('/exam/scores')) return '/exam/manage'
  if (path.startsWith('/question/repository')) return '/question/repository'
  if (path.startsWith('/question/knowledge-points')) return '/question/knowledge-points'
  if (path.startsWith('/question/ai')) return '/question/ai'
  if (path.startsWith('/paper/repository')) return '/paper/repository'
  if (path.startsWith('/paper/ai-assemble')) return '/paper/ai-assemble'
  if (path.startsWith('/training/base')) return '/training/base'
  if (path.startsWith('/training/schedule')) return '/training/schedule'
  if (path.startsWith('/training/board')) return '/training/board'
  if (path.startsWith('/training')) return '/training'
  if (path.startsWith('/resource/library')) return '/resource/library'
  if (path.startsWith('/resource/recommend')) return '/resource/recommend'
  if (path.startsWith('/resource/my')) return '/resource/my'
  if (path.startsWith('/resource/teaching-generate')) return '/resource/teaching-generate'
  if (path.startsWith('/resource/ai-generate')) return '/resource/teaching-generate'
  if (path.startsWith('/resource/manage')) return '/resource/manage'
  if (path.startsWith('/resource/review')) return '/resource/review'
  if (path.startsWith('/resource/policy')) return '/resource/policy'
  if (path.startsWith('/trainee')) return '/trainee'
  if (path.startsWith('/instructor')) return '/instructor'
  if (path.startsWith('/talent')) return '/talent'
  if (path.startsWith('/certificate')) return '/certificate'
  if (path.startsWith('/report')) return '/report'
  if (path.startsWith('/system/users')) return '/system/users'
  if (path.startsWith('/system/roles')) return '/system/roles'
  if (path.startsWith('/system/departments')) return '/system/departments'
  if (path.startsWith('/system/dict')) return '/system/dict'
  if (path.startsWith('/system/dashboard-modules')) return '/system/dashboard-modules'
  if (path.startsWith('/system/configs')) return '/system/configs'
  if (path.startsWith('/profile')) return '/profile'
  return path
}

function getOpenKeysByPath(path) {
  if (path.startsWith('/courses')) return ['learn']
  if (path.startsWith('/resource/manage')) return ['manage']
  if (path.startsWith('/resource/review')) return ['review']
  if (path.startsWith('/resource/policy')) return ['review']
  if (path.startsWith('/resource/')) return ['learn']
  if (path.startsWith('/exam/') || path.startsWith('/question/') || path.startsWith('/paper/')) return ['exam']
  if (path.startsWith('/training/board')) return ['evaluate']
  if (path.startsWith('/training')) return ['train']
  if (path.startsWith('/report')) return ['evaluate']
  if (
    path.startsWith('/trainee')
    || path.startsWith('/instructor')
    || path.startsWith('/talent')
    || path.startsWith('/certificate')
  ) {
    return ['evaluate']
  }
  if (path.startsWith('/system/')) return ['manage']
  return []
}

const allSubMenuKeys = computed(() =>
  visibleMenuItems.value.filter((item) => item.children?.length).map((item) => item.key)
)

watch(
  () => route.path,
  (path) => {
    selectedKeys.value = [getSelectedMenuKeyByPath(path)]
    const pathKeys = getOpenKeysByPath(path)
    const merged = new Set([...allSubMenuKeys.value, ...pathKeys])
    openKeys.value = [...merged]
  },
  { immediate: true }
)

function handleMenuClick({ key }) {
  // 跳过父菜单（如"智能题库"），它们没有 '/' 前缀
  if (!key.startsWith('/')) {
    return
  }
  router.push(key)
}

function handleDrawerMenuClick({ key }) {
  router.push(key)
  mobileDrawerOpen.value = false
}


function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
  height: 100vh;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  background: var(--police-sidebar-bg) !important;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  position: fixed;
  inset: 0 auto 0 0;
  height: 100vh;
  z-index: 120;
  transition: width 0.2s ease;
}

.main-shell {
  min-width: 0;
  min-height: 100vh;
  height: 100vh;
  overflow: hidden;
  transition: margin-left 0.2s ease;
}

.sidebar-logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0 16px;
  overflow: hidden;
}

.logo-icon {
  height: 44px;
  width: auto;
  object-fit: contain;
  flex-shrink: 0;
}

.logo-text {
  color: white;
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
  letter-spacing: 0.5px;
}

.sidebar-menu {
  background: transparent !important;
  border: none !important;
  margin-top: 8px;
  height: calc(var(--app-vh, 1vh) * 100 - 72px);
  overflow-y: auto;
  overflow-x: hidden;
  -ms-overflow-style: none;
  scrollbar-width: none;
  padding-bottom: 8px;
}

.sidebar-menu::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

:deep(.ant-menu-item),
:deep(.ant-menu-submenu-title) {
  color: rgba(255, 255, 255, 0.75) !important;
}

:deep(.ant-menu-item:hover),
:deep(.ant-menu-submenu-title:hover) {
  background: var(--police-sidebar-item-hover) !important;
  color: white !important;
}

:deep(.ant-menu-item-selected) {
  background: var(--police-sidebar-item-active) !important;
  color: white !important;
}

:deep(.ant-menu-item-selected::after) {
  border-right-color: var(--police-gold) !important;
}

:deep(.ant-menu-sub) {
  background: rgba(0, 0, 0, 0.2) !important;
}

/* 顶部栏 */
.topbar {
  background: white !important;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 48, 135, 0.1);
  position: relative;
  z-index: 100;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-trigger {
  font-size: 18px;
  color: var(--police-text-secondary);
  cursor: pointer;
  transition: color 0.2s;
}

.collapse-trigger:hover {
  color: var(--police-primary);
}

.page-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--police-text-primary);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--police-radius);
  transition: background 0.2s;
}

.user-info:hover {
  background: var(--police-bg);
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--police-text-primary);
}

.user-arrow {
  font-size: 11px;
  color: var(--police-text-muted);
}

/* 内容区 */
.content-area {
  flex: 1;
  padding: 24px;
  background: var(--police-bg);
  min-height: 0;
  height: calc(var(--app-vh, 1vh) * 100 - 64px);
  overflow-y: auto;
  overflow-x: hidden;
}

.content-area.immersive-content {
  padding: 0;
  background: #000;
  height: calc(var(--app-vh, 1vh) * 100 - 64px);
  min-height: calc(var(--app-vh, 1vh) * 100 - 64px);
  overflow: hidden;
}

/* 用户下拉菜单 */
.user-dropdown-menu {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.12);
  padding: 4px 0;
  min-width: 140px;
}
.user-dropdown-item {
  padding: 9px 16px;
  font-size: 14px;
  cursor: pointer;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.15s;
}
.user-dropdown-item:hover { background: #f5f5f5; }
.user-dropdown-item.danger { color: #ff4d4f; }
.user-dropdown-divider { height: 1px; background: #f0f0f0; margin: 4px 0; }
</style>

<style>
@import '../assets/styles/mobile.css';
</style>
