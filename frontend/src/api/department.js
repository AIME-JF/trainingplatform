import request from './request'

export function createDepartment(data) {
  return request.post('/departments/create', data)
}

export function getDepartmentDetail(departmentId) {
  return request.get(`/departments/${departmentId}/detail`)
}

export function getDepartmentList(params) {
  return request.get('/departments/list', { params })
}

export function getDepartmentTree() {
  return request.get('/departments/tree')
}

export function updateDepartment(departmentId, data) {
  return request.post(`/departments/${departmentId}/update`, data)
}

export function deleteDepartment(departmentId) {
  return request.post(`/departments/${departmentId}/delete`)
}

export function toggleDepartmentStatus(departmentId, isActive) {
  return updateDepartment(departmentId, { isActive })
}

export function updateDepartmentPermissions(departmentId, permissionIds) {
  return request.post(`/departments/${departmentId}/permissions`, { permissionIds })
}
