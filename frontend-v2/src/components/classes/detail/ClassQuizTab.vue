<template>
  <div class="quiz-tab">
    <div class="quiz-toolbar">
      <div class="quiz-toolbar-meta">
        <strong>随堂测试</strong>
        <span>共 {{ quizSessions.length }} 场</span>
      </div>
      <a-button v-if="isInstructor" type="primary" @click="openCreateModal">
        <PlusOutlined /> 发布随堂测试
      </a-button>
    </div>

    <a-empty v-if="!quizSessions.length" description="暂无随堂测试" />
    <div v-else class="quiz-list">
      <div v-for="quiz in quizSessions" :key="quiz.id" class="quiz-row">
        <div class="quiz-main">
          <div class="quiz-title-row">
            <span class="quiz-title">{{ quiz.title || '随堂测试' }}</span>
            <a-tag color="gold">随堂测试</a-tag>
            <a-tag :color="statusColor(quiz.status)">{{ statusLabel(quiz.status) }}</a-tag>
          </div>
          <div class="quiz-meta">
            <span>{{ formatDateTime(quiz.start_time) }}</span>
            <span>题目 {{ quiz.question_count || 0 }} 道</span>
            <span>时长 {{ quiz.duration || 30 }} 分钟</span>
            <span>及格 {{ quiz.passing_score || 60 }} 分</span>
            <span>最多 {{ quiz.max_attempts || 1 }} 次</span>
          </div>
          <div v-if="quiz.description" class="quiz-desc">{{ quiz.description }}</div>
        </div>

        <div class="quiz-actions">
          <a-button size="small" @click="openQuiz(quiz)">{{ primaryActionLabel(quiz) }}</a-button>
          <template v-if="isInstructor">
            <a-button size="small" @click="openEditModal(quiz)">编辑</a-button>
            <a-popconfirm title="删除后不可恢复，确认删除？" ok-text="删除" cancel-text="取消" @confirm="handleDeleteQuiz(quiz)">
              <a-button size="small" danger>删除</a-button>
            </a-popconfirm>
          </template>
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="modalVisible"
      :title="isEditing ? '编辑随堂测试' : '发布随堂测试'"
      width="760px"
      :confirm-loading="submitting"
      :ok-text="isEditing ? '保存' : '发布'"
      cancel-text="取消"
      @ok="handleSubmit"
      @cancel="handleCloseModal"
    >
      <template v-if="!isEditing">
        <a-tabs v-model:activeKey="publishMode">
          <a-tab-pane key="paper" tab="选择测验试卷发布">
            <a-form layout="vertical">
              <a-form-item label="测验试卷" required>
                <a-select
                  v-model:value="form.paperId"
                  show-search
                  allow-clear
                  :filter-option="filterSelectOption"
                  :loading="paperLoading"
                  placeholder="请选择已发布的测验试卷"
                  :options="paperSelectOptions"
                />
              </a-form-item>
            </a-form>
          </a-tab-pane>
          <a-tab-pane key="course_generate" tab="按课程抽题发布">
            <a-form layout="vertical">
              <a-form-item label="关联课程" required>
                <a-select
                  v-model:value="form.courseId"
                  show-search
                  allow-clear
                  :filter-option="filterSelectOption"
                  placeholder="请选择培训班内的课程"
                  :options="courseSelectOptions"
                />
              </a-form-item>
              <a-row :gutter="16">
                <a-col :span="12">
                  <a-form-item label="抽题数量" required>
                    <a-input-number v-model:value="form.questionCount" :min="1" :max="100" style="width: 100%" />
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="题型范围" required>
                    <a-checkbox-group v-model:value="form.questionTypes">
                      <a-checkbox value="single">单选题</a-checkbox>
                      <a-checkbox value="multi">多选题</a-checkbox>
                      <a-checkbox value="judge">判断题</a-checkbox>
                    </a-checkbox-group>
                  </a-form-item>
                </a-col>
              </a-row>
            </a-form>
          </a-tab-pane>
        </a-tabs>
      </template>

      <a-form layout="vertical" class="quiz-form">
        <a-form-item label="测试名称" required>
          <a-input v-model:value="form.title" placeholder="请输入随堂测试名称" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="时长(分钟)" required>
              <a-input-number v-model:value="form.duration" :min="5" :max="300" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="及格分" required>
              <a-input-number v-model:value="form.passingScore" :min="0" :max="paperPassingScoreMax" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="最大作答次数" required>
              <a-input-number v-model:value="form.maxAttempts" :min="1" :max="10" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="开放时间" required>
              <a-range-picker
                v-model:value="dateRange"
                show-time
                format="YYYY-MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
                style="width: 100%"
                :placeholder="['开始时间', '结束时间']"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="测试说明">
          <a-textarea v-model:value="form.description" :rows="3" placeholder="可选，支持填写答题说明" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { getExamPapers, getUnifiedExamDetail } from '@/api/exam'
import { createTrainingQuiz, deleteTrainingQuiz, updateTrainingQuiz } from '@/api/training-quiz'

interface QuizSession {
  id: number
  title?: string
  status?: string
  purpose?: string
  type?: string | null
  start_time?: string | null
  end_time?: string | null
  description?: string | null
  duration?: number
  question_count?: number
  passing_score?: number
  max_attempts?: number
  attempt_count?: number
  latest_result?: string | null
  can_join?: boolean | null
}

interface CourseOption {
  id?: number
  course_id?: number | null
  name?: string
}

interface QuizPaperOption {
  id: number
  title: string
  totalScore: number
  questionCount: number
}

const props = withDefaults(defineProps<{
  trainingId: number
  quizSessions?: QuizSession[]
  courses?: CourseOption[]
  isInstructor?: boolean
  isStudent?: boolean
}>(), {
  quizSessions: () => [],
  courses: () => [],
  isInstructor: false,
  isStudent: false,
})

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

const router = useRouter()

const modalVisible = ref(false)
const publishMode = ref<'paper' | 'course_generate'>('paper')
const submitting = ref(false)
const paperLoading = ref(false)
const editingQuizId = ref<number | null>(null)
const dateRange = ref<string[]>([])
const paperOptions = ref<QuizPaperOption[]>([])

const form = ref({
  title: '',
  description: '',
  duration: 30,
  passingScore: 60,
  maxAttempts: 1,
  paperId: undefined as number | undefined,
  courseId: undefined as number | undefined,
  questionCount: 10,
  questionTypes: ['single', 'multi', 'judge'] as string[],
})

const isEditing = computed(() => editingQuizId.value !== null)

const courseSelectOptions = computed(() => {
  const map = new Map<number, string>()
  for (const item of props.courses || []) {
    if (!item.course_id || !item.name || map.has(item.course_id)) continue
    map.set(item.course_id, item.name)
  }
  return Array.from(map.entries()).map(([value, label]) => ({ value, label }))
})

const paperSelectOptions = computed(() =>
  paperOptions.value.map((item) => ({
    value: item.id,
    label: `${item.title} · ${item.questionCount}题 · ${item.totalScore}分`,
  })),
)

const selectedPaper = computed(() =>
  paperOptions.value.find((item) => item.id === form.value.paperId),
)

const paperPassingScoreMax = computed(() => {
  if (publishMode.value !== 'paper') return 999
  return Math.max(0, Number(selectedPaper.value?.totalScore || 0))
})

function filterSelectOption(input: string, option?: { label?: string }) {
  return String(option?.label || '').toLowerCase().includes(input.toLowerCase())
}

watch([() => form.value.paperId, () => dateRange.value[0], publishMode], () => {
  if (isEditing.value || publishMode.value !== 'paper' || !selectedPaper.value) return
  form.value.title = buildPaperQuizTitle(selectedPaper.value.title, dateRange.value[0])
  form.value.passingScore = resolvePaperPassingScore(selectedPaper.value.totalScore)
})

function resetForm() {
  publishMode.value = 'paper'
  editingQuizId.value = null
  dateRange.value = []
  form.value = {
    title: '',
    description: '',
    duration: 30,
    passingScore: 60,
    maxAttempts: 1,
    paperId: undefined,
    courseId: undefined,
    questionCount: 10,
    questionTypes: ['single', 'multi', 'judge'],
  }
}

function handleCloseModal() {
  modalVisible.value = false
  resetForm()
}

async function fetchQuizPapers() {
  paperLoading.value = true
  try {
    const result = await getExamPapers({
      page: 1,
      size: -1,
      status: 'published',
      type: 'quiz',
    })
    const rows = result?.items || result || []
    paperOptions.value = rows.map((item: Record<string, unknown>) => ({
      id: Number(item.id || 0),
      title: String(item.title || ''),
      totalScore: Number(item.totalScore ?? item.total_score ?? 0),
      questionCount: Number(item.questionCount ?? item.question_count ?? 0),
    })).filter((item: QuizPaperOption) => item.id > 0)
  } catch (error) {
    paperOptions.value = []
    message.error(error instanceof Error ? error.message : '加载测验试卷失败')
  } finally {
    paperLoading.value = false
  }
}

async function openCreateModal() {
  resetForm()
  modalVisible.value = true
  if (!paperOptions.value.length) {
    await fetchQuizPapers()
  }
}

async function openEditModal(quiz: QuizSession) {
  try {
    const detail = await getUnifiedExamDetail(quiz.id)
    resetForm()
    editingQuizId.value = quiz.id
    form.value.title = detail.title || ''
    form.value.description = detail.description || ''
    form.value.duration = detail.duration || 30
    form.value.passingScore = detail.passing_score || 60
    form.value.maxAttempts = detail.max_attempts || 1
    dateRange.value = [detail.start_time, detail.end_time].filter((item): item is string => Boolean(item))
    modalVisible.value = true
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载随堂测试详情失败')
  }
}

function validateForm() {
  if (!form.value.title.trim()) {
    message.warning('请输入随堂测试名称')
    return false
  }
  if (publishMode.value === 'paper' && form.value.passingScore > paperPassingScoreMax.value) {
    message.warning(`及格分不能超过试卷满分（${paperPassingScoreMax.value}分）`)
    return false
  }
  if (!dateRange.value.length || !dateRange.value[0] || !dateRange.value[1]) {
    message.warning('请选择测试开放时间')
    return false
  }
  if (!isEditing.value && publishMode.value === 'paper' && !form.value.paperId) {
    message.warning('请选择测验试卷')
    return false
  }
  if (!isEditing.value && publishMode.value === 'course_generate') {
    if (!form.value.courseId) {
      message.warning('请选择课程')
      return false
    }
    if (!form.value.questionCount || form.value.questionCount < 1) {
      message.warning('请填写抽题数量')
      return false
    }
    if (!form.value.questionTypes.length) {
      message.warning('请至少选择一种题型')
      return false
    }
  }
  return true
}

async function handleSubmit() {
  if (!validateForm()) return

  submitting.value = true
  try {
    if (isEditing.value && editingQuizId.value) {
      await updateTrainingQuiz(props.trainingId, editingQuizId.value, {
        title: form.value.title.trim(),
        description: form.value.description || undefined,
        duration: Number(form.value.duration),
        passing_score: Number(form.value.passingScore),
        max_attempts: Number(form.value.maxAttempts),
        start_time: dateRange.value[0],
        end_time: dateRange.value[1],
      })
      message.success('随堂测试已更新')
    } else if (publishMode.value === 'paper') {
      await createTrainingQuiz(props.trainingId, {
        mode: 'paper',
        training_id: props.trainingId,
        title: form.value.title.trim(),
        description: form.value.description || undefined,
        duration: Number(form.value.duration),
        passing_score: Number(form.value.passingScore),
        max_attempts: Number(form.value.maxAttempts),
        start_time: dateRange.value[0],
        end_time: dateRange.value[1],
        paper_id: form.value.paperId,
      })
      message.success('随堂测试已发布')
    } else {
      await createTrainingQuiz(props.trainingId, {
        mode: 'course_generate',
        training_id: props.trainingId,
        title: form.value.title.trim(),
        description: form.value.description || undefined,
        duration: Number(form.value.duration),
        passing_score: Number(form.value.passingScore),
        max_attempts: Number(form.value.maxAttempts),
        start_time: dateRange.value[0],
        end_time: dateRange.value[1],
        course_id: form.value.courseId,
        question_count: Number(form.value.questionCount),
        question_types: form.value.questionTypes,
      })
      message.success('随堂测试已发布并自动组卷')
    }

    handleCloseModal()
    emit('refresh')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '保存随堂测试失败')
  } finally {
    submitting.value = false
  }
}

async function handleDeleteQuiz(quiz: QuizSession) {
  try {
    await deleteTrainingQuiz(props.trainingId, quiz.id)
    message.success('随堂测试已删除')
    emit('refresh')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '删除随堂测试失败')
  }
}

function formatDateTime(value?: string | null) {
  if (!value) return '-'
  return String(value).slice(0, 16).replace('T', ' ')
}

function buildPaperQuizTitle(paperTitle?: string, startAt?: string) {
  const baseTitle = String(paperTitle || '').trim()
  if (!baseTitle) return ''
  const dateText = formatQuizDateLabel(startAt)
  return `${baseTitle}${dateText}随堂测试`
}

function formatQuizDateLabel(value?: string) {
  const date = value ? new Date(value) : new Date()
  const time = Number.isNaN(date.getTime()) ? new Date() : date
  return `${time.getMonth() + 1}月${time.getDate()}日`
}

function resolvePaperPassingScore(totalScore?: number) {
  const score = Number(totalScore || 0)
  if (score <= 0) return 0
  return Math.min(score, Math.ceil(score * 0.6))
}

function statusLabel(status?: string) {
  const map: Record<string, string> = {
    upcoming: '未开始',
    active: '进行中',
    ended: '已结束',
  }
  return map[String(status || '')] || '未开始'
}

function statusColor(status?: string) {
  const map: Record<string, string> = {
    upcoming: 'gold',
    active: 'green',
    ended: 'default',
  }
  return map[String(status || '')] || 'default'
}

function canTakeQuiz(quiz: QuizSession) {
  if (typeof quiz.can_join === 'boolean') {
    return quiz.can_join
  }
  if (!quiz.start_time) return false
  const now = Date.now()
  const start = new Date(quiz.start_time).getTime()
  const end = quiz.end_time ? new Date(quiz.end_time).getTime() : start + 2 * 3600 * 1000
  return now >= start && now <= end
}

function primaryActionLabel(quiz: QuizSession) {
  if (!props.isStudent) return '查看详情'
  if ((quiz.attempt_count || 0) > 0 && (!canTakeQuiz(quiz) || quiz.latest_result)) return '查看结果'
  if (canTakeQuiz(quiz)) return '开始测试'
  return '查看详情'
}

function openQuiz(quiz: QuizSession) {
  router.push(`/exam/overview/${quiz.id}?kind=training`)
}
</script>

<style scoped>
.quiz-tab {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quiz-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.quiz-toolbar-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--v2-text-muted);
}

.quiz-list {
  display: flex;
  flex-direction: column;
}

.quiz-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid var(--v2-border-light);
}

.quiz-row:last-child {
  border-bottom: none;
}

.quiz-main {
  min-width: 0;
  flex: 1;
}

.quiz-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.quiz-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
}

.quiz-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  color: var(--v2-text-muted);
  font-size: 13px;
}

.quiz-desc {
  margin-top: 8px;
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.quiz-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.quiz-form {
  margin-top: 12px;
}

@media (max-width: 768px) {
  .quiz-toolbar,
  .quiz-row {
    flex-direction: column;
    align-items: stretch;
  }

  .quiz-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}
</style>
