import request from './request'

export function getCertificates(params) {
  return request.get('/certificates', { params })
}

export function createCertificate(data) {
  return request.post('/certificates', data)
}
