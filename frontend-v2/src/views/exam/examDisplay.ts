import type { ExamResponse } from '@/api/generated/model'

export type ExamKind = 'training' | 'admission'

type ExamLike = Partial<Pick<ExamResponse, 'status' | 'can_join' | 'attempt_count' | 'max_attempts' | 'kind'>>

export function resolveExamKind(value?: unknown, fallback: ExamKind = 'training'): ExamKind {
  if (value === 'admission') {
    return 'admission'
  }
  if (value === 'training') {
    return 'training'
  }
  return fallback
}

export function normalizeExamStatus(status?: string | null): 'active' | 'upcoming' | 'ended' | 'unknown' {
  switch (status) {
    case 'active':
    case 'ongoing':
      return 'active'
    case 'upcoming':
      return 'upcoming'
    case 'ended':
    case 'finished':
      return 'ended'
    default:
      return 'unknown'
  }
}

export function getExamStatusClass(status?: string | null) {
  switch (normalizeExamStatus(status)) {
    case 'active':
      return 'status-ongoing'
    case 'upcoming':
      return 'status-upcoming'
    case 'ended':
      return 'status-finished'
    default:
      return ''
  }
}

export function getExamStatusText(exam?: ExamLike | null) {
  const normalizedStatus = normalizeExamStatus(exam?.status)
  if (normalizedStatus === 'upcoming') {
    return '即将开始'
  }
  if (normalizedStatus === 'ended') {
    return '已结束'
  }
  if (exam?.can_join) {
    return '进行中'
  }
  const attemptCount = Number(exam?.attempt_count || 0)
  const maxAttempts = Number(exam?.max_attempts || 1)
  if (attemptCount >= maxAttempts) {
    return '已达作答次数'
  }
  return '暂不可参加'
}

export function isExamEnded(status?: string | null) {
  return normalizeExamStatus(status) === 'ended'
}

export function isExamActive(status?: string | null) {
  return normalizeExamStatus(status) === 'active'
}
