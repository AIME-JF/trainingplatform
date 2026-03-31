<template>
  <a-tooltip :title="tooltipTitle">
    <span
      class="permission-tooltip-wrapper"
      :class="{ 'permission-tooltip-wrapper-block': block }"
    >
      <slot
        :disabled="mergedDisabled"
        :has-permission="hasAccess"
        :permission-denied="permissionDenied"
      />
    </span>
  </a-tooltip>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const props = withDefaults(defineProps<{
  permissions?: string | string[]
  mode?: 'all' | 'any'
  allowed?: boolean
  tips?: string
  disabled?: boolean
  block?: boolean
}>(), {
  permissions: undefined,
  mode: 'all',
  allowed: undefined,
  tips: '您没有权限执行该操作',
  disabled: false,
  block: false,
})

const authStore = useAuthStore()

const normalizedPermissions = computed(() => {
  if (Array.isArray(props.permissions)) {
    return props.permissions.filter(Boolean)
  }
  return props.permissions ? [props.permissions].filter(Boolean) : []
})

const hasAccess = computed(() => {
  if (typeof props.allowed === 'boolean') {
    return props.allowed
  }
  if (!normalizedPermissions.value.length) {
    return true
  }
  if (props.mode === 'any') {
    return authStore.hasAnyPermission(normalizedPermissions.value)
  }
  return authStore.hasAllPermissions(normalizedPermissions.value)
})

const permissionDenied = computed(() => !hasAccess.value)
const mergedDisabled = computed(() => props.disabled || permissionDenied.value)
const tooltipTitle = computed(() => (permissionDenied.value ? props.tips : ''))
</script>

<style scoped>
.permission-tooltip-wrapper {
  display: inline-flex;
  max-width: 100%;
}

.permission-tooltip-wrapper-block {
  display: flex;
  width: 100%;
}
</style>
