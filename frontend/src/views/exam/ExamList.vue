<template>
  <div class="exam-list-page">
    <div class="page-header">
      <div>
        <h2>在线考试</h2>
        <p class="page-sub">支持准入考试与班内考核，共用统一题库</p>
      </div>
      <div class="header-stats">
        <a-tag color="green">可参加 {{ joinableExams.length }} 场</a-tag>
        <a-tag color="orange">即将开始 {{ upcomingExams.length }} 场</a-tag>
      </div>
    </div>

    <a-row :gutter="[20, 20]">
      <a-col :span="12" v-for="exam in examList" :key="`${exam.kind}-${exam.id}`">
        <div class="exam-card">
          <div class="exam-card-header">
            <a-tag :color="statusColors[exam.status]">{{ statusLabels[exam.status] }}</a-tag>
            <a-tag>{{ exam.kind === 'admission' ? '准入考试' : (purposeLabels[exam.purpose] || exam.purpose) }}</a-tag>
            <a-tag>{{ exam.type === 'formal' ? '正式考核' : '测验' }}</a-tag>
          </div>

          <div class="exam-title">{{ exam.title }}</div>
          <div class="exam-desc">{{ exam.description || '暂无说明' }}</div>

          <div class="exam-info-grid">
            <div class="info-item"><ClockCircleOutlined /> {{ exam.duration }} 分钟</div>
            <div class="info-item"><FileTextOutlined /> {{ exam.questionCount || 0 }} 题</div>
            <div class="info-item"><TrophyOutlined /> 满分 {{ exam.totalScore || 0 }} 分</div>
            <div class="info-item"><CheckCircleOutlined /> 及格 {{ exam.passingScore || 0 }} 分</div>
          </div>

          <div class="exam-meta">
            <div>{{ exam.kind === 'admission' ? `适用范围：${exam.scope || '全体学员'}` : `培训班：${exam.trainingName || '独立场次'}` }}</div>
            <div>次数：{{ exam.attemptCount || 0 }}/{{ exam.maxAttempts || 1 }}</div>
            <div>时间：{{ formatDate(exam.startTime) }} ~ {{ formatDate(exam.endTime) }}</div>
          </div>

          <div class="exam-actions">
            <a-space direction="vertical" style="width: 100%">
              <a-button
                v-if="exam.canJoin"
                type="primary"
                block
                size="large"
                @click="startExam(exam)"
              >
                进入考试
              </a-button>
              <a-button
                v-if="hasExamResult(exam)"
                block
                size="large"
                @click="viewExamResult(exam)"
              >
                查看考试详情
              </a-button>
              <a-button v-if="!exam.canJoin && !hasExamResult(exam)" block size="large" disabled>
                {{ disabledLabel(exam) }}
              </a-button>
            </a-space>
          </div>
        </div>
      </a-col>
    </a-row>

    <a-empty v-if="!examList.length" description="暂无考试记录" style="margin-top:80px" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  TrophyOutlined,
} from '@ant-design/icons-vue'
import { getAdmissionExams, getExams } from '@/api/exam'

const router = useRouter()
const examList = ref([])

const statusLabels = { upcoming: '即将开始', active: '进行中', ended: '已结束' }
const statusColors = { upcoming: 'orange', active: 'green', ended: 'default' }
const purposeLabels = {
  admission: '准入考试',
  class_assessment: '班内考核',
  final_assessment: '结业考核',
  quiz: '随堂测验',
}

const joinableExams = computed(() => examList.value.filter(item => item.canJoin))
const upcomingExams = computed(() => examList.value.filter(item => item.status === 'upcoming'))

async function fetchExams() {
  try {
    const [activeTraining, upcomingTraining, endedTraining, activeAdmission, upcomingAdmission, endedAdmission] = await Promise.all([
      getExams({ size: 100, status: 'active' }),
      getExams({ size: 100, status: 'upcoming' }),
      getExams({ size: 100, status: 'ended' }),
      getAdmissionExams({ size: 100, status: 'active' }),
      getAdmissionExams({ size: 100, status: 'upcoming' }),
      getAdmissionExams({ size: 100, status: 'ended' }),
    ])
    const items = [
      ...(activeTraining.items || []),
      ...(upcomingTraining.items || []),
      ...((endedTraining.items || []).filter((item) => (item.attemptCount || 0) > 0)),
      ...(activeAdmission.items || []),
      ...(upcomingAdmission.items || []),
      ...((endedAdmission.items || []).filter((item) => (item.attemptCount || 0) > 0)),
    ]
    const unique = new Map(items.map(item => [`${item.kind}-${item.id}`, item]))
    examList.value = [...unique.values()].sort((left, right) => {
      const leftTime = left.startTime ? new Date(left.startTime).getTime() : 0
      const rightTime = right.startTime ? new Date(right.startTime).getTime() : 0
      return leftTime - rightTime
    })
  } catch (error) {
    message.error(error.message || '获取考试列表失败')
  }
}

function formatDate(value) {
  return value ? String(value).replace('T', ' ').slice(0, 16) : '未设置'
}

function disabledLabel(exam) {
  if (exam.status === 'upcoming') return '考试未开始'
  if (exam.status === 'ended') return '考试已结束'
  return '暂不可参加'
}

function hasExamResult(exam) {
  return (exam.attemptCount || 0) > 0
}

function startExam(exam) {
  Modal.confirm({
    title: '确认开始考试',
    content: `即将进入【${exam.title}】，共 ${exam.questionCount || 0} 题。`,
    onOk() {
      router.push({ name: 'DoExam', params: { id: exam.id }, query: { kind: exam.kind || 'training' } })
    },
  })
}

function viewExamResult(exam) {
  router.push({ name: 'ExamResult', params: { id: exam.id }, query: { kind: exam.kind || 'training' } })
}

onMounted(fetchExams)
</script>

<style scoped>
.exam-list-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 16px; }
.page-header h2 { margin: 0; color: #001234; }
.page-sub { margin: 6px 0 0; color: #8c8c8c; font-size: 13px; }
.header-stats { display: flex; gap: 8px; }
.exam-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 12px; padding: 18px; height: 100%; box-shadow: 0 4px 18px rgba(0, 32, 96, 0.06); }
.exam-card-header { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.exam-title { font-size: 17px; font-weight: 700; color: #1f1f1f; margin-bottom: 8px; }
.exam-desc { min-height: 38px; color: #666; font-size: 13px; }
.exam-info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 16px 0; }
.info-item { padding: 8px 10px; border-radius: 6px; background: #f7f9fc; display: flex; align-items: center; gap: 6px; font-size: 12px; color: #555; }
.exam-meta { display: flex; flex-direction: column; gap: 6px; font-size: 12px; color: #777; margin-bottom: 16px; }

@media (max-width: 768px) {
  .exam-info-grid { grid-template-columns: 1fr; }
}
</style>
