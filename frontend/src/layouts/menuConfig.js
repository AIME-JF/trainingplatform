import {
  HomeOutlined,
  PlayCircleOutlined,
  FormOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  TeamOutlined,
  BookOutlined,
  UserOutlined,
  BarChartOutlined,
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
  EXAM_LIST_PAGE_PERMISSIONS,
  EXAM_MANAGE_PAGE_PERMISSIONS,
  PAPER_PAGE_PERMISSIONS,
  QUESTION_BANK_PAGE_PERMISSIONS,
  REPORT_PAGE_PERMISSIONS,
  RESOURCE_MANAGE_PAGE_PERMISSIONS,
  RESOURCE_POLICY_PAGE_PERMISSIONS,
  RESOURCE_REVIEW_PAGE_PERMISSIONS,
  RESOURCE_UPLOAD_PAGE_PERMISSIONS,
  ROLE_MANAGE_PAGE_PERMISSIONS,
  TALENT_PAGE_PERMISSIONS,
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
    key: '/courses',
    label: '课程学习',
    icon: PlayCircleOutlined,
    anyPermissions: COURSE_PAGE_PERMISSIONS,
  },
  {
    key: 'examCenter',
    label: '考试中心',
    icon: FormOutlined,
    children: [
      {
        key: '/exam/manage',
        label: '考试管理',
        anyPermissions: EXAM_MANAGE_PAGE_PERMISSIONS,
      },
      {
        key: '/exam/list',
        label: '参加考试',
        anyPermissions: EXAM_LIST_PAGE_PERMISSIONS,
      },
    ],
  },
  {
    key: 'questionCenter',
    label: '题库管理',
    icon: DatabaseOutlined,
    children: [
      {
        key: '/question/repository',
        label: '试题仓库',
        anyPermissions: QUESTION_BANK_PAGE_PERMISSIONS,
      },
      {
        key: '/question/ai',
        label: 'AI 智能出题',
        anyPermissions: AI_QUESTION_PAGE_PERMISSIONS,
      },
    ],
  },
  {
    key: 'paperCenter',
    label: '卷库管理',
    icon: FileTextOutlined,
    children: [
      {
        key: '/paper/repository',
        label: '试卷仓库',
        anyPermissions: PAPER_PAGE_PERMISSIONS,
      },
      {
        key: '/paper/ai-assemble',
        label: 'AI 自动组卷',
        anyPermissions: AI_PAPER_ASSEMBLE_PAGE_PERMISSIONS,
      },
      {
        key: '/paper/ai-generate',
        label: 'AI 自动生成试卷',
        anyPermissions: AI_PAPER_GENERATE_PAGE_PERMISSIONS,
      },
    ],
  },
  {
    key: 'training',
    label: '培训管理',
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
      {
        key: '/training/board',
        label: '培训看板',
        anyPermissions: REPORT_PAGE_PERMISSIONS,
      },
    ],
  },
  {
    key: 'resource',
    label: '资源中心',
    icon: BookOutlined,
    children: [
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
        key: '/resource/upload',
        label: '上传资源',
        anyPermissions: RESOURCE_UPLOAD_PAGE_PERMISSIONS,
      },
      {
        key: '/resource/my',
        label: '我的资源',
        anyPermissions: MY_RESOURCE_PAGE_PERMISSIONS,
      },
      {
        key: '/resource/manage',
        label: '资源管理',
        anyPermissions: RESOURCE_MANAGE_PAGE_PERMISSIONS,
      },
      {
        key: '/resource/review',
        label: '审核工作台',
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
    key: 'archives',
    label: '人员档案',
    icon: UserOutlined,
    children: [
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
    key: '/report',
    label: '数据看板',
    icon: BarChartOutlined,
    anyPermissions: REPORT_PAGE_PERMISSIONS,
  },
  {
    key: 'system',
    label: '系统管理',
    icon: SettingOutlined,
    children: [
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
        key: '/system/configs',
        label: '配置管理',
        roles: ['admin'],
      },
    ],
  },
]
