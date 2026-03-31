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
