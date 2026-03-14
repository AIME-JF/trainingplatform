<template>
  <div class="training-base-page">
    <div class="page-header">
      <div>
        <h2>培训基地</h2>
        <p class="page-sub">维护培训班可选基地，并支持按部门归档</p>
      </div>
      <a-button type="primary" @click="openCreateModal">
        <template #icon><PlusOutlined /></template>新增培训基地
      </a-button>
    </div>

    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-space wrap>
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索基地名称或地点"
          allow-clear
          style="width: 260px"
          @search="fetchTrainingBases"
        />
        <a-select v-model:value="departmentFilter" allow-clear placeholder="筛选部门" style="width: 220px">
          <a-select-option v-for="item in departmentOptions" :key="item.id" :value="item.id">
            {{ item.name }}
          </a-select-option>
        </a-select>
        <a-button @click="fetchTrainingBases">查询</a-button>
      </a-space>
    </a-card>

    <a-card :bordered="false">
      <a-table :data-source="trainingBaseList" :columns="columns" :pagination="false" row-key="id">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'departmentName'">
            {{ record.departmentName || '未设置' }}
          </template>
          <template v-if="column.key === 'linkedTrainingCount'">
            <a-tag color="blue">{{ record.linkedTrainingCount || 0 }}</a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space size="small">
              <a-button type="link" size="small" @click="openEditModal(record)">编辑</a-button>
              <a-button v-if="authStore.isAdmin" type="link" size="small" danger @click="handleDelete(record)">删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="showModal"
      :title="editingBase ? '编辑培训基地' : '新增培训基地'"
      width="640px"
      @ok="handleSubmit"
      @cancel="resetForm"
      ok-text="保存"
      cancel-text="取消"
    >
      <a-form :model="baseForm" layout="vertical" style="margin-top: 12px">
        <a-form-item label="基地名称" required>
          <a-input v-model:value="baseForm.name" />
        </a-form-item>
        <a-form-item label="基地地点" required>
          <a-input v-model:value="baseForm.location" />
        </a-form-item>
        <a-form-item label="部门">
          <a-select v-model:value="baseForm.departmentId" allow-clear placeholder="可选">
            <a-select-option v-for="item in departmentOptions" :key="item.id" :value="item.id">
              {{ item.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="baseForm.description" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import {
  createTrainingBase,
  deleteTrainingBase,
  getTrainingBases,
  updateTrainingBase,
} from '@/api/training'
import { getDepartmentList } from '@/api/department'

const authStore = useAuthStore()
const searchText = ref('')
const departmentFilter = ref(undefined)
const trainingBaseList = ref([])
const departmentOptions = ref([])
const showModal = ref(false)
const editingBase = ref(null)

const columns = [
  { title: '基地名称', dataIndex: 'name', key: 'name' },
  { title: '基地地点', dataIndex: 'location', key: 'location' },
  { title: '部门', dataIndex: 'departmentName', key: 'departmentName', width: 180 },
  { title: '关联培训班', dataIndex: 'linkedTrainingCount', key: 'linkedTrainingCount', width: 120 },
  { title: '操作', key: 'action', width: 140 },
]

const baseForm = reactive({
  name: '',
  location: '',
  departmentId: undefined,
  description: '',
})

function resetForm() {
  Object.assign(baseForm, {
    name: '',
    location: '',
    departmentId: undefined,
    description: '',
  })
  editingBase.value = null
  showModal.value = false
}

function openCreateModal() {
  resetForm()
  showModal.value = true
}

function openEditModal(record) {
  editingBase.value = record
  Object.assign(baseForm, {
    name: record.name || '',
    location: record.location || '',
    departmentId: record.departmentId,
    description: record.description || '',
  })
  showModal.value = true
}

async function fetchDepartments() {
  try {
    const result = await getDepartmentList({ size: -1 })
    departmentOptions.value = result.items || []
  } catch {
    departmentOptions.value = []
  }
}

async function fetchTrainingBases() {
  try {
    const result = await getTrainingBases({
      size: -1,
      search: searchText.value || undefined,
      departmentId: departmentFilter.value || undefined,
    })
    trainingBaseList.value = result.items || []
  } catch (error) {
    message.error(error.message || '加载培训基地失败')
  }
}

async function handleSubmit() {
  if (!baseForm.name || !baseForm.location) {
    message.warning('请填写基地名称和地点')
    return
  }

  const payload = {
    name: baseForm.name,
    location: baseForm.location,
    departmentId: baseForm.departmentId || undefined,
    description: baseForm.description || undefined,
  }

  try {
    if (editingBase.value) {
      await updateTrainingBase(editingBase.value.id, payload)
      message.success('培训基地已更新')
    } else {
      await createTrainingBase(payload)
      message.success('培训基地已创建')
    }
    resetForm()
    fetchTrainingBases()
  } catch (error) {
    message.error(error.message || '保存失败')
  }
}

function handleDelete(record) {
  Modal.confirm({
    title: '确认删除培训基地？',
    content: record.name,
    okType: 'danger',
    onOk: async () => {
      try {
        await deleteTrainingBase(record.id)
        message.success('已删除')
        fetchTrainingBases()
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

onMounted(() => {
  fetchDepartments()
  fetchTrainingBases()
})
</script>

<style scoped>
.training-base-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 16px; }
.page-header h2 { margin: 0; font-size: 22px; color: #001234; }
.page-sub { margin: 6px 0 0; color: #8c8c8c; font-size: 13px; }

@media (max-width: 768px) {
  .page-header { flex-direction: column; }
}
</style>
