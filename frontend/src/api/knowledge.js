import request from './request'

// ==================== 知识库 ====================

export function getKnowledgeBases(params) {
  return request.get('/knowledge-bases', { params })
}

export function getKnowledgeBase(kbId) {
  return request.get(`/knowledge-bases/${kbId}`)
}

export function createKnowledgeBase(data) {
  return request.post('/knowledge-bases', data)
}

export function updateKnowledgeBase(kbId, data) {
  return request.put(`/knowledge-bases/${kbId}`, data)
}

export function deleteKnowledgeBase(kbId) {
  return request.delete(`/knowledge-bases/${kbId}`)
}

// ==================== 知识库文档 ====================

export function getKnowledgeDocuments(kbId, params) {
  return request.get(`/knowledge-bases/${kbId}/documents`, { params })
}

export function createKnowledgeDocument(kbId, data) {
  return request.post(`/knowledge-bases/${kbId}/documents`, data)
}

export function updateKnowledgeDocument(docId, data) {
  return request.put(`/knowledge-bases/documents/${docId}`, data)
}

export function deleteKnowledgeDocument(docId) {
  return request.delete(`/knowledge-bases/documents/${docId}`)
}

// ==================== 场景模板 ====================

export function getScenarioTemplates(params) {
  return request.get('/scenarios/templates', { params })
}

export function getScenarioTemplate(templateId) {
  return request.get(`/scenarios/templates/${templateId}`)
}

export function createScenarioTemplate(data) {
  return request.post('/scenarios/templates', data)
}

export function updateScenarioTemplate(templateId, data) {
  return request.put(`/scenarios/templates/${templateId}`, data)
}

export function deleteScenarioTemplate(templateId) {
  return request.delete(`/scenarios/templates/${templateId}`)
}

export function publishScenarioTemplate(templateId) {
  return request.post(`/scenarios/templates/${templateId}/publish`)
}

// ==================== 场景模拟记录 ====================

export function getTemplateScenarioSessions(templateId, params) {
  return request.get(`/scenarios/templates/${templateId}/sessions`, { params })
}

export function getScenarioSession(sessionId) {
  return request.get(`/scenarios/sessions/${sessionId}`)
}
