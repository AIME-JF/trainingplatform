import request from './request'

export function getDashboard(role) {
  return request.get('/dashboard', { params: { role } })
}
