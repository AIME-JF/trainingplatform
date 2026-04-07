<template>
  <div class="training-base-page">
    <div class="page-header">
      <div>
        <h2>培训基地</h2>
        <p class="page-sub">维护培训班可选基地，并支持按部门归档</p>
      </div>
      <permissions-tooltip
        :allowed="canManageTrainingBase"
        tips="仅管理员或教官可新增培训基地"
        v-slot="{ disabled }"
      >
        <a-button type="primary" :disabled="disabled" @click="openCreateModal">
          <template #icon><PlusOutlined /></template>新增培训基地
        </a-button>
      </permissions-tooltip>
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
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'active' ? 'green' : 'default'">
              {{ record.status === 'active' ? '启用' : '停用' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'departmentName'">
            {{ record.departmentName || '未设置' }}
          </template>
          <template v-if="column.key === 'linkedTrainingStatus'">
            <a-space size="small">
              <a-tag color="orange">待开班 {{ record.upcomingTrainingCount || 0 }}</a-tag>
              <a-tag color="green">已开班 {{ record.activeTrainingCount || 0 }}</a-tag>
            </a-space>
          </template>
          <template v-if="column.key === 'action'">
            <a-space size="small">
              <permissions-tooltip
                :allowed="canManageTrainingBase"
                tips="仅管理员或教官可编辑培训基地"
                v-slot="{ disabled }"
              >
                <a-button type="link" size="small" :disabled="disabled" @click="openEditModal(record)">编辑</a-button>
              </permissions-tooltip>
              <permissions-tooltip
                :allowed="canDeleteTrainingBase"
                tips="仅管理员可删除培训基地"
                v-slot="{ disabled }"
              >
                <a-button type="link" size="small" danger :disabled="disabled" @click="handleDelete(record)">删除</a-button>
              </permissions-tooltip>
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
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="基地名称" required>
              <a-input v-model:value="baseForm.name" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="基地地点" required>
              <a-input v-model:value="baseForm.location" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="最大容纳人数">
              <a-input-number v-model:value="baseForm.capacity" :min="0" style="width: 100%" placeholder="可选" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="占地面积">
              <a-input v-model:value="baseForm.areaSize" placeholder="如：5000平方米" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="联系人">
              <a-input v-model:value="baseForm.contactPerson" placeholder="可选" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="联系电话">
              <a-input v-model:value="baseForm.contactPhone" placeholder="可选" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="部门">
              <a-select v-model:value="baseForm.departmentId" allow-clear placeholder="可选">
                <a-select-option v-for="item in departmentOptions" :key="item.id" :value="item.id">
                  {{ item.name }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="状态">
              <a-select v-model:value="baseForm.status">
                <a-select-option value="active">启用</a-select-option>
                <a-select-option value="inactive">停用</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="设施设备">
          <a-textarea v-model:value="baseForm.facilities" :rows="2" placeholder="如：射击场、体能训练馆、多媒体教室" />
        </a-form-item>
        <a-form-item label="备注">
          <a-textarea v-model:value="baseForm.description" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
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
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

const authStore = useAuthStore()
const canManageTrainingBase = computed(() => authStore.isAdmin || authStore.isInstructor)
const canDeleteTrainingBase = computed(() => authStore.isAdmin)
const searchText = ref('')
const departmentFilter = ref(undefined)
const trainingBaseList = ref([])
const departmentOptions = ref([])
const showModal = ref(false)
const editingBase = ref(null)

const columns = [
  { title: '基地名称', dataIndex: 'name', key: 'name' },
  { title: '基地地点', dataIndex: 'location', key: 'location' },
  { title: '容量', dataIndex: 'capacity', key: 'capacity', width: 80 },
  { title: '联系人', dataIndex: 'contactPerson', key: 'contactPerson', width: 100 },
  { title: '联系电话', dataIndex: 'contactPhone', key: 'contactPhone', width: 120 },
  { title: '状态', key: 'status', width: 80 },
  { title: '部门', dataIndex: 'departmentName', key: 'departmentName', width: 140 },
  { title: '关联培训班', key: 'linkedTrainingStatus', width: 200 },
  { title: '操作', key: 'action', width: 140 },
]

const baseForm = reactive({
  name: '',
  location: '',
  departmentId: undefined,
  capacity: undefined,
  contactPerson: '',
  contactPhone: '',
  areaSize: '',
  facilities: '',
  status: 'active',
  description: '',
})

function resetForm() {
  Object.assign(baseForm, {
    name: '',
    location: '',
    departmentId: undefined,
    capacity: undefined,
    contactPerson: '',
    contactPhone: '',
    areaSize: '',
    facilities: '',
    status: 'active',
    description: '',
  })
  editingBase.value = null
  showModal.value = false
}

function openCreateModal() {
  if (!canManageTrainingBase.value) return
  resetForm()
  showModal.value = true
}

function openEditModal(record) {
  if (!canManageTrainingBase.value) return
  editingBase.value = record
  Object.assign(baseForm, {
    name: record.name || '',
    location: record.location || '',
    departmentId: record.departmentId,
    capacity: record.capacity,
    contactPerson: record.contactPerson || '',
    contactPhone: record.contactPhone || '',
    areaSize: record.areaSize || '',
    facilities: record.facilities || '',
    status: record.status || 'active',
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
  if (!canManageTrainingBase.value) return
  if (!baseForm.name || !baseForm.location) {
    message.warning('请填写基地名称和地点')
    return
  }

  const payload = {
    name: baseForm.name,
    location: baseForm.location,
    departmentId: baseForm.departmentId || undefined,
    capacity: baseForm.capacity || undefined,
    contactPerson: baseForm.contactPerson || undefined,
    contactPhone: baseForm.contactPhone || undefined,
    areaSize: baseForm.areaSize || undefined,
    facilities: baseForm.facilities || undefined,
    status: baseForm.status || 'active',
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
  if (!canDeleteTrainingBase.value) return
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
