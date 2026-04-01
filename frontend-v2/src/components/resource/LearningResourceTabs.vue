<template>
  <div class="resource-tabs">
    <button
      v-for="tab in visibleTabs"
      :key="tab.path"
      type="button"
      class="resource-tab"
      :class="{ active: isActive(tab.path) }"
      @click="router.push(tab.path)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  COURSE_PERMISSIONS,
  MY_RESOURCE_PERMISSIONS,
  TEACHING_RESOURCE_GENERATION_PERMISSIONS,
} from '@/constants/permissions'

interface TabItem {
  path: string
  label: string
  permissions?: string[]
}

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const tabs: TabItem[] = [
  { path: '/resource/courses', label: '课程资源', permissions: COURSE_PERMISSIONS },
  { path: '/resource/library', label: '资源库' },
  { path: '/resource/community', label: '资源社区' },
  { path: '/resource/my', label: '我的资源', permissions: MY_RESOURCE_PERMISSIONS },
  { path: '/resource/teaching-generate', label: '教学资源生成', permissions: TEACHING_RESOURCE_GENERATION_PERMISSIONS },
]

const visibleTabs = computed(() => tabs.filter((tab) => authStore.hasAnyPermission(tab.permissions || [])))

function isActive(path: string) {
  if (path === '/resource/courses') {
    return route.path.startsWith('/resource/courses')
  }
  return route.path === path
}
</script>

<style scoped>
.resource-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-bottom: 26px;
}

.resource-tab {
  position: relative;
  border: none;
  background: rgba(255, 255, 255, 0.42);
  color: var(--v2-text-secondary);
  border-radius: 0;
  min-height: 52px;
  padding: 14px 28px;
  font-size: 17px;
  font-weight: 600;
  cursor: pointer;
  overflow: hidden;
  transition:
    color 0.2s ease,
    background 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.resource-tab::before,
.resource-tab::after {
  content: '';
  position: absolute;
  top: 8%;
  bottom: 8%;
  width: 3px;
  border-radius: 0;
  background: linear-gradient(180deg, rgba(75, 110, 245, 0), rgba(75, 110, 245, 0.98), rgba(75, 110, 245, 0));
  opacity: 0;
  box-shadow: 0 0 12px rgba(75, 110, 245, 0.28);
  transition: opacity 0.2s ease;
}

.resource-tab::before {
  left: 0;
}

.resource-tab::after {
  right: 0;
}

.resource-tab:hover {
  color: var(--v2-primary);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(242, 246, 255, 0.9));
  box-shadow: 0 14px 30px rgba(75, 110, 245, 0.12);
  transform: translateY(-1px);
}

.resource-tab:hover::before,
.resource-tab:hover::after {
  opacity: 1;
}

.resource-tab.active {
  color: var(--v2-primary);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(238, 243, 255, 0.95));
  box-shadow:
    inset 0 0 0 1px rgba(75, 110, 245, 0.08),
    0 16px 34px rgba(75, 110, 245, 0.14);
}

.resource-tab.active::before,
.resource-tab.active::after {
  opacity: 1;
}

@media (max-width: 768px) {
  .resource-tab {
    min-height: 46px;
    padding: 12px 22px;
    font-size: 15px;
  }
}
</style>
