import request from './request'

export function getProfile() {
  return request.get('/profile')
}

export function updateProfile(data) {
  return request.put('/profile', data)
}

export function getStudyStats() {
  return request.get('/profile/study-stats')
}

export function getExamHistory() {
  return request.get('/profile/exam-history')
}
