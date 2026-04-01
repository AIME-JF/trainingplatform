import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axiosInstance from '@/api/custom-instance'

export interface UserInfo {
  id: number
  username: string
  nickname?: string
  name?: string
  role: string
  role_codes: string[]
  permissions: string[]
  phone?: string
  police_id?: string
  id_card_number?: string
  unit?: string
  department_id?: number
  police_type_id?: number
  study_hours?: number
  exam_count?: number
  avg_score?: number
  level?: string
}

export const useAuthStore = defineStore('auth', () => {
  const currentUser = ref<UserInfo | null>(null)

  // -- computed --
  const isLoggedIn = computed(() => !!currentUser.value)
  const role = computed(() => currentUser.value?.role || '')
  const permissions = computed(() => currentUser.value?.permissions || [])
  const isInstructor = computed(() => role.value === 'instructor')
  const isStudent = computed(() => role.value === 'student')
  const roleCodes = computed(() => currentUser.value?.role_codes || [])

  // -- methods --
  function hasPermission(code: string): boolean {
    return permissions.value.includes(code)
  }

  function hasAnyPermission(codes: string[]): boolean {
    if (!codes || codes.length === 0) return true
    return codes.some((code) => permissions.value.includes(code))
  }

  function hasAllPermissions(codes: string[]): boolean {
    if (!codes || codes.length === 0) return true
    return codes.every((code) => permissions.value.includes(code))
  }

  function mapUserData(user: Record<string, unknown>): UserInfo {
    const roles = (user.roles as Array<Record<string, unknown>>) || []
    const primaryRole = roles[0] || {}

    // 提取权限
    const permSet = new Set<string>()
    const directPerms = (user.permissions as Array<Record<string, string> | string>) || []
    for (const p of directPerms) {
      if (typeof p === 'string' && p.trim()) {
        permSet.add(p.trim())
        continue
      }
      if (p && typeof p === 'object' && 'code' in p && typeof p.code === 'string' && p.code.trim()) {
        permSet.add(p.code.trim())
      }
    }
    for (const r of roles) {
      const rolePerms = (r.permissions as Array<Record<string, string>>) || []
      for (const p of rolePerms) {
        if (p.code?.trim()) permSet.add(p.code.trim())
      }
    }

    return {
      id: user.id as number,
      username: (user.username as string) || '',
      nickname: (user.nickname as string) || undefined,
      name: (user.nickname || user.name || user.username) as string,
      role: (primaryRole.code as string) || (user.role as string) || '',
      role_codes: roles.map((r) => r.code as string).filter(Boolean),
      permissions: [...permSet].sort(),
      phone: (user.phone as string) || undefined,
      police_id: (user.police_id as string) || undefined,
      id_card_number: (user.id_card_number as string) || undefined,
      unit: ((user.departments as Array<Record<string, string>>)?.[0]?.name || user.unit) as string || undefined,
      department_id: user.department_id as number | undefined,
      police_type_id: user.police_type_id as number | undefined,
      study_hours: user.study_hours as number | undefined,
      exam_count: user.exam_count as number | undefined,
      avg_score: user.avg_score as number | undefined,
      level: user.level as string | undefined,
    }
  }

  async function loginWithCredentials(username: string, password: string) {
    const res = await axiosInstance.post('/auth/login', { username, password })
    const data = res.data as Record<string, unknown>
    const token = data.access_token as string
    const user = data.user as Record<string, unknown>

    localStorage.setItem('token', token)
    currentUser.value = mapUserData(user)
    localStorage.setItem('userInfo', JSON.stringify(currentUser.value))
  }

  async function restoreFromStorage() {
    const token = localStorage.getItem('token')
    if (!token) return

    try {
      const res = await axiosInstance.get('/auth/me')
      const user = res.data as Record<string, unknown>
      currentUser.value = mapUserData(user)
      localStorage.setItem('userInfo', JSON.stringify(currentUser.value))
    } catch {
      // 网络不可用时尝试从缓存恢复
      const cached = localStorage.getItem('userInfo')
      if (cached) {
        try {
          currentUser.value = JSON.parse(cached) as UserInfo
        } catch {
          logout()
        }
      }
    }
  }

  function logout() {
    currentUser.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  }

  return {
    currentUser,
    isLoggedIn,
    role,
    permissions,
    isInstructor,
    isStudent,
    roleCodes,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    loginWithCredentials,
    restoreFromStorage,
    logout,
  }
})
