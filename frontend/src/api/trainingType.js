import request from './request'

export function getTrainingTypes(params) {
  return request.get('/training-types', { params })
}

export function getTrainingType(id) {
  return request.get(`/training-types/${id}`)
}

export function createTrainingType(data) {
  return request.post('/training-types', data)
}

export function updateTrainingType(id, data) {
  return request.put(`/training-types/${id}`, data)
}

export function deleteTrainingType(id) {
  return request.delete(`/training-types/${id}`)
}
