<template>
  <div class="scores-page">
    <div class="page-header-bar">
      <div>
        <h2 class="page-h2">考试成绩</h2>
        <p class="page-sub">教官可查看本场所有学员成绩，并进入完整答卷详情</p>
      </div>
      <div class="header-actions">
        <a-select
          v-model:value="selectedExam"
          style="width: 320px"
          placeholder="请选择考试场次"
          @change="loadScores"
        >
          <a-select-option v-for="exam in examList" :key="exam.id" :value="exam.id">
            {{ exam.title }}
          </a-select-option>
        </a-select>
        <permissions-tooltip
          :allowed="canExportScores"
          tips="需要 GET_EXAM_SCORES 权限"
          v-slot="{ disabled }"
        >
          <a-button type="primary" ghost :disabled="disabled" @click="exportCSV">
            <DownloadOutlined /> 导出成绩
          </a-button>
        </permissions-tooltip>
      </div>
    </div>

    <div class="score-kpis">
      <div class="skpi-card">
        <div class="skpi-value">{{ filteredRecords.length }}<span class="skpi-unit">人</span></div>
        <div class="skpi-label">参考人数</div>
      </div>
      <div class="skpi-card">
        <div class="skpi-value">{{ avgScore }}<span class="skpi-unit">分</span></div>
        <div class="skpi-label">平均分</div>
      </div>
      <div class="skpi-card">
        <div class="skpi-value">{{ bestScore }}<span class="skpi-unit">分</span></div>
        <div class="skpi-label">最高分</div>
      </div>
      <div class="skpi-card">
        <div class="skpi-value">{{ passRate }}<span class="skpi-unit">%</span></div>
        <div class="skpi-label">通过率</div>
      </div>
    </div>

    <div class="detail-table-card">
      <div class="table-header">
        <h3 class="table-title">学员成绩总表</h3>
        <a-input-search
          v-model:value="searchText"
          allow-clear
          placeholder="搜索姓名/账号"
          style="width: 260px"
        />
      </div>
      <a-table
        :columns="columns"
        :data-source="filteredRecords"
        :loading="loading"
        row-key="id"
        :pagination="{ pageSize: 10 }"
        size="middle"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'student'">
            {{ record.userNickname || record.userName || `学员#${record.userId}` }}
          </template>
          <template v-if="column.key === 'score'">
            <span :class="scoreClass(record.score)">{{ record.score }}</span>
          </template>
          <template v-if="column.key === 'accuracy'">
            {{ accuracy(record) }}%
          </template>
          <template v-if="column.key === 'result'">
            <a-tag :color="record.result === 'pass' ? 'green' : 'red'">
              {{ record.result === 'pass' ? '通过' : '未通过' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'endTime'">
            {{ formatDateTime(record.endTime) }}
          </template>
          <template v-if="column.key === 'duration'">
            {{ record.duration || 0 }} 分钟
          </template>
          <template v-if="column.key === 'action'">
            <a-button type="link" size="small" @click="openDetail(record)">查看答卷</a-button>
          </template>
        </template>
      </a-table>
    </div>

    <a-modal
      v-model:open="detailVisible"
      :title="detailTitle"
      :footer="null"
      :width="980"
      destroy-on-close
    >
      <div v-if="detailRecord">
        <a-descriptions :column="4" bordered size="small" style="margin-bottom: 12px">
          <a-descriptions-item label="学员">
            {{ detailRecord.userNickname || detailRecord.userName || `学员#${detailRecord.userId}` }}
          </a-descriptions-item>
          <a-descriptions-item label="成绩">{{ detailRecord.score }} 分</a-descriptions-item>
          <a-descriptions-item label="结果">
            {{ detailRecord.result === 'pass' ? '通过' : '未通过' }}
          </a-descriptions-item>
          <a-descriptions-item label="用时">{{ detailRecord.duration || 0 }} 分钟</a-descriptions-item>
          <a-descriptions-item label="作答情况">
            {{ detailRecord.correctCount || 0 }} 对 / {{ detailRecord.wrongCount || 0 }} 错
          </a-descriptions-item>
          <a-descriptions-item label="提交时间" :span="3">
            {{ formatDateTime(detailRecord.endTime) }}
          </a-descriptions-item>
        </a-descriptions>

        <a-table
          :columns="questionColumns"
          :data-source="detailQuestionRows"
          row-key="questionId"
          size="small"
          :pagination="{ pageSize: 8 }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'type'">
              {{ questionTypeText(record.type) }}
            </template>
            <template v-if="column.key === 'isCorrect'">
              <a-tag :color="record.isCorrect ? 'green' : 'red'">
                {{ record.isCorrect ? '正确' : '错误' }}
              </a-tag>
            </template>
            <template v-if="column.key === 'myAnswer'">
              {{ formatAnswer(record.myAnswer) }}
            </template>
            <template v-if="column.key === 'answer'">
              {{ formatAnswer(record.answer) }}
            </template>
          </template>
        </a-table>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { DownloadOutlined } from '@ant-design/icons-vue'
import { getExams, getExamScores } from '@/api/exam'
import { useAuthStore } from '@/stores/auth'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

const authStore = useAuthStore()
const canExportScores = computed(() => authStore.hasPermission('GET_EXAM_SCORES'))

const loading = ref(false)
const examList = ref([])
const selectedExam = ref(null)
const records = ref([])
const searchText = ref('')

const detailVisible = ref(false)
const detailRecord = ref(null)

const columns = [
  { title: '学员', key: 'student', width: 120 },
  { title: '成绩', key: 'score', width: 80, sorter: (a, b) => (a.score || 0) - (b.score || 0) },
  { title: '及格线', dataIndex: 'passingScore', key: 'passingScore', width: 90 },
  { title: '正确率', key: 'accuracy', width: 90 },
  { title: '考试次数', dataIndex: 'attemptNo', key: 'attemptNo', width: 90 },
  { title: '提交时间', key: 'endTime', width: 150 },
  { title: '用时', key: 'duration', width: 90 },
  { title: '结果', key: 'result', width: 90 },
  { title: '操作', key: 'action', width: 100, fixed: 'right' },
]

const questionColumns = [
  { title: '题号', dataIndex: 'questionId', key: 'questionId', width: 80 },
  { title: '题型', key: 'type', width: 90 },
  { title: '题目', dataIndex: 'content', key: 'content', ellipsis: true },
  { title: '我的答案', key: 'myAnswer', width: 120 },
  { title: '正确答案', key: 'answer', width: 120 },
  { title: '判定', key: 'isCorrect', width: 90 },
]

const filteredRecords = computed(() => {
  const keyword = searchText.value?.trim()
  if (!keyword) return records.value
  return records.value.filter((row) => {
    const name = row.userNickname || row.userName || ''
    const account = row.userName || ''
    return name.includes(keyword) || account.includes(keyword)
  })
})

const avgScore = computed(() => {
  const list = filteredRecords.value
  if (!list.length) return 0
  return (list.reduce((sum, row) => sum + (row.score || 0), 0) / list.length).toFixed(1)
})

const bestScore = computed(() => {
  if (!filteredRecords.value.length) return 0
  return Math.max(...filteredRecords.value.map((row) => row.score || 0))
})

const passRate = computed(() => {
  const list = filteredRecords.value
  if (!list.length) return 0
  const passCount = list.filter((row) => row.result === 'pass').length
  return ((passCount / list.length) * 100).toFixed(1)
})

const detailTitle = computed(() => {
  if (!detailRecord.value) return '学员答卷详情'
  const name = detailRecord.value.userNickname || detailRecord.value.userName || `学员#${detailRecord.value.userId}`
  return `${name} · 完整答卷`
})

const detailQuestionRows = computed(() => {
  return (detailRecord.value?.questionDetails || []).map((item) => ({
    questionId: item.questionId,
    type: item.type,
    content: item.content,
    myAnswer: item.myAnswer,
    answer: item.answer,
    isCorrect: item.isCorrect,
  }))
})

function accuracy(record) {
  const correct = record.correctCount || 0
  const wrong = record.wrongCount || 0
  const total = correct + wrong
  if (!total) return 0
  return Math.round((correct / total) * 100)
}

function scoreClass(score) {
  if (score >= 80) return 'score-good'
  if (score >= 60) return 'score-ok'
  return 'score-fail'
}

function questionTypeText(type) {
  return {
    single: '单选题',
    multi: '多选题',
    judge: '判断题',
  }[type] || type
}

function formatAnswer(answer) {
  if (answer === undefined || answer === null || answer === '') return '未作答'
  if (Array.isArray(answer)) return answer.join('、')
  return String(answer)
}

function formatDateTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function loadExamList() {
  try {
    const res = await getExams({ size: 100 })
    examList.value = res.items || []
    if (examList.value.length && !selectedExam.value) {
      selectedExam.value = examList.value[0].id
      await loadScores()
    }
  } catch {
    message.error('加载考试场次失败')
  }
}

function normalizeRecord(item) {
  return {
    id: item.id,
    examId: item.examId,
    userId: item.userId,
    userName: item.userName,
    userNickname: item.userNickname,
    score: item.score || 0,
    result: item.result || 'fail',
    passingScore: item.passingScore || 60,
    attemptNo: item.attemptNo || 1,
    correctCount: item.correctCount || 0,
    wrongCount: item.wrongCount || 0,
    duration: item.duration || 0,
    endTime: item.endTime,
    questionDetails: item.questionDetails || [],
  }
}

async function loadScores() {
  if (!selectedExam.value) return
  loading.value = true
  try {
    const res = await getExamScores(selectedExam.value, { size: -1 })
    records.value = (res.items || []).map(normalizeRecord)
  } catch {
    message.error('加载成绩失败')
  } finally {
    loading.value = false
  }
}

function openDetail(record) {
  detailRecord.value = record
  detailVisible.value = true
}

function exportCSV() {
  if (!canExportScores.value) return
  const header = ['学员', '成绩', '及格线', '正确率', '结果', '考试次数', '提交时间', '用时(分钟)']
  const rows = filteredRecords.value.map((row) => [
    row.userNickname || row.userName || `学员#${row.userId}`,
    row.score,
    row.passingScore,
    `${accuracy(row)}%`,
    row.result === 'pass' ? '通过' : '未通过',
    row.attemptNo,
    formatDateTime(row.endTime),
    row.duration || 0,
  ])
  const csv = '\uFEFF' + [header, ...rows].map((line) => line.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `考试成绩_${new Date().toLocaleDateString('zh-CN')}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  loadExamList()
})
</script>

<style scoped>
.scores-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 12px;
}

.page-h2 {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 700;
}

.page-sub {
  margin: 0;
  color: #8c8c8c;
  font-size: 13px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.score-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.skpi-card {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 18px 12px;
  text-align: center;
}

.skpi-value {
  font-size: 30px;
  line-height: 1.2;
  font-weight: 700;
  color: #003087;
}

.skpi-unit {
  font-size: 14px;
  margin-left: 2px;
}

.skpi-label {
  margin-top: 6px;
  color: #8c8c8c;
  font-size: 13px;
}

.detail-table-card {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 16px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.table-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.score-good {
  color: #52c41a;
  font-weight: 700;
}

.score-ok {
  color: #fa8c16;
  font-weight: 700;
}

.score-fail {
  color: #ff4d4f;
  font-weight: 700;
}

@media (max-width: 992px) {
  .score-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
