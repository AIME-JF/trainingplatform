import request from './request'

export function getTrainingPlans(params) {
  return request.get('/training-plans', { params })
}

export function getTrainingPlan(id) {
  return request.get(`/training-plans/${id}`)
}

export function createTrainingPlan(data) {
  return request.post('/training-plans', data)
}

export function updateTrainingPlan(id, data) {
  return request.put(`/training-plans/${id}`, data)
}

export function deleteTrainingPlan(id) {
  return request.delete(`/training-plans/${id}`)
}
