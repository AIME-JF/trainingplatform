export const COURSE_CATEGORIES = [
  { key: 'all', label: '全部课程' },
  { key: 'law', label: '法律法规' },
  { key: 'fraud', label: '专项业务' },
  { key: 'traffic', label: '交通管理' },
  { key: 'community', label: '基层警务' },
  { key: 'cybersec', label: '科技应用' },
  { key: 'physical', label: '体能技能' },
]

export const RESOURCE_SCOPE_LABELS: Record<string, string> = {
  all: '全部',
  user: '指定用户',
  department: '指定部门',
  role: '指定角色',
}

export const RESOURCE_STATUS_LABELS: Record<string, string> = {
  draft: '草稿',
  pending_review: '待审核',
  pendingReview: '待审核',
  reviewing: '审核中',
  published: '已发布',
  rejected: '已驳回',
  offline: '已下线',
  approved: '已通过',
  pending: '待处理',
  skipped: '已跳过',
  processing: '处理中',
  completed: '已完成',
  confirmed: '已确认',
  failed: '失败',
}

export const RESOURCE_STATUS_COLORS: Record<string, string> = {
  draft: 'default',
  pending_review: 'gold',
  pendingReview: 'gold',
  reviewing: 'blue',
  published: 'green',
  rejected: 'red',
  offline: 'orange',
  processing: 'processing',
  completed: 'blue',
  confirmed: 'green',
  failed: 'red',
}

export function formatDate(value?: string | null) {
  if (!value) {
    return '-'
  }
  return String(value).slice(0, 10)
}

export function formatDateTime(value?: string | null) {
  if (!value) {
    return '-'
  }
  return String(value).replace('T', ' ').slice(0, 16)
}

export function formatTagList(values?: Array<string | null | undefined> | null) {
  const normalized = (values || []).filter(Boolean) as string[]
  return normalized.length ? normalized.join('、') : '未设置'
}

export function getUserDisplayName(user?: {
  id: number
  nickname?: string | null
  username?: string | null
} | null, fallbackPrefix = '用户') {
  if (!user) {
    return '-'
  }
  return user.nickname || user.username || `${fallbackPrefix}#${user.id}`
}

export function getResourceContentTypeLabel(contentType?: string | null) {
  const map: Record<string, string> = {
    video: '视频',
    document: '文档',
    image: '图片',
    image_text: '图片',
    mixed: '混合',
  }
  return map[contentType || ''] || contentType || '-'
}

export function getResourceStatusLabel(status?: string | null) {
  return RESOURCE_STATUS_LABELS[status || ''] || status || '-'
}

export function getResourceStatusColor(status?: string | null) {
  return RESOURCE_STATUS_COLORS[status || ''] || 'default'
}

export function getScopeTypeLabel(scopeType?: string | null) {
  return RESOURCE_SCOPE_LABELS[scopeType || ''] || scopeType || '全部'
}

export function getCourseCategoryLabel(category?: string | null) {
  return COURSE_CATEGORIES.find((item) => item.key === category)?.label ?? category ?? '-'
}

export function getCourseFileTypeLabel(fileType?: string | null) {
  if (fileType === 'video') {
    return '视频型'
  }
  if (fileType === 'image') {
    return '图片型'
  }
  if (fileType === 'mixed') {
    return '混合型'
  }
  return '文档型'
}

export function getCourseFileTypeColor(fileType?: string | null) {
  if (fileType === 'video') {
    return 'purple'
  }
  if (fileType === 'image') {
    return 'green'
  }
  if (fileType === 'mixed') {
    return 'orange'
  }
  return 'cyan'
}

export function getDifficultyLabel(value?: number | null) {
  const labels = ['', '初级', '初中级', '中级', '中高级', '高级']
  return labels[Math.max(0, Math.min(5, Math.round(Number(value || 0))))] || ''
}

export function detectMediaKind(url?: string | null) {
  if (!url) {
    return 'unknown'
  }
  const cleanUrl = url.split('?')[0].split('#')[0].toLowerCase()
  if (cleanUrl.endsWith('.mp4')) {
    return 'video'
  }
  if (['.jpg', '.jpeg', '.png', '.webp', '.gif'].some((ext) => cleanUrl.endsWith(ext))) {
    return 'image'
  }
  if (['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.html', '.htm'].some((ext) => cleanUrl.endsWith(ext))) {
    return 'document'
  }
  return 'unknown'
}
