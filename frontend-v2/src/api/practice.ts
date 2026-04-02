import type {
  KnowledgePointResponse,
  PoliceTypeSimpleResponse,
  QuestionResponse,
} from '@/api/generated/model'
import { customInstance } from '@/api/custom-instance'

export interface PracticeQuestionFolder {
  id: number
  name: string
  category?: string | null
  parent_id?: number | null
  sort_order?: number
  question_count?: number
  paper_count?: number
  exercise_count?: number
  status?: string
  created_by?: number | null
  created_by_name?: string | null
  created_at?: string
  updated_at?: string
  children?: PracticeQuestionFolder[]
}

export interface PracticeSourcesResponse {
  knowledge_points: KnowledgePointResponse[]
  question_folders: PracticeQuestionFolder[]
  police_types: PoliceTypeSimpleResponse[]
}

export interface PaginatedResponse<T> {
  page: number
  size: number
  total: number
  items: T[]
}

export interface GetPracticeQuestionsParams {
  page?: number
  size?: number
  search?: string
  type?: string
  difficulty?: number
  police_type_id?: number
  knowledge_point_id?: number
  folder_id?: number
  recursive?: boolean
}

export async function getPracticeSources() {
  return customInstance<PracticeSourcesResponse>({
    url: '/practice/sources',
    method: 'GET',
  })
}

export async function getPracticeQuestions(params?: GetPracticeQuestionsParams) {
  return customInstance<PaginatedResponse<QuestionResponse>>({
    url: '/practice/questions',
    method: 'GET',
    params,
  })
}
