import axios from 'axios'
import router from '@/router'

// snake_case to camelCase recursive converter
function toCamelCase(str) {
  return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase())
}

function toSnakeCase(str) {
  return str.replace(/[A-Z]/g, (c) => '_' + c.toLowerCase())
}

function convertKeys(obj, converter) {
  if (Array.isArray(obj)) {
    return obj.map((item) => convertKeys(item, converter))
  }
  if (obj !== null && typeof obj === 'object' && !(obj instanceof Date)) {
    return Object.keys(obj).reduce((acc, key) => {
      acc[converter(key)] = convertKeys(obj[key], converter)
      return acc
    }, {})
  }
  return obj
}

function extractErrorMessage(payload) {
  if (!payload) {
    return ''
  }
  if (typeof payload === 'string') {
    return payload
  }
  if (Array.isArray(payload)) {
    return payload.map((item) => extractErrorMessage(item)).filter(Boolean).join('；')
  }
  if (typeof payload === 'object') {
    if (typeof payload.detail === 'string') {
      return payload.detail
    }
    if (Array.isArray(payload.detail)) {
      return extractErrorMessage(payload.detail)
    }
    if (typeof payload.message === 'string') {
      return payload.message
    }
    if (Array.isArray(payload.errors)) {
      return extractErrorMessage(payload.errors)
    }
    if (Array.isArray(payload.loc) && typeof payload.msg === 'string') {
      return `${payload.loc.join('.')}：${payload.msg}`
    }
  }
  return ''
}

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
})

// Request interceptor: attach JWT token & convert keys to snake_case
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // Convert request body keys to snake_case
  if (config.data && typeof config.data === 'object' && !(config.data instanceof FormData)) {
    config.data = convertKeys(config.data, toSnakeCase)
  }
  // Convert query params keys to snake_case
  if (config.params && typeof config.params === 'object') {
    config.params = convertKeys(config.params, toSnakeCase)
  }
  return config
})

// Response interceptor: unwrap { code, message, data } and convert keys to camelCase
request.interceptors.response.use(
  (response) => {
    if (response.config?.responseType === 'blob' || response.config?.responseType === 'arraybuffer') {
      return response.data
    }
    const res = response.data
    if (res instanceof Blob || res instanceof ArrayBuffer) {
      return res
    }
    // If response has the standard wrapper format
    if (res && typeof res === 'object' && 'code' in res) {
      if (res.code === 200) {
        return convertKeys(res.data, toCamelCase)
      }
      // Business error
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    // Non-standard response (e.g. direct data), still convert keys
    return convertKeys(res, toCamelCase)
  },
  (error) => {
    if (error.response) {
      const { status } = error.response
      if (status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
        router.push('/login')
      }
      const message = extractErrorMessage(error.response.data)
      if (message) {
        return Promise.reject(new Error(message))
      }
    }
    return Promise.reject(error)
  }
)

export default request
