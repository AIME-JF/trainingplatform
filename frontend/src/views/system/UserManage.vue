<template>
  <div class="user-manage-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <a-space>
        <a-button @click="openImportModal">用户导入</a-button>
        <a-button :loading="exportingUsers" @click="handleExportUsers">用户导出</a-button>
        <a-button type="primary" @click="openCreateModal">
          <PlusOutlined />
          新增用户
        </a-button>
      </a-space>
    </div>

    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-row :gutter="16">
        <a-col :span="10">
          <a-input-search
            v-model:value="filters.search"
            placeholder="搜索姓名/用户名/警号"
            allow-clear
            @search="handleSearch"
          />
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="filters.role"
            placeholder="按角色筛选"
            allow-clear
            style="width: 100%"
            @change="handleSearch"
          >
            <a-select-option v-for="role in roleList" :key="role.code" :value="role.code">
              {{ role.name }}
            </a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="userList"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'roles'">
            <a-tag
              v-for="role in record.roles || []"
              :key="role.id"
              :color="getRoleColor(role.code)"
            >
              {{ role.name }}
            </a-tag>
            <span v-if="!record.roles || record.roles.length === 0" style="color: #999;">未分配</span>
          </template>

          <template v-if="column.key === 'departments'">
            <a-tag
              v-for="department in record.departments || []"
              :key="department.id"
              color="cyan"
            >
              {{ department.name }}
            </a-tag>
            <span v-if="!record.departments || record.departments.length === 0" style="color: #999;">-</span>
          </template>

          <template v-if="column.key === 'isActive'">
            <a-tag :color="record.isActive ? 'green' : 'red'">
              {{ record.isActive ? '正常' : '禁用' }}
            </a-tag>
          </template>

          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="openEditModal(record)">编辑</a-button>
              <a-button type="link" size="small" @click="openResetPasswordModal(record)">重置密码</a-button>
              <a-popconfirm
                :title="`确认删除用户「${record.nickname || record.username}」吗？`"
                ok-text="删除"
                cancel-text="取消"
                @confirm="handleDelete(record)"
              >
                <a-button type="link" size="small" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <ExcelImportModal
      v-model:open="importDialog.visible"
      title="用户导入"
      :confirm-loading="importDialog.submitting"
      @submit="submitImport"
      @download-template="handleDownloadImportTemplate"
    />

    <a-modal
      v-model:open="editDialog.visible"
      :title="editDialog.mode === 'add' ? '新增用户' : '编辑用户'"
      :confirm-loading="editDialog.submitting"
      @ok="submitUser"
    >
      <a-form :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="用户名" :required="editDialog.mode === 'add'">
          <a-input
            v-model:value="editDialog.form.username"
            :disabled="editDialog.mode === 'edit'"
            placeholder="请输入用户名"
          />
        </a-form-item>
        <a-form-item v-if="editDialog.mode === 'add'" label="密码" required>
          <a-input-password v-model:value="editDialog.form.password" placeholder="请输入密码" />
        </a-form-item>
        <a-form-item label="姓名">
          <a-input v-model:value="editDialog.form.nickname" placeholder="请输入姓名" />
        </a-form-item>
        <a-form-item label="角色">
          <a-select
            v-model:value="editDialog.form.roleIds"
            mode="multiple"
            placeholder="请选择角色"
            :disabled="isProtectedAdminUser"
          >
            <a-select-option v-for="role in roleList" :key="role.id" :value="role.id">
              {{ role.name }}
            </a-select-option>
          </a-select>
          <div v-if="isProtectedAdminUser" class="role-lock-tip">管理员用户权限不可修改</div>
        </a-form-item>
        <a-form-item label="性别">
          <a-radio-group v-model:value="editDialog.form.gender">
            <a-radio value="男">男</a-radio>
            <a-radio value="女">女</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="手机号">
          <a-input v-model:value="editDialog.form.phone" placeholder="请输入手机号" />
        </a-form-item>
        <a-form-item label="警号">
          <a-input v-model:value="editDialog.form.policeId" placeholder="请输入警号" />
        </a-form-item>
        <a-form-item label="邮箱">
          <a-input v-model:value="editDialog.form.email" placeholder="请输入邮箱" />
        </a-form-item>
        <a-form-item label="入警日期">
          <a-date-picker
            v-model:value="editDialog.form.joinDate"
            value-format="YYYY-MM-DD"
            placeholder="请选择入警日期"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="所属单位">
          <a-select
            v-model:value="editDialog.form.departmentIds"
            mode="multiple"
            placeholder="请选择所属单位（可多选）"
            :options="departmentOptions"
            :filter-option="departmentFilter"
            allow-clear
            show-search
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="警种">
          <a-select
            v-model:value="editDialog.form.policeTypeIds"
            mode="multiple"
            placeholder="请选择警种"
            :options="policeTypeOptions"
            allow-clear
            style="width: 100%"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="resetPasswordDialog.visible"
      title="重置密码"
      :confirm-loading="resetPasswordDialog.submitting"
      @ok="submitResetPassword"
    >
      <p>
        正在为用户
        <strong>{{ resetPasswordDialog.user?.nickname || resetPasswordDialog.user?.username }}</strong>
        重置密码
      </p>
      <a-form :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="新密码" required>
          <a-input-password
            v-model:value="resetPasswordDialog.newPassword"
            placeholder="请输入新密码"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import {
  createUser,
  deleteUser,
  downloadUserImportTemplate,
  exportUsers,
  getPoliceTypes,
  getUsers,
  importUsers,
  resetPassword,
  updateUser,
  updateUserDepartments,
  updateUserPoliceTypes,
  updateUserRoles,
} from '@/api/user'
import { getDepartmentList } from '@/api/department'
import { getRoleList } from '@/api/role'
import { downloadBlob } from '@/utils/download'
import ExcelImportModal from './components/ExcelImportModal.vue'

const loading = ref(false)
const userList = ref([])
const roleList = ref([])
const departmentList = ref([])
const policeTypeList = ref([])
const exportingUsers = ref(false)

const PROTECTED_ADMIN_USERNAME = 'admin'

const filters = reactive({
  search: '',
  role: undefined,
})

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
})

const columns = [
  { title: '用户名', dataIndex: 'username', key: 'username' },
  { title: '姓名', dataIndex: 'nickname', key: 'nickname' },
  { title: '角色', key: 'roles' },
  { title: '所属单位', key: 'departments' },
  { title: '警号', dataIndex: 'policeId', key: 'policeId' },
  { title: '手机号', dataIndex: 'phone', key: 'phone' },
  { title: '状态', key: 'isActive', width: 90 },
  { title: '操作', key: 'action', width: 220 },
]

const departmentOptions = computed(() =>
  departmentList.value.map((item) => ({ value: item.id, label: item.name }))
)

const policeTypeOptions = computed(() =>
  policeTypeList.value.map((item) => ({ value: item.id, label: item.name }))
)

const isProtectedAdminUser = computed(() =>
  editDialog.mode === 'edit' && String(editDialog.form.username || '').toLowerCase() === PROTECTED_ADMIN_USERNAME
)

const departmentFilter = (input, option) => option.label.toLowerCase().includes(input.toLowerCase())

const editDialog = reactive({
  visible: false,
  mode: 'add',
  submitting: false,
  currentUserId: null,
  form: {
    username: '',
    password: '',
    nickname: '',
    roleIds: [],
    departmentIds: [],
    policeTypeIds: [],
    gender: undefined,
    phone: '',
    policeId: '',
    email: '',
    joinDate: null,
  },
})

const importDialog = reactive({
  visible: false,
  submitting: false,
})

const resetPasswordDialog = reactive({
  visible: false,
  submitting: false,
  user: null,
  newPassword: '',
})

onMounted(() => {
  loadRoleOptions()
  loadDepartmentOptions()
  loadPoliceTypeOptions()
  loadUsers()
})

function getRoleColor(code) {
  const colorMap = {
    admin: 'red',
    instructor: 'blue',
    student: 'green',
  }
  return colorMap[code] || 'default'
}

function getListParams() {
  return {
    page: pagination.current,
    size: pagination.pageSize,
    search: filters.search || undefined,
    role: filters.role || undefined,
  }
}

async function loadUsers() {
  loading.value = true
  try {
    const res = await getUsers(getListParams())
    userList.value = res?.items || []
    pagination.total = res?.total || 0
  } catch (error) {
    userList.value = []
    pagination.total = 0
    message.error(error?.message || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function loadRoleOptions() {
  try {
    const res = await getRoleList({ size: -1 })
    roleList.value = res?.items || []
  } catch {
    roleList.value = []
  }
}

async function loadDepartmentOptions() {
  try {
    const res = await getDepartmentList({ size: -1 })
    departmentList.value = res?.items || []
  } catch {
    departmentList.value = []
  }
}

async function loadPoliceTypeOptions() {
  try {
    const res = await getPoliceTypes()
    policeTypeList.value = Array.isArray(res) ? res : (res?.items || [])
  } catch {
    policeTypeList.value = []
  }
}

function handleSearch() {
  pagination.current = 1
  loadUsers()
}

function handleTableChange(pageInfo) {
  pagination.current = pageInfo.current
  pagination.pageSize = pageInfo.pageSize
  loadUsers()
}

function resetEditForm() {
  editDialog.form.username = ''
  editDialog.form.password = ''
  editDialog.form.nickname = ''
  editDialog.form.roleIds = []
  editDialog.form.departmentIds = []
  editDialog.form.policeTypeIds = []
  editDialog.form.gender = undefined
  editDialog.form.phone = ''
  editDialog.form.policeId = ''
  editDialog.form.email = ''
  editDialog.form.joinDate = null
}

function openCreateModal() {
  editDialog.mode = 'add'
  editDialog.currentUserId = null
  resetEditForm()
  editDialog.visible = true
}

function openEditModal(record) {
  editDialog.mode = 'edit'
  editDialog.currentUserId = record.id
  editDialog.form.username = record.username || ''
  editDialog.form.password = ''
  editDialog.form.nickname = record.nickname || ''
  editDialog.form.roleIds = (record.roles || []).map((item) => item.id)
  editDialog.form.departmentIds = (record.departments || []).map((item) => item.id)
  editDialog.form.policeTypeIds = (record.policeTypes || []).map((item) => item.id)
  editDialog.form.gender = record.gender || undefined
  editDialog.form.phone = record.phone || ''
  editDialog.form.policeId = record.policeId || ''
  editDialog.form.email = record.email || ''
  editDialog.form.joinDate = record.joinDate || null
  editDialog.visible = true
}

async function submitUser() {
  if (editDialog.mode === 'add') {
    if (!editDialog.form.username.trim()) {
      message.warning('请输入用户名')
      return
    }
    if (!editDialog.form.password) {
      message.warning('请输入密码')
      return
    }
  }

  editDialog.submitting = true
  try {
    if (editDialog.mode === 'add') {
      await createUser({
        username: editDialog.form.username.trim(),
        password: editDialog.form.password,
        nickname: editDialog.form.nickname || undefined,
        roleIds: editDialog.form.roleIds,
        departmentIds: editDialog.form.departmentIds,
        policeTypeIds: editDialog.form.policeTypeIds,
        gender: editDialog.form.gender || undefined,
        phone: editDialog.form.phone || undefined,
        policeId: editDialog.form.policeId || undefined,
        email: editDialog.form.email || undefined,
        joinDate: editDialog.form.joinDate || undefined,
      })
      message.success('新增用户成功')
    } else {
      await updateUser(editDialog.currentUserId, {
        nickname: editDialog.form.nickname || undefined,
        gender: editDialog.form.gender || undefined,
        phone: editDialog.form.phone || undefined,
        policeId: editDialog.form.policeId || undefined,
        email: editDialog.form.email || undefined,
        joinDate: editDialog.form.joinDate || undefined,
      })
      if (!isProtectedAdminUser.value) {
        await updateUserRoles(editDialog.currentUserId, editDialog.form.roleIds)
      }
      await updateUserDepartments(editDialog.currentUserId, editDialog.form.departmentIds)
      await updateUserPoliceTypes(editDialog.currentUserId, editDialog.form.policeTypeIds)
      message.success('更新用户成功')
    }

    editDialog.visible = false
    loadUsers()
  } catch (error) {
    message.error(error?.message || '保存用户失败')
  } finally {
    editDialog.submitting = false
  }
}

async function handleDelete(record) {
  try {
    await deleteUser(record.id)
    message.success('删除用户成功')
    loadUsers()
  } catch (error) {
    message.error(error?.message || '删除用户失败')
  }
}

function openResetPasswordModal(record) {
  resetPasswordDialog.user = record
  resetPasswordDialog.newPassword = ''
  resetPasswordDialog.visible = true
}

async function submitResetPassword() {
  if (!resetPasswordDialog.newPassword) {
    message.warning('请输入新密码')
    return
  }
  if (!resetPasswordDialog.user?.id) return

  resetPasswordDialog.submitting = true
  try {
    await resetPassword(resetPasswordDialog.user.id, resetPasswordDialog.newPassword)
    message.success('重置密码成功')
    resetPasswordDialog.visible = false
  } catch (error) {
    message.error(error?.message || '重置密码失败')
  } finally {
    resetPasswordDialog.submitting = false
  }
}

function openImportModal() {
  importDialog.visible = true
}

async function handleDownloadImportTemplate() {
  try {
    const blob = await downloadUserImportTemplate()
    downloadBlob(blob, '用户导入模板.xlsx')
  } catch (error) {
    message.error(error?.message || '下载模板失败')
  }
}

async function submitImport(file) {
  importDialog.submitting = true
  try {
    const result = await importUsers(file, 'student')
    message.success(
      `导入完成：成功 ${result?.successRows || 0} 行，新增账号 ${result?.createdCount || 0} 个，更新 ${result?.updatedCount || 0} 个`
    )
    importDialog.visible = false
    loadUsers()
  } catch (error) {
    message.error(error?.message || '用户导入失败')
  } finally {
    importDialog.submitting = false
  }
}

async function handleExportUsers() {
  exportingUsers.value = true
  try {
    const blob = await exportUsers({
      search: filters.search || undefined,
      role: filters.role || undefined,
    })
    downloadBlob(blob, '用户导出.xlsx')
  } catch (error) {
    message.error(error?.message || '用户导出失败')
  } finally {
    exportingUsers.value = false
  }
}
</script>

<style scoped>
.user-manage-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--police-primary);
}

.role-lock-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #999;
}
</style>
