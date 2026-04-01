import {
  HomeOutlined,
  ReadOutlined,
  TeamOutlined,
  EditOutlined,
  BarChartOutlined,
  AuditOutlined,
  SettingOutlined,
} from '@ant-design/icons-vue'

import {
  AI_PAPER_ASSEMBLE_PAGE_PERMISSIONS,
  AI_PAPER_GENERATE_PAGE_PERMISSIONS,
  AI_QUESTION_PAGE_PERMISSIONS,
  CERTIFICATE_PAGE_PERMISSIONS,
  COURSE_PAGE_PERMISSIONS,
  DASHBOARD_PAGE_PERMISSIONS,
  DEPARTMENT_MANAGE_PAGE_PERMISSIONS,
  DICT_MANAGE_PAGE_PERMISSIONS,
  EXAM_LIST_PAGE_PERMISSIONS,
  EXAM_MANAGE_PAGE_PERMISSIONS,
  PAPER_PAGE_PERMISSIONS,
  KNOWLEDGE_POINT_PAGE_PERMISSIONS,
  QUESTION_BANK_PAGE_PERMISSIONS,
  REPORT_PAGE_PERMISSIONS,
  RESOURCE_MANAGE_PAGE_PERMISSIONS,
  RESOURCE_POLICY_PAGE_PERMISSIONS,
  RESOURCE_REVIEW_PAGE_PERMISSIONS,
  ROLE_MANAGE_PAGE_PERMISSIONS,
  TALENT_PAGE_PERMISSIONS,
  TEACHING_RESOURCE_GENERATION_PAGE_PERMISSIONS,
  TRAINING_BASE_PAGE_PERMISSIONS,
  TRAINING_PAGE_PERMISSIONS,
  TRAINING_SCHEDULE_PAGE_PERMISSIONS,
  USER_ARCHIVE_PAGE_PERMISSIONS,
  USER_MANAGE_PAGE_PERMISSIONS,
  MY_RESOURCE_PAGE_PERMISSIONS,
} from '@/constants/pagePermissions'

export const appMenuConfig = [
  {
    key: '/',
    label: '工作台',
    icon: HomeOutlined,
    anyPermissions: DASHBOARD_PAGE_PERMISSIONS,
  },
  {
    key: 'learn',
    label: '学习资源',
    icon: ReadOutlined,
    children: [
      {
        key: '/courses',
        label: '课程资源',
        anyPermissions: COURSE_PAGE_PERMISSIONS,
      },
      {
        key: '/resource/library',
        label: '资源库',
        anyPermissions: [],
      },
      {
        key: '/resource/recommend',
        label: '资源推荐',
        anyPermissions: [],
      },
      {
        key: '/resource/my',
        label: '我的空间',
        anyPermissions: MY_RESOURCE_PAGE_PERMISSIONS,
      },
      {
        key: '/resource/teaching-generate',
        label: '教学资源生成',
        anyPermissions: TEACHING_RESOURCE_GENERATION_PAGE_PERMISSIONS,
      },
    ],
  },
  {
    key: 'train',
    label: '培训组织',
    icon: TeamOutlined,
    children: [
      {
        key: '/training',
        label: '培训班列表',
        anyPermissions: TRAINING_PAGE_PERMISSIONS,
      },
      {
        key: '/training/base',
        label: '培训基地',
        anyPermissions: TRAINING_BASE_PAGE_PERMISSIONS,
      },
      {
        key: '/training/schedule',
        label: '周训练计划',
        anyPermissions: TRAINING_SCHEDULE_PAGE_PERMISSIONS,
      },
    ],
  },
  {
    key: 'exam',
    label: '考试测评',
    icon: EditOutlined,
    children: [
      {
        key: '/exam/list',
        label: '参加考试',
        anyPermissions: EXAM_LIST_PAGE_PERMISSIONS,
      },
      {
        key: '/exam/manage',
        label: '考试管理',
        anyPermissions: EXAM_MANAGE_PAGE_PERMISSIONS,
      },
      {
        key: '/paper/repository',
        label: '试卷仓库',
        anyPermissions: PAPER_PAGE_PERMISSIONS,
      },
      {
        key: '/question/knowledge-points',
        label: '知识点管理',
        anyPermissions: KNOWLEDGE_POINT_PAGE_PERMISSIONS,
      },
      {
        key: '/question/repository',
        label: '智能题库',
        anyPermissions: [...QUESTION_BANK_PAGE_PERMISSIONS, ...AI_QUESTION_PAGE_PERMISSIONS],
      },
      {
        key: '/paper/ai-assemble',
        label: '智能出卷',
        anyPermissions: [...AI_PAPER_ASSEMBLE_PAGE_PERMISSIONS, ...AI_PAPER_GENERATE_PAGE_PERMISSIONS],
      },
    ],
  },
  {
    key: 'evaluate',
    label: '评估分析',
    icon: BarChartOutlined,
    children: [
      {
        key: '/report',
        label: '数据看板',
        anyPermissions: REPORT_PAGE_PERMISSIONS,
      },
      {
        key: '/trainee',
        label: '学员库',
        anyPermissions: USER_ARCHIVE_PAGE_PERMISSIONS,
      },
      {
        key: '/instructor',
        label: '教官库',
        anyPermissions: USER_ARCHIVE_PAGE_PERMISSIONS,
      },
      {
        key: '/talent',
        label: '人才库',
        anyPermissions: TALENT_PAGE_PERMISSIONS,
      },
      {
        key: '/certificate',
        label: '结业证书',
        anyPermissions: CERTIFICATE_PAGE_PERMISSIONS,
      },
    ],
  },
  {
    key: 'review',
    label: '审核管理',
    icon: AuditOutlined,
    children: [
      {
        key: '/resource/review',
        label: '资源审核',
        anyPermissions: RESOURCE_REVIEW_PAGE_PERMISSIONS,
      },
      {
        key: '/resource/policy',
        label: '审核策略',
        anyPermissions: RESOURCE_POLICY_PAGE_PERMISSIONS,
      },
    ],
  },
  {
    key: 'manage',
    label: '系统管理',
    icon: SettingOutlined,
    children: [
      {
        key: '/resource/manage',
        label: '资源管理',
        anyPermissions: RESOURCE_MANAGE_PAGE_PERMISSIONS,
      },
      {
        key: '/system/users',
        label: '用户管理',
        anyPermissions: USER_MANAGE_PAGE_PERMISSIONS,
      },
      {
        key: '/system/roles',
        label: '角色管理',
        anyPermissions: ROLE_MANAGE_PAGE_PERMISSIONS,
      },
      {
        key: '/system/departments',
        label: '部门管理',
        anyPermissions: DEPARTMENT_MANAGE_PAGE_PERMISSIONS,
      },
      {
        key: '/system/dict',
        label: '字典管理',
        anyPermissions: DICT_MANAGE_PAGE_PERMISSIONS,
      },
      {
        key: '/system/dashboard-modules',
        label: '看板配置',
        roles: ['admin'],
      },
      {
        key: '/system/configs',
        label: '配置管理',
        roles: ['admin'],
      },
    ],
  },
]
