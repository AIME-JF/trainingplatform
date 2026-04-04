import request from './custom-instance'

export function getAiQuestionTasks(params?: { page?: number; size?: number; status?: string }) {
  return request.get('/ai/question-tasks', { params }) as Promise<any>
}

export function createAiQuestionTask(data: {
  task_name: string
  topic: string
  source_text?: string
  knowledge_points?: string[]
  question_count?: number
  question_types?: string[]
  difficulty?: number
  police_type_id?: number
  score?: number
  requirements?: string
  target_bank_name?: string
  course_id?: number
  course_name?: string
  source_material_name?: string
}) {
  return request.post('/ai/question-tasks', data) as Promise<any>
}

export function getAiQuestionTaskDetail(taskId: number) {
  return request.get(`/ai/question-tasks/${taskId}`) as Promise<any>
}

export function updateAiQuestionTaskResult(taskId: number, data: { taskName?: string; questions?: any[] }) {
  return request.put(`/ai/question-tasks/${taskId}/result`, data) as Promise<any>
}

export function confirmAiQuestionTask(taskId: number) {
  return request.post(`/ai/question-tasks/${taskId}/confirm`) as Promise<any>
}

export function parseAiDocumentFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/ai/files/parse', formData) as Promise<any>
}
