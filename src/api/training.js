import request from './request'

export function getTrainings(params) {
  return request.get('/trainings', { params })
}

export function getTraining(id) {
  return request.get(`/trainings/${id}`)
}

export function createTraining(data) {
  return request.post('/trainings', data)
}

export function updateTraining(id, data) {
  return request.put(`/trainings/${id}`, data)
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

export function getCheckinRecords(id, date) {
  return request.get(`/trainings/${id}/checkin/records`, { params: { date } })
}

export function checkin(id, data) {
  return request.post(`/trainings/${id}/checkin`, data)
}

export function getCheckinQR(id) {
  return request.get(`/trainings/${id}/checkin/qr`)
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
