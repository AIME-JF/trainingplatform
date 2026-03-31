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

export function updateUserDepartments(id, departmentIds) {
  return request.put(`/users/${id}/departments`, { departmentIds })
}

export function getPoliceTypes() {
  return request.get('/police-types', { params: { size: -1 } })
}

export function updateUserPoliceTypes(id, policeTypeIds) {
  return request.put(`/users/${id}/police-types`, { police_type_ids: policeTypeIds })
}

export function importPoliceBase(file, defaultRole = 'student') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('default_role', defaultRole)
  return request.post('/users/import/police-base', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function downloadUserImportTemplate() {
  return request.get('/users/import/template', {
    responseType: 'blob',
  })
}

export function exportUsers(params) {
  return request.get('/users/export', {
    params,
    responseType: 'blob',
  })
}

export function importUsers(file, defaultRole = 'student') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('default_role', defaultRole)
  return request.post('/users/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
