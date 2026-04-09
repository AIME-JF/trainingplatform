export type AssistantMode = 'qa' | 'case'

interface AssistantModeMeta {
  pageTitle: string
  welcomeTitle: string
  welcomeDesc: string
  quickPrompts: string[]
}

const ASSISTANT_MODE_META: Record<AssistantMode, AssistantModeMeta> = {
  qa: {
    pageTitle: '知识问答',
    welcomeTitle: '知识问答助手',
    welcomeDesc: '可直接发起通识问答；若选择知识点，我会优先基于这些知识点回答。',
    quickPrompts: [
      '什么情况下可以使用警械？',
      '治安调解的适用条件有哪些？',
      '询问未成年人有哪些特殊规定？',
    ],
  },
  case: {
    pageTitle: '案例分析生成',
    welcomeTitle: '案例分析助手',
    welcomeDesc: '可结合已选知识点生成案例分析材料，未选择时则按通用案例分析处理。',
    quickPrompts: [
      '生成一个醉驾查处的教学案例',
      '帮我分析一个入室盗窃的典型案例',
      '制作一个涉及正当防卫的案例分析',
    ],
  },
}

const CHAT_MODE_LABELS: Record<string, string> = {
  qa: '知识问答',
  case: '案例分析',
  generate: '教案/课件生成（历史记录）',
}

export function isAssistantMode(mode: string): mode is AssistantMode {
  return mode === 'qa' || mode === 'case'
}

export function getAssistantModeMeta(mode: AssistantMode): AssistantModeMeta {
  return ASSISTANT_MODE_META[mode]
}

export function getKnowledgeChatModeLabel(mode: string) {
  return CHAT_MODE_LABELS[mode] || mode || '-'
}
