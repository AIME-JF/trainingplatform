<template>
  <div>
    <div class="tab-toolbar">
      <a-space>
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
        <template v-if="column.key === 'status'">
          <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
        </template>
        <template v-if="column.key === 'source'">
          {{ record.source === 'auto' ? '自动' : '手动' }}
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
        <a-form-item label="选择培训班" required>
          <a-input
            :value="selectedTrainingName"
            read-only
            placeholder="点击选择培训班"
            @click="trainingSelectOpen = true"
          >
            <template #suffix>
              <CloseCircleOutlined v-if="form.trainingId" style="cursor: pointer; color: #999" @click.stop="clearTraining" />
            </template>
          </a-input>
        </a-form-item>
        <a-alert type="info" show-icon style="margin-bottom: 16px">
          <template #message>说明</template>
          <template #description>
            系统将自动为该培训班的所有课程、教官、培训班本身以及关联的培训基地生成评价项，学员收到一份综合问卷即可完成所有评价。
          </template>
        </a-alert>
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
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { CloseCircleOutlined } from '@ant-design/icons-vue'
import request from '@/api/request'
import TrainingSelectModal from '@/components/common/TrainingSelectModal.vue'

const loading = ref(false)
const taskList = ref([])
const filterStatus = ref(undefined)

const columns = [
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '培训班', dataIndex: 'trainingName', key: 'trainingName', width: 160, ellipsis: true },
  { title: '来源', key: 'source', width: 70 },
  { title: '状态', key: 'status', width: 90 },
  { title: '评价项', dataIndex: 'itemCount', key: 'itemCount', width: 80 },
  { title: '填写数', dataIndex: 'recordCount', key: 'recordCount', width: 80 },
  { title: '操作', key: 'action', width: 120 },
]

function statusColor(s) { return { active: 'green', closed: 'default', draft: 'orange' }[s] || 'default' }
function statusLabel(s) { return { active: '进行中', closed: '已关闭', draft: '草稿' }[s] || s }

async function fetchTasks() {
  loading.value = true
  try {
    const params = {}
    if (filterStatus.value) params.status = filterStatus.value
    taskList.value = await request.get('/evaluations/tasks', { params }) || []
  } catch { taskList.value = [] } finally { loading.value = false }
}

const createVisible = ref(false)
const creating = ref(false)
const form = reactive({ title: '', trainingId: undefined, startTime: null, endTime: null })
const trainingSelectOpen = ref(false)
const selectedTrainingName = ref('')

function openCreateModal() {
  form.title = ''
  form.trainingId = undefined
  form.startTime = null
  form.endTime = null
  selectedTrainingName.value = ''
  createVisible.value = true
}

function onTrainingSelected(record) {
  form.trainingId = record.id
  selectedTrainingName.value = record.name || `培训班#${record.id}`
  if (!form.title) form.title = `${selectedTrainingName.value} - 评价`
}

function clearTraining() {
  form.trainingId = undefined
  selectedTrainingName.value = ''
}

async function handleCreate() {
  if (!form.title?.trim() || !form.trainingId) { message.warning('请填写标题并选择培训班'); return }
  creating.value = true
  try {
    await request.post('/evaluations/tasks', {
      title: form.title.trim(),
      trainingId: form.trainingId,
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
