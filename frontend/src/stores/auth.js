import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, loginByPhone as apiLoginByPhone, getCurrentUser } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const currentUser = ref(null)

  const isLoggedIn = computed(() => !!currentUser.value)
  const role = computed(() => currentUser.value?.role || null)
  const permissions = computed(() => currentUser.value?.permissions || [])
  const isAdmin = computed(() => role.value === 'admin')
  const isInstructor = computed(() => role.value === 'instructor')
  const isStudent = computed(() => role.value === 'student')

  function extractPermissionCodes(user) {
    const codeSet = new Set()
    for (const code of user?.permissions || []) {
      if (code) {
        codeSet.add(String(code).trim())
      }
    }
    for (const roleItem of user?.roles || []) {
      for (const permission of roleItem?.permissions || []) {
        if (permission?.code) {
          codeSet.add(String(permission.code).trim())
        }
      }
    }
    return Array.from(codeSet).sort()
  }

  function setUserFromResponse(user) {
    const permissionCodes = extractPermissionCodes(user)
    // Map backend user fields to frontend expected shape
    const mapped = {
      ...user,
      name: user.nickname || user.name || user.username,
      role: user.roles?.[0]?.code || user.role || 'student',
      roleCodes: (user.roles || []).map((item) => item.code).filter(Boolean),
      permissions: permissionCodes,
      policeId: user.policeId || user.police_id,
      idCardNumber: user.idCardNumber || user.id_card_number,
      unit: user.departments?.[0]?.name || user.unit || '',
      studyHours: user.studyHours ?? 0,
      examCount: user.examCount ?? 0,
      avgScore: user.avgScore ?? 0,
      level: user.level || '',
    }
    currentUser.value = mapped
    localStorage.setItem('userInfo', JSON.stringify(mapped))
  }

  async function loginWithCredentials(username, password) {
    try {
      const res = await apiLogin(username, password)
      const token = res.accessToken || res.access_token
      if (token) {
        localStorage.setItem('token', token)
      }
      setUserFromResponse(res.user || res)
      return { success: true }
    } catch (e) {
      return { success: false, error: e.message || '登录失败' }
    }
  }

  async function loginWithPhone(phone, code) {
    try {
      const res = await apiLoginByPhone(phone, code)
      const token = res.accessToken || res.access_token
      if (token) {
        localStorage.setItem('token', token)
      }
      setUserFromResponse(res.user || res)
      return { success: true }
    } catch (e) {
      return { success: false, error: e.message || '登录失败' }
    }
  }

  function logout() {
    currentUser.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  async function restoreFromStorage() {
    const token = localStorage.getItem('token')
    if (!token) return
    // Try to get fresh user info from server
    try {
      const user = await getCurrentUser()
      setUserFromResponse(user)
    } catch {
      // If server unavailable, fallback to cached user info
      const savedUser = localStorage.getItem('userInfo')
      if (savedUser) {
        try {
          currentUser.value = JSON.parse(savedUser)
        } catch {
          logout()
        }
      } else {
        logout()
      }
    }
  }

  function hasPermission(permission) {
    if (!permission) return true
    return permissions.value.includes(permission)
  }

  function hasAnyPermission(permissionList) {
    const list = Array.isArray(permissionList)
      ? permissionList.filter(Boolean)
      : [permissionList].filter(Boolean)
    if (!list.length) return true
    return list.some((permission) => hasPermission(permission))
  }

  function hasAllPermissions(permissionList) {
    const list = Array.isArray(permissionList)
      ? permissionList.filter(Boolean)
      : [permissionList].filter(Boolean)
    if (!list.length) return true
    return list.every((permission) => hasPermission(permission))
  }

  return {
    currentUser,
    isLoggedIn,
    role,
    permissions,
    isAdmin,
    isInstructor,
    isStudent,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    loginWithCredentials,
    loginWithPhone,
    logout,
    restoreFromStorage,
  }
})
