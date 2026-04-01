import axios from 'axios'
import type { AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios'

const axiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
})

// 请求拦截器：附加 JWT token
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器：解包信封 + 401 处理
axiosInstance.interceptors.response.use(
  (response) => {
    const data = response.data
    // 标准信封格式：{ code, message, data }
    if (data && typeof data === 'object' && 'code' in data) {
      if (data.code === 200) {
        return { ...response, data: data.data }
      }
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    // 非标准响应直接返回
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      window.location.href = '/login'
    }

    const message = extractErrorMessage(error)
    return Promise.reject(new Error(message))
  },
)

function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data
    if (typeof data === 'string') return data
    if (data?.detail) {
      if (typeof data.detail === 'string') return data.detail
      if (Array.isArray(data.detail)) {
        return data.detail
          .map((item: { msg?: string; loc?: string[] }) => {
            const field = item.loc?.slice(-1)[0] || ''
            return field ? `${field}: ${item.msg}` : (item.msg || '')
          })
          .filter(Boolean)
          .join('；')
      }
    }
    if (data?.message) return data.message
    return error.message || '网络请求失败'
  }
  if (error instanceof Error) return error.message
  return '未知错误'
}

type UnwrapStandardResponse<T> = T extends { data?: infer D } ? D : T

function normalizeGeneratedUrl(url?: string): string | undefined {
  if (!url) {
    return url
  }
  // 兼容已生成的旧代码；新生成代码会在 Orval transformer 阶段去掉 /api/v1。
  if (url.startsWith('/api/v1/')) {
    return url.slice('/api/v1'.length)
  }
  return url
}

/**
 * Orval mutator：所有生成的 API 函数都会调用此函数
 */
export const customInstance = <T>(config: AxiosRequestConfig): Promise<UnwrapStandardResponse<T>> => {
  const source = axios.CancelToken.source()
  const promise = axiosInstance({
    ...config,
    url: normalizeGeneratedUrl(config.url),
    cancelToken: source.token,
  }).then(({ data }) => data as UnwrapStandardResponse<T>)

  // @ts-expect-error attach cancel method
  promise.cancel = () => source.cancel('Query was cancelled')

  return promise
}

export default axiosInstance
