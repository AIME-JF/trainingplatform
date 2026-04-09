import axiosInstance from './custom-instance'

// ==================== 知识库 ====================

export function getKnowledgeBases(params?: { page?: number; size?: number; visibility?: string }) {
  return axiosInstance.get('/knowledge-bases', { params }) as Promise<any>
}

export function getKnowledgeBase(kbId: number) {
  return axiosInstance.get(`/knowledge-bases/${kbId}`) as Promise<any>
}

export function createKnowledgeBase(data: { name: string; description?: string; visibility?: string }) {
  return axiosInstance.post('/knowledge-bases', data) as Promise<any>
}

export function updateKnowledgeBase(kbId: number, data: { name?: string; description?: string; visibility?: string }) {
  return axiosInstance.put(`/knowledge-bases/${kbId}`, data) as Promise<any>
}

export function deleteKnowledgeBase(kbId: number) {
  return axiosInstance.delete(`/knowledge-bases/${kbId}`) as Promise<any>
}

// ==================== 知识库文档 ====================

export function getKnowledgeDocuments(kbId: number, params?: { page?: number; size?: number; search?: string }) {
  return axiosInstance.get(`/knowledge-bases/${kbId}/documents`, { params }) as Promise<any>
}

export function createKnowledgeDocument(kbId: number, data: { title: string; content: string; source_type?: string }) {
  return axiosInstance.post(`/knowledge-bases/${kbId}/documents`, data) as Promise<any>
}

export function updateKnowledgeDocument(docId: number, data: { title?: string; content?: string }) {
  return axiosInstance.put(`/knowledge-bases/documents/${docId}`, data) as Promise<any>
}

export function deleteKnowledgeDocument(docId: number) {
  return axiosInstance.delete(`/knowledge-bases/documents/${docId}`) as Promise<any>
}

// ==================== 知识问答 ====================

export function createChatSession(data: { knowledge_item_ids?: number[]; mode: string }) {
  return axiosInstance.post('/knowledge-chat/sessions', data) as Promise<any>
}

export function sendChatMessage(sessionId: number, content: string) {
  return axiosInstance.post(`/knowledge-chat/sessions/${sessionId}/messages`, { content }) as Promise<any>
}

export function getChatSessions(params?: { page?: number; size?: number }) {
  return axiosInstance.get('/knowledge-chat/sessions', { params }) as Promise<any>
}

export function getChatSession(sessionId: number) {
  return axiosInstance.get(`/knowledge-chat/sessions/${sessionId}`) as Promise<any>
}

// ==================== 场景模板 ====================

export function getScenarioTemplates(params?: { page?: number; size?: number; category?: string; status?: string }) {
  return axiosInstance.get('/scenarios/templates', { params }) as Promise<any>
}

export function getAvailableScenarioTemplates(params?: { category?: string }) {
  return axiosInstance.get('/scenarios/templates/available', { params }) as Promise<any>
}

export function getScenarioTemplate(templateId: number) {
  return axiosInstance.get(`/scenarios/templates/${templateId}`) as Promise<any>
}

export function createScenarioTemplate(data: Record<string, any>) {
  return axiosInstance.post('/scenarios/templates', data) as Promise<any>
}

export function updateScenarioTemplate(templateId: number, data: Record<string, any>) {
  return axiosInstance.put(`/scenarios/templates/${templateId}`, data) as Promise<any>
}

export function deleteScenarioTemplate(templateId: number) {
  return axiosInstance.delete(`/scenarios/templates/${templateId}`) as Promise<any>
}

export function publishScenarioTemplate(templateId: number) {
  return axiosInstance.post(`/scenarios/templates/${templateId}/publish`) as Promise<any>
}

// ==================== 场景模拟会话 ====================

export function startScenarioSession(templateId: number) {
  return axiosInstance.post('/scenarios/sessions', { template_id: templateId }) as Promise<any>
}

export function sendScenarioMessage(sessionId: number, content: string) {
  return axiosInstance.post(`/scenarios/sessions/${sessionId}/messages`, { content }) as Promise<any>
}

export function endScenarioSession(sessionId: number) {
  return axiosInstance.post(`/scenarios/sessions/${sessionId}/end`) as Promise<any>
}

export function getMyScenarioSessions(params?: { page?: number; size?: number }) {
  return axiosInstance.get('/scenarios/sessions/my', { params }) as Promise<any>
}

export function getScenarioSession(sessionId: number) {
  return axiosInstance.get(`/scenarios/sessions/${sessionId}`) as Promise<any>
}

export function getTemplateScenarioSessions(templateId: number, params?: { page?: number; size?: number }) {
  return axiosInstance.get(`/scenarios/templates/${templateId}/sessions`, { params }) as Promise<any>
}
