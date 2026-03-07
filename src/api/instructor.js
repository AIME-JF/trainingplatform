import request from './request'

export function getInstructors(params) {
  return request.get('/instructors', { params })
}

export function getInstructor(id) {
  return request.get(`/instructors/${id}`)
}

export function createInstructor(data) {
  return request.post('/instructors', data)
}
