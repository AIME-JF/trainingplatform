import { customInstance } from '@/api/custom-instance'

export interface NoticeItem {
  id: number
  title: string
  content: string
  type: string
  training_id?: number | null
  author_id?: number | null
  author_name?: string | null
  target_user_id?: number | null
  reminder_type?: string | null
  is_read: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface NoticeUnreadCount {
  total: number
  reminder: number
  system: number
}

interface PaginatedResponse<T> {
  page: number
  size: number
  total: number
  items: T[]
}

export function getMyNotifications(params: { page?: number; size?: number; tab?: string }) {
  return customInstance<PaginatedResponse<NoticeItem>>({
    url: '/notices/my',
    method: 'GET',
    params,
  })
}

export function getUnreadCount() {
  return customInstance<NoticeUnreadCount>({
    url: '/notices/unread-count',
    method: 'GET',
  })
}

export function markAsRead(noticeId: number) {
  return customInstance<void>({
    url: `/notices/${noticeId}/read`,
    method: 'POST',
  })
}

export function markAllAsRead(tab?: string) {
  return customInstance<void>({
    url: '/notices/read-all',
    method: 'POST',
    params: tab ? { tab } : undefined,
  })
}
