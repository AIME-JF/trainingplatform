export const MOCK_DASHBOARD = {
  // 管理员视图统计
  admin: {
    stats: [
      { label: '注册用户', value: 12486, unit: '人', trend: '+342', trendType: 'up' },
      { label: '活跃学员', value: 8234, unit: '人', trend: '+128', trendType: 'up' },
      { label: '课程资源', value: 1356, unit: '门', trend: '+24', trendType: 'up' },
      { label: '本月考试', value: 86, unit: '场次', trend: '+12', trendType: 'up' },
    ],
    monthlyStudy: [
      { month: '9月', hours: 12400 },
      { month: '10月', hours: 15600 },
      { month: '11月', hours: 13200 },
      { month: '12月', hours: 9800 },
      { month: '1月', hours: 11200 },
      { month: '2月', hours: 14500 },
    ],
    trainingStatus: [
      { name: '进行中', value: 12, color: '#003087' },
      { name: '即将开始', value: 5, color: '#faad14' },
      { name: '已结束', value: 38, color: '#8c8c8c' },
    ],
    recentTrainings: [
      { name: '2025年春季刑侦专项训练班', status: 'active', enrolled: 38, startDate: '2025-03-03' },
      { name: '南宁市派出所所长专题培训班', status: 'upcoming', enrolled: 52, startDate: '2025-04-07' },
      { name: '网络安全专项技能提升班', status: 'upcoming', enrolled: 30, startDate: '2025-04-14' },
    ],
    announcements: [
      { id: 1, title: '关于开展2025年春季执法能力大培训的通知', date: '2025-03-01', urgent: true },
      { id: 2, title: '《反电信网络诈骗法》专项学习要求', date: '2025-02-20', urgent: false },
      { id: 3, title: '关于提交2025年度培训计划的通知', date: '2025-02-10', urgent: false },
    ],
  },

  // 教官视图
  instructor: {
    stats: [
      { label: '管理学员', value: 386, unit: '人', trend: '+28', trendType: 'up' },
      { label: '本月课时', value: 32, unit: '课时', trend: '+4', trendType: 'up' },
      { label: '待批改', value: 12, unit: '份', trend: '', trendType: 'neutral' },
      { label: '课程好评率', value: '96.2', unit: '%', trend: '+1.2%', trendType: 'up' },
    ],
    weekSchedule: [
      { day: '周一', date: '3/10', course: '刑事诉讼法实务（第3课）', time: '09:00-11:30', room: '201教室' },
      { day: '周三', date: '3/12', course: '审讯技巧演练', time: '14:00-17:00', room: '询问室' },
      { day: '周五', date: '3/14', course: '综合复盘与答疑', time: '14:00-16:00', room: '201教室' },
    ],
    pendingTasks: [
      { type: 'review', text: '12份作业待批改（刑诉法期中作业）' },
      { type: 'confirm', text: '3月12日签到记录待确认' },
      { type: 'upload', text: '审讯技巧课件更新提醒' },
    ],
    studentProgressData: [
      { name: '张伟', progress: 68, score: 86 },
      { name: '陈小红', progress: 45, score: 72 },
      { name: '黄明', progress: 82, score: 91 },
      { name: '韦大勇', progress: 55, score: 78 },
      { name: '蓝天宇', progress: 30, score: 65 },
    ],
  },

  // 学员视图
  student: {
    stats: [
      { label: '累计学时', value: 128, unit: '小时', trend: '+12', trendType: 'up' },
      { label: '考试次数', value: 8, unit: '次', trend: '', trendType: 'neutral' },
      { label: '平均分', value: 86, unit: '分', trend: '+3', trendType: 'up' },
      { label: '本月任务', value: '3/5', unit: '', trend: '待完成', trendType: 'warning' },
    ],
    pendingTasks: [
      { id: 1, type: 'course', text: '《刑事诉讼法实务操作》第三章待完成', urgent: true },
      { id: 2, type: 'exam', text: '2025年度综合执法能力考核（3月31日截止）', urgent: true },
      { id: 3, type: 'course', text: '《电信网络诈骗专项》课程待开始', urgent: false },
    ],
    recentCourses: [
      { id: 'c001', title: '刑事诉讼法实务操作', progress: 33, lastStudied: '2025-03-08' },
      { id: 'c002', title: '电信网络诈骗案件侦办', progress: 40, lastStudied: '2025-03-06' },
      { id: 'c003', title: '交通事故处置与法律适用', progress: 75, lastStudied: '2025-02-28' },
    ],
    monthProgress: 60, // 本月完成度%
  },
}

// 数据看板（领导视图）
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
