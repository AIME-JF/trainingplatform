import request from './request'

export function getUsers(params) {
  return request.get('/users', { params })
}

export function getUser(id) {
  return request.get(`/users/${id}`)
}

export function createUser(data) {
  return request.post('/users', data)
}

export function updateUser(id, data) {
  return request.put(`/users/${id}`, data)
}

export function updateUserRoles(id, roleIds) {
  return request.put(`/users/${id}/roles`, { roleIds })
}

export function resetPassword(id, password) {
  return request.put(`/users/${id}/password`, { password })
}

export function deleteUser(id) {
  return request.delete(`/users/${id}`)
}

export function getRoles() {
  return request.get('/roles')
}
