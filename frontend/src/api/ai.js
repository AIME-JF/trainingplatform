import request from './request'

export function getAiQuestionTasks(params) {
  return request.get('/ai/question-tasks', { params })
}

export function createAiQuestionTask(data) {
  return request.post('/ai/question-tasks', data)
}

export function getAiQuestionTaskDetail(taskId) {
  return request.get(`/ai/question-tasks/${taskId}`)
}

export function updateAiQuestionTaskResult(taskId, data) {
  return request.put(`/ai/question-tasks/${taskId}/result`, data)
}

export function confirmAiQuestionTask(taskId) {
  return request.post(`/ai/question-tasks/${taskId}/confirm`)
}

export function getAiPaperAssemblyTasks(params) {
  return request.get('/ai/paper-assembly-tasks', { params })
}

export function createAiPaperAssemblyTask(data) {
  return request.post('/ai/paper-assembly-tasks', data)
}

export function getAiPaperAssemblyTaskDetail(taskId) {
  return request.get(`/ai/paper-assembly-tasks/${taskId}`)
}

export function updateAiPaperAssemblyTaskResult(taskId, data) {
  return request.put(`/ai/paper-assembly-tasks/${taskId}/result`, data)
}

export function confirmAiPaperAssemblyTask(taskId) {
  return request.post(`/ai/paper-assembly-tasks/${taskId}/confirm`)
}

export function deleteAiPaperAssemblyTask(taskId) {
  return request.delete(`/ai/paper-assembly-tasks/${taskId}`)
}

export function getAiPaperGenerationTasks(params) {
  return request.get('/ai/paper-generation-tasks', { params })
}

export function createAiPaperGenerationTask(data) {
  return request.post('/ai/paper-generation-tasks', data)
}

export function getAiPaperGenerationTaskDetail(taskId) {
  return request.get(`/ai/paper-generation-tasks/${taskId}`)
}

export function updateAiPaperGenerationTaskResult(taskId, data) {
  return request.put(`/ai/paper-generation-tasks/${taskId}/result`, data)
}

export function confirmAiPaperGenerationTask(taskId) {
  return request.post(`/ai/paper-generation-tasks/${taskId}/confirm`)
}

export function deleteAiPaperGenerationTask(taskId) {
  return request.delete(`/ai/paper-generation-tasks/${taskId}`)
}

export function getAiPaperDocumentGenerationTasks(params) {
  return request.get('/ai/paper-document-generation-tasks', { params })
}

export function createAiPaperDocumentGenerationTask(data) {
  return request.post('/ai/paper-document-generation-tasks', data)
}

export function getAiPaperDocumentGenerationTaskDetail(taskId) {
  return request.get(`/ai/paper-document-generation-tasks/${taskId}`)
}

export function updateAiPaperDocumentGenerationTaskResult(taskId, data) {
  return request.put(`/ai/paper-document-generation-tasks/${taskId}/result`, data)
}

export function confirmAiPaperDocumentGenerationTask(taskId) {
  return request.post(`/ai/paper-document-generation-tasks/${taskId}/confirm`)
}

export function deleteAiPaperDocumentGenerationTask(taskId) {
  return request.delete(`/ai/paper-document-generation-tasks/${taskId}`)
}

export function parseAiDocumentFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/ai/files/parse', formData)
}

export function getTeachingResourceGenerationTasks(params) {
  return request.get('/ai/teaching-resource-generation-tasks', { params })
}

export function createTeachingResourceGenerationTask(data) {
  return request.post('/ai/teaching-resource-generation-tasks', data)
}

export function getTeachingResourceGenerationTaskDetail(taskId) {
  return request.get(`/ai/teaching-resource-generation-tasks/${taskId}`)
}

export function updateTeachingResourceGenerationTaskMeta(taskId, data) {
  return request.put(`/ai/teaching-resource-generation-tasks/${taskId}/resource-meta`, data)
}

export function confirmTeachingResourceGenerationTask(taskId) {
  return request.post(`/ai/teaching-resource-generation-tasks/${taskId}/confirm`)
}

export function getAiScheduleTasks(params) {
  return request.get('/ai/schedule-tasks', { params })
}

export function previewAiScheduleTask(data) {
  return request.post('/ai/schedule-tasks/preview', data)
}

export function createAiScheduleTask(data) {
  return request.post('/ai/schedule-tasks', data)
}

export function getAiScheduleTaskDetail(taskId) {
  return request.get(`/ai/schedule-tasks/${taskId}`)
}

export function deleteAiScheduleTask(taskId) {
  return request.delete(`/ai/schedule-tasks/${taskId}`)
}

export function confirmAiScheduleTaskRules(taskId, data) {
  return request.post(`/ai/schedule-tasks/${taskId}/confirm-rules`, data)
}

export function updateAiScheduleTaskResult(taskId, data) {
  return request.put(`/ai/schedule-tasks/${taskId}/result`, data)
}

export function confirmAiScheduleTask(taskId) {
  return request.post(`/ai/schedule-tasks/${taskId}/confirm`)
}

// 智能解析课表
export function getScheduleFileParseTaskList(params) {
  return request.get('/ai/schedule-file-parse-tasks', { params })
}

export function createScheduleFileParseTask(file, taskName) {
  const formData = new FormData()
  formData.append('file', file)
  const params = taskName ? { task_name: taskName } : {}
  return request.post('/ai/schedule-file-parse-tasks', formData, { params })
}

export function getScheduleFileParseTaskDetail(taskId) {
  return request.get(`/ai/schedule-file-parse-tasks/${taskId}`)
}

export function updateScheduleFileParseTask(taskId, data) {
  return request.put(`/ai/schedule-file-parse-tasks/${taskId}`, data)
}

export function confirmScheduleFileParseTask(taskId) {
  return request.post(`/ai/schedule-file-parse-tasks/${taskId}/confirm`)
}
