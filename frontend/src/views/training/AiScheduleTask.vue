<template>
  <ai-task-tabs-layout
    v-model:active-tab="activeTab"
    title="AI排课建议"
    subtitle="先生成建议方案，再人工调整并确认应用到现有课表"
    tag-text="训练智能体"
    :task-list="taskList"
    :task-loading="taskLoading"
    :active-task-id="activeTask?.id || null"
    :status-labels="statusLabels"
    :status-colors="statusColors"
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
                  <div class="field-help">这里只需要输入自然语言要求。系统会先解析成结构化排课配置，再生成主方案、备选方案和冲突清单。</div>
                </a-form-item>
              </div>
              <div data-tour-id="schedule-create-button">
                <a-button type="primary" block :loading="creating" @click="handleCreateTask">
                  创建智能排课任务
                </a-button>
              </div>
            </a-form>
          </a-tab-pane>

          <a-tab-pane key="manual" tab="普通排课">
            <a-form layout="vertical">
              <div data-tour-id="schedule-task-name">
                <a-form-item label="任务名称" required>
                  <a-input v-model:value="taskForm.taskName" placeholder="例：三月第二周排课建议" />
                </a-form-item>
              </div>
              <div data-tour-id="schedule-training">
                <a-form-item label="培训班" required>
                  <a-select v-model:value="taskForm.trainingId" :options="trainingOptions" placeholder="请选择培训班" />
                </a-form-item>
              </div>
              <a-row :gutter="12">
                <a-col :span="12">
                  <div data-tour-id="schedule-scope">
                    <a-form-item label="排课范围">
                      <a-select v-model:value="taskForm.scopeType">
                        <a-select-option value="all">全班次</a-select-option>
                        <a-select-option value="current_week">指定周</a-select-option>
                        <a-select-option value="unscheduled">仅未排课课次</a-select-option>
                      </a-select>
                    </a-form-item>
                  </div>
                </a-col>
                <a-col :span="12">
                  <div data-tour-id="schedule-goal">
                    <a-form-item label="排课目标">
                      <a-select v-model:value="taskForm.goal">
                        <a-select-option value="balanced">均衡排课</a-select-option>
                        <a-select-option value="practice_first">优先实战</a-select-option>
                        <a-select-option value="theory_first">优先理论</a-select-option>
                        <a-select-option value="exam_intensive">考前强化</a-select-option>
                      </a-select>
                    </a-form-item>
                  </div>
                </a-col>
              </a-row>
              <a-row :gutter="12">
                <a-col :span="12">
                  <div data-tour-id="schedule-planning-mode">
                    <a-form-item label="排课方式">
                      <a-select v-model:value="taskForm.planningMode">
                        <a-select-option value="fill_workdays">排满工作日</a-select-option>
                        <a-select-option value="fill_all_days">排满</a-select-option>
                        <a-select-option value="by_hours">按课时排</a-select-option>
                      </a-select>
                      <div class="field-help">按课时排会严格使用课程计划课时；排满模式会优先铺满可排日期，不受计划课时限制。</div>
                    </a-form-item>
                  </div>
                </a-col>
                <a-col :span="12">
                  <div data-tour-id="schedule-daily-hours">
                    <a-form-item label="单日最大课时">
                      <a-input-number v-model:value="taskForm.dailyMaxHours" :min="1" :max="12" style="width:100%" />
                    </a-form-item>
                  </div>
                </a-col>
              </a-row>
              <div data-tour-id="schedule-rule-overrides">
                <a-divider orientation="left" plain>任务级规则覆盖</a-divider>
                <a-row :gutter="12">
                  <a-col :span="6">
                    <a-form-item label="单课时分钟数">
                      <a-input-number v-model:value="taskForm.lessonUnitMinutes" :min="20" :max="180" style="width:100%" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="6">
                    <a-form-item label="课间休息分钟数">
                      <a-input-number v-model:value="taskForm.breakMinutes" :min="0" :max="60" style="width:100%" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="6">
                    <a-form-item label="单节最多课时">
                      <a-input-number v-model:value="taskForm.maxUnitsPerSession" :min="1" :max="12" style="width:100%" />
                    </a-form-item>
                  </a-col>
                  <a-col :span="6">
                    <a-form-item label="拆分策略">
                      <a-select value="balanced" disabled>
                        <a-select-option value="balanced">尽量平分</a-select-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                </a-row>
                <a-form-item label="可排课时间段">
                  <a-textarea v-model:value="taskForm.teachingWindowsText" :rows="3" placeholder="每行一个时间段，如：上午|08:30-12:30" />
                  <div class="field-help">不填时默认使用培训班规则。支持写多行，格式如“上午|08:30-12:30”。</div>
                </a-form-item>
              </div>
              <div v-if="taskForm.scopeType === 'current_week'" data-tour-id="schedule-week">
                <a-form-item label="指定周">
                  <a-date-picker
                    v-model:value="taskForm.scopeStartDate"
                    style="width:100%"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    placeholder="请选择该周任意日期"
                  />
                  <div class="field-help">默认取培训周期内最近有效周，可修改；系统会自动按该周周一处理。</div>
                </a-form-item>
              </div>
              <div data-tour-id="schedule-constraint">
                <a-form-item>
                  <a-checkbox v-model:checked="taskForm.avoidExamDays">避开考试日</a-checkbox>
                </a-form-item>
              </div>
              <div data-tour-id="schedule-fixed-course-key">
                <a-form-item label="固定课程键">
                  <a-textarea v-model:value="taskForm.fixedCourseKeysText" :rows="2" placeholder="每行一个 course_key，可选" />
                  <div class="field-help">填写需要锁定的 course_key。AI 生成建议时会保留这些已定课次，不再重新调整。</div>
                </a-form-item>
              </div>
              <div data-tour-id="schedule-notes">
                <a-form-item label="补充说明">
                  <a-textarea v-model:value="taskForm.notes" :rows="3" />
                </a-form-item>
              </div>
              <div data-tour-id="schedule-create-button">
                <a-button type="primary" block :loading="creating" @click="handleCreateTask">
                  创建普通排课任务
                </a-button>
              </div>
            </a-form>
          </a-tab-pane>
        </a-tabs>
      </div>
    </template>

    <template #task-description="{ item }">
      {{ item.trainingName || '未命名培训班' }} · {{ item.itemCount || 0 }} 个课次
    </template>

    <template #detail>
      <template v-if="activeTask">
        <div data-tour-id="schedule-detail-header" class="detail-header">
          <div>
            <div class="detail-title">{{ activeTask.taskName }}</div>
            <div class="detail-sub">{{ activeTask.trainingName || '未命名培训班' }}</div>
          </div>
          <a-space>
            <a-button @click="loadTaskDetail(activeTask.id)">刷新详情</a-button>
            <a-button :disabled="activeTask.status !== 'completed'" :loading="saving" @click="handleSaveTask">保存修改</a-button>
            <a-button type="primary" :disabled="activeTask.status !== 'completed'" :loading="confirming" @click="handleConfirmTask">
              确认应用
            </a-button>
          </a-space>
        </div>

        <ai-task-timeline
          :status="activeTask.status"
          :created-at="activeTask.createdAt"
          :completed-at="activeTask.completedAt"
          :confirmed-at="activeTask.confirmedAt"
        />

        <div data-tour-id="schedule-request-section" class="detail-section">
          <div class="detail-section-title">任务请求</div>
          <a-descriptions :column="2" size="small" bordered>
            <a-descriptions-item label="自然语言要求" :span="2">
              {{ activeTask.requestPayload.naturalLanguagePrompt || '未填写' }}
            </a-descriptions-item>
            <a-descriptions-item label="排课范围">{{ scopeLabels[activeTask.requestPayload.scopeType] || activeTask.requestPayload.scopeType }}</a-descriptions-item>
            <a-descriptions-item label="排课目标">{{ goalLabels[activeTask.requestPayload.goal] || activeTask.requestPayload.goal }}</a-descriptions-item>
            <a-descriptions-item label="排课方式">{{ planningModeLabels[resolvePlanningMode(activeTask.requestPayload.planningMode)] || resolvePlanningMode(activeTask.requestPayload.planningMode) }}</a-descriptions-item>
            <a-descriptions-item label="单日最大课时">{{ activeTask.requestPayload.constraintPayload?.dailyMaxHours || 0 }}</a-descriptions-item>
            <a-descriptions-item label="避开考试日">{{ activeTask.requestPayload.constraintPayload?.avoidExamDays ? '是' : '否' }}</a-descriptions-item>
            <a-descriptions-item
              v-if="activeTask.requestPayload.scopeType === 'current_week' && activeTask.requestPayload.scopeStartDate"
              label="指定周"
            >
              {{ activeTask.requestPayload.scopeStartDate }}
            </a-descriptions-item>
            <a-descriptions-item label="规则覆盖" :span="2">
              {{ formatRuleOverrideSummary(activeTask.requestPayload.scheduleRuleOverride) }}
            </a-descriptions-item>
          </a-descriptions>
        </div>

        <div class="detail-section" v-if="activeTask.parseSummary || activeTask.parseWarnings?.length">
          <div class="detail-section-title">自然语言解析结果</div>
          <a-alert v-if="activeTask.parseSummary" type="success" :message="activeTask.parseSummary" show-icon style="margin-bottom:12px" />
          <div v-if="activeTask.parseWarnings?.length" class="conflict-list">
            <a-alert v-for="(item, index) in activeTask.parseWarnings" :key="index" type="warning" :message="item" show-icon />
          </div>
        </div>

        <div class="detail-section" v-if="activeTask.explanation">
          <div class="detail-section-title">方案说明</div>
          <a-alert type="info" :message="activeTask.explanation" show-icon />
        </div>

        <div data-tour-id="schedule-conflict-section" class="detail-section">
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
                  <a-button v-if="activeTask.status === 'completed'" type="link" size="small" @click="openEditSession(courseIndex, scheduleIndex)">
                    编辑
                  </a-button>
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

  <a-tour
    v-model:open="scheduleTourOpen"
    v-model:current="scheduleTourCurrent"
    :steps="scheduleTourSteps"
    @close="handleScheduleTourClose"
  />
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { QuestionCircleOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import {
  confirmAiScheduleTask,
  createAiScheduleTask,
  getAiScheduleTaskDetail,
  getAiScheduleTasks,
  updateAiScheduleTaskResult,
} from '@/api/ai'
import { getTraining, getTrainings } from '@/api/training'
import AiTaskTabsLayout from '@/views/exam/components/AiTaskTabsLayout.vue'
import AiTaskTimeline from '@/views/exam/components/AiTaskTimeline.vue'

const route = useRoute()
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
const sessionForm = reactive({ courseIndex: -1, scheduleIndex: -1, date: '', timeRange: '', location: '' })

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

const taskForm = reactive({
  taskName: '',
  trainingId: route.params.id ? Number(route.params.id) : undefined,
  naturalLanguagePrompt: '',
  scopeType: 'all',
  scopeStartDate: '',
  goal: 'balanced',
  planningMode: 'fill_workdays',
  dailyMaxHours: 6,
  lessonUnitMinutes: 40,
  breakMinutes: 10,
  maxUnitsPerSession: 3,
  teachingWindowsText: '',
  avoidExamDays: true,
  fixedCourseKeysText: '',
  notes: '',
})

const trainingOptions = computed(() => (trainings.value || []).map(item => ({
  label: item.name,
  value: item.id,
})))
const hasPresetTrainingId = computed(() => Boolean(route.params.id))
const selectedTraining = computed(() => (trainings.value || []).find(item => item.id === taskForm.trainingId) || null)

function cloneDeep(value) {
  return JSON.parse(JSON.stringify(value))
}

function parseFixedCourseKeys() {
  return taskForm.fixedCourseKeysText.split(/\r?\n|,|，|;|；/).map(item => item.trim()).filter(Boolean)
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

function resolvePlanningMode(value) {
  const normalized = String(value || '').trim()
  if (Object.prototype.hasOwnProperty.call(planningModeLabels, normalized)) {
    return normalized
  }
  return 'auto'
}

const activePlanningMode = computed(() => resolvePlanningMode(activeTask.value?.requestPayload?.planningMode))

function applyTrainingRuleDefaults(ruleConfig) {
  const config = ruleConfig || {}
  taskForm.lessonUnitMinutes = Number(config.lessonUnitMinutes || config.lesson_unit_minutes || 40)
  taskForm.breakMinutes = Number(config.breakMinutes || config.break_minutes || 10)
  taskForm.maxUnitsPerSession = Number(config.maxUnitsPerSession || config.max_units_per_session || 3)
  taskForm.dailyMaxHours = Number(config.dailyMaxUnits || config.daily_max_units || 6)
  taskForm.planningMode = resolvePlanningMode(config.preferredPlanningMode || config.preferred_planning_mode || taskForm.planningMode)
  taskForm.teachingWindowsText = formatTeachingWindowsText(config.teachingWindows || config.teaching_windows || [])
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

function buildSmartTaskName() {
  const trainingName = selectedTraining.value?.name || '培训班'
  return `${trainingName}智能排课-${dayjs().format('MMDDHHmm')}`
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

function syncScopeStartDate() {
  if (taskForm.scopeType !== 'current_week') {
    taskForm.scopeStartDate = ''
    return
  }
  taskForm.scopeStartDate = getNearestValidWeekStart(selectedTraining.value)
}

async function loadSelectedTrainingDetail() {
  if (!taskForm.trainingId) {
    return
  }
  try {
    const result = await getTraining(taskForm.trainingId)
    applyTrainingRuleDefaults(result.scheduleRuleConfig)
    if (taskForm.scopeType === 'current_week') {
      syncScopeStartDate()
    }
  } catch {
  }
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
    return [
      createTourStep('这里看当前任务结果', '当前选中的任务名称、刷新、保存和确认操作都集中在这里。', 'schedule-detail-header', 'bottom'),
      createTourStep('先核对任务请求', '先确认排课范围、排课目标、排课方式和单日最大课时是否符合本次意图。', 'schedule-request-section', 'bottom'),
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
      createTourStep('这里只写自然语言要求', '你可以直接写“本周按工作日排满，上午 08:30-12:30，一个课时 40 分钟，课间休息 10 分钟”这类自然语言。', 'schedule-natural-language', 'bottom'),
      createTourStep('系统会自动创建任务', '智能排课模式下不需要手工填写任务名称，系统会自动生成任务名并开始解析排课要求。', 'schedule-create-button', 'top'),
    ].filter(Boolean)
  }

  return [
    createTourStep('先给任务命名', '建议带上班期、周次或目标，后续在任务列表里会更容易定位。', 'schedule-task-name', 'bottom'),
    createTourStep('这里选择培训班', '系统会基于培训周期、课程清单、已有课次和考试安排生成建议。', 'schedule-training', 'bottom'),
    createTourStep('这里决定排课范围', '首次排课建议选全班次；只调整某一周时，改成指定周。', 'schedule-scope', 'bottom'),
    createTourStep('这里决定排课倾向', '均衡排课适合常规安排，专项强化适合实战、理论或考前阶段。', 'schedule-goal', 'bottom'),
    createTourStep('这里决定排课方式', '你可以直接选择排满、排满工作日或按课时排。只有按课时排时，系统才会严格使用课程计划课时。', 'schedule-planning-mode', 'bottom'),
    createTourStep('用它控制每日强度', '单日最大课时会影响可排时段和冲突判断，过高或过低都会影响结果。', 'schedule-daily-hours', 'bottom'),
    createTourStep('这里可临时覆盖更多规则', '如果本次任务想临时调整单课时分钟数、课间休息或时间段，可以在这里覆盖，不会直接改培训班正式规则。', 'schedule-rule-overrides', 'top'),
    taskForm.scopeType === 'current_week'
      ? createTourStep('指定周默认已带出', '这里默认取培训周期内最近有效周，你可以改成其他周；如果超出培训周期，后端会直接提示。', 'schedule-week', 'left')
      : null,
    createTourStep('先决定是否避开考试日', '开启后，系统会在生成建议时主动避开考试日期或考试时段。', 'schedule-constraint', 'top'),
    createTourStep('固定课程键用于锁定已定课次', '这里填的不是课程名称，而是 course_key。填写后，AI 生成建议时会保留这些课程，不会重新调整它们；如果当前没有固定课次，可以留空。', 'schedule-fixed-course-key', 'top'),
    createTourStep('补充说明写人工约束', '这里适合填写“周三下午不排理论课”“重点课程尽量前置”这类额外要求。', 'schedule-notes', 'top'),
    createTourStep('从这里生成方案', '创建后会进入任务列表，可以查看主方案、冲突清单和备选方案。', 'schedule-create-button', 'top'),
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
  if (createMode.value === 'smart' && !taskForm.naturalLanguagePrompt.trim()) {
    message.warning('请输入自然语言排课要求')
    return
  }
  if (createMode.value === 'manual' && !taskForm.taskName.trim()) {
    message.warning('请填写任务名称')
    return
  }
  creating.value = true
  try {
    const payload = createMode.value === 'smart'
      ? {
          taskName: buildSmartTaskName(),
          trainingId: taskForm.trainingId,
          naturalLanguagePrompt: taskForm.naturalLanguagePrompt.trim(),
        }
      : {
          taskName: taskForm.taskName,
          trainingId: taskForm.trainingId,
          scopeType: taskForm.scopeType,
          scopeStartDate: taskForm.scopeType === 'current_week' && taskForm.scopeStartDate
            ? normalizeWeekStart(taskForm.scopeStartDate)
            : undefined,
          goal: taskForm.goal,
          planningMode: taskForm.planningMode,
          constraintPayload: {
            dailyMaxHours: taskForm.dailyMaxHours,
            avoidExamDays: taskForm.avoidExamDays,
            fixedCourseKeys: parseFixedCourseKeys(),
          },
          scheduleRuleOverride: {
            lessonUnitMinutes: taskForm.lessonUnitMinutes,
            breakMinutes: taskForm.breakMinutes,
            maxUnitsPerSession: taskForm.maxUnitsPerSession,
            dailyMaxUnits: taskForm.dailyMaxHours,
            preferredPlanningMode: taskForm.planningMode,
            splitStrategy: 'balanced',
            teachingWindows: parseTeachingWindowsText(taskForm.teachingWindowsText),
          },
          notes: taskForm.notes,
        }
    const result = await createAiScheduleTask(payload)
    message.success('排课任务已创建')
    await loadTasks()
    await loadTaskDetail(result.id)
    activeTab.value = 'list'
  } catch (error) {
    message.error(error.message || '创建任务失败')
  } finally {
    creating.value = false
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
  sessionModalOpen.value = false
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
  confirming.value = true
  try {
    const saved = await handleSaveTask()
    if (!saved) {
      return
    }
    const result = await confirmAiScheduleTask(activeTask.value.id)
    activeTask.value = cloneDeep(result)
    await loadTasks()
    message.success('排课方案已应用到现有课表')
  } catch (error) {
    message.error(error.message || '确认失败')
  } finally {
    confirming.value = false
  }
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

watch(
  () => taskForm.trainingId,
  async () => {
    await loadSelectedTrainingDetail()
    if (taskForm.scopeType === 'current_week') {
      syncScopeStartDate()
    }
  },
)

watch(
  () => taskForm.scopeType,
  (value) => {
    if (value === 'current_week') {
      syncScopeStartDate()
      return
    }
    taskForm.scopeStartDate = ''
  },
)

onMounted(async () => {
  await loadTrainings()
  await loadSelectedTrainingDetail()
  if (taskForm.scopeType === 'current_week') {
    syncScopeStartDate()
  }
  await loadTasks()
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
@media (max-width: 960px) {
  .course-grid, .alternative-grid { grid-template-columns: 1fr; }
  .detail-header { flex-direction: column; }
}
</style>
