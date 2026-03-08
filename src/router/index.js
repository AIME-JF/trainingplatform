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
        // 课程学习
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
        // 考试系统
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
          meta: { title: '考试场次管理', roles: ['admin', 'instructor'] },
        },
        {
          path: 'exam/bank',
          name: 'QuestionBank',
          component: () => import('../views/exam/QuestionBank.vue'),
          meta: { title: '题库管理', roles: ['admin', 'instructor'] },
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
        // AI 功能
        {
          path: 'ai/question-gen',
          name: 'QuestionGen',
          component: () => import('../views/ai/QuestionGen.vue'),
          meta: { title: 'AI智能组卷', roles: ['admin', 'instructor'] },
        },
        {
          path: 'ai/lesson-plan',
          name: 'LessonPlan',
          component: () => import('../views/ai/LessonPlan.vue'),
          meta: { title: 'AI教案生成', roles: ['instructor'] },
        },
        // 培训管理（静态路由必须在 /:id 之前）
        {
          path: 'training',
          name: 'TrainingList',
          component: () => import('../views/training/List.vue'),
          meta: { title: '培训管理' },
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
        // 教官管理
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
        // 学员库
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
        // 人才库
        {
          path: 'talent',
          name: 'Talent',
          component: () => import('../views/talent/Index.vue'),
          meta: { title: '人才库', roles: ['admin'] },
        },
        // 数据看板
        {
          path: 'report',
          name: 'Report',
          component: () => import('../views/report/Dashboard.vue'),
          meta: { title: '数据看板', roles: ['admin'] },
        },
        // 系统管理
        {
          path: 'system/users',
          name: 'UserManage',
          component: () => import('../views/system/UserManage.vue'),
          meta: { title: '用户管理', roles: ['admin'] },
        },
        // 个人中心
        {
          path: 'profile',
          name: 'Profile',
          component: () => import('../views/profile/Index.vue'),
          meta: { title: '个人中心' },
        },
        // 报名管理
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
        // 成绩管理
        {
          path: 'exam/scores',
          name: 'ExamScores',
          component: () => import('../views/exam/Scores.vue'),
          meta: { title: '成绩管理', roles: ['admin', 'instructor'] },
        },
        // 结业证书
        {
          path: 'certificate',
          name: 'Certificate',
          component: () => import('../views/certificate/Index.vue'),
          meta: { title: '结业证书' },
        },
      ],
    },
    // 移动端签到（独立页，无主布局）
    {
      path: '/mobile/checkin/:token/:sessionKey?',
      name: 'MobileCheckin',
      component: () => import('../views/mobile/Checkin.vue'),
      meta: { title: '扫码签到' },
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

// 导航守卫：检查 JWT token + 角色权限
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return '/login'
  }
  if (to.path === '/login' && token) {
    return '/'
  }
  // 角色权限检查
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
