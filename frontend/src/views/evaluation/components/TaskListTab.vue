<template>
  <div>
    <div class="tab-toolbar">
      <a-space>
        <a-select v-model:value="filterType" placeholder="对象类型" allow-clear style="width: 140px" @change="fetchTasks">
          <a-select-option value="course">课程</a-select-option>
          <a-select-option value="instructor">教官</a-select-option>
          <a-select-option value="training">培训班</a-select-option>
          <a-select-option value="training_base">培训基地</a-select-option>
        </a-select>
        <a-select v-model:value="filterStatus" placeholder="状态" allow-clear style="width: 120px" @change="fetchTasks">
          <a-select-option value="active">进行中</a-select-option>
          <a-select-option value="closed">已关闭</a-select-option>
          <a-select-option value="draft">草稿</a-select-option>
        </a-select>
      </a-space>
      <a-button type="primary" size="small" @click="openCreateModal">发布任务</a-button>
    </div>

    <a-table :data-source="taskList" :columns="columns" :loading="loading" :pagination="false" row-key="id" size="small">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'targetType'">
          {{ targetTypeLabels[record.targetType] || record.targetType }}
        </template>
        <template v-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button v-if="record.status === 'active'" type="link" size="small" @click="handleClose(record.id)">关闭</a-button>
            <a-popconfirm title="确定删除该任务？" @confirm="handleDelete(record.id)">
              <a-button type="link" size="small" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- 发布弹窗 -->
    <a-modal v-model:open="createVisible" title="发布评价任务" :confirm-loading="creating" ok-text="发布" @ok="handleCreate">
      <a-form layout="vertical">
        <a-form-item label="任务标题" required>
          <a-input v-model:value="form.title" placeholder="如：2026春季培训班评价" :maxlength="200" />
        </a-form-item>
        <a-form-item label="评价对象类型" required>
          <a-select v-model:value="form.targetType" placeholder="选择类型" @change="onTargetTypeChange">
            <a-select-option value="course">课程</a-select-option>
            <a-select-option value="instructor">教官</a-select-option>
            <a-select-option value="training">培训班</a-select-option>
            <a-select-option value="training_base">培训基地</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="被评对象" required>
          <template v-if="form.targetType === 'training'">
            <a-input
              :value="selectedTargetName"
              read-only
              placeholder="点击选择培训班"
              @click="targetTrainingSelectOpen = true"
            >
              <template #suffix>
                <CloseCircleOutlined v-if="form.targetId" style="cursor: pointer; color: #999" @click.stop="clearTarget" />
              </template>
            </a-input>
          </template>
          <a-select
            v-else
            v-model:value="form.targetId"
            :options="targetOptions"
            :loading="targetOptionsLoading"
            show-search
            option-filter-prop="label"
            placeholder="请先选择评价对象类型"
            :disabled="!form.targetType"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="关联培训班">
          <a-input
            :value="selectedTrainingName"
            read-only
            placeholder="点击选择培训班（选填）"
            @click="trainingSelectOpen = true"
          >
            <template #suffix>
              <CloseCircleOutlined v-if="form.trainingId" style="cursor: pointer; color: #999" @click.stop="clearTraining" />
            </template>
          </a-input>
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="开始时间">
              <a-date-picker v-model:value="form.startTime" show-time style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="截止时间">
              <a-date-picker v-model:value="form.endTime" show-time style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <TrainingSelectModal v-model:open="trainingSelectOpen" @select="onTrainingSelected" />
    <TrainingSelectModal v-model:open="targetTrainingSelectOpen" title="选择被评培训班" @select="onTargetTrainingSelected" />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { CloseCircleOutlined } from '@ant-design/icons-vue'
import request from '@/api/request'
import TrainingSelectModal from '@/components/common/TrainingSelectModal.vue'

const targetTypeLabels = { course: '课程', instructor: '教官', training: '培训班', training_base: '培训基地' }

const loading = ref(false)
const taskList = ref([])
const filterType = ref(undefined)
const filterStatus = ref(undefined)

const columns = [
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '对象类型', key: 'targetType', width: 100 },
  { title: '状态', key: 'status', width: 90 },
  { title: '填写数', dataIndex: 'recordCount', key: 'recordCount', width: 80 },
  { title: '操作', key: 'action', width: 120 },
]

function statusColor(s) { return { active: 'green', closed: 'default', draft: 'orange' }[s] || 'default' }
function statusLabel(s) { return { active: '进行中', closed: '已关闭', draft: '草稿' }[s] || s }

async function fetchTasks() {
  loading.value = true
  try {
    const params = {}
    if (filterType.value) params.targetType = filterType.value
    if (filterStatus.value) params.status = filterStatus.value
    taskList.value = await request.get('/evaluations/tasks', { params }) || []
  } catch { taskList.value = [] } finally { loading.value = false }
}

// 发布
const createVisible = ref(false)
const creating = ref(false)
const form = reactive({ title: '', targetType: undefined, targetId: undefined, trainingId: undefined, startTime: null, endTime: null })
const targetOptions = ref([])
const targetOptionsLoading = ref(false)
const trainingSelectOpen = ref(false)
const selectedTrainingName = ref('')
const targetTrainingSelectOpen = ref(false)
const selectedTargetName = ref('')

function openCreateModal() {
  form.title = ''
  form.targetType = undefined
  form.targetId = undefined
  form.trainingId = undefined
  form.startTime = null
  form.endTime = null
  targetOptions.value = []
  selectedTrainingName.value = ''
  selectedTargetName.value = ''
  createVisible.value = true
}

async function onTargetTypeChange(val) {
  form.targetId = undefined
  selectedTargetName.value = ''
  if (!val) { targetOptions.value = []; return }
  if (val === 'training') return  // 培训班用弹窗选择
  targetOptionsLoading.value = true
  try {
    if (val === 'course') {
      const res = await request.get('/courses', { params: { size: -1 } })
      targetOptions.value = (res.items || []).map((c) => ({ value: c.id, label: c.title || c.name || `课程#${c.id}` }))
    } else if (val === 'instructor') {
      const res = await request.get('/users', { params: { role: 'instructor', size: -1 } })
      targetOptions.value = (res.items || []).map((u) => ({ value: u.id, label: u.nickname || u.username }))
    } else if (val === 'training') {
      const res = await request.get('/trainings', { params: { size: -1 } })
      targetOptions.value = (res.items || []).map((t) => ({ value: t.id, label: t.name || `培训班#${t.id}` }))
    } else if (val === 'training_base') {
      const res = await request.get('/training-bases', { params: { size: -1 } })
      targetOptions.value = (res.items || []).map((b) => ({ value: b.id, label: `${b.name}${b.location ? ' / ' + b.location : ''}` }))
    }
  } catch { targetOptions.value = [] } finally { targetOptionsLoading.value = false }
}

function onTrainingSelected(record) {
  form.trainingId = record.id
  selectedTrainingName.value = record.name || `培训班#${record.id}`
}

function clearTraining() {
  form.trainingId = undefined
  selectedTrainingName.value = ''
}

function onTargetTrainingSelected(record) {
  form.targetId = record.id
  selectedTargetName.value = record.name || `培训班#${record.id}`
}

function clearTarget() {
  form.targetId = undefined
  selectedTargetName.value = ''
}

async function handleCreate() {
  if (!form.title?.trim() || !form.targetType || !form.targetId) { message.warning('请填写必填项'); return }
  creating.value = true
  try {
    await request.post('/evaluations/tasks', {
      title: form.title.trim(),
      targetType: form.targetType,
      targetId: form.targetId,
      trainingId: form.trainingId || undefined,
      startTime: form.startTime?.toISOString?.() || undefined,
      endTime: form.endTime?.toISOString?.() || undefined,
    })
    message.success('评价任务已发布')
    createVisible.value = false
    fetchTasks()
  } catch (err) { message.error(err.message || '发布失败') } finally { creating.value = false }
}

async function handleClose(taskId) {
  try {
    await request.put(`/evaluations/tasks/${taskId}`, { status: 'closed' })
    message.success('任务已关闭')
    fetchTasks()
  } catch (err) { message.error(err.message || '操作失败') }
}

async function handleDelete(taskId) {
  try {
    await request.delete(`/evaluations/tasks/${taskId}`)
    message.success('已删除')
    fetchTasks()
  } catch (err) { message.error(err.message || '删除失败') }
}

onMounted(fetchTasks)
</script>

<style scoped>
.tab-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
</style>
