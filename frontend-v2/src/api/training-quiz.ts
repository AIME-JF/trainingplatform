import { customInstance } from './custom-instance'

export function createTrainingQuiz(trainingId: number, data: Record<string, unknown>) {
  return customInstance<any>({
    url: `/trainings/${trainingId}/quizzes`,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    data,
  })
}

export function updateTrainingQuiz(trainingId: number, examId: number, data: Record<string, unknown>) {
  return customInstance<any>({
    url: `/trainings/${trainingId}/quizzes/${examId}`,
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    data,
  })
}

export function deleteTrainingQuiz(trainingId: number, examId: number) {
  return customInstance<any>({
    url: `/trainings/${trainingId}/quizzes/${examId}`,
    method: 'DELETE',
  })
}
