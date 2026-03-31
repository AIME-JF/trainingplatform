<template>
  <div class="dashboard">
    <a-card>
      <a-result
        status="success"
        :title="`欢迎回来，${authStore.currentUser?.name || '用户'}`"
        :sub-title="`角色：${roleLabel} | 权限数：${authStore.permissions.length}`"
      >
        <template #extra>
          <a-space>
            <a-tag color="blue">{{ authStore.role }}</a-tag>
            <a-tag v-if="authStore.currentUser?.unit" color="gold">{{ authStore.currentUser.unit }}</a-tag>
          </a-space>
        </template>
      </a-result>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const roleLabel = computed(() => {
  if (authStore.isInstructor) return '教官'
  if (authStore.isStudent) return '学员'
  return authStore.role
})
</script>

<style scoped>
.dashboard {
  max-width: 800px;
  margin: 0 auto;
}
</style>
