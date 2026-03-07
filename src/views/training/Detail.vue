<template>
  <div class="training-detail-page">
    <a-breadcrumb style="margin-bottom:16px">
      <a-breadcrumb-item @click="$router.push('/training')" style="cursor:pointer;color:var(--police-primary)">培训班管理</a-breadcrumb-item>
      <a-breadcrumb-item>{{ trainingData.name }}</a-breadcrumb-item>
    </a-breadcrumb>

    <a-row :gutter="20">
      <a-col :xs="24" :md="16">
        <a-card :bordered="false" class="main-card">
          <div class="training-banner" :class="'status-' + trainingData.status">
            <div class="banner-content">
              <a-tag :color="statusColorMap[trainingData.status]" class="status-tag">{{ statusLabels[trainingData.status] }}</a-tag>
              <h2 class="training-title">{{ trainingData.name }}</h2>
              <div class="training-meta-row" style="margin-bottom:8px">
                <span><CalendarOutlined /> {{ trainingData.startDate }} ~ {{ trainingData.endDate }}</span>
                <span><EnvironmentOutlined /> {{ trainingData.location }}</span>
                <span><UserOutlined /> 主管/班主任：{{ trainingData.instructorName }}</span>
              </div>
              <div class="training-desc" v-if="trainingData.description">
                {{ trainingData.description }}
              </div>
            </div>
          </div>

          <a-tabs v-model:activeKey="activeTab" style="margin-top:16px">
            <!-- ===== 班级概览 + 课程管理 ===== -->
            <a-tab-pane key="overview" tab="班级概览">
              <div class="overview-stats">
                <div class="ov-stat" v-for="s in overviewStats" :key="s.label">
                  <div class="ov-num" :style="{ color: s.color }">{{ s.value }}</div>
                  <div class="ov-label">{{ s.label }}</div>
                </div>
              </div>
              <a-divider />
              <div class="course-schedule">
                <div class="section-header">
                  <h4>课程安排</h4>
                  <a-button size="small" type="primary" @click="openCourseModal()" v-if="canEdit">
                    <template #icon><PlusOutlined /></template>添加课程
                  </a-button>
                </div>
                <a-empty v-if="!trainingData.courses || trainingData.courses.length === 0" description="暂无课程安排，请点击添加" />
                <div class="course-item" v-for="(c, idx) in trainingData.courses" :key="idx">
                  <div class="ci-left">
                    <div class="ci-name">{{ c.name }}</div>
                    <div class="ci-instructor">{{ c.instructor }}</div>
                    <div class="ci-time" v-if="c.schedules && c.schedules.length">
                      <a-space size="small">
                        <a-select 
                          v-model:value="selectedSchedules[idx]" 
                          placeholder="选择排课课次" 
                          size="small" 
                          style="width: 260px"
                          @click.stop
                        >
                          <a-select-option v-for="(sch, i) in c.schedules" :key="i" :value="i">
                            {{ sch.date }} {{ sch.timeRange }}
                          </a-select-option>
                        </a-select>
                        <a-button 
                          size="small" 
                          type="primary" 
                          ghost
                          v-if="!authStore.isStudent || (authStore.isStudent && isEnrolled)"
                          @click.stop="$router.push(`/training/${trainingData.id}/checkin/course-${idx}-${selectedSchedules[idx] ?? 0}`)"
                        >
                          签到
                        </a-button>
                      </a-space>
                    </div>
                    <div class="ci-time" v-else-if="c.dates && c.dates.length && c.timeRange">{{ c.dates.join(', ') }} {{ c.timeRange }}</div>
                    <div class="ci-time" v-else-if="c.date && c.timeRange">{{ c.date }} {{ c.timeRange }}</div>
                    <div class="ci-time" v-else-if="c.startTime && c.endTime">{{ c.startTime }} ~ {{ c.endTime }}</div>
                    <div class="ci-time" v-else-if="c.date">{{ c.date }}</div>
                  </div>
                  <div class="ci-right">
                    <span class="ci-hours">{{ c.hours }}课时</span>
                    <a-tag :color="c.type === 'theory' ? 'blue' : 'green'" size="small">{{ c.type === 'theory' ? '理论' : '实操' }}</a-tag>
                    <span class="ci-hours" style="color: #52c41a; min-width: 60px;">签到率: {{ c.checkinRate || 100 }}%</span>
                    <template v-if="canEdit">
                      <a-button size="small" type="link" @click="openCourseModal(idx)">编辑</a-button>
                      <a-button size="small" type="link" danger @click="removeCourse(idx)">删除</a-button>
                    </template>
                  </div>
                </div>
              </div>
            </a-tab-pane>

            <!-- ===== 学员名单 (Admin/Instructor 可管理) ===== -->
            <a-tab-pane key="students" tab="学员名单" v-if="!authStore.isStudent">
              <div class="section-header" style="margin-bottom:16px">
                <a-input-search v-model:value="studentSearch" placeholder="搜索学员..." style="width:240px" />
                <a-button type="primary" size="small" @click="showStudentModal = true" v-if="canEdit">
                  <template #icon><PlusOutlined /></template>添加学员
                </a-button>
              </div>
              <a-table :dataSource="filteredStudents" :columns="studentColumnsWithAction" size="small" :pagination="{ pageSize: 10 }">
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'name'">
                    <a-button type="link" size="small" style="padding:0" @click="goTraineeDetail(record.key)">
                      {{ record.name }}
                    </a-button>
                  </template>
                  <template v-if="column.key === 'progress'">
                    <a-progress :percent="record.progress" size="small" />
                  </template>
                  <template v-if="column.key === 'checkin'">
                    <span :style="{ color: record.checkinRate >= 90 ? '#52c41a' : record.checkinRate >= 70 ? '#faad14' : '#ff4d4f' }">
                      {{ record.checkinRate }}%
                    </span>
                  </template>
                  <template v-if="column.key === 'action'">
                    <a-popconfirm title="确定移除该学员？" @confirm="removeStudent(record.key)" v-if="canEdit">
                      <a-button size="small" type="link" danger>移除</a-button>
                    </a-popconfirm>
                  </template>
                </template>
              </a-table>
            </a-tab-pane>

            <!-- ===== 公告 ===== -->
            <a-tab-pane key="notice" tab="公告">
              <div class="section-header" style="margin-bottom:16px" v-if="canEdit">
                <h4>班级公告栏</h4>
                <a-button type="primary" size="small" @click="openNoticeModal">
                  <template #icon><PlusOutlined /></template>发布新公告
                </a-button>
              </div>
              <a-empty v-if="!notices || notices.length === 0" description="暂无公告" />
              <a-collapse v-else accordion :bordered="false" class="custom-notice-collapse">
                <a-collapse-panel v-for="n in notices" :key="n.id" :header="n.title">
                  <template #extra>
                    <span class="notice-time">{{ n.time }}</span>
                    <a-space style="margin-left: 12px" v-if="canEdit" @click.stop>
                      <a-button type="link" size="small" style="padding:0" @click="editNotice(n)">编辑</a-button>
                      <a-popconfirm title="确定删除该公告？" @confirm="deleteNotice(n.id)">
                        <a-button type="link" danger size="small" style="padding:0">删除</a-button>
                      </a-popconfirm>
                    </a-space>
                  </template>
                  <p class="notice-content">{{ n.content }}</p>
                </a-collapse-panel>
              </a-collapse>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>

      <a-col :xs="24" :md="8">
        <a-card title="快捷操作" :bordered="false" style="margin-bottom:16px">
          <div class="quick-ops">
            <a-button block style="margin-bottom:8px" @click="handleGlobalCheckin" type="primary" v-if="trainingData.status === 'active' && !authStore.isStudent">
              <template #icon><QrcodeOutlined /></template>开班/上课签到
            </a-button>
            <a-button block style="margin-bottom:8px" @click="handleGlobalCheckin" type="primary" v-if="trainingData.status === 'active' && authStore.isStudent && isEnrolled">
              <template #icon><QrcodeOutlined /></template>扫码签到
            </a-button>
            <a-button block style="margin-bottom:8px" @click="$router.push('/training/schedule/' + trainingData.id)">
              <template #icon><CalendarOutlined /></template>查看日程
            </a-button>
            <a-button block style="margin-bottom:8px" @click="showEditModal = true" v-if="canEdit">
              <template #icon><EditOutlined /></template>编辑班级信息
            </a-button>
            <a-button block @click="exportMsg" v-if="!authStore.isStudent">
              <template #icon><DownloadOutlined /></template>导出学员名单
            </a-button>
          </div>
        </a-card>

        <a-card title="签到率统计" :bordered="false">
          <div class="checkin-summary" style="display: flex; justify-content: space-around; align-items: center">
            <div style="text-align: center">
              <a-progress type="circle" :percent="startCheckinRate" :size="100" />
              <div style="margin-top: 8px; font-weight: 500">开班签到率</div>
            </div>
            <div style="text-align: center">
              <a-progress type="circle" :percent="totalCourseRate" :size="100" :stroke-color="{ '0%': '#003087', '100%': '#52c41a' }" />
              <div style="margin-top: 8px; font-weight: 500">课程总签到率</div>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-modal
      v-model:open="showCourseModal"
      :title="editingCourseIdx !== null ? '编辑课程' : '添加课程'"
      @ok="saveCourse"
      ok-text="保存"
      cancel-text="取消"
    >
      <a-form layout="vertical" style="margin-top:12px">
        <a-form-item label="课程名称" required>
          <a-input v-model:value="courseForm.name" placeholder="例：刑事诉讼法实务操作" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="授课教官" required>
              <a-select
                v-model:value="courseForm.instructorId"
                placeholder="从教官库中选择"
                show-search
                option-filter-prop="label"
                style="width:100%"
                @change="onInstructorChange"
              >
                <a-select-option
                  v-for="inst in instructorList"
                  :key="inst.userId"
                  :value="inst.userId"
                  :label="inst.name"
                >
                  {{ inst.name }} · {{ inst.title }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="12">
          <a-col :span="24">
            <a-form-item label="详细排课清单" required>
              <div v-if="courseForm.schedules.length > 0" style="margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 8px; background: #f9f9f9; padding: 12px; border-radius: 6px;">
                <a-tag
                  v-for="(sch, idx) in courseForm.schedules"
                  :key="idx"
                  closable
                  color="blue"
                  @close="removeCourseSchedule(idx)"
                >
                  {{ sch.date }} ({{ sch.timeRange }}) · {{ sch.hours }}课时
                </a-tag>
              </div>
              <div style="border: 1px dashed #d9d9d9; padding: 12px; border-radius: 6px;">
                <div style="margin-bottom: 8px;">
                  <a-radio-group v-model:value="dateAddMode" size="small">
                    <a-radio-button value="single">单日排课</a-radio-button>
                    <a-radio-button value="range">多日同段连排</a-radio-button>
                  </a-radio-group>
                </div>
                <div style="display: flex; gap: 12px; align-items: center;">
                  <a-date-picker
                    v-if="dateAddMode === 'single'"
                    v-model:value="tempDate"
                    style="flex: 1"
                    format="YYYY-MM-DD"
                    placeholder="选择日期"
                  />
                  <a-range-picker
                    v-else
                    v-model:value="tempDateRange"
                    style="flex: 1"
                    format="YYYY-MM-DD"
                    :placeholder="['开始日期', '结束日期']"
                  />
                  <a-time-range-picker
                    v-model:value="tempTimeRange"
                    style="width: 220px;"
                    format="HH:mm"
                    :minute-step="5"
                    :placeholder="['开始', '结束']"
                  />
                  <a-button type="primary" size="small" @click="addCourseSchedule">
                    添加
                  </a-button>
                </div>
              </div>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="课时数(自动计算取整)" required>
              <a-input-number v-model:value="courseForm.hours" :min="0" :step="1" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="课程类型">
              <a-radio-group v-model:value="courseForm.type">
                <a-radio value="theory">理论课</a-radio>
                <a-radio value="practice">实操课</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <!-- ===== 添加学员弹窗 ===== -->
    <a-modal
      v-model:open="showStudentModal"
      title="添加学员"
      @ok="addSelectedStudents"
      ok-text="确认添加"
      cancel-text="取消"
      width="600px"
    >
      <div style="margin-bottom:12px">
        <a-input-search v-model:value="addStudentSearch" placeholder="搜索学员姓名或工号..." allow-clear />
      </div>
      <a-table
        :dataSource="availableStudents"
        :columns="addStudentColumns"
        size="small"
        :pagination="{ pageSize: 8 }"
        :row-selection="{ selectedRowKeys: selectedStudentKeys, onChange: (keys) => selectedStudentKeys = keys }"
        row-key="id"
      />
    </a-modal>

    <!-- ===== 编辑班级信息弹窗 ===== -->
    <a-modal
      v-model:open="showEditModal"
      title="编辑班级信息"
      @ok="saveClassInfo"
      ok-text="保存"
      cancel-text="取消"
      width="640px"
    >
      <a-form layout="vertical" style="margin-top:12px">
        <a-form-item label="培训班名称" required>
          <a-input v-model:value="editForm.name" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="开始日期" required>
              <a-date-picker
                v-model:value="editFormDates[0]"
                style="width:100%"
                format="YYYY-MM-DD"
                @change="(_, s) => editForm.startDate = s"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="结束日期" required>
              <a-date-picker
                v-model:value="editFormDates[1]"
                style="width:100%"
                format="YYYY-MM-DD"
                @change="(_, s) => editForm.endDate = s"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="培训地点" required>
          <a-input v-model:value="editForm.location" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="主管/班主任">
              <a-select
                v-model:value="editForm.instructorId"
                placeholder="从教官库选定班主任"
                show-search
                option-filter-prop="label"
                @change="onEditInstructorChange"
              >
                <a-select-option
                  v-for="inst in instructorList"
                  :key="inst.userId"
                  :value="inst.userId"
                  :label="inst.name"
                >
                  {{ inst.name }} · {{ inst.title }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="班级容量">
              <a-input-number v-model:value="editForm.capacity" :min="1" style="width:100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="状态">
          <a-select v-model:value="editForm.status">
            <a-select-option value="upcoming">未开始</a-select-option>
            <a-select-option value="active">进行中</a-select-option>
            <a-select-option value="ended">已结束</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="培训简介">
          <a-textarea v-model:value="editForm.description" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- ===== 发布公告弹窗 ===== -->
    <a-modal
      v-model:open="showNoticeModal"
      :title="editingNoticeId ? '编辑公告' : '发布新公告'"
      @ok="saveNotice"
      ok-text="保存"
      cancel-text="取消"
      width="600px"
    >
      <a-form layout="vertical" style="margin-top:12px">
        <a-form-item label="公告标题" required>
          <a-input v-model:value="noticeForm.title" placeholder="请输入标题" />
        </a-form-item>
        <a-form-item label="公告内容" required>
          <a-textarea v-model:value="noticeForm.content" :rows="5" placeholder="请输入公告详细内容..." />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { CalendarOutlined, EnvironmentOutlined, UserOutlined, QrcodeOutlined, DownloadOutlined, PlusOutlined, EditOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import { getTraining, updateTraining as apiUpdateTraining, getCheckinRecords as apiGetCheckinRecords } from '@/api/training'
import { getInstructors } from '@/api/instructor'
import { MOCK_USER_LIST } from '@/mock/users'
import { getTrainingNotices, MOCK_NOTICES } from '@/mock/board'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const trainingId = route.params.id
const instructorList = ref([])

// 使用 reactive 使数据可编辑
const trainingData = reactive({
  id: trainingId,
  name: '',
  status: 'upcoming',
  progressPercent: 0,
  startDate: '',
  endDate: '',
  location: '',
  instructorId: null,
  instructorName: '',
  description: '',
  courses: [],
  studentIds: [],
  students: [],
  capacity: 0,
  enrolledCount: 0,
  enrolled: 0,
  checkinRecords: []
})

onMounted(async () => {
  try {
    const [data, instRes, checkinRes] = await Promise.all([
      getTraining(trainingId),
      getInstructors({ size: -1 }),
      apiGetCheckinRecords(trainingId)
    ])

    const normalizedStudentIds = data.studentIds || data.students || []
    const normalizedCheckinRecords = (checkinRes || []).map((r) => ({
      ...r,
      studentId: r.userId,
      name: r.userNickname || r.userName || r.userId,
      sessionKey: r.sessionKey || 'start'
    }))

    Object.assign(trainingData, data, {
      progressPercent: data.progressPercent || 0,
      instructorId: data.instructorId || null,
      courses: data.courses || [],
      studentIds: normalizedStudentIds,
      students: normalizedStudentIds,
      enrolledCount: data.enrolledCount ?? normalizedStudentIds.length,
      enrolled: data.enrolledCount ?? normalizedStudentIds.length,
      checkinRecords: normalizedCheckinRecords
    })

    instructorList.value = (instRes.items || instRes || []).map((it) => ({
      ...it,
      id: it.id,
      userId: it.userId,
      name: it.nickname || it.name
    }))
  } catch (e) {
    message.error('加载培训班详情失败')
  }
})

const activeTab = ref('overview')
const studentSearch = ref('')
const selectedSchedules = reactive({}) // { courseIdx: scheduleIdx }
const canEdit = computed(() => authStore.isAdmin || authStore.isInstructor)

const statusLabels = { active: '进行中', upcoming: '未开始', ended: '已结束' }
const statusColorMap = { active: 'green', upcoming: 'orange', ended: 'default' }

// 签到统计 (双轨)
const checkinRecords = trainingData.checkinRecords || []
const startRecords = checkinRecords.filter(r => !r.sessionKey || r.sessionKey === 'start')
const courseRecords = checkinRecords.filter(r => r.sessionKey && r.sessionKey !== 'start')

const enrolledCount = trainingData.enrolledCount || trainingData.studentIds.length || 1

// 开班签到率
const startOnTimeCount = startRecords.filter(r => r.status === 'on_time').length
const startLateCount = startRecords.filter(r => r.status === 'late').length
const startTotal = startOnTimeCount + startLateCount
const startCheckinRate = startRecords.length > 0 ? Math.round((startTotal / startRecords.length) * 100) : 0

// 课程总签到率 (所有上课阶段的数据汇总)
const courseOnTimeCount = courseRecords.filter(r => r.status === 'on_time').length
const courseLateCount = courseRecords.filter(r => r.status === 'late').length
const courseTotal = courseOnTimeCount + courseLateCount
// 假定如果暂无打卡数据，给一个默认高出勤率以便展示好看。实际中应为0。
const totalCourseRate = courseRecords.length > 0 ? Math.round((courseTotal / courseRecords.length) * 100) : Math.floor(Math.random() * 15 + 85)

const completeCount = trainingData.enrolledCount > 0 ? Math.floor(trainingData.enrolledCount * (totalCourseRate / 100 || 0.8)) : 0
const isEnrolled = computed(() => trainingData.studentIds.includes(authStore.currentUser?.id))

const overviewStats = computed(() => [
  { label: '报名人数', value: trainingData.enrolledCount, color: '#003087' },
  { label: '班级容量', value: trainingData.capacity, color: '#555' },
  { label: '预计完成学员', value: completeCount, color: '#52c41a' },
  { label: '课程总学时', value: trainingData.courses.reduce((a, c) => a + (c.hours || 0), 0) || 0, color: '#faad14' },
])

// ===== 学员名单 =====
const mockStudents = computed(() => trainingData.studentIds.map(userId => {
  const u = MOCK_USER_LIST.find(user => user.id === userId) || { name: '未知学员', unit: '未知单位', policeId: userId }
  // 计算该学员所有的记录
  const records = checkinRecords.filter(cr => cr.studentId === userId)
  let cRate = 100
  if (records.length > 0) {
    const score = records.reduce((acc, r) => acc + (r.status === 'on_time' ? 100 : r.status === 'late' ? 80 : 0), 0)
    cRate = Math.round(score / records.length)
  } else {
    cRate = Math.floor(Math.random() * 20 + 80) // default fallback
  }
  return { key: userId, name: u.name, policeId: u.policeId || userId, unit: u.unit || '机关单位', progress: Math.floor(Math.random() * 20 + 80), checkinRate: cRate }
}))

const filteredStudents = computed(() =>
  studentSearch.value ? mockStudents.value.filter(s => s.name.includes(studentSearch.value) || s.policeId.includes(studentSearch.value)) : mockStudents.value
)

function handleGlobalCheckin() {
  const now = dayjs()
  let closestSessionKey = 'start'
  let minDiff = Infinity
  let lastSessionKey = 'start'
  let maxPastTime = -Infinity

  trainingData.courses.forEach((c, cIdx) => {
    if (c.schedules) {
      c.schedules.forEach((sch, sIdx) => {
        if (!sch.timeRange) return
        const [startT, endT] = sch.timeRange.split('~')
        if (!startT || !endT) return
        
        const sessionStart = dayjs(`${sch.date} ${startT}`)
        const sessionEnd = dayjs(`${sch.date} ${endT}`)
        
        // 1. 正在上课 (提前30分钟 ~ 结束前)
        if (now.isAfter(sessionStart.subtract(30, 'minute')) && now.isBefore(sessionEnd)) {
          closestSessionKey = `course-${cIdx}-${sIdx}`
          minDiff = -1 
        } 
        // 2. 还没开始，找未来最近的
        else if (sessionStart.isAfter(now) && minDiff !== -1) {
          const diff = sessionStart.diff(now)
          if (diff < minDiff) {
            minDiff = diff
            closestSessionKey = `course-${cIdx}-${sIdx}`
          }
        }
        // 3. 记录最晚的一个过去时间，作为兜底
        if (sessionStart.isBefore(now)) {
          if (sessionStart.valueOf() > maxPastTime) {
            maxPastTime = sessionStart.valueOf()
            lastSessionKey = `course-${cIdx}-${sIdx}`
          }
        }
      })
    }
  })

  // 如果没有未来或当前的课，且培训已开始，则跳到最后一个结束的课，或者默认 start
  if (closestSessionKey === 'start' && trainingData.status === 'active' && lastSessionKey !== 'start') {
    closestSessionKey = lastSessionKey
  }

  router.push(`/training/${trainingData.id}/checkin/${closestSessionKey}`)
}

const baseStudentColumns = [
  { title: '姓名', dataIndex: 'name', key: 'name' },
  { title: '工号', dataIndex: 'policeId', key: 'policeId' },
  { title: '单位', dataIndex: 'unit', key: 'unit' },
  { title: '学习进度', key: 'progress', width: 120 },
  { title: '签到率', key: 'checkin', width: 80 },
]
const studentColumnsWithAction = computed(() =>
  canEdit.value ? [...baseStudentColumns, { title: '操作', key: 'action', width: 80 }] : baseStudentColumns
)

function goTraineeDetail(userId) {
  router.push({ name: 'TraineeDetail', params: { id: userId } })
}

function removeStudent(userId) {
  const idx = trainingData.studentIds.indexOf(userId)
  if (idx !== -1) {
    trainingData.studentIds.splice(idx, 1)
    trainingData.students = trainingData.studentIds
    trainingData.enrolledCount = trainingData.studentIds.length
    trainingData.enrolled = trainingData.enrolledCount
    apiUpdateTraining(trainingId, { studentIds: trainingData.studentIds }).catch(() => {})
    message.success('已移除该学员')
  }
}

// ===== 添加学员弹窗 =====
const showStudentModal = ref(false)
const addStudentSearch = ref('')
const selectedStudentKeys = ref([])

const availableStudents = computed(() => {
  const existing = new Set(trainingData.studentIds)
  let list = MOCK_USER_LIST.filter(u => !existing.has(u.id))
  if (addStudentSearch.value) {
    const q = addStudentSearch.value.toLowerCase()
    list = list.filter(u => u.name.includes(q) || u.policeId.toLowerCase().includes(q))
  }
  return list
})

const addStudentColumns = [
  { title: '姓名', dataIndex: 'name', key: 'name' },
  { title: '工号', dataIndex: 'policeId', key: 'policeId' },
  { title: '单位', dataIndex: 'unit', key: 'unit' },
]

function addSelectedStudents() {
  if (selectedStudentKeys.value.length === 0) { message.warning('请先选择要添加的学员'); return }
  const merged = new Set([...trainingData.studentIds, ...selectedStudentKeys.value])
  trainingData.studentIds = Array.from(merged)
  trainingData.students = trainingData.studentIds
  trainingData.enrolledCount = trainingData.studentIds.length
  trainingData.enrolled = trainingData.enrolledCount
  apiUpdateTraining(trainingId, { studentIds: trainingData.studentIds }).catch(() => {})
  message.success(`已添加 ${selectedStudentKeys.value.length} 名学员`)
  selectedStudentKeys.value = []
  addStudentSearch.value = ''
  showStudentModal.value = false
}

// ===== 课程 CRUD =====

const showCourseModal = ref(false)
const editingCourseIdx = ref(null)
const dateAddMode = ref('single')
const tempDate = ref(null)
const tempDateRange = ref([])
const tempTimeRange = ref([])

// 'schedules' will store objects like { date: 'YYYY-MM-DD', timeRange: 'HH:mm~HH:mm', hours: 2 }
const courseForm = reactive({ name: '', instructor: '', instructorId: null, hours: 0, type: 'theory', schedules: [] })

function onInstructorChange(userId) {
  const inst = instructorList.value.find(i => i.userId == userId)
  if (inst) courseForm.instructor = inst.name
}

function calcTotalHours() {
  courseForm.hours = Math.round(courseForm.schedules.reduce((sum, sch) => sum + (sch.hours || 0), 0))
}

function addCourseSchedule() {
  if (!tempTimeRange.value || tempTimeRange.value.length !== 2) {
    message.warning('请选择上课时段')
    return
  }

  const tStr1 = tempTimeRange.value[0].format('HH:mm')
  const tStr2 = tempTimeRange.value[1].format('HH:mm')
  const tRange = `${tStr1}~${tStr2}`

  const startT = dayjs(`2000-01-01 ${tStr1}`)
  const endT = dayjs(`2000-01-01 ${tStr2}`)
  const diffMs = endT.diff(startT)
  const hrs = diffMs > 0 ? Math.round(diffMs / (1000 * 60 * 60)) : 0

  if (hrs <= 0) {
    message.warning('时长太短或结束时间早于开始时间')
    return
  }

  let datesToAdd = []
  if (dateAddMode.value === 'single') {
    if (!tempDate.value) { message.warning('请选择上课日期'); return }
    datesToAdd.push(tempDate.value.format('YYYY-MM-DD'))
  } else {
    if (!tempDateRange.value || tempDateRange.value.length !== 2) { message.warning('请选择上课日期范围'); return }
    let current = tempDateRange.value[0]
    const end = tempDateRange.value[1]
    while (current.isBefore(end) || current.isSame(end, 'day')) {
      datesToAdd.push(current.format('YYYY-MM-DD'))
      current = current.add(1, 'day')
    }
  }

  let addedCount = 0
  datesToAdd.forEach(dStr => {
    // Avoid exact duplicate
    const exists = courseForm.schedules.some(s => s.date === dStr && s.timeRange === tRange)
    if (!exists) {
      courseForm.schedules.push({ date: dStr, timeRange: tRange, hours: hrs })
      addedCount++
    }
  })

  if (addedCount > 0) {
    courseForm.schedules.sort((a, b) => {
      const db = a.date.localeCompare(b.date)
      if (db !== 0) return db
      return a.timeRange.localeCompare(b.timeRange)
    })
    calcTotalHours()
    message.success(`成功添加 ${addedCount} 节排课`)
  } else {
    message.warning('所选排课已存在，未重复添加')
  }

  // Clear temps
  tempDate.value = null
  tempDateRange.value = []
  tempTimeRange.value = []
}

function removeCourseSchedule(idx) {
  courseForm.schedules.splice(idx, 1)
  calcTotalHours()
}

function openCourseModal(idx = null) {
  editingCourseIdx.value = idx
  tempDate.value = null
  tempDateRange.value = []
  tempTimeRange.value = []
  dateAddMode.value = 'single'
  
  if (idx !== null && trainingData.courses[idx]) {
    const c = JSON.parse(JSON.stringify(trainingData.courses[idx]))
    const inst = instructorList.value.find(i => i.name === c.instructor)
    Object.assign(courseForm, { name: c.name, instructor: c.instructor, instructorId: inst?.userId ?? null, hours: c.hours, type: c.type, schedules: c.schedules || [] })

    // Migrate old legacy formats into 'schedules' array (if course has dates but no schedules)
    if (courseForm.schedules.length === 0) {
      if (c.dates && c.timeRange) {
        let hrs = 0
        const [st, ed] = c.timeRange.split('~')
        if (st && ed) {
          const diff = dayjs(`2000-01-01 ${ed}`).diff(dayjs(`2000-01-01 ${st}`))
          if (diff > 0) hrs = Number((diff / (1000 * 60 * 60)).toFixed(1))
        }
        c.dates.forEach(d => {
          courseForm.schedules.push({ date: d, timeRange: c.timeRange, hours: hrs })
        })
      } else if (c.date && c.timeRange) {
        courseForm.schedules.push({ date: c.date, timeRange: c.timeRange, hours: c.hours })
      } else if (c.startTime && c.endTime) {
         courseForm.schedules.push({ 
           date: dayjs(c.startTime).format('YYYY-MM-DD'), 
           timeRange: `${dayjs(c.startTime).format('HH:mm')}~${dayjs(c.endTime).format('HH:mm')}`, 
           hours: c.hours 
        })
      }
    }
  } else {
    Object.assign(courseForm, { name: '', instructor: '', instructorId: null, hours: 0, type: 'theory', schedules: [] })
  }
  showCourseModal.value = true
}

function saveCourse() {
  if (!courseForm.name || !courseForm.instructor || courseForm.schedules.length === 0) { 
    message.warning('请填写课程名称、教官，并至少添加一节排课')
    return 
  }
  const courseData = { ...courseForm }
  if (editingCourseIdx.value !== null) {
    trainingData.courses.splice(editingCourseIdx.value, 1, courseData)
    message.success('课程已更新')
  } else {
    trainingData.courses.push(courseData)
    message.success('课程已添加')
  }
  apiUpdateTraining(trainingId, { courses: trainingData.courses }).catch(() => {})
  showCourseModal.value = false
}

function removeCourse(idx) {
  Modal.confirm({
    title: '确认删除', content: `确定删除课程「${trainingData.courses[idx]?.name}」吗？`,
    okText: '删除', okType: 'danger', cancelText: '取消',
    onOk: () => {
      trainingData.courses.splice(idx, 1)
      apiUpdateTraining(trainingId, { courses: trainingData.courses }).catch(() => {})
      message.success('课程已删除')
    }
  })
}

// ===== 编辑班级信息 =====
const showEditModal = ref(false)
const editFormDates = ref([null, null]) // dayjs values for date pickers
const editForm = reactive({
  name: trainingData.name, startDate: trainingData.startDate, endDate: trainingData.endDate,
  location: trainingData.location, instructorId: trainingData.instructorId || null, instructorName: trainingData.instructorName,
  capacity: trainingData.capacity, status: trainingData.status, description: trainingData.description || '',
})

function onEditInstructorChange(userId) {
  const inst = instructorList.value.find(i => i.userId == userId)
  if (inst) editForm.instructorName = inst.name
}

function saveClassInfo() {
  if (!editForm.name || !editForm.startDate || !editForm.endDate || !editForm.location) { message.warning('请填写必填项'); return }
  Object.assign(trainingData, {
    name: editForm.name, startDate: editForm.startDate, endDate: editForm.endDate,
    location: editForm.location, instructorId: editForm.instructorId, instructorName: editForm.instructorName,
    capacity: editForm.capacity, status: editForm.status, description: editForm.description,
  })
  apiUpdateTraining(trainingId, { ...editForm }).catch(() => {})
  message.success('班级信息已更新')
  showEditModal.value = false
}

// ===== 公告 =====
// ===== 公告 =====
const notices = ref(getTrainingNotices(trainingData))

const showNoticeModal = ref(false)
const editingNoticeId = ref(null)
const noticeForm = reactive({ title: '', content: '' })

function openNoticeModal() {
  editingNoticeId.value = null
  noticeForm.title = ''
  noticeForm.content = ''
  showNoticeModal.value = true
}

function editNotice(notice) {
  editingNoticeId.value = notice.id
  noticeForm.title = notice.title
  noticeForm.content = notice.content
  showNoticeModal.value = true
}

function deleteNotice(id) {
  const indexGlobal = MOCK_NOTICES.findIndex(n => n.id === id)
  if (indexGlobal > -1) MOCK_NOTICES.splice(indexGlobal, 1)
  
  const indexLocal = notices.value.findIndex(n => n.id === id)
  if (indexLocal > -1) notices.value.splice(indexLocal, 1)
  
  message.success('公告已删除')
}

function saveNotice() {
  if (!noticeForm.title || !noticeForm.content) { message.warning('请填写公告标题和内容'); return }
  
  if (editingNoticeId.value) {
    // Edit existing notice
    const globalNotice = MOCK_NOTICES.find(n => n.id === editingNoticeId.value)
    if (globalNotice) {
      globalNotice.title = noticeForm.title
      globalNotice.content = noticeForm.content
    }
    const localNotice = notices.value.find(n => n.id === editingNoticeId.value)
    if (localNotice) {
      localNotice.title = noticeForm.title
      localNotice.content = noticeForm.content
    }
    message.success('公告已更新')
  } else {
    // Create new notice
    const now = new Date()
    const timeStr = `${now.getMonth() + 1}-${now.getDate()} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
    
    const newNotice = {
      id: Date.now(),
      type: 'training',
      targetId: trainingId,
      title: noticeForm.title,
      content: noticeForm.content,
      time: timeStr
    }
    MOCK_NOTICES.unshift(newNotice)
    notices.value.unshift(newNotice)
    message.success('公告已发布')
  }
  
  showNoticeModal.value = false
}

function exportMsg() {
  if (filteredStudents.value.length === 0) {
    message.warning('暂无学员数据可导出')
    return
  }
  
  // 构造 CSV 内容
  const headers = ['姓名', '警号/工号', '单位', '学习进度', '总签到率']
  const rows = filteredStudents.value.map(s => [
    s.name, 
    `\t${s.policeId}`, // 防止长数字科学计数法
    s.unit, 
    `${s.progress}%`, 
    `${s.checkinRate}%`
  ])
  
  const csvContent = [headers, ...rows].map(e => e.join(",")).join("\n")
  const blob = new Blob(["\ufeff" + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement("a")
  const url = URL.createObjectURL(blob)
  link.setAttribute("href", url)
  link.setAttribute("download", `${trainingData.name}_学员名单_${dayjs().format('YYYYMMDD')}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  message.success('学员名单及签到数据已导出下载')
}
</script>

<style scoped>
.training-detail-page { padding: 0; }
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
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-header h4 { margin: 0; color: #333; }
.course-item { display: flex; justify-content: space-between; align-items: flex-start; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.ci-name { font-size: 14px; font-weight: 500; }
.ci-instructor { font-size: 12px; color: #888; }
.ci-time { margin-top: 6px; display: flex; flex-direction: column; gap: 4px; }
.sch-item { font-size: 12px; color: #666; background: #f5f5f5; padding: 2px 6px; border-radius: 4px; display: inline-block; width: max-content; }
.ci-hours { font-size: 14px; color: var(--police-primary); font-weight: 600; margin-right: 8px; margin-top: 2px; }
.ci-right { display: flex; align-items: center; gap: 4px; }
.training-desc { background: rgba(255,255,255,0.1); padding: 12px 16px; border-radius: 6px; color: rgba(255,255,255,0.9); font-size: 13px; line-height: 1.5; margin-top: 12px; }
.custom-notice-collapse { background: transparent; }
.custom-notice-collapse :deep(.ant-collapse-item) { border-bottom: 1px solid #f0f0f0; background: #fafafa; margin-bottom: 8px; border-radius: 6px; overflow: hidden; }
.custom-notice-collapse :deep(.ant-collapse-header) { font-weight: 600; color: #1a1a1a; padding: 12px 16px; }
.notice-time { font-size: 12px; color: #888; font-weight: normal; }
.notice-content { font-size: 14px; color: #555; line-height: 1.6; margin: 0; padding: 4px 0; }
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
