import type { Component } from 'vue'
import {
  FileTextOutlined,
  HistoryOutlined,
  MessageOutlined,
  SettingOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue'

export type AssistantPanelKey = 'qa' | 'scenario' | 'generate' | 'records' | 'templates'

export interface AssistantWorkbenchItem {
  key: AssistantPanelKey
  title: string
  description: string
  group: 'training' | 'teaching' | 'manage'
  icon: Component
  roles?: Array<'admin' | 'instructor' | 'student'>
}

export interface AssistantWorkbenchGroup {
  key: string
  title: string
  description: string
  items: AssistantWorkbenchItem[]
}

const allItems: AssistantWorkbenchItem[] = [
  {
    key: 'qa',
    title: '知识问答',
    description: '围绕知识点或资料发起定向问答，也支持直接进行通识问答。',
    group: 'training',
    icon: MessageOutlined,
  },
  {
    key: 'scenario',
    title: '场景模拟训练',
    description: '进入执法场景、笔录训练与法律适用推演等模拟实训。',
    group: 'training',
    icon: TeamOutlined,
  },
  {
    key: 'generate',
    title: '教案/课件生成',
    description: '创建教学资源生成任务，预览结果并确认保存为资源。',
    group: 'teaching',
    icon: FileTextOutlined,
    roles: ['admin', 'instructor'],
  },
  {
    key: 'records',
    title: '学习记录',
    description: '查看知识问答与场景模拟的历史记录，并回看具体内容。',
    group: 'manage',
    icon: HistoryOutlined,
  },
  {
    key: 'templates',
    title: '场景模板管理',
    description: '创建、发布和维护场景模板，支持教官持续迭代训练内容。',
    group: 'manage',
    icon: SettingOutlined,
    roles: ['admin', 'instructor'],
  },
]

const groupMeta: Record<AssistantWorkbenchItem['group'], Omit<AssistantWorkbenchGroup, 'items'>> = {
  training: {
    key: 'training',
    title: '智能训练',
    description: '围绕执法知识学习与模拟训练开展互动练习。',
  },
  teaching: {
    key: 'teaching',
    title: '教学辅助',
    description: '为教官准备教案、课件等教学支持能力。',
  },
  manage: {
    key: 'manage',
    title: '复盘与管理',
    description: '查看训练记录并管理可复用的场景模板。',
  },
}

export function isAssistantPanelKey(value: unknown): value is AssistantPanelKey {
  return typeof value === 'string' && allItems.some((item) => item.key === value)
}

export function getAssistantWorkbenchGroups(options: {
  isAdmin: boolean
  isInstructor: boolean
  isStudent: boolean
}): AssistantWorkbenchGroup[] {
  const visibleItems = allItems.filter((item) => {
    if (!item.roles?.length) {
      return true
    }
    return item.roles.some((role) => {
      if (role === 'admin') return options.isAdmin
      if (role === 'instructor') return options.isInstructor
      if (role === 'student') return options.isStudent
      return false
    })
  })

  return Object.values(groupMeta)
    .map((group) => ({
      ...group,
      items: visibleItems.filter((item) => item.group === group.key),
    }))
    .filter((group) => group.items.length > 0)
}

export function getAssistantWorkbenchItem(key: AssistantPanelKey) {
  return allItems.find((item) => item.key === key) || allItems[0]
}

