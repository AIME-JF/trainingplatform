<template>
  <div class="dashboard">
    <!-- 欢迎语 -->
    <div class="welcome-bar">
      <div class="welcome-text">
        <h2>{{ greeting }}，{{ authStore.currentUser?.name }} {{ roleLabel }}</h2>
        <p>{{ today }} · {{ authStore.currentUser?.unit }}</p>
      </div>
      <div class="welcome-actions" v-if="isStudent">
        <a-button type="primary" @click="$router.push('/courses')">
          <PlayCircleOutlined /> 继续学习
        </a-button>
        <a-button @click="$router.push('/exam/bank')">
          <FormOutlined /> 参加考试
        </a-button>
      </div>
      <div class="welcome-actions" v-else-if="isInstructor">
        <a-button type="primary" @click="$router.push('/ai/question-gen')">
          <RobotOutlined /> AI 智能组卷
        </a-button>
        <a-button @click="$router.push('/training')">
          <TeamOutlined /> 我的培训班
        </a-button>
      </div>
      <div class="welcome-actions" v-else>
        <a-button type="primary" @click="$router.push('/report')">
          <BarChartOutlined /> 查看数据看板
        </a-button>
        <a-button @click="$router.push('/training')">
          <PlusOutlined /> 新建培训班
        </a-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div
        v-for="stat in dashData.stats"
        :key="stat.label"
        class="stat-card"
      >
        <div class="stat-value">
          {{ stat.value }}<span class="stat-unit">{{ stat.unit }}</span>
        </div>
        <div class="stat-label">{{ stat.label }}</div>
        <div class="stat-trend" :class="stat.trendType" v-if="stat.trend">
          <arrow-up-outlined v-if="stat.trendType === 'up'" />
          {{ stat.trend }}
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="dashboard-body">
      <!-- 学员视图 -->
      <template v-if="isStudent">
        <div class="grid-2">
          <!-- 待办事项 -->
          <div class="police-card">
            <div class="card-header">
              <span class="card-title">待完成任务</span>
              <a-tag color="red">{{ dashData.pendingTasks.length }} 项</a-tag>
            </div>
            <div class="task-list">
              <div
                v-for="task in dashData.pendingTasks"
                :key="task.id"
                class="task-item"
                :class="{ urgent: task.urgent }"
              >
                <span class="task-dot" :class="task.urgent ? 'red' : 'blue'" />
                <span class="task-text">{{ task.text }}</span>
                <right-outlined class="task-arrow" />
              </div>
            </div>
          </div>

          <!-- 最近学习 -->
          <div class="police-card">
            <div class="card-header">
              <span class="card-title">最近学习</span>
              <a @click="$router.push('/courses')">查看全部 →</a>
            </div>
            <div class="recent-courses">
              <div
                v-for="course in dashData.recentCourses"
                :key="course.id"
                class="recent-course"
                @click="$router.push(`/courses/${course.id}`)"
              >
                <div class="course-name">{{ course.title }}</div>
                <div class="course-progress-row">
                  <a-progress
                    :percent="course.progress"
                    :strokeColor="'#003087'"
                    size="small"
                    style="flex:1"
                  />
                  <span class="progress-text">{{ course.progress }}%</span>
                </div>
                <div class="course-meta">上次学习：{{ course.lastStudied }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 本月进度 -->
        <div class="police-card" style="margin-top: 16px">
          <div class="card-header">
            <span class="card-title">本月训练完成度</span>
            <span class="card-sub">目标：完成5项训练任务</span>
          </div>
          <div class="month-progress">
            <a-progress
              :percent="dashData.monthProgress"
              :strokeColor="{ '0%': '#003087', '100%': '#1a4fa0' }"
              size="default"
            />
            <div class="progress-hint">已完成 3/5 项，继续加油！</div>
          </div>
        </div>
      </template>

      <!-- 教官视图 -->
      <template v-else-if="isInstructor">
        <div class="grid-2">
          <!-- 本周课程安排 -->
          <div class="police-card">
            <div class="card-header">
              <span class="card-title">本周课程安排</span>
              <a @click="$router.push('/training/schedule')">查看完整计划 →</a>
            </div>
            <div class="schedule-list">
              <div
                v-for="item in dashData.weekSchedule"
                :key="item.day"
                class="schedule-item"
              >
                <div class="schedule-day">
                  <div class="day-label">{{ item.day }}</div>
                  <div class="day-date">{{ item.date }}</div>
                </div>
                <div class="schedule-info">
                  <div class="schedule-course">{{ item.course }}</div>
                  <div class="schedule-meta">{{ item.time }} · {{ item.room }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 待处理事项 -->
          <div class="police-card">
            <div class="card-header">
              <span class="card-title">待处理事项</span>
              <a-badge :count="dashData.pendingTasks.length" />
            </div>
            <div class="pending-list">
              <div v-for="(task, i) in dashData.pendingTasks" :key="i" class="pending-item">
                <warning-outlined style="color: #faad14; margin-right: 8px" />
                {{ task.text }}
              </div>
            </div>

            <!-- 学员学情 -->
            <div style="margin-top: 20px">
              <div class="card-sub" style="margin-bottom: 12px">学员学习进度概览</div>
              <div v-for="s in dashData.studentProgressData" :key="s.name" class="student-row">
                <span class="student-name">{{ s.name }}</span>
                <a-progress :percent="s.progress" size="small" style="flex:1;margin:0 12px" />
                <span class="student-score">{{ s.score }}分</span>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- 管理员视图 -->
      <template v-else>
        <div class="grid-3">
          <!-- 系统公告 -->
          <div class="police-card">
            <div class="card-header">
              <span class="card-title">系统公告</span>
              <a-button size="small" type="text" @click="announceMsg">发布公告</a-button>
            </div>
            <div class="notice-list">
              <div v-for="n in dashData.announcements" :key="n.id" class="notice-item">
                <a-tag v-if="n.urgent" color="red" size="small">紧急</a-tag>
                <span class="notice-title">{{ n.title }}</span>
                <span class="notice-date">{{ n.date }}</span>
              </div>
            </div>
          </div>

          <!-- 近期培训班 -->
          <div class="police-card">
            <div class="card-header">
              <span class="card-title">近期培训班</span>
              <a @click="$router.push('/training')">查看全部 →</a>
            </div>
            <div class="training-mini-list">
              <div v-for="t in dashData.recentTrainings" :key="t.name" class="training-mini-item">
                <span class="status-dot" :class="t.status" />
                <div class="training-mini-info">
                  <div class="training-mini-name">{{ t.name }}</div>
                  <div class="training-mini-meta">{{ t.enrolled }}人报名 · {{ t.startDate }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 快速操作 -->
          <div class="police-card">
            <div class="card-header"><span class="card-title">快速操作</span></div>
            <div class="quick-actions">
              <div class="qa-item" @click="$router.push('/training')">
                <div class="qa-icon" style="background:#003087">📋</div>
                <span>新建培训班</span>
              </div>
              <div class="qa-item" @click="$router.push('/ai/question-gen')">
                <div class="qa-icon" style="background:#1a7a3e">🤖</div>
                <span>AI智能组卷</span>
              </div>
              <div class="qa-item" @click="$router.push('/instructor')">
                <div class="qa-icon" style="background:#8b1a1a">👮</div>
                <span>教官管理</span>
              </div>
              <div class="qa-item" @click="$router.push('/report')">
                <div class="qa-icon" style="background:#4a3728">📊</div>
                <span>数据看板</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth.js'
import { getDashboard } from '@/api/dashboard'
import { message } from 'ant-design-vue'
import {
  PlayCircleOutlined, FormOutlined, RobotOutlined, TeamOutlined,
  BarChartOutlined, PlusOutlined, RightOutlined, ArrowUpOutlined,
  WarningOutlined,
} from '@ant-design/icons-vue'

const authStore = useAuthStore()
const isStudent = computed(() => authStore.isStudent)
const isInstructor = computed(() => authStore.isInstructor)
const isAdmin = computed(() => authStore.isAdmin)

const roleLabel = computed(() => {
  if (isAdmin.value) return '管理员'
  if (isInstructor.value) return '教官'
  return '同志'
})

const now = new Date()
const hour = now.getHours()
const greeting = hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好'
const today = `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日`

const dashData = ref({ stats: [], pendingTasks: [], recentCourses: [], weekSchedule: [], monthProgress: 0, announcements: [], recentTrainings: [], studentProgressData: [] })

onMounted(async () => {
  try {
    const role = isAdmin.value ? 'admin' : isInstructor.value ? 'instructor' : 'student'
    const res = await getDashboard(role)
    // Adapt backend response format to frontend expected structure
    if (res) {
      const adapted = { ...res }
      // If stats is a dict, convert to array format expected by frontend
      if (res.stats && !Array.isArray(res.stats)) {
        adapted.stats = Object.entries(res.stats).map(([key, val]) => ({
          label: key,
          value: val,
          unit: '',
        }))
      }
      Object.assign(dashData.value, adapted)
    }
  } catch {
    // Silently fail - dashboard will show empty state
  }
})

const announceMsg = () => message.info('公告发布功能开发中...')
</script>

<style scoped>
.dashboard {}

.welcome-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: white;
  border-radius: var(--police-radius-lg);
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: var(--police-shadow-sm);
  border-left: 4px solid var(--police-primary);
}

.welcome-text h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--police-text-primary);
  margin-bottom: 4px;
}

.welcome-text p {
  font-size: 13px;
  color: var(--police-text-muted);
}

.welcome-actions {
  display: flex;
  gap: 10px;
}

/* 统计卡片 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  border-radius: var(--police-radius);
  padding: 20px;
  box-shadow: var(--police-shadow-sm);
  border: 1px solid var(--police-border-light);
  transition: box-shadow 0.2s;
}

.stat-card:hover {
  box-shadow: var(--police-shadow);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--police-primary);
  line-height: 1;
  margin-bottom: 8px;
}

.stat-unit {
  font-size: 14px;
  font-weight: 400;
  color: var(--police-text-secondary);
  margin-left: 2px;
}

.stat-label {
  font-size: 13px;
  color: var(--police-text-secondary);
  margin-bottom: 4px;
}

.stat-trend {
  font-size: 12px;
}
.stat-trend.up { color: #389e0d; }
.stat-trend.warning { color: #d48806; }

/* 网格布局 */
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--police-text-primary);
}

.card-sub {
  font-size: 12px;
  color: var(--police-text-muted);
}

/* 任务列表 */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--police-radius-sm);
  background: var(--police-bg);
  cursor: pointer;
  transition: background 0.2s;
}

.task-item:hover { background: var(--police-primary-light); }
.task-item.urgent { background: #fff1f0; }

.task-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.task-dot.red { background: #cf1322; }
.task-dot.blue { background: #003087; }

.task-text { flex: 1; font-size: 13px; color: var(--police-text-primary); }
.task-arrow { font-size: 11px; color: var(--police-text-muted); }

/* 最近课程 */
.recent-courses { display: flex; flex-direction: column; gap: 14px; }
.recent-course {
  cursor: pointer;
  padding: 10px;
  border-radius: var(--police-radius-sm);
  transition: background 0.2s;
}
.recent-course:hover { background: var(--police-bg); }
.course-name { font-size: 13px; font-weight: 500; margin-bottom: 6px; }
.course-progress-row { display: flex; align-items: center; gap: 8px; }
.progress-text { font-size: 12px; color: var(--police-text-muted); width: 32px; text-align: right; }
.course-meta { font-size: 11px; color: var(--police-text-muted); margin-top: 4px; }

/* 本月进度 */
.month-progress { padding: 4px 0; }
.progress-hint { font-size: 12px; color: var(--police-text-muted); margin-top: 8px; }

/* 教官 - 课程安排 */
.schedule-list { display: flex; flex-direction: column; gap: 12px; }
.schedule-item {
  display: flex;
  gap: 14px;
  padding: 12px;
  background: var(--police-bg);
  border-radius: var(--police-radius-sm);
  align-items: center;
}
.schedule-day { text-align: center; min-width: 40px; }
.day-label { font-size: 13px; font-weight: 700; color: var(--police-primary); }
.day-date { font-size: 11px; color: var(--police-text-muted); }
.schedule-course { font-size: 13px; font-weight: 500; }
.schedule-meta { font-size: 12px; color: var(--police-text-muted); margin-top: 2px; }

.pending-list { display: flex; flex-direction: column; gap: 10px; }
.pending-item { font-size: 13px; color: var(--police-text-secondary); padding: 6px 0; border-bottom: 1px solid var(--police-border-light); }

.student-row { display: flex; align-items: center; margin-bottom: 8px; }
.student-name { font-size: 12px; width: 48px; color: var(--police-text-secondary); }
.student-score { font-size: 12px; color: var(--police-primary); font-weight: 600; width: 36px; text-align: right; }

/* 管理员 - 公告 */
.notice-list { display: flex; flex-direction: column; gap: 10px; }
.notice-item { display: flex; align-items: flex-start; gap: 8px; padding: 8px 0; border-bottom: 1px solid var(--police-border-light); }
.notice-title { flex: 1; font-size: 13px; color: var(--police-text-primary); line-height: 1.4; }
.notice-date { font-size: 11px; color: var(--police-text-muted); white-space: nowrap; }

.training-mini-list { display: flex; flex-direction: column; gap: 12px; }
.training-mini-item { display: flex; align-items: flex-start; gap: 10px; }
.training-mini-info {}
.training-mini-name { font-size: 13px; font-weight: 500; }
.training-mini-meta { font-size: 12px; color: var(--police-text-muted); margin-top: 2px; }

.quick-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.qa-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 8px;
  border-radius: var(--police-radius);
  background: var(--police-bg);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
  color: var(--police-text-secondary);
}
.qa-item:hover { background: var(--police-primary-light); transform: translateY(-2px); }
.qa-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}
@media (max-width: 768px) {
  .grid-2, .grid-3 {
    grid-template-columns: 1fr !important;
  }
  .welcome-bar {
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 12px !important;
  }
}
</style>
