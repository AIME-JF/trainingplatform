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

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  permissions: {
    type: [String, Array],
    default: undefined,
  },
  mode: {
    type: String,
    default: 'all',
  },
  allowed: {
    type: Boolean,
    default: undefined,
  },
  tips: {
    type: String,
    default: '您没有权限执行该操作',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  block: {
    type: Boolean,
    default: false,
  },
})

const authStore = useAuthStore()

const normalizedPermissions = computed(() => {
  if (Array.isArray(props.permissions)) {
    return props.permissions.filter(Boolean)
  }
  return props.permissions ? [props.permissions] : []
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
