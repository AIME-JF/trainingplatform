import { customInstance } from './custom-instance'

export function getUnifiedExams(params?: Record<string, unknown>) {
  return customInstance<any>({
    url: '/exams',
    method: 'GET',
    params,
  })
}

export function createUnifiedExam(data: Record<string, unknown>) {
  return customInstance<any>({
    url: '/exams',
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    data,
  })
}

export function getExamDashboard(params?: Record<string, unknown>) {
  return customInstance<any>({
    url: '/exams/dashboard',
    method: 'GET',
    params,
  })
}
