import request from './request'

export function getExams(params) {
    return request.get('/exams', { params })
}

export function getAdmissionExams(params) {
    return request.get('/exams/admission', { params })
}

export function getExamRecordsAnalysis(examId) {
    return request.get(`/exams/${examId}/records/analysis`)
}

export function getAdmissionExamRecordsAnalysis(examId) {
    return request.get(`/exams/admission/${examId}/records/analysis`)
}

export function createExam(data) {
    return request.post('/exams', data)
}

export function createAdmissionExam(data) {
    return request.post('/exams/admission', data)
}

export function updateExam(id, data) {
    return request.put(`/exams/${id}`, data)
}

export function updateAdmissionExam(id, data) {
    return request.put(`/exams/admission/${id}`, data)
}

export function getExamDetail(id) {
    return request.get(`/exams/${id}`)
}

export function getAdmissionExamDetail(id) {
    return request.get(`/exams/admission/${id}`)
}

export function submitExam(id, data) {
    return request.post(`/exams/${id}/submit`, data)
}

export function submitAdmissionExam(id, data) {
    return request.post(`/exams/admission/${id}/submit`, data)
}

export function getExamResult(id) {
    return request.get(`/exams/${id}/result`)
}

export function getAdmissionExamResult(id) {
    return request.get(`/exams/admission/${id}/result`)
}

export function getExamScores(id, params) {
    return request.get(`/exams/${id}/scores`, { params })
}

export function getAdmissionExamScores(id, params) {
    return request.get(`/exams/admission/${id}/scores`, { params })
}
