import request from './request'

export function getQuestions(params) {
    return request.get('/questions', { params })
}

export function createQuestion(data) {
    return request.post('/questions', data)
}

export function updateQuestion(id, data) {
    return request.put(`/questions/${id}`, data)
}

export function deleteQuestion(id) {
    return request.delete(`/questions/${id}`)
}

export function batchCreateQuestions(data) {
    return request.post('/questions/batch', data)
}

export function getQuestionFolders() {
    return request.get('/questions/folders')
}

export function createQuestionFolder(data) {
    return request.post('/questions/folders', data)
}

export function updateQuestionFolder(id, data) {
    return request.put(`/questions/folders/${id}`, data)
}

export function deleteQuestionFolder(id) {
    return request.delete(`/questions/folders/${id}`)
}

export function moveQuestionToFolder(questionId, folderId) {
    return request.patch(`/questions/${questionId}/folder`, { folder_id: folderId })
}
