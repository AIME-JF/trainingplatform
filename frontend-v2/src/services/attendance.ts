import { customInstance } from '@/api/custom-instance'
import type {
  CheckinResponse,
  TrainingCheckinQrResponse,
} from '@/api/generated/model'

export interface AttendanceQrParams {
  session_key?: string
  date?: string
  action?: 'checkin' | 'checkout'
}

export function getAttendanceQr(trainingId: number, params?: AttendanceQrParams) {
  return customInstance<TrainingCheckinQrResponse>({
    url: `/trainings/${trainingId}/attendance/qr`,
    method: 'GET',
    params,
  })
}

export function getAttendanceQrPayload(token: string) {
  return customInstance<TrainingCheckinQrResponse>({
    url: `/trainings/attendance/qr/${token}`,
    method: 'GET',
  })
}

export function submitAttendanceByQr(token: string) {
  return customInstance<CheckinResponse>({
    url: `/trainings/attendance/qr/${token}`,
    method: 'POST',
  })
}
