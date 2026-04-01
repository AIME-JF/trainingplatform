<template>
  <div class="teaching-resource-page">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h2>教学资源生成</h2>
        <p class="page-sub">描述教学需求，系统智能生成课件资源</p>
      </div>
      <div class="page-header-actions">
        <a-button @click="$router.push('/resource/my')">返回我的空间</a-button>
        <a-tag color="blue">建议型任务</a-tag>
      </div>
    </div>

    <!-- Task List View -->
    <template v-if="!detailVisible">
      <a-card :bordered="false" class="list-card">
        <template #title>
          <div class="list-card-title">
            <span>任务列表</span>
            <a-space>
              <a-button @click="loadTasks">刷新</a-button>
              <permissions-tooltip
                :allowed="canCreateTaskPermission"
                tips="需要 USE_TEACHING_RESOURCE_GENERATION 权限"
                v-slot="{ disabled }"
              >
                <a-button type="primary" :disabled="disabled" @click="showCreateModal">
                  <template #icon><plus-outlined /></template>
                  新建任务
                </a-button>
              </permissions-tooltip>
            </a-space>
          </div>
        </template>

        <a-spin :spinning="taskLoading">
          <a-empty v-if="!taskList.length && !taskLoading" description="暂无教学资源生成任务" />
          <div v-else class="task-list">
            <div
              v-for="item in taskList"
              :key="item.id"
              class="task-list-row"
            >
              <div class="task-row-content">
                <div class="task-row-name">{{ item.taskName }}</div>
                <div class="task-row-desc">{{ item.itemCount || 0 }} 页 · {{ item.summaryText || '等待生成结果' }}</div>
              </div>
              <div class="task-row-right">
                <a-tag :color="statusColors[item.status] || 'default'">
                  {{ statusLabels[item.status] || item.status }}
                </a-tag>
                <span class="task-row-time">{{ formatTime(item.createdAt) }}</span>
              </div>
              <div class="task-row-actions">
                <a-button type="link" size="small" @click="openDetail(item.id)">详情</a-button>
                <a-button
                  v-if="item.confirmedResourceId"
                  type="link"
                  size="small"
                  @click="$router.push(`/resource/detail/${item.confirmedResourceId}`)"
                >查看资源</a-button>
              </div>
            </div>
          </div>
        </a-spin>
      </a-card>
    </template>

    <!-- Detail View -->
    <template v-if="detailVisible && activeTask">
      <a-card :bordered="false" class="detail-card">
        <template #title>
          <div class="detail-card-title">
            <a-button @click="closeDetail">
              <template #icon><arrow-left-outlined /></template>
              返回列表
            </a-button>
            <span class="detail-card-name">{{ activeTask.resourceMeta?.resourceTitle || activeTask.previewTitle || activeTask.taskName }}</span>
          </div>
        </template>
        <template #extra>
          <a-button @click="loadTaskDetail(activeTask.id)" size="small">刷新</a-button>
        </template>

        <!-- Steps Timeline -->
        <ai-task-timeline
          :status="activeTask.status"
          :created-at="activeTask.createdAt"
          :completed-at="activeTask.completedAt"
          :confirmed-at="activeTask.confirmedAt"
          :active-step="currentDetailStep"
          mode="resource-generation"
        />

        <!-- Detail Step Navigation -->
        <div class="detail-step-nav">
          <a-button :disabled="currentDetailStep <= 0" @click="prevStep">
            <template #icon><left-outlined /></template>
            上一步
          </a-button>
          <span class="detail-step-label">{{ detailStepLabels[currentDetailStep] }}</span>
          <a-button :disabled="currentDetailStep >= maxDetailStep" @click="nextStep">
            下一步
            <template #icon><right-outlined /></template>
          </a-button>
        </div>

        <!-- Step 0 & 1: 任务请求（创建任务 / 智能生成共用） -->
        <div v-show="currentDetailStep <= 1" class="detail-section">
          <div class="detail-section-title">任务请求</div>
          <a-descriptions :column="2" size="small" bordered>
            <a-descriptions-item label="模板">通用教学课件模板</a-descriptions-item>
            <a-descriptions-item label="标题生成">系统自动生成</a-descriptions-item>
            <a-descriptions-item label="教学资源要求" :span="2">
              <div class="multiline-text">{{ activeTask.requestPayload?.requirements }}</div>
            </a-descriptions-item>
          </a-descriptions>
          <div v-if="activeTask.status === 'pending' || activeTask.status === 'processing'" class="generation-status">
            <a-spin />
            <span>{{ activeTask.status === 'pending' ? '任务排队中，请稍候...' : '智能生成中，请稍候...' }}</span>
          </div>
          <div v-if="activeTask.status === 'failed'" class="generation-status generation-failed">
            <a-result status="error" title="生成失败" sub-title="请检查系统 AI 配置或重新创建任务" />
          </div>
        </div>

        <!-- Step 2: 查看结果 (解析结果 + 模板与页面方案) -->
        <div v-show="currentDetailStep === 2" class="detail-section">
          <div class="detail-section-title">解析结果</div>
          <a-empty v-if="!activeTask.parsedRequest" description="任务尚未生成解析结果" />
          <template v-else>
            <a-descriptions :column="2" size="small" bordered>
              <a-descriptions-item label="主题">{{ activeTask.parsedRequest.theme }}</a-descriptions-item>
              <a-descriptions-item label="适用对象">{{ activeTask.parsedRequest.targetAudience || '未指定' }}</a-descriptions-item>
              <a-descriptions-item label="使用场景">{{ activeTask.parsedRequest.usageScenario || '未指定' }}</a-descriptions-item>
              <a-descriptions-item label="表达风格">{{ activeTask.parsedRequest.tone || '未指定' }}</a-descriptions-item>
              <a-descriptions-item label="关键词">{{ formatTagList(activeTask.parsedRequest.keywords) }}</a-descriptions-item>
              <a-descriptions-item label="学习目标">{{ formatTagList(activeTask.parsedRequest.learningGoals) }}</a-descriptions-item>
              <a-descriptions-item label="解析摘要" :span="2">{{ activeTask.parsedRequest.summary || '无' }}</a-descriptions-item>
            </a-descriptions>
          </template>

          <div class="detail-section-title" style="margin-top: 24px">模板与页面方案</div>
          <a-empty v-if="!activeTask.pagePlan?.length" description="任务尚未生成页面方案" />
          <template v-else>
            <a-alert
              type="success"
              show-icon
              class="template-result-alert"
              :message="activeTask.selectedTemplate?.name || '通用教学课件模板'"
              :description="activeTask.selectedTemplate?.description || '本次任务已按固定模板生成页面内容。'"
            />
            <div class="page-plan-grid">
              <div v-for="page in activeTask.pagePlan" :key="page.pageNo" class="page-plan-card">
                <div class="page-plan-head">
                  <a-tag color="blue">第 {{ page.pageNo }} 页</a-tag>
                  <a-tag>{{ formatPageType(page.pageType) }}</a-tag>
                </div>
                <div class="page-plan-title">{{ page.title }}</div>
                <div v-if="page.subtitle" class="page-plan-subtitle">{{ page.subtitle }}</div>
                <ul class="page-plan-list">
                  <li v-for="(bullet, index) in page.bullets || []" :key="`${page.pageNo}-${index}`">{{ bullet }}</li>
                </ul>
                <div v-if="page.highlight" class="page-plan-highlight">重点：{{ page.highlight }}</div>
              </div>
            </div>
          </template>
        </div>

        <!-- Step 3: 预览 (HTML课件预览) -->
        <div v-show="currentDetailStep === 3" class="detail-section">
          <div class="detail-section-title">课件预览</div>
          <a-empty v-if="!activeTask.htmlContent" description="任务尚未生成 HTML 课件" />
          <iframe
            v-else
            class="preview-frame"
            :srcdoc="activeTask.htmlContent"
            sandbox="allow-scripts"
            title="教学资源预览"
          />
        </div>

        <!-- Step 4: 确认完成 (资源基础信息) -->
        <div v-show="currentDetailStep === 4" class="detail-section">
          <div class="detail-section-title">资源基础信息</div>
          <a-empty
            v-if="!['completed', 'confirmed'].includes(activeTask.status)"
            description="生成完成后可填写资源基础信息"
          />
          <template v-else>
            <a-form v-if="activeTask.status === 'completed'" layout="vertical" class="meta-form">
              <a-form-item label="标题" required>
                <a-input
                  v-model:value="resourceMetaForm.resourceTitle"
                  :maxlength="200"
                  placeholder="可修改系统自动生成的标题"
                />
              </a-form-item>

              <a-form-item label="资源摘要">
                <a-textarea
                  v-model:value="resourceMetaForm.resourceSummary"
                  :rows="3"
                  :maxlength="1000"
                  show-count
                  placeholder="请输入资源摘要"
                />
              </a-form-item>

              <a-form-item label="资源标签">
                <a-select
                  v-model:value="resourceMetaForm.tags"
                  mode="tags"
                  show-search
                  :options="mergedTagOptions"
                  :filter-option="false"
                  :loading="tagSearching"
                  placeholder="支持搜索已有标签，输入后回车可直接创建新标签"
                  style="width: 100%"
                  @search="handleTagSearch"
                  @change="handleTagChange"
                />
              </a-form-item>

              <a-form-item label="可见范围">
                <admission-scope-selector
                  v-model:scope-type="resourceMetaForm.scopeType"
                  v-model:scope-target-ids="resourceMetaForm.scopeTargetIds"
                  :user-role="''"
                  all-hint="全部用户都可以查看确认后的资源草稿。"
                  user-placeholder="请选择可查看资源的用户"
                  department-placeholder="请选择可查看资源的部门"
                  role-placeholder="请选择可查看资源的角色"
                  user-hint="仅选中的用户可以查看确认后的资源。"
                  department-hint="选中部门下的用户可以查看确认后的资源。"
                  role-hint="拥有选中角色的用户可以查看确认后的资源。"
                />
              </a-form-item>

              <div class="confirm-actions">
                <permissions-tooltip
                  :allowed="canConfirmTaskPermission"
                  tips="需要 USE_TEACHING_RESOURCE_GENERATION 权限"
                  v-slot="{ disabled }"
                >
                  <a-button
                    type="primary"
                    size="large"
                    :loading="confirming"
                    :disabled="disabled"
                    @click="handleConfirmTask"
                  >
                    确认保存资源草稿
                  </a-button>
                </permissions-tooltip>
              </div>
            </a-form>

            <!-- Confirmed: read-only display -->
            <template v-if="activeTask.status === 'confirmed'">
              <a-result status="success" title="已保存为资源草稿" sub-title="可继续在我的空间中走审核流程">
                <template #extra>
                  <a-button
                    v-if="activeTask.confirmedResourceId"
                    type="primary"
                    @click="$router.push(`/resource/detail/${activeTask.confirmedResourceId}`)"
                  >查看资源</a-button>
                </template>
              </a-result>
              <a-descriptions :column="2" size="small" bordered>
                <a-descriptions-item label="标题" :span="2">{{ resourceMetaForm.resourceTitle || '未设置' }}</a-descriptions-item>
                <a-descriptions-item label="可见范围">{{ formatScopeType(resourceMetaForm.scopeType) }}</a-descriptions-item>
                <a-descriptions-item label="资源标签">{{ formatTagList(resourceMetaForm.tags) }}</a-descriptions-item>
                <a-descriptions-item label="资源摘要" :span="2">{{ resourceMetaForm.resourceSummary || '未填写' }}</a-descriptions-item>
              </a-descriptions>
            </template>
          </template>
        </div>
      </a-card>
    </template>

    <!-- Create Task Modal -->
    <a-modal
      v-model:open="createModalVisible"
      title="新建教学资源生成任务"
      :confirm-loading="creating"
      ok-text="创建任务"
      cancel-text="取消"
      :ok-button-props="{ disabled: !canCreateTaskPermission }"
      width="680px"
      @ok="handleCreateTask"
    >
      <a-form layout="vertical">
        <a-alert
          type="info"
          show-icon
          class="template-alert"
          message="当前版本使用固定的「通用教学课件模板」生成内容"
          description="只需填写教学资源要求。系统会先智能生成课件，生成后可在详情页预览效果、补充资源信息并确认保存。"
        />
        <a-form-item
          label="教学资源要求"
          required
          extra="建议写明课件主题、适用对象、希望强调的重点、案例场景或课堂用途。标题会在生成后自动给出。"
        >
          <a-textarea
            v-model:value="taskForm.requirements"
            :rows="7"
            :maxlength="4000"
            show-count
            placeholder="例：请生成一份面向新警培训的课件，主题是执法规范化流程，要求突出常见风险点、处置步骤和案例提醒，适合课堂投屏讲解。"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, toRef } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, ArrowLeftOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  confirmTeachingResourceGenerationTask,
  createTeachingResourceGenerationTask,
  getTeachingResourceGenerationTaskDetail,
  getTeachingResourceGenerationTasks,
  updateTeachingResourceGenerationTaskMeta,
} from '@/api/ai'
import { createResourceTag, getResourceTags } from '@/api/resource'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'
import AdmissionScopeSelector from '@/views/exam/components/AdmissionScopeSelector.vue'
import AiTaskTimeline from '@/views/exam/components/AiTaskTimeline.vue'
import { useCreatableTagSelect } from '@/utils/creatableTagSelect'

const authStore = useAuthStore()
const creating = ref(false)
const confirming = ref(false)
const taskLoading = ref(false)
const taskList = ref([])
const activeTask = ref(null)
const detailVisible = ref(false)
const createModalVisible = ref(false)
const currentDetailStep = ref(0)

const statusLabels = { pending: '排队中', processing: '智能生成中', completed: '生成完成', confirmed: '已保存草稿', failed: '生成失败' }
const statusColors = { pending: 'default', processing: 'processing', completed: 'blue', confirmed: 'green', failed: 'red' }
const detailStepLabels = ['任务请求', '智能生成', '查看结果', '预览', '确认完成']

const taskForm = reactive({ requirements: '' })
const resourceMetaForm = reactive({
  resourceTitle: '',
  resourceSummary: '',
  tags: [],
  scopeType: 'all',
  scopeTargetIds: [],
})

const canCreateTaskPermission = computed(() => authStore.hasPermission('USE_TEACHING_RESOURCE_GENERATION'))
const canConfirmTaskPermission = computed(() => authStore.hasPermission('USE_TEACHING_RESOURCE_GENERATION'))

const maxDetailStep = computed(() => {
  if (!activeTask.value) return 0
  const status = activeTask.value.status
  if (status === 'confirmed') return 4
  if (status === 'completed') return 4
  if (status === 'processing') return 1
  if (status === 'pending') return 1
  if (status === 'failed') return 1
  return 0
})

const pageTypeLabels = {
  cover: '封面页', goal: '目标页', background: '背景页',
  knowledge: '知识页', case: '案例页', practice: '建议页', summary: '总结页',
}

const {
  tagSearching, mergedTagOptions, normalizeTags,
  fetchTagOptions, handleTagSearch, handleTagChange,
} = useCreatableTagSelect(toRef(resourceMetaForm, 'tags'), {
  fetchTags: getResourceTags,
  createTag: createResourceTag,
  createErrorMessage: (tagName, error) => error?.message || `标签"${tagName}"创建失败`,
})

function syncResourceMetaForm(task) {
  const meta = task?.resourceMeta || {}
  Object.assign(resourceMetaForm, {
    resourceTitle: meta.resourceTitle || '',
    resourceSummary: meta.resourceSummary || '',
    tags: [...(meta.tags || [])],
    scopeType: meta.scopeType || 'all',
    scopeTargetIds: [...(meta.scopeTargetIds || [])],
  })
}

function formatTagList(values = []) {
  const normalized = (values || []).filter(Boolean)
  return normalized.length ? normalized.join('、') : '未设置'
}

function formatPageType(value) {
  return pageTypeLabels[value] || value || '页面'
}

function formatScopeType(value) {
  const labels = { all: '全部', user: '指定用户', department: '指定部门', role: '指定角色' }
  return labels[value] || value || '全部'
}

function formatTime(value) {
  if (!value) return ''
  return String(value).replace('T', ' ').slice(0, 16)
}

function computeInitialStep(task) {
  if (!task) return 0
  const status = task.status
  if (status === 'confirmed') return 4
  if (status === 'completed') return 2
  if (status === 'processing' || status === 'pending') return 1
  if (status === 'failed') return 1
  return 0
}

function prevStep() {
  if (currentDetailStep.value > 0) {
    currentDetailStep.value--
  }
}

function nextStep() {
  if (currentDetailStep.value < maxDetailStep.value) {
    currentDetailStep.value++
  }
}

function showCreateModal() {
  taskForm.requirements = ''
  createModalVisible.value = true
}

function closeDetail() {
  detailVisible.value = false
  activeTask.value = null
}

async function loadTasks() {
  taskLoading.value = true
  try {
    const result = await getTeachingResourceGenerationTasks({ size: -1 })
    taskList.value = result.items || []
  } catch (error) {
    message.error(error.message || '加载任务失败')
  } finally {
    taskLoading.value = false
  }
}

async function loadTaskDetail(taskId) {
  try {
    activeTask.value = await getTeachingResourceGenerationTaskDetail(taskId)
    syncResourceMetaForm(activeTask.value)
  } catch (error) {
    message.error(error.message || '加载任务详情失败')
  }
}

async function openDetail(taskId) {
  await loadTaskDetail(taskId)
  currentDetailStep.value = computeInitialStep(activeTask.value)
  detailVisible.value = true
}

async function handleCreateTask() {
  if (!canCreateTaskPermission.value) return
  if (!taskForm.requirements.trim()) {
    message.warning('请填写教学资源要求')
    return
  }
  creating.value = true
  try {
    const result = await createTeachingResourceGenerationTask({ ...taskForm })
    message.success('任务已加入处理队列')
    createModalVisible.value = false
    await loadTasks()
    await openDetail(result.id)
  } catch (error) {
    message.error(error.message || '创建任务失败')
  } finally {
    creating.value = false
  }
}

async function handleSaveResourceMeta(options = {}) {
  if (!activeTask.value || activeTask.value.status !== 'completed') return true
  if (!resourceMetaForm.resourceTitle?.trim()) {
    message.warning('请填写标题')
    return false
  }
  if (resourceMetaForm.scopeType !== 'all' && !resourceMetaForm.scopeTargetIds.length) {
    message.warning('请选择可见范围目标')
    return false
  }
  try {
    const result = await updateTeachingResourceGenerationTaskMeta(activeTask.value.id, {
      resourceTitle: resourceMetaForm.resourceTitle.trim(),
      resourceSummary: resourceMetaForm.resourceSummary || '',
      tags: normalizeTags(resourceMetaForm.tags),
      scopeType: resourceMetaForm.scopeType,
      scopeTargetIds: resourceMetaForm.scopeTargetIds,
    })
    activeTask.value = result
    syncResourceMetaForm(result)
    if (!options.silentSuccess) {
      message.success('资源基础信息已保存')
    }
    return true
  } catch (error) {
    message.error(error.message || '保存基础信息失败')
    return false
  }
}

async function handleConfirmTask() {
  if (!canConfirmTaskPermission.value || !activeTask.value) return
  confirming.value = true
  try {
    const saved = await handleSaveResourceMeta({ silentSuccess: true })
    if (!saved) return
    const result = await confirmTeachingResourceGenerationTask(activeTask.value.id)
    activeTask.value = result
    syncResourceMetaForm(result)
    currentDetailStep.value = 4
    await loadTasks()
    message.success('已确认保存为资源草稿，可继续走审核流程')
  } catch (error) {
    message.error(error.message || '确认失败')
  } finally {
    confirming.value = false
  }
}

onMounted(() => {
  fetchTagOptions().catch(() => {})
  loadTasks()
})
</script>

<style scoped>
.teaching-resource-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
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

/* List Card */
.list-card {
  border-radius: 12px;
}

.list-card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

/* Task List */
.task-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.task-list-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 12px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.task-list-row:last-child {
  border-bottom: none;
}

.task-list-row:hover {
  background: #f7f9ff;
}

.task-row-actions {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex-shrink: 0;
  min-width: 72px;
}

.task-row-content {
  flex: 1;
  min-width: 0;
}

.task-row-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f1f1f;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-row-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #8c8c8c;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-row-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
}

.task-row-time {
  font-size: 12px;
  color: #bfbfbf;
}

/* Detail Card */
.detail-card {
  border-radius: 12px;
}

.detail-card-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-card-name {
  font-size: 16px;
  font-weight: 600;
  color: #001234;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Step Navigation */
.detail-step-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 20px;
  padding: 12px 16px;
  border-radius: 8px;
  background: #fafbfc;
  border: 1px solid #f0f0f0;
}

.detail-step-label {
  font-size: 15px;
  font-weight: 600;
  color: #1f1f1f;
}

/* Detail Sections */
.detail-section {
  margin-top: 20px;
}

.detail-section-title {
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 600;
  color: #1f1f1f;
}

.multiline-text {
  white-space: pre-wrap;
  line-height: 1.7;
}

.generation-status {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 24px;
  padding: 24px;
  border-radius: 10px;
  background: rgba(0, 48, 135, 0.03);
  color: #595959;
  font-size: 14px;
}

.generation-failed {
  background: rgba(255, 77, 79, 0.03);
}

.template-alert,
.template-result-alert {
  margin-bottom: 16px;
}

.meta-form {
  max-width: 720px;
}

.confirm-actions {
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

/* Page Plan Grid */
.page-plan-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.page-plan-card {
  padding: 14px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #eef0f5;
}

.page-plan-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.page-plan-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f1f1f;
}

.page-plan-subtitle {
  margin-top: 6px;
  color: #8c8c8c;
  line-height: 1.6;
}

.page-plan-list {
  margin: 12px 0 0;
  padding-left: 18px;
  color: #333;
  line-height: 1.7;
}

.page-plan-highlight {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(0, 48, 135, 0.05);
  color: #0d3f8a;
}

/* Preview Frame */
.preview-frame {
  width: 100%;
  min-height: 720px;
  border: 1px solid #eef0f5;
  border-radius: 12px;
  background: #fff;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
  }

  .task-list-row {
    flex-wrap: wrap;
  }

  .task-row-actions {
    flex-direction: row;
    min-width: auto;
  }

  .page-plan-grid {
    grid-template-columns: 1fr;
  }

  .preview-frame {
    min-height: 560px;
  }

  .detail-step-nav {
    gap: 8px;
  }
}
</style>
