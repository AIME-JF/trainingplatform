<template>
  <a-layout class="main-layout" :class="{ immersive: isImmersiveRoute }">
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

      <!-- 标签页栏 -->
      <div v-if="!isImmersiveRoute && !isMobile" class="tab-bar" @click="hideTabMenu">
        <div class="tab-bar-inner">
          <div
            v-for="tab in tabList"
            :key="tab.path"
            class="tab-item"
            :class="{ active: tab.path === currentTabPath }"
            @click="goTab(tab)"
            @contextmenu.prevent="showTabMenu($event, tab)"
          >
            <span v-if="tab.path === currentTabPath" class="tab-dot"></span>
            <span class="tab-label">{{ tab.title }}</span>
            <close-outlined
              v-if="tab.closable"
              class="tab-close"
              @click.stop="closeTab(tab)"
            />
          </div>
        </div>
      </div>

      <!-- 标签页右键菜单 -->
      <teleport to="body">
        <div
          v-if="tabMenu.visible"
          class="tab-context-menu"
          :style="{ top: tabMenu.y + 'px', left: tabMenu.x + 'px' }"
          @click.stop
        >
          <div
            class="tab-ctx-item"
            :class="{ disabled: !tabMenu.tab?.closable }"
            @click="ctxClose"
          >
            <close-outlined class="tab-ctx-icon" /> 关闭
          </div>
          <div class="tab-ctx-divider"></div>
          <div class="tab-ctx-item" @click="ctxCloseOthers">
            <minus-outlined class="tab-ctx-icon" /> 关闭其他
          </div>
          <div class="tab-ctx-item" @click="ctxCloseAll">
            <close-circle-outlined class="tab-ctx-icon" /> 关闭全部
          </div>
        </div>
      </teleport>

      <!-- 内容区 -->
      <a-layout-content class="content-area" :class="{ 'immersive-content': isImmersiveRoute, 'with-tabbar': !isImmersiveRoute && !isMobile }">
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
  CloseOutlined, MinusOutlined, CloseCircleOutlined,
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

const isImmersiveRoute = computed(() => route.meta?.immersive === true)

// ── 多标签页 ──────────────────────────────────────────
const tabList = ref([{ path: '/', title: '首页', closable: false }])

// 当前激活的标签路径：对 detail 子路由做归一化
const currentTabPath = computed(() => {
  const p = route.path
  if (tabList.value.find(t => t.path === p)) return p
  const matched = tabList.value
    .filter(t => t.path !== '/' && p.startsWith(t.path + '/'))
    .sort((a, b) => b.path.length - a.path.length)
  return matched[0]?.path ?? p
})

watch(
  () => route.path,
  (path) => {
    if (isImmersiveRoute.value) return
    const title = route.meta?.title
    if (!title || path === '/login') return
    const exists = tabList.value.find(t => t.path === path)
    if (!exists) {
      tabList.value.push({ path, title, closable: true })
    }
  },
  { immediate: true },
)

function goTab(tab) {
  router.push(tab.path)
}

function closeTab(tab) {
  const idx = tabList.value.findIndex(t => t.path === tab.path)
  if (idx === -1) return
  tabList.value.splice(idx, 1)
  if (currentTabPath.value === tab.path) {
    const next = tabList.value[Math.min(idx, tabList.value.length - 1)]
    if (next) router.push(next.path)
  }
}

// ── 右键菜单 ──────────────────────────────────────────
const tabMenu = ref({ visible: false, x: 0, y: 0, tab: null })

function showTabMenu(e, tab) {
  tabMenu.value = { visible: true, x: e.clientX, y: e.clientY, tab }
}

function hideTabMenu() {
  tabMenu.value.visible = false
}

function ctxClose() {
  if (tabMenu.value.tab?.closable) closeTab(tabMenu.value.tab)
  hideTabMenu()
}

function ctxCloseOthers() {
  const keep = tabMenu.value.tab
  tabList.value = tabList.value.filter(t => !t.closable || t.path === keep?.path)
  if (keep) router.push(keep.path)
  hideTabMenu()
}

function ctxCloseAll() {
  tabList.value = tabList.value.filter(t => !t.closable)
  router.push('/')
  hideTabMenu()
}

onMounted(() => document.addEventListener('click', hideTabMenu))
onUnmounted(() => document.removeEventListener('click', hideTabMenu))
// ─────────────────────────────────────────────────────
const desktopSidebarWidth = computed(() => {
  if (isMobile.value) {
    return 0
  }
  return collapsed.value ? COLLAPSED_SIDEBAR_WIDTH : SIDEBAR_WIDTH
})
const mainShellStyle = computed(() => {
  if (isImmersiveRoute.value) {
    return { marginLeft: '0', width: '100%' }
  }
  return {
    marginLeft: `${desktopSidebarWidth.value}px`,
    width: `calc(100% - ${desktopSidebarWidth.value}px)`,
  }
})

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
    '/question/repository',
    '/paper/repository',
    '/exam/manage',
  ]
  return preferredRoutes.find((item) => visibleMenuKeys.value.includes(item)) || ''
})

function getSelectedMenuKeyByPath(path) {
  if (path === '/') return '/'
  if (path.startsWith('/courses')) return '/courses'
  if (path.startsWith('/library')) return '/library'
  if (path.startsWith('/resource/detail')) return '/resource/library'
  if (path.startsWith('/resource/uploads')) return '/resource/library'
  if (path.startsWith('/exam/do')) return '/exam/manage'
  if (path.startsWith('/exam/result')) return '/exam/manage'
  if (path.startsWith('/exam/list')) return '/exam/manage'
  if (path.startsWith('/exam/manage')) return '/exam/manage'
  if (path.startsWith('/exam/scores')) return '/exam/manage'
  if (path.startsWith('/question/repository')) return '/question/repository'
  if (path.startsWith('/question/ai')) return '/question/repository'
  if (path.startsWith('/paper/ai-assemble')) return '/paper/repository'
  if (path.startsWith('/paper/repository')) return '/paper/repository'
  if (path.startsWith('/training/base')) return '/training/base'
  if (path.startsWith('/training/schedule')) return '/training/schedule'
  if (path.startsWith('/training/board')) return '/training/board'
  if (path.startsWith('/training')) return '/training'
  if (path.startsWith('/resource/my')) return '/resource/my'
  if (path.startsWith('/resource/assistant')) return '/resource/assistant'
  if (path.startsWith('/resource/recommend')) return '/resource/assistant'
  if (path.startsWith('/resource/library')) return '/resource/library'
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
  if (path.startsWith('/library')) return ['learn']
  if (path.startsWith('/resource/my')) return ['community']
  if (path.startsWith('/resource/assistant')) return ['community']
  if (path.startsWith('/resource/recommend')) return ['community']
  if (path.startsWith('/resource/library')) return ['community']
  if (path.startsWith('/resource/uploads')) return ['community']
  if (path.startsWith('/resource/detail')) return ['community']
  if (path.startsWith('/resource/teaching-generate')) return ['learn']
  if (path.startsWith('/resource/ai-generate')) return ['learn']
  if (path.startsWith('/resource/manage')) return ['manage']
  if (path.startsWith('/resource/review')) return ['review']
  if (path.startsWith('/resource/policy')) return ['review']
  if (path.startsWith('/resource/')) return ['community']
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
  // 跳过父菜单，它们没有 '/' 前缀
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

/* 标签页栏 */
.tab-bar {
  background: #fff;
  border-bottom: 1px solid #e8eaf0;
  box-shadow: 0 1px 3px rgba(0, 48, 135, 0.06);
  flex-shrink: 0;
  overflow: hidden;
  z-index: 90;
}

.tab-bar-inner {
  display: flex;
  align-items: stretch;
  height: 38px;
  padding: 0 8px;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: none;
  gap: 4px;
}

.tab-bar-inner::-webkit-scrollbar {
  display: none;
}

.tab-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0 12px;
  height: 28px;
  margin-top: 5px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  background: #f0f2f5;
  color: #595959;
  transition: background 0.15s, color 0.15s;
  flex-shrink: 0;
  user-select: none;
}

.tab-item:hover {
  background: #e6eaf5;
  color: var(--police-primary, #003087);
}

.tab-item.active {
  background: var(--police-primary, #003087);
  color: #fff;
}

.tab-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.85);
  flex-shrink: 0;
}

.tab-label {
  line-height: 1;
}

.tab-close {
  font-size: 10px;
  color: inherit;
  opacity: 0.7;
  border-radius: 50%;
  padding: 2px;
  transition: opacity 0.15s, background 0.15s;
}

.tab-close:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.12);
}

.tab-item.active .tab-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 右键菜单 */
.tab-context-menu {
  position: fixed;
  z-index: 9999;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.14);
  padding: 4px 0;
  min-width: 130px;
  user-select: none;
}

.tab-ctx-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  font-size: 13px;
  color: #333;
  cursor: pointer;
  transition: background 0.15s;
}

.tab-ctx-item:hover {
  background: #f0f4ff;
  color: var(--police-primary, #003087);
}

.tab-ctx-item.disabled {
  color: #bbb;
  cursor: not-allowed;
}

.tab-ctx-item.disabled:hover {
  background: transparent;
  color: #bbb;
}

.tab-ctx-icon {
  font-size: 12px;
}

.tab-ctx-divider {
  height: 1px;
  background: #f0f0f0;
  margin: 4px 0;
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

.content-area.with-tabbar {
  height: calc(var(--app-vh, 1vh) * 100 - 64px - 38px);
}

.content-area.immersive-content {
  padding: 0;
  background: #F8FAFC;
  height: calc(var(--app-vh, 1vh) * 100);
  min-height: calc(var(--app-vh, 1vh) * 100);
  overflow-y: auto;
  overflow-x: hidden;
}

/* 沉浸模式：隐藏侧边栏和顶栏 */
.main-layout.immersive .sidebar {
  display: none;
}
.main-layout.immersive .topbar {
  display: none;
}
.main-layout.immersive .main-shell {
  margin-left: 0 !important;
  width: 100% !important;
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
