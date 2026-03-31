import request from './request'

export function getPoliceTypes(params) {
  return request.get('/police-types', { params })
}

export function getPoliceType(id) {
  return request.get(`/police-types/${id}`)
}

export function createPoliceType(data) {
  return request.post('/police-types', data)
}

export function updatePoliceType(id, data) {
  return request.put(`/police-types/${id}`, data)
}

export function deletePoliceType(id) {
  return request.delete(`/police-types/${id}`)
}
