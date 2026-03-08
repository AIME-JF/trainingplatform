import request from './request'

export function getExams(params) {
    return request.get('/exams', { params })
}

export function getExamRecordsAnalysis(examId) {
    return request.get(`/exams/${examId}/records/analysis`)
}

export function createExam(data) {
    return request.post('/exams', data)
}

export function updateExam(id, data) {
    return request.put(`/exams/${id}`, data)
}

export function getExamDetail(id) {
    return request.get(`/exams/${id}`)
}

export function submitExam(id, data) {
    return request.post(`/exams/${id}/submit`, data)
}

export function getExamResult(id) {
    return request.get(`/exams/${id}/result`)
}
