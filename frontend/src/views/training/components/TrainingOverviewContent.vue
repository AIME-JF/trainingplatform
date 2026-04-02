<template>
  <div>
    <div class="overview-stats">
      <div class="ov-stat" v-for="s in overviewStats" :key="s.label">
        <div class="ov-num" :style="{ color: s.color }">{{ s.value }}</div>
        <div class="ov-label">{{ s.label }}</div>
      </div>
    </div>
    <div v-if="showOverviewSetupGuide" ref="setupGuideCardRef" class="setup-guide-card">
      <div class="section-header" style="margin-bottom:14px">
        <div>
          <h4 style="margin:0">开班指引</h4>
          <div class="section-helper">先准备学员、课程和课次，再发布培训班、锁定名单并开班。</div>
        </div>
        <a-button size="small" type="link" @click="$emit('go-schedule')">去课程安排</a-button>
      </div>
      <div class="setup-guide-list">
        <div
          v-for="item in setupGuideItems"
          :key="item.key"
          class="setup-guide-item"
          :class="`status-${item.status}`"
        >
          <div class="setup-guide-main">
            <div class="setup-guide-title-row">
              <span class="setup-guide-step">{{ item.index }}</span>
              <span class="setup-guide-title">{{ item.title }}</span>
            </div>
            <div class="setup-guide-desc">{{ item.description }}</div>
          </div>
          <a-tag :color="item.statusColor">{{ item.statusText }}</a-tag>
        </div>
      </div>
    </div>
    <a-divider />
    <div v-if="showOverviewCurrentCourse" ref="currentCourseSectionRef" class="course-schedule">
      <div class="section-header">
        <h4>当前课程</h4>
      </div>
      <a-empty v-if="!currentSession" description="当前没有可操作课次" />
      <div v-else class="course-item current-course-card">
        <div class="ci-left">
          <div class="ci-name">{{ currentSession.courseName }}</div>
          <div class="ci-instructor">
            主讲：{{ currentSession.primaryInstructorName || '未指定' }}
            <template v-if="currentSession.assistantInstructorNames?.length">
              / 带教：{{ currentSession.assistantInstructorNames.join('、') }}
            </template>
          </div>
          <div class="ci-time">{{ currentSession.date }} {{ currentSession.timeRange }}</div>
          <div class="ci-time">地点：{{ currentSession.location || '未设置' }} · 状态：{{ currentSessionStatusLabel }}</div>
        </div>
          <div class="ci-right">
            <a-space wrap>
              <a-button v-if="currentSession.actionPermissions?.canStartCheckout" size="small" type="primary" ghost @click="$emit('start-session-checkout')">开始签退</a-button>
              <a-button v-if="currentSession.actionPermissions?.canEndCheckout" size="small" @click="$emit('end-session-checkout')">结束签退</a-button>
              <a-button
                v-if="isEnrolled && currentSession.status === 'checkout_open'"
                size="small"
              @click="$emit('go-current-session-checkout')"
            >
              学员签退
            </a-button>
            <a-button v-if="currentSession.actionPermissions?.canSkip" size="small" danger ghost @click="$emit('skip-current-session')">跳过课程</a-button>
          </a-space>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  overviewStats: { type: Array, default: () => [] },
  showOverviewSetupGuide: { type: Boolean, default: false },
  setupGuideItems: { type: Array, default: () => [] },
  trainingData: { type: Object, required: true },
  showOverviewCurrentCourse: { type: Boolean, default: false },
  currentSession: { type: Object, default: null },
  currentSessionStatusLabel: { type: String, default: '' },
  isEnrolled: { type: Boolean, default: false },
})

defineEmits([
  'go-schedule',
  'start-session-checkout',
  'end-session-checkout',
  'go-current-session-checkout',
  'skip-current-session',
])

const setupGuideCardRef = ref(null)
const currentCourseSectionRef = ref(null)

defineExpose({
  setupGuideCardRef,
  currentCourseSectionRef,
})
</script>

<style scoped>
.overview-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
.ov-stat { text-align: center; padding: 16px; background: #f8f9ff; border-radius: 8px; }
.ov-num { font-size: 28px; font-weight: 700; }
.ov-label { font-size: 12px; color: #888; margin-top: 4px; }
.setup-guide-card { margin-bottom: 16px; padding: 16px; border: 1px solid #e2e8f0; border-radius: 12px; background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%); }
.setup-guide-list { display: flex; flex-direction: column; gap: 10px; }
.setup-guide-item { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; padding: 12px 14px; border-radius: 10px; border: 1px solid #e5e7eb; background: #fff; }
.setup-guide-item.status-done { border-color: #d1fae5; background: #f0fdf4; }
.setup-guide-item.status-progress { border-color: #fde68a; background: #fffbeb; }
.setup-guide-main { min-width: 0; }
.setup-guide-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.setup-guide-step { display: inline-flex; width: 22px; height: 22px; align-items: center; justify-content: center; border-radius: 999px; background: #dbeafe; color: #1d4ed8; font-size: 12px; font-weight: 700; }
.setup-guide-title { font-size: 14px; font-weight: 600; color: #111827; }
.setup-guide-desc { color: #64748b; font-size: 12px; line-height: 1.6; }
.training-base-info { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 16px; margin-bottom: 12px; }
.info-row { display: flex; flex-direction: column; gap: 4px; padding: 12px 14px; background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 8px; }
.info-label { font-size: 12px; color: #6b7280; }
.info-value { font-size: 14px; color: #111827; font-weight: 500; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-header h4 { margin: 0; color: #333; }
.section-helper { color: #64748b; font-size: 12px; line-height: 1.6; }
.course-schedule { margin-top: 12px; }
.current-course-card { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; background: #f8fbff; border: 1px solid #dbeafe; border-radius: 8px; padding: 16px; }
.ci-left { min-width: 0; }
.ci-name { font-size: 14px; font-weight: 500; color: #0f172a; }
.ci-instructor { font-size: 12px; color: #64748b; margin-top: 6px; }
.ci-time { margin-top: 6px; color: #475569; display: flex; flex-direction: column; gap: 4px; }
.ci-right { flex-shrink: 0; }
</style>
