import type { RouteRecordRaw } from 'vue-router'
import {
  DASHBOARD_PERMISSIONS,
  TRAINING_PERMISSIONS,
  TRAINING_SCHEDULE_PERMISSIONS,
  EXAM_LIST_PERMISSIONS,
  COURSE_PERMISSIONS,
  MY_RESOURCE_PERMISSIONS,
  TEACHING_RESOURCE_GENERATION_PERMISSIONS,
} from '@/constants/permissions'

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
    path: '/',
    component: MobileLayout,
    meta: { requiresAuth: true },
    children: [
      // -- 首页 --
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
      // -- 班级 --
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
      // -- 考试 --
      {
        path: 'exam/list',
        name: 'ExamList',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '在线考试', anyPermissions: EXAM_LIST_PERMISSIONS },
      },
      {
        path: 'exam/do/:id',
        name: 'ExamDo',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '考试作答' },
      },
      {
        path: 'exam/result/:id',
        name: 'ExamResult',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '考试结果' },
      },
      // -- 资源 --
      {
        path: 'resource/courses',
        name: 'LearningCourses',
        component: () => import('@/views/resource/Courses.vue'),
        meta: { title: '学习资源', anyPermissions: COURSE_PERMISSIONS },
      },
      {
        path: 'resource/courses/:id',
        name: 'CourseDetail',
        component: () => import('@/views/resource/CourseDetail.vue'),
        meta: { title: '课程资源详情', anyPermissions: COURSE_PERMISSIONS },
      },
      {
        path: 'resource/library',
        name: 'ResourceLibrary',
        component: () => import('@/views/resource/Library.vue'),
        meta: { title: '资源库' },
      },
      {
        path: 'resource/community',
        name: 'ResourceCommunity',
        component: () => import('@/views/resource/Recommend.vue'),
        meta: { title: '资源社区' },
      },
      {
        path: 'resource/recommend',
        redirect: { name: 'ResourceCommunity' },
      },
      {
        path: 'resource/detail/:id',
        name: 'ResourceDetail',
        component: () => import('@/views/resource/Detail.vue'),
        meta: { title: '资源详情' },
      },
      {
        path: 'resource/my',
        name: 'MyResources',
        component: () => import('@/views/resource/MyResources.vue'),
        meta: { title: '我的资源', anyPermissions: MY_RESOURCE_PERMISSIONS },
      },
      {
        path: 'resource/teaching-generate',
        name: 'TeachingResourceGenerationTask',
        component: () => import('@/views/resource/TeachingResourceGenerationTask.vue'),
        meta: { title: '教学资源生成', anyPermissions: TEACHING_RESOURCE_GENERATION_PERMISSIONS },
      },
      {
        path: 'resource/ai-generate',
        redirect: { name: 'TeachingResourceGenerationTask' },
      },
      // -- 个人中心 --
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '个人中心' },
      },
    ],
  },
]
