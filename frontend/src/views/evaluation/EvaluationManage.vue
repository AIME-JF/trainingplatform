<template>
  <div class="evaluation-manage-page">
    <div class="page-header">
      <h2>评价管理</h2>
    </div>

    <a-card :bordered="false">
      <a-tabs v-model:activeKey="activeTab">
        <!-- ========== 维度配置 ========== -->
        <a-tab-pane key="dimensions" tab="维度配置">
          <a-tabs v-model:activeKey="activeTargetType" size="small" type="card" style="margin-bottom: 16px">
            <a-tab-pane key="course" tab="课程评价" />
            <a-tab-pane key="instructor" tab="教官评价" />
            <a-tab-pane key="training" tab="培训班评价" />
            <a-tab-pane key="training_base" tab="培训基地评价" />
          </a-tabs>

          <a-spin :spinning="templateLoading">
            <div v-if="currentTemplate" class="template-info">
              <a-descriptions :column="2" size="small" bordered>
                <a-descriptions-item label="模板名称">{{ currentTemplate.name }}</a-descriptions-item>
                <a-descriptions-item label="状态">
                  <a-switch
                    :checked="currentTemplate.enabled"
                    checked-children="启用"
                    un-checked-children="停用"
                    @change="(val) => handleToggleTemplate(val)"
                  />
                </a-descriptions-item>
                <a-descriptions-item label="说明" :span="2">{{ currentTemplate.description || '未设置' }}</a-descriptions-item>
              </a-descriptions>
            </div>

            <div class="dim-toolbar">
              <span class="dim-title">评价维度</span>
              <a-button type="primary" size="small" @click="openDimModal()">添加维度</a-button>
            </div>

            <a-table
              :data-source="currentDimensions"
              :columns="dimColumns"
              :pagination="false"
              row-key="id"
              size="small"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'action'">
                  <a-space>
                    <a-button type="link" size="small" @click="openDimModal(record)">编辑</a-button>
                    <a-popconfirm title="确定删除该维度？" @confirm="handleDeleteDim(record.id)">
                      <a-button type="link" size="small" danger>删除</a-button>
                    </a-popconfirm>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-spin>
        </a-tab-pane>

        <!-- ========== 评价任务 ========== -->
        <a-tab-pane key="tasks" tab="评价任务">
          <div class="dim-toolbar">
            <a-space>
              <a-select v-model:value="taskFilterType" placeholder="对象类型" allow-clear style="width: 140px" @change="fetchTasks">
                <a-select-option value="course">课程</a-select-option>
                <a-select-option value="instructor">教官</a-select-option>
                <a-select-option value="training">培训班</a-select-option>
                <a-select-option value="training_base">培训基地</a-select-option>
              </a-select>
              <a-select v-model:value="taskFilterStatus" placeholder="状态" allow-clear style="width: 120px" @change="fetchTasks">
                <a-select-option value="active">进行中</a-select-option>
                <a-select-option value="closed">已关闭</a-select-option>
                <a-select-option value="draft">草稿</a-select-option>
              </a-select>
            </a-space>
            <a-button type="primary" size="small" @click="openTaskModal()">发布任务</a-button>
          </div>

          <a-table
            :data-source="taskList"
            :columns="taskColumns"
            :loading="taskLoading"
            :pagination="false"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'targetType'">
                {{ targetTypeLabels[record.targetType] || record.targetType }}
              </template>
              <template v-if="column.key === 'status'">
                <a-tag :color="taskStatusColor(record.status)">{{ taskStatusLabel(record.status) }}</a-tag>
              </template>
              <template v-if="column.key === 'action'">
                <a-space>
                  <a-button v-if="record.status === 'active'" type="link" size="small" @click="handleCloseTask(record.id)">关闭</a-button>
                  <a-popconfirm title="确定删除该任务？" @confirm="handleDeleteTask(record.id)">
                    <a-button type="link" size="small" danger>删除</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-tab-pane>

        <!-- ========== 评价记录 ========== -->
        <a-tab-pane key="records" tab="评价记录">
          <div class="dim-toolbar">
            <a-space>
              <a-select v-model:value="recordFilterType" placeholder="对象类型" allow-clear style="width: 140px" @change="fetchRecords">
                <a-select-option value="course">课程</a-select-option>
                <a-select-option value="instructor">教官</a-select-option>
                <a-select-option value="training">培训班</a-select-option>
                <a-select-option value="training_base">培训基地</a-select-option>
              </a-select>
            </a-space>
          </div>

          <a-table
            :data-source="recordList"
            :columns="recordColumns"
            :loading="recordLoading"
            :pagination="false"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'targetType'">
                {{ targetTypeLabels[record.targetType] || record.targetType }}
              </template>
              <template v-if="column.key === 'avgScore'">
                <a-rate :value="record.avgScore" disabled allow-half :count="5" style="font-size: 14px" />
                <span style="margin-left: 4px; color: #faad14">{{ record.avgScore }}</span>
              </template>
            </template>
          </a-table>
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- 维度编辑弹窗 -->
    <a-modal
      v-model:open="dimModalVisible"
      :title="dimEditingId ? '编辑维度' : '添加维度'"
      :confirm-loading="dimSaving"
      ok-text="保存"
      @ok="handleSaveDim"
    >
      <a-form layout="vertical">
        <a-form-item label="维度名称" required>
          <a-input v-model:value="dimForm.name" placeholder="如：教学质量" :maxlength="100" />
        </a-form-item>
        <a-form-item label="维度说明">
          <a-input v-model:value="dimForm.description" placeholder="选填" :maxlength="500" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="排序">
              <a-input-number v-model:value="dimForm.sortOrder" :min="0" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="权重">
              <a-input-number v-model:value="dimForm.weight" :min="0" :step="0.1" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <!-- 任务发布弹窗 -->
    <a-modal
      v-model:open="taskModalVisible"
      title="发布评价任务"
      :confirm-loading="taskSaving"
      ok-text="发布"
      @ok="handleCreateTask"
    >
      <a-form layout="vertical">
        <a-form-item label="任务标题" required>
          <a-input v-model:value="taskForm.title" placeholder="如：2026春季培训班评价" :maxlength="200" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="评价对象类型" required>
              <a-select v-model:value="taskForm.targetType" placeholder="选择类型">
                <a-select-option value="course">课程</a-select-option>
                <a-select-option value="instructor">教官</a-select-option>
                <a-select-option value="training">培训班</a-select-option>
                <a-select-option value="training_base">培训基地</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="被评对象ID" required>
              <a-input-number v-model:value="taskForm.targetId" :min="1" style="width: 100%" placeholder="对象ID" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="关联培训班ID">
          <a-input-number v-model:value="taskForm.trainingId" :min="1" style="width: 100%" placeholder="选填" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="开始时间">
              <a-date-picker v-model:value="taskForm.startTime" show-time style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="截止时间">
              <a-date-picker v-model:value="taskForm.endTime" show-time style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/api/request'

const activeTab = ref('dimensions')
const activeTargetType = ref('course')

const targetTypeLabels = {
  course: '课程',
  instructor: '教官',
  training: '培训班',
  training_base: '培训基地',
}

// ========== 模板与维度 ==========
const templateLoading = ref(false)
const templates = ref([])

const currentTemplate = computed(() =>
  templates.value.find((t) => t.targetType === activeTargetType.value) || null,
)
const currentDimensions = computed(() => currentTemplate.value?.dimensions || [])

const dimColumns = [
  { title: '排序', dataIndex: 'sortOrder', key: 'sortOrder', width: 70 },
  { title: '维度名称', dataIndex: 'name', key: 'name' },
  { title: '说明', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '权重', dataIndex: 'weight', key: 'weight', width: 80 },
  { title: '操作', key: 'action', width: 140 },
]

async function fetchTemplates() {
  templateLoading.value = true
  try {
    templates.value = await request.get('/evaluations/templates') || []
  } catch {
    templates.value = []
  } finally {
    templateLoading.value = false
  }
}

async function handleToggleTemplate(enabled) {
  if (!currentTemplate.value) return
  try {
    await request.put(`/evaluations/templates/${currentTemplate.value.id}`, { enabled })
    message.success(enabled ? '已启用' : '已停用')
    fetchTemplates()
  } catch (err) {
    message.error(err.message || '操作失败')
  }
}

// 维度弹窗
const dimModalVisible = ref(false)
const dimSaving = ref(false)
const dimEditingId = ref(null)
const dimForm = reactive({ name: '', description: '', sortOrder: 0, weight: 1.0 })

function openDimModal(record) {
  if (record) {
    dimEditingId.value = record.id
    dimForm.name = record.name || ''
    dimForm.description = record.description || ''
    dimForm.sortOrder = record.sortOrder ?? 0
    dimForm.weight = record.weight ?? 1.0
  } else {
    dimEditingId.value = null
    dimForm.name = ''
    dimForm.description = ''
    dimForm.sortOrder = currentDimensions.value.length
    dimForm.weight = 1.0
  }
  dimModalVisible.value = true
}

async function handleSaveDim() {
  if (!dimForm.name.trim()) {
    message.warning('请输入维度名称')
    return
  }
  dimSaving.value = true
  try {
    const payload = {
      name: dimForm.name.trim(),
      description: dimForm.description?.trim() || undefined,
      sortOrder: dimForm.sortOrder,
      weight: dimForm.weight,
    }
    if (dimEditingId.value) {
      await request.put(`/evaluations/dimensions/${dimEditingId.value}`, payload)
      message.success('维度已更新')
    } else {
      await request.post(`/evaluations/templates/${currentTemplate.value.id}/dimensions`, payload)
      message.success('维度已添加')
    }
    dimModalVisible.value = false
    fetchTemplates()
  } catch (err) {
    message.error(err.message || '保存失败')
  } finally {
    dimSaving.value = false
  }
}

async function handleDeleteDim(dimId) {
  try {
    await request.delete(`/evaluations/dimensions/${dimId}`)
    message.success('已删除')
    fetchTemplates()
  } catch (err) {
    message.error(err.message || '删除失败')
  }
}

// ========== 任务 ==========
const taskLoading = ref(false)
const taskList = ref([])
const taskFilterType = ref(undefined)
const taskFilterStatus = ref(undefined)

const taskColumns = [
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '对象类型', key: 'targetType', width: 100 },
  { title: '对象ID', dataIndex: 'targetId', key: 'targetId', width: 80 },
  { title: '状态', key: 'status', width: 90 },
  { title: '填写数', dataIndex: 'recordCount', key: 'recordCount', width: 80 },
  { title: '操作', key: 'action', width: 120 },
]

function taskStatusColor(s) {
  return { active: 'green', closed: 'default', draft: 'orange' }[s] || 'default'
}
function taskStatusLabel(s) {
  return { active: '进行中', closed: '已关闭', draft: '草稿' }[s] || s
}

async function fetchTasks() {
  taskLoading.value = true
  try {
    const params = {}
    if (taskFilterType.value) params.targetType = taskFilterType.value
    if (taskFilterStatus.value) params.status = taskFilterStatus.value
    taskList.value = await request.get('/evaluations/tasks', { params }) || []
  } catch {
    taskList.value = []
  } finally {
    taskLoading.value = false
  }
}

// 任务发布弹窗
const taskModalVisible = ref(false)
const taskSaving = ref(false)
const taskForm = reactive({
  title: '',
  targetType: undefined,
  targetId: undefined,
  trainingId: undefined,
  startTime: null,
  endTime: null,
})

function openTaskModal() {
  taskForm.title = ''
  taskForm.targetType = undefined
  taskForm.targetId = undefined
  taskForm.trainingId = undefined
  taskForm.startTime = null
  taskForm.endTime = null
  taskModalVisible.value = true
}

async function handleCreateTask() {
  if (!taskForm.title?.trim() || !taskForm.targetType || !taskForm.targetId) {
    message.warning('请填写必填项')
    return
  }
  taskSaving.value = true
  try {
    await request.post('/evaluations/tasks', {
      title: taskForm.title.trim(),
      targetType: taskForm.targetType,
      targetId: taskForm.targetId,
      trainingId: taskForm.trainingId || undefined,
      startTime: taskForm.startTime?.toISOString?.() || undefined,
      endTime: taskForm.endTime?.toISOString?.() || undefined,
    })
    message.success('评价任务已发布')
    taskModalVisible.value = false
    fetchTasks()
  } catch (err) {
    message.error(err.message || '发布失败')
  } finally {
    taskSaving.value = false
  }
}

async function handleCloseTask(taskId) {
  try {
    await request.put(`/evaluations/tasks/${taskId}`, { status: 'closed' })
    message.success('任务已关闭')
    fetchTasks()
  } catch (err) {
    message.error(err.message || '操作失败')
  }
}

async function handleDeleteTask(taskId) {
  try {
    await request.delete(`/evaluations/tasks/${taskId}`)
    message.success('已删除')
    fetchTasks()
  } catch (err) {
    message.error(err.message || '删除失败')
  }
}

// ========== 记录 ==========
const recordLoading = ref(false)
const recordList = ref([])
const recordFilterType = ref(undefined)

const recordColumns = [
  { title: '评价人', dataIndex: 'userNickname', key: 'userNickname', width: 100, customRender: ({ record }) => record.userNickname || record.userName },
  { title: '对象类型', key: 'targetType', width: 100 },
  { title: '对象ID', dataIndex: 'targetId', key: 'targetId', width: 80 },
  { title: '评分', key: 'avgScore', width: 200 },
  { title: '评语', dataIndex: 'comment', key: 'comment', ellipsis: true },
  { title: '时间', dataIndex: 'createdAt', key: 'createdAt', width: 160 },
]

async function fetchRecords() {
  recordLoading.value = true
  try {
    const params = {}
    if (recordFilterType.value) params.targetType = recordFilterType.value
    recordList.value = await request.get('/evaluations/records', { params }) || []
  } catch {
    recordList.value = []
  } finally {
    recordLoading.value = false
  }
}

// ========== 生命周期 ==========
onMounted(() => {
  fetchTemplates()
})

watch(activeTab, (tab) => {
  if (tab === 'tasks' && !taskList.value.length) fetchTasks()
  if (tab === 'records' && !recordList.value.length) fetchRecords()
})
</script>

<style scoped>
.evaluation-manage-page { padding: 0; }
.page-header { margin-bottom: 16px; }
.page-header h2 { margin: 0; color: #001234; }
.template-info { margin-bottom: 16px; }
.dim-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.dim-title { font-size: 15px; font-weight: 600; color: #1f1f1f; }
</style>
