<template>
  <div class="dashboard-module-page">
    <div class="page-header">
      <div>
        <h2>看板配置</h2>
        <p class="page-sub">配置各看板模块对不同角色的可见性</p>
      </div>
    </div>

    <a-card :bordered="false">
      <a-table
        :data-source="modules"
        :columns="columns"
        :loading="loading"
        row-key="id"
        :pagination="false"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'category'">
            <a-tag :color="record.category === 'training' ? 'green' : record.category === 'exam' ? 'orange' : 'blue'">
              {{ record.category === 'training' ? '培训运营' : record.category === 'exam' ? '考试统计' : '综合数据' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'visibleRoleCodes'">
            <a-tag v-for="code in (record.visibleRoleCodes || [])" :key="code" style="margin-bottom: 2px">
              {{ roleLabels[code] || code }}
            </a-tag>
            <span v-if="!(record.visibleRoleCodes || []).length" style="color: #8c8c8c">全部角色</span>
          </template>
          <template v-else-if="column.key === 'isActive'">
            <a-switch
              :checked="record.isActive"
              checked-children="启用"
              un-checked-children="停用"
              @change="(val) => handleToggle(record, val)"
            />
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button type="link" size="small" @click="openEditModal(record)">编辑</a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="modalVisible"
      title="编辑看板模块"
      :confirm-loading="saving"
      ok-text="保存"
      @ok="handleSave"
    >
      <a-form layout="vertical" style="margin-top: 12px">
        <a-form-item label="模块名称">
          <a-input :value="editingRecord?.moduleName" disabled />
        </a-form-item>
        <a-form-item label="可见角色">
          <a-select
            v-model:value="form.visibleRoleCodes"
            mode="multiple"
            show-search
            :options="roleOptions"
            :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
            placeholder="不选择则对全部角色可见"
            style="width: 100%"
            allow-clear
          />
        </a-form-item>
        <a-form-item label="排序号">
          <a-input-number v-model:value="form.sortOrder" :min="0" style="width: 100%" placeholder="数值越小越靠前" />
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="form.isActive" checked-children="启用" un-checked-children="停用" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { getDashboardModules, updateDashboardModule } from '@/api/system'
import { getRoleList } from '@/api/role'

const loading = ref(false)
const saving = ref(false)
const modules = ref([])
const modalVisible = ref(false)
const editingRecord = ref(null)
const form = reactive({
  visibleRoleCodes: [],
  sortOrder: 0,
  isActive: true,
})

const roleLabels = ref({})
const roleOptions = ref([])

async function fetchRoles() {
  try {
    const result = await getRoleList({ size: -1 })
    const items = result.items || result || []
    const labels = {}
    roleOptions.value = items.filter(r => r.isActive !== false).map(r => {
      labels[r.code] = r.name
      return { label: r.name, value: r.code }
    })
    roleLabels.value = labels
  } catch {
    roleOptions.value = []
    roleLabels.value = {}
  }
}

const columns = [
  { title: '模块名称', dataIndex: 'moduleName', key: 'moduleName' },
  { title: '说明', dataIndex: 'moduleDescription', key: 'moduleDescription', ellipsis: true },
  { title: '分类', key: 'category', width: 100 },
  { title: '可见角色', key: 'visibleRoleCodes', width: 240 },
  { title: '排序', dataIndex: 'sortOrder', key: 'sortOrder', width: 70 },
  { title: '状态', key: 'isActive', width: 90 },
  { title: '操作', key: 'action', width: 80 },
]

async function fetchModules() {
  loading.value = true
  try {
    modules.value = await getDashboardModules()
  } catch (e) {
    message.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function openEditModal(record) {
  editingRecord.value = record
  form.visibleRoleCodes = [...(record.visibleRoleCodes || [])]
  form.sortOrder = record.sortOrder ?? 0
  form.isActive = record.isActive !== false
  modalVisible.value = true
}

async function handleSave() {
  if (!editingRecord.value) return
  saving.value = true
  try {
    await updateDashboardModule(editingRecord.value.id, {
      visibleRoleCodes: form.visibleRoleCodes,
      sortOrder: form.sortOrder || 0,
      isActive: form.isActive,
    })
    message.success('保存成功')
    modalVisible.value = false
    fetchModules()
  } catch (e) {
    message.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function handleToggle(record, value) {
  try {
    await updateDashboardModule(record.id, { isActive: value })
    record.isActive = value
    message.success(value ? '已启用' : '已停用')
  } catch (e) {
    message.error(e.message || '操作失败')
  }
}

onMounted(() => {
  fetchRoles()
  fetchModules()
})
</script>

<style scoped>
.dashboard-module-page { padding: 0; }
.page-header { margin-bottom: 16px; }
.page-header h2 { margin: 0; color: #001234; }
.page-sub { margin: 4px 0 0; color: #8c8c8c; font-size: 13px; }
</style>
