import request from './request'

export function createRole(data) {
  return request.post('/roles/create', data)
}

export function getRoleDetail(roleId) {
  return request.get(`/roles/${roleId}/detail`)
}

export function getRoleList(params) {
  return request.get('/roles/list', { params })
}

export function updateRole(roleId, data) {
  return request.post(`/roles/${roleId}/update`, data)
}

export function deleteRole(roleId) {
  return request.post(`/roles/${roleId}/delete`)
}

export function toggleRoleStatus(roleId, isActive) {
  return updateRole(roleId, { isActive })
}

export function updateRolePermissions(roleId, permissionIds) {
  return request.post(`/roles/${roleId}/permissions`, { permissionIds })
}

export function downloadRoleImportTemplate() {
  return request.get('/roles/import/template', {
    responseType: 'blob',
  })
}

export function exportRoles(params) {
  return request.get('/roles/export', {
    params,
    responseType: 'blob',
  })
}

export function importRoles(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/roles/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
