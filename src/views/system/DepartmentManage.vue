<template>
  <div class="department-manage-page">
    <div class="page-header">
      <h2>部门管理</h2>
      <a-button type="primary" @click="openCreate">新增部门</a-button>
    </div>

    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-row :gutter="12">
        <a-col :xs="24" :sm="10" :md="8">
          <a-input-search
            v-model:value="searchForm.keyword"
            placeholder="搜索部门名称/编码"
            allow-clear
            @search="handleSearch"
          />
        </a-col>
        <a-col :xs="12" :sm="7" :md="6">
          <a-select v-model:value="searchForm.status" style="width: 100%" @change="handleSearch">
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="true">启用</a-select-option>
            <a-select-option value="false">停用</a-select-option>
          </a-select>
        </a-col>
        <a-col :xs="12" :sm="7" :md="6">
          <a-select
            v-model:value="searchForm.parentId"
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option value="">全部层级</a-select-option>
            <a-select-option value="root">根部门</a-select-option>
            <a-select-option
              v-for="option in allDepartmentOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :xs="24" :sm="24" :md="4">
          <a-space>
            <a-button type="primary" @click="handleSearch">搜索</a-button>
            <a-button @click="handleReset">重置</a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="treeRows"
        :loading="loading"
        :pagination="false"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'parentName'">
            {{ getParentName(record.parentId) }}
          </template>
          <template v-if="column.key === 'inheritSubPermissions'">
            <a-tag :color="record.inheritSubPermissions ? 'blue' : 'default'">
              {{ record.inheritSubPermissions ? '继承' : '不继承' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'isActive'">
            <a-switch
              :checked="record.isActive"
              :loading="switchingDepartmentId === record.id"
              @change="(checked) => changeStatus(record, checked)"
            />
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="openAddChild(record)">添加子部门</a-button>
              <a-button size="small" @click="openEdit(record)">编辑</a-button>
              <a-button size="small" @click="openPermissionDialog(record)">分配权限</a-button>
              <a-popconfirm
                title="确认删除该部门吗？"
                ok-text="删除"
                cancel-text="取消"
                @confirm="removeDepartment(record)"
              >
                <a-button size="small" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      v-model:open="editDialog.visible"
      :title="editDialog.mode === 'add' ? '新增部门' : '编辑部门'"
      :confirm-loading="editDialog.submitting"
      @ok="submitDepartment"
    >
      <a-form layout="vertical">
        <a-form-item label="部门编码" required>
          <a-input
            v-model:value="editDialog.form.code"
            :disabled="editDialog.mode === 'edit'"
            placeholder="请输入部门编码，例如 TECH"
          />
        </a-form-item>
        <a-form-item label="部门名称" required>
          <a-input v-model:value="editDialog.form.name" placeholder="请输入部门名称" />
        </a-form-item>
        <a-form-item label="父级部门">
          <a-select
            v-model:value="editDialog.form.parentId"
            allow-clear
            placeholder="默认根部门"
          >
            <a-select-option
              v-for="option in dialogParentOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="权限继承">
          <a-switch v-model:checked="editDialog.form.inheritSubPermissions" />
        </a-form-item>
        <a-form-item label="部门描述">
          <a-textarea
            v-model:value="editDialog.form.description"
            :rows="3"
            placeholder="请输入部门描述"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="permissionDialog.visible"
      title="分配权限"
      width="1080px"
      :confirm-loading="permissionDialog.submitting"
      @ok="submitDepartmentPermissions"
    >
      <p class="perm-tip">
        当前部门：
        <strong>{{ permissionDialog.department?.name || '-' }}</strong>
      </p>
      <PermissionTransfer
        v-model:target-keys="permissionDialog.targetKeys"
        :permissions="permissionDialog.permissions"
        :loading="permissionDialog.loading"
        :height="480"
      />
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  createDepartment,
  deleteDepartment,
  getDepartmentDetail,
  getDepartmentList,
  toggleDepartmentStatus,
  updateDepartment,
  updateDepartmentPermissions,
} from '@/api/department'
import { getPermissionList } from '@/api/permission'
import PermissionTransfer from './components/PermissionTransfer.vue'

const loading = ref(false)
const rows = ref([])
const switchingDepartmentId = ref(null)

const searchForm = reactive({
  keyword: '',
  status: '',
  parentId: '',
})

const columns = [
  { title: '部门名称', dataIndex: 'name', key: 'name', width: 220 },
  { title: '部门编码', dataIndex: 'code', key: 'code', width: 160 },
  { title: '父级部门', key: 'parentName', width: 180 },
  { title: '权限继承', dataIndex: 'inheritSubPermissions', key: 'inheritSubPermissions', width: 110 },
  { title: '状态', dataIndex: 'isActive', key: 'isActive', width: 100 },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '操作', key: 'action', width: 360, fixed: 'right' },
]

const editDialog = reactive({
  visible: false,
  mode: 'add',
  submitting: false,
  currentId: null,
  form: {
    code: '',
    name: '',
    parentId: null,
    inheritSubPermissions: false,
    description: '',
  },
})

const permissionDialog = reactive({
  visible: false,
  loading: false,
  submitting: false,
  department: null,
  permissions: [],
  targetKeys: [],
})

const allDepartmentOptions = computed(() =>
  rows.value.map((item) => ({
    value: item.id,
    label: item.name,
  }))
)

const dialogParentOptions = computed(() => {
  if (editDialog.mode !== 'edit' || !editDialog.currentId) {
    return allDepartmentOptions.value
  }
  const blocked = new Set([editDialog.currentId, ...getDescendantIds(editDialog.currentId)])
  return allDepartmentOptions.value.filter((item) => !blocked.has(item.value))
})

const treeRows = computed(() => buildTree(filteredRows.value))

const filteredRows = computed(() => {
  const keyword = searchForm.keyword.trim().toLowerCase()
  const status = searchForm.status
  const parentId = searchForm.parentId

  return rows.value.filter((item) => {
    if (keyword) {
      const hit = String(item.name || '').toLowerCase().includes(keyword)
        || String(item.code || '').toLowerCase().includes(keyword)
        || String(item.description || '').toLowerCase().includes(keyword)
      if (!hit) return false
    }
    if (status !== '') {
      const shouldActive = status === 'true'
      if (item.isActive !== shouldActive) return false
    }
    if (parentId !== '') {
      if (parentId === 'root') {
        if (item.parentId !== null && item.parentId !== undefined) return false
      } else if (Number(item.parentId) !== Number(parentId)) {
        return false
      }
    }
    return true
  })
})

onMounted(() => {
  fetchDepartmentList()
})

function buildTree(items) {
  const map = new Map()
  const roots = []

  items.forEach((item) => {
    map.set(item.id, { ...item, children: [] })
  })

  map.forEach((node) => {
    if (node.parentId && map.has(node.parentId)) {
      map.get(node.parentId).children.push(node)
    } else {
      roots.push(node)
    }
  })

  return roots
}

function getDescendantIds(departmentId) {
  const childMap = new Map()
  rows.value.forEach((item) => {
    if (!childMap.has(item.parentId)) {
      childMap.set(item.parentId, [])
    }
    childMap.get(item.parentId).push(item.id)
  })

  const result = []
  const queue = [...(childMap.get(departmentId) || [])]
  while (queue.length) {
    const id = queue.shift()
    result.push(id)
    const children = childMap.get(id) || []
    queue.push(...children)
  }
  return result
}

function getParentName(parentId) {
  if (parentId === null || parentId === undefined) return '根部门'
  const target = rows.value.find((item) => item.id === parentId)
  return target?.name || '-'
}

async function fetchDepartmentList() {
  loading.value = true
  try {
    const res = await getDepartmentList({ size: -1 })
    rows.value = res?.items || []
  } catch (error) {
    message.error(error?.message || '获取部门列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  // 使用本地过滤，保持树形结构不重新请求
}

function handleReset() {
  searchForm.keyword = ''
  searchForm.status = ''
  searchForm.parentId = ''
}

function resetEditForm() {
  editDialog.form.code = ''
  editDialog.form.name = ''
  editDialog.form.parentId = null
  editDialog.form.inheritSubPermissions = false
  editDialog.form.description = ''
}

function openCreate() {
  editDialog.mode = 'add'
  editDialog.currentId = null
  resetEditForm()
  editDialog.visible = true
}

function openAddChild(record) {
  editDialog.mode = 'add'
  editDialog.currentId = null
  resetEditForm()
  editDialog.form.parentId = record.id
  editDialog.visible = true
}

function openEdit(record) {
  editDialog.mode = 'edit'
  editDialog.currentId = record.id
  editDialog.form.code = record.code || ''
  editDialog.form.name = record.name || ''
  editDialog.form.parentId = record.parentId ?? null
  editDialog.form.inheritSubPermissions = !!record.inheritSubPermissions
  editDialog.form.description = record.description || ''
  editDialog.visible = true
}

async function submitDepartment() {
  if (!editDialog.form.name?.trim()) {
    message.warning('请输入部门名称')
    return
  }
  if (editDialog.mode === 'add' && !editDialog.form.code?.trim()) {
    message.warning('请输入部门编码')
    return
  }

  const normalizedParentId = editDialog.form.parentId ?? null
  editDialog.submitting = true
  try {
    if (editDialog.mode === 'add') {
      await createDepartment({
        code: editDialog.form.code.trim(),
        name: editDialog.form.name.trim(),
        parentId: normalizedParentId,
        inheritSubPermissions: editDialog.form.inheritSubPermissions,
        description: editDialog.form.description?.trim() || undefined,
      })
      message.success('新增部门成功')
    } else {
      await updateDepartment(editDialog.currentId, {
        name: editDialog.form.name.trim(),
        parentId: normalizedParentId,
        inheritSubPermissions: editDialog.form.inheritSubPermissions,
        description: editDialog.form.description?.trim() || undefined,
      })
      message.success('更新部门成功')
    }
    editDialog.visible = false
    fetchDepartmentList()
  } catch (error) {
    message.error(error?.message || '保存部门失败')
  } finally {
    editDialog.submitting = false
  }
}

async function changeStatus(record, checked) {
  const oldStatus = record.isActive
  record.isActive = checked
  switchingDepartmentId.value = record.id
  try {
    await toggleDepartmentStatus(record.id, checked)
    message.success(`部门${checked ? '启用' : '停用'}成功`)
  } catch (error) {
    record.isActive = oldStatus
    message.error(error?.message || '更新部门状态失败')
  } finally {
    switchingDepartmentId.value = null
  }
}

async function removeDepartment(record) {
  try {
    await deleteDepartment(record.id)
    message.success('删除部门成功')
    fetchDepartmentList()
  } catch (error) {
    message.error(error?.message || '删除部门失败')
  }
}

async function openPermissionDialog(record) {
  permissionDialog.visible = true
  permissionDialog.department = record
  permissionDialog.loading = true
  permissionDialog.targetKeys = []

  try {
    const [permissionRes, departmentRes] = await Promise.all([
      getPermissionList({ size: -1 }),
      getDepartmentDetail(record.id),
    ])
    permissionDialog.permissions = permissionRes?.items || []
    permissionDialog.targetKeys = (departmentRes?.permissions || []).map((item) => String(item.id))
  } catch (error) {
    message.error(error?.message || '加载部门权限数据失败')
    permissionDialog.visible = false
  } finally {
    permissionDialog.loading = false
  }
}

async function submitDepartmentPermissions() {
  if (!permissionDialog.department) return
  const permissionIds = permissionDialog.targetKeys
    .map((key) => Number(key))
    .filter((id) => Number.isFinite(id))

  permissionDialog.submitting = true
  try {
    await updateDepartmentPermissions(permissionDialog.department.id, permissionIds)
    message.success('更新部门权限成功')
    permissionDialog.visible = false
    fetchDepartmentList()
  } catch (error) {
    message.error(error?.message || '更新部门权限失败')
  } finally {
    permissionDialog.submitting = false
  }
}
</script>

<style scoped>
.department-manage-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--police-primary);
}

.perm-tip {
  margin-bottom: 12px;
}
</style>
