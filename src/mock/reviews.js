// 教官/学员评价 & 培训记录 mock 数据
import { MOCK_TRAININGS } from './trainings'
import { MOCK_USER_LIST } from './users'

// 通用评价（根据被评人动态生成）
export const MOCK_REVIEWS = [
    { id: 1, user: '张伟', rating: 5, date: '2025-03-01', content: '讲课深入浅出，案例生动，学完很有收获，强烈推荐！', tags: ['内容丰富', '互动性强', '实用性高'] },
    { id: 2, user: '韦大勇', rating: 4, date: '2025-02-20', content: '理论知识讲解很扎实，实操环节还可以再多一些。', tags: ['理论扎实', '专业权威'] },
    { id: 3, user: '蓝天宇', rating: 5, date: '2025-02-10', content: '老师很有耐心，答疑及时，遇到问题都能快速解答。', tags: ['耐心负责', '答疑及时'] },
    { id: 4, user: '陈小红', rating: 4, date: '2025-01-15', content: '课程安排合理，内容贴合实际工作需要。', tags: ['贴合实际', '实用'] },
    { id: 5, user: '黄明', rating: 5, date: '2024-12-20', content: '通过这次培训受益匪浅，对执法规范有了更深的理解。', tags: ['受益匪浅', '规范'] },
]

// 培训记录 — 从 MOCK_TRAININGS 动态生成
export function getTrainingHistory(personId) {
    return MOCK_TRAININGS
        .filter(t => t.students.includes(personId) || t.instructorId === personId)
        .map((t, i) => ({
            key: i + 1,
            title: t.name,
            period: `${t.startDate} ~ ${t.endDate}`,
            students: t.enrolled,
            score: (4.5 + Math.random() * 0.5).toFixed(1),
        }))
}
