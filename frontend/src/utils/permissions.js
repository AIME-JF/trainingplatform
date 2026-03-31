import { useAuthStore } from '@/stores/auth'

function getAuthStore() {
  return useAuthStore()
}

export function hasPermission(permission) {
  return getAuthStore().hasPermission(permission)
}

export function hasAnyPermission(permissionList) {
  return getAuthStore().hasAnyPermission(permissionList)
}

export function hasAllPermissions(permissionList) {
  return getAuthStore().hasAllPermissions(permissionList)
}
