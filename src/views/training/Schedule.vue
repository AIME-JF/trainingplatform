<template>
  <div class="schedule-page">
    <div class="page-header">
      <h2>周训练计划</h2>
      <div class="week-nav">
        <a-button @click="prevWeek">‹</a-button>
        <span class="week-label">2025年第{{ weekNum }}周（{{ weekRange }}）</span>
        <a-button @click="nextWeek">›</a-button>
      </div>
    </div>

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

          <div class="day-col-body" v-for="day in weekDays" :key="day.date">
            <div v-for="item in getScheduleForDay(day.weekday)" :key="item.id"
              class="schedule-item" :class="'type-' + item.type"
              :style="{ top: getTopOffset(item.timeStart) + 'px', height: getHeight(item.duration) + 'px' }"
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
      <a-col :span="16">
        <a-card title="本周课程安排" :bordered="false">
          <a-list :dataSource="scheduleItems" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #avatar>
                    <div class="type-dot" :class="'type-' + item.type">{{ typeIcons[item.type] }}</div>
                  </template>
                  <template #title>{{ item.title }}</template>
                  <template #description>{{ item.day === 1 ? '周一' : item.day === 2 ? '周二' : item.day === 3 ? '周三' : item.day === 4 ? '周四' : '周五' }} {{ item.timeStart }} · {{ item.location }}</template>
                </a-list-item-meta>
                <template #extra>
                  <a-tag :color="typeColors[item.type]" size="small">{{ typeLabels[item.type] }}</a-tag>
                </template>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
      <a-col :span="8">
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
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { MOCK_WEEK_SCHEDULE } from '@/mock/schedules'

const scheduleItems = MOCK_WEEK_SCHEDULE.items || []

const currentWeek = ref(0)

// 动态计算周日期
const baseMonday = new Date(2025, 2, 10) // 2025-03-10 周一
const weekDays = computed(() => {
  const monday = new Date(baseMonday)
  monday.setDate(monday.getDate() + currentWeek.value * 7)
  const names = ['周一', '周二', '周三', '周四', '周五']
  return names.map((name, i) => {
    const d = new Date(monday)
    d.setDate(d.getDate() + i)
    return {
      name,
      date: `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`,
      weekday: i + 1,
      isToday: currentWeek.value === 0 && i === 0,
    }
  })
})

const weekNum = computed(() => {
  const monday = new Date(baseMonday)
  monday.setDate(monday.getDate() + currentWeek.value * 7)
  const start = new Date(monday.getFullYear(), 0, 1)
  return Math.ceil(((monday - start) / 86400000 + start.getDay()) / 7)
})

const weekRange = computed(() => {
  if (!weekDays.value.length) return ''
  return `${weekDays.value[0].date} - ${weekDays.value[4].date}`
})

const prevWeek = () => currentWeek.value--
const nextWeek = () => currentWeek.value++

const timeSlots = ['08:00', '09:00', '10:00', '11:00', '14:00', '15:00', '16:00', '17:00']

const getScheduleForDay = (weekday) => scheduleItems.filter(s => s.day === weekday)

const getTopOffset = (time) => {
  const [h, m] = (time || '08:00').split(':').map(Number)
  const baseHour = 8
  const hourOffset = (h - baseHour) * 60 + m
  return Math.max(0, hourOffset * 1.2)
}

const getHeight = (duration) => (duration || 90) * 1.2

const typeColors = { theory: 'blue', skill: 'green', review: 'purple', physical: 'orange', drill: 'red' }
const typeLabels = { theory: '理论课', skill: '技能课', review: '复习', physical: '体能', drill: '演练' }
const typeIcons = { theory: '📖', skill: '🔧', review: '📝', physical: '💪', drill: '⚠️' }

const weekStats = [
  { icon: '📚', label: '课程总数', value: scheduleItems.length + '节', color: '#003087' },
  { icon: '⏱', label: '总课时', value: scheduleItems.reduce((a, b) => a + (b.duration || 90), 0) + '分钟', color: '#52c41a' },
  { icon: '💪', label: '体能训练', value: scheduleItems.filter(s => s.type === 'physical').length + '节', color: '#faad14' },
  { icon: '📖', label: '理论课时', value: scheduleItems.filter(s => s.type === 'theory').reduce((a, b) => a + (b.duration || 90), 0) + '分钟', color: '#722ed1' },
]
</script>

<style scoped>
.schedule-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.week-nav { display: flex; align-items: center; gap: 12px; }
.week-label { font-size: 14px; font-weight: 500; color: #333; min-width: 200px; text-align: center; }
.schedule-card { overflow-x: auto; }
.schedule-grid { min-width: 700px; }
.grid-header { display: flex; border-bottom: 2px solid #003087; }
.time-col { width: 64px; flex-shrink: 0; }
.day-col { flex: 1; text-align: center; padding: 10px 4px; }
.day-col.today { background: #e8f0fe; border-radius: 6px 6px 0 0; }
.day-name { font-size: 12px; color: #888; }
.day-date { font-size: 16px; font-weight: 700; color: #333; }
.day-col.today .day-date { color: var(--police-primary); }
.grid-body { display: flex; position: relative; min-height: 480px; }
.time-slots { width: 64px; flex-shrink: 0; padding-top: 4px; }
.time-slot { height: 72px; font-size: 11px; color: #aaa; padding-top: 2px; }
.day-col-body { flex: 1; border-left: 1px dashed #e8e8e8; position: relative; padding: 4px; }
.schedule-item { position: absolute; left: 4px; right: 4px; border-radius: 4px; padding: 4px 8px; font-size: 12px; overflow: hidden; cursor: pointer; }
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
</style>
