import request from './request'

export function getLibraryFolders() {
  return request.get('/library/folders')
}

export function createLibraryFolder(data) {
  return request.post('/library/folders', data)
}

export function updateLibraryFolder(id, data) {
  return request.put(`/library/folders/${id}`, data)
}

export function deleteLibraryFolder(id) {
  return request.delete(`/library/folders/${id}`)
}

export function getLibraryItems(params) {
  return request.get('/library/items', { params })
}

export function getLibraryItem(id) {
  return request.get(`/library/items/${id}`)
}

export function createLibraryItemsFromFiles(data) {
  return request.post('/library/items/files', data)
}

export function createLibraryKnowledgeItem(data) {
  return request.post('/library/items/knowledge', data)
}

export function updateLibraryItem(id, data) {
  return request.put(`/library/items/${id}`, data)
}

export function moveLibraryItem(id, data) {
  return request.post(`/library/items/${id}/move`, data)
}

export function shareLibraryItem(id) {
  return request.post(`/library/items/${id}/share`)
}

export function unshareLibraryItem(id) {
  return request.post(`/library/items/${id}/unshare`)
}

export function deleteLibraryItem(id) {
  return request.delete(`/library/items/${id}`)
}
