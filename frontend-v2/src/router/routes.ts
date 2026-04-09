import type { RouteRecordRaw } from 'vue-router'
import {
  DASHBOARD_PERMISSIONS,
  REPORT_PERMISSIONS,
  TRAINING_PERMISSIONS,
  TRAINING_SCHEDULE_PERMISSIONS,
  COURSE_PERMISSIONS,
  TEACHING_RESOURCE_GENERATION_PERMISSIONS,
} from '@/constants/permissions'
import { COURSE_RESOURCES_TITLE } from '@/constants/navigationTitles'

const MobileLayout = () => import('@/layouts/MobileLayout.vue')
const AuthLayout = () => import('@/layouts/AuthLayout.vue')

export const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    component: AuthLayout,
    children: [
      {
        path: '',
        name: 'Login',
        component: () => import('@/views/auth/Login.vue'),
        meta: { title: '登录' },
      },
    ],
  },
  {
    path: '/attendance/:token/:sessionKey?',
    name: 'AttendanceScan',
    component: () => import('@/views/attendance/Scan.vue'),
    meta: { title: '扫码出勤' },
  },
  {
    path: '/',
    component: MobileLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '工作台', anyPermissions: DASHBOARD_PERMISSIONS },
      },
      {
        path: 'calendar',
        redirect: { name: 'ClassSchedule' },
      },
      {
        path: 'classes',
        name: 'ClassList',
        component: () => import('@/views/classes/List.vue'),
        meta: { title: '班级列表', anyPermissions: TRAINING_PERMISSIONS },
      },
      {
        path: 'classes/:id',
        name: 'ClassDetail',
        component: () => import('@/views/classes/Detail.vue'),
        meta: { title: '班级详情', anyPermissions: TRAINING_PERMISSIONS },
      },
      {
        path: 'classes/schedule/:id?',
        name: 'ClassSchedule',
        component: () => import('@/views/classes/Schedule.vue'),
        meta: { title: '周训练计划', anyPermissions: TRAINING_SCHEDULE_PERMISSIONS },
      },
      {
        path: 'classes/:id/enroll',
        name: 'ClassEnroll',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '报名', roles: ['student'] },
      },
      {
        path: 'classes/:id/checkin',
        name: 'ClassCheckin',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '签到' },
      },
      {
        path: 'classes/:id/checkout',
        name: 'ClassCheckout',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '签退' },
      },
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('@/views/notification/Index.vue'),
        meta: { title: '通知中心' },
      },
      {
        path: 'exam/list',
        name: 'ExamList',
        component: () => import('@/views/exam/List.vue'),
        meta: { title: '在线考试' },
      },
      {
        path: 'exam/overview/:id',
        name: 'ExamOverview',
        component: () => import('@/views/exam/ExamOverview.vue'),
        meta: { title: '考试概览' },
      },
      {
        path: 'exam/do/:id',
        name: 'ExamDo',
        component: () => import('@/views/exam/Do.vue'),
        meta: { title: '考试作答' },
      },
      {
        path: 'exam/result/:id',
        name: 'ExamResult',
        component: () => import('@/views/exam/Result.vue'),
        meta: { title: '考试结果' },
      },
      {
        path: 'report/exam',
        name: 'ExamStatistics',
        component: () => import('@/views/report/ExamStatistics.vue'),
        meta: { title: '考试统计', anyPermissions: REPORT_PERMISSIONS },
      },
      {
        path: 'practice',
        name: 'Practice',
        component: () => import('@/views/practice/Index.vue'),
        meta: { title: '刷题练习' },
      },
      {
        path: 'practice/do',
        name: 'PracticeDo',
        component: () => import('@/views/practice/Do.vue'),
        meta: { title: '答题' },
      },
      {
        path: 'knowledge/courses',
        name: 'KnowledgeCourses',
        component: () => import('@/views/knowledge/Courses.vue'),
        meta: { title: COURSE_RESOURCES_TITLE, anyPermissions: COURSE_PERMISSIONS },
      },
      {
        path: 'knowledge/courses/:id',
        name: 'CourseDetail',
        component: () => import('@/views/knowledge/CourseDetail.vue'),
        meta: { title: '课程详情', anyPermissions: COURSE_PERMISSIONS },
      },
      {
        path: 'knowledge/teaching-generate',
        name: 'TeachingResourceGenerationTask',
        component: () => import('@/views/knowledge/TeachingResourceGenerationTask.vue'),
        meta: { title: '教学资源生成', anyPermissions: TEACHING_RESOURCE_GENERATION_PERMISSIONS },
      },
      {
        path: 'knowledge/ai-generate',
        redirect: { name: 'TeachingResourceGenerationTask' },
      },
      {
        path: 'knowledge/assistant',
        name: 'KnowledgeAssistant',
        component: () => import('@/views/knowledge/assistant/Index.vue'),
        meta: { title: '知识助手' },
      },
      {
        path: 'knowledge/assistant/chat',
        name: 'KnowledgeAssistantChat',
        component: () => import('@/views/knowledge/assistant/Chat.vue'),
        meta: { title: '知识问答' },
      },
      {
        path: 'knowledge/assistant/chat/:legacyKnowledgeBaseId',
        redirect: (to) => ({
          path: '/knowledge/assistant/chat',
          query: to.query,
        }),
      },
      {
        path: 'knowledge/assistant/scenario-sim/:scenarioId?',
        name: 'KnowledgeScenarioSim',
        component: () => import('@/views/knowledge/assistant/ScenarioSim.vue'),
        meta: { title: '场景模拟训练' },
      },
      {
        path: 'knowledge/scenarios',
        name: 'KnowledgeScenarios',
        component: () => import('@/views/knowledge/scenarios/Index.vue'),
        meta: { title: '场景模板管理', roles: ['admin', 'instructor'] },
      },
      {
        path: 'knowledge/scenarios/create',
        name: 'KnowledgeScenarioCreate',
        component: () => import('@/views/knowledge/scenarios/Editor.vue'),
        meta: { title: '创建场景模板', roles: ['admin', 'instructor'] },
      },
      {
        path: 'knowledge/scenarios/:id/edit',
        name: 'KnowledgeScenarioEdit',
        component: () => import('@/views/knowledge/scenarios/Editor.vue'),
        meta: { title: '编辑场景模板', roles: ['admin', 'instructor'] },
      },
      {
        path: 'knowledge/scenarios/:id/records',
        name: 'KnowledgeScenarioRecords',
        component: () => import('@/views/knowledge/scenarios/Records.vue'),
        meta: { title: '模拟记录', roles: ['admin', 'instructor'] },
      },
      {
        path: 'knowledge/records',
        name: 'KnowledgeRecords',
        component: () => import('@/views/knowledge/records/Index.vue'),
        meta: { title: '学习记录' },
      },
      {
        path: 'resource/library',
        name: 'ResourceLibrary',
        component: () => import('@/views/knowledge/Library.vue'),
        meta: { title: '社区精选' },
      },
      {
        path: 'resource/community',
        name: 'ResourceCommunity',
        component: () => import('@/views/knowledge/Recommend.vue'),
        meta: { title: '资源社区' },
      },
      {
        path: 'resource/recommend',
        redirect: { name: 'ResourceCommunity' },
      },
      {
        path: 'resource/detail/:id',
        name: 'ResourceDetail',
        component: () => import('@/views/knowledge/Detail.vue'),
        meta: { title: '资源详情' },
      },
      {
        path: 'resource/my',
        name: 'MyResources',
        component: () => import('@/views/knowledge/MyResources.vue'),
        meta: { title: '我的空间' },
      },
      {
        path: 'library',
        name: 'Library',
        component: () => import('@/views/library/Index.vue'),
        meta: { title: '知识库', roles: ['admin', 'instructor', 'student'] },
      },
      { path: 'resource/courses', redirect: { name: 'KnowledgeCourses' } },
      { path: 'resource/courses/:id', redirect: '/knowledge/courses/:id' },
      { path: 'resource/teaching-generate', redirect: { name: 'TeachingResourceGenerationTask' } },
      { path: 'resource/ai-generate', redirect: { name: 'TeachingResourceGenerationTask' } },
      {
        path: 'evaluation',
        name: 'EvaluationCenter',
        component: () => import('@/views/evaluation/Index.vue'),
        meta: { title: '问卷中心' },
      },
      {
        path: 'evaluation/fill/:taskId',
        name: 'EvaluationFill',
        component: () => import('@/views/evaluation/Fill.vue'),
        meta: { title: '问卷填写' },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/Index.vue'),
        meta: { title: '个人中心' },
      },
    ],
  },
]
