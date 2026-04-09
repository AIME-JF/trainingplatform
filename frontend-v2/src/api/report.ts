import { customInstance } from './custom-instance'
import {
  getCityRankingApiV1ReportCityRankingGet,
  getKpiApiV1ReportKpiGet,
  getPoliceTypeDistributionApiV1ReportPoliceTypeDistributionGet,
  getTrainingCityAttendanceApiV1ReportTrainingCityAttendanceGet,
  getTrainingCityCompletionApiV1ReportTrainingCityCompletionGet,
  getTrainingTrendApiV1ReportTrainingTrendGet,
  getTrendApiV1ReportTrendGet,
} from './generated/reporting/reporting'

export const getReportKpi = getKpiApiV1ReportKpiGet
export const getReportTrend = getTrendApiV1ReportTrendGet
export const getTrainingTrend = getTrainingTrendApiV1ReportTrainingTrendGet
export const getTrainingCityAttendance = getTrainingCityAttendanceApiV1ReportTrainingCityAttendanceGet
export const getTrainingCityCompletion = getTrainingCityCompletionApiV1ReportTrainingCityCompletionGet
export const getPoliceTypeDistribution = getPoliceTypeDistributionApiV1ReportPoliceTypeDistributionGet
export const getCityRanking = getCityRankingApiV1ReportCityRankingGet

export function getExamStatistics(params: Record<string, unknown>) {
  return customInstance<any>({
    url: '/exams/statistics',
    method: 'GET',
    params,
  })
}
