<template>
  <section class="page-content schedule-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">周训练计划</h1>
        <p class="page-subtitle">按培训班查看本周课程安排和每日训练节次。</p>
      </div>

      <div class="header-actions">
        <a-select
          v-model:value="selectedTrainingId"
          class="training-select"
          :options="trainingOptions"
          placeholder="请选择培训班"
          :loading="trainingLoading"
          show-search
          option-filter-prop="label"
          @change="handleTrainingChange"
        />
      </div>
    </div>

    <div v-if="selectedTraining" class="hero-strip">
      <div class="hero-main">
        <div class="hero-badges">
          <span v-if="selectedTraining.status" class="hero-badge" :class="`badge-${selectedTraining.status}`">
            {{ statusLabels[selectedTraining.status] || selectedTraining.status }}
          </span>
          <span class="hero-badge subtle">{{ typeLabels[selectedTraining.type] || selectedTraining.type || '训练班' }}</span>
        </div>
        <h2 class="hero-title">{{ selectedTraining.name }}</h2>
        <div class="hero-meta">
          <span><UserOutlined /> {{ selectedTraining.instructor_name || '未指定教官' }}</span>
          <span><EnvironmentOutlined /> {{ selectedTraining.location || '未设置地点' }}</span>
          <span><TeamOutlined /> {{ selectedTraining.enrolled_count ?? 0 }}{{ selectedTraining.capacity ? ` / ${selectedTraining.capacity}` : '' }} 人</span>
        </div>
      </div>

      <div class="week-switcher">
        <a-button :disabled="weekStartList.length <= 1 || currentWeekIndex <= 0" @click="goPrevWeek">上一周</a-button>
        <div class="week-current">
          <strong>{{ currentWeekLabel }}</strong>
          <span>{{ currentWeekRange }}</span>
        </div>
        <a-button :disabled="weekStartList.length <= 1 || currentWeekIndex >= weekStartList.length - 1" @click="goNextWeek">下一周</a-button>
      </div>
    </div>

    <div v-if="trainingLoading || scheduleLoading" class="loading-wrapper">
      <a-spin size="large" />
    </div>

    <a-empty
      v-else-if="!trainingOptions.length"
      description="暂无可查看的培训班"
      class="empty-block"
    />

    <a-empty
      v-else-if="!selectedTraining"
      description="请选择培训班查看课表"
      class="empty-block"
    />

    <template v-else>
      <a-empty
        v-if="!normalizedScheduleItems.length"
        description="当前培训班暂无训练安排"
        class="empty-block"
      />

      <template v-else>
        <div class="stats-row">
          <div class="stat-card">
            <span class="stat-label">本周课程</span>
            <strong class="stat-value">{{ currentWeekItems.length }}</strong>
          </div>
          <div class="stat-card">
            <span class="stat-label">理论课程</span>
            <strong class="stat-value">{{ currentWeekItems.filter((item) => item.type === 'theory').length }}</strong>
          </div>
          <div class="stat-card">
            <span class="stat-label">技能课程</span>
            <strong class="stat-value">{{ currentWeekItems.filter((item) => item.type === 'skill').length }}</strong>
          </div>
          <div class="stat-card">
            <span class="stat-label">训练地点</span>
            <strong class="stat-value stat-text">{{ distinctLocations }}</strong>
          </div>
        </div>

        <div class="schedule-board">
          <article
            v-for="day in currentWeekDays"
            :key="day.dateKey"
            class="day-column"
            :class="{ today: day.isToday }"
          >
            <header class="day-head">
              <span class="day-name">{{ day.label }}</span>
              <strong class="day-date">{{ day.displayDate }}</strong>
            </header>

            <div v-if="getItemsForDay(day.dateKey).length" class="day-list">
              <div
                v-for="item in getItemsForDay(day.dateKey)"
                :key="item.id"
                class="schedule-item"
                :class="`type-${item.type}`"
              >
                <div class="schedule-item-top">
                  <strong>{{ item.title }}</strong>
                  <a-tag :color="typeTagColors[item.type] || 'blue'">{{ typeTagLabels[item.type] || '课程' }}</a-tag>
                </div>
                <div class="schedule-item-meta">
                  <span><ClockCircleOutlined /> {{ item.timeText }}</span>
                  <span><EnvironmentOutlined /> {{ item.location || '地点待定' }}</span>
                </div>
                <div class="schedule-item-meta secondary">
                  <span><UserOutlined /> {{ item.instructor || selectedTraining.instructor_name || '待安排' }}</span>
                  <span v-if="item.status">{{ statusLabels[item.status] || item.status }}</span>
                </div>
              </div>
            </div>

            <a-empty v-else :image="simpleImage" description="当天无安排" class="day-empty" />
          </article>
        </div>
      </template>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import dayjs from 'dayjs'
import { Empty, message } from 'ant-design-vue'
import {
  ClockCircleOutlined,
  EnvironmentOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'
import {
  getScheduleApiV1TrainingsTrainingIdScheduleGet,
  getTrainingsApiV1TrainingsGet,
} from '@/api/generated/training-management/training-management'
import type { ScheduleItemResponse, TrainingListResponse } from '@/api/generated/model'

interface NormalizedScheduleItem {
  id: number
  dateKey: string
  title: string
  type: string
  timeText: string
  location: string
  instructor: string
  status: string
}

interface WeekDayInfo {
  label: string
  dateKey: string
  displayDate: string
  isToday: boolean
}

const route = useRoute()
const router = useRouter()

const trainingLoading = ref(false)
const scheduleLoading = ref(false)
const trainingList = ref<TrainingListResponse[]>([])
const selectedTrainingId = ref<number | undefined>()
const rawScheduleItems = ref<ScheduleItemResponse[]>([])
const currentWeekIndex = ref(0)

const simpleImage = Empty.PRESENTED_IMAGE_SIMPLE

const statusLabels: Record<string, string> = {
  active: '进行中',
  upcoming: '未开始',
  ended: '已结束',
  draft: '草稿',
  pending: '待开始',
}

const typeLabels: Record<string, string> = {
  basic: '基础训练',
  special: '专项训练',
  promotion: '晋升培训',
  online: '线上培训',
}

const typeTagLabels: Record<string, string> = {
  theory: '理论课',
  skill: '技能课',
  practice: '实训课',
}

const typeTagColors: Record<string, string> = {
  theory: 'blue',
  skill: 'green',
  practice: 'orange',
}

const trainingOptions = computed(() =>
  trainingList.value.map((item) => ({
    value: item.id,
    label: item.name,
  })),
)

const selectedTraining = computed(() =>
  trainingList.value.find((item) => item.id === selectedTrainingId.value) || null,
)

const normalizedScheduleItems = computed<NormalizedScheduleItem[]>(() =>
  rawScheduleItems.value
    .map((item) => {
      const dateValue = resolveItemDate(item)
      if (!dateValue) return null

      const timeStart = normalizeClock(item.time_start)
      const timeEnd = normalizeClock(item.time_end)
      const timeText = timeStart && timeEnd ? `${timeStart} - ${timeEnd}` : (timeStart || timeEnd || '时间待定')

      return {
        id: item.id,
        dateKey: dateValue.format('YYYY-MM-DD'),
        title: item.title || '未命名课程',
        type: item.type || 'theory',
        timeText,
        location: item.location || '',
        instructor: item.instructor || '',
        status: item.status || '',
      }
    })
    .filter((item): item is NormalizedScheduleItem => Boolean(item))
    .sort((left, right) => `${left.dateKey} ${left.timeText}`.localeCompare(`${right.dateKey} ${right.timeText}`)),
)

const weekStartList = computed(() => {
  const weekMap = new Map<string, dayjs.Dayjs>()
  for (const item of rawScheduleItems.value) {
    const dateValue = resolveItemDate(item)
    if (!dateValue) continue
    const start = dateValue.startOf('week').add(1, 'day')
    weekMap.set(start.format('YYYY-MM-DD'), start)
  }

  if (!weekMap.size && selectedTraining.value?.start_date) {
    const fallback = dayjs(selectedTraining.value.start_date).startOf('week').add(1, 'day')
    weekMap.set(fallback.format('YYYY-MM-DD'), fallback)
  }

  return [...weekMap.values()].sort((left, right) => left.valueOf() - right.valueOf())
})

const currentWeekStart = computed(() => weekStartList.value[currentWeekIndex.value] || null)

const currentWeekDays = computed<WeekDayInfo[]>(() => {
  const base = currentWeekStart.value || dayjs().startOf('week').add(1, 'day')
  return Array.from({ length: 7 }, (_, index) => {
    const day = base.add(index, 'day')
    return {
      label: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'][index],
      dateKey: day.format('YYYY-MM-DD'),
      displayDate: day.format('MM/DD'),
      isToday: day.isSame(dayjs(), 'day'),
    }
  })
})

const currentWeekItems = computed(() => {
  const validKeys = new Set(currentWeekDays.value.map((item) => item.dateKey))
  return normalizedScheduleItems.value.filter((item) => validKeys.has(item.dateKey))
})

const currentWeekLabel = computed(() =>
  currentWeekStart.value ? `第 ${currentWeekIndex.value + 1} 周` : '本周',
)

const currentWeekRange = computed(() => {
  if (!currentWeekDays.value.length) return ''
  return `${currentWeekDays.value[0].displayDate} - ${currentWeekDays.value[6].displayDate}`
})

const distinctLocations = computed(() => {
  const values = [...new Set(currentWeekItems.value.map((item) => item.location).filter(Boolean))]
  if (!values.length) return '待定'
  if (values.length === 1) return values[0]
  return `${values[0]} 等 ${values.length} 处`
})

function normalizeClock(value?: string | null) {
  if (!value) return ''
  return value.slice(0, 5)
}

function resolveItemDate(item: ScheduleItemResponse) {
  if (item.date) return dayjs(item.date)
  if (item.week_start && typeof item.day === 'number') {
    return dayjs(item.week_start).add(Math.max(item.day - 1, 0), 'day')
  }
  return null
}

function getItemsForDay(dateKey: string) {
  return currentWeekItems.value.filter((item) => item.dateKey === dateKey)
}

function syncRouteWithTraining(trainingId?: number) {
  const currentId = route.params.id ? Number(route.params.id) : undefined
  if (!trainingId) {
    if (currentId) {
      router.replace({ name: 'ClassSchedule' })
    }
    return
  }
  if (currentId !== trainingId) {
    router.replace({ name: 'ClassSchedule', params: { id: trainingId } })
  }
}

function chooseInitialTrainingId() {
  const routeId = route.params.id ? Number(route.params.id) : undefined
  if (routeId && trainingList.value.some((item) => item.id === routeId)) {
    return routeId
  }
  return trainingList.value.find((item) => item.status === 'active')?.id || trainingList.value[0]?.id
}

function chooseInitialWeekIndex() {
  if (!weekStartList.value.length) {
    currentWeekIndex.value = 0
    return
  }
  const todayIndex = weekStartList.value.findIndex((item) => dayjs().isSame(item, 'week'))
  currentWeekIndex.value = todayIndex >= 0 ? todayIndex : 0
}

async function fetchTrainings() {
  trainingLoading.value = true
  try {
    const response = await getTrainingsApiV1TrainingsGet({ page: 1, size: -1 })
    trainingList.value = response?.items || []
    selectedTrainingId.value = chooseInitialTrainingId()
    syncRouteWithTraining(selectedTrainingId.value)
  } catch (error) {
    trainingList.value = []
    message.error(error instanceof Error ? error.message : '加载培训班失败')
  } finally {
    trainingLoading.value = false
  }
}

async function fetchSchedule(trainingId?: number) {
  if (!trainingId) {
    rawScheduleItems.value = []
    currentWeekIndex.value = 0
    return
  }

  scheduleLoading.value = true
  try {
    rawScheduleItems.value = (await getScheduleApiV1TrainingsTrainingIdScheduleGet(trainingId)) || []
    chooseInitialWeekIndex()
  } catch (error) {
    rawScheduleItems.value = []
    currentWeekIndex.value = 0
    message.error(error instanceof Error ? error.message : '加载周训练计划失败')
  } finally {
    scheduleLoading.value = false
  }
}

async function handleTrainingChange(value: number) {
  selectedTrainingId.value = value
  syncRouteWithTraining(value)
  await fetchSchedule(value)
}

function goPrevWeek() {
  if (currentWeekIndex.value > 0) {
    currentWeekIndex.value -= 1
  }
}

function goNextWeek() {
  if (currentWeekIndex.value < weekStartList.value.length - 1) {
    currentWeekIndex.value += 1
  }
}

watch(
  () => route.params.id,
  async (value) => {
    const nextId = value ? Number(value) : undefined
    if (!nextId || nextId === selectedTrainingId.value) {
      return
    }
    if (trainingList.value.some((item) => item.id === nextId)) {
      selectedTrainingId.value = nextId
      await fetchSchedule(nextId)
    }
  },
)

onMounted(async () => {
  await fetchTrainings()
  await fetchSchedule(selectedTrainingId.value)
})
</script>

<style scoped>
.schedule-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--v2-text-primary);
  margin-bottom: 6px;
}

.page-subtitle {
  color: var(--v2-text-secondary);
  line-height: 1.7;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.training-select {
  width: 320px;
  max-width: 100%;
}

.hero-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
  padding: 24px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.96) 0%, rgba(240, 243, 255, 0.88) 100%);
  box-shadow: var(--v2-shadow);
}

.hero-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hero-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--v2-radius-full);
  font-size: 12px;
  font-weight: 600;
}

.hero-badge.subtle {
  background: rgba(75, 110, 245, 0.1);
  color: var(--v2-primary);
}

.badge-active {
  background: rgba(52, 199, 89, 0.14);
  color: #278947;
}

.badge-upcoming {
  background: rgba(75, 110, 245, 0.14);
  color: var(--v2-primary);
}

.badge-ended {
  background: rgba(142, 142, 147, 0.14);
  color: #6f6f75;
}

.hero-title {
  font-size: 28px;
  line-height: 1.1;
  color: var(--v2-text-primary);
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.hero-meta span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.week-switcher {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.week-current {
  min-width: 180px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.week-current strong {
  font-size: 16px;
  color: var(--v2-text-primary);
}

.week-current span {
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.loading-wrapper,
.empty-block {
  padding: 80px 0;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px 20px;
  border-radius: 20px;
  background: var(--v2-bg-card);
  box-shadow: var(--v2-shadow-sm);
}

.stat-label {
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.stat-value {
  font-size: 28px;
  line-height: 1;
  color: var(--v2-text-primary);
}

.stat-text {
  font-size: 18px;
  line-height: 1.4;
}

.schedule-board {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 14px;
}

.day-column {
  display: flex;
  flex-direction: column;
  min-height: 360px;
  border-radius: 22px;
  padding: 14px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(245, 246, 250, 0.92) 100%);
  box-shadow: var(--v2-shadow-sm);
}

.day-column.today {
  box-shadow: 0 0 0 1px rgba(75, 110, 245, 0.14), var(--v2-shadow);
  background: linear-gradient(180deg, rgba(238, 242, 255, 0.88) 0%, rgba(255, 255, 255, 0.96) 100%);
}

.day-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-bottom: 12px;
  margin-bottom: 12px;
  border-bottom: 1px solid rgba(229, 229, 234, 0.85);
}

.day-name {
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.day-date {
  font-size: 20px;
  color: var(--v2-text-primary);
}

.day-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.schedule-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(229, 229, 234, 0.82);
}

.schedule-item.type-theory {
  border-color: rgba(75, 110, 245, 0.16);
  background: linear-gradient(180deg, rgba(238, 242, 255, 0.86) 0%, rgba(255, 255, 255, 0.96) 100%);
}

.schedule-item.type-skill,
.schedule-item.type-practice {
  border-color: rgba(52, 199, 89, 0.18);
  background: linear-gradient(180deg, rgba(241, 253, 245, 0.92) 0%, rgba(255, 255, 255, 0.98) 100%);
}

.schedule-item-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
}

.schedule-item-top strong {
  font-size: 14px;
  line-height: 1.5;
  color: var(--v2-text-primary);
}

.schedule-item-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.schedule-item-meta span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.schedule-item-meta.secondary {
  padding-top: 6px;
  border-top: 1px dashed rgba(229, 229, 234, 0.9);
}

.day-empty {
  margin: auto 0;
  padding: 32px 0 16px;
}

@media (max-width: 1400px) {
  .schedule-board {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 1024px) {
  .stats-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .schedule-board {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .page-header,
  .hero-strip {
    align-items: flex-start;
  }

  .training-select {
    width: 100%;
  }

  .header-actions,
  .week-switcher {
    width: 100%;
  }

  .week-switcher {
    justify-content: space-between;
  }

  .stats-row,
  .schedule-board {
    grid-template-columns: 1fr;
  }

  .hero-strip,
  .day-column {
    padding: 18px;
  }
}
</style>
