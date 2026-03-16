<template>
  <div class="paper-detail-page">
    <div class="page-header">
      <div>
        <h2>{{ paper?.title || '试卷详情' }}</h2>
        <p class="page-sub">查看试卷题目、选项、标准答案和解析</p>
      </div>
      <a-space>
        <a-button @click="router.back()">返回</a-button>
        <a-button type="primary" @click="router.push('/paper/repository')">返回试卷仓库</a-button>
      </a-space>
    </div>

    <a-card v-if="paper" :bordered="false" style="margin-bottom: 16px">
      <a-descriptions :column="4" bordered size="small">
        <a-descriptions-item label="试卷名称">{{ paper.title }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="statusColors[paper.status] || 'default'">
            {{ statusLabels[paper.status] || paper.status }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="类型">{{ typeLabels[paper.type] || paper.type }}</a-descriptions-item>
        <a-descriptions-item label="题目数">{{ paper.questionCount || 0 }}</a-descriptions-item>
        <a-descriptions-item label="总分">{{ paper.totalScore || 0 }}</a-descriptions-item>
        <a-descriptions-item label="及格分">{{ paper.passingScore || 0 }}</a-descriptions-item>
        <a-descriptions-item label="考试时长">{{ paper.duration || 0 }} 分钟</a-descriptions-item>
        <a-descriptions-item label="发布时间">{{ formatDateTime(paper.publishedAt) }}</a-descriptions-item>
        <a-descriptions-item label="试卷说明" :span="4">
          {{ paper.description || '暂无说明' }}
        </a-descriptions-item>
      </a-descriptions>
    </a-card>

    <a-card :bordered="false">
      <template v-if="paper?.questions?.length">
        <a-collapse class="question-collapse">
          <a-collapse-panel
            v-for="(question, index) in paper.questions"
            :key="`${question.id}-${index}`"
          >
            <template #header>
              <div class="panel-header">
                <a-space>
                  <a-tag :color="typeColors[question.type] || 'default'">
                    {{ questionTypeLabels[question.type] || question.type }}
                  </a-tag>
                  <span class="panel-index">第 {{ index + 1 }} 题</span>
                  <span class="panel-score">{{ question.score || 0 }} 分</span>
                </a-space>
                <span class="panel-answer">答案：{{ formatAnswer(question) }}</span>
              </div>
            </template>

            <div class="question-content">{{ index + 1 }}. {{ question.content }}</div>
            <div v-if="question.options?.length" class="question-options">
              <div
                v-for="(option, optionIndex) in question.options"
                :key="option.key || option.value || optionIndex"
                class="question-option"
              >
                <span class="option-key">{{ option.key || option.value || String.fromCharCode(65 + optionIndex) }}.</span>
                <span>{{ option.text || option.label || option.content || option }}</span>
              </div>
            </div>
            <a-alert
              type="success"
              show-icon
              class="answer-alert"
              :message="`标准答案：${formatAnswer(question)}`"
            />
            <a-alert
              v-if="question.explanation"
              type="info"
              show-icon
              class="answer-alert"
              :message="`解析：${question.explanation}`"
            />
            <div class="question-foot">
              <span>知识点：{{ question.knowledgePoint || '未设置' }}</span>
            </div>
          </a-collapse-panel>
        </a-collapse>
      </template>
      <a-empty v-else description="该试卷暂无题目" />
    </a-card>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { getExamPaperDetail } from '@/api/exam'

const route = useRoute()
const router = useRouter()

const paper = ref(null)

const statusLabels = { draft: '草稿', published: '已发布', archived: '已归档' }
const statusColors = { draft: 'orange', published: 'green', archived: 'default' }
const typeLabels = { formal: '正式考核', quiz: '测验' }
const questionTypeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }
const typeColors = { single: 'blue', multi: 'purple', judge: 'orange' }

function formatDateTime(value) {
  if (!value) return '未设置'
  return String(value).replace('T', ' ').slice(0, 16)
}

function normalizeJudgeAnswer(answer) {
  const raw = Array.isArray(answer) ? answer[0] : answer
  if ([true, 'true', 1, '1', 'A', 'a', '正确', 'T', 't'].includes(raw)) {
    return '正确'
  }
  if ([false, 'false', 0, '0', 'B', 'b', '错误', 'F', 'f'].includes(raw)) {
    return '错误'
  }
  return raw == null ? '未设置' : String(raw)
}

function formatAnswer(question) {
  const answer = question?.answer
  if (question?.type === 'judge') {
    return normalizeJudgeAnswer(answer)
  }
  if (Array.isArray(answer)) {
    return answer.join('、')
  }
  if (answer == null || answer === '') {
    return '未设置'
  }
  return String(answer)
}

async function loadPaperDetail() {
  try {
    paper.value = await getExamPaperDetail(route.params.id)
  } catch (error) {
    message.error(error.message || '加载试卷详情失败')
    router.replace('/paper/repository')
  }
}

onMounted(loadPaperDetail)
</script>

<style scoped>
.paper-detail-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #001234;
}

.page-sub {
  margin: 6px 0 0;
  color: #8c8c8c;
  font-size: 13px;
}

.question-collapse :deep(.ant-collapse-header) {
  align-items: center !important;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  width: 100%;
  padding-right: 12px;
}

.panel-index {
  font-weight: 600;
  color: #1f1f1f;
}

.panel-score,
.panel-answer {
  color: #8c8c8c;
}

.question-content {
  line-height: 1.8;
  font-size: 15px;
  color: #1f1f1f;
  margin-bottom: 12px;
}

.question-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.question-option {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  background: #fafafa;
  border-radius: 8px;
}

.option-key {
  min-width: 18px;
  font-weight: 600;
  color: #003087;
}

.answer-alert {
  margin-bottom: 12px;
}

.question-foot {
  color: #8c8c8c;
  font-size: 12px;
}
</style>
