<template>
  <div class="ai-task-page">
    <div class="page-header">
      <div>
        <h2>AI 自动组卷</h2>
        <p class="page-sub">基于现有题库筛题生成试卷草稿，可调整题目后确认进入试卷仓库</p>
      </div>
      <a-tag color="blue">任务流</a-tag>
    </div>

    <a-row :gutter="16">
      <a-col :span="9">
        <a-card title="创建任务" :bordered="false">
          <a-form layout="vertical">
            <a-form-item label="任务名称" required>
              <a-input v-model:value="taskForm.taskName" placeholder="例：新警训练自动组卷任务" />
            </a-form-item>
            <a-form-item label="试卷名称" required>
              <a-input v-model:value="taskForm.paperTitle" placeholder="例：刑侦基础能力测验卷" />
            </a-form-item>
            <a-form-item label="试卷说明">
              <a-textarea v-model:value="taskForm.description" :rows="3" />
            </a-form-item>
            <a-row :gutter="12">
              <a-col :span="12">
                <a-form-item label="试卷类型">
                  <a-select v-model:value="taskForm.paperType">
                    <a-select-option value="formal">正式考核</a-select-option>
                    <a-select-option value="quiz">测验</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="组卷模式">
                  <a-select v-model:value="taskForm.assemblyMode">
                    <a-select-option value="balanced">均衡组卷</a-select-option>
                    <a-select-option value="practice">练习导向</a-select-option>
                    <a-select-option value="exam">考试导向</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>
            <a-row :gutter="12">
              <a-col :span="12">
                <a-form-item label="考试时长">
                  <a-input-number v-model:value="taskForm.duration" :min="10" :max="300" style="width:100%" />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="及格分">
                  <a-input-number v-model:value="taskForm.passingScore" :min="1" style="width:100%" />
                </a-form-item>
              </a-col>
            </a-row>
            <a-form-item label="知识点">
              <a-textarea v-model:value="knowledgePointsText" :rows="3" placeholder="每行一个知识点" />
            </a-form-item>
            <a-form-item label="警种">
              <a-select v-model:value="taskForm.policeTypeId" allow-clear placeholder="可选">
                <a-select-option v-for="item in policeTypeOptions" :key="item.id" :value="item.id">
                  {{ item.name }}
                </a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="题型配置">
              <div class="config-list">
                <div v-for="config in taskForm.typeConfigs" :key="config.type" class="config-item">
                  <span class="config-type">{{ typeLabels[config.type] }}</span>
                  <a-input-number v-model:value="config.count" :min="1" :max="30" />
                  <a-select v-model:value="config.difficulty" style="width:90px">
                    <a-select-option v-for="level in [1, 2, 3, 4, 5]" :key="level" :value="level">
                      {{ level }}级
                    </a-select-option>
                  </a-select>
                  <a-input-number v-model:value="config.score" :min="1" :max="20" />
                </div>
              </div>
            </a-form-item>
            <a-form-item label="补充要求">
              <a-textarea v-model:value="taskForm.requirements" :rows="3" :maxlength="1000" show-count />
            </a-form-item>
            <a-button type="primary" block :loading="creating" @click="handleCreateTask">创建任务</a-button>
          </a-form>
        </a-card>

        <a-card title="任务列表" :bordered="false" style="margin-top:16px">
          <template #extra>
            <a-button type="link" size="small" @click="loadTasks">刷新</a-button>
          </template>
          <a-list :data-source="taskList" :loading="taskLoading">
            <template #renderItem="{ item }">
              <a-list-item class="task-list-item" @click="selectTask(item.id)">
                <a-list-item-meta :title="item.taskName" :description="item.paperTitle || '未命名试卷'" />
                <a-tag :color="statusColors[item.status]">{{ statusLabels[item.status] }}</a-tag>
              </a-list-item>
            </template>
          </a-list>
          <a-empty v-if="!taskLoading && !taskList.length" description="暂无任务" />
        </a-card>
      </a-col>

      <a-col :span="15">
        <a-card :bordered="false">
          <template v-if="activeTask">
            <div class="detail-header">
              <div>
                <div class="detail-title">{{ activeTask.taskName }}</div>
                <div class="detail-sub">试卷：{{ activeTask.paperDraft?.title || activeTask.paperTitle }}</div>
              </div>
              <a-space>
                <a-button @click="loadTaskDetail(activeTask.id)">刷新详情</a-button>
                <a-button v-if="canEditTask" :loading="saving" @click="handleSaveTask">保存修改</a-button>
                <a-button type="primary" :loading="confirming" :disabled="activeTask.status !== 'completed'" @click="handleConfirmTask">
                  确认入卷库
                </a-button>
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
                <a-descriptions-item label="组卷模式">{{ modeLabels[activeTask.requestPayload.assemblyMode] }}</a-descriptions-item>
                <a-descriptions-item label="知识点">{{ activeTask.requestPayload.knowledgePoints?.join('、') || '未设置' }}</a-descriptions-item>
                <a-descriptions-item label="题型配置">
                  {{ formatTypeConfigs(activeTask.requestPayload.typeConfigs) }}
                </a-descriptions-item>
                <a-descriptions-item label="警种">
                  {{ findPoliceTypeName(activeTask.requestPayload.policeTypeId) || '未设置' }}
                </a-descriptions-item>
              </a-descriptions>
            </div>

            <div class="detail-section">
              <div class="detail-section-title">试卷草稿</div>
              <paper-draft-editor
                v-if="activeTask.paperDraft"
                v-model="activeTask.paperDraft"
                :disabled="!canEditTask"
                :allow-manual-question="true"
                @edit-question="openEditQuestion"
                @create-question="openCreateQuestion"
              />
              <a-empty v-else description="任务结果中暂无试卷草稿" />
            </div>
          </template>
          <a-empty v-else description="请选择左侧任务查看详情" />
        </a-card>
      </a-col>
    </a-row>

    <question-form-modal
      v-model:open="questionModalOpen"
      :title="editingQuestionIndex === -1 ? '新增题目' : '编辑题目'"
      :question="editingQuestion"
      :police-type-options="policeTypeOptions"
      @submit="handleSubmitQuestion"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  confirmAiPaperAssemblyTask,
  createAiPaperAssemblyTask,
  getAiPaperAssemblyTaskDetail,
  getAiPaperAssemblyTasks,
  updateAiPaperAssemblyTaskResult,
} from '@/api/ai'
import { getPoliceTypes } from '@/api/user'
import AiTaskTimeline from './components/AiTaskTimeline.vue'
import PaperDraftEditor from './components/PaperDraftEditor.vue'
import QuestionFormModal from './components/QuestionFormModal.vue'

const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }
const modeLabels = { balanced: '均衡组卷', practice: '练习导向', exam: '考试导向' }
const statusLabels = { pending: '待处理', processing: '处理中', completed: '已完成', confirmed: '已确认', failed: '处理失败' }
const statusColors = { pending: 'default', processing: 'processing', completed: 'blue', confirmed: 'green', failed: 'red' }

const creating = ref(false)
const saving = ref(false)
const confirming = ref(false)
const taskLoading = ref(false)
const questionModalOpen = ref(false)
const editingQuestion = ref(null)
const editingQuestionIndex = ref(-1)
const taskList = ref([])
const activeTask = ref(null)
const knowledgePointsText = ref('')
const policeTypeOptions = ref([])

const taskForm = reactive(createDefaultTaskForm())

const canEditTask = computed(() => activeTask.value?.status === 'completed')

function createDefaultTaskForm() {
  return {
    taskName: '',
    paperTitle: '',
    paperType: 'formal',
    description: '',
    duration: 60,
    passingScore: 60,
    assemblyMode: 'balanced',
    policeTypeId: undefined,
    typeConfigs: [
      { type: 'single', count: 5, difficulty: 3, score: 2 },
      { type: 'multi', count: 3, difficulty: 3, score: 3 },
      { type: 'judge', count: 2, difficulty: 2, score: 1 },
    ],
    requirements: '',
  }
}

function parseKnowledgePoints() {
  return knowledgePointsText.value
    .split(/\r?\n|,|，|；|;/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function resetTaskForm() {
  Object.assign(taskForm, createDefaultTaskForm())
  knowledgePointsText.value = ''
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
    const result = await getAiPaperAssemblyTasks({ size: -1 })
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
    const result = await getAiPaperAssemblyTaskDetail(taskId)
    activeTask.value = {
      ...result,
      paperDraft: result.paperDraft ? JSON.parse(JSON.stringify(result.paperDraft)) : null,
    }
  } catch (error) {
    message.error(error.message || '加载任务详情失败')
  }
}

async function selectTask(taskId) {
  await loadTaskDetail(taskId)
}

async function handleCreateTask() {
  if (!taskForm.taskName.trim() || !taskForm.paperTitle.trim()) {
    message.warning('请填写任务名称和试卷名称')
    return
  }
  creating.value = true
  try {
    const result = await createAiPaperAssemblyTask({
      ...taskForm,
      knowledgePoints: parseKnowledgePoints(),
    })
    message.success('任务已创建')
    resetTaskForm()
    await loadTasks()
    await loadTaskDetail(result.id)
  } catch (error) {
    message.error(error.message || '创建任务失败')
  } finally {
    creating.value = false
  }
}

function openEditQuestion(question, index) {
  editingQuestion.value = { ...question }
  editingQuestionIndex.value = index
  questionModalOpen.value = true
}

function openCreateQuestion() {
  editingQuestion.value = { origin: 'manual', difficulty: 3, score: 2 }
  editingQuestionIndex.value = -1
  questionModalOpen.value = true
}

function handleSubmitQuestion(question) {
  if (!activeTask.value?.paperDraft) return
  const nextQuestions = [...(activeTask.value.paperDraft.questions || [])]
  if (editingQuestionIndex.value > -1) {
    nextQuestions.splice(editingQuestionIndex.value, 1, question)
  } else {
    nextQuestions.push(question)
  }
  activeTask.value.paperDraft.questions = nextQuestions
  editingQuestion.value = null
  editingQuestionIndex.value = -1
}

async function handleSaveTask() {
  if (!activeTask.value) return false
  saving.value = true
  try {
    const result = await updateAiPaperAssemblyTaskResult(activeTask.value.id, {
      taskName: activeTask.value.taskName,
      paperDraft: activeTask.value.paperDraft,
    })
    activeTask.value = {
      ...result,
      paperDraft: result.paperDraft ? JSON.parse(JSON.stringify(result.paperDraft)) : null,
    }
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
  if (!activeTask.value) return
  confirming.value = true
  try {
    if (activeTask.value.status === 'completed') {
      const saved = await handleSaveTask()
      if (!saved) {
        return
      }
    }
    const result = await confirmAiPaperAssemblyTask(activeTask.value.id)
    activeTask.value = {
      ...result,
      paperDraft: result.paperDraft ? JSON.parse(JSON.stringify(result.paperDraft)) : null,
    }
    await loadTasks()
    message.success(`试卷已入库，试卷 ID：${result.confirmedPaperId}`)
  } catch (error) {
    message.error(error.message || '确认失败')
  } finally {
    confirming.value = false
  }
}

function formatTypeConfigs(configs = []) {
  return configs.map((item) => `${typeLabels[item.type]} ${item.count}题`).join(' / ')
}

function findPoliceTypeName(id) {
  return policeTypeOptions.value.find((item) => item.id === id)?.name
}

onMounted(() => {
  loadPoliceTypeOptions()
  loadTasks()
})
</script>

<style scoped>
.ai-task-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
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

.task-list-item {
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s;
}

.task-list-item:hover {
  background: #f7f9ff;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
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
}

.config-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.config-item {
  display: grid;
  grid-template-columns: 72px 1fr 90px 1fr;
  gap: 8px;
  align-items: center;
}

.config-type {
  color: #595959;
  font-size: 13px;
}
</style>
