<template>
  <div class="training-detail-page">
    <a-breadcrumb style="margin-bottom:16px">
      <a-breadcrumb-item @click="$router.push('/training')" style="cursor:pointer;color:var(--police-primary)">培训班管理</a-breadcrumb-item>
      <a-breadcrumb-item>{{ training.name }}</a-breadcrumb-item>
    </a-breadcrumb>

    <a-row :gutter="20">
      <a-col :span="16">
        <a-card :bordered="false" class="main-card">
          <div class="training-banner" :class="'status-' + training.status">
            <div class="banner-content">
              <a-tag :color="statusColorMap[training.status]" class="status-tag">{{ statusLabels[training.status] }}</a-tag>
              <h2 class="training-title">{{ training.name }}</h2>
              <div class="training-meta-row">
                <span><CalendarOutlined /> {{ training.startDate }} ~ {{ training.endDate }}</span>
                <span><EnvironmentOutlined /> {{ training.location }}</span>
                <span><UserOutlined /> 主讲：{{ training.instructorName }}</span>
              </div>
            </div>
          </div>

          <a-tabs v-model:activeKey="activeTab" style="margin-top:16px">
            <a-tab-pane key="overview" tab="班级概览">
              <div class="overview-stats">
                <div class="ov-stat" v-for="s in overviewStats" :key="s.label">
                  <div class="ov-num" :style="{ color: s.color }">{{ s.value }}</div>
                  <div class="ov-label">{{ s.label }}</div>
                </div>
              </div>
              <a-divider />
              <div class="course-schedule">
                <h4>课程安排</h4>
                <div class="course-item" v-for="c in training.courses" :key="c.name">
                  <div class="ci-left">
                    <div class="ci-name">{{ c.name }}</div>
                    <div class="ci-instructor">{{ c.instructor }}</div>
                  </div>
                  <div class="ci-right">
                    <span class="ci-hours">{{ c.hours }}课时</span>
                    <a-tag :color="c.type === 'theory' ? 'blue' : 'green'" size="small">{{ c.type === 'theory' ? '理论' : '实操' }}</a-tag>
                  </div>
                </div>
              </div>
            </a-tab-pane>

            <a-tab-pane key="students" tab="学员名单">
              <a-input-search v-model:value="studentSearch" placeholder="搜索学员..." style="width:240px;margin-bottom:16px" />
              <a-table :dataSource="filteredStudents" :columns="studentColumns" size="small" :pagination="{ pageSize: 10 }">
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'progress'">
                    <a-progress :percent="record.progress" size="small" />
                  </template>
                  <template v-if="column.key === 'checkin'">
                    <span :style="{ color: record.checkinRate >= 90 ? '#52c41a' : record.checkinRate >= 70 ? '#faad14' : '#ff4d4f' }">
                      {{ record.checkinRate }}%
                    </span>
                  </template>
                </template>
              </a-table>
            </a-tab-pane>

            <a-tab-pane key="notice" tab="公告">
              <div class="notice-list">
                <div v-for="n in notices" :key="n.id" class="notice-item">
                  <div class="notice-header">
                    <span class="notice-title">{{ n.title }}</span>
                    <span class="notice-time">{{ n.time }}</span>
                  </div>
                  <div class="notice-content">{{ n.content }}</div>
                </div>
              </div>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>

      <a-col :span="8">
        <a-card title="快捷操作" :bordered="false" style="margin-bottom:16px">
          <div class="quick-ops">
            <a-button block style="margin-bottom:8px" @click="$router.push('/training/checkin/' + training.id)" type="primary">
              <template #icon><QrcodeOutlined /></template>开始签到
            </a-button>
            <a-button block style="margin-bottom:8px" @click="$router.push('/training/schedule')">
              <template #icon><CalendarOutlined /></template>查看日程
            </a-button>
            <a-button block @click="exportMsg">
              <template #icon><DownloadOutlined /></template>导出学员名单
            </a-button>
          </div>
        </a-card>

        <a-card title="签到率统计" :bordered="false">
          <div class="checkin-summary">
            <a-progress type="circle" :percent="checkinRate" :stroke-color="{ '0%': '#003087', '100%': '#52c41a' }" />
            <div class="checkin-detail">
              <div class="cd-item green">已签到 {{ onTimeCount }} 人</div>
              <div class="cd-item orange">迟到 {{ lateCount }} 人</div>
              <div class="cd-item red">缺席 {{ absentCount }} 人</div>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { CalendarOutlined, EnvironmentOutlined, UserOutlined, QrcodeOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import { MOCK_TRAININGS } from '@/mock/trainings'

const route = useRoute()
const trainingId = route.params.id
const training = MOCK_TRAININGS.find(t => t.id === trainingId) || MOCK_TRAININGS[0]

const activeTab = ref('overview')
const studentSearch = ref('')

const statusLabels = { active: '进行中', upcoming: '未开始', ended: '已结束' }
const statusColorMap = { active: 'green', upcoming: 'orange', ended: 'default' }

const overviewStats = [
  { label: '报名人数', value: training.enrolled, color: '#003087' },
  { label: '班级容量', value: training.capacity, color: '#555' },
  { label: '已完成学员', value: Math.floor((training.enrolled || 0) * 0.6), color: '#52c41a' },
  { label: '课程总学时', value: (training.courses || []).reduce((a, c) => a + (c.hours || 0), 0) || 48, color: '#faad14' },
]

const trainingWithCourses = {
  ...training,
  courses: training.courses?.length ? training.courses : [
    { name: '刑事诉讼法实务操作', instructor: '李教官', hours: 12, type: 'theory' },
    { name: '现场处置技能', instructor: '王教官', hours: 16, type: 'practice' },
    { name: '电信诈骗案件侦办', instructor: '张教官', hours: 8, type: 'theory' },
    { name: '体能训练', instructor: '刘教官', hours: 12, type: 'practice' },
  ]
}

const mockStudents = Array.from({ length: 15 }, (_, i) => ({
  key: i,
  name: ['张明', '李华', '王刚', '陈红', '刘洋', '赵伟', '孙丽', '周明', '吴强', '郑浩', '钱磊', '冯雪', '蒋峰', '谢辉', '韩婷'][i],
  policeId: `GX2024${String(i+1).padStart(3,'0')}`,
  unit: ['南宁市公安局', '桂林市公安局', '柳州市公安局'][i % 3],
  progress: [100, 82, 65, 40, 95, 78, 55, 90, 33, 72, 88, 61, 45, 99, 70][i],
  checkinRate: [100, 90, 85, 75, 95, 80, 70, 90, 60, 85, 95, 75, 65, 100, 80][i],
}))

const filteredStudents = computed(() =>
  studentSearch.value ? mockStudents.filter(s => s.name.includes(studentSearch.value) || s.policeId.includes(studentSearch.value)) : mockStudents
)

const studentColumns = [
  { title: '姓名', dataIndex: 'name', key: 'name' },
  { title: '工号', dataIndex: 'policeId', key: 'policeId' },
  { title: '单位', dataIndex: 'unit', key: 'unit' },
  { title: '学习进度', key: 'progress', width: 120 },
  { title: '签到率', key: 'checkin', width: 80 },
]

const onTimeCount = training.checkinRecords?.filter(r => r.status === 'on_time').length || 0
const lateCount = training.checkinRecords?.filter(r => r.status === 'late').length || 0
const absentCount = training.checkinRecords?.filter(r => r.status === 'absent').length || 0
const checkinRate = Math.round(((onTimeCount + lateCount) / (training.checkinRecords?.length || 1)) * 100)

const notices = [
  { id: 1, title: '本周六体能测试通知', time: '2025-03-10', content: '本周六上午9:00在训练场进行体能测试，请携带运动装备，准时参加。' },
  { id: 2, title: '教材发放通知', time: '2025-03-08', content: '本次培训教材已到位，请于本周四前往综合楼312室领取。' },
]

const exportMsg = () => message.success('学员名单已导出！')
</script>

<style scoped>
.training-detail-page { padding: 0; }
.main-card { }
.training-banner { padding: 24px; border-radius: 8px; margin-bottom: 4px; }
.training-banner.status-active { background: linear-gradient(135deg, #001a50, #003087); }
.training-banner.status-upcoming { background: linear-gradient(135deg, #78350f, #b45309); }
.training-banner.status-ended { background: linear-gradient(135deg, #374151, #6b7280); }
.status-tag { margin-bottom: 8px; }
.training-title { color: #fff; font-size: 20px; margin: 8px 0; }
.training-meta-row { display: flex; gap: 20px; color: rgba(255,255,255,0.8); font-size: 13px; flex-wrap: wrap; }
.overview-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
.ov-stat { text-align: center; padding: 16px; background: #f8f9ff; border-radius: 8px; }
.ov-num { font-size: 28px; font-weight: 700; }
.ov-label { font-size: 12px; color: #888; margin-top: 4px; }
.course-schedule { }
.course-schedule h4 { margin-bottom: 12px; color: #333; }
.course-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.ci-name { font-size: 14px; font-weight: 500; }
.ci-instructor { font-size: 12px; color: #888; }
.ci-hours { font-size: 14px; color: var(--police-primary); font-weight: 600; margin-right: 8px; }
.notice-list { display: flex; flex-direction: column; gap: 12px; }
.notice-item { padding: 14px; border: 1px solid #e8e8e8; border-radius: 6px; border-left: 3px solid var(--police-primary); }
.notice-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
.notice-title { font-weight: 600; color: #1a1a1a; }
.notice-time { font-size: 12px; color: #888; }
.notice-content { font-size: 13px; color: #555; line-height: 1.6; }
.quick-ops { }
.checkin-summary { display: flex; align-items: center; gap: 20px; }
.checkin-detail { display: flex; flex-direction: column; gap: 8px; }
.cd-item { font-size: 14px; }
.cd-item.green { color: #52c41a; }
.cd-item.orange { color: #faad14; }
.cd-item.red { color: #ff4d4f; }
</style>
