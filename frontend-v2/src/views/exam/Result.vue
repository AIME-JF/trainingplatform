<template>
  <div class="page-content result-page">
    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" />
    </div>

    <!-- ===== 学员视角：自己的考试成绩 ===== -->
    <template v-else-if="isStudentView && result">
      <!-- 结果头部 -->
      <div class="section-block result-hero" :class="{ passed: isPassed, failed: !isPassed }">
        <div class="hero-left">
          <div class="hero-icon">
            <CheckCircleOutlined v-if="isPassed" />
            <CloseCircleOutlined v-else />
          </div>
          <div class="hero-text">
            <div class="hero-title">{{ isPassed ? '考试通过' : '未通过' }}</div>
            <div class="hero-exam">{{ result.exam_title || '考试成绩' }}</div>
          </div>
        </div>
        <div class="hero-right">
          <div class="score-big">{{ result.score || 0 }}</div>
          <div class="score-label">及格线 {{ result.passing_score || 60 }} 分</div>
        </div>
      </div>

      <div class="divider" />

      <!-- 基本信息 -->
      <div class="section-block info-grid">
        <div class="info-item">
          <span class="info-label">提交时间</span>
          <span class="info-value">{{ formatDateTime(result.end_time) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">用时</span>
          <span class="info-value">{{ formatDuration(result.duration) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">答题情况</span>
          <span class="info-value">{{ result.correct_count || 0 }} 答对 / {{ result.wrong_count || 0 }} 答错</span>
        </div>
        <div class="info-item">
          <span class="info-label">正确率</span>
          <span class="info-value">{{ accuracyPercent }}%</span>
        </div>
        <div class="info-item">
          <span class="info-label">考试次数</span>
          <span class="info-value">第 {{ result.attempt_no || 1 }} 次</span>
        </div>
      </div>

      <div class="divider" />

      <!-- 答题回顾：所有题目 -->
      <div v-if="allQuestionDetails.length > 0" class="section-block review-section">
        <div class="section-header">
          <FileTextOutlined /> 答题回顾 · {{ allQuestionDetails.length }} 题
        </div>

        <div
          v-for="(q, index) in allQuestionDetails"
          :key="q.question_id"
          class="review-block"
          :class="{ correct: q.is_correct, wrong: !q.is_correct }"
        >
          <div class="review-top">
            <span class="review-num" :class="{ 'num-correct': q.is_correct, 'num-wrong': !q.is_correct }">
              {{ index + 1 }}
            </span>
            <a-tag class="type-tag" :class="getQuestionTypeClass(q.type)">{{ getQuestionTypeText(q.type) }}</a-tag>
            <span class="review-score" :class="q.is_correct ? 'correct-text' : 'wrong-text'">
              {{ q.is_correct ? '+' : '-' }}{{ q.score || 0 }}分
            </span>
            <span class="review-status">
              <CheckCircleOutlined v-if="q.is_correct" class="icon-correct" />
              <CloseCircleOutlined v-else class="icon-wrong" />
            </span>
          </div>

          <div class="review-question">{{ q.content }}</div>

          <div class="answer-rows">
            <div class="answer-row">
              <span class="answer-key">你的答案</span>
              <span class="answer-val" :class="q.is_correct ? 'correct-text' : 'wrong-text'">
                {{ formatAnswer(q.my_answer) || '未作答' }}
              </span>
            </div>
            <div class="answer-row">
              <span class="answer-key">正确答案</span>
              <span class="answer-val correct-text">{{ formatAnswer(q.answer) }}</span>
            </div>
          </div>

          <div v-if="q.explanation" class="explanation-row">
            <BulbOutlined /> {{ q.explanation }}
          </div>
        </div>
      </div>

      <a-empty v-else-if="isPassed" class="all-correct">
        <template #description><span>恭喜您全部答对，继续保持！</span></template>
      </a-empty>

      <div class="divider" />

      <!-- 操作 -->
      <div class="section-block action-row">
        <a-button type="primary" ghost size="large" @click="openPaperPreview">
          <FileTextOutlined /> 查看试卷题目
        </a-button>
        <a-button size="large" @click="router.push('/exam/list')">
          <RollbackOutlined /> 返回考试列表
        </a-button>
        <a-button v-if="!isPassed" type="primary" size="large" @click="router.push({ path: `/exam/do/${examId}`, query: { kind: examKind } })">
          <RedoOutlined /> 重新考试
        </a-button>
      </div>
    </template>

    <!-- ===== 教官视角：所有学员成绩表格 ===== -->
    <template v-else-if="!isStudentView">
      <!-- 深色头部横幅 -->
      <header class="instructor-header">
        <div class="instructor-header-body">
          <div class="instructor-header-left">
            <button class="back-btn-light" @click="router.push('/exam/list')">
              <LeftOutlined /> 返回考试列表
            </button>
            <h1 class="instructor-title">
              <FileTextOutlined />
              {{ examTitle }}
            </h1>
            <div class="instructor-meta-row">
              <span class="meta-chip">
                <TeamOutlined class="chip-icon-ant" />
                共 {{ totalCount }} 名学员
              </span>
              <span class="meta-chip">
                <SafetyCertificateOutlined class="chip-icon-ant" />
                培训班内考试
              </span>
            </div>
          </div>
          <div class="instructor-header-right">
            <a-button class="preview-paper-btn" size="large" @click="openPaperPreview">
              <FileTextOutlined /> 查看试卷题目
            </a-button>
            <div class="stat-box">
              <div class="stat-box-num">{{ averageScore }}</div>
              <div class="stat-box-label">平均分</div>
            </div>
            <div class="stat-box stat-box--pass">
              <div class="stat-box-num">{{ passRate }}%</div>
              <div class="stat-box-label">及格率</div>
            </div>
            <div class="stat-box">
              <div class="stat-box-num">{{ totalCount }}</div>
              <div class="stat-box-label">学员总数</div>
            </div>
          </div>
        </div>
      </header>

      <div v-if="scoresLoading" class="loading-wrapper">
        <a-spin size="large" />
      </div>

      <template v-else-if="studentScores.length > 0">
        <div class="scores-card">
          <a-table
            :columns="scoreColumns"
            :data-source="studentScores"
            :pagination="false"
            row-key="id"
            size="middle"
            :scroll="{ x: 800 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'user'">
                <div class="user-cell">
                  <span class="user-name">{{ record.user_nickname || record.user_name || '匿名用户' }}</span>
                  <span class="user-id">ID: {{ record.user_id }}</span>
                </div>
              </template>
              <template v-else-if="column.key === 'result'">
                <a-tag :color="record.result === 'pass' ? 'success' : 'error'" class="result-tag">
                  {{ record.result === 'pass' ? '及格' : '不及格' }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'accuracy'">
                <span>{{ record.correct_count || 0 }} / {{ (record.correct_count || 0) + (record.wrong_count || 0) }}</span>
              </template>
              <template v-else-if="column.key === 'duration'">
                <span>{{ formatDuration(record.duration) }}</span>
              </template>
              <template v-else-if="column.key === 'action'">
                <a-button type="link" size="small" @click="viewStudentDetail(record)">
                  查看详情
                </a-button>
              </template>
            </template>
          </a-table>
        </div>
      </template>

      <a-empty v-else description="暂无学员成绩" class="empty-block" />
    </template>

    <a-empty v-else description="暂无考试结果" />

    <!-- 试卷题目预览 -->
    <a-modal
      v-model:open="paperPreviewVisible"
      :title="paperPreviewTitle"
      width="860px"
      :footer="null"
      class="paper-preview-modal"
    >
      <div v-if="paperPreviewLoading" class="loading-wrapper">
        <a-spin size="large" />
      </div>
      <div v-else class="paper-preview-content">
        <div class="paper-preview-summary">
          <span>共 {{ paperQuestionDetails.length }} 题</span>
          <span v-if="paperMeta.totalScore">总分 {{ paperMeta.totalScore }} 分</span>
          <span v-if="paperMeta.duration">时长 {{ paperMeta.duration }} 分钟</span>
          <span v-if="paperMeta.passingScore">及格 {{ paperMeta.passingScore }} 分</span>
        </div>

        <a-empty v-if="paperQuestionDetails.length === 0" description="暂无试卷题目" />

        <div v-else class="question-list">
          <div
            v-for="(q, index) in paperQuestionDetails"
            :key="`${q.id}-${index}`"
            class="question-item paper-question-item"
          >
            <div class="q-header">
              <span class="q-num">{{ index + 1 }}</span>
              <a-tag class="type-tag" :class="getQuestionTypeClass(q.type)">
                {{ getQuestionTypeText(q.type) }}
              </a-tag>
              <span class="q-score preview-score"> {{ q.score || 0 }}分 </span>
            </div>
            <div class="q-content">{{ q.content }}</div>

            <div v-if="getQuestionOptions(q).length > 0" class="paper-options">
              <div v-for="option in getQuestionOptions(q)" :key="`${q.id}-${option.key}`" class="paper-option-row">
                <span class="paper-option-key">{{ option.key }}</span>
                <span class="paper-option-text">{{ option.value }}</span>
              </div>
            </div>

            <div class="q-answers">
              <div class="q-answer-row">
                <span class="answer-label">正确答案</span>
                <span class="answer-val correct-text">{{ formatAnswer(q.answer) || '暂无答案' }}</span>
              </div>
            </div>

            <div v-if="q.knowledge_points?.length" class="paper-kp-row">
              <span class="answer-label">知识点</span>
              <span class="paper-kp-tags">
                <a-tag v-for="kp in q.knowledge_points" :key="kp" class="knowledge-tag">{{ kp }}</a-tag>
              </span>
            </div>

            <div v-if="q.explanation" class="q-explanation">
              <BulbOutlined /> {{ q.explanation }}
            </div>
          </div>
        </div>
      </div>
    </a-modal>

    <!-- 学员答题详情弹窗 -->
    <a-modal
      v-model:open="detailModalVisible"
      :title="`学员答题详情 — ${selectedRecord?.user_nickname || selectedRecord?.user_name || ''}`"
      width="720px"
      :footer="null"
      class="detail-modal"
    >
      <div v-if="selectedRecord" class="detail-modal-content">
        <div class="detail-summary">
          <div class="detail-stat">
            <span class="stat-label">得分</span>
            <span class="stat-value" :class="selectedRecord.result === 'pass' ? 'pass' : 'fail'">
              {{ selectedRecord.score || 0 }} / {{ selectedRecord.passing_score || 0 }}
            </span>
          </div>
          <div class="detail-stat">
            <span class="stat-label">结果</span>
            <span class="stat-value" :class="selectedRecord.result === 'pass' ? 'pass' : 'fail'">
              {{ selectedRecord.result === 'pass' ? '及格' : '不及格' }}
            </span>
          </div>
          <div class="detail-stat">
            <span class="stat-label">用时</span>
            <span class="stat-value">{{ formatDuration(selectedRecord.duration) }}</span>
          </div>
          <div class="detail-stat">
            <span class="stat-label">正确率</span>
            <span class="stat-value">
              {{ Math.round(((selectedRecord.correct_count || 0) / ((selectedRecord.correct_count || 0) + (selectedRecord.wrong_count || 0))) * 100) || 0 }}%
            </span>
          </div>
        </div>

        <div class="question-list">
          <div
            v-for="(q, index) in studentQuestionDetails"
            :key="q.question_id"
            class="question-item"
            :class="{ correct: q.is_correct, wrong: !q.is_correct }"
          >
            <div class="q-header">
              <span class="q-num">{{ index + 1 }}</span>
              <a-tag class="type-tag" :class="getQuestionTypeClass(q.type)">
                {{ getQuestionTypeText(q.type) }}
              </a-tag>
              <span class="q-score" :class="q.is_correct ? 'correct-text' : 'wrong-text'">
                {{ q.is_correct ? '+' : '-' }}{{ q.score || 0 }}分
              </span>
              <span class="q-status">
                <CheckCircleOutlined v-if="q.is_correct" class="icon-correct" />
                <CloseCircleOutlined v-else class="icon-wrong" />
              </span>
            </div>
            <div class="q-content">{{ q.content }}</div>
            <div class="q-answers">
              <div class="q-answer-row">
                <span class="answer-label">学员答案</span>
                <span class="answer-val" :class="q.is_correct ? 'correct-text' : 'wrong-text'">
                  {{ formatAnswer(q.my_answer) || '未作答' }}
                </span>
              </div>
              <div class="q-answer-row">
                <span class="answer-label">正确答案</span>
                <span class="answer-val correct-text">{{ formatAnswer(q.answer) }}</span>
              </div>
            </div>
            <div v-if="q.explanation" class="q-explanation">
              <BulbOutlined /> {{ q.explanation }}
            </div>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import {
  BulbOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  FileTextOutlined,
  LeftOutlined,
  RedoOutlined,
  RollbackOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
  WarningOutlined,
} from '@ant-design/icons-vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import type {
  AdmissionExamDetailResponse,
  AdmissionExamRecordResponse,
  ExamDetailResponse,
  ExamQuestionSnapshotResponse,
  ExamRecordResponse,
} from '@/api/generated/model'
import {
  getAdmissionExamApiV1ExamsAdmissionExamIdGet,
  getAdmissionExamResultApiV1ExamsAdmissionExamIdResultGet,
  getAdmissionExamScoresApiV1ExamsAdmissionExamIdScoresGet,
  getExamApiV1ExamsExamIdGet,
  getExamResultApiV1ExamsExamIdResultGet,
  getExamScoresApiV1ExamsExamIdScoresGet,
} from '@/api/generated/exam-management/exam-management'
import { resolveExamKind, type ExamKind } from './examDisplay'
import type { TableColumnType } from 'ant-design-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const scoresLoading = ref(false)
const result = ref<ExamRecordResponse | AdmissionExamRecordResponse | null>(null)
const isStudentView = computed(() => authStore.isStudent)

// 教官视角数据
const studentScores = ref<ExamRecordResponse[]>([])
const totalCount = ref(0)
const examTitle = ref('')
const detailModalVisible = ref(false)
const selectedRecord = ref<ExamRecordResponse | AdmissionExamRecordResponse | null>(null)
const studentQuestionDetails = ref<Array<{
  question_id: number
  type: string
  content: string
  my_answer?: unknown
  answer?: unknown
  is_correct: boolean
  explanation?: string | null
  score?: number
}>>([])
const paperPreviewVisible = ref(false)
const paperPreviewLoading = ref(false)
const paperQuestionDetails = ref<ExamQuestionSnapshotResponse[]>([])
const paperPreviewTitle = ref('试卷题目')
const paperMeta = ref({
  totalScore: 0,
  duration: 0,
  passingScore: 0,
})

function getKindFromQuery(): ExamKind {
  const kind = route.query.kind
  if (Array.isArray(kind)) {
    return resolveExamKind(kind[0], 'training')
  }
  return resolveExamKind(kind, 'training')
}

const examKind = ref<ExamKind>(getKindFromQuery())
watch(() => route.query.kind, () => {
  examKind.value = getKindFromQuery()
})

const examId = computed(() => Number(route.params.id))

const isPassed = computed(() => {
  if (!result.value) return false
  return result.value.result === 'pass' || result.value.score! >= (result.value.passing_score || 0)
})

const accuracyPercent = computed(() => {
  if (!result.value) return 0
  const correct = result.value.correct_count || 0
  const wrong = result.value.wrong_count || 0
  const total = correct + wrong
  if (total === 0) return 0
  return Math.round((correct / total) * 100)
})

const wrongQuestionDetails = computed(() => result.value?.wrong_question_details || [])
const allQuestionDetails = computed(() => result.value?.question_details || [])

const averageScore = computed(() => {
  if (studentScores.value.length === 0) return 0
  const total = studentScores.value.reduce((sum, r) => sum + (r.score || 0), 0)
  return Math.round(total / studentScores.value.length)
})

const passRate = computed(() => {
  if (studentScores.value.length === 0) return 0
  const passCount = studentScores.value.filter(r => r.result === 'pass').length
  return Math.round((passCount / studentScores.value.length) * 100)
})

const scoreColumns: TableColumnType[] = [
  { title: '学员', key: 'user', width: 180, fixed: 'left' },
  { title: '分数', dataIndex: 'score', key: 'score', width: 80 },
  { title: '结果', key: 'result', width: 80 },
  { title: '用时', key: 'duration', width: 100 },
  { title: '正确率', key: 'accuracy', width: 100 },
  { title: '考试次数', dataIndex: 'attempt_no', key: 'attempt_no', width: 100 },
  { title: '操作', key: 'action', width: 100, fixed: 'right' },
]

onMounted(async () => {
  if (isStudentView.value) {
    await fetchResult()
  } else {
    await fetchAllScores()
  }
})

async function fetchResult() {
  loading.value = true
  try {
    const currentKind = examKind.value
    try {
      result.value = currentKind === 'admission'
        ? await getAdmissionExamResultApiV1ExamsAdmissionExamIdResultGet(examId.value)
        : await getExamResultApiV1ExamsExamIdResultGet(examId.value)
    } catch {
      const fallbackKind = currentKind === 'admission' ? 'training' : 'admission'
      try {
        result.value = fallbackKind === 'admission'
          ? await getAdmissionExamResultApiV1ExamsAdmissionExamIdResultGet(examId.value)
          : await getExamResultApiV1ExamsExamIdResultGet(examId.value)
        examKind.value = fallbackKind
      } catch {
        void message.warning('考试记录不存在，即将返回考试列表')
        await router.replace('/exam/list')
        return
      }
    }
  } finally {
    loading.value = false
  }
}

async function fetchAllScores() {
  scoresLoading.value = true
  try {
    const response = examKind.value === 'admission'
      ? await getAdmissionExamScoresApiV1ExamsAdmissionExamIdScoresGet(examId.value, { size: -1 })
      : await getExamScoresApiV1ExamsExamIdScoresGet(examId.value, { size: -1 })

    studentScores.value = response?.items || []
    totalCount.value = response?.total || studentScores.value.length
    examTitle.value = studentScores.value[0]?.exam_title || '考试成绩'
  } catch {
    studentScores.value = []
    totalCount.value = 0
  } finally {
    scoresLoading.value = false
  }
}

function viewStudentDetail(record: ExamRecordResponse | AdmissionExamRecordResponse) {
  selectedRecord.value = record
  studentQuestionDetails.value = (record.question_details || record.wrong_question_details || []) as any
  detailModalVisible.value = true
}

async function openPaperPreview() {
  paperPreviewVisible.value = true
  paperPreviewLoading.value = true
  try {
    const detail = examKind.value === 'admission'
      ? await getAdmissionExamApiV1ExamsAdmissionExamIdGet(examId.value)
      : await getExamApiV1ExamsExamIdGet(examId.value)

    const examDetail = detail as AdmissionExamDetailResponse | ExamDetailResponse
    paperPreviewTitle.value = `${examDetail.paper_title || examDetail.title || '试卷题目'}`
    paperQuestionDetails.value = examDetail.questions || []
    paperMeta.value = {
      totalScore: Number(examDetail.total_score || 0),
      duration: Number(examDetail.duration || 0),
      passingScore: Number(examDetail.passing_score || 0),
    }
  } catch (error) {
    paperQuestionDetails.value = []
    message.error(error instanceof Error ? error.message : '试卷题目加载失败')
  } finally {
    paperPreviewLoading.value = false
  }
}

function formatDuration(minutes?: number) {
  if (minutes === undefined || minutes === null) return '-'
  return `${minutes} 分钟`
}

function formatDateTime(time?: string | null) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

function formatAnswer(answer?: unknown) {
  if (answer === undefined || answer === null) return ''
  if (Array.isArray(answer)) return answer.join('、')
  return String(answer)
}

function getQuestionTypeText(type?: string) {
  switch (type) {
    case 'single': return '单选题'
    case 'multi': return '多选题'
    case 'judge': return '判断题'
    default: return type || '未知'
  }
}

function getQuestionTypeClass(type?: string) {
  switch (type) {
    case 'single': return 'type-single'
    case 'multi': return 'type-multi'
    case 'judge': return 'type-judge'
    default: return 'type-default'
  }
}

function getQuestionOptions(question: ExamQuestionSnapshotResponse) {
  if (question.type === 'judge') {
    return [
      { key: 'A', value: '正确' },
      { key: 'B', value: '错误' },
    ]
  }
  const opts = question.options
  if (!opts || !Array.isArray(opts)) return []
  return opts.map((item) => {
    if (item && typeof item === 'object' && !Array.isArray(item)) {
      const record = item as Record<string, unknown>
      if ('key' in record) {
        const key = String(record.key ?? '').trim()
        const value = String(record.text ?? record.value ?? '').trim()
        if (key) return { key, value: value || key }
      }
      const entry = Object.entries(record).find(([k]) => k !== 'key' && k !== 'text' && k !== 'value')
      if (entry) {
        return { key: String(entry[0]), value: String(entry[1] ?? '') }
      }
    }
    return { key: '', value: '' }
  }).filter((item) => item.key)
}
</script>

<style scoped>
.result-page {
  padding: 20px;
  max-width: 100%;
}

.loading-wrapper {
  padding: 80px 0;
  text-align: center;
}

.empty-block {
  padding: 80px 0;
}

.divider {
  height: 1px;
  background: var(--v2-border);
  margin: 0;
}

.section-block {
  padding: 24px 28px;
  background: var(--v2-bg-card);
}

.section-block:first-child {
  border-radius: 20px 20px 0 0;
}

.section-block:last-child {
  border-radius: 0 0 20px 20px;
}

.info-grid {
  display: flex;
  gap: 0;
}

.info-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 0 16px;
  border-right: 1px solid var(--v2-border);
}

.info-item:first-child {
  padding-left: 0;
}

.info-item:last-child {
  border-right: none;
}

.info-label {
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.info-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
}

.result-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
}

.result-hero.passed {
  background: linear-gradient(135deg, #2DA44E 0%, #1a7a37 100%);
}

.result-hero.failed {
  background: linear-gradient(135deg, #FF3B30 0%, #d42a1f 100%);
}

.hero-left {
  display: flex;
  align-items: center;
  gap: 18px;
}

.hero-icon {
  font-size: 52px;
}

.hero-title {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.hero-exam {
  font-size: 14px;
  opacity: 0.85;
  margin-top: 4px;
}

.hero-right {
  text-align: right;
}

.score-big {
  font-size: 64px;
  font-weight: 700;
  line-height: 1;
}

.score-label {
  font-size: 14px;
  opacity: 0.85;
  margin-top: 6px;
}

.review-section {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 17px;
  font-weight: 600;
  color: var(--v2-primary);
  margin-bottom: 18px;
}

.review-block {
  padding: 16px 0;
  border-top: 1px solid var(--v2-border);
}

.review-block:first-of-type {
  border-top: none;
  padding-top: 0;
}

.review-block.correct {
  /* correct state - no extra styling needed */
}

.review-block.wrong {
  /* wrong state - no extra styling needed */
}

.review-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.review-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.review-num.num-correct {
  background: var(--v2-success);
  color: #fff;
}

.review-num.num-wrong {
  background: var(--v2-danger);
  color: #fff;
}

.type-tag {
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.review-score {
  margin-left: auto;
  font-weight: 700;
  font-size: 14px;
}

.review-score.correct-text {
  color: var(--v2-success);
}

.review-score.wrong-text {
  color: var(--v2-danger);
}

.review-status {
  display: flex;
  align-items: center;
}

.icon-correct {
  color: var(--v2-success);
  font-size: 18px;
}

.icon-wrong {
  color: var(--v2-danger);
  font-size: 18px;
}

.review-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.review-question {
  font-size: 15px;
  line-height: 1.8;
  color: var(--v2-text-primary);
}

.answer-rows {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 10px;
  padding: 12px 16px;
}

.answer-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.answer-key {
  font-size: 13px;
  color: var(--v2-text-secondary);
  width: 68px;
  flex-shrink: 0;
}

.answer-val {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.6;
}

.wrong-val {
  color: var(--v2-danger);
}

.correct-val {
  color: var(--v2-success);
}

.explanation-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(75, 110, 245, 0.06);
  border-radius: 10px;
  font-size: 14px;
  color: var(--v2-primary);
  line-height: 1.8;
}

.all-correct {
  background: var(--v2-bg-card);
  border-radius: 20px;
  padding: 40px 0;
}

.action-row {
  display: flex;
  gap: 14px;
  justify-content: center;
}

.action-row :deep(.ant-btn) {
  border-radius: 12px;
  height: 44px;
  padding: 0 28px;
  font-size: 14px;
  font-weight: 600;
}

.preview-paper-btn {
  border-radius: 12px;
  height: 48px;
  padding: 0 18px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.12);
}

.preview-paper-btn:hover {
  background: rgba(255, 255, 255, 0.18);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
}

.top-bar {
  margin-bottom: 16px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 999px;
  border: 1px solid var(--v2-border);
  background: var(--v2-bg-card);
  color: var(--v2-text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  border-color: var(--v2-primary);
  color: var(--v2-primary);
}

.scores-header {
  border-radius: 20px 20px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.scores-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--v2-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.scores-meta {
  font-size: 14px;
  color: var(--v2-text-secondary);
}

.scores-meta strong {
  color: var(--v2-primary);
}

.scores-meta .sep {
  margin: 0 8px;
  color: var(--v2-border);
}

.scores-card {
  background: var(--v2-bg-card);
  border-radius: 0 0 20px 20px;
  overflow: hidden;
}

.scores-card :deep(.ant-table) {
  background: transparent;
}

.scores-card :deep(.ant-table-thead > tr > th) {
  background: var(--v2-bg);
  color: var(--v2-text-secondary);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--v2-border);
}

.scores-card :deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid var(--v2-border-light);
}

.scores-card :deep(.ant-table-tbody > tr:hover > td) {
  background: var(--v2-bg);
}

/* ===== 教官视图：深色头部 ===== */
.instructor-header {
  background: var(--v2-bg-header);
  padding: 24px 28px 20px;
  border-radius: 20px 20px 0 0;
  margin-top: 0;
}

.instructor-header-body {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}

.instructor-header-left {
  flex: 1;
  min-width: 0;
}

.back-btn-light {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.75);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 12px;
}

.back-btn-light:hover {
  background: rgba(255, 255, 255, 0.14);
  border-color: rgba(255, 255, 255, 0.3);
  color: #fff;
}

.instructor-title {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  line-height: 1.2;
}

.instructor-meta-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.chip-icon-ant {
  font-size: 13px;
}

.instructor-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.stat-box {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: var(--v2-radius);
  padding: 12px 20px;
  text-align: center;
  min-width: 90px;
  transition: background 0.2s;
}

.stat-box:hover {
  background: rgba(255, 255, 255, 0.12);
}

.stat-box--pass {
  border-color: rgba(52, 199, 89, 0.3);
  background: rgba(52, 199, 89, 0.1);
}

.stat-box-num {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-box--pass .stat-box-num {
  color: #6EE49A;
}

.stat-box-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.user-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-weight: 600;
  color: var(--v2-text-primary);
}

.user-id {
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.result-tag {
  font-weight: 600;
}

.detail-modal-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.paper-preview-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.paper-preview-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--v2-bg);
  color: var(--v2-text-secondary);
  font-size: 13px;
}

.detail-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding: 16px;
  background: var(--v2-bg);
  border-radius: 12px;
}

.detail-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.detail-stat .stat-label {
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.detail-stat .stat-value {
  font-size: 20px;
  font-weight: 700;
}

.detail-stat .stat-value.pass {
  color: var(--v2-success);
}

.detail-stat .stat-value.fail {
  color: var(--v2-danger);
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 480px;
  overflow-y: auto;
}

.question-item {
  border: 1.5px solid var(--v2-border);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
}

.paper-question-item {
  background: var(--v2-bg-card);
}

.question-item.correct {
  border-color: rgba(52, 199, 89, 0.3);
  background: rgba(52, 199, 89, 0.04);
}

.question-item.wrong {
  border-color: rgba(255, 59, 48, 0.3);
  background: rgba(255, 59, 48, 0.04);
}

.q-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.q-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--v2-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.question-item.wrong .q-num {
  background: var(--v2-danger);
}

.q-score {
  margin-left: auto;
  font-size: 14px;
  font-weight: 700;
}

.preview-score {
  color: var(--v2-primary);
}

.correct-text {
  color: var(--v2-success);
}

.wrong-text {
  color: var(--v2-danger);
}

.q-status {
  font-size: 16px;
}

.icon-correct {
  color: var(--v2-success);
}

.icon-wrong {
  color: var(--v2-danger);
}

.q-content {
  font-size: 15px;
  line-height: 1.7;
  color: var(--v2-text-primary);
  margin-bottom: 12px;
}

.paper-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.paper-option-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.04);
}

.paper-option-key {
  width: 24px;
  height: 24px;
  border-radius: 999px;
  background: var(--v2-primary-light);
  color: var(--v2-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.paper-option-text {
  flex: 1;
  line-height: 1.7;
  color: var(--v2-text-primary);
}

.q-answers {
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 8px;
  padding: 10px 14px;
}

.q-answer-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.answer-label {
  color: var(--v2-text-secondary);
  width: 70px;
  flex-shrink: 0;
}

.paper-kp-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 10px;
}

.paper-kp-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.knowledge-tag {
  margin: 0;
  border-radius: 999px;
  background: rgba(75, 110, 245, 0.08);
  color: var(--v2-primary);
  border-color: rgba(75, 110, 245, 0.16);
}

.q-explanation {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 10px;
  padding: 8px 12px;
  background: rgba(75, 110, 245, 0.06);
  border-radius: 8px;
  font-size: 13px;
  color: var(--v2-primary);
  line-height: 1.7;
}

.type-single {
  background: #EFF6FF;
  color: #2563EB;
}

.type-multi {
  background: #F5F3FF;
  color: #7C3AED;
}

.type-judge {
  background: #F0FDF4;
  color: #16A34A;
}

.type-default {
  background: #F8FAFC;
  color: #64748B;
}

@media (max-width: 768px) {
  .result-hero {
    flex-direction: column;
    text-align: center;
    gap: 16px;
  }

  .hero-right {
    text-align: center;
  }

  .info-grid {
    flex-wrap: wrap;
    gap: 12px;
  }

  .info-item {
    flex: 0 0 calc(50% - 8px);
    border-right: none;
    padding: 0;
  }

  .action-row {
    flex-direction: column;
  }

  .detail-summary {
    grid-template-columns: repeat(2, 1fr);
  }

  .instructor-header {
    padding: 16px;
  }

  .instructor-header-body {
    flex-direction: column;
  }

  .instructor-title {
    font-size: 18px;
  }

  .instructor-header-right {
    width: 100%;
    justify-content: space-between;
    flex-wrap: wrap;
  }

  .stat-box {
    flex: 1;
    min-width: 80px;
    padding: 10px 12px;
  }

  .stat-box-num {
    font-size: 20px;
  }
}
</style>
