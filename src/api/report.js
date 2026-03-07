import request from './request'

export function getKpi() {
  return request.get('/report/kpi')
}

export function getTrend() {
  return request.get('/report/trend')
}

export function getTrainingTrend() {
  return request.get('/report/training-trend')
}

export function getCityAttendance() {
  return request.get('/report/training-city-attendance')
}

export function getCityCompletion() {
  return request.get('/report/training-city-completion')
}

export function getPoliceTypeDistribution() {
  return request.get('/report/police-type-distribution')
}

export function getCityRanking() {
  return request.get('/report/city-ranking')
}

export function exportReport() {
  return request.get('/report/export', { responseType: 'blob' })
}
