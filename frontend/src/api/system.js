import request from './request'

export function getConfigGroupList(params = { size: -1 }) {
  return request.get('/system/config-groups', { params })
}

export function getConfigGroupDetail(groupId) {
  return request.get(`/system/config-groups/${groupId}`)
}

export function resetConfigGroup(groupId) {
  return request.post(`/system/config-groups/${groupId}/reset`)
}

export function getConfigList(params = {}) {
  return request.get('/system/configs', { params })
}

export function getConfigDetail(configId) {
  return request.get(`/system/configs/${configId}`)
}

export function updateConfig(configId, data) {
  return request.put(`/system/configs/${configId}`, data)
}
