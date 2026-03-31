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
  RESOURCE_LIBRARY_PERMISSIONS,
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
  { path: '/resource/library', label: '资源库', permissions: RESOURCE_LIBRARY_PERMISSIONS },
  { path: '/resource/recommend', label: '资源推荐', permissions: RESOURCE_LIBRARY_PERMISSIONS },
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
  gap: 10px;
  margin-bottom: 20px;
}

.resource-tab {
  border: 1px solid var(--v2-border);
  background: var(--v2-bg-card);
  color: var(--v2-text-secondary);
  border-radius: var(--v2-radius-full);
  padding: 8px 18px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.resource-tab:hover {
  border-color: var(--v2-primary);
  color: var(--v2-primary);
}

.resource-tab.active {
  border-color: var(--v2-primary);
  background: var(--v2-primary);
  color: #fff;
}
</style>
