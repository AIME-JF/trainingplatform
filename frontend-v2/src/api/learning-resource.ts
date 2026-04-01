import type {
  AITaskSummaryResponse,
  CourseCreate,
  CourseLearningStatusResponse,
  CourseListResponse,
  CourseNoteResponse,
  CourseNoteUpdate,
  CourseProgressUpdate,
  CourseQACreate,
  CourseQAResponse,
  CourseResourceBindRequest,
  CourseResponse,
  CourseTagCreate,
  CourseTagResponse,
  CourseUpdate,
  DepartmentSimpleResponse,
  GetCourseTagsApiV1CoursesTagsGetParams,
  GetCoursesApiV1CoursesGetParams,
  GetDepartmentListApiV1DepartmentsListGetParams,
  GetFeedApiV1ResourcesRecommendationsFeedGetParams,
  GetResourcesApiV1ResourcesGetParams,
  GetResourceTagsApiV1ResourcesTagsGetParams,
  GetReviewTasksApiV1ReviewsTasksGetParams,
  GetRoleListApiV1RolesListGetParams,
  GetUsersApiV1UsersGetParams,
  MediaFileResponse,
  PaginatedResponseAITaskSummaryResponse,
  PaginatedResponseCourseListResponse,
  PaginatedResponseDepartmentSimpleResponse,
  PaginatedResponseResourceListItemResponse,
  PaginatedResponseRoleSimpleResponse,
  PaginatedResponseUserSimpleResponse,
  ResourceBehaviorEventCreateEventType,
  ResourceCommentCreate,
  ResourceCommentResponse,
  ResourceCreate,
  ResourceDetailResponse as GeneratedResourceDetailResponse,
  ResourceLikeStatusResponse,
  ResourceListItemResponse as GeneratedResourceListItemResponse,
  ResourceRecommendationFeedResponse as GeneratedResourceRecommendationFeedResponse,
  ResourceRecommendationItem as GeneratedResourceRecommendationItem,
  ResourceShareStatusResponse,
  ResourceTagCreate,
  ResourceTagResponse,
  ResourceUpdate,
  ReviewTaskResponse,
  ReviewWorkflowResponse,
  RoleSimpleResponse,
  TeachingResourceGenerationMetaUpdateRequest,
  TeachingResourceGenerationTaskCreateRequest,
  TeachingResourceGenerationTaskDetailResponse,
  UserSimpleResponse,
} from '@/api/generated/model'
import {
  createTeachingResourceGenerationTaskApiV1AiTeachingResourceGenerationTasksPost,
  confirmTeachingResourceGenerationTaskApiV1AiTeachingResourceGenerationTasksTaskIdConfirmPost,
  getTeachingResourceGenerationTaskDetailApiV1AiTeachingResourceGenerationTasksTaskIdGet,
  listTeachingResourceGenerationTasksApiV1AiTeachingResourceGenerationTasksGet,
  updateTeachingResourceGenerationTaskMetaApiV1AiTeachingResourceGenerationTasksTaskIdResourceMetaPut,
} from '@/api/generated/ai-tasks/ai-tasks'
import {
  createCourseApiV1CoursesPost,
  createCourseQaApiV1CoursesCourseIdQaPost,
  createCourseTagApiV1CoursesTagsPost,
  deleteCourseApiV1CoursesCourseIdDelete,
  getCourseApiV1CoursesCourseIdGet,
  getCourseLearningStatusApiV1CoursesCourseIdLearningStatusGet,
  getCourseNoteApiV1CoursesCourseIdNoteGet,
  getCourseQaApiV1CoursesCourseIdQaGet,
  getCoursesApiV1CoursesGet,
  getCourseTagsApiV1CoursesTagsGet,
  listCourseResourcesApiV1CoursesCourseIdResourcesGet,
  addCourseResourceApiV1CoursesCourseIdResourcesPost,
  removeCourseResourceApiV1CoursesCourseIdResourcesResourceIdDelete,
  updateChapterProgressApiV1CoursesCourseIdChaptersChapterIdProgressPut,
  updateCourseNoteApiV1CoursesCourseIdNotePut,
  updateCourseApiV1CoursesCourseIdPut,
} from '@/api/generated/course-management/course-management'
import { uploadFileApiV1MediaUploadPost } from '@/api/generated/media-management/media-management'
import {
  createResourceApiV1ResourcesPost,
  createResourceCommentApiV1ResourcesResourceIdCommentsPost,
  createResourceTagApiV1ResourcesTagsPost,
  deleteResourceCommentApiV1ResourcesResourceIdCommentsCommentIdDelete,
  deleteResourceApiV1ResourcesResourceIdDelete,
  getResourceApiV1ResourcesResourceIdGet,
  getResourceCommentsApiV1ResourcesResourceIdCommentsGet,
  getResourcesApiV1ResourcesGet,
  getResourceTagsApiV1ResourcesTagsGet,
  offlineResourceApiV1ResourcesResourceIdOfflinePost,
  publishResourceApiV1ResourcesResourceIdPublishPost,
  updateResourceApiV1ResourcesResourceIdPut,
} from '@/api/generated/resource-library/resource-library'
import {
  getFeedApiV1ResourcesRecommendationsFeedGet,
  likeResourceApiV1ResourcesResourceIdLikesPost,
  recordEventApiV1ResourcesResourceIdEventsPost,
  shareResourceApiV1ResourcesResourceIdSharePost,
  unlikeResourceApiV1ResourcesResourceIdLikesDelete,
} from '@/api/generated/resource-recommendation/resource-recommendation'
import {
  getReviewTasksApiV1ReviewsTasksGet,
  getWorkflowApiV1ReviewsWorkflowsResourceIdGet,
  submitResourceApiV1ResourcesResourceIdSubmitPost,
} from '@/api/generated/resource-review/resource-review'
import {
  getDepartmentListApiV1DepartmentsListGet,
} from '@/api/generated/department-management/department-management'
import {
  getRoleListApiV1RolesListGet,
} from '@/api/generated/role-management/role-management'
import {
  getUsersApiV1UsersGet,
} from '@/api/generated/user-management/user-management'

export type {
  AITaskSummaryResponse,
  CourseCreate,
  CourseLearningStatusResponse,
  CourseListResponse,
  CourseNoteResponse,
  CourseNoteUpdate,
  CourseProgressUpdate,
  CourseQACreate,
  CourseQAResponse,
  CourseResourceBindRequest,
  CourseResponse,
  CourseTagResponse,
  CourseUpdate,
  DepartmentSimpleResponse,
  MediaFileResponse,
  PaginatedResponseAITaskSummaryResponse,
  PaginatedResponseCourseListResponse,
  PaginatedResponseDepartmentSimpleResponse,
  PaginatedResponseResourceListItemResponse,
  PaginatedResponseRoleSimpleResponse,
  PaginatedResponseUserSimpleResponse,
  ResourceBehaviorEventCreateEventType,
  ResourceCommentCreate,
  ResourceCommentResponse,
  ResourceCreate,
  ResourceLikeStatusResponse,
  ResourceTagResponse,
  ResourceUpdate,
  ReviewTaskResponse,
  ReviewWorkflowResponse,
  RoleSimpleResponse,
  TeachingResourceGenerationMetaUpdateRequest,
  TeachingResourceGenerationTaskCreateRequest,
  TeachingResourceGenerationTaskDetailResponse,
  ResourceShareStatusResponse,
  UserSimpleResponse,
}

export type ResourceListItemResponse = GeneratedResourceListItemResponse

export type ResourceDetailResponse = GeneratedResourceDetailResponse

export type PaginatedResourceListResponse = PaginatedResponseResourceListItemResponse

export type ResourceRecommendationItem = GeneratedResourceRecommendationItem

export type ResourceRecommendationFeed = GeneratedResourceRecommendationFeedResponse

export async function listResources(params?: GetResourcesApiV1ResourcesGetParams) {
  return (await getResourcesApiV1ResourcesGet(params)) as PaginatedResourceListResponse
}

export async function getResourceDetail(resourceId: number) {
  return (await getResourceApiV1ResourcesResourceIdGet(resourceId)) as ResourceDetailResponse
}

export async function createResource(resource: ResourceCreate) {
  return (await createResourceApiV1ResourcesPost(resource)) as ResourceDetailResponse
}

export async function updateResource(resourceId: number, resource: ResourceUpdate) {
  return (await updateResourceApiV1ResourcesResourceIdPut(resourceId, resource)) as ResourceDetailResponse
}

export async function publishResource(resourceId: number) {
  return (await publishResourceApiV1ResourcesResourceIdPublishPost(resourceId)) as ResourceDetailResponse
}

export async function offlineResource(resourceId: number) {
  return (await offlineResourceApiV1ResourcesResourceIdOfflinePost(resourceId)) as ResourceDetailResponse
}

export async function removeResource(resourceId: number) {
  return deleteResourceApiV1ResourcesResourceIdDelete(resourceId)
}

export async function listResourceTags(params?: GetResourceTagsApiV1ResourcesTagsGetParams) {
  return (await getResourceTagsApiV1ResourcesTagsGet(params)) as ResourceTagResponse[]
}

export async function createResourceTag(tag: ResourceTagCreate) {
  return (await createResourceTagApiV1ResourcesTagsPost(tag)) as ResourceTagResponse
}

export async function uploadMediaFile(file: File, durationSeconds?: number) {
  return (await uploadFileApiV1MediaUploadPost({
    file,
    duration_seconds: durationSeconds,
  })) as MediaFileResponse
}

export async function submitResourceReview(resourceId: number) {
  return (await submitResourceApiV1ResourcesResourceIdSubmitPost(resourceId)) as ReviewWorkflowResponse
}

export async function getReviewWorkflow(resourceId: number) {
  return (await getWorkflowApiV1ReviewsWorkflowsResourceIdGet(resourceId)) as ReviewWorkflowResponse
}

export async function listReviewTasks(params?: GetReviewTasksApiV1ReviewsTasksGetParams) {
  return (await getReviewTasksApiV1ReviewsTasksGet(params)) as ReviewTaskResponse[]
}

export async function listRecommendationFeed(params?: GetFeedApiV1ResourcesRecommendationsFeedGetParams) {
  const feed = await getFeedApiV1ResourcesRecommendationsFeedGet(params)
  return feed || {
    items: [],
    page: params?.page || 1,
    size: params?.size || 10,
    total: 0,
  }
}

export async function recordResourceEvent(resourceId: number, eventType: ResourceBehaviorEventCreateEventType) {
  return recordEventApiV1ResourcesResourceIdEventsPost(resourceId, { event_type: eventType })
}

export async function likeResource(resourceId: number) {
  return likeResourceApiV1ResourcesResourceIdLikesPost(resourceId) as Promise<ResourceLikeStatusResponse>
}

export async function unlikeResource(resourceId: number) {
  return unlikeResourceApiV1ResourcesResourceIdLikesDelete(resourceId) as Promise<ResourceLikeStatusResponse>
}

export async function shareResource(resourceId: number) {
  return shareResourceApiV1ResourcesResourceIdSharePost(resourceId) as Promise<ResourceShareStatusResponse>
}

export async function listResourceComments(resourceId: number) {
  const comments = await getResourceCommentsApiV1ResourcesResourceIdCommentsGet(resourceId)
  return comments || []
}

export async function createResourceComment(resourceId: number, payload: ResourceCommentCreate) {
  return createResourceCommentApiV1ResourcesResourceIdCommentsPost(resourceId, payload) as Promise<ResourceCommentResponse>
}

export async function deleteResourceComment(resourceId: number, commentId: number) {
  return deleteResourceCommentApiV1ResourcesResourceIdCommentsCommentIdDelete(resourceId, commentId) as Promise<{ success?: boolean }>
}

export async function listCourses(params?: GetCoursesApiV1CoursesGetParams) {
  return (await getCoursesApiV1CoursesGet(params)) as PaginatedResponseCourseListResponse
}

export async function getCourseDetail(courseId: number) {
  return (await getCourseApiV1CoursesCourseIdGet(courseId)) as CourseResponse
}

export async function createCourse(course: CourseCreate) {
  return (await createCourseApiV1CoursesPost(course)) as CourseResponse
}

export async function updateCourse(courseId: number, course: CourseUpdate) {
  return (await updateCourseApiV1CoursesCourseIdPut(courseId, course)) as CourseResponse
}

export async function deleteCourse(courseId: number) {
  return deleteCourseApiV1CoursesCourseIdDelete(courseId)
}

export async function listCourseTags(params?: GetCourseTagsApiV1CoursesTagsGetParams) {
  return (await getCourseTagsApiV1CoursesTagsGet(params)) as CourseTagResponse[]
}

export async function createCourseTag(tag: CourseTagCreate) {
  return (await createCourseTagApiV1CoursesTagsPost(tag)) as CourseTagResponse
}

export async function listCourseResources(courseId: number) {
  return (await listCourseResourcesApiV1CoursesCourseIdResourcesGet(courseId)) as ResourceListItemResponse[]
}

export async function bindCourseResource(courseId: number, payload: CourseResourceBindRequest) {
  return (await addCourseResourceApiV1CoursesCourseIdResourcesPost(courseId, payload)) as ResourceListItemResponse
}

export async function unbindCourseResource(courseId: number, resourceId: number) {
  return removeCourseResourceApiV1CoursesCourseIdResourcesResourceIdDelete(courseId, resourceId)
}

export async function updateCourseChapterProgress(courseId: number, chapterId: number, payload: CourseProgressUpdate) {
  return updateChapterProgressApiV1CoursesCourseIdChaptersChapterIdProgressPut(courseId, chapterId, payload)
}

export async function getCourseNote(courseId: number) {
  return (await getCourseNoteApiV1CoursesCourseIdNoteGet(courseId)) as CourseNoteResponse
}

export async function updateCourseNote(courseId: number, payload: CourseNoteUpdate) {
  return (await updateCourseNoteApiV1CoursesCourseIdNotePut(courseId, payload)) as CourseNoteResponse
}

export async function listCourseQa(courseId: number) {
  return (await getCourseQaApiV1CoursesCourseIdQaGet(courseId)) as CourseQAResponse[]
}

export async function createCourseQuestion(courseId: number, payload: CourseQACreate) {
  return (await createCourseQaApiV1CoursesCourseIdQaPost(courseId, payload)) as CourseQAResponse
}

export async function getCourseLearningStatus(courseId: number) {
  return (await getCourseLearningStatusApiV1CoursesCourseIdLearningStatusGet(courseId)) as CourseLearningStatusResponse[]
}

export async function listTeachingResourceGenerationTasks(params?: { page?: number; size?: number; status?: string }) {
  return (await listTeachingResourceGenerationTasksApiV1AiTeachingResourceGenerationTasksGet(params)) as PaginatedResponseAITaskSummaryResponse
}

export async function createTeachingResourceGenerationTask(payload: TeachingResourceGenerationTaskCreateRequest) {
  return (await createTeachingResourceGenerationTaskApiV1AiTeachingResourceGenerationTasksPost(payload)) as TeachingResourceGenerationTaskDetailResponse
}

export async function getTeachingResourceGenerationTaskDetail(taskId: number) {
  return (await getTeachingResourceGenerationTaskDetailApiV1AiTeachingResourceGenerationTasksTaskIdGet(taskId)) as TeachingResourceGenerationTaskDetailResponse
}

export async function updateTeachingResourceGenerationTaskMeta(taskId: number, payload: TeachingResourceGenerationMetaUpdateRequest) {
  return (await updateTeachingResourceGenerationTaskMetaApiV1AiTeachingResourceGenerationTasksTaskIdResourceMetaPut(taskId, payload)) as TeachingResourceGenerationTaskDetailResponse
}

export async function confirmTeachingResourceGenerationTask(taskId: number) {
  return (await confirmTeachingResourceGenerationTaskApiV1AiTeachingResourceGenerationTasksTaskIdConfirmPost(taskId)) as TeachingResourceGenerationTaskDetailResponse
}

export async function listUsers(params?: GetUsersApiV1UsersGetParams) {
  return (await getUsersApiV1UsersGet(params)) as PaginatedResponseUserSimpleResponse
}

export async function listDepartments(params?: GetDepartmentListApiV1DepartmentsListGetParams) {
  return (await getDepartmentListApiV1DepartmentsListGet(params)) as PaginatedResponseDepartmentSimpleResponse
}

export async function listRoles(params?: GetRoleListApiV1RolesListGetParams) {
  return (await getRoleListApiV1RolesListGet(params)) as PaginatedResponseRoleSimpleResponse
}
