import request from './request'

/**
 * 上传文件 (视频/文档)
 * @param {File} file - 原始 File 对象
 * @param {function} [onProgress] - 上传进度回调 (percent: number)
 * @returns {Promise<{id, filename, mimeType, size, url}>}
 */
export function uploadFile(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/media/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000, // 10 min for large videos
    onUploadProgress: onProgress
      ? (e) => { onProgress(Math.round((e.loaded / (e.total || 1)) * 100)) }
      : undefined,
  })
}

/**
 * 获取文件直链 URL
 * @param {number} fileId
 * @returns {string}
 */
export function getFileUrl(fileId) {
  const base = import.meta.env.VITE_API_BASE_URL
  return `${base}/media/files/${fileId}`
}
