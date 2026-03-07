import request from './request'

export function getUsers(params) {
  return request.get('/users', { params })
}

export function getUser(id) {
  return request.get(`/users/${id}`)
}
