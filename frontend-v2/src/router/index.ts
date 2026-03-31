import { createRouter, createWebHistory } from 'vue-router'
import { routes } from './routes'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    anyPermissions?: string[]
    allPermissions?: string[]
    roles?: string[]
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 智慧教育训练平台`
  }

  const token = localStorage.getItem('token')

  // 需要认证但没有 token → 跳登录
  const requiresAuth = to.matched.some((r) => r.meta.requiresAuth)
  if (requiresAuth && !token) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  // 已登录访问登录页 → 跳首页
  if (to.path === '/login' && token) {
    return next('/')
  }

  // 从 localStorage 读缓存用户信息做同步权限校验
  let cachedUser: { permissions?: string[]; role?: string; role_codes?: string[] } | null = null
  try {
    const raw = localStorage.getItem('userInfo')
    if (raw) cachedUser = JSON.parse(raw)
  } catch {
    // ignore
  }

  if (cachedUser && requiresAuth) {
    const userPermissions = cachedUser.permissions || []
    const userRole = cachedUser.role || ''
    const userRoleCodes = cachedUser.role_codes || []

    // anyPermissions 检查
    if (to.meta.anyPermissions?.length) {
      const hasAny = to.meta.anyPermissions.some((p) => userPermissions.includes(p))
      if (!hasAny) return next('/')
    }

    // allPermissions 检查
    if (to.meta.allPermissions?.length) {
      const hasAll = to.meta.allPermissions.every((p) => userPermissions.includes(p))
      if (!hasAll) return next('/')
    }

    // roles 检查
    if (to.meta.roles?.length) {
      const matched = to.meta.roles.some(
        (r) => r === userRole || userRoleCodes.includes(r),
      )
      if (!matched) return next('/')
    }
  }

  next()
})

export default router
