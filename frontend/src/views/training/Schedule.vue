<template>
  <div class="schedule-page">
    <!-- 页头：选择班级 + 周导航 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">周训练计划</h2>
        <a-select
          v-model:value="selectedTrainingId"
          style="min-width: 280px; max-width: 420px;"
          placeholder="请选择培训班"
          :options="trainingOptions"
          @change="onTrainingChange"
        />
        <div class="training-meta" v-if="selectedTraining">
          <a-tag :color="statusColors[selectedTraining.status]">{{ statusLabels[selectedTraining.status] }}</a-tag>
          <span>主讲：{{ selectedTraining.instructorName }}</span>
          <span>地点：{{ selectedTraining.location }}</span>
          <span>{{ selectedTraining.startDate }} ~ {{ selectedTraining.endDate }}</span>
        </div>
      </div>
      <div class="week-nav">
        <a-button v-if="canImportInstructors" @click="showInstructorImportModal = true">
          导入教官
        </a-button>
        <a-button v-if="canImportSchedule" @click="showScheduleImportModal = true">
          导入课次
        </a-button>
        <a-button v-if="selectedTrainingId && canImportSchedule" type="primary" ghost @click="openAiSchedule">
          智能排课
        </a-button>
        <a-button @click="prevWeek" :disabled="currentWeek <= 0">‹</a-button>
        <span class="week-label">第 {{ currentWeek + 1 }} 周（{{ weekRange }}）</span>
        <a-button @click="nextWeek">›</a-button>
      </div>
    </div>

    <!-- 空状态 -->
    <a-empty v-if="!selectedTraining" description="您暂无可查看的培训班课程计划" style="margin-top:60px" />

    <template v-else-if="initialized">
      <!-- 日历视图 -->
      <a-card :bordered="false" class="schedule-card">
        <div class="schedule-grid">
          <!-- 表头 -->
          <div class="grid-header">
            <div class="time-col"></div>
            <div class="day-col" v-for="day in weekDays" :key="day.date" :class="{ today: day.isToday }">
              <div class="day-name">{{ day.name }}</div>
              <div class="day-date">{{ day.date }}</div>
            </div>
          </div>

          <!-- 时间行 -->
          <div class="grid-body">
            <div class="time-slots">
              <div class="time-slot" v-for="t in timeSlots" :key="t">{{ t }}</div>
            </div>

            <div class="day-col-body" v-for="day in weekDays" :key="day.date"
                 @dragover.prevent
                 @drop="canEdit ? onDrop($event, day) : null"
            >
              <div v-for="item in getScheduleForDay(day.weekday)" :key="item.id"
                class="schedule-item" :class="['type-' + item.type, { 'is-draggable': isItemEditable(item), 'is-locked': !isItemEditable(item) }]"
                :style="{ top: getTopOffset(item.timeStart) + 'px', height: getHeight(item.duration) + 'px' }"
                :draggable="isItemEditable(item)"
                @dragstart="isItemEditable(item) ? onDragStart($event, item) : null"
                @click.stop="isItemEditable(item) ? openEditItem(item) : null"
              >
                <div class="si-title">{{ item.title }}</div>
                <div class="si-meta">{{ item.timeStart }} · {{ item.location }}</div>
                <div class="si-instructor" v-if="item.instructor">{{ item.instructor }}</div>
              </div>
            </div>
          </div>
        </div>
      </a-card>

      <!-- 本周汇总 -->
      <a-row :gutter="16" style="margin-top:16px">
        <a-col :xs="24" :sm="16">
          <a-card title="本周课程安排" :bordered="false">
            <a-list :dataSource="currentScheduleItems" size="small">
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta>
                    <template #avatar>
                      <div class="type-dot" :class="'type-' + item.type">{{ typeIcons[item.type] }}</div>
                    </template>
                    <template #title>{{ item.title }}</template>
                    <template #description>{{ item.dayName }} {{ item.timeStart }} · {{ item.location }}</template>
                  </a-list-item-meta>
                  <template #extra>
                    <a-tag :color="typeColors[item.type]" size="small">{{ typeLabels[item.type] }}</a-tag>
                  </template>
                </a-list-item>
              </template>
              <template #empty>
                <a-empty description="本班暂无详细课程日程，正在排课中" />
              </template>
            </a-list>
          </a-card>
        </a-col>
        <a-col :xs="24" :sm="8">
          <a-card title="本周统计" :bordered="false">
            <div class="week-stats">
              <div class="ws-item" v-for="s in weekStats" :key="s.label">
                <div class="ws-icon" :style="{ color: s.color }">{{ s.icon }}</div>
                <div class="ws-info">
                  <div class="ws-val">{{ s.value }}</div>
                  <div class="ws-label">{{ s.label }}</div>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </template>

    <!-- 编辑课程项弹窗 -->
    <a-modal
      v-model:open="editItemVisible"
      title="编辑课程安排"
      ok-text="保存"
      cancel-text="取消"
      :confirm-loading="editItemSaving"
      @ok="saveEditItem"
      :width="480"
    >
      <a-form :label-col="{ span: 6 }" style="margin-top:16px">
        <a-form-item label="课程名称">
          <a-input v-model:value="editItemForm.title" placeholder="课程名称" />
        </a-form-item>
        <a-form-item label="开始时间">
          <a-time-picker
            v-model:value="editItemForm.timeStartObj"
            format="HH:mm"
            :minute-step="5"
            style="width:100%"
            placeholder="选择开始时间"
          />
        </a-form-item>
        <a-form-item label="结束时间">
          <a-time-picker
            v-model:value="editItemForm.timeEndObj"
            format="HH:mm"
            :minute-step="5"
            style="width:100%"
            placeholder="选择结束时间"
          />
        </a-form-item>
        <a-form-item label="课时（自动）">
          <a-input-number
            :value="editItemComputedHours"
            :disabled="true"
            addon-after="小时"
            style="width:100%"
          />
        </a-form-item>
        <a-form-item label="上课地点">
          <a-input v-model:value="editItemForm.location" placeholder="上课地点" />
        </a-form-item>
        <a-form-item label="课程类型">
          <a-select v-model:value="editItemForm.type" style="width:100%">
            <a-select-option value="theory">📖 理论课</a-select-option>
            <a-select-option value="skill">🔧 技能课</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <ExcelImportModal
      v-model:open="showInstructorImportModal"
      title="教官导入"
      :confirm-loading="importingInstructor"
      :can-submit="canImportInstructors"
      :can-download-template="canImportInstructors"
      submit-tooltip="无权导入教官"
      download-template-tooltip="无权下载教官导入模板"
      @submit="submitInstructorImport"
      @download-template="handleDownloadInstructorTemplate"
    />

    <ExcelImportModal
      v-model:open="showScheduleImportModal"
      title="课次导入"
      :confirm-loading="importingSchedule"
      :can-submit="canImportSchedule"
      :can-download-template="canImportSchedule"
      submit-tooltip="无权导入课次"
      download-template-tooltip="无权下载课次导入模板"
      @submit="submitScheduleImport"
      @download-template="handleDownloadScheduleTemplate"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MOCK_WEEK_SCHEDULE } from '@/mock/schedules'
import {
  getTrainings,
  getTraining,
  manageTraining,
  updateTraining,
  downloadTrainingInstructorImportTemplate,
  downloadTrainingSessionImportTemplate,
  importTrainingInstructors,
  importTrainingSessions,
} from '@/api/training'
import { useAuthStore } from '@/stores/auth'
import { downloadBlob } from '@/utils/download'
import ExcelImportModal from '@/views/system/components/ExcelImportModal.vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const importingInstructor = ref(false)
const importingSchedule = ref(false)
const showInstructorImportModal = ref(false)
const showScheduleImportModal = ref(false)

const allTrainings = ref([])

async function loadTrainings() {
  try {
    const res = await getTrainings({ size: -1 })
    allTrainings.value = res.items || res || []
  } catch {
    allTrainings.value = []
  }
}

// 根据角色过滤可见的培训班
const availableTrainings = computed(() => {
  if (authStore.isAdmin) {
    return allTrainings.value
  } else if (authStore.isInstructor) {
    const myName = authStore.currentUser?.name || authStore.currentUser?.username
    return allTrainings.value.filter(t => t.instructorName === myName || t.instructorId === authStore.currentUser?.username)
  } else {
    const me = authStore.currentUser?.id
    return allTrainings.value.filter(t =>
      (t.studentIds || t.students || []).includes(me)
    )
  }
})

const trainingOptions = computed(() =>
  availableTrainings.value.map(t => ({
    value: t.id,
    label: `[${statusLabels[t.status]}] ${t.name}`,
  }))
)

// 初始选中：优先路由参数 > 第一个进行中 > 列表第一个
const selectedTrainingId = ref(null)

// 存储详情数据（含 courses）
const trainingDetailMap = ref({})

const selectedTrainingDetail = computed(() => {
  if (!selectedTrainingId.value) {
    return null
  }
  return trainingDetailMap.value[selectedTrainingId.value] || null
})

const canEdit = computed(() => Boolean(selectedTrainingDetail.value?.canEditCourses))
const canImportInstructors = computed(() => Boolean(selectedTrainingDetail.value?.canManageTraining))
const canImportSchedule = computed(() => Boolean(selectedTrainingDetail.value?.canEditCourses))

const selectedTraining = computed(() => {
  const base = availableTrainings.value.find(t => t.id === selectedTrainingId.value) || null
  if (!base) return null
  const detail = trainingDetailMap.value[base.id]
  if (detail) {
    return { ...base, courses: detail.courses || base.courses || [] }
  }
  return base
})

const currentWeek = ref(0)

function calcCurrentWeekIndex(startDateStr) {
  if (!startDateStr) return 0
  const start = new Date(startDateStr.replace(/-/g, '/'))
  const today = new Date()
  // 将 start 对齐到所在周的周一
  const startDay = start.getDay()
  const startMonday = new Date(start)
  startMonday.setDate(start.getDate() - ((startDay === 0 ? 7 : startDay) - 1))
  startMonday.setHours(0, 0, 0, 0)
  // 将 today 对齐到所在周的周一
  const todayDay = today.getDay()
  const todayMonday = new Date(today)
  todayMonday.setDate(today.getDate() - ((todayDay === 0 ? 7 : todayDay) - 1))
  todayMonday.setHours(0, 0, 0, 0)
  const diffDays = Math.floor((todayMonday - startMonday) / (1000 * 60 * 60 * 24))
  const weekIndex = Math.floor(diffDays / 7)
  return Math.max(0, weekIndex)
}

async function loadTrainingDetail(id) {
  if (!id) return
  try {
    const detail = await getTraining(id)
    trainingDetailMap.value[id] = detail
  } catch { /* ignore */ }
}

async function onTrainingChange() {
  await loadTrainingDetail(selectedTrainingId.value)
  const training = availableTrainings.value.find(t => t.id === selectedTrainingId.value)
  currentWeek.value = calcCurrentWeekIndex(training?.startDate)
}

function openAiSchedule() {
  if (!selectedTrainingId.value) {
    return
  }
  router.push({ name: 'AiScheduleTask', params: { id: selectedTrainingId.value } })
}

async function refreshCurrentTraining() {
  await loadTrainings()
  if (selectedTrainingId.value) {
    await loadTrainingDetail(selectedTrainingId.value)
  }
}

async function submitTrainingUpdate(payload) {
  if (!selectedTrainingId.value) {
    throw new Error('未选择培训班')
  }

  if (selectedTrainingDetail.value?.canManageTraining) {
    return manageTraining(selectedTrainingId.value, payload)
  }

  return updateTraining(selectedTrainingId.value, payload)
}

async function handleDownloadInstructorTemplate() {
  if (!selectedTrainingId.value || !canImportInstructors.value) {
    return
  }
  try {
    const blob = await downloadTrainingInstructorImportTemplate(selectedTrainingId.value)
    downloadBlob(blob, '培训班教官导入模板.xlsx')
  } catch (error) {
    message.error(error?.message || '下载模板失败')
  }
}

async function submitInstructorImport(file) {
  if (!selectedTrainingId.value || !canImportInstructors.value) {
    message.warning('无权导入教官')
    return
  }
  importingInstructor.value = true
  try {
    const result = await importTrainingInstructors(selectedTrainingId.value, file)
    await refreshCurrentTraining()
    showInstructorImportModal.value = false
    message.success(`教官导入完成：成功 ${result.successRows || 0} 行，新增账号 ${result.createdCount || 0} 个`)
  } catch (error) {
    message.error(error?.message || '教官导入失败')
  } finally {
    importingInstructor.value = false
  }
}

async function handleDownloadScheduleTemplate() {
  if (!selectedTrainingId.value || !canImportSchedule.value) {
    return
  }
  try {
    const blob = await downloadTrainingSessionImportTemplate(selectedTrainingId.value)
    downloadBlob(blob, '培训班课次导入模板.xlsx')
  } catch (error) {
    message.error(error?.message || '下载模板失败')
  }
}

async function submitScheduleImport(file) {
  if (!selectedTrainingId.value || !canImportSchedule.value) {
    message.warning('无权导入课次')
    return
  }
  importingSchedule.value = true
  try {
    const result = await importTrainingSessions(selectedTrainingId.value, file)
    await refreshCurrentTraining()
    showScheduleImportModal.value = false
    message.success(`课次导入完成：新增课次 ${result.addedSessionCount || 0} 个，跳过 ${result.skippedCount || 0} 行`)
    if (result?.courseMatchFailureSummary) {
      message.warning(result.courseMatchFailureSummary, 6)
    }
  } catch (error) {
    message.error(error?.message || '课次导入失败')
  } finally {
    importingSchedule.value = false
  }
}

const initialized = ref(false)

onMounted(async () => {
  await loadTrainings()

  // 设置初始选中
  const initId = route.params.id
    ? parseInt(route.params.id)
    : (availableTrainings.value.find(t => t.status === 'active')?.id || availableTrainings.value[0]?.id)
  selectedTrainingId.value = initId || null

  // 加载详情（含 courses）并定位到当前周
  if (selectedTrainingId.value) {
    await loadTrainingDetail(selectedTrainingId.value)
    const training = availableTrainings.value.find(t => t.id === selectedTrainingId.value)
    currentWeek.value = calcCurrentWeekIndex(training?.startDate)
  }

  initialized.value = true
})

// 追踪调度更新
const triggerUpdate = ref(0)
const draggedItem = ref(null)
const draggedPointerOffsetY = ref(0)

// 动态计算周日期：固定周一至周日 7 天
const weekDays = computed(() => {
  const startDateStr = selectedTraining.value?.startDate || new Date().toISOString().split('T')[0]
  const base = new Date(startDateStr.replace(/-/g, '/'))
  base.setDate(base.getDate() + currentWeek.value * 7)

  // 找到本周的周一
  const dayOfWeek = base.getDay() // 0=周日, 1=周一 ...
  const monday = new Date(base)
  monday.setDate(base.getDate() - ((dayOfWeek === 0 ? 7 : dayOfWeek) - 1))

  const daysOfWeek = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  const today = new Date()

  const arr = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)

    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const dt = String(d.getDate()).padStart(2, '0')

    arr.push({
      name: daysOfWeek[i],
      date: `${m}/${dt}`,
      fullDate: `${y}-${m}-${dt}`,
      weekday: i + 1,
      isToday: d.getFullYear() === today.getFullYear() && d.getMonth() === today.getMonth() && d.getDate() === today.getDate()
    })
  }
  return arr
})

const weekRange = computed(() => {
  if (!weekDays.value.length) return ''
  return `${weekDays.value[0].date} - ${weekDays.value[6].date}`
})

const prevWeek = () => { if (currentWeek.value > 0) currentWeek.value-- }
const nextWeek = () => currentWeek.value++

const SCHEDULE_START_HOUR = 8
const MINUTES_PER_HOUR = 60
const PIXELS_PER_MINUTE = 1.2
const SCHEDULE_SNAP_MINUTES = 30
const DEFAULT_DURATION_MINUTES = 180
const timeSlots = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']
const SCHEDULE_TOTAL_MINUTES = timeSlots.length * MINUTES_PER_HOUR

function normalizeText(value) {
  return typeof value === 'string' ? value.trim() : ''
}

function parseClockTime(value) {
  const [hourText = '', minuteText = ''] = String(value || '').split(':')
  const hour = Number(hourText)
  const minute = Number(minuteText)
  if (!Number.isFinite(hour) || !Number.isFinite(minute)) {
    return null
  }
  return { hour, minute }
}

function parseTimeRange(timeRange) {
  const [startText = '', endText = ''] = String(timeRange || '').split('~').map(item => item.trim())
  return { startText, endText }
}

function timeTextToOffsetMinutes(timeText) {
  const parsed = parseClockTime(timeText)
  if (!parsed) {
    return 0
  }
  return ((parsed.hour - SCHEDULE_START_HOUR) * MINUTES_PER_HOUR) + parsed.minute
}

function formatOffsetMinutes(offsetMinutes) {
  const totalMinutes = (SCHEDULE_START_HOUR * MINUTES_PER_HOUR) + Math.max(0, Math.round(offsetMinutes))
  const hour = Math.floor(totalMinutes / MINUTES_PER_HOUR)
  const minute = totalMinutes % MINUTES_PER_HOUR
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
}

function getScheduleDurationMinutes(schedule) {
  const { startText, endText } = parseTimeRange(schedule?.timeRange)
  const startOffset = timeTextToOffsetMinutes(startText)
  const endOffset = timeTextToOffsetMinutes(endText)
  if (startText && endText && endOffset > startOffset) {
    return endOffset - startOffset
  }

  const hours = Number(schedule?.hours || 0)
  if (Number.isFinite(hours) && hours > 0) {
    return Math.round(hours * MINUTES_PER_HOUR)
  }

  return DEFAULT_DURATION_MINUTES
}

function mapCourseTypeToItemType(courseType) {
  return courseType === 'practice' || courseType === 'skill' ? 'skill' : 'theory'
}

function mapItemTypeToCourseType(itemType) {
  return itemType === 'skill' ? 'practice' : 'theory'
}

function getScheduleLocation(schedule, course) {
  return normalizeText(schedule?.location) || normalizeText(course?.location) || normalizeText(selectedTraining.value?.location)
}

function isItemEditable(item) {
  return canEdit.value && Boolean(item?.canEdit)
}

function clampScheduleOffsetMinutes(offsetMinutes, durationMinutes = 0) {
  const maxStartMinutes = Math.max(0, SCHEDULE_TOTAL_MINUTES - Math.max(durationMinutes, 0))
  return Math.max(0, Math.min(Math.round(offsetMinutes), maxStartMinutes))
}

function snapScheduleOffsetMinutes(offsetMinutes) {
  return Math.round(offsetMinutes / SCHEDULE_SNAP_MINUTES) * SCHEDULE_SNAP_MINUTES
}

function syncItemFromSchedule(item, course, scheduleRef) {
  if (!item || !course || !scheduleRef) {
    return
  }

  const { startText } = parseTimeRange(scheduleRef.timeRange)
  const dayMatch = weekDays.value.find(day => day.fullDate === scheduleRef.date)

  item.fullDate = scheduleRef.date
  item.day = dayMatch?.weekday ?? item.day
  item.dayName = dayMatch?.name ?? item.dayName
  item.timeStart = startText || item.timeStart
  item.duration = getScheduleDurationMinutes(scheduleRef)
  item.sourceTimeRange = scheduleRef.timeRange || ''
  item.location = getScheduleLocation(scheduleRef, course)
  item.title = course.name
  item.type = mapCourseTypeToItemType(course.type)
  item.instructor = course.instructor
}

function applyScheduleMutation(item, changes = {}) {
  const scheduleState = findScheduleReference(item)
  if (!scheduleState) {
    return null
  }

  const { course, scheduleRef } = scheduleState

  if (Object.prototype.hasOwnProperty.call(changes, 'date')) {
    scheduleRef.date = changes.date
  }
  if (Object.prototype.hasOwnProperty.call(changes, 'timeRange')) {
    scheduleRef.timeRange = changes.timeRange
  }
  if (Object.prototype.hasOwnProperty.call(changes, 'hours')) {
    scheduleRef.hours = changes.hours
  }
  if (Object.prototype.hasOwnProperty.call(changes, 'location')) {
    scheduleRef.location = changes.location || course.location || null
  }
  if (Object.prototype.hasOwnProperty.call(changes, 'title')) {
    course.name = changes.title
  }
  if (Object.prototype.hasOwnProperty.call(changes, 'type')) {
    course.type = changes.type
  }

  syncItemFromSchedule(item, course, scheduleRef)
  return scheduleState
}

function updateTrainingDetailCache(detail) {
  if (!selectedTrainingId.value || !detail) {
    return
  }
  trainingDetailMap.value = {
    ...trainingDetailMap.value,
    [selectedTrainingId.value]: detail,
  }
}

// 从课程 schedules 中精准解析日程数据
const currentScheduleItems = computed(() => {
  triggerUpdate.value // 依赖项，用于强制刷新
  if (!selectedTraining.value) return []
  
  const courses = selectedTraining.value.courses || []
  if (courses.length > 0) {
    const items = []
    
    courses.forEach((c, cIdx) => {
      if (c.schedules) {
        c.schedules.forEach((sch, sIdx) => {
          const schDateStr = sch.date
          const dayMatch = weekDays.value.find(d => d.fullDate === schDateStr)
          
          if (dayMatch) {
            const { startText } = parseTimeRange(sch.timeRange)
            const duration = getScheduleDurationMinutes(sch)
            
            items.push({
              id: `${selectedTraining.value.id}-c${cIdx}-s${sIdx}`,
              courseId: c.id,
              courseIdx: cIdx,
              scheduleIdx: sIdx,
              day: dayMatch.weekday,
              dayName: dayMatch.name,
              fullDate: schDateStr,
              sourceTimeRange: sch.timeRange || '',
              title: c.name,
              type: mapCourseTypeToItemType(c.type),
              timeStart: startText || '09:00',
              duration,
              location: getScheduleLocation(sch, c),
              instructor: c.instructor,
              status: sch.status || 'pending',
              isExpired: Boolean(sch.isExpired),
              canEdit: sch.canEdit !== false,
              canDelete: sch.canDelete !== false,
            })
          }
        })
      }
    })
    return items
  }
  return MOCK_WEEK_SCHEDULE.items || []
})

const getScheduleForDay = (weekday) => currentScheduleItems.value.filter(s => s.day === weekday)

// 拖拽调整逻辑
function onDragStart(e, item) {
  if (!isItemEditable(item)) {
    draggedItem.value = null
    draggedPointerOffsetY.value = 0
    return
  }
  draggedItem.value = item
  const rect = e.currentTarget?.getBoundingClientRect?.()
  draggedPointerOffsetY.value = rect ? Math.max(0, e.clientY - rect.top) : 0
  e.dataTransfer.effectAllowed = 'move'
}

function findScheduleReference(item) {
  const training = selectedTraining.value
  const courses = training?.courses
  if (!training || !Array.isArray(courses) || !item) {
    return null
  }

  const course =
    courses.find(c => c?.id === item.courseId) ??
    courses[item.courseIdx]

  if (!course || !Array.isArray(course.schedules)) {
    return null
  }

  let scheduleIdx = Number.isInteger(item.scheduleIdx) ? item.scheduleIdx : -1
  let scheduleRef = course.schedules[scheduleIdx]

  const matchesOriginal =
    scheduleRef &&
    scheduleRef.date === item.fullDate &&
    (scheduleRef.timeRange || '') === (item.sourceTimeRange || '')

  if (!matchesOriginal) {
    scheduleIdx = course.schedules.findIndex(s =>
      s &&
      s.date === item.fullDate &&
      (s.timeRange || '') === (item.sourceTimeRange || '')
    )
    scheduleRef = scheduleIdx >= 0 ? course.schedules[scheduleIdx] : null
  }

  if (!scheduleRef) {
    return null
  }

  return { course, scheduleRef, scheduleIdx }
}

async function onDrop(e, targetDay) {
  if (!draggedItem.value) return
  const item = draggedItem.value
  if (!isItemEditable(item)) {
    draggedItem.value = null
    draggedPointerOffsetY.value = 0
    return
  }
  
  const rect = e.currentTarget.getBoundingClientRect()
  const rawTopPixels = e.clientY - rect.top - draggedPointerOffsetY.value
  const durationMinutes = item.duration || DEFAULT_DURATION_MINUTES
  let nextStartMinutes = rawTopPixels / PIXELS_PER_MINUTE
  nextStartMinutes = snapScheduleOffsetMinutes(nextStartMinutes)
  nextStartMinutes = clampScheduleOffsetMinutes(nextStartMinutes, durationMinutes)

  const newStartString = formatOffsetMinutes(nextStartMinutes)
  const newEndString = formatOffsetMinutes(nextStartMinutes + durationMinutes)
  const nextTimeRange = `${newStartString}~${newEndString}`

  try {
    const scheduleState = applyScheduleMutation(item, {
      date: targetDay.fullDate,
      timeRange: nextTimeRange,
      hours: Number((durationMinutes / MINUTES_PER_HOUR).toFixed(1)),
    })
    if (!scheduleState) {
      message.warning('当前课表数据已更新，请刷新后重试')
      await refreshCurrentTraining()
      return
    }

    triggerUpdate.value++

    const detail = await submitTrainingUpdate({ courses: selectedTraining.value.courses })
    updateTrainingDetailCache(detail)
    message.success('课程时段已保存')
  } catch {
    await refreshCurrentTraining()
    message.error('保存失败，请重试')
  } finally {
    draggedItem.value = null
    draggedPointerOffsetY.value = 0
  }
}

const getTopOffset = (time) => {
  return Math.max(0, timeTextToOffsetMinutes(time) * PIXELS_PER_MINUTE)
}

const getHeight = (duration) => (duration || 90) * PIXELS_PER_MINUTE

const statusLabels = { active: '进行中', upcoming: '未开始', ended: '已结束' }
const statusColors = { active: 'green', upcoming: 'orange', ended: 'default' }
const dayNames = { 1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六', 7: '周日' }
const typeColors = { theory: 'blue', skill: 'green', review: 'purple', physical: 'orange', drill: 'red' }
const typeLabels = { theory: '理论课', skill: '技能课', review: '复习', physical: '体能', drill: '演练' }
const typeIcons = { theory: '📖', skill: '🔧', review: '📝', physical: '💪', drill: '⚠️' }

const weekStats = computed(() => {
  const items = currentScheduleItems.value
  return [
    { icon: '📚', label: '课程总数', value: items.length + '节', color: '#003087' },
    { icon: '⏱', label: '总课时', value: Math.round(items.reduce((a, b) => a + (b.duration || 90), 0) / 60) + '小时', color: '#52c41a' },
    { icon: '🔧', label: '实操课时', value: items.filter(s => s.type === 'skill').length + '节', color: '#faad14' },
    { icon: '📖', label: '理论课时', value: items.filter(s => s.type === 'theory').length + '节', color: '#722ed1' },
  ]
})

// ─── 编辑课程项弹窗 ───
const editItemVisible = ref(false)
const editItemSaving = ref(false)
const editItemTarget = ref(null) // 正在编辑的 item 对象
const editItemForm = ref({
  title: '',
  timeStartObj: null,
  timeEndObj: null,
  location: '',
  type: 'theory',
})

// 根据起止时间自动计算课时（小时，保留1位小数）
const editItemComputedHours = computed(() => {
  const s = editItemForm.value.timeStartObj
  const e = editItemForm.value.timeEndObj
  if (!s || !e) return 0
  const diffMins = e.diff(s, 'minute')
  return diffMins > 0 ? Number((diffMins / 60).toFixed(1)) : 0
})

function openEditItem(item) {
  if (!isItemEditable(item)) {
    return
  }
  editItemTarget.value = item
  const endStr = formatOffsetMinutes(timeTextToOffsetMinutes(item.timeStart || '09:00') + (item.duration || 90))

  editItemForm.value = {
    title: item.title,
    timeStartObj: dayjs(`2000-01-01 ${item.timeStart}`),
    timeEndObj: dayjs(`2000-01-01 ${endStr}`),
    location: item.location || '',
    type: item.type === 'skill' ? 'skill' : 'theory',
  }
  editItemVisible.value = true
}

async function saveEditItem() {
  const item = editItemTarget.value
  if (!item) return

  const form = editItemForm.value
  const normalizedTitle = normalizeText(form.title)
  if (!form.timeStartObj || !form.timeEndObj) {
    message.warning('请选择上课起止时间')
    return
  }
  if (!normalizedTitle) {
    message.warning('请输入课程名称')
    return
  }
  const newStart = form.timeStartObj.format('HH:mm')
  const newEnd = form.timeEndObj.format('HH:mm')
  if (form.timeEndObj.isBefore(form.timeStartObj)) {
    message.warning('结束时间不能早于开始时间')
    return
  }
  const hours = editItemComputedHours.value
  if (hours <= 0) {
    message.warning('课时必须大于 0')
    return
  }

  editItemSaving.value = true
  try {
    const scheduleState = applyScheduleMutation(item, {
      timeRange: `${newStart}~${newEnd}`,
      hours,
      location: normalizeText(form.location),
      title: normalizedTitle,
      type: mapItemTypeToCourseType(form.type),
    })
    if (!scheduleState) {
      message.warning('当前课表数据已更新，请刷新后重试')
      await refreshCurrentTraining()
      return
    }

    triggerUpdate.value++

    const detail = await submitTrainingUpdate({ courses: selectedTraining.value.courses })
    updateTrainingDetailCache(detail)
    message.success('课程安排已保存')
    editItemVisible.value = false
  } catch {
    await refreshCurrentTraining()
    message.error('保存失败，请重试')
  } finally {
    editItemSaving.value = false
  }
}
</script>

<style scoped>
.schedule-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.header-left { display: flex; flex-direction: column; gap: 8px; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.training-meta { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #555; flex-wrap: wrap; }
.week-nav { display: flex; align-items: center; gap: 12px; }
.week-label { font-size: 14px; font-weight: 500; color: #333; min-width: 180px; text-align: center; }
.schedule-card { overflow-x: auto; }
.schedule-grid { min-width: 700px; }
.grid-header { display: flex; border-bottom: 2px solid #003087; }
.time-col { width: 64px; flex-shrink: 0; }
.day-col { flex: 1; text-align: center; padding: 10px 4px; }
.day-col.today { background: #e8f0fe; border-radius: 6px 6px 0 0; }
.day-name { font-size: 12px; color: #888; }
.day-date { font-size: 16px; font-weight: 700; color: #333; }
.day-col.today .day-date { color: var(--police-primary); }
.grid-body { display: flex; position: relative; min-height: 800px; padding-bottom: 20px; }
.time-slots { width: 64px; flex-shrink: 0; padding-top: 4px; }
.time-slot { height: 72px; font-size: 11px; color: #aaa; padding-top: 2px; }
.day-col-body { flex: 1; border-left: 1px dashed #e8e8e8; position: relative; padding: 4px; transition: background 0.2s; }
.day-col-body:last-child { border-right: 1px dashed #e8e8e8; }
.day-col-body:focus-within, .day-col-body:hover { background: #fafafa; }
.schedule-item { position: absolute; left: 4px; right: 4px; border-radius: 4px; padding: 4px 8px; font-size: 12px; overflow: hidden; transition: box-shadow 0.2s, top 0.2s; z-index: 2; }
.schedule-item.is-draggable { cursor: grab; }
.schedule-item.is-draggable:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); z-index: 5; }
.schedule-item.is-draggable:active { cursor: grabbing; z-index: 10; opacity: 0.9; }
.schedule-item.is-locked { cursor: default; opacity: 0.72; }
.schedule-item.type-theory { background: #e6f4ff; border-left: 3px solid #1890ff; color: #003a8c; }
.schedule-item.type-skill { background: #f6ffed; border-left: 3px solid #52c41a; color: #135200; }
.schedule-item.type-review { background: #f9f0ff; border-left: 3px solid #722ed1; color: #391085; }
.schedule-item.type-physical { background: #fff7e6; border-left: 3px solid #fa8c16; color: #873800; }
.schedule-item.type-drill { background: #fff1f0; border-left: 3px solid #ff4d4f; color: #820014; }
.si-title { font-weight: 600; }
.si-meta { font-size: 11px; opacity: 0.8; }
.type-dot { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; background: #f5f5f5; }
.week-stats { display: flex; flex-direction: column; gap: 16px; }
.ws-item { display: flex; align-items: center; gap: 12px; }
.ws-icon { font-size: 28px; }
.ws-val { font-size: 20px; font-weight: 700; color: #1a1a1a; }
.ws-label { font-size: 12px; color: #888; }

@media (max-width: 768px) {
  .page-header { flex-direction: column; }
  .week-nav { width: 100%; justify-content: center; }
}
</style>
