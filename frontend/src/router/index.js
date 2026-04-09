import { createRouter, createWebHistory } from 'vue-router'
import {
  TEACHING_RESOURCE_GENERATION_PAGE_PERMISSIONS,
  AI_PAPER_ASSEMBLE_PAGE_PERMISSIONS,
  AI_PAPER_GENERATE_PAGE_PERMISSIONS,
  AI_QUESTION_PAGE_PERMISSIONS,
  CERTIFICATE_PAGE_PERMISSIONS,
  COURSE_PAGE_PERMISSIONS,
  DASHBOARD_PAGE_PERMISSIONS,
  DEPARTMENT_MANAGE_PAGE_PERMISSIONS,
  DICT_MANAGE_PAGE_PERMISSIONS,
  ENROLL_MANAGE_PAGE_PERMISSIONS,
  EXAM_LIST_PAGE_PERMISSIONS,
  EXAM_MANAGE_PAGE_PERMISSIONS,
  PAPER_PAGE_PERMISSIONS,
  QUESTION_BANK_PAGE_PERMISSIONS,
  REPORT_PAGE_PERMISSIONS,
  RESOURCE_MANAGE_PAGE_PERMISSIONS,
  RESOURCE_POLICY_PAGE_PERMISSIONS,
  RESOURCE_REVIEW_PAGE_PERMISSIONS,
  ROLE_MANAGE_PAGE_PERMISSIONS,
  TALENT_PAGE_PERMISSIONS,
  TRAINING_BASE_PAGE_PERMISSIONS,
  TRAINING_MANAGE_PAGE_PERMISSIONS,
  TRAINING_PAGE_PERMISSIONS,
  TRAINING_SCHEDULE_PAGE_PERMISSIONS,
  USER_ARCHIVE_PAGE_PERMISSIONS,
  USER_MANAGE_PAGE_PERMISSIONS,
  MY_RESOURCE_PAGE_PERMISSIONS,
} from '../constants/pagePermissions'
import {
  COMMUNITY_ASSISTANT_TITLE,
  COMMUNITY_BOARD_TITLE,
  COMMUNITY_MANAGEMENT_TITLE,
  COURSE_RESOURCES_TITLE,
  MY_UPLOAD_TITLE,
} from '../constants/navigationTitles'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/auth/Login.vue'),
      meta: { layout: 'auth' },
    },
    {
      path: '/',
      component: () => import('../layouts/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('../views/dashboard/Index.vue'),
          meta: { title: '工作台', icon: 'HomeOutlined', anyPermissions: DASHBOARD_PAGE_PERMISSIONS },
        },
        {
          path: 'courses',
          name: 'CourseList',
          component: () => import('../views/courses/List.vue'),
          meta: { title: COURSE_RESOURCES_TITLE, icon: 'PlayCircleOutlined', anyPermissions: COURSE_PAGE_PERMISSIONS },
        },
        {
          path: 'courses/:id',
          name: 'CourseDetail',
          component: () => import('../views/courses/Detail.vue'),
          meta: { title: '课程详情', anyPermissions: COURSE_PAGE_PERMISSIONS },
        },
        {
          path: 'exam/list',
          name: 'ExamList',
          component: () => import('../views/exam/ExamList.vue'),
          meta: { title: '考试中心', anyPermissions: EXAM_LIST_PAGE_PERMISSIONS },
        },
        {
          path: 'exam/manage',
          name: 'ExamManage',
          component: () => import('../views/exam/ExamManage.vue'),
          meta: { title: '考试管理', anyPermissions: EXAM_MANAGE_PAGE_PERMISSIONS },
        },
        {
          path: 'paper/repository',
          name: 'PaperManage',
          component: () => import('../views/exam/PaperManage.vue'),
          meta: { title: '试卷管理', anyPermissions: PAPER_PAGE_PERMISSIONS },
        },
        {
          path: 'paper/repository/:id',
          name: 'PaperDetail',
          component: () => import('../views/exam/PaperDetail.vue'),
          meta: { title: '试卷详情', anyPermissions: PAPER_PAGE_PERMISSIONS },
        },
        {
          path: 'question/repository',
          name: 'QuestionBank',
          component: () => import('../views/exam/QuestionBank.vue'),
          meta: { title: '题库管理', anyPermissions: [...QUESTION_BANK_PAGE_PERMISSIONS, ...AI_QUESTION_PAGE_PERMISSIONS] },
        },
        {
          path: 'exam/do/:id',
          name: 'DoExam',
          component: () => import('../views/exam/Exam.vue'),
          meta: { title: '在线考试', fullscreen: true, anyPermissions: EXAM_LIST_PAGE_PERMISSIONS },
        },
        {
          path: 'exam/result/:id',
          name: 'ExamResult',
          component: () => import('../views/exam/Result.vue'),
          meta: { title: '考试结果', anyPermissions: EXAM_LIST_PAGE_PERMISSIONS },
        },
        {
          path: 'question/ai',
          name: 'AiQuestionTask',
          component: () => import('../views/exam/AiQuestionTask.vue'),
          meta: { title: '智能出题', anyPermissions: AI_QUESTION_PAGE_PERMISSIONS },
        },
        {
          path: 'paper/ai-assemble',
          name: 'AiPaperTask',
          component: () => import('../views/exam/AiPaperTask.vue'),
          meta: { title: '智能出卷', anyPermissions: [...AI_PAPER_ASSEMBLE_PAGE_PERMISSIONS, ...AI_PAPER_GENERATE_PAGE_PERMISSIONS] },
        },
        {
          path: 'paper/ai-generate',
          redirect: '/paper/ai-assemble',
        },
        {
          path: 'training',
          name: 'TrainingList',
          component: () => import('../views/training/List.vue'),
          meta: { title: '培训管理', anyPermissions: TRAINING_PAGE_PERMISSIONS },
        },
        {
          path: 'training/base',
          name: 'TrainingBaseManage',
          component: () => import('../views/training/Base.vue'),
          meta: { title: '培训基地', anyPermissions: TRAINING_BASE_PAGE_PERMISSIONS },
        },
        {
          path: 'training/plan',
          name: 'TrainingPlan',
          component: () => import('../views/training/Plan.vue'),
          meta: { title: '培训计划管理', anyPermissions: TRAINING_SCHEDULE_PAGE_PERMISSIONS },
        },
        {
          path: 'training/schedule/:id?',
          name: 'TrainingSchedule',
          component: () => import('../views/training/Schedule.vue'),
          meta: { title: '周训练计划', anyPermissions: TRAINING_SCHEDULE_PAGE_PERMISSIONS },
        },
        {
          path: 'training/ai-schedule/:id?',
          name: 'AiScheduleTask',
          component: () => import('../views/training/AiScheduleTask.vue'),
          meta: { title: '智能排课', anyPermissions: TRAINING_MANAGE_PAGE_PERMISSIONS },
        },
        {
          path: 'training/ai-schedule-file-parse',
          name: 'AiScheduleFileParse',
          component: () => import('../views/training/AiScheduleFileParse.vue'),
          meta: { title: '智能解析课表创建', anyPermissions: TRAINING_MANAGE_PAGE_PERMISSIONS },
        },
        {
          path: 'training/board',
          redirect: '/report',
        },
        {
          path: 'training/:id',
          name: 'TrainingDetail',
          component: () => import('../views/training/Detail.vue'),
          meta: { title: '培训班详情', anyPermissions: TRAINING_PAGE_PERMISSIONS },
        },
        {
          path: 'training/:id/checkout/:sessionKey?',
          name: 'Checkout',
          component: () => import('../views/training/Checkout.vue'),
          meta: { title: '签退评课' },
        },
        {
          path: 'training/:id/history',
          name: 'TrainingHistory',
          component: () => import('../views/training/History.vue'),
          meta: { title: '培训训历', anyPermissions: TRAINING_PAGE_PERMISSIONS },
        },
        {
          path: 'library',
          name: 'Library',
          component: () => import('../views/library/Index.vue'),
          meta: { title: '知识库', roles: ['admin', 'instructor', 'student'] },
        },
        {
          path: 'knowledge/scenarios',
          name: 'ScenarioTemplates',
          component: () => import('../views/knowledge/ScenarioTemplates.vue'),
          meta: { title: '场景模板管理', roles: ['admin', 'instructor'] },
        },
        // -- 社区中心 --
        {
          path: 'resource/my',
          name: 'CommunityBoard',
          component: () => import('../views/resource/CommunityBoard.vue'),
          meta: { title: COMMUNITY_BOARD_TITLE },
        },
        {
          path: 'resource/assistant',
          name: 'CommunityAssistant',
          component: () => import('../views/resource/CommunityAssistant.vue'),
          meta: { title: COMMUNITY_ASSISTANT_TITLE },
        },
        {
          path: 'resource/recommend',
          redirect: { name: 'CommunityAssistant' },
        },
        {
          path: 'resource/library',
          name: 'CommunityManagement',
          component: () => import('../views/resource/Library.vue'),
          meta: { title: COMMUNITY_MANAGEMENT_TITLE },
        },
        {
          path: 'resource/detail/:id',
          name: 'ResourceDetail',
          component: () => import('../views/resource/Detail.vue'),
          meta: { title: '资源详情' },
        },
        {
          path: 'resource/uploads',
          name: 'MyResources',
          component: () => import('../views/resource/MyResources.vue'),
          meta: { title: MY_UPLOAD_TITLE, anyPermissions: MY_RESOURCE_PAGE_PERMISSIONS },
        },
        {
          path: 'resource/teaching-generate',
          name: 'TeachingResourceGenerationTask',
          component: () => import('../views/resource/TeachingResourceGenerationTask.vue'),
          meta: { title: '教学资源生成', anyPermissions: TEACHING_RESOURCE_GENERATION_PAGE_PERMISSIONS },
        },
        {
          path: 'resource/ai-generate',
          redirect: { name: 'TeachingResourceGenerationTask' },
        },
        // -- 资源管理/审核 --
        {
          path: 'resource/manage',
          name: 'ResourceManage',
          component: () => import('../views/resource/Manage.vue'),
          meta: { title: '资源管理', anyPermissions: RESOURCE_MANAGE_PAGE_PERMISSIONS },
        },
        {
          path: 'resource/review',
          name: 'ResourceReviewQueue',
          component: () => import('../views/resource/ReviewQueue.vue'),
          meta: { title: '审核工作台', anyPermissions: RESOURCE_REVIEW_PAGE_PERMISSIONS },
        },
        {
          path: 'resource/policy',
          name: 'ResourcePolicyManage',
          component: () => import('../views/resource/PolicyManage.vue'),
          meta: { title: '审核策略', anyPermissions: RESOURCE_POLICY_PAGE_PERMISSIONS },
        },
        {
          path: 'resource/review-history',
          name: 'ResourceReviewHistory',
          component: () => import('../views/resource/ReviewHistory.vue'),
          meta: { title: '审核记录' },
        },
        {
          path: 'instructor',
          name: 'InstructorList',
          component: () => import('../views/instructor/List.vue'),
          meta: { title: '教官库', anyPermissions: USER_ARCHIVE_PAGE_PERMISSIONS },
        },
        {
          path: 'instructor/:id',
          name: 'InstructorDetail',
          component: () => import('../views/instructor/Detail.vue'),
          meta: { title: '教官详情', anyPermissions: USER_ARCHIVE_PAGE_PERMISSIONS },
        },
        {
          path: 'trainee',
          name: 'TraineeList',
          component: () => import('../views/trainee/List.vue'),
          meta: { title: '学员库', anyPermissions: USER_ARCHIVE_PAGE_PERMISSIONS },
        },
        {
          path: 'trainee/:id',
          name: 'TraineeDetail',
          component: () => import('../views/trainee/Detail.vue'),
          meta: { title: '学员详情', anyPermissions: USER_ARCHIVE_PAGE_PERMISSIONS },
        },
        {
          path: 'talent',
          name: 'Talent',
          component: () => import('../views/talent/Index.vue'),
          meta: { title: '人才库', anyPermissions: TALENT_PAGE_PERMISSIONS },
        },
        {
          path: 'report',
          name: 'Report',
          component: () => import('../views/report/DataBoard.vue'),
          meta: { title: '数据看板', anyPermissions: REPORT_PAGE_PERMISSIONS },
        },
        {
          path: 'report/exam',
          name: 'ExamStatisticsBoard',
          component: () => import('../views/report/DataBoard.vue'),
          meta: { title: '考试统计', anyPermissions: REPORT_PAGE_PERMISSIONS, reportCategory: 'exam' },
        },
        {
          path: 'system/dashboard-modules',
          name: 'DashboardModuleManage',
          component: () => import('../views/system/DashboardModuleManage.vue'),
          meta: { title: '看板配置', roles: ['admin'] },
        },
        {
          path: 'system/users',
          name: 'UserManage',
          component: () => import('../views/system/UserManage.vue'),
          meta: { title: '用户管理', anyPermissions: USER_MANAGE_PAGE_PERMISSIONS },
        },
        {
          path: 'system/roles',
          name: 'RoleManage',
          component: () => import('../views/system/RoleManage.vue'),
          meta: { title: '角色管理', anyPermissions: ROLE_MANAGE_PAGE_PERMISSIONS },
        },
        {
          path: 'system/departments',
          name: 'DepartmentManage',
          component: () => import('../views/system/DepartmentManage.vue'),
          meta: { title: '部门管理', anyPermissions: DEPARTMENT_MANAGE_PAGE_PERMISSIONS },
        },
        {
          path: 'system/notices',
          name: 'NoticeManage',
          component: () => import('../views/system/NoticeManage.vue'),
          meta: { title: '通知管理', roles: ['admin'] },
        },
        {
          path: 'system/configs',
          name: 'ConfigManage',
          component: () => import('../views/system/ConfigManage.vue'),
          meta: { title: '配置管理', roles: ['admin'] },
        },
        {
          path: 'system/dict',
          name: 'DictManage',
          component: () => import('../views/system/DictManage.vue'),
          meta: { title: '字典管理', anyPermissions: DICT_MANAGE_PAGE_PERMISSIONS },
        },
        {
          path: 'evaluation',
          name: 'EvaluationManage',
          component: () => import('../views/evaluation/EvaluationManage.vue'),
          meta: { title: '评价管理' },
        },
        {
          path: 'profile',
          name: 'Profile',
          component: () => import('../views/profile/Index.vue'),
          meta: { title: '个人中心' },
        },
        {
          path: 'training/:id/enroll',
          name: 'Enroll',
          component: () => import('../views/training/Enroll.vue'),
          meta: { title: '报名申请', roles: ['student'] },
        },
        {
          path: 'training/:id/enroll/manage',
          name: 'EnrollManage',
          component: () => import('../views/training/EnrollManage.vue'),
          meta: { title: '报名审核', anyPermissions: ENROLL_MANAGE_PAGE_PERMISSIONS },
        },
        {
          path: 'exam/scores',
          name: 'ExamScores',
          component: () => import('../views/exam/Scores.vue'),
          meta: { title: '成绩管理', anyPermissions: EXAM_MANAGE_PAGE_PERMISSIONS },
        },
        {
          path: 'certificate',
          name: 'Certificate',
          component: () => import('../views/certificate/Index.vue'),
          meta: { title: '结业证书', anyPermissions: CERTIFICATE_PAGE_PERMISSIONS },
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/login' },
  ],
})

function getCachedUser() {
  const userInfo = localStorage.getItem('userInfo')
  if (!userInfo) return null
  try {
    return JSON.parse(userInfo)
  } catch {
    return null
  }
}

function getCachedPermissions() {
  return Array.isArray(getCachedUser()?.permissions) ? getCachedUser().permissions : []
}

function hasAnyPermission(permissionList) {
  const list = Array.isArray(permissionList)
    ? permissionList.filter(Boolean)
    : [permissionList].filter(Boolean)
  if (!list.length) return true
  const permissions = getCachedPermissions()
  return list.some((permission) => permissions.includes(permission))
}

function hasAllPermissions(permissionList) {
  const list = Array.isArray(permissionList)
    ? permissionList.filter(Boolean)
    : [permissionList].filter(Boolean)
  if (!list.length) return true
  const permissions = getCachedPermissions()
  return list.every((permission) => permissions.includes(permission))
}

function hasAllowedRole(roleList) {
  const list = Array.isArray(roleList)
    ? roleList.filter(Boolean)
    : [roleList].filter(Boolean)
  if (!list.length) return true

  const user = getCachedUser()
  const roleCodes = Array.isArray(user?.roleCodes) ? user.roleCodes : []
  const activeRoles = new Set([user?.role, ...roleCodes].filter(Boolean))
  return list.some((role) => activeRoles.has(role))
}

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return '/login'
  }
  if (to.path === '/login' && token) {
    return '/'
  }
  if (!token) {
    return true
  }

  if (to.meta.anyPermissions && !hasAnyPermission(to.meta.anyPermissions)) {
    return '/login'
  }
  if (to.meta.allPermissions && !hasAllPermissions(to.meta.allPermissions)) {
    return '/login'
  }
  if (to.meta.roles && !hasAllowedRole(to.meta.roles)) {
    return '/login'
  }
  return true
})

export default router
