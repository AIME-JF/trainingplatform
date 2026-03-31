import request from './request'

export function submitResource(resourceId) {
  return request.post(`/resources/${resourceId}/submit`)
}

export function getReviewTasks(params) {
  return request.get('/reviews/tasks', { params })
}

export function approveReviewTask(taskId, data) {
  return request.post(`/reviews/tasks/${taskId}/approve`, data)
}

export function rejectReviewTask(taskId, data) {
  return request.post(`/reviews/tasks/${taskId}/reject`, data)
}

export function getReviewWorkflow(resourceId) {
  return request.get(`/reviews/workflows/${resourceId}`)
}

export function getReviewPolicies() {
  return request.get('/review-policies')
}

export function createReviewPolicy(data) {
  return request.post('/review-policies', data)
}

export function updateReviewPolicy(id, data) {
  return request.put(`/review-policies/${id}`, data)
}
