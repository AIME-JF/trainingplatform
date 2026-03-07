import request from './request'

export function getKpi() {
  return request.get('/report/kpi')
}

export function getTrend() {
  return request.get('/report/trend')
}

export function getPoliceTypeDistribution() {
  return request.get('/report/police-type-distribution')
}

export function getCityRanking() {
  return request.get('/report/city-ranking')
}
