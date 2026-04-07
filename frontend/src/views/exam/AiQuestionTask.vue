<template>
  <div class="ai-question-task-page">
    <!-- 顶部通栏 Header -->
    <header class="page-header">
      <div class="header-left">
        <a-button type="text" @click="router.push({ name: 'QuestionBank' })">
          <template #icon><LeftOutlined /></template>
        </a-button>
        <div class="header-logo">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
        </div>
        <div class="header-titles">
          <h1 class="header-title">智能出题</h1>
          <div class="header-subtitle">AI Generation Flow</div>
        </div>
      </div>
    </header>

    <!-- 主体容器 -->
    <main class="page-main">
      <div class="page-container">
        <!-- 主内容卡片 -->
        <div class="main-card">
          <!-- 内部选项卡导航 -->
          <div class="card-tabs">
            <button
              class="tab-btn"
              :class="{ 'tab-active': activeTab === 'create' }"
              @click="activeTab = 'create'"
            >创建新任务</button>
            <button
              class="tab-btn"
              :class="{ 'tab-active': activeTab === 'list' }"
              @click="switchToListTab"
            >历史记录</button>
          </div>

          <!-- 创建任务表单 -->
          <div v-show="activeTab === 'create'">
            <!-- 任务基础信息 -->
            <section class="card-section">
              <div class="form-grid-2">
                <div class="form-field">
                  <label class="field-label required">任务名称</label>
                  <input
                    type="text"
                    class="field-input"
                    v-model="taskForm.taskName"
                    placeholder="例：刑侦基础训练出题任务"
                  />
                </div>
                <div class="form-field">
                  <label class="field-label required">出题主题</label>
                  <input
                    type="text"
                    class="field-input"
                    v-model="taskForm.topic"
                    placeholder="例：刑事侦查程序规范"
                  />
                </div>
              </div>
              <div class="form-grid-2 mt-16">
                <div class="form-field">
                  <label class="field-label required">生成到题库</label>
                  <input
                    type="text"
                    class="field-input"
                    v-model="taskForm.targetBankName"
                    placeholder="例：刑侦基础训练题库"
                  />
                </div>
                <div class="form-field">
                  <label class="field-label">关联课程</label>
                  <a-select
                    v-model:value="taskForm.courseId"
                    allow-clear
                    show-search
                    option-filter-prop="label"
                    placeholder="不关联课程时仅自己可见"
                    style="width: 100%"
                    @change="handleCourseChange"
                  >
                    <a-select-option v-for="item in courseOptions" :key="item.id" :value="item.id" :label="item.title">
                      {{ item.title }}
                    </a-select-option>
                  </a-select>
                </div>
              </div>
            </section>

            <!-- 核心区域：左右分栏 -->
            <div class="form-split-layout">
              <!-- 左栏：生成参数配置 -->
              <div class="form-split-left">
                <!-- 知识点检索 -->
                <div class="form-field-full">
                  <label class="field-label">知识点检索 (可选)</label>
                  <div class="select-wrapper">
                    <svg class="select-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                    <a-select
                      v-model:value="taskForm.knowledgePoints"
                      mode="multiple"
                      allow-clear
                      show-search
                      :filter-option="false"
                      :loading="knowledgePointLoading"
                      placeholder="搜索知识点关键词..."
                      :options="knowledgePointSelectOptions"
                      @search="handleKnowledgePointSearch"
                      @focus="handleKnowledgePointFocus"
                      class="search-select"
                    />
                  </div>
                </div>

                <!-- 数量、分值、题型 (3列) -->
                <div class="form-grid-3">
                  <div class="form-field">
                    <label class="field-label required">数量</label>
                    <a-input-number
                      v-model:value="taskForm.questionCount"
                      :min="1"
                      :max="50"
                      style="width: 100%"
                    />
                  </div>
                  <div class="form-field">
                    <label class="field-label required">分值</label>
                    <a-input-number
                      v-model:value="taskForm.score"
                      :min="1"
                      :max="20"
                      style="width: 100%"
                    />
                  </div>
                  <div class="form-field">
                    <label class="field-label">题型</label>
                    <a-select v-model:value="selectedQuestionType" style="width: 100%">
                      <a-select-option value="single">单选题</a-select-option>
                      <a-select-option value="multi">多选题</a-select-option>
                      <a-select-option value="judge">判断题</a-select-option>
                    </a-select>
                  </div>
                </div>

                <!-- 难度与警种 (2列) -->
                <div class="form-grid-2">
                  <div class="form-field">
                    <label class="field-label">难度等级</label>
                    <a-select v-model:value="taskForm.difficulty" style="width: 100%">
                      <a-select-option v-for="level in [1, 2, 3, 4, 5]" :key="level" :value="level">
                        {{ level }}级
                      </a-select-option>
                    </a-select>
                  </div>
                  <div class="form-field">
                    <label class="field-label">适用警种</label>
                    <a-select v-model:value="taskForm.policeTypeId" allow-clear placeholder="可选" style="width: 100%">
                      <a-select-option v-for="item in policeTypeOptions" :key="item.id" :value="item.id">
                        {{ item.name }}
                      </a-select-option>
                    </a-select>
                  </div>
                </div>
              </div>

              <!-- 右栏：补充要求 & 参考文本 -->
              <div class="form-split-right">
                <!-- 补充要求 -->
                <div class="form-field-full">
                  <label class="field-label">补充要求 (可选)</label>
                  <textarea
                    class="field-textarea min-h-[80px] text-xs"
                    v-model="taskForm.requirements"
                    placeholder="例如：侧重实战程序，选项需具有迷惑性..."
                    maxlength="1000"
                  ></textarea>
                </div>

                <!-- 参考文本 -->
                <div class="form-field-full">
                  <label class="field-label">参考文本 (AI 生成依据)</label>
                  <div class="material-toolbar">
                    <input ref="fileInputRef" type="file" class="hidden-file-input" accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt" @change="handleSourceFileChange" />
                    <a-space>
                      <a-button :loading="parsingFile" @click="triggerSourceFileSelect">上传材料并提取文本</a-button>
                      <span v-if="taskForm.sourceMaterialName" class="material-name">
                        已加载：{{ taskForm.sourceMaterialName }}
                      </span>
                    </a-space>
                  </div>
                  <div class="textarea-wrapper">
                    <textarea
                      class="field-textarea min-h-[200px]"
                      v-model="taskForm.sourceText"
                      placeholder="请粘贴相关的法律条文、教材段落或业务手册内容..."
                      maxlength="2000"
                    ></textarea>
                    <div class="textarea-counter">Max 2000 Characters</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 任务列表视图 -->
          <div v-show="activeTab === 'list'" class="card-section">
            <a-row :gutter="[16, 16]">
              <a-col :xs="24" :xl="8">
                <div class="task-list-panel">
                  <div class="task-list-header">
                    <span class="task-list-title">任务列表</span>
                    <a-button type="link" size="small" @click="loadTasks">刷新</a-button>
                  </div>
                  <a-list :data-source="taskList" :loading="taskLoading">
                    <template #renderItem="{ item }">
                      <a-list-item
                        class="task-list-item"
                        :class="{ active: item.id === activeTask?.id }"
                        @click="selectTask(item.id)"
                      >
                        <a-list-item-meta>
                          <template #title>
                            {{ item.taskName }}
                          </template>
                          <template #description>
                            共 {{ item.itemCount || 0 }} 题
                          </template>
                        </a-list-item-meta>
                        <div class="task-list-item-extra">
                          <a-tag :color="statusColors[item.status]">
                            {{ statusLabels[item.status] }}
                          </a-tag>
                        </div>
                      </a-list-item>
                    </template>
                  </a-list>
                  <a-empty v-if="!taskLoading && !taskList.length" description="暂无任务" />
                </div>
              </a-col>
              <a-col :xs="24" :xl="16">
                <div class="task-detail-panel">
                  <template v-if="activeTask">
                    <div class="detail-header">
                      <div>
                        <div class="detail-title">{{ activeTask.taskName }}</div>
                        <div class="detail-sub">主题：{{ activeTask.requestPayload?.topic }}</div>
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
                            确认生成题库
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
                        <a-descriptions-item label="目标题库">{{ activeTask.requestPayload?.targetBankName || '未设置' }}</a-descriptions-item>
                        <a-descriptions-item label="关联课程">{{ activeTask.requestPayload?.courseName || '未关联' }}</a-descriptions-item>
                        <a-descriptions-item label="知识点">{{ activeTask.requestPayload?.knowledgePoints?.join('、') || '未设置' }}</a-descriptions-item>
                        <a-descriptions-item label="题型">{{ formatQuestionTypes(activeTask.requestPayload?.questionTypes) }}</a-descriptions-item>
                        <a-descriptions-item label="题目数量">{{ activeTask.requestPayload?.questionCount }}</a-descriptions-item>
                        <a-descriptions-item label="默认分值">{{ activeTask.requestPayload?.score }}</a-descriptions-item>
                        <a-descriptions-item label="来源材料">{{ activeTask.requestPayload?.sourceMaterialName || '未上传材料' }}</a-descriptions-item>
                        <a-descriptions-item label="材料类型">{{ activeTask.requestPayload?.sourceMaterialType || '未设置' }}</a-descriptions-item>
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
                            <span>{{ formatKnowledgePoints(item.knowledgePoints) }}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </template>
                  <a-empty v-else description="请选择任务查看详情" />
                </div>
              </a-col>
            </a-row>
          </div>

          <!-- 底部操作栏 -->
          <div v-show="activeTab === 'create'" class="card-footer">
            <div class="footer-stats">
              <div class="stat-item">
                <span class="stat-label">任务摘要</span>
                <span class="stat-value">{{ taskForm.questionCount }} <span class="stat-unit">题 / AI 拟制</span></span>
              </div>
              <div class="stat-divider"></div>
              <div class="stat-item">
                <span class="stat-label">运行环境</span>
                <span class="stat-value-text">Celery Queue</span>
              </div>
            </div>
            <permissions-tooltip
              :allowed="canCreateTaskPermission"
              tips="需要 CREATE_AI_QUESTION_TASK 权限"
              block
              v-slot="{ disabled }"
            >
              <button
                class="btn-create"
                :class="{ 'btn-disabled': disabled }"
                :loading="creating"
                :disabled="disabled"
                @click="handleCreateTask"
              >
                <span>发起生成任务</span>
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>
              </button>
            </permissions-tooltip>
          </div>
        </div>
      </div>
    </main>

    <question-form-modal
      v-model:open="questionModalOpen"
      :title="editingQuestionIndex === -1 ? '新增题目' : '编辑题目'"
      :question="editingQuestion"
      :police-type-options="policeTypeOptions"
      :allowed-types="questionModalAllowedTypes"
      @submit="handleSubmitQuestion"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { LeftOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  confirmAiQuestionTask,
  createAiQuestionTask,
  getAiQuestionTaskDetail,
  getAiQuestionTasks,
  parseAiDocumentFile,
  updateAiQuestionTaskResult,
} from '@/api/ai'
import { getCourses } from '@/api/course'
import { getPoliceTypes } from '@/api/user'
import AiTaskTimeline from './components/AiTaskTimeline.vue'
import QuestionFormModal from './components/QuestionFormModal.vue'
import { createKnowledgePointRemoteSelect } from './utils/knowledgePointRemoteSelect'
import { sortQuestionsByType } from './utils/questionSort'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

const router = useRouter()
const authStore = useAuthStore()
const difficultyLabels = { 1: '1级', 2: '2级', 3: '3级', 4: '4级', 5: '5级' }
const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }
const typeColors = { single: 'blue', multi: 'purple', judge: 'orange' }
const statusLabels = { pending: '排队中', processing: '处理中', completed: '已完成', confirmed: '已确认', failed: '处理失败' }
const statusColors = { pending: 'default', processing: 'processing', completed: 'blue', confirmed: 'green', failed: 'red' }
const DEFAULT_QUESTION_TYPE = 'single'

const creating = ref(false)
const saving = ref(false)
const confirming = ref(false)
const parsingFile = ref(false)
const taskLoading = ref(false)
const questionModalOpen = ref(false)
const editingQuestion = ref(null)
const editingQuestionIndex = ref(-1)
const taskList = ref([])
const activeTask = ref(null)
const activeTab = ref('create')
const policeTypeOptions = ref([])
const courseOptions = ref([])
const fileInputRef = ref(null)
const {
  knowledgePointLoading,
  knowledgePointSelectOptions,
  handleKnowledgePointSearch,
  handleKnowledgePointFocus,
} = createKnowledgePointRemoteSelect('name')

const taskForm = reactive({
  taskName: '',
  topic: '',
  targetBankName: '',
  courseId: undefined,
  courseName: '',
  sourceMaterialName: '',
  sourceMaterialType: '',
  sourceText: '',
  knowledgePoints: [],
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

function resetTaskForm() {
  Object.assign(taskForm, {
    taskName: '',
    topic: '',
    targetBankName: '',
    courseId: undefined,
    courseName: '',
    sourceMaterialName: '',
    sourceMaterialType: '',
    sourceText: '',
    knowledgePoints: [],
    questionCount: 10,
    questionTypes: [DEFAULT_QUESTION_TYPE],
    difficulty: 3,
    policeTypeId: undefined,
    score: 2,
    requirements: '',
  })
}

function formatQuestionTypes(types = []) {
  const labels = (types || []).map((item) => typeLabels[item] || item).filter(Boolean)
  return labels.length ? labels.join('、') : '未设置'
}

function formatKnowledgePoints(points = []) {
  const values = Array.isArray(points)
    ? points.map((item) => (typeof item === 'string' ? item : item?.name)).filter(Boolean)
    : (points ? [String(points)] : [])
  return values.length ? values.join('、') : '未设置知识点'
}

async function loadPoliceTypeOptions() {
  try {
    const result = await getPoliceTypes()
    policeTypeOptions.value = result.items || result || []
  } catch {
    policeTypeOptions.value = []
  }
}

async function loadCourseOptions() {
  try {
    const result = await getCourses({ page: 1, size: -1 })
    courseOptions.value = result.items || []
  } catch {
    courseOptions.value = []
  }
}

function handleCourseChange(value) {
  const selectedCourse = courseOptions.value.find((item) => item.id === value)
  taskForm.courseName = selectedCourse?.title || ''
}

function triggerSourceFileSelect() {
  fileInputRef.value?.click?.()
}

async function handleSourceFileChange(event) {
  const file = event?.target?.files?.[0]
  if (!file) return

  parsingFile.value = true
  try {
    const result = await parseAiDocumentFile(file)
    taskForm.sourceText = result.text || ''
    taskForm.sourceMaterialName = result.filename || file.name
    const filename = result.filename || file.name || ''
    const extension = filename.includes('.') ? filename.split('.').pop()?.toLowerCase() : ''
    taskForm.sourceMaterialType = extension || file.type || ''
    message.success('材料内容已提取，可继续生成题库')
  } catch (error) {
    message.error(error.message || '材料解析失败')
  } finally {
    parsingFile.value = false
    if (event?.target) {
      event.target.value = ''
    }
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

function switchToListTab() {
  activeTab.value = 'list'
  if (!taskList.value.length) {
    loadTasks()
  }
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
      targetBankName: taskForm.targetBankName?.trim() || `${taskForm.topic.trim()}题库`,
      courseName: taskForm.courseName || undefined,
      sourceMaterialName: taskForm.sourceMaterialName || undefined,
      sourceMaterialType: taskForm.sourceMaterialType || undefined,
      questionTypes: [...taskForm.questionTypes],
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
  loadCourseOptions()
  loadTasks()
})
</script>

<style scoped>
.ai-question-task-page {
  min-height: 100vh;
  background-color: #F8FAFC;
  display: flex;
  flex-direction: column;
}

/* 顶部通栏 */
.page-header {
  height: 64px;
  background-color: #fff;
  border-bottom: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
  flex-shrink: 0;
  z-index: 30;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-logo {
  width: 32px;
  height: 32px;
  background-color: #2563EB;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.2);
}

.header-titles {
  display: flex;
  flex-direction: column;
}

.header-title {
  font-size: 16px;
  font-weight: 700;
  color: #1E293B;
  margin: 0;
  letter-spacing: -0.01em;
}

.header-subtitle {
  font-size: 9px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* 主体 */
.page-main {
  flex: 1;
  overflow-y: auto;
  padding: 24px 40px;
}

.page-container {
  width: 100%;
}

/* 主卡片 */
.main-card {
  width: 100%;
  background-color: #fff;
  border: 1px solid #E2E8F0;
  border-radius: 24px;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

/* 选项卡 */
.card-tabs {
  padding: 0 32px;
  border-bottom: 1px solid #F1F5F9;
  display: flex;
  gap: 32px;
}

.tab-btn {
  padding: 16px 0;
  font-size: 14px;
  font-weight: 700;
  color: #CBD5E1;
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
}

.tab-btn:hover {
  color: #64748B;
}

.tab-active {
  color: #2563EB;
  border-bottom-color: #2563EB;
}

/* 表单区块 */
.card-section {
  padding: 32px;
}

.mt-16 {
  margin-top: 16px;
}

/* 表单网格 */
.form-grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 32px;
}

.form-grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.form-grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
}

.form-field-full {
  display: flex;
  flex-direction: column;
}

.field-label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}

.field-label.required::after {
  content: '*';
  color: #EF4444;
  margin-left: 4px;
}

.field-input {
  width: 100%;
  background-color: transparent;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 14px;
  color: #1E293B;
  transition: all 0.2s;
  outline: none;
}

.field-input:hover {
  border-color: #CBD5E1;
}

.field-input:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.field-textarea {
  width: 100%;
  background-color: transparent;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
  color: #1E293B;
  transition: all 0.2s;
  outline: none;
  resize: none;
  line-height: 1.6;
}

.field-textarea:hover {
  border-color: #CBD5E1;
}

.field-textarea:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.textarea-wrapper {
  position: relative;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.material-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.hidden-file-input {
  display: none;
}

.material-name {
  font-size: 12px;
  color: #64748B;
}

.textarea-counter {
  position: absolute;
  bottom: 12px;
  right: 12px;
  font-size: 9px;
  font-weight: 700;
  color: #CBD5E1;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* 选择框 */
.select-wrapper {
  position: relative;
}

.select-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: #CBD5E1;
  z-index: 1;
  pointer-events: none;
}

.search-select {
  width: 100%;
}

.search-select :deep(.ant-select-selector) {
  padding-left: 36px !important;
}

/* 左右分栏布局 */
.form-split-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  border-top: 1px solid #E2E8F0;
}

.form-split-left {
  padding: 32px;
  border-right: 1px solid #E2E8F0;
  background-color: rgba(248, 250, 252, 0.1);
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-split-right {
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 任务列表 */
.task-list-panel {
  padding: 20px;
}

.task-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.task-list-title {
  font-size: 15px;
  font-weight: 600;
  color: #1E293B;
}

.task-list-item {
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s;
  padding: 12px !important;
  border: 1px solid transparent;
}

.task-list-item:hover {
  background: #f7f9ff;
}

.task-list-item.active {
  background: #eef4ff;
  border-color: rgba(37, 99, 235, 0.12);
}

.task-list-item-extra {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-detail-panel {
  padding: 20px;
  min-height: 400px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.detail-title {
  font-size: 18px;
  font-weight: 600;
  color: #001234;
}

.detail-sub {
  margin-top: 6px;
  color: #8c8c8c;
  font-size: 13px;
}

.detail-section {
  margin-top: 24px;
}

.detail-section-title {
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 600;
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

/* 底部操作栏 */
.card-footer {
  padding: 16px 32px;
  background-color: #1E293B;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 40px;
}

.footer-stats {
  display: flex;
  align-items: center;
  gap: 40px;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 9px;
  color: #64748B;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 2px;
}

.stat-value {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
}

.stat-unit {
  font-size: 10px;
  font-weight: 400;
  color: #64748B;
}

.stat-value-text {
  font-size: 12px;
  font-weight: 500;
  color: #fff;
  text-transform: uppercase;
}

.stat-divider {
  width: 1px;
  height: 32px;
  background-color: #334155;
}

.btn-create {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 6px 48px;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  background-color: #2563EB;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
}

.btn-create:hover {
  background-color: #3B82F6;
}

.btn-create:active {
  transform: scale(0.98);
}

.btn-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 响应式 */
@media (max-width: 1024px) {
  .form-split-layout {
    grid-template-columns: 1fr;
  }

  .form-split-left {
    border-right: none;
    border-bottom: 1px solid #E2E8F0;
  }

  .form-grid-2 {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .page-main {
    padding: 16px;
  }

  .card-tabs {
    padding: 0 16px;
  }

  .card-section {
    padding: 16px;
  }

  .card-footer {
    padding: 16px;
    flex-direction: column;
    gap: 16px;
  }

  .footer-stats {
    width: 100%;
    justify-content: center;
  }

  .question-grid {
    grid-template-columns: 1fr;
  }
}
</style>
