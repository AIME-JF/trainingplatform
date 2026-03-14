import request from './request'

export function getTalents(params) {
  return request.get('/talent', { params })
}

export function getTalentStats() {
  return request.get('/talent/stats')
}
