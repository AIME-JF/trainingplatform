<template>
  <ai-task-tabs-layout
    v-model:active-tab="activeTab"
    title="教学资源生成"
    subtitle="填写自然语言要求后创建任务，系统会先生成预览课件；资源摘要、标签和可见范围在预览后补充"
    tag-text="建议型任务"
    :task-list="taskList"
    :task-loading="taskLoading"
    :active-task-id="activeTask?.id || null"
    :status-labels="statusLabels"
    :status-colors="statusColors"
    empty-text="暂无教学资源生成任务"
    @refresh-tasks="loadTasks"
    @select-task="selectTask"
  >
    <template #header-extra>
      <a-button @click="$router.push('/resource/my')">返回我的资源</a-button>
    </template>

    <template #create>
      <div class="create-form-wrap">
        <a-form layout="vertical">
          <a-alert
            type="info"
            show-icon
            class="template-alert"
            message="当前版本使用固定的“通用教学课件模板”生成内容"
            description="现在只需填写自然语言要求。系统会先生成预览课件，等你查看结果后，再在详情页补资源摘要、标签和可见范围；标题由系统自动生成。"
          />

          <a-form-item
            label="自然语言要求"
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

          <permissions-tooltip
            :allowed="canCreateTaskPermission"
            tips="需要 CREATE_RESOURCE 或 VIEW_RESOURCE_ALL 权限"
            block
            v-slot="{ disabled }"
          >
            <a-button type="primary" block :loading="creating" :disabled="disabled" @click="handleCreateTask">
              创建教学资源生成任务
            </a-button>
          </permissions-tooltip>
        </a-form>
      </div>
    </template>

    <template #task-description="{ item }">
      {{ item.itemCount || 0 }} 页 · {{ item.summaryText || '等待生成结果' }}
    </template>

    <template #detail>
      <template v-if="activeTask">
        <div class="detail-header">
          <div>
            <div class="detail-title">{{ activeTask.resourceMeta?.resourceTitle || activeTask.previewTitle || activeTask.taskName }}</div>
            <div class="detail-sub">任务名称：{{ activeTask.taskName }}</div>
          </div>
          <a-space>
            <a-button @click="loadTaskDetail(activeTask.id)">刷新详情</a-button>
            <a-button
              v-if="activeTask.confirmedResourceId"
              @click="$router.push(`/resource/detail/${activeTask.confirmedResourceId}`)"
            >
              查看资源
            </a-button>
            <permissions-tooltip
              :allowed="canConfirmTaskPermission"
              :disabled="activeTask.status !== 'completed'"
              tips="需要 CREATE_RESOURCE 或 VIEW_RESOURCE_ALL 权限"
              v-slot="{ disabled }"
            >
              <a-button type="primary" :loading="confirming" :disabled="disabled" @click="handleConfirmTask">
                确认入资源草稿
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
            <a-descriptions-item label="模板">通用教学课件模板</a-descriptions-item>
            <a-descriptions-item label="标题生成">系统自动生成</a-descriptions-item>
            <a-descriptions-item label="自然语言要求" :span="2">
              <div class="multiline-text">{{ activeTask.requestPayload.requirements }}</div>
            </a-descriptions-item>
          </a-descriptions>
        </div>

        <div class="detail-section">
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
        </div>

        <div class="detail-section">
          <div class="detail-section-title">模板与页面方案</div>
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

        <div class="detail-section">
          <div class="detail-section-title">资源基础信息</div>
          <a-empty
            v-if="!['completed', 'confirmed'].includes(activeTask.status)"
            description="生成预览后可填写资源摘要、标签和可见范围"
          />
          <template v-else>
            <a-alert
              type="info"
              show-icon
              class="template-result-alert"
              message="标题由系统自动生成"
              description="请在确认入资源草稿前补充资源摘要、标签和可见范围。这些信息会直接用于后续资源草稿和审核流。"
            />
            <a-form v-if="activeTask.status === 'completed'" layout="vertical" class="meta-form">
              <a-form-item label="自动生成标题">
                <a-input :value="resourceMetaForm.resourceTitle || '生成完成后显示'" disabled />
              </a-form-item>

              <a-form-item label="资源摘要">
                <a-textarea
                  v-model:value="resourceMetaForm.resourceSummary"
                  :rows="3"
                  :maxlength="1000"
                  show-count
                  :disabled="!isMetaEditable"
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
                  :disabled="!isMetaEditable"
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

              <a-space>
                <permissions-tooltip
                  :allowed="canConfirmTaskPermission"
                  tips="需要 CREATE_RESOURCE 或 VIEW_RESOURCE_ALL 权限"
                  v-slot="{ disabled }"
                >
                  <a-button :loading="metaSaving" :disabled="disabled || !isMetaEditable" @click="handleSaveResourceMeta()">
                    保存基础信息
                  </a-button>
                </permissions-tooltip>
              </a-space>
            </a-form>
            <a-descriptions v-else :column="2" size="small" bordered>
              <a-descriptions-item label="自动生成标题">{{ resourceMetaForm.resourceTitle || '未生成' }}</a-descriptions-item>
              <a-descriptions-item label="可见范围">{{ formatScopeType(resourceMetaForm.scopeType) }}</a-descriptions-item>
              <a-descriptions-item label="资源摘要" :span="2">{{ resourceMetaForm.resourceSummary || '未填写' }}</a-descriptions-item>
              <a-descriptions-item label="资源标签" :span="2">{{ formatTagList(resourceMetaForm.tags) }}</a-descriptions-item>
            </a-descriptions>
          </template>
        </div>

        <div class="detail-section">
          <div class="detail-section-title">HTML 预览</div>
          <a-empty v-if="!activeTask.htmlContent" description="任务尚未生成 HTML 课件" />
          <iframe
            v-else
            class="preview-frame"
            :srcdoc="activeTask.htmlContent"
            sandbox="allow-scripts"
            title="教学资源预览"
          />
        </div>
      </template>
      <a-empty v-else description="请选择任务查看详情" />
    </template>
  </ai-task-tabs-layout>
</template>

<script setup>
import { computed, onMounted, reactive, ref, toRef } from 'vue'
import { message } from 'ant-design-vue'
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
import AiTaskTabsLayout from '@/views/exam/components/AiTaskTabsLayout.vue'
import AiTaskTimeline from '@/views/exam/components/AiTaskTimeline.vue'
import { useCreatableTagSelect } from '@/utils/creatableTagSelect'

const authStore = useAuthStore()
const creating = ref(false)
const confirming = ref(false)
const metaSaving = ref(false)
const taskLoading = ref(false)
const taskList = ref([])
const activeTask = ref(null)
const activeTab = ref('create')
const statusLabels = { pending: '排队中', processing: '处理中', completed: '已完成', confirmed: '已确认', failed: '处理失败' }
const statusColors = { pending: 'default', processing: 'processing', completed: 'blue', confirmed: 'green', failed: 'red' }

const taskForm = reactive({
  requirements: '',
})
const resourceMetaForm = reactive({
  resourceTitle: '',
  resourceSummary: '',
  tags: [],
  scopeType: 'all',
  scopeTargetIds: [],
})

const canCreateTaskPermission = computed(() => authStore.hasAnyPermission(['CREATE_RESOURCE', 'VIEW_RESOURCE_ALL']))
const canConfirmTaskPermission = computed(() => authStore.hasAnyPermission(['CREATE_RESOURCE', 'VIEW_RESOURCE_ALL']))
const isMetaEditable = computed(() => activeTask.value?.status === 'completed' && canConfirmTaskPermission.value)
const pageTypeLabels = {
  cover: '封面页',
  goal: '目标页',
  background: '背景页',
  knowledge: '知识页',
  case: '案例页',
  practice: '建议页',
  summary: '总结页',
}

const {
  tagSearching,
  mergedTagOptions,
  normalizeTags,
  fetchTagOptions,
  handleTagSearch,
  handleTagChange,
} = useCreatableTagSelect(toRef(resourceMetaForm, 'tags'), {
  fetchTags: getResourceTags,
  createTag: createResourceTag,
  createErrorMessage: (tagName, error) => error?.message || `标签“${tagName}”创建失败`,
})

function resetTaskForm() {
  Object.assign(taskForm, {
    requirements: '',
  })
}

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
  const labels = {
    all: '全部',
    user: '指定用户',
    department: '指定部门',
    role: '指定角色',
  }
  return labels[value] || value || '全部'
}

async function loadTasks() {
  taskLoading.value = true
  try {
    const result = await getTeachingResourceGenerationTasks({ size: -1 })
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
    activeTask.value = await getTeachingResourceGenerationTaskDetail(taskId)
    syncResourceMetaForm(activeTask.value)
  } catch (error) {
    message.error(error.message || '加载任务详情失败')
  }
}

async function selectTask(taskId) {
  await loadTaskDetail(taskId)
}

async function handleCreateTask() {
  if (!canCreateTaskPermission.value) return
  if (!taskForm.requirements.trim()) {
    message.warning('请填写自然语言要求')
    return
  }

  creating.value = true
  try {
    const result = await createTeachingResourceGenerationTask({ ...taskForm })
    message.success('任务已加入处理队列')
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

async function handleSaveResourceMeta(options = {}) {
  if (!activeTask.value || activeTask.value.status !== 'completed') return true
  if (resourceMetaForm.scopeType !== 'all' && !resourceMetaForm.scopeTargetIds.length) {
    message.warning('请选择可见范围目标')
    return false
  }
  metaSaving.value = true
  try {
    const result = await updateTeachingResourceGenerationTaskMeta(activeTask.value.id, {
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
  } finally {
    metaSaving.value = false
  }
}

async function handleConfirmTask() {
  if (!canConfirmTaskPermission.value || !activeTask.value) return
  confirming.value = true
  try {
    const saved = await handleSaveResourceMeta({ silentSuccess: true })
    if (!saved) {
      return
    }
    const result = await confirmTeachingResourceGenerationTask(activeTask.value.id)
    activeTask.value = result
    syncResourceMetaForm(result)
    await loadTasks()
    message.success('已确认入资源草稿，可继续走审核流程')
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
.create-form-wrap {
  width: 100%;
  max-width: 920px;
}

.template-alert,
.template-result-alert {
  margin-bottom: 16px;
}

.meta-form {
  max-width: 920px;
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
  color: #1f1f1f;
}

.multiline-text {
  white-space: pre-wrap;
  line-height: 1.7;
}

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

.preview-frame {
  width: 100%;
  min-height: 720px;
  border: 1px solid #eef0f5;
  border-radius: 12px;
  background: #fff;
}

@media (max-width: 768px) {
  .detail-header {
    flex-direction: column;
  }

  .page-plan-grid {
    grid-template-columns: 1fr;
  }

  .preview-frame {
    min-height: 560px;
  }
}
</style>
