import dayjs from 'dayjs'

export const reminderTypeLabelMap: Record<string, string> = {
  exam_reminder: '考试提醒',
  review_approved: '审核通过',
  review_rejected: '审核驳回',
  enrollment_approved: '报名通过',
  enrollment_rejected: '报名驳回',
  enrollment_pending: '报名待审批',
  training_notice: '培训通知',
}

export function getReminderTypeLabel(type?: string | null): string {
  if (!type) return ''
  return reminderTypeLabelMap[type] || type
}

export function formatNoticeTime(time?: string | null): string {
  if (!time) return ''

  const diff = Date.now() - new Date(time).getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}
