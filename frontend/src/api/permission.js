import request from './request'

export function getPermissionList(params) {
  return request.get('/permissions/list', { params })
}

export function getPermissionDetail(permissionId) {
  return request.get(`/permissions/${permissionId}/detail`)
}

export function createPermission(data) {
  return request.post('/permissions/create', data)
}

export function updatePermission(permissionId, data) {
  return request.post(`/permissions/${permissionId}/update`, data)
}

export function deletePermission(permissionId) {
  return request.post(`/permissions/${permissionId}/delete`)
}

export function syncPermissions() {
  return request.post('/permissions/sync')
}

export function getPermissionGroups() {
  return request.get('/permissions/groups')
}
