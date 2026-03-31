import request from './request'

export function login(username, password) {
  return request.post('/auth/login', { username, password })
}

export function loginByPhone(phone, code) {
  return request.post('/auth/login/phone', null, { params: { phone, code } })
}

export function getCurrentUser() {
  return request.get('/auth/me')
}
