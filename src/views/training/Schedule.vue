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
        <a-button @click="prevWeek" :disabled="currentWeek <= 0">‹</a-button>
        <span class="week-label">第 {{ currentWeek + 1 }} 周（{{ weekRange }}）</span>
        <a-button @click="nextWeek">›</a-button>
      </div>
    </div>

    <!-- 空状态 -->
    <a-empty v-if="!selectedTraining" description="您暂无可查看的培训班课程计划" style="margin-top:60px" />

    <template v-else>
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
                 @drop="onDrop($event, day)"
            >
              <div v-for="item in getScheduleForDay(day.weekday)" :key="item.id"
                class="schedule-item" :class="'type-' + item.type"
                :style="{ top: getTopOffset(item.timeStart) + 'px', height: getHeight(item.duration) + 'px' }"
                draggable="true"
                @dragstart="onDragStart($event, item)"
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
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { MOCK_WEEK_SCHEDULE } from '@/mock/schedules'
import { MOCK_TRAININGS } from '@/mock/trainings'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()

// 根据角色过滤可见的培训班
const availableTrainings = computed(() => {
  if (authStore.isAdmin) {
    // 管理员看所有
    return MOCK_TRAININGS
  } else if (authStore.isInstructor) {
    // 教官看自己主讲的班
    const myName = authStore.currentUser?.name || authStore.currentUser?.username
    return MOCK_TRAININGS.filter(t => t.instructorName === myName || t.instructorId === authStore.currentUser?.username)
  } else {
    // 学员看自己已报名或已加入的班
    const me = authStore.currentUser?.id
    return MOCK_TRAININGS.filter(t =>
      (t.students || []).includes(me)
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
const initId = route.params.id || (availableTrainings.value.find(t => t.status === 'active')?.id) || availableTrainings.value[0]?.id
const selectedTrainingId = ref(initId || null)

const selectedTraining = computed(() =>
  availableTrainings.value.find(t => t.id === selectedTrainingId.value) || null
)

const currentWeek = ref(0)

function onTrainingChange() {
  currentWeek.value = 0
}

// 追踪调度更新
const triggerUpdate = ref(0)
const draggedItem = ref(null)

// 动态计算周日期，基于选中培训班的开始时间
const weekDays = computed(() => {
  const startDateStr = selectedTraining.value?.startDate || new Date().toISOString().split('T')[0]
  const base = new Date(startDateStr.replace(/-/g, '/'))
  base.setDate(base.getDate() + currentWeek.value * 7)
  
  const daysOfWeek = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  const today = new Date()
  
  const arr = []
  for (let i = 0; i < 5; i++) {
    const d = new Date(base)
    d.setDate(d.getDate() + i)
    
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const dt = String(d.getDate()).padStart(2, '0')
    
    arr.push({
      name: daysOfWeek[d.getDay()],
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
  return `${weekDays.value[0].date} - ${weekDays.value[4].date}`
})

const prevWeek = () => { if (currentWeek.value > 0) currentWeek.value-- }
const nextWeek = () => currentWeek.value++

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
            const timeStart = sch.timeRange ? sch.timeRange.split('~')[0] : '09:00'
            const timeEnd = sch.timeRange ? sch.timeRange.split('~')[1] : '12:00'
            
            let duration = 180
            if (timeStart && timeEnd) {
              const [sh, sm] = timeStart.split(':').map(Number)
              const [eh, em] = timeEnd.split(':').map(Number)
              duration = (eh - sh) * 60 + (em - sm)
            } else if (sch.hours) {
              duration = sch.hours * 60
            }
            
            items.push({
              id: `${selectedTraining.value.id}-c${cIdx}-s${sIdx}`,
              courseIdx: cIdx,
              scheduleIdx: sIdx,
              day: dayMatch.weekday,
              dayName: dayMatch.name,
              fullDate: schDateStr,
              title: c.name,
              type: c.type === 'practice' ? 'skill' : 'theory',
              timeStart,
              duration,
              location: selectedTraining.value.location,
              instructor: c.instructor,
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

// 连续修正时间轴避免对齐偏差
const timeSlots = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']

// 拖拽调整逻辑
function onDragStart(e, item) {
  draggedItem.value = item
  e.dataTransfer.effectAllowed = 'move'
}

function onDrop(e, targetDay) {
  if (!draggedItem.value) return
  const item = draggedItem.value
  
  // 基于容器计算确切的 Y 偏移
  const rect = e.currentTarget.getBoundingClientRect()
  const y = e.clientY - rect.top
  
  // 将 Y 轴像素反算为分钟 (1.2px = 1min)，并按照 30 分钟刻度吸附吸附
  let minutes = Math.round(y / 1.2)
  minutes = Math.round(minutes / 30) * 30
  
  const h = Math.floor(minutes / 60) + 8
  const m = minutes % 60
  const newStartString = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
  
  const endTotalMins = minutes + item.duration
  const endH = Math.floor(endTotalMins / 60) + 8
  const endM = endTotalMins % 60
  const newEndString = `${String(endH).padStart(2, '0')}:${String(endM).padStart(2, '0')}`
  
  // 静默更新训练班的排课数据并触发重渲染
  const scheduleRef = selectedTraining.value.courses[item.courseIdx].schedules[item.scheduleIdx]
  scheduleRef.date = targetDay.fullDate
  scheduleRef.timeRange = `${newStartString}~${newEndString}`
  
  triggerUpdate.value++
  draggedItem.value = null
}

const getTopOffset = (time) => {
  const [h, m] = (time || '08:00').split(':').map(Number)
  return Math.max(0, ((h - 8) * 60 + m) * 1.2)
}

const getHeight = (duration) => (duration || 90) * 1.2

const statusLabels = { active: '进行中', upcoming: '未开始', ended: '已结束' }
const statusColors = { active: 'green', upcoming: 'orange', ended: 'default' }
const dayNames = { 1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五' }
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
.schedule-item { position: absolute; left: 4px; right: 4px; border-radius: 4px; padding: 4px 8px; font-size: 12px; overflow: hidden; cursor: grab; transition: box-shadow 0.2s, top 0.2s; z-index: 2; }
.schedule-item:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); z-index: 5; }
.schedule-item:active { cursor: grabbing; z-index: 10; opacity: 0.9; }
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
