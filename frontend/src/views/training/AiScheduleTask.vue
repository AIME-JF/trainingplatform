<template>
  <ai-task-tabs-layout
    v-model:active-tab="activeTab"
    title="智能排课"
    subtitle="智能排课会先异步解析规则，再确认生成课表，最后人工调整并应用到现有课表"
    tag-text="训练智能体"
    :task-list="taskList"
    :task-loading="taskLoading"
    :active-task-id="activeTask?.id || null"
    :status-labels="statusLabels"
    :status-colors="statusColors"
    :status-label-resolver="resolveTaskStatusLabel"
    :status-color-resolver="resolveTaskStatusColor"
    @refresh-tasks="loadTasks"
    @select-task="selectTask"
  >
    <template #header-extra>
      <a-button shape="circle" class="tour-trigger-button" title="查看页面引导" @click="openScheduleTour">
        <template #icon><QuestionCircleOutlined /></template>
      </a-button>
    </template>

    <template #create>
      <div class="create-form-wrap">
        <a-tabs v-model:activeKey="createMode" size="large" class="create-mode-tabs">
          <a-tab-pane key="smart" tab="智能排课">
            <a-form layout="vertical">
              <div v-if="!hasPresetTrainingId" data-tour-id="schedule-training">
                <a-form-item label="培训班" required>
                  <a-select v-model:value="taskForm.trainingId" :options="trainingOptions" placeholder="请选择培训班" />
                </a-form-item>
              </div>
              <a-alert
                v-else
                type="info"
                show-icon
                style="margin-bottom:16px"
                :message="`当前培训班：${selectedTraining?.name || '未命名培训班'}`"
                description="智能排课会直接基于当前培训班的培训周期、课程清单、考试安排和排课规则生成建议。"
              />
              <div data-tour-id="schedule-natural-language">
                <a-form-item label="排课要求" required>
                  <a-textarea
                    v-model:value="taskForm.naturalLanguagePrompt"
                    :rows="7"
                    placeholder="例：本周按工作日排满，上午 08:30-12:30，下午 14:00-17:30；一个课时 40 分钟，课间休息 10 分钟，一节课最多 3 个课时，尽量平分，避开考试。"
                  />
                  <div class="field-help">这里只需要输入排课要求。提交后会创建异步任务，后台先解析规则，完成后再到任务页确认。</div>
                </a-form-item>
              </div>
              <a-form-item label="是否覆盖当前课表">
                <a-switch v-model:checked="taskForm.overwriteExistingSchedule" />
                <div class="field-help">
                  开启后会按新课表重新生成，最终确认应用时还会再次提示是否覆盖；关闭后会保留当前已有课次。
                </div>
              </a-form-item>
              <div data-tour-id="schedule-notes">
                <a-form-item label="补充说明">
                  <a-textarea v-model:value="taskForm.notes" :rows="3" />
                </a-form-item>
              </div>
              <div data-tour-id="schedule-create-button">
                <a-button type="primary" block :loading="creating" @click="handleCreateTask">
                  创建智能排课任务
                </a-button>
              </div>
            </a-form>
          </a-tab-pane>

          <a-tab-pane key="manual" tab="手动排课">
            <schedule-structured-task-form
              :form-state="taskForm"
              :training-options="trainingOptions"
              :loading="creating"
              submit-text="创建手动排课任务"
              tour-prefix="schedule"
              @submit="handleCreateTask"
            />
          </a-tab-pane>
        </a-tabs>
      </div>
    </template>

    <template #task-description="{ item }">
      {{ item.trainingName || '未命名培训班' }} · {{ item.itemCount ? `${item.itemCount} 个课次` : resolveTaskStatusLabel(item) }}
    </template>

    <template #task-actions="{ item }">
      <a-popconfirm
        v-if="item.canDelete"
        title="确定删除这个任务吗？"
        ok-text="删除"
        cancel-text="取消"
        @confirm="handleDeleteTask(item)"
      >
        <a-button
          type="link"
          danger
          size="small"
          :loading="deletingTaskId === item.id"
          @click.stop
        >
          删除
        </a-button>
      </a-popconfirm>
    </template>

    <template #detail>
      <template v-if="activeTask">
        <div data-tour-id="schedule-detail-header" class="detail-header">
          <div>
            <div class="detail-title">{{ activeTask.taskName }}</div>
            <div class="detail-sub">{{ activeTask.trainingName || '未命名培训班' }} · {{ resolveTaskStatusLabel(activeTask) }}</div>
          </div>
          <a-space>
            <a-button @click="loadTaskDetail(activeTask.id)">刷新详情</a-button>
            <a-button v-if="isScheduleConfirmationStage(activeTask)" @click="openPlanCalendar">周历预览</a-button>
            <a-button v-if="isScheduleConfirmationStage(activeTask)" :loading="saving" @click="handleSaveTask">保存修改</a-button>
            <a-button v-if="isScheduleConfirmationStage(activeTask)" type="primary" :loading="confirming" @click="handleConfirmTask">
              确认应用
            </a-button>
          </a-space>
        </div>

        <ai-task-timeline
          mode="schedule"
          :status="activeTask.status"
          :stage="activeTask.taskStage"
          :created-at="activeTask.createdAt"
          :completed-at="activeTask.completedAt"
          :confirmed-at="activeTask.confirmedAt"
        />

        <div class="detail-section" v-if="isProcessingStage(activeTask)">
          <a-alert
            type="info"
            show-icon
            :message="activeTask.taskStage === 'schedule_generation' ? '后台正在生成课表，请稍候' : '后台正在解析规则，请稍候'"
            description="当前页面会自动刷新任务详情。"
          />
        </div>

        <div class="detail-section" v-else-if="isRuleConfirmationStage(activeTask)">
          <a-alert
            type="success"
            show-icon
            message="规则解析已完成，请先确认结构化规则"
            description="请直接在当前任务详情里核对并修改结构化规则；确认后任务会自动进入课表生成阶段。"
          />
        </div>

        <div data-tour-id="schedule-parse-section" class="detail-section" v-if="showPrimaryParseSection">
          <div class="detail-section-title">需求解析结果</div>
          <a-alert v-if="activeTask.parseSummary" type="success" :message="activeTask.parseSummary" show-icon style="margin-bottom:12px" />
          <a-descriptions v-if="activeTask.understoodItems?.length" :column="1" size="small" bordered style="margin-bottom:12px">
            <a-descriptions-item label="系统理解了什么">
              <div class="preview-list">
                <div v-for="(item, index) in activeTask.understoodItems" :key="`task-understood-${index}`">{{ item }}</div>
              </div>
            </a-descriptions-item>
          </a-descriptions>
          <div v-if="activeTask.parseWarnings?.length" class="conflict-list">
            <a-alert v-for="(item, index) in activeTask.parseWarnings" :key="index" type="warning" :message="item" show-icon />
          </div>
        </div>

        <div data-tour-id="schedule-rule-confirm-section" class="detail-section" v-if="isRuleConfirmationStage(activeTask)">
          <div class="detail-section-title">确认结构化规则</div>
          <schedule-structured-task-form
            :form-state="ruleConfirmForm"
            :training-options="trainingOptions"
            :disable-training-select="true"
            :loading="ruleConfirming"
            submit-text="确认规则并生成课表"
            tour-prefix="schedule-rule-confirm"
            @submit="handleConfirmRules"
          >
            <template #top>
              <a-alert
                type="info"
                show-icon
                style="margin-bottom:16px"
                message="当前规则来自需求解析结果"
                description="你可以直接修改结构化字段。确认后仍停留在任务列表，等待后台继续生成课表。"
              />
            </template>
          </schedule-structured-task-form>
        </div>

        <div class="detail-section" v-if="activeTask.explanation && isScheduleConfirmationStage(activeTask)">
          <div class="detail-section-title">方案说明</div>
          <a-alert type="info" :message="activeTask.explanation" show-icon />
        </div>

        <div data-tour-id="schedule-conflict-section" class="detail-section" v-if="isScheduleConfirmationStage(activeTask)">
          <div class="detail-section-title">冲突清单</div>
          <a-empty v-if="!activeTask.conflicts?.length" description="当前主方案未发现冲突" />
          <div v-else class="conflict-list">
            <a-alert
              v-for="(item, index) in activeTask.conflicts"
              :key="`${item.sessionId || item.courseKey || index}`"
              :type="item.severity === 'error' ? 'error' : 'warning'"
              :message="item.message"
              :description="item.suggestion"
              show-icon
            />
          </div>
        </div>

        <div data-tour-id="schedule-main-plan" class="detail-section" v-if="activeTask.mainPlan">
          <div class="detail-section-title">主方案</div>
          <div class="plan-meta">
            <a-tag color="blue">{{ activeTask.mainPlan.metrics?.totalSessions || 0 }} 个课次</a-tag>
            <a-tag color="green">{{ activeTask.mainPlan.metrics?.totalHours || 0 }} 课时</a-tag>
            <a-tag color="orange">理论 {{ activeTask.mainPlan.metrics?.theoryHours || 0 }}</a-tag>
            <a-tag color="purple">实操 {{ activeTask.mainPlan.metrics?.practiceHours || 0 }}</a-tag>
          </div>

          <div class="course-grid">
            <div v-for="(course, courseIndex) in activeTask.mainPlan.courses || []" :key="course.courseKey || courseIndex" class="course-card">
              <div class="course-head">
                <div>
                  <div class="course-title">{{ course.name }}</div>
                  <div class="course-sub">{{ typeLabels[course.type] || course.type }} · {{ course.instructor || '未指定教官' }}</div>
                  <div class="course-sub">{{ getCoursePlanHint(course) }}</div>
                </div>
                <a-tag :color="getCoursePlanTagColor(course)">{{ getCoursePlanTagText(course) }}</a-tag>
              </div>
              <div class="schedule-list">
                <div v-for="(session, scheduleIndex) in course.schedules || []" :key="session.sessionId || scheduleIndex" class="schedule-row">
                  <div>
                    <div>{{ session.date }} {{ session.timeRange }}</div>
                    <div class="schedule-sub">{{ session.location || '未指定地点' }} · {{ getSessionDisplayHours(session) }} 课时</div>
                  </div>
                  <a-space v-if="activeTask.status === 'completed'" size="small">
                    <a-button type="link" size="small" @click="openEditSession(courseIndex, scheduleIndex)">
                      编辑
                    </a-button>
                    <a-button type="link" danger size="small" @click="removeTaskSession(courseIndex, scheduleIndex)">
                      删除
                    </a-button>
                  </a-space>
                </div>
                <a-empty v-if="!(course.schedules || []).length" description="暂无课次" />
              </div>
            </div>
          </div>
        </div>

        <div data-tour-id="schedule-alternative-plan" class="detail-section" v-if="activeTask.alternativePlans?.length">
          <div class="detail-section-title">备选方案</div>
          <div class="alternative-grid">
            <div v-for="plan in activeTask.alternativePlans" :key="plan.planId" class="alternative-card">
              <div class="alternative-title">{{ plan.title }}</div>
              <div class="alternative-sub">{{ plan.summary }}</div>
              <div class="alternative-metrics">{{ plan.metrics?.totalSessions || 0 }} 个课次 · {{ plan.metrics?.totalHours || 0 }} 课时</div>
              <a-button size="small" @click="adoptAlternativePlan(plan)">设为主方案</a-button>
            </div>
          </div>
        </div>

        <div class="detail-section detail-more-toggle" v-if="hasHiddenDetailContent">
          <a-button type="link" class="detail-more-button" @click="detailExtrasExpanded = !detailExtrasExpanded">
            {{ detailExtrasExpanded ? '收起详细规则与任务信息' : '展开详细规则与任务信息' }}
          </a-button>
        </div>

        <div v-if="detailExtrasExpanded">
          <div v-if="activeTask.requestPayload" data-tour-id="schedule-request-section" class="detail-section">
            <div class="detail-section-title">任务请求</div>
            <a-descriptions :column="2" size="small" bordered>
              <a-descriptions-item label="排课要求" :span="2">
                {{ activeTask.requestPayload.naturalLanguagePrompt || '未填写' }}
              </a-descriptions-item>
              <a-descriptions-item label="排课范围">{{ scopeLabels[activeTask.requestPayload.scopeType] || activeTask.requestPayload.scopeType }}</a-descriptions-item>
              <a-descriptions-item label="排课目标">{{ goalLabels[activeTask.requestPayload.goal] || activeTask.requestPayload.goal }}</a-descriptions-item>
              <a-descriptions-item label="排课方式">{{ planningModeLabels[resolvePlanningMode(activeTask.requestPayload.planningMode)] || resolvePlanningMode(activeTask.requestPayload.planningMode) }}</a-descriptions-item>
              <a-descriptions-item label="单日最大课时">{{ activeTask.requestPayload.constraintPayload?.dailyMaxHours || 0 }}</a-descriptions-item>
              <a-descriptions-item label="避开考试日">{{ activeTask.requestPayload.constraintPayload?.avoidExamDays ? '是' : '否' }}</a-descriptions-item>
              <a-descriptions-item label="覆盖当前课表">{{ activeTask.requestPayload.overwriteExistingSchedule ? '是' : '否' }}</a-descriptions-item>
              <a-descriptions-item
                v-if="activeTask.requestPayload.scopeType === 'current_week' && activeTask.requestPayload.scopeStartDate"
                label="指定周"
              >
                {{ activeTask.requestPayload.scopeStartDate }}
              </a-descriptions-item>
              <a-descriptions-item label="培训班默认规则" :span="2">
                {{ formatRuleOverrideSummary(activeTask.trainingRuleConfig) }}
              </a-descriptions-item>
              <a-descriptions-item label="规则覆盖" :span="2">
                {{ formatRuleOverrideSummary(activeTask.requestPayload.scheduleRuleOverride) }}
              </a-descriptions-item>
              <a-descriptions-item label="全局禁排" :span="2">
                {{ formatSlotTextSummary(formatSlotLines(activeTask.requestPayload.constraintPayload?.blockedTimeSlots || [])) }}
              </a-descriptions-item>
              <a-descriptions-item label="教官不可用" :span="2">
                {{ formatSlotTextSummary(formatSlotLines(activeTask.requestPayload.constraintPayload?.instructorUnavailableSlots || [], { withLabel: true }), { withLabel: true }) }}
              </a-descriptions-item>
              <a-descriptions-item label="场地不可用" :span="2">
                {{ formatSlotTextSummary(formatSlotLines(activeTask.requestPayload.constraintPayload?.locationUnavailableSlots || [], { withLabel: true }), { withLabel: true }) }}
              </a-descriptions-item>
              <a-descriptions-item label="课程类型时段偏好" :span="2">
                {{ formatCourseTypePreferenceSummary(formatCourseTypePreferencesText(activeTask.requestPayload.constraintPayload?.courseTypeTimePreferences || [])) }}
              </a-descriptions-item>
              <a-descriptions-item label="考前强化偏好" :span="2">
                {{ formatExamWeekFocusSummary(formatExamWeekFocusText(activeTask.requestPayload.constraintPayload?.examWeekFocus)) }}
              </a-descriptions-item>
            </a-descriptions>
          </div>

          <div data-tour-id="schedule-parse-section" class="detail-section" v-if="showDetailParseSection">
            <div class="detail-section-title">需求解析结果</div>
            <a-alert v-if="activeTask.parseSummary" type="success" :message="activeTask.parseSummary" show-icon style="margin-bottom:12px" />
            <a-descriptions v-if="activeTask.understoodItems?.length" :column="1" size="small" bordered style="margin-bottom:12px">
              <a-descriptions-item label="系统理解了什么">
                <div class="preview-list">
                  <div v-for="(item, index) in activeTask.understoodItems" :key="`task-understood-detail-${index}`">{{ item }}</div>
                </div>
              </a-descriptions-item>
            </a-descriptions>
            <div v-if="activeTask.parseWarnings?.length" class="conflict-list">
              <a-alert v-for="(item, index) in activeTask.parseWarnings" :key="`detail-warning-${index}`" type="warning" :message="item" show-icon />
            </div>
          </div>
        </div>
      </template>
      <a-empty v-else description="请选择任务查看详情" />
    </template>
  </ai-task-tabs-layout>

  <a-modal v-model:open="sessionModalOpen" title="编辑课次" ok-text="保存" cancel-text="取消" @ok="handleSessionEdit">
    <a-form layout="vertical">
      <a-form-item label="日期">
        <a-input v-model:value="sessionForm.date" placeholder="YYYY-MM-DD" />
      </a-form-item>
      <a-form-item label="时间段">
        <a-input v-model:value="sessionForm.timeRange" placeholder="09:00~12:00" />
      </a-form-item>
      <a-form-item label="地点">
        <a-input v-model:value="sessionForm.location" placeholder="上课地点" />
      </a-form-item>
    </a-form>
  </a-modal>

  <a-modal v-model:open="planCalendarOpen" title="周历课表预览" width="1100px">
    <a-empty v-if="!planCalendarWeeks.length" description="当前任务暂无可预览课表" />
    <a-tabs v-else v-model:activeKey="planCalendarActiveWeek">
      <a-tab-pane v-for="week in planCalendarWeeks" :key="week.key" :tab="week.label">
        <div class="calendar-grid">
          <div v-for="day in week.days" :key="day.date" class="calendar-cell">
            <div class="calendar-date">{{ day.label }}</div>
            <div class="calendar-session-list">
              <div v-for="session in day.sessions" :key="session.id" class="calendar-session">
                <div class="calendar-session-title">{{ session.courseName }}</div>
                <div class="calendar-session-sub">{{ session.timeRange }} · {{ session.location }}</div>
                <div class="calendar-session-sub">{{ session.instructor }} · {{ session.hours }} 课时</div>
              </div>
              <a-empty v-if="!day.sessions.length" :image="false" description="无课次" />
            </div>
          </div>
        </div>
      </a-tab-pane>
    </a-tabs>
    <template #footer>
      <a-space>
        <a-button @click="planCalendarOpen = false">关闭</a-button>
        <a-button v-if="isScheduleConfirmationStage(activeTask)" type="primary" :loading="confirming" @click="handleConfirmTask">
          确认应用该课表
        </a-button>
      </a-space>
    </template>
  </a-modal>

  <a-tour
    v-model:open="scheduleTourOpen"
    v-model:current="scheduleTourCurrent"
    :steps="scheduleTourSteps"
    @close="handleScheduleTourClose"
  />
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Modal, message } from 'ant-design-vue'
import { QuestionCircleOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import {
  confirmAiScheduleTask,
  confirmAiScheduleTaskRules,
  createAiScheduleTask,
  deleteAiScheduleTask,
  getAiScheduleTaskDetail,
  getAiScheduleTasks,
  updateAiScheduleTaskResult,
} from '@/api/ai'
import { getTraining, getTrainings } from '@/api/training'
import AiTaskTabsLayout from '@/views/exam/components/AiTaskTabsLayout.vue'
import AiTaskTimeline from '@/views/exam/components/AiTaskTimeline.vue'
import ScheduleStructuredTaskForm from '@/views/training/components/ScheduleStructuredTaskForm.vue'

const route = useRoute()
const router = useRouter()
const activeTab = ref('create')
const createMode = ref('smart')
const taskList = ref([])
const activeTask = ref(null)
const taskLoading = ref(false)
const creating = ref(false)
const saving = ref(false)
const confirming = ref(false)
const trainings = ref([])
const scheduleTourOpen = ref(false)
const scheduleTourCurrent = ref(0)
const sessionModalOpen = ref(false)
const planCalendarOpen = ref(false)
const planCalendarActiveWeek = ref('')
const detailExtrasExpanded = ref(false)
const detailExtrasTaskId = ref(null)
const deletingTaskId = ref(null)
const ruleConfirming = ref(false)
const ruleConfirmTaskId = ref(null)
const sessionForm = reactive({ courseIndex: -1, scheduleIndex: -1, date: '', timeRange: '', location: '' })
let taskPollTimer = 0

const statusLabels = { pending: '待处理', processing: '处理中', completed: '已完成', confirmed: '已确认', failed: '处理失败' }
const statusColors = { pending: 'default', processing: 'processing', completed: 'blue', confirmed: 'green', failed: 'red' }
const scopeLabels = { all: '全班次', current_week: '指定周', unscheduled: '仅未排课课次' }
const goalLabels = { balanced: '均衡排课', practice_first: '优先实战', theory_first: '优先理论', exam_intensive: '考前强化' }
const planningModeLabels = {
  auto: '按课程计划自动判断',
  fill_all_days: '排满',
  fill_workdays: '排满工作日',
  by_hours: '按课时排',
}
const typeLabels = { theory: '理论课', practice: '实操课' }
const weekdayLabels = { 1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六', 7: '周日' }

function createStructuredTaskFormState(trainingId) {
  return {
    taskName: '',
    trainingId,
    naturalLanguagePrompt: '',
    scopeType: 'all',
    scopeStartDate: '',
    goal: 'balanced',
    planningMode: 'fill_workdays',
    overwriteExistingSchedule: false,
    dailyMaxHours: 6,
    lessonUnitMinutes: 40,
    breakMinutes: 10,
    maxUnitsPerSession: 3,
    teachingWindowsText: '',
    avoidExamDays: true,
    fixedCourseKeysText: '',
    blockedTimeSlotsText: '',
    courseTypePreferencesText: '',
    instructorUnavailableSlotsText: '',
    locationUnavailableSlotsText: '',
    examWeekFocusText: '',
    notes: '',
  }
}

const taskForm = reactive(createStructuredTaskFormState(route.params.id ? Number(route.params.id) : undefined))
const ruleConfirmForm = reactive(createStructuredTaskFormState(route.params.id ? Number(route.params.id) : undefined))

const trainingOptions = computed(() => (trainings.value || []).map(item => ({
  label: item.name,
  value: item.id,
})))
const hasPresetTrainingId = computed(() => Boolean(route.params.id))

function getTrainingById(trainingId) {
  return (trainings.value || []).find(item => item.id === trainingId) || null
}

const selectedTraining = computed(() => getTrainingById(taskForm.trainingId))
const planCalendarWeeks = computed(() => buildPlanCalendarWeeks(activeTask.value?.mainPlan))

function cloneDeep(value) {
  return JSON.parse(JSON.stringify(value))
}

function parseSlotLines(text, { withLabel = false } = {}) {
  return String(text || '')
    .split(/\r?\n/)
    .map(item => item.trim())
    .filter(Boolean)
    .map((item) => {
      const parts = item.split('|').map(part => part.trim()).filter(Boolean)
      if (withLabel) {
        const [label = '', date = '', timeRange = ''] = parts
        return { label, date, timeRange }
      }
      const [date = '', timeRange = '', label = ''] = parts
      return { date, timeRange, label }
    })
    .filter(item => item.date && item.timeRange)
}

function formatSlotLines(slots, { withLabel = false } = {}) {
  return (slots || [])
    .map((item) => {
      if (withLabel) {
        return `${item.label || ''}|${item.date || ''}|${item.timeRange || item.time_range || ''}`.replace(/^\|/, '')
      }
      const parts = [item.date || '', item.timeRange || item.time_range || '']
      if (item.label) parts.push(item.label)
      return parts.join('|')
    })
    .join('\n')
}

function parseCourseTypePreferencesText(text) {
  return String(text || '')
    .split(/\r?\n/)
    .map(item => item.trim())
    .filter(Boolean)
    .map((item) => {
      const [courseType = '', timeRange = '', weekdaysText = '', priority = 'prefer'] = item.split('|').map(part => part.trim())
      const separator = timeRange.includes('-') ? '-' : '~'
      const [startTime = '', endTime = ''] = timeRange.split(separator).map(part => part.trim())
      const normalizedCourseType = /实/.test(courseType) ? 'practice' : /理/.test(courseType) ? 'theory' : courseType
      const weekdays = weekdaysText
        .split(/[、,，]/)
        .map(part => Number(part.trim()))
        .filter(part => Number.isInteger(part) && part >= 1 && part <= 7)
      return {
        courseType: normalizedCourseType,
        startTime,
        endTime,
        weekdays,
        priority: priority === 'only' ? 'only' : 'prefer',
      }
    })
    .filter(item => item.courseType && item.startTime && item.endTime)
}

function formatCourseTypePreferencesText(preferences) {
  return (preferences || [])
    .map(item => {
      const weekdays = (item.weekdays || []).join(',')
      return `${item.courseType || ''}|${item.startTime || item.start_time || ''}~${item.endTime || item.end_time || ''}|${weekdays}|${item.priority || 'prefer'}`
    })
    .join('\n')
}

function parseExamWeekFocusText(text) {
  const lines = String(text || '')
    .split(/\r?\n/)
    .map(item => item.trim())
    .filter(Boolean)
  if (!lines.length) {
    return undefined
  }
  const [daysText = '7', courseType = '', keywordsText = ''] = lines[0].split('|').map(part => part.trim())
  const courseKeywords = keywordsText
    .split(/[、,，]/)
    .map(item => item.trim())
    .filter(Boolean)
  return {
    daysBeforeExam: Math.max(1, Number(daysText || 7) || 7),
    courseType: /实/.test(courseType) ? 'practice' : /理/.test(courseType) ? 'theory' : (courseType || undefined),
    courseKeywords,
  }
}

function formatExamWeekFocusText(focus) {
  if (!focus) {
    return ''
  }
  return `${focus.daysBeforeExam || 7}|${focus.courseType || ''}|${(focus.courseKeywords || []).join(',')}`
}

function parseTeachingWindowsText(text) {
  return String(text || '')
    .split(/\r?\n/)
    .map(item => item.trim())
    .filter(Boolean)
    .map((item) => {
      const [label, rangeText] = item.includes('|') ? item.split('|') : ['', item]
      const separator = rangeText.includes('-') ? '-' : '~'
      const [startTime = '', endTime = ''] = rangeText.split(separator).map(part => part.trim())
      return {
        label: String(label || '').trim(),
        startTime,
        endTime,
      }
    })
    .filter(item => item.startTime && item.endTime)
}

function formatTeachingWindowsText(windows) {
  return (windows || [])
    .map(item => `${item.label ? `${item.label}|` : ''}${item.startTime || item.start_time}-${item.endTime || item.end_time}`)
    .join('\n')
}

function normalizeCourseHours(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return 0
  }
  return Number(numeric.toFixed(1))
}

function getEffectiveRuleConfig(config) {
  const source = config || activeTask.value?.effectiveRuleConfig || activeTask.value?.requestPayload?.scheduleRuleOverride || {}
  return {
    lessonUnitMinutes: Math.max(1, Number(source.lessonUnitMinutes || source.lesson_unit_minutes || 40)),
    breakMinutes: Math.max(0, Number(source.breakMinutes || source.break_minutes || 10)),
  }
}

function calculateSessionUnitsFromTimeRange(timeRange, ruleConfig) {
  if (!timeRange || !String(timeRange).includes('~')) {
    return 0
  }
  const [startText = '', endText = ''] = String(timeRange).split('~')
  const start = dayjs(`2000-01-01 ${startText.trim()}`)
  const end = dayjs(`2000-01-01 ${endText.trim()}`)
  const diffMinutes = end.diff(start, 'minute')
  if (diffMinutes <= 0) {
    return 0
  }
  const effectiveRule = getEffectiveRuleConfig(ruleConfig)
  if (diffMinutes <= effectiveRule.lessonUnitMinutes || effectiveRule.breakMinutes <= 0) {
    return normalizeCourseHours(diffMinutes / effectiveRule.lessonUnitMinutes)
  }
  const exactUnits = (diffMinutes + effectiveRule.breakMinutes) / (effectiveRule.lessonUnitMinutes + effectiveRule.breakMinutes)
  const roundedUnits = Math.round(exactUnits)
  if (Math.abs(exactUnits - roundedUnits) <= 0.05) {
    return normalizeCourseHours(roundedUnits)
  }
  return normalizeCourseHours(exactUnits)
}

function getSessionDisplayHours(session) {
  return normalizeCourseHours(session?.hours) || calculateSessionUnitsFromTimeRange(session?.timeRange)
}

function buildLocalPlanMetrics(plan) {
  const metrics = {
    totalSessions: 0,
    totalHours: 0,
    theoryHours: 0,
    practiceHours: 0,
  }
  for (const course of plan?.courses || []) {
    const courseType = course?.type || 'theory'
    for (const session of course?.schedules || []) {
      const hours = getSessionDisplayHours(session)
      metrics.totalSessions += 1
      metrics.totalHours += hours
      if (courseType === 'practice') {
        metrics.practiceHours += hours
      } else {
        metrics.theoryHours += hours
      }
    }
  }
  metrics.totalHours = normalizeCourseHours(metrics.totalHours)
  metrics.theoryHours = normalizeCourseHours(metrics.theoryHours)
  metrics.practiceHours = normalizeCourseHours(metrics.practiceHours)
  return metrics
}

function syncMainPlanMetrics() {
  if (!activeTask.value?.mainPlan) {
    return
  }
  activeTask.value.mainPlan.metrics = buildLocalPlanMetrics(activeTask.value.mainPlan)
}

function resolvePlanningMode(value) {
  const normalized = String(value || '').trim()
  if (Object.prototype.hasOwnProperty.call(planningModeLabels, normalized)) {
    return normalized
  }
  return 'auto'
}

const activePlanningMode = computed(() => resolvePlanningMode(activeTask.value?.requestPayload?.planningMode))

function resetStructuredTaskForm(formState, trainingId = formState.trainingId) {
  Object.assign(formState, createStructuredTaskFormState(trainingId))
}

function parseFixedCourseKeys(formState) {
  return String(formState.fixedCourseKeysText || '')
    .split(/\r?\n|,|，|;|；/)
    .map(item => item.trim())
    .filter(Boolean)
}

function applyTrainingRuleDefaults(formState, ruleConfig) {
  const config = ruleConfig || {}
  formState.lessonUnitMinutes = Number(config.lessonUnitMinutes || config.lesson_unit_minutes || 40)
  formState.breakMinutes = Number(config.breakMinutes || config.break_minutes || 10)
  formState.maxUnitsPerSession = Number(config.maxUnitsPerSession || config.max_units_per_session || 3)
  formState.dailyMaxHours = Number(config.dailyMaxUnits || config.daily_max_units || 6)
  formState.planningMode = resolvePlanningMode(config.preferredPlanningMode || config.preferred_planning_mode || formState.planningMode)
  formState.teachingWindowsText = formatTeachingWindowsText(config.teachingWindows || config.teaching_windows || [])
  formState.blockedTimeSlotsText = ''
  formState.courseTypePreferencesText = ''
  formState.instructorUnavailableSlotsText = ''
  formState.locationUnavailableSlotsText = ''
  formState.examWeekFocusText = ''
}

function applyStructuredTaskPayload(formState, payload, { preserveTaskName = false } = {}) {
  const request = payload || {}
  formState.trainingId = request.trainingId || request.training_id || formState.trainingId
  formState.naturalLanguagePrompt = request.naturalLanguagePrompt || request.natural_language_prompt || ''
  if (!preserveTaskName) {
    formState.taskName = request.taskName || request.task_name || buildSmartTaskName(formState.trainingId)
  }
  formState.scopeType = request.scopeType || request.scope_type || 'all'
  formState.scopeStartDate = request.scopeStartDate || request.scope_start_date || ''
  formState.goal = request.goal || 'balanced'
  formState.planningMode = resolvePlanningMode(request.planningMode || request.planning_mode || 'fill_workdays')
  formState.overwriteExistingSchedule = Boolean(request.overwriteExistingSchedule || request.overwrite_existing_schedule)
  const constraintPayload = request.constraintPayload || request.constraint_payload || {}
  formState.dailyMaxHours = Number(constraintPayload.dailyMaxHours || constraintPayload.daily_max_hours || formState.dailyMaxHours || 6)
  formState.avoidExamDays = constraintPayload.avoidExamDays !== false && constraintPayload.avoid_exam_days !== false
  formState.fixedCourseKeysText = (constraintPayload.fixedCourseKeys || constraintPayload.fixed_course_keys || []).join('\n')
  formState.blockedTimeSlotsText = formatSlotLines(constraintPayload.blockedTimeSlots || constraintPayload.blocked_time_slots || [])
  formState.courseTypePreferencesText = formatCourseTypePreferencesText(
    constraintPayload.courseTypeTimePreferences || constraintPayload.course_type_time_preferences || [],
  )
  formState.instructorUnavailableSlotsText = formatSlotLines(
    constraintPayload.instructorUnavailableSlots || constraintPayload.instructor_unavailable_slots || [],
    { withLabel: true },
  )
  formState.locationUnavailableSlotsText = formatSlotLines(
    constraintPayload.locationUnavailableSlots || constraintPayload.location_unavailable_slots || [],
    { withLabel: true },
  )
  formState.examWeekFocusText = formatExamWeekFocusText(
    constraintPayload.examWeekFocus || constraintPayload.exam_week_focus,
  )
  const ruleOverride = request.scheduleRuleOverride || request.schedule_rule_override || {}
  formState.lessonUnitMinutes = Number(ruleOverride.lessonUnitMinutes || ruleOverride.lesson_unit_minutes || formState.lessonUnitMinutes || 40)
  formState.breakMinutes = Number(ruleOverride.breakMinutes || ruleOverride.break_minutes || formState.breakMinutes || 10)
  formState.maxUnitsPerSession = Number(ruleOverride.maxUnitsPerSession || ruleOverride.max_units_per_session || formState.maxUnitsPerSession || 3)
  formState.teachingWindowsText = formatTeachingWindowsText(ruleOverride.teachingWindows || ruleOverride.teaching_windows || [])
  formState.notes = request.notes || ''
}

function formatRuleOverrideSummary(ruleOverride) {
  const config = ruleOverride || {}
  const lessonUnitMinutes = config.lessonUnitMinutes || config.lesson_unit_minutes
  const breakMinutes = config.breakMinutes || config.break_minutes
  const maxUnitsPerSession = config.maxUnitsPerSession || config.max_units_per_session
  const windows = formatTeachingWindowsText(config.teachingWindows || config.teaching_windows || [])
  const parts = []
  if (lessonUnitMinutes) parts.push(`${lessonUnitMinutes} 分钟/课时`)
  if (breakMinutes !== undefined && breakMinutes !== null) parts.push(`课间 ${breakMinutes} 分钟`)
  if (maxUnitsPerSession) parts.push(`单节最多 ${maxUnitsPerSession} 课时`)
  if (windows) parts.push(windows.replace(/\n/g, '；'))
  return parts.join('，') || '未覆盖培训班默认规则'
}

function formatSlotTextSummary(text, { withLabel = false } = {}) {
  const slots = parseSlotLines(text, { withLabel })
  if (!slots.length) {
    return '无'
  }
  return slots
    .slice(0, 3)
    .map(item => withLabel
      ? `${item.label || '未命名'} ${item.date} ${item.timeRange}`
      : `${item.date} ${item.timeRange}${item.label ? `（${item.label}）` : ''}`
    )
    .join('；')
}

function formatCourseTypePreferenceSummary(text) {
  const preferences = parseCourseTypePreferencesText(text)
  if (!preferences.length) {
    return '无'
  }
  return preferences
    .slice(0, 3)
    .map(item => {
      const courseType = item.courseType === 'practice' ? '实操课' : '理论课'
      const weekdays = item.weekdays.length ? `（${item.weekdays.map(day => weekdayLabels[day] || `周${day}`).join('、')}）` : ''
      const priority = item.priority === 'only' ? '仅允许' : '优先'
      return `${courseType}${priority}${item.startTime}~${item.endTime}${weekdays}`
    })
    .join('；')
}

function formatExamWeekFocusSummary(text) {
  const focus = parseExamWeekFocusText(text)
  if (!focus) {
    return '无'
  }
  const courseType = focus.courseType === 'practice' ? '实操课' : focus.courseType === 'theory' ? '理论课' : '未指定类型'
  const keywords = focus.courseKeywords.length ? `，关键词 ${focus.courseKeywords.join('、')}` : ''
  return `考前 ${focus.daysBeforeExam} 天优先强化 ${courseType}${keywords}`
}

function buildSmartTaskName(trainingId = taskForm.trainingId) {
  const trainingName = getTrainingById(trainingId)?.name || '培训班'
  return `${trainingName}智能排课-${dayjs().format('MMDDHHmm')}`
}

function resolveTaskStatusLabel(task) {
  if (!task) {
    return '未知状态'
  }
  if (task.status === 'failed') {
    return '处理失败'
  }
  if (task.status === 'confirmed') {
    return '已确认'
  }
  if (task.taskStage === 'rule_parsing') {
    return task.status === 'processing' ? '解析规则中' : '待解析规则'
  }
  if (task.taskStage === 'rule_confirmation') {
    return '待确认规则'
  }
  if (task.taskStage === 'schedule_generation') {
    return task.status === 'processing' ? '生成课表中' : '待生成课表'
  }
  if (task.taskStage === 'schedule_confirmation') {
    return '待确认课表'
  }
  return statusLabels[task.status] || task.status
}

function resolveTaskStatusColor(task) {
  if (!task) {
    return 'default'
  }
  if (task.status === 'failed') {
    return 'red'
  }
  if (task.status === 'confirmed') {
    return 'green'
  }
  if (task.taskStage === 'rule_confirmation') {
    return 'gold'
  }
  if (task.taskStage === 'schedule_confirmation') {
    return 'blue'
  }
  if (task.status === 'processing') {
    return 'processing'
  }
  return statusColors[task.status] || 'default'
}

function isRuleConfirmationStage(task) {
  return task?.status === 'completed' && task?.taskStage === 'rule_confirmation'
}

function isScheduleConfirmationStage(task) {
  return task?.status === 'completed' && task?.taskStage === 'schedule_confirmation'
}

function isProcessingStage(task) {
  return Boolean(task && ['pending', 'processing'].includes(task.status) && ['rule_parsing', 'schedule_generation'].includes(task.taskStage))
}

const hasParseContent = computed(() => Boolean(
  activeTask.value?.parseSummary
  || activeTask.value?.parseWarnings?.length
  || activeTask.value?.understoodItems?.length,
))

const showPrimaryParseSection = computed(() => Boolean(
  activeTask.value
  && isRuleConfirmationStage(activeTask.value)
  && hasParseContent.value,
))

const showDetailParseSection = computed(() => Boolean(
  activeTask.value
  && detailExtrasExpanded.value
  && !isRuleConfirmationStage(activeTask.value)
  && hasParseContent.value,
))

const hasHiddenDetailContent = computed(() => Boolean(
  activeTask.value
  && (
    activeTask.value.requestPayload
    || (!isRuleConfirmationStage(activeTask.value) && hasParseContent.value)
  ),
))

function buildStructuredTaskPayload(formState, taskName, { includeNaturalLanguage = false, parsedRequestConfirmed = false } = {}) {
  return {
    taskName,
    trainingId: formState.trainingId,
    naturalLanguagePrompt: includeNaturalLanguage ? (String(formState.naturalLanguagePrompt || '').trim() || undefined) : undefined,
    parsedRequestConfirmed,
    scopeType: formState.scopeType,
    scopeStartDate: formState.scopeType === 'current_week' && formState.scopeStartDate
      ? normalizeWeekStart(formState.scopeStartDate)
      : undefined,
    goal: formState.goal,
    planningMode: formState.planningMode,
    overwriteExistingSchedule: formState.overwriteExistingSchedule,
    constraintPayload: {
      dailyMaxHours: formState.dailyMaxHours,
      avoidExamDays: formState.avoidExamDays,
      fixedCourseKeys: parseFixedCourseKeys(formState),
      blockedTimeSlots: parseSlotLines(formState.blockedTimeSlotsText),
      courseTypeTimePreferences: parseCourseTypePreferencesText(formState.courseTypePreferencesText),
      instructorUnavailableSlots: parseSlotLines(formState.instructorUnavailableSlotsText, { withLabel: true }),
      locationUnavailableSlots: parseSlotLines(formState.locationUnavailableSlotsText, { withLabel: true }),
      examWeekFocus: parseExamWeekFocusText(formState.examWeekFocusText),
    },
    scheduleRuleOverride: {
      lessonUnitMinutes: formState.lessonUnitMinutes,
      breakMinutes: formState.breakMinutes,
      maxUnitsPerSession: formState.maxUnitsPerSession,
      dailyMaxUnits: formState.dailyMaxHours,
      preferredPlanningMode: formState.planningMode,
      splitStrategy: 'balanced',
      teachingWindows: parseTeachingWindowsText(formState.teachingWindowsText),
    },
    notes: formState.notes,
  }
}

function getEffectiveCoursePlanningMode(course) {
  const planningMode = activePlanningMode.value
  if (planningMode !== 'auto') {
    return planningMode
  }
  return normalizeCourseHours(course?.hours) > 0 ? 'by_hours' : 'fill_workdays'
}

function getCoursePlanHint(course) {
  const plannedHours = normalizeCourseHours(course?.hours)
  const effectiveMode = getEffectiveCoursePlanningMode(course)
  if (effectiveMode === 'by_hours') {
    if (plannedHours > 0) {
      return `计划课时 ${plannedHours}，本任务按课时排`
    }
    return '计划课时未设置，本任务按课时排前需先补齐计划课时'
  }
  if (effectiveMode === 'fill_all_days') {
    return plannedHours > 0
      ? `已设置计划课时 ${plannedHours}，但本任务按全部日期排满`
      : '计划课时未设置，本任务按全部日期排满'
  }
  return plannedHours > 0
    ? `已设置计划课时 ${plannedHours}，但本任务按工作日排满`
    : '计划课时未设置，本任务按工作日排满'
}

function getCoursePlanTagText(course) {
  const plannedHours = normalizeCourseHours(course?.hours)
  const effectiveMode = getEffectiveCoursePlanningMode(course)
  if (effectiveMode === 'by_hours') {
    return plannedHours > 0 ? `按课时排 · ${plannedHours}课时` : '按课时排'
  }
  if (effectiveMode === 'fill_all_days') {
    return '排满'
  }
  return '排满工作日'
}

function getCoursePlanTagColor(course) {
  const effectiveMode = getEffectiveCoursePlanningMode(course)
  if (effectiveMode === 'by_hours') {
    return 'blue'
  }
  if (effectiveMode === 'fill_all_days') {
    return 'volcano'
  }
  return 'gold'
}

function normalizeWeekStart(value) {
  const current = dayjs(value)
  if (!current.isValid()) {
    return ''
  }
  const dayIndex = current.day()
  const offset = dayIndex === 0 ? 6 : dayIndex - 1
  return current.subtract(offset, 'day').format('YYYY-MM-DD')
}

function getNearestValidWeekStart(training) {
  const currentWeekStart = normalizeWeekStart(dayjs())
  if (!training?.startDate || !training?.endDate) {
    return currentWeekStart
  }
  const minWeekStart = normalizeWeekStart(training.startDate)
  const maxWeekStart = normalizeWeekStart(training.endDate)
  if (!minWeekStart || !maxWeekStart) {
    return currentWeekStart
  }
  if (dayjs(currentWeekStart).isBefore(dayjs(minWeekStart), 'day')) {
    return minWeekStart
  }
  if (dayjs(currentWeekStart).isAfter(dayjs(maxWeekStart), 'day')) {
    return maxWeekStart
  }
  return currentWeekStart
}

function syncScopeStartDate(formState, training) {
  if (formState.scopeType !== 'current_week') {
    formState.scopeStartDate = ''
    return
  }
  formState.scopeStartDate = getNearestValidWeekStart(training)
}

async function loadTaskFormTrainingDetail() {
  if (!taskForm.trainingId) {
    return
  }
  try {
    const result = await getTraining(taskForm.trainingId)
    applyTrainingRuleDefaults(taskForm, result.scheduleRuleConfig)
    if (taskForm.scopeType === 'current_week') {
      syncScopeStartDate(taskForm, result)
    }
  } catch {}
}

function primeRuleConfirmForm(task) {
  if (!task?.requestPayload) {
    ruleConfirmTaskId.value = null
    return
  }
  resetStructuredTaskForm(ruleConfirmForm, task.requestPayload.trainingId || task.requestPayload.training_id || task.trainingId)
  applyStructuredTaskPayload(ruleConfirmForm, task.requestPayload)
  ruleConfirmForm.taskName = task.taskName || ruleConfirmForm.taskName || buildSmartTaskName(ruleConfirmForm.trainingId)
  if (ruleConfirmForm.scopeType === 'current_week' && !ruleConfirmForm.scopeStartDate) {
    syncScopeStartDate(ruleConfirmForm, getTrainingById(ruleConfirmForm.trainingId))
  }
  ruleConfirmTaskId.value = task.id
}

function queryTourTarget(tourId) {
  if (typeof document === 'undefined') {
    return null
  }
  return document.querySelector(`[data-tour-id="${tourId}"]`)
}

function createTourStep(title, description, tourId, placement = 'bottom') {
  return {
    title,
    description,
    placement,
    target: () => queryTourTarget(tourId),
  }
}

const scheduleTourSteps = computed(() => {
  if (activeTab.value === 'list' && activeTask.value) {
    if (isRuleConfirmationStage(activeTask.value)) {
      return [
        createTourStep('这里看当前任务状态', '当前选中的任务名称、状态和刷新操作都集中在这里。', 'schedule-detail-header', 'bottom'),
        hasParseContent.value
          ? createTourStep('先看解析结果', '这里会展示系统理解了什么，以及还需要你特别注意的警告。', 'schedule-parse-section', 'top')
          : null,
        createTourStep('直接在这里确认规则', '不需要再跳到创建区；就在当前任务详情里调整结构化规则。', 'schedule-rule-confirm-section', 'top'),
        createTourStep('确认后继续生成课表', '提交后仍停留在任务列表，后台会继续生成课表，完成后再预览并确认应用。', 'schedule-rule-confirm-create-button', 'top'),
      ].filter(Boolean)
    }
    return [
      createTourStep('这里看当前任务结果', '当前选中的任务名称、刷新、保存和确认操作都集中在这里。', 'schedule-detail-header', 'bottom'),
      createTourStep('优先处理冲突', '如果这里还有硬冲突，先修改方案，不要直接确认应用。', 'schedule-conflict-section', 'top'),
      createTourStep('主方案会真正落库', '这里是当前准备应用的课表，可以逐条检查课次时间、地点和课时。', 'schedule-main-plan', 'top'),
      createTourStep('备选方案可一键切换', '主方案不合适时，可以先切换备选方案，再继续微调。', 'schedule-alternative-plan', 'top'),
    ]
  }

  if (createMode.value === 'smart') {
    return [
      !hasPresetTrainingId.value
        ? createTourStep('先选择培训班', '智能排课会基于该培训班的培训周期、课程清单、考试安排和排课规则生成建议。', 'schedule-training', 'bottom')
        : null,
      createTourStep('这里填写排课要求', '你可以直接写”本周按工作日排满，上午 08:30-12:30，一个课时 40 分钟，课间休息 10 分钟”这样的描述。', 'schedule-natural-language', 'bottom'),
      createTourStep('先创建智能排课任务', '提交后会进入任务列表，后台先解析规则；解析完成后再确认结构化规则，并继续生成课表。', 'schedule-create-button', 'top'),
    ].filter(Boolean)
  }

  return [
    createTourStep('先给任务命名', '建议带上班期、周次或目标，后续在任务列表里会更容易定位。', 'schedule-task-name', 'bottom'),
    createTourStep('这里选择培训班', '系统会基于培训周期、课程清单、已有课次和考试安排生成建议。', 'schedule-training', 'bottom'),
    createTourStep('这里决定排课范围', '首次排课建议选全班次；只调整某一周时，改成指定周。', 'schedule-scope', 'bottom'),
    createTourStep('这里决定排课倾向', '均衡排课适合常规安排，专项强化适合实战、理论或考前阶段。', 'schedule-goal', 'bottom'),
    createTourStep('这里决定排课方式', '你可以直接选择排满、排满工作日或按课时排。只有按课时排时，系统才会严格使用课程计划课时。', 'schedule-planning-mode', 'bottom'),
    createTourStep('用它控制每日强度', '单日最大课时会影响可排时段和冲突判断，过高或过低都会影响结果。', 'schedule-daily-hours', 'bottom'),
    taskForm.scopeType === 'current_week'
      ? createTourStep('指定周默认已带出', '这里默认取培训周期内最近有效周，你可以改成其他周；如果超出培训周期，后端会直接提示。', 'schedule-week', 'left')
      : null,
    createTourStep('先决定是否避开考试日', '开启后，系统会在生成建议时主动避开考试日期或考试时段。', 'schedule-constraint', 'top'),
    createTourStep('补充说明写人工约束', '这里适合填写“周三下午不排理论课”“重点课程尽量前置”这类额外要求。', 'schedule-notes', 'top'),
    createTourStep('从这里生成方案', '创建后会进入任务列表，等待后台生成主方案、冲突清单和备选方案。', 'schedule-create-button', 'top'),
  ].filter(Boolean)
})

async function loadTrainings() {
  try {
    const result = await getTrainings({ size: -1 })
    trainings.value = result.items || result || []
  } catch {
    trainings.value = []
  }
}

async function loadTasks() {
  taskLoading.value = true
  try {
    const result = await getAiScheduleTasks({ size: -1 })
    taskList.value = result.items || []
    if (!activeTask.value && taskList.value.length) {
      await loadTaskDetail(taskList.value[0].id)
    }
  } catch (error) {
    message.error(error.message || '加载任务失败')
  } finally {
    taskLoading.value = false
  }
}

async function loadTaskDetail(taskId) {
  try {
    const result = await getAiScheduleTaskDetail(taskId)
    activeTask.value = cloneDeep(result)
  } catch (error) {
    message.error(error.message || '加载任务详情失败')
  }
}

async function selectTask(taskId) {
  await loadTaskDetail(taskId)
}

async function handleCreateTask() {
  if (!taskForm.trainingId) {
    message.warning('请先选择培训班')
    return
  }
  if (createMode.value === 'smart') {
    if (!taskForm.naturalLanguagePrompt.trim()) {
      message.warning('请输入排课要求')
      return
    }
    creating.value = true
    try {
      const result = await createAiScheduleTask({
        taskName: buildSmartTaskName(taskForm.trainingId),
        trainingId: taskForm.trainingId,
        naturalLanguagePrompt: taskForm.naturalLanguagePrompt.trim(),
        overwriteExistingSchedule: taskForm.overwriteExistingSchedule,
        notes: taskForm.notes || undefined,
      })
      message.success('智能排课任务已创建，后台正在解析规则')
      await loadTasks()
      await loadTaskDetail(result.id)
      activeTab.value = 'list'
    } catch (error) {
      message.error(error.message || '创建任务失败')
    } finally {
      creating.value = false
    }
    return
  }
  if (!taskForm.taskName.trim()) {
    message.warning('请填写任务名称')
    return
  }
  creating.value = true
  try {
    const payload = buildStructuredTaskPayload(taskForm, taskForm.taskName)
    const result = await createAiScheduleTask(payload)
    message.success('手动排课任务已创建')
    await loadTasks()
    await loadTaskDetail(result.id)
    activeTab.value = 'list'
  } catch (error) {
    message.error(error.message || '创建任务失败')
  } finally {
    creating.value = false
  }
}

async function handleConfirmRules() {
  if (!activeTask.value?.id) {
    return
  }
  if (!ruleConfirmForm.taskName.trim()) {
    message.warning('请填写任务名称')
    return
  }
  ruleConfirming.value = true
  try {
    const taskId = activeTask.value.id
    const result = await confirmAiScheduleTaskRules(
      taskId,
      buildStructuredTaskPayload(ruleConfirmForm, ruleConfirmForm.taskName, {
        includeNaturalLanguage: true,
        parsedRequestConfirmed: true,
      }),
    )
    await loadTasks()
    await loadTaskDetail(result.id || taskId)
    message.success('规则已确认，后台正在生成课表')
  } catch (error) {
    message.error(error.message || '确认规则失败')
  } finally {
    ruleConfirming.value = false
  }
}

async function handleDeleteTask(task) {
  if (!task?.id || !task?.canDelete) {
    return
  }
  deletingTaskId.value = task.id
  try {
    const deletingActiveTask = activeTask.value?.id === task.id
    if (deletingActiveTask) {
      clearTaskPollTimer()
      activeTask.value = null
    }
    await deleteAiScheduleTask(task.id)
    await loadTasks()
    message.success('任务已删除')
  } catch (error) {
    message.error(error.message || '删除任务失败')
  } finally {
    deletingTaskId.value = null
  }
}

function openEditSession(courseIndex, scheduleIndex) {
  const session = activeTask.value?.mainPlan?.courses?.[courseIndex]?.schedules?.[scheduleIndex]
  if (!session) return
  sessionForm.courseIndex = courseIndex
  sessionForm.scheduleIndex = scheduleIndex
  sessionForm.date = session.date || ''
  sessionForm.timeRange = session.timeRange || ''
  sessionForm.location = session.location || ''
  sessionModalOpen.value = true
}

function handleSessionEdit() {
  const course = activeTask.value?.mainPlan?.courses?.[sessionForm.courseIndex]
  const session = course?.schedules?.[sessionForm.scheduleIndex]
  if (!session) return
  session.date = sessionForm.date.trim()
  session.timeRange = sessionForm.timeRange.trim()
  session.location = sessionForm.location.trim()
  session.hours = calculateSessionUnitsFromTimeRange(session.timeRange)
  syncMainPlanMetrics()
  sessionModalOpen.value = false
}

function removeTaskSession(courseIndex, scheduleIndex) {
  const session = activeTask.value?.mainPlan?.courses?.[courseIndex]?.schedules?.[scheduleIndex]
  const courseName = activeTask.value?.mainPlan?.courses?.[courseIndex]?.name || '未命名课程'
  if (!session) {
    return
  }
  Modal.confirm({
    title: '确认删除课次',
    content: `确定删除课次「${courseName} ${session.date || ''} ${session.timeRange || ''}」吗？`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => {
      const targetCourse = activeTask.value?.mainPlan?.courses?.[courseIndex]
      if (!targetCourse?.schedules?.[scheduleIndex]) {
        return
      }
      targetCourse.schedules.splice(scheduleIndex, 1)
      syncMainPlanMetrics()
      message.success('课次已从当前任务草案中移除，请记得保存')
    },
  })
}

function adoptAlternativePlan(plan) {
  activeTask.value.mainPlan = cloneDeep(plan)
  message.success(`已将${plan.title}设为主方案`)
}

async function handleSaveTask() {
  if (!activeTask.value) return false
  saving.value = true
  try {
    const result = await updateAiScheduleTaskResult(activeTask.value.id, {
      taskName: activeTask.value.taskName,
      mainPlan: activeTask.value.mainPlan,
      alternativePlans: activeTask.value.alternativePlans || [],
      conflicts: activeTask.value.conflicts || [],
      explanation: activeTask.value.explanation,
    })
    activeTask.value = cloneDeep(result)
    await loadTasks()
    message.success('方案已保存')
    return true
  } catch (error) {
    message.error(error.message || '保存失败')
    return false
  } finally {
    saving.value = false
  }
}

async function handleConfirmTask() {
  if (!activeTask.value) return
  if (activeTask.value.requestPayload?.overwriteExistingSchedule) {
    const shouldContinue = await new Promise(resolve => {
      Modal.confirm({
        title: '确认覆盖当前课表？',
        content: '应用后将以当前主方案覆盖现有课表，已有未锁定课次会被替换。',
        okText: '确认覆盖并应用',
        cancelText: '取消',
        onOk: () => resolve(true),
        onCancel: () => resolve(false),
      })
    })
    if (!shouldContinue) {
      return
    }
  }
  confirming.value = true
  try {
    const saved = await handleSaveTask()
    if (!saved) {
      return
    }
    const result = await confirmAiScheduleTask(activeTask.value.id)
    activeTask.value = cloneDeep(result)
    await loadTasks()
    planCalendarOpen.value = false
    message.success('排课方案已应用到现有课表')
  } catch (error) {
    message.error(error.message || '确认失败')
  } finally {
    confirming.value = false
  }
}

function clearTaskPollTimer() {
  if (!taskPollTimer) {
    return
  }
  window.clearTimeout(taskPollTimer)
  taskPollTimer = 0
}

function scheduleTaskPoll() {
  clearTaskPollTimer()
  if (!isProcessingStage(activeTask.value)) {
    return
  }
  taskPollTimer = window.setTimeout(async () => {
    if (!activeTask.value?.id) {
      return
    }
    await loadTaskDetail(activeTask.value.id)
    await loadTasks()
    if (isProcessingStage(activeTask.value)) {
      scheduleTaskPoll()
      return
    }
    if (isRuleConfirmationStage(activeTask.value)) {
      message.success('规则解析完成，请确认规则后继续生成课表')
    } else if (isScheduleConfirmationStage(activeTask.value)) {
      message.success('课表生成完成，请预览后确认应用')
    }
  }, 3000)
}

function buildPlanCalendarWeeks(plan) {
  const sessions = []
  for (const course of plan?.courses || []) {
    for (const schedule of course.schedules || []) {
      if (!schedule.date || !schedule.timeRange) {
        continue
      }
      sessions.push({
        id: `${course.courseKey || course.name}-${schedule.sessionId || schedule.date}-${schedule.timeRange}`,
        date: schedule.date,
        timeRange: schedule.timeRange,
        courseName: course.name || '未命名课程',
        instructor: course.instructor || '未指定教官',
        location: schedule.location || course.location || '未指定地点',
        hours: getSessionDisplayHours(schedule),
      })
    }
  }
  sessions.sort((left, right) => `${left.date} ${left.timeRange}`.localeCompare(`${right.date} ${right.timeRange}`))
  const grouped = new Map()
  for (const session of sessions) {
    const weekKey = normalizeWeekStart(session.date)
    if (!grouped.has(weekKey)) {
      const days = Array.from({ length: 7 }, (_, index) => {
        const current = dayjs(weekKey).add(index, 'day')
        return {
          date: current.format('YYYY-MM-DD'),
          label: `${current.format('MM-DD')} ${weekdayLabels[index + 1]}`,
          sessions: [],
        }
      })
      grouped.set(weekKey, {
        key: weekKey,
        label: `${weekKey} - ${dayjs(weekKey).add(6, 'day').format('YYYY-MM-DD')}`,
        days,
      })
    }
    const targetWeek = grouped.get(weekKey)
    const targetDay = targetWeek.days.find(item => item.date === session.date)
    if (targetDay) {
      targetDay.sessions.push(session)
    }
  }
  return Array.from(grouped.values()).sort((left, right) => left.key.localeCompare(right.key))
}

function openPlanCalendar() {
  if (!planCalendarWeeks.value.length) {
    message.info('当前任务暂无可预览课表')
    return
  }
  planCalendarActiveWeek.value = planCalendarWeeks.value[0].key
  planCalendarOpen.value = true
}

async function openScheduleTour() {
  if (activeTab.value === 'list' && !activeTask.value) {
    activeTab.value = 'create'
  }
  scheduleTourOpen.value = false
  scheduleTourCurrent.value = 0
  await nextTick()
  await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))
  if (!scheduleTourSteps.value.length) {
    return
  }
  scheduleTourOpen.value = true
}

function handleScheduleTourClose() {
  scheduleTourOpen.value = false
  scheduleTourCurrent.value = 0
}

async function maybeOpenRequestedTour() {
  if (String(route.query.tour || '').trim() !== 'smart-schedule') {
    return
  }
  activeTab.value = 'create'
  createMode.value = 'smart'
  await nextTick()
  await openScheduleTour()
  const nextQuery = { ...route.query }
  delete nextQuery.tour
  router.replace({
    name: route.name,
    params: route.params,
    query: nextQuery,
  })
}

watch(
  () => taskForm.trainingId,
  async () => {
    await loadTaskFormTrainingDetail()
    if (taskForm.scopeType === 'current_week') {
      syncScopeStartDate(taskForm, selectedTraining.value)
    }
  },
)

watch(
  () => taskForm.scopeType,
  (value) => {
    if (value === 'current_week') {
      syncScopeStartDate(taskForm, selectedTraining.value)
      return
    }
    taskForm.scopeStartDate = ''
  },
)

watch(
  () => ruleConfirmForm.scopeType,
  (value) => {
    if (value === 'current_week') {
      syncScopeStartDate(ruleConfirmForm, getTrainingById(ruleConfirmForm.trainingId))
      return
    }
    ruleConfirmForm.scopeStartDate = ''
  },
)

watch(
  activeTask,
  () => {
    if (activeTask.value?.id !== detailExtrasTaskId.value) {
      detailExtrasExpanded.value = false
      detailExtrasTaskId.value = activeTask.value?.id || null
    }
    if (isRuleConfirmationStage(activeTask.value) && activeTask.value?.id !== ruleConfirmTaskId.value) {
      primeRuleConfirmForm(activeTask.value)
    } else if (!isRuleConfirmationStage(activeTask.value)) {
      ruleConfirmTaskId.value = null
    }
    if (planCalendarWeeks.value.length && !planCalendarWeeks.value.some(item => item.key === planCalendarActiveWeek.value)) {
      planCalendarActiveWeek.value = planCalendarWeeks.value[0].key
    }
    scheduleTaskPoll()
  },
  { deep: true },
)

onMounted(async () => {
  await loadTrainings()
  await loadTaskFormTrainingDetail()
  if (taskForm.scopeType === 'current_week') {
    syncScopeStartDate(taskForm, selectedTraining.value)
  }
  await loadTasks()
  await maybeOpenRequestedTour()
})

onBeforeUnmount(() => {
  clearTaskPollTimer()
})
</script>

<style scoped>
.create-form-wrap { max-width: 880px; }
.create-mode-tabs :deep(.ant-tabs-nav) { margin-bottom: 16px; }
.tour-trigger-button { flex-shrink: 0; border-color: #bfdbfe; color: #1d4ed8; background: #eff6ff; }
.tour-trigger-button:hover,
.tour-trigger-button:focus { color: #1e40af; border-color: #93c5fd; background: #dbeafe; }
.field-help { margin-top: 6px; color: #8c8c8c; font-size: 12px; line-height: 1.6; }
.detail-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 16px; }
.detail-title { font-size: 18px; font-weight: 600; color: #001234; }
.detail-sub { margin-top: 6px; color: #8c8c8c; }
.detail-section { margin-top: 20px; }
.detail-section-title { margin-bottom: 12px; font-size: 15px; font-weight: 600; color: #1f1f1f; }
.detail-more-toggle { display: flex; justify-content: center; }
.detail-more-button { padding-inline: 0; }
.preview-list { display: flex; flex-direction: column; gap: 6px; }
.conflict-list { display: flex; flex-direction: column; gap: 10px; }
.plan-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.course-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.course-card { padding: 14px; border: 1px solid #eef0f5; border-radius: 10px; background: #fff; }
.course-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 10px; }
.course-title { font-size: 15px; font-weight: 600; color: #1f1f1f; }
.course-sub { margin-top: 4px; color: #8c8c8c; font-size: 12px; }
.schedule-list { display: flex; flex-direction: column; gap: 8px; }
.schedule-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 10px 0; border-top: 1px dashed #eef0f5; }
.schedule-row:first-child { border-top: 0; padding-top: 0; }
.schedule-sub { color: #8c8c8c; font-size: 12px; }
.alternative-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.alternative-card { padding: 14px; border-radius: 10px; border: 1px solid #eef0f5; background: #fafcff; }
.alternative-title { font-weight: 600; color: #1f1f1f; }
.alternative-sub { margin-top: 6px; min-height: 40px; color: #595959; font-size: 13px; }
.alternative-metrics { margin: 10px 0 12px; color: #8c8c8c; font-size: 12px; }
.calendar-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 12px; }
.calendar-cell { min-height: 220px; padding: 12px; border: 1px solid #eef0f5; border-radius: 12px; background: #fbfcff; }
.calendar-date { font-weight: 600; color: #001234; }
.calendar-session-list { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.calendar-session { padding: 10px; border-radius: 10px; background: #eef4ff; }
.calendar-session-title { font-weight: 600; color: #1d4ed8; }
.calendar-session-sub { margin-top: 4px; color: #475569; font-size: 12px; line-height: 1.5; }
@media (max-width: 960px) {
  .course-grid, .alternative-grid { grid-template-columns: 1fr; }
  .detail-header { flex-direction: column; }
  .calendar-grid { grid-template-columns: 1fr; }
}
</style>
