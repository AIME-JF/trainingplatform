import request from './request'

// 资源审核提交（兼容旧接口）
export function submitResource(resourceId) {
  return request.post(`/resources/${resourceId}/submit`)
}

// 通用审核提交
export function submitReview(data) {
  return request.post('/reviews/submit', data)
}

// 审核任务列表
export function getReviewTasks(params) {
  return request.get('/reviews/tasks', { params })
}

export function approveReviewTask(taskId, data) {
  return request.post(`/reviews/tasks/${taskId}/approve`, data)
}

export function rejectReviewTask(taskId, data) {
  return request.post(`/reviews/tasks/${taskId}/reject`, data)
}

// 资源审核轨迹（兼容旧路由）
export function getReviewWorkflow(resourceId) {
  return request.get(`/reviews/workflows/${resourceId}`)
}

// 通用审核轨迹
export function getReviewWorkflowByBiz(businessType, businessId) {
  return request.get(`/reviews/workflows/${businessType}/${businessId}`)
}

// 策略管理
export function getReviewPolicies(params) {
  return request.get('/review-policies', { params })
}

export function createReviewPolicy(data) {
  return request.post('/review-policies', data)
}

export function updateReviewPolicy(id, data) {
  return request.put(`/review-policies/${id}`, data)
}

export function getReviewWorkflows(params) {
  return request.get('/reviews/workflows', { params })
}

export function getReviewWorkflowLogs(workflowId) {
  return request.get(`/reviews/workflows/${workflowId}/logs`)
}
