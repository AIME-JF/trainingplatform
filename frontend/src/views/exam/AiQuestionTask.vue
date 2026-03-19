<template>
  <ai-task-tabs-layout
    v-model:active-tab="activeTab"
    title="AI 智能出题"
    subtitle="填写信息后创建任务，系统会按队列异步调用 AI 生成题目，你可调整题目后确认入库"
    :task-list="taskList"
    :task-loading="taskLoading"
    :active-task-id="activeTask?.id || null"
    :status-labels="statusLabels"
    :status-colors="statusColors"
    @refresh-tasks="loadTasks"
    @select-task="selectTask"
  >
    <template #create>
      <div class="create-form-wrap">
        <a-form layout="vertical">
          <a-form-item label="任务名称" required>
            <a-input v-model:value="taskForm.taskName" placeholder="例：刑侦基础训练出题任务" />
          </a-form-item>
          <a-form-item label="出题主题" required>
            <a-input v-model:value="taskForm.topic" placeholder="例：刑事侦查程序规范" />
          </a-form-item>
          <a-form-item label="参考文本">
            <a-textarea v-model:value="taskForm.sourceText" :rows="5" :maxlength="2000" show-count />
          </a-form-item>
          <a-form-item label="知识点">
            <a-textarea v-model:value="knowledgePointsText" :rows="3" placeholder="每行一个知识点" />
          </a-form-item>
          <a-row :gutter="12">
            <a-col :span="12">
              <a-form-item label="题目数量">
                <a-input-number v-model:value="taskForm.questionCount" :min="1" :max="20" style="width:100%" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="默认分值">
                <a-input-number v-model:value="taskForm.score" :min="1" :max="20" style="width:100%" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-form-item label="题型">
            <a-select v-model:value="selectedQuestionType" placeholder="请选择题型">
              <a-select-option v-for="item in questionTypeOptions" :key="item.value" :value="item.value">
                {{ item.label }}
              </a-select-option>
            </a-select>
          </a-form-item>
          <a-row :gutter="12">
            <a-col :span="12">
              <a-form-item label="整体难度">
                <a-select v-model:value="taskForm.difficulty">
                  <a-select-option v-for="level in [1, 2, 3, 4, 5]" :key="level" :value="level">
                    {{ difficultyLabels[level] }}
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="警种">
                <a-select v-model:value="taskForm.policeTypeId" allow-clear placeholder="可选">
                  <a-select-option v-for="item in policeTypeOptions" :key="item.id" :value="item.id">
                    {{ item.name }}
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>
          <a-form-item label="补充要求">
            <a-textarea v-model:value="taskForm.requirements" :rows="3" :maxlength="1000" show-count />
          </a-form-item>
          <permissions-tooltip
            :allowed="canCreateTaskPermission"
            tips="需要 CREATE_AI_QUESTION_TASK 权限"
            block
            v-slot="{ disabled }"
          >
            <a-button type="primary" block :loading="creating" :disabled="disabled" @click="handleCreateTask">创建任务</a-button>
          </permissions-tooltip>
        </a-form>
      </div>
    </template>

    <template #task-description="{ item }">
      共 {{ item.itemCount || 0 }} 题
    </template>

    <template #detail>
      <template v-if="activeTask">
        <div class="detail-header">
          <div>
            <div class="detail-title">{{ activeTask.taskName }}</div>
            <div class="detail-sub">主题：{{ activeTask.requestPayload.topic }}</div>
        </div>
        <a-space>
          <a-button @click="loadTaskDetail(activeTask.id)">刷新详情</a-button>
          <permissions-tooltip
            :allowed="canUpdateTaskPermission"
            :disabled="activeTask.status !== 'completed'"
            tips="需要 UPDATE_AI_QUESTION_TASK 权限"
            v-slot="{ disabled }"
          >
            <a-button :disabled="disabled" @click="openCreateQuestion">新增题目</a-button>
          </permissions-tooltip>
          <permissions-tooltip
            :allowed="canUpdateTaskPermission"
            :disabled="activeTask.status !== 'completed'"
            tips="需要 UPDATE_AI_QUESTION_TASK 权限"
            v-slot="{ disabled }"
          >
            <a-button :loading="saving" :disabled="disabled" @click="handleSaveTask">保存修改</a-button>
          </permissions-tooltip>
          <permissions-tooltip
            :allowed="canConfirmTaskPermission"
            :disabled="activeTask.status !== 'completed'"
            tips="需要 CONFIRM_AI_QUESTION_TASK 权限"
            v-slot="{ disabled }"
          >
            <a-button type="primary" :loading="confirming" :disabled="disabled" @click="handleConfirmTask">
              确认入题库
            </a-button>
          </permissions-tooltip>
        </a-space>
      </div>

        <ai-task-timeline
          :status="activeTask.status"
          :created-at="activeTask.createdAt"
          :completed-at="activeTask.completedAt"
          :confirmed-at="activeTask.confirmedAt"
        />

        <div class="detail-section">
          <div class="detail-section-title">任务请求</div>
          <a-descriptions :column="2" size="small" bordered>
            <a-descriptions-item label="知识点">{{ activeTask.requestPayload.knowledgePoints?.join('、') || '未设置' }}</a-descriptions-item>
            <a-descriptions-item label="题型">{{ formatQuestionTypes(activeTask.requestPayload.questionTypes) }}</a-descriptions-item>
            <a-descriptions-item label="题目数量">{{ activeTask.requestPayload.questionCount }}</a-descriptions-item>
            <a-descriptions-item label="默认分值">{{ activeTask.requestPayload.score }}</a-descriptions-item>
          </a-descriptions>
        </div>

        <div class="detail-section">
          <div class="detail-section-title">任务结果</div>
          <a-empty v-if="!activeTask.questions?.length" description="任务尚未生成结果" />
          <div v-else class="question-grid">
            <div v-for="(item, index) in activeTask.questions" :key="item.tempId || index" class="question-card">
              <div class="question-card-head">
                <a-space>
                  <a-tag :color="typeColors[item.type]">{{ typeLabels[item.type] }}</a-tag>
                  <span>第 {{ index + 1 }} 题</span>
                </a-space>
                <a-space v-if="activeTask.status === 'completed'">
                  <permissions-tooltip
                    :allowed="canUpdateTaskPermission"
                    tips="需要 UPDATE_AI_QUESTION_TASK 权限"
                    v-slot="{ disabled }"
                  >
                    <a-button type="link" size="small" :disabled="disabled" @click="openEditQuestion(item, index)">编辑</a-button>
                  </permissions-tooltip>
                  <permissions-tooltip
                    :allowed="canUpdateTaskPermission"
                    tips="需要 UPDATE_AI_QUESTION_TASK 权限"
                    v-slot="{ disabled }"
                  >
                    <a-button type="link" danger size="small" :disabled="disabled" @click="removeQuestion(index)">删除</a-button>
                  </permissions-tooltip>
                </a-space>
              </div>
              <div class="question-card-content">{{ item.content }}</div>
              <div class="question-card-meta">
                <span>难度 {{ item.difficulty }}</span>
                <span>分值 {{ item.score }}</span>
                <span>{{ item.knowledgePoint || '未设置知识点' }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>
      <a-empty v-else description="请选择任务查看详情" />
    </template>
  </ai-task-tabs-layout>

  <question-form-modal
    v-model:open="questionModalOpen"
    :title="editingQuestionIndex === -1 ? '新增题目' : '编辑题目'"
    :question="editingQuestion"
    :police-type-options="policeTypeOptions"
    :allowed-types="questionModalAllowedTypes"
    @submit="handleSubmitQuestion"
  />
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import {
  confirmAiQuestionTask,
  createAiQuestionTask,
  getAiQuestionTaskDetail,
  getAiQuestionTasks,
  updateAiQuestionTaskResult,
} from '@/api/ai'
import { getPoliceTypes } from '@/api/user'
import AiTaskTabsLayout from './components/AiTaskTabsLayout.vue'
import AiTaskTimeline from './components/AiTaskTimeline.vue'
import QuestionFormModal from './components/QuestionFormModal.vue'
import { sortQuestionsByType } from './utils/questionSort'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

const authStore = useAuthStore()
const difficultyLabels = { 1: '1级', 2: '2级', 3: '3级', 4: '4级', 5: '5级' }
const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }
const typeColors = { single: 'blue', multi: 'purple', judge: 'orange' }
const statusLabels = { pending: '排队中', processing: '处理中', completed: '已完成', confirmed: '已确认', failed: '处理失败' }
const statusColors = { pending: 'default', processing: 'processing', completed: 'blue', confirmed: 'green', failed: 'red' }
const DEFAULT_QUESTION_TYPE = 'single'
const questionTypeOptions = [
  { value: 'single', label: '单选题' },
  { value: 'multi', label: '多选题' },
  { value: 'judge', label: '判断题' },
]

const creating = ref(false)
const saving = ref(false)
const confirming = ref(false)
const taskLoading = ref(false)
const questionModalOpen = ref(false)
const editingQuestion = ref(null)
const editingQuestionIndex = ref(-1)
const taskList = ref([])
const activeTask = ref(null)
const activeTab = ref('create')
const knowledgePointsText = ref('')
const policeTypeOptions = ref([])

const taskForm = reactive({
  taskName: '',
  topic: '',
  sourceText: '',
  questionCount: 10,
  questionTypes: [DEFAULT_QUESTION_TYPE],
  difficulty: 3,
  policeTypeId: undefined,
  score: 2,
  requirements: '',
})

const canCreateTaskPermission = computed(() => authStore.hasPermission('CREATE_AI_QUESTION_TASK'))
const canUpdateTaskPermission = computed(() => authStore.hasPermission('UPDATE_AI_QUESTION_TASK'))
const canConfirmTaskPermission = computed(() => authStore.hasPermission('CONFIRM_AI_QUESTION_TASK'))
const selectedQuestionType = computed({
  get: () => taskForm.questionTypes?.[0] || DEFAULT_QUESTION_TYPE,
  set: (value) => {
    taskForm.questionTypes = value ? [value] : [DEFAULT_QUESTION_TYPE]
  },
})
const questionModalAllowedTypes = computed(() => {
  const types = activeTask.value?.requestPayload?.questionTypes?.filter((item) => typeLabels[item]) || []
  return types.length ? types : [selectedQuestionType.value]
})

function parseKnowledgePoints() {
  return knowledgePointsText.value
    .split(/\r?\n|,|，|；|;/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function resetTaskForm() {
  Object.assign(taskForm, {
    taskName: '',
    topic: '',
    sourceText: '',
    questionCount: 10,
    questionTypes: [DEFAULT_QUESTION_TYPE],
    difficulty: 3,
    policeTypeId: undefined,
    score: 2,
    requirements: '',
  })
  knowledgePointsText.value = ''
}

function formatQuestionTypes(types = []) {
  const labels = (types || []).map((item) => typeLabels[item] || item).filter(Boolean)
  return labels.length ? labels.join('、') : '未设置'
}

async function loadPoliceTypeOptions() {
  try {
    const result = await getPoliceTypes()
    policeTypeOptions.value = result.items || result || []
  } catch {
    policeTypeOptions.value = []
  }
}

async function loadTasks() {
  taskLoading.value = true
  try {
    const result = await getAiQuestionTasks({ size: -1 })
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
    const result = await getAiQuestionTaskDetail(taskId)
    activeTask.value = {
      ...result,
      questions: [...(result.questions || [])],
    }
  } catch (error) {
    message.error(error.message || '加载任务详情失败')
  }
}

async function selectTask(taskId) {
  await loadTaskDetail(taskId)
}

async function handleCreateTask() {
  if (!canCreateTaskPermission.value) return
  if (!taskForm.taskName.trim() || !taskForm.topic.trim()) {
    message.warning('请填写任务名称和出题主题')
    return
  }
  creating.value = true
  try {
    const result = await createAiQuestionTask({
      ...taskForm,
      questionTypes: [...taskForm.questionTypes],
      knowledgePoints: parseKnowledgePoints(),
    })
    message.success('任务已创建')
    resetTaskForm()
    await loadTasks()
    await loadTaskDetail(result.id)
    activeTab.value = 'list'
  } catch (error) {
    message.error(error.message || '创建任务失败')
  } finally {
    creating.value = false
  }
}

function openEditQuestion(question, index) {
  if (!canUpdateTaskPermission.value) return
  editingQuestion.value = { ...question }
  editingQuestionIndex.value = index
  questionModalOpen.value = true
}

function openCreateQuestion() {
  if (!canUpdateTaskPermission.value) return
  editingQuestion.value = {
    origin: 'manual',
    type: questionModalAllowedTypes.value[0] || 'single',
    difficulty: 3,
    score: 2,
  }
  editingQuestionIndex.value = -1
  questionModalOpen.value = true
}

function handleSubmitQuestion(question) {
  if (!activeTask.value) return
  const nextQuestions = [...(activeTask.value.questions || [])]
  if (editingQuestionIndex.value > -1) {
    nextQuestions.splice(editingQuestionIndex.value, 1, question)
  } else {
    nextQuestions.push(question)
  }
  activeTask.value.questions = sortQuestionsByType(nextQuestions)
  editingQuestionIndex.value = -1
  editingQuestion.value = null
}

function removeQuestion(index) {
  if (!canUpdateTaskPermission.value) return
  activeTask.value.questions.splice(index, 1)
}

async function handleSaveTask() {
  if (!canUpdateTaskPermission.value) return false
  if (!activeTask.value) return false
  saving.value = true
  try {
    const result = await updateAiQuestionTaskResult(activeTask.value.id, {
      taskName: activeTask.value.taskName,
      questions: activeTask.value.questions || [],
    })
    activeTask.value = { ...result, questions: [...(result.questions || [])] }
    await loadTasks()
    message.success('任务结果已保存')
    return true
  } catch (error) {
    message.error(error.message || '保存失败')
    return false
  } finally {
    saving.value = false
  }
}

async function handleConfirmTask() {
  if (!canConfirmTaskPermission.value) return
  if (!activeTask.value) return
  confirming.value = true
  try {
    if (activeTask.value.status === 'completed') {
      const saved = await handleSaveTask()
      if (!saved) {
        return
      }
    }
    const result = await confirmAiQuestionTask(activeTask.value.id)
    activeTask.value = { ...result, questions: [...(result.questions || [])] }
    await loadTasks()
    message.success(`已确认入库 ${result.confirmedQuestionIds?.length || 0} 道题目`)
  } catch (error) {
    message.error(error.message || '确认失败')
  } finally {
    confirming.value = false
  }
}

onMounted(() => {
  loadPoliceTypeOptions()
  loadTasks()
})
</script>

<style scoped>
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
}

.create-form-wrap {
  width: 100%;
  max-width: 880px;
}

.detail-title {
  font-size: 18px;
  font-weight: 600;
  color: #001234;
}

.detail-sub {
  margin-top: 6px;
  color: #8c8c8c;
}

.detail-section {
  margin-top: 20px;
}

.detail-section-title {
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 600;
  color: #1f1f1f;
}

.question-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.question-card {
  padding: 14px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #eef0f5;
}

.question-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.question-card-content {
  line-height: 1.7;
  color: #1f1f1f;
}

.question-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 10px;
  font-size: 12px;
  color: #8c8c8c;
}
</style>
