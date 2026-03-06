export const MOCK_TRAININGS = [
  {
    id: 't001',
    name: '2025年春季刑侦专项训练班（第一期）',
    type: 'special',
    typeLabel: '专项训练',
    status: 'active',
    startDate: '2025-03-03',
    endDate: '2025-03-28',
    location: '广西公安警察学院第三训练楼 201教室',
    instructorId: 'u002',
    instructorName: '李志强',
    capacity: 40,
    enrolled: 38,
    students: ['u003', 'u004', 'u005', 'u006', 'u008'],
    description: '针对全区刑警大队骨干人员开展的专项强化训练，重点提升刑事侦查、证据固定、审讯技巧等核心能力。',
    subjects: ['刑事法律法规', '侦查技术', '审讯实务', '证据固定', '案例复盘'],
    courses: [
      {
        name: '刑事诉讼法实务操作', instructor: '李志强', hours: 12, type: 'theory',
        schedules: [
          { date: '2025-03-10', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-10', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-03-11', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-11', timeRange: '14:30~17:30', hours: 3 }
        ]
      },
      {
        name: '现场勘查技术', instructor: '王技术官', hours: 16, type: 'practice',
        schedules: [
          { date: '2025-03-12', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-12', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-03-13', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-13', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-03-14', timeRange: '08:30~12:30', hours: 4 }
        ]
      },
      {
        name: '审讯技巧与策略', instructor: '李志强', hours: 10, type: 'theory',
        schedules: [
          { date: '2025-03-17', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-17', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-03-18', timeRange: '08:30~12:30', hours: 4 }
        ]
      },
      {
        name: '体能与战术格斗', instructor: '梁勇', hours: 10, type: 'practice',
        schedules: [
          { date: '2025-03-19', timeRange: '09:00~11:00', hours: 2 },
          { date: '2025-03-19', timeRange: '15:00~17:00', hours: 2 },
          { date: '2025-03-20', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-20', timeRange: '14:30~17:30', hours: 3 }
        ]
      },
    ],
    checkinRecords: [
      { sessionKey: 'start', studentId: 'u003', name: '张伟', time: '08:45', date: '2025-03-03', status: 'on_time' },
      { sessionKey: 'start', studentId: 'u004', name: '陈小红', time: '08:52', date: '2025-03-03', status: 'on_time' },
      { sessionKey: 'start', studentId: 'u005', name: '黄明', time: '09:12', date: '2025-03-03', status: 'late' },
      { sessionKey: 'start', studentId: 'u006', name: '韦大勇', time: '08:58', date: '2025-03-03', status: 'on_time' },
      { sessionKey: 'course-0-0', studentId: 'u003', name: '张伟', time: '08:50', date: '2025-03-10', status: 'on_time' },
      { sessionKey: 'course-0-0', studentId: 'u004', name: '陈小红', time: '08:55', date: '2025-03-10', status: 'on_time' },
      { sessionKey: 'course-0-0', studentId: 'u005', name: '黄明', time: '09:05', date: '2025-03-10', status: 'late' },
      { sessionKey: 'course-0-0', studentId: 'u006', name: '韦大勇', time: '08:42', date: '2025-03-10', status: 'on_time' },
      { sessionKey: 'course-0-0', studentId: 'u008', name: '蓝天宇', time: null, date: '2025-03-10', status: 'absent' },
      { sessionKey: 'course-0-1', studentId: 'u003', name: '张伟', time: '14:20', date: '2025-03-10', status: 'on_time' },
      { sessionKey: 'course-0-1', studentId: 'u004', name: '陈小红', time: '14:25', date: '2025-03-10', status: 'on_time' },
      { sessionKey: 'course-0-1', studentId: 'u005', name: '黄明', time: '14:28', date: '2025-03-10', status: 'on_time' },
      { sessionKey: 'course-0-1', studentId: 'u006', name: '韦大勇', time: '14:35', date: '2025-03-10', status: 'late' },
      { sessionKey: 'course-0-1', studentId: 'u008', name: '蓝天宇', time: '14:22', date: '2025-03-10', status: 'on_time' },
    ],
  },
  {
    id: 't002',
    name: '南宁市派出所所长专题培训班',
    type: 'promotion',
    typeLabel: '晋升培训',
    status: 'upcoming',
    startDate: '2025-04-07',
    endDate: '2025-04-18',
    location: '广西公安警察学院行政楼 报告厅',
    instructorId: 'u015',
    instructorName: '覃国强',
    capacity: 60,
    enrolled: 52,
    students: [],
    description: '面向南宁市各派出所所长及候选人，重点培训基层警务管理、警情分析、社区治理等领导力课程。',
    subjects: ['基层警务管理', '警情数据分析', '社区治理', '廉政教育'],
    courses: [
      {
        name: '基层警务管理实务', instructor: '覃国强', hours: 14, type: 'theory',
        schedules: [
          { date: '2025-04-07', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-04-07', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-04-08', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-04-08', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-04-09', timeRange: '09:00~11:00', hours: 2 }
        ]
      },
      {
        name: '警情数据分析方法', instructor: '覃志文', hours: 8, type: 'theory',
        schedules: [
          { date: '2025-04-10', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-04-10', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-04-11', timeRange: '09:00~11:00', hours: 2 }
        ]
      },
      {
        name: '廉政警示教育', instructor: '纪委讲师', hours: 4, type: 'theory',
        schedules: [
          { date: '2025-04-14', timeRange: '08:30~12:30', hours: 4 }
        ]
      },
      {
        name: '社区治理案例研讨', instructor: '黄丽华', hours: 10, type: 'practice',
        schedules: [
          { date: '2025-04-15', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-04-15', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-04-16', timeRange: '08:30~12:30', hours: 4 }
        ]
      },
    ],
    checkinRecords: [],
  },
  {
    id: 't003',
    name: '2024年冬季基础训练（交通类）',
    type: 'basic',
    typeLabel: '基础训练',
    status: 'ended',
    startDate: '2024-12-02',
    endDate: '2024-12-20',
    location: '南宁市公安局培训中心',
    instructorId: 'u011',
    instructorName: '刘海波',
    capacity: 50,
    enrolled: 48,
    students: [],
    description: '面向交警大队全体民警的年度基础训练，涵盖交通法规更新、执法规范、文明执勤等内容。',
    subjects: ['交通法规更新', '执法规范', '文明执勤', '事故处置'],
    courses: [
      {
        name: '交通法规更新解读', instructor: '刘海波', hours: 8, type: 'theory',
        schedules: [
          { date: '2024-12-05', timeRange: '09:00~11:00', hours: 2 },
          { date: '2024-12-05', timeRange: '14:30~16:30', hours: 2 },
          { date: '2024-12-06', timeRange: '09:00~11:00', hours: 2 },
          { date: '2024-12-06', timeRange: '14:30~16:30', hours: 2 }
        ]
      },
      {
        name: '执法规范化训练', instructor: '刘海波', hours: 12, type: 'practice',
        schedules: [
          { date: '2024-12-10', timeRange: '09:00~12:00', hours: 3 },
          { date: '2024-12-10', timeRange: '14:30~17:30', hours: 3 },
          { date: '2024-12-11', timeRange: '09:00~12:00', hours: 3 },
          { date: '2024-12-11', timeRange: '14:30~17:30', hours: 3 }
        ]
      },
      {
        name: '交通事故处置演练', instructor: '技术支队', hours: 10, type: 'practice',
        schedules: [
          { date: '2024-12-16', timeRange: '09:00~12:00', hours: 3 },
          { date: '2024-12-16', timeRange: '14:30~17:30', hours: 3 },
          { date: '2024-12-17', timeRange: '08:30~12:30', hours: 4 }
        ]
      },
    ],
    checkinRecords: [
      { sessionKey: 'start', studentId: 'u004', name: '陈小红', time: '08:50', date: '2024-12-02', status: 'on_time' },
      { sessionKey: 'start', studentId: 'u016', name: '李大明', time: '09:10', date: '2024-12-02', status: 'late' },
      { sessionKey: 'start', studentId: 'u017', name: '黄秀华', time: '08:58', date: '2024-12-02', status: 'on_time' },
      { sessionKey: 'start', studentId: 'u018', name: '陈志远', time: '08:45', date: '2024-12-02', status: 'on_time' },
      { sessionKey: 'course-0-0', studentId: 'u004', name: '陈小红', time: '08:55', date: '2024-12-05', status: 'on_time' },
      { sessionKey: 'course-0-0', studentId: 'u016', name: '李大明', time: '09:12', date: '2024-12-05', status: 'late' },
      { sessionKey: 'course-0-0', studentId: 'u017', name: '黄秀华', time: '08:58', date: '2024-12-05', status: 'on_time' },
      { sessionKey: 'course-0-0', studentId: 'u018', name: '陈志远', time: null, date: '2024-12-05', status: 'absent' },
    ],
  },
  {
    id: 't004',
    name: '2025年网络安全与数字取证专项班',
    type: 'special',
    typeLabel: '专项训练',
    status: 'active',
    startDate: '2025-02-24',
    endDate: '2025-03-21',
    location: '桂林市公安局数字化训练中心',
    instructorId: 'u013',
    instructorName: '覃志文',
    capacity: 30,
    enrolled: 28,
    students: ['u003', 'u005', 'u019', 'u020'],
    description: '面向全区网安部门及技术骨干，系统培训数字取证、电子数据分析及网络犯罪侦查技术。',
    subjects: ['网络犯罪识别', '数字取证技术', '手机取证实务', '暗网追踪', '电子证据规范'],
    courses: [
      {
        name: '网络犯罪侦查技术', instructor: '覃志文', hours: 16, type: 'theory',
        schedules: [
          { date: '2025-02-25', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-02-25', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-02-26', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-02-26', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-02-27', timeRange: '08:30~12:30', hours: 4 }
        ]
      },
      {
        name: '数字取证实操', instructor: '覃志文', hours: 20, type: 'practice',
        schedules: [
          { date: '2025-03-03', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-03', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-03-04', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-04', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-03-05', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-05', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-03-06', timeRange: '09:00~11:00', hours: 2 }
        ]
      },
      {
        name: '电子证据法律规范', instructor: '李志强', hours: 6, type: 'theory',
        schedules: [
          { date: '2025-03-10', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-10', timeRange: '14:30~17:30', hours: 3 }
        ]
      },
    ],
    checkinRecords: [
      { sessionKey: 'start', studentId: 'u003', name: '张伟', time: '08:50', date: '2025-02-24', status: 'on_time' },
      { sessionKey: 'start', studentId: 'u005', name: '黄明', time: '09:10', date: '2025-02-24', status: 'late' },
      { sessionKey: 'start', studentId: 'u019', name: '韦志鹏', time: '08:58', date: '2025-02-24', status: 'on_time' },
      { sessionKey: 'start', studentId: 'u020', name: '廖宇航', time: '08:45', date: '2025-02-24', status: 'on_time' },
      { sessionKey: 'course-1-0', studentId: 'u003', name: '张伟', time: '09:00', date: '2025-03-03', status: 'on_time' },
      { sessionKey: 'course-1-0', studentId: 'u005', name: '黄明', time: '09:08', date: '2025-03-03', status: 'on_time' },
      { sessionKey: 'course-1-0', studentId: 'u019', name: '韦志鹏', time: '09:18', date: '2025-03-03', status: 'late' },
      { sessionKey: 'course-1-0', studentId: 'u020', name: '廖宇航', time: '09:02', date: '2025-03-03', status: 'on_time' },
    ],
  },
  {
    id: 't005',
    name: '广西公安反诈骨干强化培训班（第二期）',
    type: 'special',
    typeLabel: '专项训练',
    status: 'active',
    startDate: '2025-03-10',
    endDate: '2025-04-04',
    location: '广西公安警察学院第一训练楼 301教室',
    instructorId: 'u010',
    instructorName: '陈建华',
    capacity: 50,
    enrolled: 47,
    students: ['u006', 'u008', 'u021', 'u022', 'u023'],
    description: '针对全区反诈骗中心骨干人员，深化电信网络诈骗打击处理能力，重点培训资金追踪、跨境协作等核心技战法。',
    subjects: ['电诈案件侦办', '资金追踪技术', '反诈宣传策略', '典型案例复盘'],
    courses: [
      {
        name: '电信诈骗案件侦办实务', instructor: '陈建华', hours: 18, type: 'theory',
        schedules: [
          { date: '2025-03-11', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-11', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-03-12', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-12', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-03-13', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-13', timeRange: '14:30~17:30', hours: 3 }
        ]
      },
      {
        name: '资金流追踪技术实训', instructor: '陈建华', hours: 14, type: 'practice',
        schedules: [
          { date: '2025-03-18', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-18', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-03-19', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-19', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-03-20', timeRange: '09:00~11:00', hours: 2 }
        ]
      },
      {
        name: '反诈宣传技能', instructor: '黄丽华', hours: 8, type: 'practice',
        schedules: [
          { date: '2025-03-25', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-03-25', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-03-26', timeRange: '09:00~11:00', hours: 2 }
        ]
      },
    ],
    checkinRecords: [
      { sessionKey: 'start', studentId: 'u006', name: '韦大勇', time: '08:52', date: '2025-03-10', status: 'on_time' },
      { sessionKey: 'start', studentId: 'u008', name: '蓝天宇', time: '08:45', date: '2025-03-10', status: 'on_time' },
      { sessionKey: 'start', studentId: 'u021', name: '谢建国', time: '09:01', date: '2025-03-10', status: 'on_time' },
      { sessionKey: 'start', studentId: 'u022', name: '林丽萍', time: '08:58', date: '2025-03-10', status: 'on_time' },
      { sessionKey: 'start', studentId: 'u023', name: '苏伟强', time: null, date: '2025-03-10', status: 'absent' },
      { sessionKey: 'course-0-0', studentId: 'u006', name: '韦大勇', time: '08:59', date: '2025-03-11', status: 'on_time' },
      { sessionKey: 'course-0-0', studentId: 'u008', name: '蓝天宇', time: '09:12', date: '2025-03-11', status: 'late' },
      { sessionKey: 'course-0-0', studentId: 'u021', name: '谢建国', time: '08:53', date: '2025-03-11', status: 'on_time' },
      { sessionKey: 'course-0-0', studentId: 'u022', name: '林丽萍', time: '09:00', date: '2025-03-11', status: 'on_time' },
    ],
  },
  {
    id: 't006',
    name: '2025年警务实战技能提升班（柳州）',
    type: 'basic',
    typeLabel: '基础训练',
    status: 'upcoming',
    startDate: '2025-04-14',
    endDate: '2025-04-25',
    location: '柳州市公安局警务训练基地',
    instructorId: 'u014',
    instructorName: '梁勇',
    capacity: 45,
    enrolled: 38,
    students: [],
    description: '面向柳州市基层一线民警，强化警务实战技能，提升执法现场处置能力和安全防护意识。',
    subjects: ['体能训练标准', '徒手控制技术', '防卫与反击', '战术配合'],
    courses: [
      {
        name: '体能达标训练', instructor: '梁勇', hours: 20, type: 'practice',
        schedules: [
          { date: '2025-04-14', timeRange: '09:00~11:00', hours: 2 },
          { date: '2025-04-14', timeRange: '15:00~17:00', hours: 2 },
          { date: '2025-04-15', timeRange: '09:00~11:00', hours: 2 },
          { date: '2025-04-15', timeRange: '15:00~17:00', hours: 2 },
          { date: '2025-04-16', timeRange: '09:00~11:00', hours: 2 },
          { date: '2025-04-16', timeRange: '15:00~17:00', hours: 2 },
          { date: '2025-04-17', timeRange: '09:00~11:00', hours: 2 },
          { date: '2025-04-17', timeRange: '15:00~17:00', hours: 2 },
          { date: '2025-04-18', timeRange: '08:30~12:30', hours: 4 }
        ]
      },
      {
        name: '徒手控制与防卫技术', instructor: '梁勇', hours: 16, type: 'practice',
        schedules: [
          { date: '2025-04-21', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-04-21', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-04-22', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-04-22', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-04-23', timeRange: '08:30~12:30', hours: 4 }
        ]
      },
      {
        name: '警械使用规范', instructor: '梁勇', hours: 8, type: 'theory',
        schedules: [
          { date: '2025-04-24', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-04-24', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-04-25', timeRange: '09:00~11:00', hours: 2 }
        ]
      },
    ],
    checkinRecords: [],
  },
  {
    id: 't007',
    name: '2024年度警务管理干部晋升培训班',
    type: 'promotion',
    typeLabel: '晋升培训',
    status: 'ended',
    startDate: '2024-10-14',
    endDate: '2024-10-25',
    location: '广西公安警察学院行政楼',
    instructorId: 'u015',
    instructorName: '覃国强',
    capacity: 40,
    enrolled: 40,
    students: [],
    description: '面向全区公安机关拟提任科级领导职务的干部，系统培训警务管理、廉政建设、依法行政等综合能力。',
    subjects: ['警务管理实务', '廉政教育', '依法行政', '危机应对'],
    courses: [
      {
        name: '警务行政管理', instructor: '覃国强', hours: 12, type: 'theory',
        schedules: [
          { date: '2024-10-15', timeRange: '09:00~12:00', hours: 3 },
          { date: '2024-10-15', timeRange: '14:30~17:30', hours: 3 },
          { date: '2024-10-16', timeRange: '09:00~12:00', hours: 3 },
          { date: '2024-10-16', timeRange: '14:30~17:30', hours: 3 }
        ]
      },
      {
        name: '廉政法规专题', instructor: '纪委讲师', hours: 6, type: 'theory',
        schedules: [
          { date: '2024-10-18', timeRange: '09:00~12:00', hours: 3 },
          { date: '2024-10-18', timeRange: '14:30~17:30', hours: 3 }
        ]
      },
      {
        name: '危机应对与舆论管理', instructor: '专家教授', hours: 6, type: 'theory',
        schedules: [
          { date: '2024-10-21', timeRange: '09:00~12:00', hours: 3 },
          { date: '2024-10-21', timeRange: '14:30~17:30', hours: 3 }
        ]
      },
    ],
    checkinRecords: [
      { sessionKey: 'start', studentId: 'u024', name: '黎明远', time: '08:50', date: '2024-10-14', status: 'on_time' },
      { sessionKey: 'start', studentId: 'u025', name: '莫云飞', time: '09:00', date: '2024-10-14', status: 'on_time' },
      { sessionKey: 'start', studentId: 'u026', name: '潘玉凤', time: '08:55', date: '2024-10-14', status: 'on_time' },
      { sessionKey: 'start', studentId: 'u027', name: '周志军', time: '09:05', date: '2024-10-14', status: 'late' },
      { sessionKey: 'course-0-0', studentId: 'u024', name: '黎明远', time: '08:55', date: '2024-10-15', status: 'on_time' },
      { sessionKey: 'course-0-0', studentId: 'u025', name: '莫云飞', time: '09:00', date: '2024-10-15', status: 'on_time' },
      { sessionKey: 'course-0-0', studentId: 'u026', name: '潘玉凤', time: '08:58', date: '2024-10-15', status: 'on_time' },
      { sessionKey: 'course-0-0', studentId: 'u027', name: '周志军', time: '09:12', date: '2024-10-15', status: 'late' },
    ],
  },
  {
    id: 't008',
    name: '2025年社区警务与矛盾化解专题班',
    type: 'special',
    typeLabel: '专项训练',
    status: 'upcoming',
    startDate: '2025-05-06',
    endDate: '2025-05-16',
    location: '南宁市公安局培训中心 多功能厅',
    instructorId: 'u012',
    instructorName: '黄丽华',
    capacity: 35,
    enrolled: 22,
    students: [],
    description: '针对社区警务站民警，强化矛盾纠纷调解、群众工作方法及社区治理服务能力。',
    subjects: ['社区治理体系', '矛盾纠纷调解', '群众工作方法', '信息收集与研判'],
    courses: [
      {
        name: '社区警务工作方法', instructor: '黄丽华', hours: 12, type: 'theory',
        schedules: [
          { date: '2025-05-06', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-05-06', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-05-07', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-05-07', timeRange: '14:30~17:30', hours: 3 }
        ]
      },
      {
        name: '矛盾调解实战演练', instructor: '黄丽华', hours: 10, type: 'practice',
        schedules: [
          { date: '2025-05-08', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-05-08', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-05-09', timeRange: '08:30~12:30', hours: 4 }
        ]
      },
      {
        name: '群众信息采集规范', instructor: '覃国强', hours: 8, type: 'theory',
        schedules: [
          { date: '2025-05-12', timeRange: '09:00~12:00', hours: 3 },
          { date: '2025-05-12', timeRange: '14:30~17:30', hours: 3 },
          { date: '2025-05-13', timeRange: '09:00~11:00', hours: 2 }
        ]
      },
    ],
    checkinRecords: [],
  },
]

// 模拟新签到的学员列表（用于签到页面动画）
export const LATE_CHECKIN_STUDENTS = [
  { studentId: 'u007', name: '覃玉兰', time: '09:32', status: 'late' },
  { studentId: 'u009', name: '罗强', time: '09:41', status: 'late' },
]

// 培训类型配置
export const TRAINING_TYPES = [
  { value: 'basic', label: '基础训练' },
  { value: 'special', label: '专项训练' },
  { value: 'promotion', label: '晋升培训' },
  { value: 'online', label: '线上培训' },
]
