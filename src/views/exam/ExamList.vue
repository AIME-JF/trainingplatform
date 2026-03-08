<template>
  <div class="exam-list-page">
    <div class="page-header">
      <h2>在线考试</h2>
      <div class="header-stats">
        <a-tag color="blue">可参加 {{ activeExams.length }} 场</a-tag>
        <a-tag color="orange">即将开始 {{ upcomingExams.length }} 场</a-tag>
      </div>
    </div>

    <!-- 考试卡片 -->
    <a-row :gutter="[20, 20]">
      <a-col :span="12" v-for="exam in allExams" :key="exam.id">
        <div class="exam-card" :class="{ upcoming: exam.status === 'upcoming' }">
          <div class="exam-card-header" :style="{ background: getHeaderBg(exam) }">
            <div class="exam-type-badge">
              <a-tag :color="exam.type === 'formal' ? 'red' : 'cyan'" style="font-size:11px;margin:0">
                {{ exam.type === 'formal' ? '📝 正式考核' : '📋 随堂测验' }}
              </a-tag>
            </div>
            <div class="exam-status-badge">
              <a-tag :color="exam.status === 'active' ? 'green' : exam.status === 'upcoming' ? 'orange' : 'default'" style="font-size:11px;margin:0">
                {{ exam.status === 'active' ? '● 进行中' : exam.status === 'upcoming' ? '◷ 即将开始' : '已结束' }}
              </a-tag>
            </div>
            <div class="exam-icon">{{ exam.type === 'formal' ? '📝' : '📋' }}</div>
          </div>

          <div class="exam-card-body">
            <div class="exam-title">{{ exam.title }}</div>
            <div class="exam-desc">{{ exam.description }}</div>

            <div class="exam-info-grid">
              <div class="info-item">
                <ClockCircleOutlined />
                <span>{{ exam.duration }} 分钟</span>
              </div>
              <div class="info-item">
                <FileTextOutlined />
                <span>{{ exam.questionCount || exam.question_count || 0 }} 题</span>
              </div>
              <div class="info-item">
                <TrophyOutlined />
                <span>满分 {{ exam.totalScore || exam.total_score || 0 }} 分</span>
              </div>
              <div class="info-item">
                <CheckCircleOutlined />
                <span>及格 {{ exam.passingScore || exam.passing_score || 0 }} 分</span>
              </div>
            </div>

            <div class="exam-meta-row">
              <span class="exam-scope"><TeamOutlined /> {{ exam.scope || '全体人员' }}</span>
              <span class="exam-time">
                {{ (exam.startTime || exam.start_time || '').replace('T', ' ').split(' ')[0] }} ~ {{ (exam.endTime || exam.end_time || '').replace('T', ' ').split(' ')[0] }}
              </span>
            </div>

            <div class="exam-actions">
              <a-button
                v-if="exam.status === 'active'"
                type="primary"
                block
                size="large"
                @click="startExam(exam)"
              >
                <template #icon><EditOutlined /></template>
                进入考试
              </a-button>
              <a-button
                v-else
                block
                size="large"
                disabled
              >
                <template #icon><ClockCircleOutlined /></template>
                考试未开始
              </a-button>
            </div>
          </div>
        </div>
      </a-col>
    </a-row>

    <a-empty v-if="allExams.length === 0" description="暂无可参加的考试" style="margin-top:80px" />
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  ClockCircleOutlined, FileTextOutlined, TrophyOutlined,
  CheckCircleOutlined, TeamOutlined, EditOutlined,
} from '@ant-design/icons-vue'
import { getExams } from '@/api/exam'

const router = useRouter()

const loading = ref(false)
const rawExams = ref([])

const activeExams = computed(() => rawExams.value.filter(e => e.status === 'active'))
const upcomingExams = computed(() => rawExams.value.filter(e => e.status === 'upcoming'))
const allExams = computed(() => rawExams.value) // We only fetch active/upcoming from backend usually, but we filter client-side just in case

const headerColors = ['#003087', '#8b1a1a', '#1a5c2e', '#6b3a8a', '#2e4057']

const getHeaderBg = (exam) => {
  const index = exam.id % headerColors.length
  const c = headerColors[index]
  return `linear-gradient(135deg, ${c}, ${c}cc)`
}

async function fetchExams() {
  loading.value = true
  try {
    // 获取正在进行和即将开始的考试。此系统为了演示，先拉所有未结束的
    const resA = await getExams({ size: 100, status: 'active' })
    const resU = await getExams({ size: 100, status: 'upcoming' })
    rawExams.value = [...(resA.items || []), ...(resU.items || [])]
  } catch (e) {
    message.error('获取考试列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchExams()
})

const startExam = (exam) => {
  Modal.confirm({
    title: '确认开始考试',
    content: `即将进入【${exam.title}】，考试时长 ${exam.duration} 分钟，共 ${exam.questionCount || exam.question_count || 0} 题，满分 ${exam.totalScore || exam.total_score || 0} 分。开始后不可暂停，确认继续？`,
    okText: '开始考试',
    cancelText: '再想想',
    centered: true,
    onOk() {
      router.push({ name: 'DoExam', params: { id: exam.id } })
    },
  })
}
</script>

<style scoped>
.exam-list-page { padding: 0; }
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--police-primary);
}
.header-stats { display: flex; gap: 8px; }

.exam-card {
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e8e8e8;
  transition: all 0.25s;
}
.exam-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 48, 135, 0.12);
  border-color: var(--police-primary);
}
.exam-card.upcoming { opacity: 0.85; }

.exam-card-header {
  height: 90px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}
.exam-type-badge { position: absolute; top: 10px; left: 12px; }
.exam-status-badge { position: absolute; top: 10px; right: 12px; }
.exam-icon { font-size: 36px; opacity: 0.3; }

.exam-card-body { padding: 18px; }

.exam-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
  margin-bottom: 6px;
}
.exam-desc {
  font-size: 13px;
  color: #888;
  margin-bottom: 14px;
  line-height: 1.5;
}

.exam-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 14px;
}
.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #555;
  background: #f6f8fc;
  padding: 6px 10px;
  border-radius: 6px;
}

.exam-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #999;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}
.exam-scope { display: flex; align-items: center; gap: 4px; }

.exam-actions { margin-top: 4px; }
.exam-actions .ant-btn-lg {
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 8px;
  letter-spacing: 1px;
}

@media (max-width: 768px) {
  .exam-meta-row { flex-direction: column !important; align-items: flex-start !important; gap: 6px; }
  .exam-info-grid { grid-template-columns: 1fr !important; }
}
</style>
