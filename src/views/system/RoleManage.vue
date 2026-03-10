<template>
  <div class="role-manage-page">
    <div class="page-header">
      <h2>角色管理</h2>
      <a-button type="primary" @click="openCreate">新增角色</a-button>
    </div>

    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-row :gutter="12">
        <a-col :xs="24" :sm="10" :md="8">
          <a-input-search
            v-model:value="searchForm.keyword"
            placeholder="搜索角色名称"
            allow-clear
            @search="handleSearch"
          />
        </a-col>
        <a-col :xs="12" :sm="7" :md="6">
          <a-select
            v-model:value="searchForm.status"
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="true">启用</a-select-option>
            <a-select-option value="false">停用</a-select-option>
          </a-select>
        </a-col>
        <a-col :xs="12" :sm="7" :md="10">
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
        :data-source="rows"
        :loading="loading"
        :pagination="false"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'isActive'">
            <a-switch
              :checked="record.isActive"
              :disabled="isAdminRole(record)"
              :loading="switchingRoleId === record.id"
              @change="(checked) => changeStatus(record, checked)"
            />
          </template>
          <template v-if="column.key === 'createdAt'">
            {{ formatDate(record.createdAt) }}
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" :disabled="isAdminRole(record)" @click="openEdit(record)">编辑</a-button>
              <a-button size="small" :disabled="isAdminRole(record)" @click="openPermissionDialog(record)">分配权限</a-button>
              <a-popconfirm
                :disabled="isAdminRole(record)"
                title="确认删除该角色吗？"
                ok-text="删除"
                cancel-text="取消"
                @confirm="removeRole(record)"
              >
                <a-button size="small" danger :disabled="isAdminRole(record)">删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>

      <div class="pager-wrap">
        <a-pagination
          :current="pagination.page"
          :page-size="pagination.size"
          :total="pagination.total"
          show-size-changer
          :page-size-options="['10', '20', '50']"
          @change="onPageChange"
          @showSizeChange="onSizeChange"
        />
      </div>
    </a-card>

    <a-modal
      v-model:open="editDialog.visible"
      :title="editDialog.mode === 'add' ? '新增角色' : '编辑角色'"
      :confirm-loading="editDialog.submitting"
      @ok="submitRole"
    >
      <a-form layout="vertical">
        <a-form-item label="角色编码" required>
          <a-input
            v-model:value="editDialog.form.code"
            :disabled="editDialog.mode === 'edit'"
            placeholder="请输入角色编码，例如 instructor"
          />
        </a-form-item>
        <a-form-item label="角色名称" required>
          <a-input v-model:value="editDialog.form.name" placeholder="请输入角色名称" />
        </a-form-item>
        <a-form-item label="角色描述">
          <a-textarea
            v-model:value="editDialog.form.description"
            :rows="3"
            placeholder="请输入角色描述"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="permissionDialog.visible"
      title="分配权限"
      width="1080px"
      :confirm-loading="permissionDialog.submitting"
      @ok="submitRolePermissions"
    >
      <p class="perm-tip">
        当前角色：
        <strong>{{ permissionDialog.role?.name || '-' }}</strong>
      </p>
      <PermissionTransfer
        v-model:target-keys="permissionDialog.targetKeys"
        :permissions="permissionDialog.permissions"
        :loading="permissionDialog.loading"
        :disabled="isAdminRole(permissionDialog.role)"
        :height="480"
      />
    </a-modal>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  createRole,
  deleteRole,
  getRoleDetail,
  getRoleList,
  toggleRoleStatus,
  updateRole,
  updateRolePermissions,
} from '@/api/role'
import { getPermissionList } from '@/api/permission'
import PermissionTransfer from './components/PermissionTransfer.vue'

const loading = ref(false)
const rows = ref([])
const switchingRoleId = ref(null)

const searchForm = reactive({
  keyword: '',
  status: '',
})

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0,
})

const ADMIN_ROLE_CODE = 'admin'

const columns = [
  { title: '角色编码', dataIndex: 'code', key: 'code', width: 150 },
  { title: '角色名称', dataIndex: 'name', key: 'name', width: 180 },
  { title: '角色描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '状态', dataIndex: 'isActive', key: 'isActive', width: 100 },
  { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt', width: 180 },
  { title: '操作', key: 'action', width: 280, fixed: 'right' },
]

const editDialog = reactive({
  visible: false,
  mode: 'add',
  submitting: false,
  currentId: null,
  form: {
    code: '',
    name: '',
    description: '',
  },
})

const permissionDialog = reactive({
  visible: false,
  loading: false,
  submitting: false,
  role: null,
  permissions: [],
  targetKeys: [],
})

onMounted(() => {
  fetchRoleList()
})

function formatDate(value) {
  if (!value) return '-'
  return dayjs(value).format('YYYY-MM-DD HH:mm')
}

function isAdminRole(role) {
  return role?.code === ADMIN_ROLE_CODE
}

function getListParams() {
  return {
    page: pagination.page,
    size: pagination.size,
    name: searchForm.keyword || undefined,
    isActive: searchForm.status === '' ? undefined : searchForm.status === 'true',
  }
}

async function fetchRoleList() {
  loading.value = true
  try {
    const res = await getRoleList(getListParams())
    rows.value = res?.items || []
    pagination.total = res?.total || 0
  } catch (error) {
    message.error(error?.message || '获取角色列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchRoleList()
}

function handleReset() {
  searchForm.keyword = ''
  searchForm.status = ''
  pagination.page = 1
  pagination.size = 10
  fetchRoleList()
}

function onPageChange(page, size) {
  pagination.page = page
  pagination.size = size
  fetchRoleList()
}

function onSizeChange(_, size) {
  pagination.page = 1
  pagination.size = size
  fetchRoleList()
}

function resetEditForm() {
  editDialog.form.code = ''
  editDialog.form.name = ''
  editDialog.form.description = ''
}

function openCreate() {
  editDialog.mode = 'add'
  editDialog.currentId = null
  resetEditForm()
  editDialog.visible = true
}

function openEdit(record) {
  if (isAdminRole(record)) {
    message.warning('管理员角色不可修改')
    return
  }

  editDialog.mode = 'edit'
  editDialog.currentId = record.id
  editDialog.form.code = record.code || ''
  editDialog.form.name = record.name || ''
  editDialog.form.description = record.description || ''
  editDialog.visible = true
}

async function submitRole() {
  if (!editDialog.form.name?.trim()) {
    message.warning('请输入角色名称')
    return
  }
  if (editDialog.mode === 'add' && !editDialog.form.code?.trim()) {
    message.warning('请输入角色编码')
    return
  }

  editDialog.submitting = true
  try {
    if (editDialog.mode === 'add') {
      await createRole({
        code: editDialog.form.code.trim(),
        name: editDialog.form.name.trim(),
        description: editDialog.form.description?.trim() || undefined,
      })
      message.success('新增角色成功')
    } else {
      await updateRole(editDialog.currentId, {
        name: editDialog.form.name.trim(),
        description: editDialog.form.description?.trim() || undefined,
      })
      message.success('更新角色成功')
    }
    editDialog.visible = false
    fetchRoleList()
  } catch (error) {
    message.error(error?.message || '保存角色失败')
  } finally {
    editDialog.submitting = false
  }
}

async function changeStatus(record, checked) {
  if (isAdminRole(record)) {
    message.warning('管理员角色不可修改')
    return
  }

  const oldStatus = record.isActive
  record.isActive = checked
  switchingRoleId.value = record.id
  try {
    await toggleRoleStatus(record.id, checked)
    message.success(`角色${checked ? '启用' : '停用'}成功`)
  } catch (error) {
    record.isActive = oldStatus
    message.error(error?.message || '更新角色状态失败')
  } finally {
    switchingRoleId.value = null
  }
}

async function removeRole(record) {
  if (isAdminRole(record)) {
    message.warning('管理员角色不可修改')
    return
  }

  try {
    await deleteRole(record.id)
    message.success('删除角色成功')
    fetchRoleList()
  } catch (error) {
    message.error(error?.message || '删除角色失败')
  }
}

async function openPermissionDialog(record) {
  if (isAdminRole(record)) {
    message.warning('管理员角色不可修改')
    return
  }

  permissionDialog.visible = true
  permissionDialog.role = record
  permissionDialog.loading = true
  permissionDialog.targetKeys = []

  try {
    const [permissionRes, roleRes] = await Promise.all([
      getPermissionList({ size: -1 }),
      getRoleDetail(record.id),
    ])
    permissionDialog.permissions = permissionRes?.items || []
    permissionDialog.targetKeys = (roleRes?.permissions || []).map((item) => String(item.id))
  } catch (error) {
    message.error(error?.message || '加载角色权限数据失败')
    permissionDialog.visible = false
  } finally {
    permissionDialog.loading = false
  }
}

async function submitRolePermissions() {
  if (!permissionDialog.role) return
  const permissionIds = permissionDialog.targetKeys
    .map((key) => Number(key))
    .filter((id) => Number.isFinite(id))

  permissionDialog.submitting = true
  try {
    await updateRolePermissions(permissionDialog.role.id, permissionIds)
    message.success('更新角色权限成功')
    permissionDialog.visible = false
    fetchRoleList()
  } catch (error) {
    message.error(error?.message || '更新角色权限失败')
  } finally {
    permissionDialog.submitting = false
  }
}
</script>

<style scoped>
.role-manage-page {
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

.pager-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.perm-tip {
  margin-bottom: 12px;
}
</style>
