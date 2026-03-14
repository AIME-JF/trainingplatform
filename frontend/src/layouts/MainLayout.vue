<template>
  <a-layout class="main-layout">
    <!-- 侧边栏 -->
    <a-layout-sider
      v-model:collapsed="collapsed"
      :trigger="null"
      collapsible
      width="220"
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
        <a-menu-item key="/">
          <template #icon><HomeOutlined /></template>
          工作台
        </a-menu-item>

        <a-menu-item key="/courses">
          <template #icon><PlayCircleOutlined /></template>
          课程学习
        </a-menu-item>

        <a-sub-menu key="exam" v-if="!isStudent">
          <template #icon><FormOutlined /></template>
          <template #title>考试系统</template>
          <a-menu-item key="/exam/papers">试卷管理</a-menu-item>
          <a-menu-item key="/exam/manage">考试场次</a-menu-item>
          <a-menu-item key="/exam/bank">题库管理</a-menu-item>
          <a-menu-item key="/exam/scores">成绩统计</a-menu-item>
        </a-sub-menu>
        <a-menu-item key="/exam/list" v-else>
          <template #icon><FormOutlined /></template>
          参加考试
        </a-menu-item>

        <a-sub-menu key="ai" v-if="!isStudent">
          <template #icon><RobotOutlined /></template>
          <template #title>AI 功能</template>
          <a-menu-item key="/ai/question-gen">智能组卷</a-menu-item>
          <a-menu-item key="/ai/lesson-plan" v-if="isInstructor">教案生成</a-menu-item>
        </a-sub-menu>

        <a-sub-menu key="training">
          <template #icon><TeamOutlined /></template>
          <template #title>培训管理</template>
          <a-menu-item key="/training">培训班列表</a-menu-item>
          <a-menu-item key="/training/base" v-if="!isStudent">培训基地</a-menu-item>
          <a-menu-item key="/training/schedule">周训练计划</a-menu-item>
          <a-menu-item key="/training/board" v-if="isAdmin">培训看板</a-menu-item>
        </a-sub-menu>

        <a-sub-menu key="resource">
          <template #icon><BookOutlined /></template>
          <template #title>资源中心</template>
          <a-menu-item key="/resource/library">资源库</a-menu-item>
          <a-menu-item key="/resource/recommend">资源推荐</a-menu-item>
          <a-menu-item key="/resource/upload" v-if="!isStudent">上传资源</a-menu-item>
          <a-menu-item key="/resource/my" v-if="!isStudent">我的资源</a-menu-item>
          <a-menu-item key="/resource/manage" v-if="isAdmin">资源管理</a-menu-item>
          <a-menu-item key="/resource/review" v-if="!isStudent">审核工作台</a-menu-item>
          <a-menu-item key="/resource/policy" v-if="isAdmin">审核策略</a-menu-item>
        </a-sub-menu>

        <a-sub-menu key="archives">
          <template #icon><UserOutlined /></template>
          <template #title>人员档案</template>
          <a-menu-item key="/trainee">学员库</a-menu-item>
          <a-menu-item key="/instructor" v-if="!isStudent">教官库</a-menu-item>
          <a-menu-item key="/talent" v-if="isAdmin">人才库</a-menu-item>
          <a-menu-item key="/certificate">结业证书</a-menu-item>
        </a-sub-menu>

        <a-menu-item key="/report" v-if="isAdmin">
          <template #icon><BarChartOutlined /></template>
          数据看板
        </a-menu-item>

        <a-sub-menu key="system" v-if="isAdmin">
          <template #icon><SettingOutlined /></template>
          <template #title>系统管理</template>
          <a-menu-item key="/system/users">用户管理</a-menu-item>
          <a-menu-item key="/system/roles">角色管理</a-menu-item>
          <a-menu-item key="/system/departments">部门管理</a-menu-item>
        </a-sub-menu>
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
        <a-menu-item key="/">
          <template #icon><HomeOutlined /></template>
          工作台
        </a-menu-item>
        <a-menu-item key="/courses">
          <template #icon><PlayCircleOutlined /></template>
          课程学习
        </a-menu-item>
        <a-sub-menu key="exam" v-if="!isStudent">
          <template #icon><FormOutlined /></template>
          <template #title>考试系统</template>
          <a-menu-item key="/exam/papers">试卷管理</a-menu-item>
          <a-menu-item key="/exam/manage">考试场次</a-menu-item>
          <a-menu-item key="/exam/bank">题库管理</a-menu-item>
          <a-menu-item key="/exam/scores">成绩统计</a-menu-item>
        </a-sub-menu>
        <a-menu-item key="/exam/list" v-else>
          <template #icon><FormOutlined /></template>
          参加考试
        </a-menu-item>
        <a-sub-menu key="ai" v-if="!isStudent">
          <template #icon><RobotOutlined /></template>
          <template #title>AI 功能</template>
          <a-menu-item key="/ai/question-gen">智能组卷</a-menu-item>
          <a-menu-item key="/ai/lesson-plan" v-if="isInstructor">教案生成</a-menu-item>
        </a-sub-menu>
        <a-sub-menu key="training">
          <template #icon><TeamOutlined /></template>
          <template #title>培训管理</template>
          <a-menu-item key="/training">培训班列表</a-menu-item>
          <a-menu-item key="/training/base" v-if="!isStudent">培训基地</a-menu-item>
          <a-menu-item key="/training/schedule">周训练计划</a-menu-item>
          <a-menu-item key="/training/board" v-if="isAdmin">培训看板</a-menu-item>
        </a-sub-menu>
        <a-sub-menu key="resource">
          <template #icon><BookOutlined /></template>
          <template #title>资源中心</template>
          <a-menu-item key="/resource/library">资源库</a-menu-item>
          <a-menu-item key="/resource/recommend">资源推荐</a-menu-item>
          <a-menu-item key="/resource/upload" v-if="!isStudent">上传资源</a-menu-item>
          <a-menu-item key="/resource/my" v-if="!isStudent">我的资源</a-menu-item>
          <a-menu-item key="/resource/manage" v-if="isAdmin">资源管理</a-menu-item>
          <a-menu-item key="/resource/review" v-if="!isStudent">审核工作台</a-menu-item>
          <a-menu-item key="/resource/policy" v-if="isAdmin">审核策略</a-menu-item>
        </a-sub-menu>
        <a-sub-menu key="archives">
          <template #icon><UserOutlined /></template>
          <template #title>人员档案</template>
          <a-menu-item key="/trainee">学员库</a-menu-item>
          <a-menu-item key="/instructor" v-if="!isStudent">教官库</a-menu-item>
          <a-menu-item key="/talent" v-if="isAdmin">人才库</a-menu-item>
          <a-menu-item key="/certificate">结业证书</a-menu-item>
        </a-sub-menu>
        <a-menu-item key="/report" v-if="isAdmin">
          <template #icon><BarChartOutlined /></template>
          数据看板
        </a-menu-item>

        <a-sub-menu key="system" v-if="isAdmin">
          <template #icon><SettingOutlined /></template>
          <template #title>系统管理</template>
          <a-menu-item key="/system/users">用户管理</a-menu-item>
          <a-menu-item key="/system/roles">角色管理</a-menu-item>
          <a-menu-item key="/system/departments">部门管理</a-menu-item>
        </a-sub-menu>
      </a-menu>
    </a-drawer>

    <a-layout>
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
          <!-- 演示角色切换 -->
          <div class="demo-switcher">
            <span class="demo-label">演示角色：</span>
            <a-space>
              <a-tag
                v-for="r in roles"
                :key="r.key"
                :color="currentRole === r.key ? 'blue' : 'default'"
                class="role-tag"
                @click="switchRole(r.key)"
              >{{ r.label }}</a-tag>
            </a-space>
          </div>

          <a-divider type="vertical" />

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
      <a class="mobile-nav-item" :class="{ active: $route.path === '/' }" @click="$router.push('/')">
        <span class="nav-icon"><HomeOutlined /></span>
        <span class="nav-label">首页</span>
      </a>
      <a class="mobile-nav-item" :class="{ active: $route.path.startsWith('/courses') }" @click="$router.push('/courses')">
        <span class="nav-icon"><PlayCircleOutlined /></span>
        <span class="nav-label">课程</span>
      </a>
      <a class="mobile-nav-item" :class="{ active: $route.path.startsWith('/training') }" @click="$router.push('/training')">
        <span class="nav-icon"><TeamOutlined /></span>
        <span class="nav-label">培训</span>
      </a>
      <a class="mobile-nav-item" :class="{ active: $route.path.startsWith('/exam') }" @click="$router.push(isStudent ? '/exam/list' : '/exam/bank')">
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
import {
  HomeOutlined, PlayCircleOutlined, FormOutlined, RobotOutlined,
  TeamOutlined, UserOutlined, BarChartOutlined, BookOutlined,
  MenuUnfoldOutlined, MenuFoldOutlined, DownOutlined, LogoutOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const collapsed = ref(false)
const mobileDrawerOpen = ref(false)
const selectedKeys = ref([])
const openKeys = ref([])

// 检测是否为移动端
const isMobile = ref(window.innerWidth <= 768)
const isMounted = ref(false)

const isImmersiveRoute = computed(() => route.path.startsWith('/resource/recommend'))

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

const isStudent = computed(() => authStore.isStudent)
const isInstructor = computed(() => authStore.isInstructor)
const isAdmin = computed(() => authStore.isAdmin)
const currentRole = computed(() => authStore.role)

const roles = [
  { key: 'admin', label: '管理员' },
  { key: 'instructor', label: '教官' },
  { key: 'student', label: '学员' },
]

const currentPageTitle = computed(() => {
  return route.meta?.title || '智慧教育训练平台'
})

function getSelectedMenuKeyByPath(path) {
  if (path === '/') return '/'
  if (path.startsWith('/courses')) return '/courses'
  if (path.startsWith('/exam/list')) return '/exam/list'
  if (path.startsWith('/exam/papers')) return '/exam/papers'
  if (path.startsWith('/exam/manage')) return '/exam/manage'
  if (path.startsWith('/exam/bank')) return '/exam/bank'
  if (path.startsWith('/exam/scores')) return '/exam/scores'
  if (path.startsWith('/ai/question-gen')) return '/ai/question-gen'
  if (path.startsWith('/ai/lesson-plan')) return '/ai/lesson-plan'
  if (path.startsWith('/training/base')) return '/training/base'
  if (path.startsWith('/training/schedule')) return '/training/schedule'
  if (path.startsWith('/training/board')) return '/training/board'
  if (path.startsWith('/training')) return '/training'
  if (path.startsWith('/resource/library')) return '/resource/library'
  if (path.startsWith('/resource/recommend')) return '/resource/recommend'
  if (path.startsWith('/resource/upload')) return '/resource/upload'
  if (path.startsWith('/resource/my')) return '/resource/my'
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
  if (path.startsWith('/profile')) return '/profile'
  return path
}

function getOpenKeysByPath(path) {
  if (path.startsWith('/exam/')) return ['exam']
  if (path.startsWith('/ai/')) return ['ai']
  if (path.startsWith('/training')) return ['training']
  if (path.startsWith('/resource/')) return ['resource']
  if (
    path.startsWith('/trainee')
    || path.startsWith('/instructor')
    || path.startsWith('/talent')
    || path.startsWith('/certificate')
  ) {
    return ['archives']
  }
  if (path.startsWith('/system/')) return ['system']
  return []
}

watch(
  () => route.path,
  (path) => {
    selectedKeys.value = [getSelectedMenuKeyByPath(path)]
    openKeys.value = getOpenKeysByPath(path)
  },
  { immediate: true }
)

function handleMenuClick({ key }) {
  router.push(key)
}

function handleDrawerMenuClick({ key }) {
  router.push(key)
  mobileDrawerOpen.value = false
}

function switchRole(roleKey) {
  authStore.switchRole(roleKey)
  router.push('/')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
}

/* 侧边栏 */
.sidebar {
  background: var(--police-sidebar-bg) !important;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.2);
  overflow: hidden;
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
  position: sticky;
  top: 0;
  z-index: 100;
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

.demo-switcher {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f0f4ff;
  padding: 4px 12px;
  border-radius: 20px;
  border: 1px dashed #aabbdd;
}

.demo-label {
  font-size: 12px;
  color: var(--police-text-muted);
  white-space: nowrap;
}

.role-tag {
  cursor: pointer;
  font-size: 12px;
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
  padding: 24px;
  background: var(--police-bg);
  min-height: calc(var(--app-vh, 1vh) * 100 - 64px);
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
