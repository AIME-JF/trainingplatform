<template>
  <section class="page-content schedule-page">
    <!-- 页头 -->
    <div class="page-header">
      <h1 class="page-title">训练日历</h1>
      <div class="header-actions">
        <a-select
          v-model:value="selectedTrainingId"
          class="training-select"
          placeholder="全部班级"
          allow-clear
          show-search
          option-filter-prop="label"
          :options="trainingOptions"
          :loading="trainingLoading"
          @change="fetchCalendar"
        />
      </div>
    </div>

    <!-- 周切换条（参考图二） -->
    <div class="week-switcher">
      <button class="week-arrow" @click="goPrevWeek">&lt;</button>
      <div
        v-for="day in weekDays"
        :key="day.dateKey"
        class="week-day-cell"
        :class="{ today: day.isToday }"
      >
        <strong class="week-day-num">{{ day.dayNum }}</strong>
        <span class="week-day-label">{{ day.label }}</span>
      </div>
      <button class="week-arrow" @click="goNextWeek">&gt;</button>
    </div>

    <!-- 加载 -->
    <div v-if="loading" class="loading-wrapper"><a-spin size="large" /></div>

    <!-- 时间网格日历（参考图一） -->
    <div v-else class="cal-wrapper">
      <div class="cal-grid">
        <!-- 表头行 -->
        <div class="cal-corner" />
        <div
          v-for="day in weekDays"
          :key="'h-' + day.dateKey"
          class="cal-col-head"
          :class="{ today: day.isToday }"
        >
          <span class="col-head-name">{{ day.label }}</span>
          <strong class="col-head-date">{{ day.displayDate }}</strong>
        </div>

        <!-- 时间行 -->
        <template v-for="hour in timeSlots" :key="hour">
          <div class="cal-time-label">{{ hour }}:00</div>
          <div
            v-for="day in weekDays"
            :key="hour + '-' + day.dateKey"
            class="cal-cell"
            :class="{ today: day.isToday }"
          />
        </template>
      </div>

      <!-- 事件层：绝对定位在网格之上 -->
      <div class="cal-events-layer">
        <div
          v-for="ev in positionedEvents"
          :key="ev.key"
          class="cal-event"
          :class="`type-${ev.data.course_type}`"
          :style="ev.style"
          @dblclick="openDetail(ev.data)"
        >
          <strong class="ev-title">{{ ev.data.course_name }}</strong>
          <span class="ev-meta">{{ ev.timeLabel }}{{ ev.data.location ? ' · ' + ev.data.location : '' }}</span>
          <span class="ev-meta">{{ ev.data.instructor || '' }}</span>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <a-modal v-model:open="detailVisible" title="课时详情" :footer="null" width="480px">
      <template v-if="detailItem">
        <a-descriptions :column="1" size="small" bordered>
          <a-descriptions-item label="课程名称">{{ detailItem.course_name }}</a-descriptions-item>
          <a-descriptions-item label="所属班级">{{ detailItem.training_name }}</a-descriptions-item>
          <a-descriptions-item label="课程类型">
            <a-tag :color="detailItem.course_type === 'theory' ? 'blue' : 'green'" size="small">
              {{ detailItem.course_type === 'theory' ? '理论课' : '实操课' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="日期">{{ detailItem.date }}</a-descriptions-item>
          <a-descriptions-item label="时间">{{ detailItem.time_range.replace('~', ' - ') }}</a-descriptions-item>
          <a-descriptions-item label="课时">{{ detailItem.hours || '-' }} 课时</a-descriptions-item>
          <a-descriptions-item label="教官">{{ detailItem.instructor || '未指定' }}</a-descriptions-item>
          <a-descriptions-item label="地点">{{ detailItem.location || '未指定' }}</a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag size="small">{{ statusLabels[detailItem.status] || detailItem.status }}</a-tag>
          </a-descriptions-item>
        </a-descriptions>
        <div style="margin-top: 16px; text-align: right">
          <a-button type="primary" @click="goToClass(detailItem.training_id)">进入班级</a-button>
        </div>
      </template>
    </a-modal>
  </section>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, type CSSProperties } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { message } from 'ant-design-vue'
import axiosInstance from '@/api/custom-instance'

const router = useRouter()

const loading = ref(false)
const trainingLoading = ref(false)
const selectedTrainingId = ref<number | undefined>(undefined)
const trainingOptions = ref<{ value: number; label: string }[]>([])
const weekOffset = ref(0)

interface CalendarEvent {
  training_id: number
  training_name: string
  course_name: string
  course_type: string
  date: string
  time_range: string
  hours: number | null
  location: string | null
  instructor: string | null
  status: string
  session_id: string | null
}

const allEvents = ref<CalendarEvent[]>([])
const detailVisible = ref(false)
const detailItem = ref<CalendarEvent | null>(null)

const statusLabels: Record<string, string> = {
  pending: '待开始',
  checkin_open: '签到中',
  checkin_closed: '进行中',
  checkout_open: '签退中',
  completed: '已完成',
  skipped: '已跳过',
}

// 时间网格配置
const HOUR_START = 8
const HOUR_END = 19
const HOUR_HEIGHT = 60 // px per hour
const HEADER_HEIGHT = 50 // col header row height
const timeSlots = Array.from({ length: HOUR_END - HOUR_START }, (_, i) => HOUR_START + i)

// 当前周周一
const currentWeekStart = computed(() =>
  dayjs().startOf('week').add(1, 'day').add(weekOffset.value, 'week'),
)

const weekDays = computed(() =>
  Array.from({ length: 7 }, (_, i) => {
    const d = currentWeekStart.value.add(i, 'day')
    return {
      label: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][i],
      dateKey: d.format('YYYY-MM-DD'),
      displayDate: d.format('MM/DD'),
      dayNum: d.date(),
      colIndex: i,
      isToday: d.isSame(dayjs(), 'day'),
    }
  }),
)

const weekItems = computed(() => {
  const keys = new Set(weekDays.value.map((d) => d.dateKey))
  return allEvents.value.filter((e) => keys.has(e.date))
})

// 将事件转化为绝对定位样式
interface PositionedEvent {
  key: string
  data: CalendarEvent
  style: CSSProperties
  timeLabel: string
}

const positionedEvents = computed<PositionedEvent[]>(() => {
  const dateToCol = new Map(weekDays.value.map((d) => [d.dateKey, d.colIndex]))
  const colCount = 7
  const result: PositionedEvent[] = []

  for (const ev of weekItems.value) {
    const col = dateToCol.get(ev.date)
    if (col === undefined) continue

    const { startMin, endMin, startLabel } = parseTimeRange(ev.time_range)
    if (startMin < 0) continue

    const topPx = (startMin - HOUR_START * 60) / 60 * HOUR_HEIGHT + HEADER_HEIGHT
    const heightPx = Math.max((endMin - startMin) / 60 * HOUR_HEIGHT, 24)

    // Position within the 7-column area (after the 60px time-label gutter)
    const colWidthCalc = `(100% - 60px) / ${colCount}`
    const leftCalc = `calc(60px + ${col} * ${colWidthCalc})`
    const widthCalc = `calc(${colWidthCalc})`

    result.push({
      key: ev.session_id || `${ev.training_id}-${ev.course_name}-${ev.time_range}-${ev.date}`,
      data: ev,
      timeLabel: startLabel,
      style: {
        position: 'absolute',
        top: `${topPx}px`,
        height: `${heightPx}px`,
        left: leftCalc,
        width: widthCalc,
      },
    })
  }
  return result
})

function parseTimeRange(tr: string): { startMin: number; endMin: number; startLabel: string } {
  if (!tr || !tr.includes('~')) return { startMin: -1, endMin: -1, startLabel: '' }
  const [s, e] = tr.split('~').map((p) => p.trim())
  const toMin = (t: string) => {
    const [h, m] = t.split(':').map(Number)
    return h * 60 + (m || 0)
  }
  return { startMin: toMin(s), endMin: toMin(e), startLabel: s.slice(0, 5) }
}

function openDetail(item: CalendarEvent) {
  detailItem.value = item
  detailVisible.value = true
}

function goToClass(id: number) {
  detailVisible.value = false
  router.push(`/classes/${id}`)
}

function goPrevWeek() { weekOffset.value -= 1 }
function goNextWeek() { weekOffset.value += 1 }

async function fetchTrainings() {
  trainingLoading.value = true
  try {
    const res = await axiosInstance.get('/trainings', { params: { page: 1, size: -1 } })
    const data = res.data as { items: { id: number; name: string }[] }
    trainingOptions.value = (data.items || []).map((t) => ({ value: t.id, label: t.name }))
  } catch {
    trainingOptions.value = []
  } finally {
    trainingLoading.value = false
  }
}

async function fetchCalendar() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {}
    if (selectedTrainingId.value) params.training_id = selectedTrainingId.value
    const res = await axiosInstance.get('/trainings/calendar', { params })
    allEvents.value = (res.data as CalendarEvent[]) || []
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '加载日历失败')
    allEvents.value = []
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchTrainings()
  await fetchCalendar()
})
</script>

<style scoped>
.schedule-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* -- 页头 -- */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--v2-text-primary);
}

.header-actions { display: flex; gap: 12px; }
.training-select { width: 220px; max-width: 100%; }

/* ====== 周切换条（图二样式） ====== */
.week-switcher {
  display: flex;
  align-items: center;
  background: var(--v2-bg-card);
  border-radius: var(--v2-radius);
  padding: 10px 6px;
  box-shadow: var(--v2-shadow-sm);
}

.week-arrow {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  font-size: 16px;
  color: var(--v2-text-muted);
  cursor: pointer;
  border-radius: var(--v2-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.15s, color 0.15s;
}

.week-arrow:hover {
  background: var(--v2-bg);
  color: var(--v2-text-primary);
}

.week-day-cell {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 0;
  border-radius: var(--v2-radius-sm);
  cursor: default;
}

.week-day-num {
  font-size: 18px;
  font-weight: 600;
  color: var(--v2-text-primary);
  line-height: 1.2;
}

.week-day-label {
  font-size: 11px;
  color: var(--v2-text-muted);
}

.week-day-cell.today {
  background: var(--v2-primary);
  border-radius: var(--v2-radius);
}

.week-day-cell.today .week-day-num {
  color: #fff;
}

.week-day-cell.today .week-day-label {
  color: rgba(255, 255, 255, 0.7);
}

/* ====== 时间网格日历（图一样式） ====== */
.loading-wrapper { padding: 80px 0; display: flex; justify-content: center; }

.cal-wrapper {
  position: relative;
  background: var(--v2-bg-card);
  border-radius: var(--v2-radius);
  overflow: hidden;
  box-shadow: var(--v2-shadow-sm);
}

.cal-grid {
  display: grid;
  /* 60px for time label + 7 equal columns */
  grid-template-columns: 60px repeat(7, 1fr);
}

/* -- 左上角空格 -- */
.cal-corner {
  height: 50px;
  border-bottom: 2px solid var(--v2-primary);
  background: var(--v2-bg-card);
  position: sticky;
  top: 0;
  z-index: 3;
}

/* -- 列头 -- */
.cal-col-head {
  height: 50px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  border-bottom: 2px solid var(--v2-primary);
  background: var(--v2-bg-card);
  position: sticky;
  top: 0;
  z-index: 3;
}

.cal-col-head.today {
  background: var(--v2-primary-light);
}

.col-head-name {
  font-size: 12px;
  color: var(--v2-text-secondary);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.cal-col-head.today .col-head-name {
  color: var(--v2-primary);
  font-weight: 600;
}

.col-head-date {
  font-size: 14px;
  font-weight: 600;
  color: var(--v2-text-primary);
}

.cal-col-head.today .col-head-date {
  color: var(--v2-primary);
}

/* -- 时间标签 -- */
.cal-time-label {
  height: 60px;
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  padding: 0 8px;
  font-size: 11px;
  color: var(--v2-text-muted);
  border-top: 1px solid var(--v2-border-light);
  transform: translateY(-7px);
}

/* -- 单元格 -- */
.cal-cell {
  height: 60px;
  border-top: 1px solid var(--v2-border-light);
  border-left: 1px solid var(--v2-border-light);
}

.cal-cell.today {
  background: rgba(75, 110, 245, 0.02);
}

/* ====== 事件层 ====== */
.cal-events-layer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.cal-event {
  position: absolute;
  /* left/top/width/height set by inline style */
  pointer-events: auto;
  border-radius: 4px;
  padding: 4px 6px;
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 1px;
  border-left: 3px solid var(--v2-primary);
  background: rgba(219, 234, 254, 0.7);
  transition: box-shadow 0.15s;
  margin: 0 2px;
}

.cal-event:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  z-index: 5;
}

.cal-event.type-theory {
  border-left-color: var(--v2-primary);
  background: rgba(219, 234, 254, 0.7);
}

.cal-event.type-practice,
.cal-event.type-skill {
  border-left-color: var(--v2-success);
  background: rgba(209, 250, 229, 0.7);
}

.ev-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--v2-text-primary);
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ev-meta {
  font-size: 10px;
  color: var(--v2-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ====== 响应式 ====== */
@media (max-width: 768px) {
  .training-select { width: 100%; }
  .cal-grid { grid-template-columns: 40px repeat(7, 1fr); }
  .cal-time-label { padding: 0 4px; font-size: 10px; }
  .week-day-num { font-size: 15px; }
}
</style>
