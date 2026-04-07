import type { Component } from 'vue'
import {
  AppstoreOutlined,
  BellOutlined,
  BookFilled,
  CalendarFilled,
  CalendarOutlined,
  DatabaseOutlined,
  FileProtectOutlined,
  FolderOpenOutlined,
  ProfileFilled,
  ReadOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'
import {
  COURSE_PERMISSIONS,
  EXAM_LIST_PERMISSIONS,
  MY_RESOURCE_PERMISSIONS,
  PROFILE_PERMISSIONS,
  TRAINING_PERMISSIONS,
  TRAINING_SCHEDULE_PERMISSIONS,
} from '@/constants/permissions'
import { COURSE_RESOURCES_TITLE } from '@/constants/navigationTitles'

export type QuickActionSurface = 'dashboard' | 'profile'

export interface QuickActionConfig {
  title: string
  description: string
  path: string
  icon: Component
  background: string
  mobileBackground?: string
  mobileIcon?: Component
  mobileIconColor?: string
  mobileShadowColor?: string
  permissions: string[]
  surfaces: QuickActionSurface[]
}

export const quickActionConfigs: QuickActionConfig[] = [
  {
    title: '我的班级',
    description: '查看训练班、时间安排与详情',
    path: '/classes',
    icon: ReadOutlined,
    background: 'var(--v2-cover-blue)',
    mobileIcon: ProfileFilled,
    mobileBackground: '#efe6ff',
    mobileIconColor: '#7e58ef',
    mobileShadowColor: 'rgba(126, 88, 239, 0.12)',
    permissions: TRAINING_PERMISSIONS,
    surfaces: ['dashboard', 'profile'],
  },
  {
    title: '周训练计划',
    description: '进入周训练计划与课程排期',
    path: '/classes/schedule',
    icon: CalendarOutlined,
    background: 'var(--v2-cover-green)',
    mobileIcon: CalendarFilled,
    mobileBackground: '#e2f4ff',
    mobileIconColor: '#3899ff',
    mobileShadowColor: 'rgba(56, 153, 255, 0.12)',
    permissions: TRAINING_SCHEDULE_PERMISSIONS,
    surfaces: ['dashboard', 'profile'],
  },
  {
    title: COURSE_RESOURCES_TITLE,
    description: '继续课程学习与资源浏览',
    path: '/resource/courses',
    icon: DatabaseOutlined,
    background: 'var(--v2-cover-purple)',
    mobileIcon: BookFilled,
    mobileBackground: '#fff1dc',
    mobileIconColor: '#ffab47',
    mobileShadowColor: 'rgba(255, 171, 71, 0.12)',
    permissions: COURSE_PERMISSIONS,
    surfaces: ['dashboard', 'profile'],
  },
  {
    title: '个人中心',
    description: '查看当前账号资料与学习概览',
    path: '/profile',
    icon: UserOutlined,
    background: 'var(--v2-cover-orange)',
    mobileIcon: UserOutlined,
    mobileBackground: '#ffe4ef',
    mobileIconColor: '#ff7ea8',
    mobileShadowColor: 'rgba(255, 126, 168, 0.12)',
    permissions: PROFILE_PERMISSIONS,
    surfaces: ['dashboard'],
  },
  {
    title: '通知中心',
    description: '查看提醒消息与平台公告',
    path: '/notifications',
    icon: BellOutlined,
    background: 'var(--v2-cover-teal)',
    mobileBackground: '#e2fbff',
    mobileIconColor: '#2ea9c1',
    mobileShadowColor: 'rgba(46, 169, 193, 0.14)',
    permissions: PROFILE_PERMISSIONS,
    surfaces: ['profile'],
  },
  {
    title: '在线考试',
    description: '查看考试安排与考试结果',
    path: '/exam/list',
    icon: FileProtectOutlined,
    background: 'var(--v2-cover-rose)',
    mobileBackground: '#ffe7e8',
    mobileIconColor: '#de5e70',
    mobileShadowColor: 'rgba(222, 94, 112, 0.14)',
    permissions: EXAM_LIST_PERMISSIONS,
    surfaces: ['profile'],
  },
  {
    title: '我的资源',
    description: '查看个人上传资源与审核状态',
    path: '/resource/my',
    icon: FolderOpenOutlined,
    background: 'var(--v2-cover-yellow)',
    mobileBackground: '#fff4da',
    mobileIconColor: '#c7912d',
    mobileShadowColor: 'rgba(199, 145, 45, 0.14)',
    permissions: MY_RESOURCE_PERMISSIONS,
    surfaces: ['profile'],
  },
  {
    title: '资源社区',
    description: '进入资源社区和精选资源',
    path: '/resource/community',
    icon: AppstoreOutlined,
    background: 'var(--v2-cover-pink)',
    mobileBackground: '#ffe7f0',
    mobileIconColor: '#d96a96',
    mobileShadowColor: 'rgba(217, 106, 150, 0.14)',
    permissions: PROFILE_PERMISSIONS,
    surfaces: ['profile'],
  },
]
