/**
 * 培训看板及个人工作台 Mock 数据
 */

// 1. 广西公安警务培训实时看板汇总数据 (用于 Board.vue)
export const MOCK_TRAINING_BOARD = {
  // 各市局参训人数分布 (柱状图)
  cityAttendance: [
    { name: '南宁', value: 486, trend: 15 },
    { name: '柳州', value: 395, trend: 8 },
    { name: '桂林', value: 312, trend: -5 },
    { name: '梧州', value: 254, trend: 12 },
    { name: '北海', value: 202, trend: 20 },
    { name: '防城港', value: 168, trend: 7 },
    { name: '钦州', value: 185, trend: 3 },
    { name: '贵港', value: 242, trend: 10 },
    { name: '玉林', value: 274, trend: 14 },
    { name: '百色', value: 198, trend: -6 },
    { name: '贺州', value: 159, trend: 2 },
    { name: '河池', value: 165, trend: 4 },
    { name: '来宾', value: 142, trend: -2 },
    { name: '崇左', value: 138, trend: 1 },
  ],

  // 近6月培训完成率趋势 (%) (折线图)
  completionTrend: {
    months: ['9月', '10月', '11月', '12月', '1月', '2月'],
    rates: [74.2, 77.5, 79.8, 82.1, 84.6, 88.3]
  },

  // 异常预警列表
  warnings: [
    { id: 1, text: '南宁市局刑侦大队本月参训率未达标（当前 65%，阈值 80%）', time: '5分钟前', level: 'high' },
    { id: 2, text: '《全警实战大练兵》系列课程即将达到报名人数上限', time: '32分钟前', level: 'medium' },
    { id: 3, text: '柳州市有 18 名学员连续 3 天课次签到异常', time: '1小时前', level: 'high' },
    { id: 4, text: '系统检测到河池地区 2 个外出实训班排课时间存在逻辑冲突', time: '3小时前', level: 'medium' },
    { id: 5, text: '贺州市教官资源配置不足，建议跨地区调拨', time: '5小时前', level: 'medium' }
  ],

  // 各市完成率排名
  cityRankings: [
    { name: '南宁', rate: 99.2 },
    { name: '柳州', rate: 96.8 },
    { name: '桂林', rate: 94.5 },
    { name: '北海', rate: 91.2 },
    { name: '贵港', rate: 88.1 },
    { name: '防城港', rate: 86.4 },
    { name: '玉林', rate: 85.2 }
  ],

  // KPI 基础趋势配置
  kpiConfig: {
    baseTrend: { inProgress: 14.2, attendance: 21.5, completion: 4.8, pending: -8.5 }
  }
}

// 2. 个人工作台数据 (用于 Index.vue)
export const MOCK_PERSONAL_DASHBOARD = {
  // 管理员角色数据
  admin: {
    stats: [
      { label: '全区注册警员', value: 52480, unit: '人', trend: '+142', trendType: 'up' },
      { label: '本月结业人数', value: 3852, unit: '人', trend: '+56', trendType: 'up' },
      { label: '在线课程资源', value: 1526, unit: '门', trend: '+12', trendType: 'up' },
      { label: '年均考核合格率', value: '94.2', unit: '%', trend: '+0.5%', trendType: 'up' },
    ],
    announcements: [
      { id: 1, title: '关于开展2025年春季全警实战大练兵的指导意见', date: '2025-03-05', urgent: true },
      { id: 2, title: '关于规范培训班考勤管理制度的补充通知', date: '2025-03-02', urgent: false },
      { id: 3, title: '广西公安教育训练管理平台V2.0上线公告', date: '2025-02-28', urgent: false },
    ]
  },

  // 教官角色数据
  instructor: {
    stats: [
      { label: '当前授课进度', value: '85', unit: '%', trend: '正常', trendType: 'up' },
      { label: '本周教学时长', value: '18', unit: '课时', trend: '+4', trendType: 'up' },
      { label: '待阅卷申请', value: '7', unit: '份', trend: '', trendType: 'neutral' },
      { label: '所带班级平均分', value: '88.5', unit: '分', trend: '+2.1', trendType: 'up' },
    ],
    weekSchedule: [
      { day: '周一', date: '03-10', course: '基层警务指挥实务', time: '09:00-11:30', room: '101多媒体教室' },
      { day: '周三', date: '03-12', course: '突发事件现场处置', time: '14:30-17:00', room: '战术模拟馆' },
      { day: '周五', date: '03-14', course: '结业考核评审', time: '09:00-12:00', room: '205会议室' },
    ],
    pendingTasks: [
      { type: 'review', text: '5份《刑事侦查基础》课后作业待评定' },
      { type: 'confirm', text: '3月8日培训班学员名单审核确认' },
      { type: 'upload', text: '下周排课计划变更提醒' },
    ],
    studentProgressData: [
      { name: '张旭', progress: 92, score: 95 },
      { name: '曾志伟', progress: 58, score: 76 },
      { name: '黎美珍', progress: 84, score: 91 },
      { name: '黄大壮', progress: 42, score: 68 },
    ],
  },

  // 学员角色数据
  student: {
    stats: [
      { label: '已修学分', value: 45, unit: '分', trend: '+5', trendType: 'up' },
      { label: '在线时长', value: 128, unit: '小时', trend: '+12', trendType: 'up' },
      { label: '证书获得', value: 3, unit: '个', trend: '', trendType: 'neutral' },
      { label: '学习任务/进行中', value: '2/4', unit: '', trend: '待完成', trendType: 'warning' },
    ],
    pendingTasks: [
      { id: 1, type: 'course', text: '《基础枪械使用规范》网络课程待修完', urgent: true },
      { id: 2, type: 'exam', text: '2025年第一季度政治理论考核', urgent: true },
      { id: 3, type: 'survey', text: '关于教学评估的调查问卷', urgent: false },
    ],
    recentCourses: [
      { id: 'c001', title: '全警实战大练兵：基础体能', progress: 75, lastStudied: '2025-03-04' },
      { id: 'c002', title: '警情处置法律适用解析', progress: 40, lastStudied: '2025-03-02' },
      { id: 'c003', title: '数字警务工作台应用指南', progress: 10, lastStudied: '2025-02-28' },
    ],
    monthProgress: 65,
  },
}

// 3. 数据看板（领导视图）数据 (用于 Report/Dashboard.vue)
export const MOCK_REPORT_DATA = {
  overview: {
    totalPolice: 48632,
    trainedThisYear: 32108,
    trainingRate: 66.0,
    avgScore: 81.3,
    passRate: 92.4,
  },
  cityComparison: [
    { city: '南宁', trainingRate: 78, avgScore: 83 },
    { city: '柳州', trainingRate: 72, avgScore: 80 },
    { city: '桂林', trainingRate: 68, avgScore: 79 },
    { city: '梧州', trainingRate: 65, avgScore: 77 },
    { city: '贺州', trainingRate: 70, avgScore: 81 },
    { city: '百色', trainingRate: 58, avgScore: 75 },
    { city: '钦州', trainingRate: 62, avgScore: 78 },
  ],
  monthlyTrend: [
    { month: '2024-09', trained: 4200, hours: 85000 },
    { month: '2024-10', trained: 5100, hours: 102000 },
    { month: '2024-11', trained: 4800, hours: 96000 },
    { month: '2024-12', trained: 3200, hours: 64000 },
    { month: '2025-01', trained: 2800, hours: 56000 },
    { month: '2025-02', trained: 4500, hours: 90000 },
  ],
  policeTypeDistribution: [
    { type: '刑警', count: 8420, trained: 6850 },
    { type: '交警', count: 7230, trained: 5440 },
    { type: '治安', count: 12600, trained: 8200 },
    { type: '社区', count: 9800, trained: 5800 },
    { type: '其他', count: 10582, trained: 5818 },
  ],
}
