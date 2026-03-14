import request from './request'

export function getTrainings(params) {
  return request.get('/trainings', { params })
}

export function getTraining(id) {
  return request.get(`/trainings/${id}`)
}

export function getTrainingBases(params) {
  return request.get('/training-bases', { params })
}

export function getTrainingBase(id) {
  return request.get(`/training-bases/${id}`)
}

export function createTrainingBase(data) {
  return request.post('/training-bases', data)
}

export function updateTrainingBase(id, data) {
  return request.put(`/training-bases/${id}`, data)
}

export function deleteTrainingBase(id) {
  return request.delete(`/training-bases/${id}`)
}

export function createTraining(data) {
  return request.post('/trainings', data)
}

export function updateTraining(id, data) {
  return request.put(`/trainings/${id}`, data)
}

export function publishTraining(id) {
  return request.post(`/trainings/${id}/publish`)
}

export function lockTraining(id) {
  return request.post(`/trainings/${id}/lock`)
}

export function deleteTraining(id) {
  return request.delete(`/trainings/${id}`)
}

export function startTraining(id) {
  return request.post(`/trainings/${id}/start`)
}

export function endTraining(id) {
  return request.post(`/trainings/${id}/end`)
}

export function getStudents(id, params) {
  return request.get(`/trainings/${id}/students`, { params })
}

export function getSchedule(id) {
  return request.get(`/trainings/${id}/schedule`)
}

export function enroll(id, data) {
  return request.post(`/trainings/${id}/enroll`, data)
}

export function getEnrollments(id, params) {
  return request.get(`/trainings/${id}/enrollments`, { params })
}

export function approveEnrollment(trainingId, enrollmentId) {
  return request.put(`/trainings/${trainingId}/enrollments/${enrollmentId}/approve`)
}

export function rejectEnrollment(trainingId, enrollmentId, note) {
  return request.put(`/trainings/${trainingId}/enrollments/${enrollmentId}/reject`, { note })
}

export function getCheckinRecords(id, params) {
  return request.get(`/trainings/${id}/checkin/records`, { params })
}

export function checkin(id, data) {
  return request.post(`/trainings/${id}/checkin`, data)
}

export function checkout(id, data) {
  return request.post(`/trainings/${id}/checkout`, data)
}

export function submitTrainingEvaluation(id, data) {
  return request.post(`/trainings/${id}/evaluation`, data)
}

export function getAttendanceSummary(id, params) {
  return request.get(`/trainings/${id}/attendance/summary`, { params })
}

export function getCheckinQR(id, params) {
  return request.get(`/trainings/${id}/checkin/qr`, { params })
}

export function startTrainingSessionCheckin(trainingId, sessionKey) {
  return request.post(`/trainings/${trainingId}/sessions/${sessionKey}/checkin/start`)
}

export function endTrainingSessionCheckin(trainingId, sessionKey) {
  return request.post(`/trainings/${trainingId}/sessions/${sessionKey}/checkin/end`)
}

export function startTrainingSessionCheckout(trainingId, sessionKey) {
  return request.post(`/trainings/${trainingId}/sessions/${sessionKey}/checkout/start`)
}

export function endTrainingSessionCheckout(trainingId, sessionKey) {
  return request.post(`/trainings/${trainingId}/sessions/${sessionKey}/checkout/end`)
}

export function skipTrainingSession(trainingId, sessionKey, data) {
  return request.post(`/trainings/${trainingId}/sessions/${sessionKey}/skip`, data)
}

export function getCheckinQrToken(token) {
  return request.get(`/trainings/checkin/qr/${token}`)
}

export function submitCheckinByQr(token) {
  return request.post(`/trainings/checkin/qr/${token}`)
}

export function updateTrainingRoster(trainingId, assignments) {
  return request.put(`/trainings/${trainingId}/roster`, assignments)
}

export function getTrainingHistories(trainingId, params) {
  return request.get(`/trainings/${trainingId}/histories`, { params })
}

export function getMyTrainingHistories() {
  return request.get('/trainings/histories/me')
}

export function bindTrainingResource(trainingId, data) {
  return request.post(`/trainings/${trainingId}/resources`, data)
}

export function getTrainingResources(trainingId) {
  return request.get(`/trainings/${trainingId}/resources`)
}

export function unbindTrainingResource(trainingId, resourceId) {
  return request.delete(`/trainings/${trainingId}/resources/${resourceId}`)
}

export function importTrainingStudents(trainingId, file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post(`/trainings/${trainingId}/import/students`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function importTrainingInstructors(trainingId, file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post(`/trainings/${trainingId}/import/instructors`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function importTrainingSchedule(trainingId, file, replaceExisting = true) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('replace_existing', String(replaceExisting))
  return request.post(`/trainings/${trainingId}/import/schedule`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
