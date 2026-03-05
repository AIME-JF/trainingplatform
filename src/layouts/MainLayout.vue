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
        <div class="logo-icon">警</div>
        <span v-if="!collapsed" class="logo-text">警务训练平台</span>
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
          <a-menu-item key="/exam/bank">题库管理</a-menu-item>
          <a-menu-item key="/exam/scores">成绩管理</a-menu-item>
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
          <a-menu-item key="/training/schedule">周训练计划</a-menu-item>
          <a-menu-item key="/training/board" v-if="isAdmin">培训看板</a-menu-item>
        </a-sub-menu>

        <a-menu-item key="/instructor">
          <template #icon><UserOutlined /></template>
          教官库
        </a-menu-item>

        <a-menu-item key="/certificate">
          <template #icon><SafetyCertificateOutlined /></template>
          结业证书
        </a-menu-item>

        <a-menu-item key="/talent" v-if="isAdmin">
          <template #icon><StarOutlined /></template>
          人才库
        </a-menu-item>

        <a-menu-item key="/report" v-if="isAdmin">
          <template #icon><BarChartOutlined /></template>
          数据看板
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <!-- 顶部导航栏 -->
      <a-layout-header class="topbar">
        <div class="topbar-left">
          <menu-unfold-outlined
            v-if="collapsed"
            class="collapse-trigger"
            @click="collapsed = false"
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
          <a-dropdown>
            <div class="user-info">
              <a-avatar :size="32" :style="{ background: '#003087' }">
                {{ authStore.currentUser?.name?.charAt(0) }}
              </a-avatar>
              <span class="user-name">{{ authStore.currentUser?.name }}</span>
              <down-outlined class="user-arrow" />
            </div>
            <template #overlay>
              <a-menu>
                <a-menu-item key="profile" @click="$router.push('/profile')">
                  <UserOutlined /> 个人中心
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="logout" @click="handleLogout">
                  <LogoutOutlined /> 退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <!-- 内容区 -->
      <a-layout-content class="content-area">
        <router-view />
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
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import {
  HomeOutlined, PlayCircleOutlined, FormOutlined, RobotOutlined,
  TeamOutlined, UserOutlined, StarOutlined, BarChartOutlined,
  MenuUnfoldOutlined, MenuFoldOutlined, DownOutlined, LogoutOutlined,
  SafetyCertificateOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const collapsed = ref(false)
const selectedKeys = ref([route.path])
const openKeys = ref([])

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
  return route.meta?.title || '广西公安警务训练平台'
})

watch(
  () => route.path,
  (path) => {
    selectedKeys.value = [path]
  }
)

function handleMenuClick({ key }) {
  router.push(key)
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
  width: 36px;
  height: 36px;
  background: var(--police-gold);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--police-sidebar-bg);
  font-weight: 900;
  font-size: 18px;
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
  min-height: calc(100vh - 64px);
}
</style>

<style>
@import '../assets/styles/mobile.css';
</style>
