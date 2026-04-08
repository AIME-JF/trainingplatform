import { customInstance } from './custom-instance'

export function getTrainingReportTasks(params: Record<string, unknown>) {
  return customInstance<any>({
    url: '/ai/training-report-tasks',
    method: 'GET',
    params,
  })
}

export function createTrainingReportTask(data: Record<string, unknown>) {
  return customInstance<any>({
    url: '/ai/training-report-tasks',
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    data,
  })
}

export function getTrainingReportTaskDetail(taskId: number) {
  return customInstance<any>({
    url: `/ai/training-report-tasks/${taskId}`,
    method: 'GET',
  })
}

export function updateTrainingReportTask(taskId: number, data: Record<string, unknown>) {
  return customInstance<any>({
    url: `/ai/training-report-tasks/${taskId}/result`,
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    data,
  })
}

export function confirmTrainingReportTask(taskId: number) {
  return customInstance<any>({
    url: `/ai/training-report-tasks/${taskId}/confirm`,
    method: 'POST',
  })
}

export function deleteTrainingReportTask(taskId: number) {
  return customInstance<any>({
    url: `/ai/training-report-tasks/${taskId}`,
    method: 'DELETE',
  })
}

export function getTrainingReportSnapshots(trainingId: number) {
  return customInstance<any>({
    url: `/trainings/${trainingId}/report-snapshots`,
    method: 'GET',
  })
}

export function getLatestTrainingReportSnapshot(trainingId: number) {
  return customInstance<any>({
    url: `/trainings/${trainingId}/report-snapshots/latest`,
    method: 'GET',
  })
}
