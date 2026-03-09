import request from './request'

export function recordResourceEvent(resourceId, data) {
  return request.post(`/resources/${resourceId}/events`, data)
}

export function getRecommendationFeed(params) {
  return request.get('/resources/recommendations/feed', { params })
}
