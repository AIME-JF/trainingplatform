<template>
  <div class="training-quiz-content">
    <div class="section-header" style="margin-bottom:16px">
      <h4>随堂测验</h4>
      <a-space v-if="!isStudent">
        <a-button size="small" type="primary" @click="openCreateQuizModal">
          <PlusOutlined /> 创建随堂测验
        </a-button>
        <a-button size="small" @click="goQuestionBank">题库管理</a-button>
      </a-space>
    </div>

    <!-- 学员视角 -->
    <template v-if="isStudent">
      <a-empty v-if="!availableQuizzes.length" description="当前暂无随堂测验安排" />
      <div v-else class="quiz-list">
        <div v-for="quiz in availableQuizzes" :key="quiz.id" class="quiz-card">
          <div class="quiz-info">
            <div class="quiz-name">{{ quiz.title }}</div>
            <div class="quiz-meta">
              <span>课程：{{ quiz.courseName || '-' }}</span>
              <span>题目数：{{ quiz.questionCount || 0 }}</span>
              <span>时长：{{ quiz.duration || 30 }}分钟</span>
            </div>
            <div class="quiz-status">
              <a-tag v-if="quiz.status === 'pending'" color="blue">待完成</a-tag>
              <a-tag v-else-if="quiz.status === 'completed'" color="green">已完成</a-tag>
              <a-tag v-else color="orange">进行中</a-tag>
            </div>
          </div>
          <a-button v-if="quiz.status !== 'completed'" type="primary" size="small" @click="startQuiz(quiz)">
            {{ quiz.status === 'pending' ? '开始答题' : '继续答题' }}
          </a-button>
          <a-button v-else type="link" size="small" @click="viewQuizResult(quiz)">
            查看成绩
          </a-button>
        </div>
      </div>
    </template>

    <!-- 教官视角 -->
    <template v-else>
      <a-tabs v-model:activeKey="quizTab">
        <a-tab-pane key="list" tab="测验列表">
          <a-empty v-if="!quizList.length" description="暂无随堂测验" />
          <a-table v-else :data-source="quizList" :pagination="{ pageSize: 10 }" row-key="id" size="small">
            <a-table-column title="测验名称" data-index="title" key="title" />
            <a-table-column title="关联课程" data-index="courseName" key="courseName" />
            <a-table-column title="题目数" data-index="questionCount" key="questionCount" width="80" />
            <a-table-column title="时长(分钟)" data-index="duration" key="duration" width="100" />
            <a-table-column title="完成情况" key="completion" width="120">
              <template #default="{ record }">
                {{ record.completedCount || 0 }}/{{ record.totalCount || 0 }}
              </template>
            </a-table-column>
            <a-table-column title="状态" data-index="status" key="status" width="100">
              <template #default="{ record }">
                <a-tag :color="getStatusColor(record.status)">{{ getStatusLabel(record.status) }}</a-tag>
              </template>
            </a-table-column>
            <a-table-column title="操作" key="action" width="150">
              <template #default="{ record }">
                <a-space>
                  <a-button type="link" size="small" @click="editQuiz(record)">编辑</a-button>
                  <a-button type="link" size="small" danger @click="deleteQuiz(record)">删除</a-button>
                </a-space>
              </template>
            </a-table-column>
          </a-table>
        </a-tab-pane>
        <a-tab-pane key="results" tab="成绩统计">
          <a-empty v-if="!quizList.length" description="暂无测验数据" />
          <div v-else class="quiz-results">
            <a-table :data-source="quizList" :pagination="{ pageSize: 10 }" row-key="id" size="small">
              <a-table-column title="测验名称" data-index="title" key="title" />
              <a-table-column title="平均分" data-index="avgScore" key="avgScore" width="100">
                <template #default="{ record }">
                  {{ record.avgScore?.toFixed(1) || '-' }}
                </template>
              </a-table-column>
              <a-table-column title="最高分" data-index="maxScore" key="maxScore" width="80" />
              <a-table-column title="最低分" data-index="minScore" key="minScore" width="80" />
              <a-table-column title="通过率" data-index="passRate" key="passRate" width="100">
                <template #default="{ record }">
                  {{ record.passRate ? (record.passRate * 100).toFixed(0) + '%' : '-' }}
                </template>
              </a-table-column>
            </a-table>
          </div>
        </a-tab-pane>
      </a-tabs>
    </template>

    <!-- 创建随堂测验弹窗 -->
    <a-modal
      v-model:open="createModalVisible"
      title="创建随堂测验"
      width="600px"
      @ok="handleCreateQuiz"
      @cancel="createModalVisible = false"
    >
      <a-form :form="quizForm" layout="vertical">
        <a-form-item label="测验名称" name="title">
          <a-input v-model:value="quizForm.title" placeholder="请输入测验名称" />
        </a-form-item>
        <a-form-item label="关联课程" name="courseId">
          <a-select v-model:value="quizForm.courseId" placeholder="请选择课程" @change="handleCourseSelect">
            <a-select-option v-for="course in courses" :key="course.id" :value="course.id">{{ course.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="题目数量" name="questionCount">
              <a-input-number v-model:value="quizForm.questionCount" :min="1" :max="50" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="时长(分钟)" name="duration">
              <a-input-number v-model:value="quizForm.duration" :min="5" :max="120" style="width:100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="及格分数" name="passingScore">
              <a-input-number v-model:value="quizForm.passingScore" :min="0" :max="100" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="题型范围" name="questionTypes">
              <a-checkbox-group v-model:value="quizForm.questionTypes">
                <a-checkbox value="single">单选题</a-checkbox>
                <a-checkbox value="multi">多选题</a-checkbox>
                <a-checkbox value="judge">判断题</a-checkbox>
              </a-checkbox-group>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <!-- 做题抽屉 -->
    <a-drawer
      v-model:open="quizDrawerVisible"
      :title="null"
      placement="right"
      :width="720"
      :closable="false"
      :destroy-on-close="true"
      @close="handleQuizClose"
    >
      <PracticeDo
        v-if="quizDrawerVisible"
        :questions="currentQuizQuestions"
        :practice-mode="false"
        :show-explanation="true"
        :time-limit="currentQuiz?.duration"
        @finish="handleQuizFinish"
        @close="quizDrawerVisible = false"
      />
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import PracticeDo from '@/views/practice/Do.vue'

const props = defineProps({
  trainingData: { type: Object, default: () => ({}) },
  isStudent: { type: Boolean, default: false },
})

const emit = defineEmits(['go-question-bank'])

// 数据
const courses = computed(() => props.trainingData.courses || [])
const quizList = ref([])
const availableQuizzes = ref([])
const quizTab = ref('list')

// 创建随堂测验
const createModalVisible = ref(false)
const quizForm = ref({
  title: '',
  courseId: null,
  questionCount: 10,
  duration: 30,
  passingScore: 60,
  questionTypes: ['single', 'multi', 'judge'],
})

// 做题相关
const quizDrawerVisible = ref(false)
const currentQuiz = ref(null)
const currentQuizQuestions = ref([])

// 状态映射
const statusColorMap = {
  draft: 'default',
  pending: 'blue',
  ongoing: 'orange',
  completed: 'green',
}

const statusLabelMap = {
  draft: '草稿',
  pending: '待开始',
  ongoing: '进行中',
  completed: '已结束',
}

const getStatusColor = (status) => statusColorMap[status] || 'default'
const getStatusLabel = (status) => statusLabelMap[status] || status

// 打开创建弹窗
const openCreateQuizModal = () => {
  quizForm.value = {
    title: '',
    courseId: null,
    questionCount: 10,
    duration: 30,
    passingScore: 60,
    questionTypes: ['single', 'multi', 'judge'],
  }
  createModalVisible.value = true
}

// 选择课程
const handleCourseSelect = (courseId) => {
  // 可以根据课程关联的题库来更新题库信息
}

// 创建随堂测验
const handleCreateQuiz = () => {
  if (!quizForm.value.title) {
    message.warning('请输入测验名称')
    return
  }
  if (!quizForm.value.courseId) {
    message.warning('请选择关联课程')
    return
  }
  if (quizForm.value.questionTypes.length === 0) {
    message.warning('请至少选择一种题型')
    return
  }
  // TODO: 调用API创建随堂测验
  message.success('随堂测验创建成功')
  createModalVisible.value = false
  loadQuizList()
}

// 加载测验列表
const loadQuizList = async () => {
  // TODO: 调用API获取随堂测验列表
  // const res = await getQuizList({ trainingId: props.trainingData.id })
  // quizList.value = res.data || []
}

// 前往题库管理
const goQuestionBank = () => {
  emit('go-question-bank')
}

// 编辑测验
const editQuiz = (quiz) => {
  // TODO: 打开编辑弹窗
  console.log('edit quiz', quiz)
}

// 删除测验
const deleteQuiz = (quiz) => {
  // TODO: 调用API删除
  console.log('delete quiz', quiz)
}

// 开始答题
const startQuiz = async (quiz) => {
  currentQuiz.value = quiz
  // TODO: 调用API获取题目
  // const res = await getQuizQuestions(quiz.id)
  // currentQuizQuestions.value = res.data || []
  quizDrawerVisible.value = true
}

// 查看成绩
const viewQuizResult = (quiz) => {
  // TODO: 打开成绩查看弹窗
  console.log('view result', quiz)
}

// 测验完成
const handleQuizFinish = (result) => {
  quizDrawerVisible.value = false
  message.success(`测验完成！正确率：${result.correctRate}`)
  // 刷新列表
  loadQuizList()
}

// 关闭答题
const handleQuizClose = () => {
  quizDrawerVisible.value = false
}
</script>

<style scoped>
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.section-header h4 {
  margin: 0;
  color: #333;
}
.quiz-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.quiz-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #eef2f7;
  border-radius: 10px;
  background: #fafcff;
}
.quiz-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.quiz-name {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}
.quiz-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  color: #6b7280;
  font-size: 13px;
}
.quiz-status {
  margin-top: 4px;
}
.quiz-results {
  margin-top: 16px;
}
</style>
