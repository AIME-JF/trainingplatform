import request from './request'

export function getResources(params) {
  return request.get('/resources', { params })
}

export function getResource(id) {
  return request.get(`/resources/${id}`)
}

export function getResourceTags(params) {
  return request.get('/resources/tags', { params })
}

export function createResourceTag(data) {
  return request.post('/resources/tags', data)
}

export function createResource(data) {
  return request.post('/resources', data)
}

export function updateResource(id, data) {
  return request.put(`/resources/${id}`, data)
}

export function publishResource(id) {
  return request.post(`/resources/${id}/publish`)
}

export function offlineResource(id) {
  return request.post(`/resources/${id}/offline`)
}

export function deleteResource(id) {
  return request.delete(`/resources/${id}`)
}

export function bindCourseResource(courseId, data) {
  return request.post(`/courses/${courseId}/resources`, data)
}

export function getCourseResources(courseId) {
  return request.get(`/courses/${courseId}/resources`)
}

export function unbindCourseResource(courseId, resourceId) {
  return request.delete(`/courses/${courseId}/resources/${resourceId}`)
}

export function bindTrainingResource(trainingId, data) {
  return request.post(`/trainings/${trainingId}/resources`, data)
}

export function getTrainingResources(trainingId) {
  return request.get(`/trainings/${trainingId}/resources`)
}

export function unbindTrainingResource(trainingId, resourceId) {
  return request.delete(`/trainings/${trainingId}/resources/${resourceId}`)
}
