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

            <a-tab-pane key="students" tab="学员名单" v-if="!authStore.isStudent">
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
            <!-- 管理员/教官：任何 active 班都可以开始签到 -->
            <a-button block style="margin-bottom:8px" @click="$router.push('/training/checkin/' + training.id)" type="primary" v-if="training.status === 'active' && !authStore.isStudent">
              <template #icon><QrcodeOutlined /></template>开始签到
            </a-button>
            <!-- 学员：只有在该班名单中且 active 才能扫码签到 -->
            <a-button block style="margin-bottom:8px" @click="$router.push('/training/checkin/' + training.id)" type="primary" v-if="training.status === 'active' && authStore.isStudent && isEnrolled">
              <template #icon><QrcodeOutlined /></template>扫码签到
            </a-button>
            <a-button block style="margin-bottom:8px" @click="$router.push('/training/schedule/' + training.id)">
              <template #icon><CalendarOutlined /></template>查看日程
            </a-button>
            <a-button block @click="exportMsg" v-if="!authStore.isStudent">
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
import { MOCK_USER_LIST } from '@/mock/users'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const trainingId = route.params.id
const training = MOCK_TRAININGS.find(t => t.id === trainingId) || MOCK_TRAININGS[0]

const activeTab = ref('overview')
const studentSearch = ref('')

const statusLabels = { active: '进行中', upcoming: '未开始', ended: '已结束' }
const statusColorMap = { active: 'green', upcoming: 'orange', ended: 'default' }

// 动态统计数据
const checkinRecords = training.checkinRecords || []
const onTimeCount = checkinRecords.filter(r => r.status === 'on_time').length
const lateCount = checkinRecords.filter(r => r.status === 'late').length
const absentCount = checkinRecords.filter(r => r.status === 'absent').length
const totalCheckin = onTimeCount + lateCount
const checkinRate = checkinRecords.length > 0 ? Math.round((totalCheckin / checkinRecords.length) * 100) : 0

const completeCount = training.enrolled > 0 ? Math.floor(training.enrolled * (checkinRate / 100 || 0.8)) : 0

// 判断当前学员是否在该培训班名单中
const isEnrolled = (training.students || []).includes(authStore.currentUser?.id)

const overviewStats = [
  { label: '报名人数', value: training.enrolled, color: '#003087' },
  { label: '班级容量', value: training.capacity, color: '#555' },
  { label: '预计完成学员', value: completeCount, color: '#52c41a' },
  { label: '课程总学时', value: (training.courses || []).reduce((a, c) => a + (c.hours || 0), 0) || 48, color: '#faad14' },
]

// 基于 MOCK_USER_LIST 通过 userId 映射真实学员数据
const mockStudents = (training.students || []).map(userId => {
  const u = MOCK_USER_LIST.find(user => user.id === userId) || { name: '未知学员', unit: '未知单位' }
  // 计算每个学员的考勤率（如果存在签到记录）
  const r = checkinRecords.find(cr => cr.studentId === userId)
  const cRate = !r ? 0 : (r.status === 'absent' ? 0 : (r.status === 'late' ? 80 : 100))
  return {
    key: userId,
    name: u.name,
    policeId: u.policeId || userId,
    unit: u.unit || '广西公安机关',
    progress: Math.floor(Math.random() * 20 + 80),
    checkinRate: cRate
  }
})

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

const notices = [
  { id: 1, title: '开班及教材发放通知', time: training.startDate, content: `本次培训【${training.name}】教材已到位，请于开班当天前往培训点领取。` },
  { id: 2, title: '体能测试及考核通知', time: training.endDate, content: '结业周将进行统一考核，请携带好装备。' },
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

@media (max-width: 768px) {
  .overview-stats { grid-template-columns: 1fr 1fr !important; }
  .training-banner { padding: 16px !important; }
  .training-title { font-size: 18px !important; }
}
</style>
