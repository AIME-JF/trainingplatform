import request from './request'

function cloneData(value) {
  return Promise.resolve(JSON.parse(JSON.stringify(value)))
}

const assistantQueue = [
  {
    id: 4101,
    title: '夜间巡逻处置实录',
    uploaderName: '海淀分局社区中队',
    submittedAt: '2026-04-07 09:20',
    duration: '02:18',
    aiScore: 91,
    riskLevel: 'high',
    status: 'manual_review',
    hitRules: ['执法场景待复核', '危险动作镜头'],
    summary: '出现夜间盘查与肢体控制片段，建议人工确认镜头表达是否合规。',
    recommendation: [
      '核验执法环节字幕和口播是否完整。',
      '确认危险动作镜头是否需要打码处理。',
      '复核是否存在不宜公开的个人隐私信息。',
    ],
  },
  {
    id: 4102,
    title: '社区防诈入户宣传纪实',
    uploaderName: '朝阳分局宣传岗',
    submittedAt: '2026-04-07 10:05',
    duration: '01:43',
    aiScore: 78,
    riskLevel: 'medium',
    status: 'ai_reviewing',
    hitRules: ['人脸信息检测'],
    summary: '宣传内容整体正常，但有多个入户镜头，需关注居民面部信息。',
    recommendation: [
      '优先检查入户画面的隐私遮挡。',
      '确认视频描述与实际内容是否一致。',
    ],
  },
  {
    id: 4103,
    title: '校园周边巡防快剪',
    uploaderName: '丰台分局巡防队',
    submittedAt: '2026-04-07 10:42',
    duration: '00:56',
    aiScore: 65,
    riskLevel: 'low',
    status: 'queued',
    hitRules: ['标题语义待确认'],
    summary: '整体风险较低，等待 AI 审核队列调度。',
    recommendation: [
      '保持标题与正文一致，避免夸张表达。',
    ],
  },
  {
    id: 4104,
    title: '矛盾纠纷调解现场记录',
    uploaderName: '石景山分局社区调解岗',
    submittedAt: '2026-04-07 11:16',
    duration: '03:05',
    aiScore: 88,
    riskLevel: 'high',
    status: 'manual_review',
    hitRules: ['涉未成年人片段', '情绪冲突镜头'],
    summary: '调解现场包含冲突与未成年人片段，建议提升复核优先级。',
    recommendation: [
      '检查未成年人是否已做遮挡处理。',
      '复核评论区引导文案是否合适。',
      '必要时建议转为内部学习素材，不对外展示。',
    ],
  },
]

const assistantDashboard = {
  summary: {
    pendingCount: 18,
    manualReviewCount: 12,
    autoApprovedCount: 86,
    highRiskCount: 4,
    avgReviewMinutes: 2.6,
  },
  reviewTrend: [
    { date: '04-01', reviewed: 32, intercepted: 4 },
    { date: '04-02', reviewed: 41, intercepted: 6 },
    { date: '04-03', reviewed: 37, intercepted: 5 },
    { date: '04-04', reviewed: 46, intercepted: 7 },
    { date: '04-05', reviewed: 39, intercepted: 3 },
    { date: '04-06', reviewed: 44, intercepted: 6 },
    { date: '04-07', reviewed: 28, intercepted: 4 },
  ],
  statusDistribution: [
    { name: '排队中', value: 18 },
    { name: 'AI审核中', value: 9 },
    { name: '待人工复核', value: 12 },
    { name: '自动通过', value: 86 },
    { name: '已拦截', value: 7 },
  ],
  ruleHits: [
    { name: '执法场景待复核', count: 21, level: 'high' },
    { name: '个人隐私打码', count: 16, level: 'medium' },
    { name: '标题语义偏差', count: 11, level: 'low' },
    { name: '情绪冲突镜头', count: 8, level: 'high' },
  ],
  queue: assistantQueue,
}

const boardDashboards = {
  '7d': {
    overview: {
      totalVideos: 168,
      totalPlays: 286000,
      totalLikes: 18920,
      totalComments: 4250,
      totalShares: 1924,
      engagementRate: 8.78,
      completionRate: 63.5,
    },
    trend: [
      { date: '04-01', plays: 35600, likes: 2210, comments: 520, shares: 218 },
      { date: '04-02', plays: 40200, likes: 2610, comments: 610, shares: 251 },
      { date: '04-03', plays: 39100, likes: 2488, comments: 590, shares: 244 },
      { date: '04-04', plays: 42800, likes: 2896, comments: 672, shares: 296 },
      { date: '04-05', plays: 46300, likes: 3140, comments: 701, shares: 318 },
      { date: '04-06', plays: 41200, likes: 2794, comments: 628, shares: 283 },
      { date: '04-07', plays: 40800, likes: 2782, comments: 529, shares: 314 },
    ],
    interactionDistribution: [
      { name: '点赞', value: 18920 },
      { name: '评论', value: 4250 },
      { name: '转发', value: 1924 },
    ],
    topVideos: [
      { id: 5201, title: '反诈情景短片：冒充客服识别', category: '反诈宣传', plays: 58200, likes: 4680, comments: 920, shares: 426, engagementRate: 10.35, completionRate: 71.2 },
      { id: 5202, title: '社区民警的一天', category: '日常纪实', plays: 50100, likes: 3860, comments: 780, shares: 364, engagementRate: 9.98, completionRate: 68.7 },
      { id: 5203, title: '邻里纠纷调解实务', category: '案例解析', plays: 46800, likes: 3320, comments: 744, shares: 338, engagementRate: 9.4, completionRate: 66.1 },
      { id: 5204, title: '校园安全宣讲快剪', category: '宣传教育', plays: 42900, likes: 3010, comments: 658, shares: 286, engagementRate: 9.21, completionRate: 64.8 },
      { id: 5205, title: '夜巡快反协同处置', category: '警务纪实', plays: 39500, likes: 2740, comments: 583, shares: 254, engagementRate: 9.06, completionRate: 62.4 },
    ],
    latestVideos: [
      { id: 5206, title: '小区消防隐患排查', uploaderName: '海淀分局', plays: 21800, likes: 1450, comments: 286, shares: 121, engagementRate: 8.53, completionRate: 61.2 },
      { id: 5207, title: '防溺水安全提醒', uploaderName: '昌平分局', plays: 24600, likes: 1588, comments: 330, shares: 149, engagementRate: 8.44, completionRate: 59.7 },
      { id: 5208, title: '出租房清查纪实', uploaderName: '朝阳分局', plays: 19800, likes: 1204, comments: 242, shares: 115, engagementRate: 7.88, completionRate: 57.3 },
      { id: 5209, title: '周末社区反诈快问快答', uploaderName: '东城分局', plays: 26300, likes: 1820, comments: 410, shares: 173, engagementRate: 9.13, completionRate: 65.1 },
      { id: 5210, title: '电动车整治现场速览', uploaderName: '西城分局', plays: 17500, likes: 1094, comments: 214, shares: 96, engagementRate: 8.02, completionRate: 55.8 },
    ],
  },
  '30d': {
    overview: {
      totalVideos: 624,
      totalPlays: 972000,
      totalLikes: 64820,
      totalComments: 15260,
      totalShares: 7180,
      engagementRate: 8.98,
      completionRate: 61.9,
    },
    trend: [
      { date: '第1周', plays: 198000, likes: 13240, comments: 3160, shares: 1460 },
      { date: '第2周', plays: 224000, likes: 14980, comments: 3560, shares: 1690 },
      { date: '第3周', plays: 261000, likes: 17420, comments: 4120, shares: 1980 },
      { date: '第4周', plays: 289000, likes: 19180, comments: 4420, shares: 2050 },
    ],
    interactionDistribution: [
      { name: '点赞', value: 64820 },
      { name: '评论', value: 15260 },
      { name: '转发', value: 7180 },
    ],
    topVideos: [
      { id: 5301, title: '反诈情景短片：冒充客服识别', category: '反诈宣传', plays: 186000, likes: 14860, comments: 3020, shares: 1406, engagementRate: 10.37, completionRate: 70.8 },
      { id: 5302, title: '社区民警的一天', category: '日常纪实', plays: 172000, likes: 13240, comments: 2740, shares: 1264, engagementRate: 10.03, completionRate: 67.9 },
      { id: 5303, title: '邻里纠纷调解实务', category: '案例解析', plays: 160000, likes: 11840, comments: 2556, shares: 1178, engagementRate: 9.73, completionRate: 65.3 },
      { id: 5304, title: '校园安全宣讲快剪', category: '宣传教育', plays: 154000, likes: 11210, comments: 2430, shares: 1092, engagementRate: 9.57, completionRate: 63.6 },
      { id: 5305, title: '夜巡快反协同处置', category: '警务纪实', plays: 149000, likes: 10840, comments: 2298, shares: 1036, engagementRate: 9.48, completionRate: 62.5 },
    ],
    latestVideos: [
      { id: 5306, title: '小区消防隐患排查', uploaderName: '海淀分局', plays: 74200, likes: 5020, comments: 1126, shares: 522, engagementRate: 8.98, completionRate: 60.4 },
      { id: 5307, title: '防溺水安全提醒', uploaderName: '昌平分局', plays: 68800, likes: 4512, comments: 1034, shares: 468, engagementRate: 8.73, completionRate: 59.2 },
      { id: 5308, title: '出租房清查纪实', uploaderName: '朝阳分局', plays: 61500, likes: 3980, comments: 886, shares: 432, engagementRate: 8.61, completionRate: 57.1 },
      { id: 5309, title: '周末社区反诈快问快答', uploaderName: '东城分局', plays: 79200, likes: 5580, comments: 1298, shares: 574, engagementRate: 9.41, completionRate: 64.7 },
      { id: 5310, title: '电动车整治现场速览', uploaderName: '西城分局', plays: 58400, likes: 3720, comments: 812, shares: 396, engagementRate: 8.78, completionRate: 55.2 },
    ],
  },
}

export function getCommunityAssistantDashboard() {
  // TODO: replace with request.get('/community/assistant/dashboard')
  return cloneData(assistantDashboard)
}

export function getCommunityBoardDashboard(params = {}) {
  return request.get('/community/board/dashboard', { params })
}
