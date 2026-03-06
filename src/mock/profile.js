// 个人主页 mock 数据
export const MOCK_ABILITIES = [
    { label: '法律知识', score: 88 },
    { label: '执法规范', score: 72 },
    { label: '证据意识', score: 64 },
    { label: '体能标准', score: 95 },
    { label: '警察素养', score: 91 },
]

export const MOCK_EXAM_HISTORY = [
    { key: 1, title: '刑事法律基础考试', date: '2025-03-05', score: 78, passed: true },
    { key: 2, title: '执法规范化测验', date: '2025-02-20', score: 92, passed: true },
    { key: 3, title: '反诈实务知识考核', date: '2025-01-15', score: 58, passed: false },
    { key: 4, title: '公共安全知识测试', date: '2024-12-10', score: 85, passed: true },
]

export const MOCK_CERT_LIST = [
    { id: 1, name: '优秀学员', issuer: '广西公安厅', date: '2024-12-31' },
    { id: 2, name: '执法能手', issuer: '南宁市公安局', date: '2024-06-15' },
    { id: 3, name: '年度先进个人', issuer: '青秀区公安局', date: '2024-03-01' },
]

export const MOCK_POINT_HISTORY = [
    { id: 1, action: '完成课程「电信诈骗案件侦办」', points: 50 },
    { id: 2, action: '通过月度考试', points: 100 },
    { id: 3, action: '签到打卡', points: 5 },
    { id: 4, action: '迟到扣分', points: -10 },
    { id: 5, action: '完成课程「刑事侦查技术」', points: 50 },
    { id: 6, action: '笔记被点赞', points: 10 },
]
