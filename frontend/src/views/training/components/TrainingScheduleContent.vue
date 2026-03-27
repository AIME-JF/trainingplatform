<template>
  <div>
    <div class="section-header schedule-section-header" style="margin-bottom:16px">
      <div class="section-title-wrap">
        <a-space>
          <h4 style="margin:0">课程安排</h4>
          <a-radio-group :value="scheduleViewMode" size="small" @update:value="$emit('update:scheduleViewMode', $event)">
            <a-radio-button value="course">按课程展示</a-radio-button>
            <a-radio-button value="timetable">按课表展示</a-radio-button>
          </a-radio-group>
        </a-space>
        <div class="section-helper">建议先补课程计划课时。智能排课任务支持排满、排满工作日、按课时排三种方式，其中按课时排会使用计划课时。</div>
      </div>
      <a-space v-if="!isStudent">
        <permissions-tooltip
          :allowed="canScheduleEdit"
          :tips="scheduleEditTooltip"
          v-slot="{ disabled }"
        >
          <a-button size="small" :disabled="disabled" @click="$emit('open-ai-schedule')">
            智能排课
          </a-button>
        </permissions-tooltip>
        <permissions-tooltip
          :allowed="canScheduleEdit"
          :tips="scheduleEditTooltip"
          v-slot="{ disabled }"
        >
          <a-button size="small" :disabled="disabled" @click="$emit('open-course-import')">
            导入课程
          </a-button>
        </permissions-tooltip>
        <permissions-tooltip
          :allowed="canScheduleEdit"
          :tips="scheduleEditTooltip"
          v-slot="{ disabled }"
        >
          <a-button size="small" :disabled="disabled" @click="$emit('open-schedule-import')">
            导入课次
          </a-button>
        </permissions-tooltip>
        <permissions-tooltip
          :allowed="canScheduleEdit"
          :tips="scheduleEditTooltip"
          v-slot="{ disabled }"
        >
          <a-button size="small" type="primary" :disabled="disabled" @click="$emit('add-course')">
            <template #icon><PlusOutlined /></template>添加课程
          </a-button>
        </permissions-tooltip>
      </a-space>
    </div>

    <template v-if="scheduleViewMode === 'course'">
      <a-empty v-if="!trainingData.courses || trainingData.courses.length === 0" description="暂无课程安排，请点击添加" />
      <div class="course-item" v-for="(c, idx) in trainingData.courses" :key="idx">
        <div class="ci-left">
          <div class="ci-name">{{ c.name }}</div>
          <div class="ci-instructor">
            {{ c.primaryInstructorName || c.instructor || '未指定教官' }}
            <template v-if="c.assistantInstructorNames?.length">
              / 带教：{{ c.assistantInstructorNames.join('、') }}
            </template>
          </div>
          <div class="ci-time">{{ getCoursePlanLabel(c) }}</div>
          <div class="ci-time" v-if="c.schedules?.length">已排 {{ c.schedules.length }} 个课次 · {{ getScheduledHours(c) }} 课时</div>
          <div class="ci-time" v-else>暂未排课</div>
          <div class="ci-time">地点：{{ c.location || '未设置' }}</div>
        </div>
        <div class="ci-right">
          <a-tag :color="c.type === 'theory' ? 'blue' : 'green'" size="small">{{ c.type === 'theory' ? '理论' : '实操' }}</a-tag>
          <template v-if="!isStudent">
            <permissions-tooltip
              :allowed="canScheduleEdit"
              :tips="scheduleEditTooltip"
              v-slot="{ disabled }"
            >
              <a-button size="small" type="link" :disabled="disabled" @click="$emit('edit-course', idx)">编辑课程</a-button>
            </permissions-tooltip>
            <permissions-tooltip
              :allowed="canScheduleEdit"
              :tips="scheduleEditTooltip"
              v-slot="{ disabled }"
            >
              <a-button
                :ref="(el) => setCourseSessionButtonRef(el, idx)"
                size="small"
                type="link"
                :disabled="disabled"
                @click="$emit('edit-course-sessions', idx)"
              >
                编辑课次
              </a-button>
            </permissions-tooltip>
            <permissions-tooltip
              :allowed="canScheduleEdit"
              :tips="scheduleEditTooltip"
              v-slot="{ disabled }"
            >
              <a-button size="small" type="link" danger :disabled="disabled" @click="$emit('remove-course', idx)">删除</a-button>
            </permissions-tooltip>
          </template>
        </div>
      </div>
    </template>

    <a-table
      v-else
      :data-source="scheduleRows"
      :pagination="false"
      row-key="sessionId"
      size="small"
    >
      <a-table-column title="日期" data-index="date" key="date" width="120" />
      <a-table-column title="时间" data-index="timeRange" key="timeRange" width="140" />
      <a-table-column title="课程" data-index="courseName" key="courseName" />
      <a-table-column title="地点" data-index="location" key="location" width="180">
        <template #default="{ record }">
          {{ record.location || '未设置' }}
        </template>
      </a-table-column>
      <a-table-column title="教官" data-index="instructorText" key="instructorText" width="220" />
      <a-table-column title="状态" key="status" width="140">
        <template #default="{ record }">
          <a-tag :color="scheduleStatusColorMap[record.status] || 'default'">{{ scheduleStatusLabelMap[record.status] || record.status }}</a-tag>
        </template>
      </a-table-column>
      <a-table-column title="操作" key="action" width="320">
        <template #default="{ record }">
          <a-space wrap>
            <template v-if="!isStudent">
              <a-button
                size="small"
                type="link"
                :disabled="!canScheduleEdit || !record.canEdit"
                @click="$emit('edit-schedule', record)"
              >
                编辑
              </a-button>
              <a-button
                size="small"
                type="link"
                danger
                :disabled="!canScheduleEdit || !record.canDelete"
                @click="$emit('remove-schedule', record)"
              >
                删除
              </a-button>
            </template>
            <template v-if="currentSession && currentSession.sessionId === record.sessionId">
              <a-button v-if="currentSession.actionPermissions?.canStartCheckin" size="small" type="link" @click="$emit('start-session-checkin')">开始签到</a-button>
              <a-button v-if="currentSession.actionPermissions?.canEndCheckin" size="small" type="link" @click="$emit('end-session-checkin')">结束签到</a-button>
              <a-button v-if="currentSession.actionPermissions?.canStartCheckout" size="small" type="link" @click="$emit('start-session-checkout')">开始签退</a-button>
              <a-button v-if="currentSession.actionPermissions?.canEndCheckout" size="small" type="link" @click="$emit('end-session-checkout')">结束签退</a-button>
              <a-button v-if="currentSession.actionPermissions?.canSkip" size="small" type="link" danger @click="$emit('skip-current-session')">跳过</a-button>
            </template>
          </a-space>
        </template>
      </a-table-column>
    </a-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

defineProps({
  trainingData: { type: Object, required: true },
  isStudent: { type: Boolean, default: false },
  scheduleViewMode: { type: String, default: 'course' },
  canScheduleEdit: { type: Boolean, default: false },
  scheduleEditTooltip: { type: String, default: '' },
  scheduleRows: { type: Array, default: () => [] },
  currentSession: { type: Object, default: null },
  scheduleStatusColorMap: { type: Object, default: () => ({}) },
  scheduleStatusLabelMap: { type: Object, default: () => ({}) },
})

defineEmits([
  'update:scheduleViewMode',
  'open-ai-schedule',
  'open-course-import',
  'open-schedule-import',
  'add-course',
  'edit-course',
  'edit-course-sessions',
  'remove-course',
  'edit-schedule',
  'remove-schedule',
  'start-session-checkin',
  'end-session-checkin',
  'start-session-checkout',
  'end-session-checkout',
  'skip-current-session',
])

const courseSessionButtonRefs = ref({})

function normalizeCourseHours(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return 0
  }
  return Number(numeric.toFixed(1))
}

function getScheduledHours(course) {
  const total = (course?.schedules || []).reduce((sum, item) => sum + Number(item?.hours || 0), 0)
  return normalizeCourseHours(total)
}

function getCoursePlanLabel(course) {
  const plannedHours = normalizeCourseHours(course?.hours)
  if (plannedHours > 0) {
    return `计划 ${plannedHours} 课时 · 可用于AI按课时排`
  }
  return '计划课时未设置 · 如需AI按课时排请先补齐'
}

function setCourseSessionButtonRef(el, idx) {
  if (el) {
    courseSessionButtonRefs.value[idx] = el
    return
  }
  delete courseSessionButtonRefs.value[idx]
}

function getCourseSessionButtonRef(idx) {
  return courseSessionButtonRefs.value[idx] || null
}

defineExpose({
  getCourseSessionButtonRef,
})
</script>

<style scoped>
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-header h4 { margin: 0; color: #333; }
.section-title-wrap { display: flex; flex-direction: column; gap: 8px; }
.section-helper { color: #64748b; font-size: 12px; line-height: 1.6; }
.schedule-section-header { align-items: flex-start; }
.course-item { display: flex; justify-content: space-between; align-items: flex-start; padding: 10px 0; border-bottom: 1px solid #f0f0f0; gap: 16px; }
.ci-left { min-width: 0; }
.ci-name { font-size: 14px; font-weight: 500; color: #0f172a; }
.ci-instructor { font-size: 12px; color: #64748b; margin-top: 6px; }
.ci-time { margin-top: 6px; color: #475569; }
.ci-right { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; flex-shrink: 0; }
</style>
