import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { MOCK_USERS } from '../mock/users.js'

export const useAuthStore = defineStore('auth', () => {
  const currentUser = ref(null)

  const isLoggedIn = computed(() => !!currentUser.value)
  const role = computed(() => currentUser.value?.role || null)
  const isAdmin = computed(() => role.value === 'admin')
  const isInstructor = computed(() => role.value === 'instructor')
  const isStudent = computed(() => role.value === 'student')

  function login(roleKey) {
    currentUser.value = MOCK_USERS[roleKey]
    localStorage.setItem('mockRole', roleKey)
    localStorage.setItem('mockUser', JSON.stringify(MOCK_USERS[roleKey]))
  }

  function logout() {
    currentUser.value = null
    localStorage.removeItem('mockRole')
    localStorage.removeItem('mockUser')
  }

  function restoreFromStorage() {
    const savedUser = localStorage.getItem('mockUser')
    if (savedUser) {
      try {
        currentUser.value = JSON.parse(savedUser)
      } catch {
        logout()
      }
    }
  }

  function loginWithCredentials(username, password) {
    const userEntry = Object.values(MOCK_USERS).find(u => u.username === username)
    if (!userEntry) return { success: false, error: '账号不存在' }
    if (userEntry.password !== password) return { success: false, error: '密码不正确' }
    currentUser.value = userEntry
    localStorage.setItem('mockRole', userEntry.role)
    localStorage.setItem('mockUser', JSON.stringify(userEntry))
    return { success: true }
  }

  function switchRole(roleKey) {
    login(roleKey)
  }

  // 手机号验证码登录：调用火山服务器 SMS API
  async function loginWithPhone(phone, code, roleKey) {
    const res = await fetch('http://118.145.115.139:3950/api/sms/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, code, role: roleKey }),
    })
    const data = await res.json()
    if (!data.success) return { success: false, error: data.message }
    currentUser.value = data.user
    localStorage.setItem('mockRole', data.user.role)
    localStorage.setItem('mockUser', JSON.stringify(data.user))
    return { success: true }
  }

  return { currentUser, isLoggedIn, role, isAdmin, isInstructor, isStudent, login, loginWithCredentials, loginWithPhone, logout, restoreFromStorage, switchRole }
})
