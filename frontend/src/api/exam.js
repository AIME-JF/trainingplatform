import request from './request'

export function getExamPapers(params) {
    return request.get('/exams/papers', { params })
}

export function createExamPaper(data) {
    return request.post('/exams/papers', data)
}

export function updateExamPaper(id, data) {
    return request.put(`/exams/papers/${id}`, data)
}

export function getExamPaperDetail(id) {
    return request.get(`/exams/papers/${id}`)
}

export function publishExamPaper(id) {
    return request.post(`/exams/papers/${id}/publish`)
}

export function archiveExamPaper(id) {
    return request.post(`/exams/papers/${id}/archive`)
}

export function deleteExamPaper(id) {
    return request.delete(`/exams/papers/${id}`)
}

export function getPaperFolders() {
    return request.get('/exams/paper-folders')
}

export function createPaperFolder(data) {
    return request.post('/exams/paper-folders', data)
}

export function updatePaperFolder(id, data) {
    return request.put(`/exams/paper-folders/${id}`, data)
}

export function deletePaperFolder(id) {
    return request.delete(`/exams/paper-folders/${id}`)
}

export function movePaperToFolder(paperId, folderId) {
    return request.patch(`/exams/papers/${paperId}/folder`, { folder_id: folderId })
}

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

export function deleteExam(id) {
    return request.delete(`/exams/${id}`)
}

export function deleteAdmissionExam(id) {
    return request.delete(`/exams/admission/${id}`)
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
