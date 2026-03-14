import { createRouter, createWebHistory } from 'vue-router'

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
          meta: { title: '工作台', icon: 'HomeOutlined' },
        },
        {
          path: 'courses',
          name: 'CourseList',
          component: () => import('../views/courses/List.vue'),
          meta: { title: '课程学习', icon: 'PlayCircleOutlined' },
        },
        {
          path: 'courses/:id',
          name: 'CourseDetail',
          component: () => import('../views/courses/Detail.vue'),
          meta: { title: '课程详情' },
        },
        {
          path: 'exam/list',
          name: 'ExamList',
          component: () => import('../views/exam/ExamList.vue'),
          meta: { title: '参加考试' },
        },
        {
          path: 'exam/manage',
          name: 'ExamManage',
          component: () => import('../views/exam/ExamManage.vue'),
          meta: { title: '考试管理', roles: ['admin', 'instructor'] },
        },
        {
          path: 'paper/repository',
          name: 'PaperManage',
          component: () => import('../views/exam/PaperManage.vue'),
          meta: { title: '试卷仓库', roles: ['admin', 'instructor'] },
        },
        {
          path: 'question/repository',
          name: 'QuestionBank',
          component: () => import('../views/exam/QuestionBank.vue'),
          meta: { title: '试题仓库', roles: ['admin', 'instructor'] },
        },
        {
          path: 'exam/do/:id',
          name: 'DoExam',
          component: () => import('../views/exam/Exam.vue'),
          meta: { title: '在线考试', fullscreen: true },
        },
        {
          path: 'exam/result/:id',
          name: 'ExamResult',
          component: () => import('../views/exam/Result.vue'),
          meta: { title: '考试结果' },
        },
        {
          path: 'question/ai',
          name: 'AiQuestionTask',
          component: () => import('../views/exam/AiQuestionTask.vue'),
          meta: { title: 'AI智能出题', roles: ['admin', 'instructor'] },
        },
        {
          path: 'paper/ai-assemble',
          name: 'AiAssemblePaperTask',
          component: () => import('../views/exam/AiAssemblePaperTask.vue'),
          meta: { title: 'AI自动组卷', roles: ['admin', 'instructor'] },
        },
        {
          path: 'paper/ai-generate',
          name: 'AiGeneratePaperTask',
          component: () => import('../views/exam/AiGeneratePaperTask.vue'),
          meta: { title: 'AI自动生成试卷', roles: ['admin', 'instructor'] },
        },
        {
          path: 'training',
          name: 'TrainingList',
          component: () => import('../views/training/List.vue'),
          meta: { title: '培训管理' },
        },
        {
          path: 'training/base',
          name: 'TrainingBaseManage',
          component: () => import('../views/training/Base.vue'),
          meta: { title: '培训基地', roles: ['admin', 'instructor'] },
        },
        {
          path: 'training/schedule/:id?',
          name: 'TrainingSchedule',
          component: () => import('../views/training/Schedule.vue'),
          meta: { title: '周训练计划' },
        },
        {
          path: 'training/board',
          name: 'TrainingBoard',
          component: () => import('../views/training/Board.vue'),
          meta: { title: '培训看板', roles: ['admin'] },
        },
        {
          path: 'training/:id',
          name: 'TrainingDetail',
          component: () => import('../views/training/Detail.vue'),
          meta: { title: '培训班详情' },
        },
        {
          path: 'training/:id/checkin/:sessionKey?',
          name: 'Checkin',
          component: () => import('../views/training/Checkin.vue'),
          meta: { title: '扫码签到' },
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
          meta: { title: '培训训历' },
        },
        {
          path: 'resource/library',
          name: 'ResourceLibrary',
          component: () => import('../views/resource/Library.vue'),
          meta: { title: '资源库' },
        },
        {
          path: 'resource/recommend',
          name: 'ResourceRecommend',
          component: () => import('../views/resource/Recommend.vue'),
          meta: { title: '资源推荐' },
        },
        {
          path: 'resource/detail/:id',
          name: 'ResourceDetail',
          component: () => import('../views/resource/Detail.vue'),
          meta: { title: '资源详情' },
        },
        {
          path: 'resource/upload',
          name: 'ResourceUpload',
          component: () => import('../views/resource/Upload.vue'),
          meta: { title: '上传资源', roles: ['admin', 'instructor'] },
        },
        {
          path: 'resource/my',
          name: 'MyResources',
          component: () => import('../views/resource/MyResources.vue'),
          meta: { title: '我的资源', roles: ['admin', 'instructor'] },
        },
        {
          path: 'resource/manage',
          name: 'ResourceManage',
          component: () => import('../views/resource/Manage.vue'),
          meta: { title: '资源管理', roles: ['admin'] },
        },
        {
          path: 'resource/review',
          name: 'ResourceReviewQueue',
          component: () => import('../views/resource/ReviewQueue.vue'),
          meta: { title: '审核工作台', roles: ['admin', 'instructor'] },
        },
        {
          path: 'resource/policy',
          name: 'ResourcePolicyManage',
          component: () => import('../views/resource/PolicyManage.vue'),
          meta: { title: '审核策略', roles: ['admin'] },
        },
        {
          path: 'instructor',
          name: 'InstructorList',
          component: () => import('../views/instructor/List.vue'),
          meta: { title: '教官库', roles: ['admin', 'instructor'] },
        },
        {
          path: 'instructor/:id',
          name: 'InstructorDetail',
          component: () => import('../views/instructor/Detail.vue'),
          meta: { title: '教官详情', roles: ['admin', 'instructor'] },
        },
        {
          path: 'trainee',
          name: 'TraineeList',
          component: () => import('../views/trainee/List.vue'),
          meta: { title: '学员库' },
        },
        {
          path: 'trainee/:id',
          name: 'TraineeDetail',
          component: () => import('../views/trainee/Detail.vue'),
          meta: { title: '学员详情' },
        },
        {
          path: 'talent',
          name: 'Talent',
          component: () => import('../views/talent/Index.vue'),
          meta: { title: '人才库', roles: ['admin'] },
        },
        {
          path: 'report',
          name: 'Report',
          component: () => import('../views/report/Dashboard.vue'),
          meta: { title: '数据看板', roles: ['admin'] },
        },
        {
          path: 'system/users',
          name: 'UserManage',
          component: () => import('../views/system/UserManage.vue'),
          meta: { title: '用户管理', roles: ['admin'] },
        },
        {
          path: 'system/roles',
          name: 'RoleManage',
          component: () => import('../views/system/RoleManage.vue'),
          meta: { title: '角色管理', roles: ['admin'] },
        },
        {
          path: 'system/departments',
          name: 'DepartmentManage',
          component: () => import('../views/system/DepartmentManage.vue'),
          meta: { title: '部门管理', roles: ['admin'] },
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
          meta: { title: '报名审核', roles: ['admin', 'instructor'] },
        },
        {
          path: 'exam/scores',
          name: 'ExamScores',
          component: () => import('../views/exam/Scores.vue'),
          meta: { title: '成绩管理', roles: ['admin', 'instructor'] },
        },
        {
          path: 'certificate',
          name: 'Certificate',
          component: () => import('../views/certificate/Index.vue'),
          meta: { title: '结业证书' },
        },
      ],
    },
    {
      path: '/mobile/checkin/:token/:sessionKey?',
      name: 'MobileCheckin',
      component: () => import('../views/mobile/Checkin.vue'),
      meta: { title: '扫码签到' },
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return '/login'
  }
  if (to.path === '/login' && token) {
    return '/'
  }
  if (to.meta.roles && token) {
    const userInfo = localStorage.getItem('userInfo')
    if (userInfo) {
      try {
        const user = JSON.parse(userInfo)
        const userRole = user.role
        if (userRole && !to.meta.roles.includes(userRole)) {
          return '/'
        }
      } catch {
        // ignore parse errors
      }
    }
  }
})

export default router
