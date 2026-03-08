import request from './request'

export function getCourses(params) {
  return request.get('/courses', { params })
}

export function getCourse(id) {
  return request.get(`/courses/${id}`)
}

export function createCourse(data) {
  return request.post('/courses', data)
}

export function updateCourse(id, data) {
  return request.put(`/courses/${id}`, data)
}

export function deleteCourse(id) {
  return request.delete(`/courses/${id}`)
}

export function getProgress() {
  return request.get('/courses/progress')
}

export function updateChapterProgress(courseId, chapterId, progress) {
  return request.put(`/courses/${courseId}/chapters/${chapterId}/progress`, { progress })
}

export function getCourseNote(courseId) {
  return request.get(`/courses/${courseId}/note`)
}

export function saveCourseNote(courseId, content) {
  return request.put(`/courses/${courseId}/note`, { content })
}
