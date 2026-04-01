<template>
  <div>
    <!-- 课表统计 -->
    <div v-if="courses.length" class="sched-stats">
      <div class="sched-stat">
        <span class="sched-stat-num">{{ courses.length }}</span>
        <span class="sched-stat-label">门课程</span>
      </div>
      <div class="sched-stat">
        <span class="sched-stat-num">{{ totalSessions }}</span>
        <span class="sched-stat-label">个课次</span>
      </div>
      <div class="sched-stat">
        <span class="sched-stat-num">{{ totalHours }}</span>
        <span class="sched-stat-label">总课时</span>
      </div>
    </div>

    <a-empty v-if="!courses.length" description="暂无课程安排" />
    <div v-else class="sched-course-list">
      <div
        v-for="course in courses"
        :key="course.course_key || course.name"
        class="sched-course-card"
        :class="`sched-type-${course.type || 'theory'}`"
      >
        <!-- 课程头 -->
        <div class="sched-course-top">
          <div class="sched-course-info">
            <h4 class="sched-course-name">{{ course.name }}</h4>
            <div class="sched-course-meta">
              <a-tag :color="course.type === 'practice' ? 'green' : 'blue'" size="small">
                {{ course.type === 'practice' ? '实操' : '理论' }}
              </a-tag>
              <span v-if="course.instructor"><UserOutlined /> {{ course.instructor }}</span>
              <span v-if="course.hours"><ClockCircleOutlined /> {{ course.hours }} 课时</span>
              <span>共 {{ (course.schedules || []).length }} 个课次</span>
            </div>
          </div>
        </div>

        <!-- 课次时间线 -->
        <div v-if="course.schedules?.length" class="sched-timeline">
          <div
            v-for="(s, i) in course.schedules"
            :key="i"
            class="sched-session"
            :class="{ 'is-past': isSessionPast(s), 'is-active': isSessionActive(s) }"
          >
            <div class="sched-dot-line">
              <span class="sched-dot" />
              <span v-if="i < course.schedules.length - 1" class="sched-line" />
            </div>
            <div class="sched-session-body">
              <div class="sched-session-row">
                <strong class="sched-session-date">{{ formatSessionDate(s.date) }}</strong>
                <span class="sched-session-time">{{ s.time_range?.replace('~', ' - ') }}</span>
                <a-tag v-if="s.status && s.status !== 'pending'" size="small" :color="sessionTagColor(s.status)">
                  {{ sessionStatusLabel(s.status) }}
                </a-tag>
              </div>
              <div v-if="s.location" class="sched-session-location">
                <EnvironmentOutlined /> {{ s.location }}
              </div>
            </div>
          </div>
        </div>
        <div v-else class="sched-no-session">暂无排课</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { UserOutlined, ClockCircleOutlined, EnvironmentOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import type { CourseItem, ScheduleItem } from './types'

const props = defineProps<{
  courses: CourseItem[]
}>()

const totalSessions = computed(() =>
  props.courses.reduce((sum, c) => sum + (c.schedules || []).length, 0),
)

const totalHours = computed(() => {
  const h = props.courses.reduce((sum, c) => sum + (c.hours || 0), 0)
  return Number.isInteger(h) ? h : h.toFixed(1)
})

function isSessionPast(s: ScheduleItem): boolean {
  if (!s.date) return false
  return s.date < dayjs().format('YYYY-MM-DD')
}

function isSessionActive(s: ScheduleItem): boolean {
  if (!s.status) return false
  return ['checkin_open', 'checkin_closed', 'checkout_open'].includes(s.status)
}

function formatSessionDate(date: string | undefined): string {
  if (!date) return '-'
  const d = dayjs(date)
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${d.format('MM/DD')} ${weekdays[d.day()]}`
}

function sessionTagColor(status: string): string {
  const map: Record<string, string> = {
    checkin_open: 'processing', checkin_closed: 'processing', checkout_open: 'warning',
    completed: 'success', skipped: 'default', missed: 'error',
  }
  return map[status] || 'default'
}

function sessionStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待开始', checkin_open: '签到中', checkin_closed: '进行中',
    checkout_open: '签退中', completed: '已完成', skipped: '已跳过', missed: '已缺课',
  }
  return map[status] || status
}
</script>

<style scoped>
.sched-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.sched-stat {
  display: flex;
  align-items: baseline;
  gap: 4px;
  padding: 10px 16px;
  border-radius: var(--v2-radius-sm);
  background: var(--v2-bg);
}

.sched-stat-num { font-size: 20px; font-weight: 700; color: var(--v2-primary); }
.sched-stat-label { font-size: 12px; color: var(--v2-text-muted); }

.sched-course-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sched-course-card {
  border-radius: var(--v2-radius);
  border: 1px solid var(--v2-border-light);
  overflow: hidden;
}

.sched-course-top {
  padding: 16px 18px;
  border-bottom: 1px solid var(--v2-border-light);
}

.sched-type-theory .sched-course-top { background: linear-gradient(135deg, rgba(75,110,245,0.04) 0%, transparent 100%); }
.sched-type-practice .sched-course-top { background: linear-gradient(135deg, rgba(52,199,89,0.04) 0%, transparent 100%); }

.sched-course-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin: 0 0 8px;
}

.sched-course-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 12px;
  color: var(--v2-text-muted);
  flex-wrap: wrap;
}

.sched-course-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* -- 时间线 -- */
.sched-timeline {
  padding: 16px 18px 12px;
}

.sched-session {
  display: flex;
  gap: 14px;
  position: relative;
}

.sched-dot-line {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 12px;
  flex-shrink: 0;
  padding-top: 6px;
}

.sched-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--v2-border);
  flex-shrink: 0;
  z-index: 1;
}

.sched-session.is-active .sched-dot {
  background: var(--v2-primary);
  box-shadow: 0 0 0 3px rgba(75,110,245,0.2);
}

.sched-session.is-past .sched-dot { background: var(--v2-text-muted); }

.sched-line {
  width: 1px;
  flex: 1;
  background: var(--v2-border-light);
  margin: 4px 0;
}

.sched-session-body {
  flex: 1;
  padding-bottom: 16px;
  min-width: 0;
}

.sched-session:last-child .sched-session-body { padding-bottom: 4px; }

.sched-session-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 2px;
}

.sched-session-date {
  font-size: 14px;
  color: var(--v2-text-primary);
  min-width: 90px;
}

.sched-session.is-past .sched-session-date { color: var(--v2-text-muted); }

.sched-session-time {
  font-size: 13px;
  color: var(--v2-text-secondary);
  min-width: 110px;
  font-variant-numeric: tabular-nums;
}

.sched-session.is-past .sched-session-time { color: var(--v2-text-muted); }

.sched-session-location {
  font-size: 12px;
  color: var(--v2-text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
}

.sched-no-session {
  padding: 20px 18px;
  font-size: 13px;
  color: var(--v2-text-muted);
  text-align: center;
}

@media (max-width: 768px) {
  .sched-stats { flex-wrap: wrap; }
  .sched-stat { flex: 1; min-width: 80px; }
}
</style>
