// 成绩管理 mock 数据
import { MOCK_USER_LIST } from './users'

export const MOCK_EXAM_LIST = [
    { id: 'exam001', title: '2025年Q1执法规范化综合考试' },
    { id: 'exam002', title: '2024年年度基础法律知识考核' },
    { id: 'exam003', title: '证据收集专项考试（2月场）' },
]

function randScore(base, range) { return Math.floor(base + Math.random() * range) }

// 从 MOCK_USER_LIST 动态生成学生成绩
export const MOCK_SCORE_STUDENTS = MOCK_USER_LIST.slice(0, 8).map((u, i) => {
    const law = randScore(55, 40)
    const enforce = randScore(50, 45)
    const evidence = randScore(45, 50)
    const physical = randScore(60, 38)
    const ethic = randScore(55, 42)
    const score = Math.round((law + enforce + evidence + physical + ethic) / 5)
    const minutes = 60 + Math.floor(Math.random() * 60)
    return {
        id: u.id,
        name: u.name,
        policeId: u.policeId,
        unit: u.unit,
        score,
        law, enforce, evidence, physical, ethic,
        time: `${Math.floor(minutes / 60)}小时${String(minutes % 60).padStart(2, '0')}分`,
    }
})

// 计算 KPI
export function computeScoreKPI(students) {
    const count = students.length
    const avg = (students.reduce((s, x) => s + x.score, 0) / count).toFixed(1)
    const max = Math.max(...students.map(s => s.score))
    const passRate = ((students.filter(s => s.score >= 60).length / count) * 100).toFixed(1)
    return [
        { label: '参考人数', value: count, unit: '人', color: '#003087' },
        { label: '班级平均分', value: avg, unit: '分', color: '#52c41a' },
        { label: '最高分', value: max, unit: '分', color: '#c8a84b' },
        { label: '通过率', value: passRate, unit: '%', color: '#fa8c16' },
    ]
}

// 错题 mock
export const MOCK_WRONG_QUESTIONS = [
    { num: 3, type: 'single', stem: '下列哪种情形不属于逮捕条件的"社会危险性"？', myAnswer: 'B', answer: 'D', explanation: '逮捕的"社会危险性"包括可能逃跑、毁灭证据等，一般违法行为不符合此条件。' },
    { num: 7, type: 'judge', stem: '对醉酒的人在醉酒状态中实施的违法行为，公安机关可以对其采取保护性措施约束至酒醒。', myAnswer: 'F', answer: 'T', explanation: '《治安管理处罚法》第15条明确规定了该情形。' },
]

// 人才库 mock
export const MOCK_TALENTS = [
    { id: 1, name: '张伟', unit: '南宁市公安局', tier: 's', tierLabel: 'S', rank: 1, totalScore: 96.8, studyHours: 128, passRate: 100, avatarColor: '#c8a84b', highlights: ['全区第一', '理论满分', '实操优秀'], aiNote: 'AI综合评估：各维度均衡发展，推荐优先选拔。' },
    { id: 2, name: '韦大勇', unit: '南宁市公安局', tier: 's', tierLabel: 'S', rank: 2, totalScore: 94.2, studyHours: 115, passRate: 98, avatarColor: '#003087', highlights: ['反诈骨干', '执法规范'], aiNote: 'AI评估：反诈能力突出，适合专项岗位。' },
    { id: 3, name: '韦志鹏', unit: '玉林市公安局', tier: 's', tierLabel: 'S', rank: 3, totalScore: 92.5, studyHours: 98, passRate: 95, avatarColor: '#52c41a', highlights: ['网安技术', '全勤'], aiNote: 'AI评估：综合素质优秀，技术过硬。' },
    { id: 4, name: '蓝天宇', unit: '南宁市公安局', tier: 'a', tierLabel: 'A', rank: 4, totalScore: 88.0, studyHours: 86, passRate: 90, avatarColor: '#722ed1', highlights: ['进步最快', '积极参与'], aiNote: 'AI评估：近3个月进步显著，可持续关注。' },
    { id: 5, name: '谢建国', unit: '贺州市公安局', tier: 'a', tierLabel: 'A', rank: 5, totalScore: 85.5, studyHours: 79, passRate: 88, avatarColor: '#eb2f96', highlights: ['基层骨干', '群众路线'], aiNote: 'AI评估：群众工作能力强，适合社区岗位。' },
    { id: 6, name: '陈小红', unit: '南宁市公安局', tier: 'b', tierLabel: 'B', rank: 6, totalScore: 78.2, studyHours: 65, passRate: 80, avatarColor: '#fa8c16', highlights: ['稳定发挥'], aiNote: 'AI评估：表现稳定，建议加强证据技能培训。' },
]

// 课程答疑 mock
export const MOCK_COURSE_QA = [
    { id: 1, user: '张伟', question: '第3章的拘留时限是指连续72小时还是可以延长？', answer: '拘留后侦查羁押一般不超过37天，但有特殊情形可申请延长。' },
    { id: 2, user: '韦大勇', question: '视频中的表格能下载吗？', answer: null },
    { id: 3, user: '蓝天宇', question: '现场勘查时如何正确保护电子证据？', answer: '首先断网隔离，避免远程擦除，然后使用专用取证设备提取数据。' },
]
