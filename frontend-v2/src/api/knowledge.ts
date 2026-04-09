import axiosInstance from './custom-instance'

async function unwrapData<T>(request: Promise<any>): Promise<T> {
  const response = await request
  return response.data as T
}

// ==================== 知识库 ====================

export function getKnowledgeBases(params?: { page?: number; size?: number; visibility?: string }) {
  return unwrapData<any>(axiosInstance.get('/knowledge-bases', { params }))
}

export function getKnowledgeBase(kbId: number) {
  return unwrapData<any>(axiosInstance.get(`/knowledge-bases/${kbId}`))
}

export function createKnowledgeBase(data: { name: string; description?: string; visibility?: string }) {
  return unwrapData<any>(axiosInstance.post('/knowledge-bases', data))
}

export function updateKnowledgeBase(kbId: number, data: { name?: string; description?: string; visibility?: string }) {
  return unwrapData<any>(axiosInstance.put(`/knowledge-bases/${kbId}`, data))
}

export function deleteKnowledgeBase(kbId: number) {
  return unwrapData<any>(axiosInstance.delete(`/knowledge-bases/${kbId}`))
}

// ==================== 知识库文档 ====================

export function getKnowledgeDocuments(kbId: number, params?: { page?: number; size?: number; search?: string }) {
  return unwrapData<any>(axiosInstance.get(`/knowledge-bases/${kbId}/documents`, { params }))
}

export function createKnowledgeDocument(kbId: number, data: { title: string; content: string; source_type?: string }) {
  return unwrapData<any>(axiosInstance.post(`/knowledge-bases/${kbId}/documents`, data))
}

export function updateKnowledgeDocument(docId: number, data: { title?: string; content?: string }) {
  return unwrapData<any>(axiosInstance.put(`/knowledge-bases/documents/${docId}`, data))
}

export function deleteKnowledgeDocument(docId: number) {
  return unwrapData<any>(axiosInstance.delete(`/knowledge-bases/documents/${docId}`))
}

// ==================== 知识问答 ====================

export function createChatSession(data: { knowledge_item_ids?: number[]; mode: string }) {
  return unwrapData<any>(axiosInstance.post('/knowledge-chat/sessions', data))
}

export function sendChatMessage(sessionId: number, content: string) {
  return unwrapData<any>(axiosInstance.post(`/knowledge-chat/sessions/${sessionId}/messages`, { content }))
}

export function getChatSessions(params?: { page?: number; size?: number }) {
  return unwrapData<any>(axiosInstance.get('/knowledge-chat/sessions', { params }))
}

export function getChatSession(sessionId: number) {
  return unwrapData<any>(axiosInstance.get(`/knowledge-chat/sessions/${sessionId}`))
}

// ==================== 场景模板 ====================

export function getScenarioTemplates(params?: { page?: number; size?: number; category?: string; status?: string }) {
  return unwrapData<any>(axiosInstance.get('/scenarios/templates', { params }))
}

export function getAvailableScenarioTemplates(params?: { category?: string }) {
  return unwrapData<any>(axiosInstance.get('/scenarios/templates/available', { params }))
}

export function getScenarioTemplate(templateId: number) {
  return unwrapData<any>(axiosInstance.get(`/scenarios/templates/${templateId}`))
}

export function createScenarioTemplate(data: Record<string, any>) {
  return unwrapData<any>(axiosInstance.post('/scenarios/templates', data))
}

export function updateScenarioTemplate(templateId: number, data: Record<string, any>) {
  return unwrapData<any>(axiosInstance.put(`/scenarios/templates/${templateId}`, data))
}

export function deleteScenarioTemplate(templateId: number) {
  return unwrapData<any>(axiosInstance.delete(`/scenarios/templates/${templateId}`))
}

export function publishScenarioTemplate(templateId: number) {
  return unwrapData<any>(axiosInstance.post(`/scenarios/templates/${templateId}/publish`))
}

// ==================== 场景模拟会话 ====================

export function startScenarioSession(templateId: number) {
  return unwrapData<any>(axiosInstance.post('/scenarios/sessions', { template_id: templateId }))
}

export function sendScenarioMessage(sessionId: number, content: string) {
  return unwrapData<any>(axiosInstance.post(`/scenarios/sessions/${sessionId}/messages`, { content }))
}

export function endScenarioSession(sessionId: number) {
  return unwrapData<any>(axiosInstance.post(`/scenarios/sessions/${sessionId}/end`))
}

export function getMyScenarioSessions(params?: { page?: number; size?: number }) {
  return unwrapData<any>(axiosInstance.get('/scenarios/sessions/my', { params }))
}

export function getScenarioSession(sessionId: number) {
  return unwrapData<any>(axiosInstance.get(`/scenarios/sessions/${sessionId}`))
}

export function getTemplateScenarioSessions(templateId: number, params?: { page?: number; size?: number }) {
  return unwrapData<any>(axiosInstance.get(`/scenarios/templates/${templateId}/sessions`, { params }))
}
