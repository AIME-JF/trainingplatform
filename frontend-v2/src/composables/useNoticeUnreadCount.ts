import { ref } from 'vue'
import type { NoticeUnreadCountResponse } from '@/api/generated/model'
import { getUnreadCountApiV1NoticesUnreadCountGet } from '@/api/generated/notice-management/notice-management'

export function useNoticeUnreadCount() {
  const notifyCount = ref(0)
  const unreadSummary = ref<NoticeUnreadCountResponse>({ total: 0, reminder: 0, system: 0 })

  async function refreshNotifyCount() {
    try {
      const data = await getUnreadCountApiV1NoticesUnreadCountGet()
      const safeData = data || { total: 0, reminder: 0, system: 0 }
      unreadSummary.value = safeData
      notifyCount.value = safeData.total ?? 0
      return safeData
    } catch {
      unreadSummary.value = { total: 0, reminder: 0, system: 0 }
      notifyCount.value = 0
      return unreadSummary.value
    }
  }

  return {
    notifyCount,
    unreadSummary,
    refreshNotifyCount,
  }
}
