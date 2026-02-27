export const MOCK_EXAM_RECORDS = [
  {
    id: 'r001',
    examId: 'e001',
    examTitle: '2025年度综合执法能力考核（刑事类）',
    userId: 'u003',
    score: 86,
    totalScore: 100,
    passingScore: 60,
    result: 'pass',
    grade: 'B',
    startTime: '2025-02-20 09:00',
    endTime: '2025-02-20 10:18',
    duration: 78,
    answers: {
      q001: 'C',
      q002: ['A', 'B', 'C', 'D'],
      q003: 'A',   // 答错
      q004: 'C',
      q005: 'C',
      q006: ['A', 'B'],  // 答错（少选D实际题目正确答案是ABC）
      q007: 'A',   // 答错
      q008: 'D',
    },
    correctCount: 5,
    wrongCount: 3,
    wrongQuestions: ['q003', 'q006', 'q007'],
    dimensionScores: {
      law: 88,
      enforce: 72,
      evidence: 64,
      physical: 95,
      ethic: 91,
    },
  },
  {
    id: 'r002',
    examId: 'e002',
    examTitle: '电信网络诈骗专项知识测验',
    userId: 'u003',
    score: 42,
    totalScore: 50,
    passingScore: 35,
    result: 'pass',
    grade: 'A',
    startTime: '2025-02-18 14:00',
    endTime: '2025-02-18 14:22',
    duration: 22,
    answers: { q003: 'B', q005: 'C', q001: 'C', q004: 'C', q007: 'A' },
    correctCount: 4,
    wrongCount: 1,
    wrongQuestions: ['q007'],
    dimensionScores: {
      law: 90,
      enforce: 85,
      evidence: 80,
      physical: 95,
      ethic: 88,
    },
  },
]

// 薄弱点推荐资源
export const WEAK_POINT_RESOURCES = {
  evidence: {
    label: '证据规则',
    courses: [{ id: 'c001', title: '刑事诉讼法实务操作' }],
    tip: '建议重点学习第三章《证据规则与标准》',
  },
  enforce: {
    label: '执法程序',
    courses: [{ id: 'c003', title: '交通事故处置与法律适用' }],
    tip: '建议复习强制措施适用的法定条件与程序',
  },
}
