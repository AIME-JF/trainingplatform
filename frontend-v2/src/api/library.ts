import axiosInstance from '@/api/custom-instance'
import type { MediaFileResponse } from '@/api/learning-resource'

export interface LibraryFolderResponse {
  id: number
  name: string
  parent_id: number | null
  sort_order: number
  item_count: number
  children: LibraryFolderResponse[]
}

export interface LibraryItemResponse {
  id: number
  owner_user_id: number
  owner_name?: string | null
  folder_id?: number | null
  folder_name?: string | null
  title: string
  content_type: 'video' | 'document' | 'image' | 'audio' | 'knowledge'
  source_kind: 'file' | 'knowledge' | 'ai_generated'
  media_file_id?: number | null
  file_name?: string | null
  file_url?: string | null
  mime_type?: string | null
  size: number
  duration_seconds: number
  is_public: boolean
  is_owner: boolean
  knowledge_content_html?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface PaginatedResult<T> {
  page: number
  size: number
  total: number
  items: T[]
}

export interface LibraryFolderCreatePayload {
  name: string
  parent_id?: number | null
  sort_order?: number
}

export interface LibraryItemQuery {
  page?: number
  size?: number
  scope?: 'private' | 'public' | 'accessible'
  category?: string
  folder_id?: number | null
  search?: string
  source_kind?: LibraryItemResponse['source_kind']
}

export interface LibraryMovePayload {
  folder_id?: number | null
}

export interface LibraryKnowledgePayload {
  title: string
  folder_id?: number | null
  knowledge_content_html: string
}

export interface LibraryFileBatchPayload {
  folder_id?: number | null
  media_file_ids: number[]
}

export async function listLibraryFolders() {
  const response = await axiosInstance.get('/library/folders')
  return response.data as LibraryFolderResponse[]
}

export async function createLibraryFolder(payload: LibraryFolderCreatePayload) {
  const response = await axiosInstance.post('/library/folders', payload)
  return response.data as LibraryFolderResponse
}

export async function deleteLibraryFolder(folderId: number) {
  const response = await axiosInstance.delete(`/library/folders/${folderId}`)
  return response.data as { success?: boolean }
}

export async function listLibraryItems(params?: LibraryItemQuery) {
  const response = await axiosInstance.get('/library/items', { params })
  return response.data as PaginatedResult<LibraryItemResponse>
}

export async function listAccessibleAssistantItems() {
  const response = await axiosInstance.get('/library/assistant-items')
  return response.data as LibraryItemResponse[]
}

export async function listAccessibleKnowledgeItems() {
  return listAccessibleAssistantItems()
}

export async function getLibraryItemDetail(itemId: number) {
  const response = await axiosInstance.get(`/library/items/${itemId}`)
  return response.data as LibraryItemResponse
}

export async function createLibraryItemsFromFiles(payload: LibraryFileBatchPayload) {
  const response = await axiosInstance.post('/library/items/files', payload)
  return response.data as LibraryItemResponse[]
}

export async function createLibraryKnowledgeItem(payload: LibraryKnowledgePayload) {
  const response = await axiosInstance.post('/library/items/knowledge', payload)
  return response.data as LibraryItemResponse
}

export async function updateLibraryItem(itemId: number, payload: { title?: string; knowledge_content_html?: string }) {
  const response = await axiosInstance.put(`/library/items/${itemId}`, payload)
  return response.data as LibraryItemResponse
}

export async function moveLibraryItem(itemId: number, payload: LibraryMovePayload) {
  const response = await axiosInstance.post(`/library/items/${itemId}/move`, payload)
  return response.data as LibraryItemResponse
}

export async function shareLibraryItem(itemId: number) {
  const response = await axiosInstance.post(`/library/items/${itemId}/share`)
  return response.data as LibraryItemResponse
}

export async function unshareLibraryItem(itemId: number) {
  const response = await axiosInstance.post(`/library/items/${itemId}/unshare`)
  return response.data as LibraryItemResponse
}

export async function deleteLibraryItem(itemId: number) {
  const response = await axiosInstance.delete(`/library/items/${itemId}`)
  return response.data as { success?: boolean }
}

export async function uploadLibraryFile(file: File, onProgress?: (percent: number) => void) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await axiosInstance.post('/media/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000,
    onUploadProgress: onProgress
      ? (event) => onProgress(Math.round((event.loaded / (event.total || 1)) * 100))
      : undefined,
  })
  return response.data as MediaFileResponse
}
