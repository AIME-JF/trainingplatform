<template>
  <ai-task-tabs-layout
    v-model:active-tab="activeTab"
    title="智能生成试卷"
    subtitle="先由系统智能生成试题，再形成试卷草稿，你可修改试题和试卷后确认入库"
    :task-list="taskList"
    :task-loading="taskLoading"
    :active-task-id="activeTask?.id || null"
    :status-labels="statusLabels"
    :status-colors="statusColors"
    @refresh-tasks="loadTasks"
    @select-task="selectTask"
  >
    <template #create>
      <a-form layout="vertical">
        <a-form-item label="任务名称" required>
          <a-input v-model:value="taskForm.taskName" placeholder="例：反诈专题自动生成试卷任务" />
        </a-form-item>
        <a-form-item label="试卷名称" required>
          <a-input v-model:value="taskForm.paperTitle" placeholder="例：反诈基础知识测试卷" />
        </a-form-item>
        <a-form-item label="试卷说明">
          <a-textarea v-model:value="taskForm.description" :rows="3" />
        </a-form-item>
        <a-form-item label="生成主题" required>
          <a-input v-model:value="taskForm.topic" placeholder="例：电信网络诈骗案件侦办规范" />
        </a-form-item>
        <a-form-item label="参考文本">
          <a-textarea v-model:value="taskForm.sourceText" :rows="5" :maxlength="2000" show-count />
        </a-form-item>
        <a-form-item
          label="知识点"
          extra="可输入关键词搜索知识点；不输入时默认展示前 20 条。"
        >
          <a-select
            v-model:value="taskForm.knowledgePoints"
            mode="multiple"
            allow-clear
            show-search
            :filter-option="false"
            :loading="knowledgePointLoading"
            placeholder="可选，可输入搜索题库知识点"
            :options="knowledgePointSelectOptions"
            @search="handleKnowledgePointSearch"
            @focus="handleKnowledgePointFocus"
          />
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
            <a-form-item label="整体难度">
              <a-select v-model:value="taskForm.difficulty">
                <a-select-option v-for="level in [1, 2, 3, 4, 5]" :key="level" :value="level">
                  {{ level }}级
                </a-select-option>
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
        <a-form-item label="警种">
          <a-select v-model:value="taskForm.policeTypeId" allow-clear placeholder="可选">
            <a-select-option v-for="item in policeTypeOptions" :key="item.id" :value="item.id">
              {{ item.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="题型配置">
          <paper-type-config-editor
            v-model="taskForm.typeConfigs"
            description="这里决定每种题型需要生成多少题、优先采用几级难度，以及每道题在试卷中的分值。"
          />
        </a-form-item>
        <a-form-item label="补充要求">
          <a-textarea v-model:value="taskForm.requirements" :rows="3" :maxlength="1000" show-count />
        </a-form-item>
        <permissions-tooltip
          :allowed="canCreateTaskPermission"
          tips="需要 CREATE_AI_PAPER_GENERATION_TASK 权限"
          block
          v-slot="{ disabled }"
        >
          <a-button type="primary" block :loading="creating" :disabled="disabled" @click="handleCreateTask">创建任务</a-button>
        </permissions-tooltip>
      </a-form>
    </template>

    <template #task-description="{ item }">
      {{ item.paperTitle || '未命名试卷' }}
    </template>

    <template #detail>
      <template v-if="activeTask">
        <div class="detail-header">
          <div>
            <div class="detail-title">{{ activeTask.taskName }}</div>
            <div class="detail-sub">试卷：{{ activeTask.paperDraft?.title || activeTask.paperTitle }}</div>
        </div>
        <a-space>
          <a-button @click="loadTaskDetail(activeTask.id)">刷新详情</a-button>
          <permissions-tooltip
            :allowed="canUpdateTaskPermission"
            :disabled="activeTask.status !== 'completed'"
            tips="需要 UPDATE_AI_PAPER_GENERATION_TASK 权限"
            v-slot="{ disabled }"
          >
            <a-button :loading="saving" :disabled="disabled" @click="handleSaveTask">保存修改</a-button>
          </permissions-tooltip>
          <permissions-tooltip
            :allowed="canConfirmTaskPermission"
            :disabled="activeTask.status !== 'completed'"
            tips="需要 CONFIRM_AI_PAPER_GENERATION_TASK 权限"
            v-slot="{ disabled }"
          >
            <a-button type="primary" :loading="confirming" :disabled="disabled" @click="handleConfirmTask">
              确认入卷库
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
            <a-descriptions-item label="生成主题">{{ activeTask.requestPayload.topic }}</a-descriptions-item>
            <a-descriptions-item label="整体难度">{{ activeTask.requestPayload.difficulty }}级</a-descriptions-item>
            <a-descriptions-item label="知识点">{{ activeTask.requestPayload.knowledgePoints?.join('、') || '未设置' }}</a-descriptions-item>
            <a-descriptions-item label="题型配置">{{ formatTypeConfigs(activeTask.requestPayload.typeConfigs) }}</a-descriptions-item>
          </a-descriptions>
        </div>

        <div class="detail-section">
          <div class="detail-section-title">试卷草稿</div>
          <paper-draft-editor
            v-if="activeTask.paperDraft"
            v-model="activeTask.paperDraft"
            :disabled="!canEditTask"
            :allow-manual-question="true"
            :sort-by-type="true"
            @edit-question="openEditQuestion"
            @create-question="openCreateQuestion"
          />
          <a-empty v-else description="任务结果中暂无试卷草稿" />
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
    @submit="handleSubmitQuestion"
  />
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import {
  confirmAiPaperGenerationTask,
  createAiPaperGenerationTask,
  getAiPaperGenerationTaskDetail,
  getAiPaperGenerationTasks,
  updateAiPaperGenerationTaskResult,
} from '@/api/ai'
import { getPoliceTypes } from '@/api/user'
import AiTaskTabsLayout from './components/AiTaskTabsLayout.vue'
import AiTaskTimeline from './components/AiTaskTimeline.vue'
import PaperDraftEditor from './components/PaperDraftEditor.vue'
import PaperTypeConfigEditor from './components/PaperTypeConfigEditor.vue'
import QuestionFormModal from './components/QuestionFormModal.vue'
import { createKnowledgePointRemoteSelect } from './utils/knowledgePointRemoteSelect'
import { formatPaperTypeConfigs, summarizePaperTypeConfigs } from './utils/paperTypeConfig'
import { sortQuestionsByType } from './utils/questionSort'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

const authStore = useAuthStore()
const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }
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
const activeTab = ref('create')
const policeTypeOptions = ref([])
const {
  knowledgePointLoading,
  knowledgePointSelectOptions,
  handleKnowledgePointSearch,
  handleKnowledgePointFocus,
} = createKnowledgePointRemoteSelect('name')

const taskForm = reactive(createDefaultTaskForm())

const canCreateTaskPermission = computed(() => authStore.hasPermission('CREATE_AI_PAPER_GENERATION_TASK'))
const canUpdateTaskPermission = computed(() => authStore.hasPermission('UPDATE_AI_PAPER_GENERATION_TASK'))
const canConfirmTaskPermission = computed(() => authStore.hasPermission('CONFIRM_AI_PAPER_GENERATION_TASK'))
const canEditTask = computed(() => activeTask.value?.status === 'completed' && canUpdateTaskPermission.value)

function createDefaultTaskForm() {
  return {
    taskName: '',
    paperTitle: '',
    paperType: 'formal',
    description: '',
    topic: '',
    sourceText: '',
    knowledgePoints: [],
    duration: 60,
    passingScore: 60,
    difficulty: 3,
    policeTypeId: undefined,
    typeConfigs: [
      { type: 'single', count: 5, difficulty: 3, score: 2 },
      { type: 'multi', count: 3, difficulty: 3, score: 3 },
      { type: 'judge', count: 2, difficulty: 2, score: 1 },
    ],
    requirements: '',
  }
}

function resetTaskForm() {
  Object.assign(taskForm, createDefaultTaskForm())
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
    const result = await getAiPaperGenerationTasks({ size: -1 })
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
    const result = await getAiPaperGenerationTaskDetail(taskId)
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
  if (!canCreateTaskPermission.value) return
  if (!taskForm.taskName.trim() || !taskForm.paperTitle.trim() || !taskForm.topic.trim()) {
    message.warning('请填写任务名称、试卷名称和生成主题')
    return
  }
  if (summarizePaperTypeConfigs(taskForm.typeConfigs).totalCount <= 0) {
    message.warning('请至少将一种题型的数量设置为大于 0')
    return
  }
  creating.value = true
  try {
    const result = await createAiPaperGenerationTask({
      ...taskForm,
      knowledgePoints: [...(taskForm.knowledgePoints || [])],
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
  activeTask.value.paperDraft.questions = sortQuestionsByType(nextQuestions)
  editingQuestion.value = null
  editingQuestionIndex.value = -1
}

async function handleSaveTask() {
  if (!canUpdateTaskPermission.value) return false
  if (!activeTask.value) return false
  saving.value = true
  try {
    const result = await updateAiPaperGenerationTaskResult(activeTask.value.id, {
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
    const result = await confirmAiPaperGenerationTask(activeTask.value.id)
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
  return formatPaperTypeConfigs(configs, typeLabels)
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
</style>
