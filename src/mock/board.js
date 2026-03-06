// 培训看板 mock 数据

export const MOCK_CITIES = ['南宁市', '柳州市', '桂林市', '梧州市', '北海市', '防城港', '钦州市', '贵港市', '玉林市', '百色市', '贺州市', '河池市', '来宾市', '崇左市']

export const MOCK_BASE_CITY_VALUES = [45, 36, 31, 19, 17, 14, 16, 15, 18, 13, 11, 12, 11, 9]

export const MOCK_WARNINGS = [
    { id: 1, text: '南宁市青秀区25名学员签到率低于60%，连续3天未完成课时', time: '今日 09:32', level: 'high' },
    { id: 2, text: '桂林市刑警支队培训班第4天缺勤率超过20%', time: '今日 08:15', level: 'high' },
    { id: 3, text: '柳州市城中区培训班8名学员请假未返，超出允许天数', time: '昨日 16:40', level: 'medium' },
    { id: 4, text: '梧州市第2期培训班课时进度落后计划3天', time: '昨日 14:20', level: 'medium' },
    { id: 5, text: '百色市右江区有4名学员结业考试不合格，需安排补考', time: '2天前', level: 'medium' },
]

export const MOCK_CITY_RANKS = [
    { name: '南宁市', rate: 94 },
    { name: '桂林市', rate: 91 },
    { name: '柳州市', rate: 88 },
    { name: '北海市', rate: 85 },
    { name: '梧州市', rate: 82 },
    { name: '玉林市', rate: 79 },
    { name: '贵港市', rate: 76 },
    { name: '钦州市', rate: 73 },
]

export function getTrainingNotices(trainingData) {
    if (!trainingData) return []
    return [
        { id: 1, title: '开班及教材发放通知', time: trainingData.startDate, content: `本次培训【${trainingData.name}】教材已到位，请于开班当天前往培训点领取。` },
        { id: 2, title: '体能测试及考核通知', time: trainingData.endDate, content: '结业周将进行统一考核，请携带好装备。' },
    ]
}
