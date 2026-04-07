import {
  AppstoreOutlined,
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
  EXAM_MANAGE_PAGE_PERMISSIONS,
  KNOWLEDGE_POINT_PAGE_PERMISSIONS,
  QUESTION_BANK_PAGE_PERMISSIONS,
  CERTIFICATE_PAGE_PERMISSIONS,
  COURSE_PAGE_PERMISSIONS,
  DASHBOARD_PAGE_PERMISSIONS,
  DEPARTMENT_MANAGE_PAGE_PERMISSIONS,
  DICT_MANAGE_PAGE_PERMISSIONS,
  PAPER_PAGE_PERMISSIONS,
  REPORT_PAGE_PERMISSIONS,
  RESOURCE_MANAGE_PAGE_PERMISSIONS,
  RESOURCE_POLICY_PAGE_PERMISSIONS,
  RESOURCE_REVIEW_PAGE_PERMISSIONS,
  ROLE_MANAGE_PAGE_PERMISSIONS,
  TEACHING_RESOURCE_GENERATION_PAGE_PERMISSIONS,
  TRAINING_BASE_PAGE_PERMISSIONS,
  TRAINING_PAGE_PERMISSIONS,
  TRAINING_SCHEDULE_PAGE_PERMISSIONS,
  USER_ARCHIVE_PAGE_PERMISSIONS,
  USER_MANAGE_PAGE_PERMISSIONS,
  MY_RESOURCE_PAGE_PERMISSIONS,
} from '@/constants/pagePermissions'
import {
  COMMUNITY_MANAGEMENT_TITLE,
  COMMUNITY_RESOURCE_MANAGE_TITLE,
  COURSE_RESOURCES_TITLE,
  LEARNING_CENTER_TITLE,
  MY_UPLOAD_TITLE,
  RESOURCE_BROWSE_TITLE,
} from '@/constants/navigationTitles'

export const appMenuConfig = [
  {
    key: '/',
    label: '工作台',
    icon: HomeOutlined,
    anyPermissions: DASHBOARD_PAGE_PERMISSIONS,
  },
  {
    key: 'learn',
    label: LEARNING_CENTER_TITLE,
    icon: ReadOutlined,
    children: [
      {
        key: '/library',
        label: '知识库',
        roles: ['admin', 'instructor'],
      },
      {
        key: '/resource/teaching-generate',
        label: '教学助手',
        anyPermissions: TEACHING_RESOURCE_GENERATION_PAGE_PERMISSIONS,
      },
      {
        key: '/courses',
        label: COURSE_RESOURCES_TITLE,
        anyPermissions: COURSE_PAGE_PERMISSIONS,
      },
    ],
  },
  {
    key: 'train',
    label: '培训中心',
    icon: TeamOutlined,
    children: [
      {
        key: '/training',
        label: '培训班管理',
        anyPermissions: TRAINING_PAGE_PERMISSIONS,
      },
      {
        key: '/training/base',
        label: '培训基地管理',
        anyPermissions: TRAINING_BASE_PAGE_PERMISSIONS,
      },
      {
        key: '/training/schedule',
        label: '培训计划管理',
        anyPermissions: TRAINING_SCHEDULE_PAGE_PERMISSIONS,
      },
    ],
  },
  {
    key: 'exam',
    label: '考试中心',
    icon: EditOutlined,
    children: [
      {
        key: '/question/repository',
        label: '题库管理',
        anyPermissions: [...QUESTION_BANK_PAGE_PERMISSIONS, ...AI_QUESTION_PAGE_PERMISSIONS, ...KNOWLEDGE_POINT_PAGE_PERMISSIONS],
      },
      {
        key: '/paper/repository',
        label: '试卷管理',
        anyPermissions: [...PAPER_PAGE_PERMISSIONS, ...AI_PAPER_ASSEMBLE_PAGE_PERMISSIONS, ...AI_PAPER_GENERATE_PAGE_PERMISSIONS],
      },
      {
        key: '/exam/manage',
        label: '考试管理',
        anyPermissions: EXAM_MANAGE_PAGE_PERMISSIONS,
      },
    ],
  },
  {
    key: 'evaluate',
    label: '数据中心',
    icon: BarChartOutlined,
    children: [
      {
        key: '/report',
        label: '数据看板',
        anyPermissions: REPORT_PAGE_PERMISSIONS,
      },
      {
        key: '/trainee',
        label: '学员统计',
        anyPermissions: USER_ARCHIVE_PAGE_PERMISSIONS,
      },
      {
        key: '/instructor',
        label: '教官统计',
        anyPermissions: USER_ARCHIVE_PAGE_PERMISSIONS,
      },
      {
        key: '/certificate',
        label: '结业证书',
        anyPermissions: CERTIFICATE_PAGE_PERMISSIONS,
      },
    ],
  },
  {
    key: 'community',
    label: COMMUNITY_MANAGEMENT_TITLE,
    icon: AppstoreOutlined,
    children: [
      {
        key: '/resource/library',
        label: COMMUNITY_RESOURCE_MANAGE_TITLE,
        anyPermissions: [],
      },
      {
        key: '/resource/recommend',
        label: RESOURCE_BROWSE_TITLE,
        anyPermissions: [],
      },
      {
        key: '/resource/my',
        label: MY_UPLOAD_TITLE,
        anyPermissions: MY_RESOURCE_PAGE_PERMISSIONS,
      },
    ],
  },
  {
    key: 'review',
    label: '审核中心',
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
        key: '/system/notices',
        label: '通知管理',
        roles: ['admin'],
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
