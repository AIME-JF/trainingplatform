import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, loginByPhone as apiLoginByPhone, getCurrentUser } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const currentUser = ref(null)

  const isLoggedIn = computed(() => !!currentUser.value)
  const role = computed(() => currentUser.value?.role || null)
  const isAdmin = computed(() => role.value === 'admin')
  const isInstructor = computed(() => role.value === 'instructor')
  const isStudent = computed(() => role.value === 'student')

  function setUserFromResponse(user) {
    // Map backend user fields to frontend expected shape
    const mapped = {
      ...user,
      name: user.nickname || user.name || user.username,
      role: user.roles?.[0]?.code || user.role || 'student',
      policeId: user.policeId || user.police_id,
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

  function switchRole(roleKey) {
    // For dev/demo convenience: update role in current user
    if (currentUser.value) {
      currentUser.value = { ...currentUser.value, role: roleKey }
      localStorage.setItem('userInfo', JSON.stringify(currentUser.value))
    }
  }

  return { currentUser, isLoggedIn, role, isAdmin, isInstructor, isStudent, loginWithCredentials, loginWithPhone, logout, restoreFromStorage, switchRole }
})
