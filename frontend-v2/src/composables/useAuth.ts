import { useAuthStore } from '@/stores/auth'

export function useAuth() {
  const store = useAuthStore()
  return {
    currentUser: store.currentUser,
    isLoggedIn: store.isLoggedIn,
    role: store.role,
    isInstructor: store.isInstructor,
    isStudent: store.isStudent,
    hasPermission: store.hasPermission,
    hasAnyPermission: store.hasAnyPermission,
    hasAllPermissions: store.hasAllPermissions,
  }
}
