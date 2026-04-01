<template>
  <div class="page-content resource-page">
    <LearningResourceTabs />

    <div class="page-header">
      <div>
        <h1 class="page-title">教学资源生成</h1>
        <p class="page-subtitle">描述教学需求，系统智能生成课件资源。</p>
      </div>
      <a-space>
        <a-button @click="router.push('/resource/my')">返回我的空间</a-button>
        <PermissionsTooltip :allowed="canCreateTaskPermission" tips="需要 USE_TEACHING_RESOURCE_GENERATION 权限">
          <template #default="{ disabled }">
            <a-button type="primary" :disabled="disabled" @click="createModalVisible = true">新建任务</a-button>
          </template>
        </PermissionsTooltip>
      </a-space>
    </div>

    <template v-if="!detailVisible">
      <a-card :bordered="false" class="list-card">
        <template #title>
          <div class="list-title">
            <span>任务列表</span>
            <a-button @click="loadTasks">刷新</a-button>
          </div>
        </template>
        <a-spin :spinning="taskLoading">
          <a-empty v-if="!taskList.length" description="暂无教学资源生成任务" />
          <div v-else class="task-list">
            <div v-for="item in taskList" :key="item.id" class="task-row">
              <div class="task-main">
                <h3>{{ item.task_name }}</h3>
                <p>{{ item.summary_text || '等待生成结果' }}</p>
              </div>
              <div class="task-side">
                <a-tag :color="getResourceStatusColor(item.status)">{{ getResourceStatusLabel(item.status) }}</a-tag>
                <span>{{ formatDateTime(item.created_at) }}</span>
              </div>
              <div class="task-actions">
                <a-button type="link" size="small" @click="openDetail(item.id)">详情</a-button>
                <a-button
                  v-if="(item as TaskSummary).confirmed_resource_id"
                  type="link"
                  size="small"
                  @click="router.push(`/resource/detail/${(item as TaskSummary).confirmed_resource_id}`)"
                >
                  查看资源
                </a-button>
              </div>
            </div>
          </div>
        </a-spin>
      </a-card>
    </template>

    <template v-else-if="activeTask">
      <a-card :bordered="false" class="detail-card">
        <template #title>
          <div class="detail-title">
            <a-button @click="closeDetail">返回列表</a-button>
            <span>{{ activeTask.resource_meta?.resource_title || activeTask.preview_title || activeTask.task_name }}</span>
          </div>
        </template>
        <template #extra>
          <a-button @click="loadTaskDetail(activeTask.id)">刷新</a-button>
        </template>

        <AiTaskTimeline
          mode="resource-generation"
          :status="activeTask.status"
          :created-at="activeTask.created_at || undefined"
          :completed-at="activeTask.completed_at || undefined"
          :confirmed-at="activeTask.confirmed_at || undefined"
          :active-step="currentDetailStep"
        />

        <div class="step-nav">
          <a-button :disabled="currentDetailStep <= 0" @click="currentDetailStep -= 1">上一步</a-button>
          <span>{{ detailStepLabels[currentDetailStep] }}</span>
          <a-button :disabled="currentDetailStep >= maxDetailStep" @click="currentDetailStep += 1">下一步</a-button>
        </div>

        <div v-show="currentDetailStep <= 1" class="detail-section">
          <div class="section-title">任务请求</div>
          <a-descriptions :column="2" size="small" bordered>
            <a-descriptions-item label="模板">通用教学课件模板</a-descriptions-item>
            <a-descriptions-item label="标题生成">系统自动生成</a-descriptions-item>
            <a-descriptions-item label="教学资源要求" :span="2">
              <div class="multiline">{{ activeTask.request_payload.requirements }}</div>
            </a-descriptions-item>
          </a-descriptions>
        </div>

        <div v-show="currentDetailStep === 2" class="detail-section">
          <div class="section-title">解析结果</div>
          <a-empty v-if="!activeTask.parsed_request" description="任务尚未生成解析结果" />
          <template v-else>
            <a-descriptions :column="2" size="small" bordered>
              <a-descriptions-item label="主题">{{ activeTask.parsed_request.theme }}</a-descriptions-item>
              <a-descriptions-item label="适用对象">{{ activeTask.parsed_request.target_audience || '未指定' }}</a-descriptions-item>
              <a-descriptions-item label="使用场景">{{ activeTask.parsed_request.usage_scenario || '未指定' }}</a-descriptions-item>
              <a-descriptions-item label="表达风格">{{ activeTask.parsed_request.tone || '未指定' }}</a-descriptions-item>
              <a-descriptions-item label="关键词">{{ formatTagList(activeTask.parsed_request.keywords) }}</a-descriptions-item>
              <a-descriptions-item label="学习目标">{{ formatTagList(activeTask.parsed_request.learning_goals) }}</a-descriptions-item>
            </a-descriptions>
          </template>

          <div class="section-title section-gap">模板与页面方案</div>
          <a-empty v-if="!activeTask.page_plan?.length" description="任务尚未生成页面方案" />
          <div v-else class="page-plan-grid">
            <div v-for="page in activeTask.page_plan" :key="page.page_no" class="page-plan-card">
              <div class="page-head">
                <a-tag color="blue">第 {{ page.page_no }} 页</a-tag>
                <a-tag>{{ page.page_type }}</a-tag>
              </div>
              <h4>{{ page.title }}</h4>
              <p v-if="page.subtitle">{{ page.subtitle }}</p>
              <ul>
                <li v-for="(bullet, index) in page.bullets || []" :key="`${page.page_no}-${index}`">{{ bullet }}</li>
              </ul>
            </div>
          </div>
        </div>

        <div v-show="currentDetailStep === 3" class="detail-section">
          <div class="section-title">课件预览</div>
          <a-empty v-if="!activeTask.html_content" description="任务尚未生成 HTML 课件" />
          <iframe
            v-else
            class="preview-frame"
            :srcdoc="activeTask.html_content"
            sandbox="allow-scripts"
            title="教学资源预览"
          />
        </div>

        <div v-show="currentDetailStep === 4" class="detail-section">
          <div class="section-title">资源基础信息</div>
          <a-empty v-if="!['completed', 'confirmed'].includes(activeTask.status)" description="生成完成后可填写资源基础信息" />
          <template v-else>
            <a-form v-if="activeTask.status === 'completed'" layout="vertical">
              <a-form-item label="标题" required>
                <a-input v-model:value="resourceMetaForm.resource_title" :maxlength="200" placeholder="请输入资源标题" />
              </a-form-item>
              <a-form-item label="资源摘要">
                <a-textarea v-model:value="resourceMetaForm.resource_summary" :rows="3" :maxlength="1000" show-count />
              </a-form-item>
              <a-form-item label="资源标签">
                <a-select
                  v-model:value="resourceMetaForm.tags"
                  mode="tags"
                  show-search
                  :options="mergedTagOptions"
                  :filter-option="false"
                  :loading="tagSearching"
                  style="width: 100%"
                  @search="handleTagSearch"
                  @change="handleTagChange"
                />
              </a-form-item>
              <a-form-item label="可见范围">
                <AdmissionScopeSelector
                  v-model:scope-type="resourceMetaForm.scope_type"
                  v-model:scope-target-ids="resourceMetaForm.scope_target_ids"
                  user-role=""
                  all-hint="全部用户都可以查看确认后的资源草稿。"
                  user-placeholder="请选择可查看资源的用户"
                  department-placeholder="请选择可查看资源的部门"
                  role-placeholder="请选择可查看资源的角色"
                  user-hint="仅选中的用户可以查看确认后的资源。"
                  department-hint="选中部门下的用户可以查看确认后的资源。"
                  role-hint="拥有选中角色的用户可以查看确认后的资源。"
                />
              </a-form-item>
              <PermissionsTooltip :allowed="canConfirmTaskPermission" tips="需要 USE_TEACHING_RESOURCE_GENERATION 权限">
                <template #default="{ disabled }">
                  <a-button type="primary" :loading="confirming" :disabled="disabled" @click="handleConfirmTask">
                    确认保存资源草稿
                  </a-button>
                </template>
              </PermissionsTooltip>
            </a-form>

            <a-result v-else status="success" title="已保存为资源草稿" sub-title="可继续在我的空间中走审核流程">
              <template #extra>
                <a-button v-if="activeTask.confirmed_resource_id" type="primary" @click="router.push(`/resource/detail/${activeTask.confirmed_resource_id}`)">
                  查看资源
                </a-button>
              </template>
            </a-result>
          </template>
        </div>
      </a-card>
    </template>

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
        <a-form-item label="教学资源要求" required extra="建议写明课件主题、适用对象、希望强调的重点、案例场景或课堂用途。">
          <a-textarea v-model:value="taskForm.requirements" :rows="7" :maxlength="4000" show-count />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, toRef } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import type { AITaskSummaryResponse, TeachingResourceGenerationTaskDetailResponse } from '@/api/learning-resource'
import {
  confirmTeachingResourceGenerationTask,
  createResourceTag,
  createTeachingResourceGenerationTask,
  getTeachingResourceGenerationTaskDetail,
  listResourceTags,
  listTeachingResourceGenerationTasks,
  updateTeachingResourceGenerationTaskMeta,
} from '@/api/learning-resource'
import { useAuthStore } from '@/stores/auth'
import { useCreatableTagSelect } from '@/composables/useCreatableTagSelect'
import LearningResourceTabs from '@/components/resource/LearningResourceTabs.vue'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'
import AdmissionScopeSelector from '@/components/common/AdmissionScopeSelector.vue'
import AiTaskTimeline from '@/components/common/AiTaskTimeline.vue'
import { formatDateTime, formatTagList, getResourceStatusColor, getResourceStatusLabel } from '@/utils/learning-resource'

type TaskSummary = AITaskSummaryResponse & { confirmed_resource_id?: number | null }

const router = useRouter()
const authStore = useAuthStore()

const creating = ref(false)
const confirming = ref(false)
const taskLoading = ref(false)
const createModalVisible = ref(false)
const detailVisible = ref(false)
const currentDetailStep = ref(0)
const taskList = ref<TaskSummary[]>([])
const activeTask = ref<TeachingResourceGenerationTaskDetailResponse | null>(null)

const detailStepLabels = ['任务请求', '智能生成', '查看结果', '预览', '确认完成']

const taskForm = reactive({
  requirements: '',
})

const resourceMetaForm = reactive({
  resource_title: '',
  resource_summary: '',
  tags: [] as string[],
  scope_type: 'all',
  scope_target_ids: [] as number[],
})

const {
  tagSearching,
  mergedTagOptions,
  normalizeTags,
  fetchTagOptions,
  handleTagSearch,
  handleTagChange,
} = useCreatableTagSelect(toRef(resourceMetaForm, 'tags'), {
  fetchTags: listResourceTags,
  createTag: createResourceTag,
})

const canCreateTaskPermission = computed(() => authStore.hasPermission('USE_TEACHING_RESOURCE_GENERATION'))
const canConfirmTaskPermission = computed(() => authStore.hasPermission('USE_TEACHING_RESOURCE_GENERATION'))

const maxDetailStep = computed(() => {
  if (!activeTask.value) {
    return 0
  }
  if (activeTask.value.status === 'confirmed' || activeTask.value.status === 'completed') {
    return 4
  }
  if (['pending', 'processing', 'failed'].includes(activeTask.value.status)) {
    return 1
  }
  return 0
})

onMounted(() => {
  void loadTasks()
})

function syncResourceMetaForm(task: TeachingResourceGenerationTaskDetailResponse | null) {
  const meta = task?.resource_meta
  resourceMetaForm.resource_title = meta?.resource_title || ''
  resourceMetaForm.resource_summary = meta?.resource_summary || ''
  resourceMetaForm.tags = [...(meta?.tags || [])]
  resourceMetaForm.scope_type = meta?.scope_type || 'all'
  resourceMetaForm.scope_target_ids = [...(meta?.scope_target_ids || [])]
}

function computeInitialStep(task: TeachingResourceGenerationTaskDetailResponse | null) {
  if (!task) {
    return 0
  }
  if (task.status === 'confirmed') return 4
  if (task.status === 'completed') return 2
  if (['processing', 'pending', 'failed'].includes(task.status)) return 1
  return 0
}

async function loadTasks() {
  taskLoading.value = true
  try {
    const response = await listTeachingResourceGenerationTasks({ page: 1, size: 30 })
    taskList.value = (response.items || []) as TaskSummary[]
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载任务失败')
  } finally {
    taskLoading.value = false
  }
}

async function loadTaskDetail(taskId: number) {
  try {
    activeTask.value = await getTeachingResourceGenerationTaskDetail(taskId)
    syncResourceMetaForm(activeTask.value)
    currentDetailStep.value = computeInitialStep(activeTask.value)
    await fetchTagOptions()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载任务详情失败')
  }
}

async function openDetail(taskId: number) {
  await loadTaskDetail(taskId)
  detailVisible.value = true
}

function closeDetail() {
  detailVisible.value = false
  activeTask.value = null
}

async function handleCreateTask() {
  if (!taskForm.requirements.trim()) {
    message.warning('请填写教学资源要求')
    return
  }
  creating.value = true
  try {
    const task = await createTeachingResourceGenerationTask({
      requirements: taskForm.requirements.trim(),
      scope_type: 'all',
      scope_target_ids: [],
      tags: [],
      template_code: 'general_teaching_slides',
    })
    taskForm.requirements = ''
    createModalVisible.value = false
    message.success('任务已创建')
    await loadTasks()
    await openDetail(task.id)
  } catch (error) {
    message.error(error instanceof Error ? error.message : '创建任务失败')
  } finally {
    creating.value = false
  }
}

async function handleConfirmTask() {
  if (!activeTask.value) {
    return
  }
  if (!resourceMetaForm.resource_title.trim()) {
    message.warning('请填写资源标题')
    return
  }
  if (resourceMetaForm.scope_type !== 'all' && !resourceMetaForm.scope_target_ids.length) {
    message.warning('请选择可见范围目标')
    return
  }

  confirming.value = true
  try {
    const updatedTask = await updateTeachingResourceGenerationTaskMeta(activeTask.value.id, {
      resource_title: resourceMetaForm.resource_title.trim(),
      resource_summary: resourceMetaForm.resource_summary || undefined,
      tags: normalizeTags(resourceMetaForm.tags),
      scope_type: resourceMetaForm.scope_type,
      scope_target_ids: resourceMetaForm.scope_target_ids,
    })
    activeTask.value = await confirmTeachingResourceGenerationTask(updatedTask.id)
    syncResourceMetaForm(activeTask.value)
    currentDetailStep.value = 4
    message.success('已保存为资源草稿')
    await loadTasks()
  } catch (error) {
    message.error(error instanceof Error ? error.message : '确认保存失败')
  } finally {
    confirming.value = false
  }
}
</script>

<style scoped>
.page-header,
.list-title,
.detail-title,
.step-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.page-header {
  margin-bottom: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 6px;
}

.page-subtitle {
  color: var(--v2-text-secondary);
}

.list-card,
.detail-card {
  border-radius: var(--v2-radius-lg);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 16px;
  padding: 16px;
  border: 1px solid var(--v2-border);
  border-radius: var(--v2-radius);
}

.task-main h3 {
  margin-bottom: 6px;
}

.task-main p,
.task-side {
  color: var(--v2-text-secondary);
}

.task-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
}

.step-nav {
  margin: 18px 0;
}

.detail-section {
  margin-top: 18px;
}

.section-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 14px;
}

.section-gap {
  margin-top: 24px;
}

.multiline {
  white-space: pre-wrap;
  line-height: 1.8;
}

.page-plan-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
}

.page-plan-card {
  border: 1px solid var(--v2-border);
  border-radius: var(--v2-radius);
  padding: 14px;
  background: var(--v2-bg-card);
}

.page-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}

.page-plan-card h4 {
  margin-bottom: 6px;
}

.page-plan-card p,
.page-plan-card ul {
  color: var(--v2-text-secondary);
}

.preview-frame {
  width: 100%;
  min-height: 72vh;
  border: 1px solid var(--v2-border);
  border-radius: var(--v2-radius);
  background: #fff;
}

.template-alert {
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .page-header,
  .list-title,
  .detail-title,
  .step-nav,
  .task-row {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }

  .task-side {
    align-items: flex-start;
  }
}
</style>
