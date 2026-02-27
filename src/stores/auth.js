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

  function switchRole(roleKey) {
    login(roleKey)
  }

  return { currentUser, isLoggedIn, role, isAdmin, isInstructor, isStudent, login, logout, restoreFromStorage, switchRole }
})
