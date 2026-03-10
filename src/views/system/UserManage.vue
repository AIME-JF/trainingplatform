<template>
  <div class="user-manage-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <a-space>
        <a-button @click="openImportModal">用户导入</a-button>
        <a-button type="primary" @click="openCreateModal"><PlusOutlined /> 新增用户</a-button>
      </a-space>
    </div>

    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input-search v-model:value="searchText" placeholder="搜索姓名/用户名/警号..." allow-clear @search="loadUsers" />
        </a-col>
        <a-col :span="6">
          <a-select v-model:value="filterRole" placeholder="按角色筛选" allow-clear style="width: 100%" @change="loadUsers">
            <a-select-option v-for="r in roleList" :key="r.code" :value="r.code">{{ r.name }}</a-select-option>
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
            <a-tag v-for="r in record.roles" :key="r.id" :color="getRoleColor(r.code)">{{ r.name }}</a-tag>
            <span v-if="!record.roles || record.roles.length === 0" style="color: #999">未分配</span>
          </template>
          <template v-if="column.key === 'departments'">
            <template v-if="record.departments && record.departments.length">
              <a-tag v-for="d in record.departments" :key="d.id" color="cyan">{{ d.name }}</a-tag>
            </template>
            <span v-else style="color: #999">-</span>
          </template>
          <template v-if="column.key === 'isActive'">
            <a-tag :color="record.isActive ? 'green' : 'red'">{{ record.isActive ? '正常' : '已禁用' }}</a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" type="link" @click="openEditModal(record)">编辑</a-button>
              <a-button size="small" type="link" @click="openResetPwdModal(record)">重置密码</a-button>
              <a-popconfirm :title="`确定删除用户「${record.nickname || record.username}」吗？`" ok-text="删除" cancel-text="取消" @confirm="handleDelete(record)">
                <a-button size="small" type="link" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 用户导入弹窗 -->
    <a-modal
      v-model:open="importModalVisible"
      title="用户导入"
      centered
      ok-text="开始导入"
      cancel-text="取消"
      :confirm-loading="importingPoliceBase"
      @ok="handleImportSubmit"
      @cancel="handleImportCancel"
      :destroy-on-close="true"
    >
      <a-upload-dragger
        v-model:fileList="importFileList"
        :before-upload="beforeImportUpload"
        :max-count="1"
        accept=".xlsx"
      >
        <p class="ant-upload-drag-icon">
          <InboxOutlined style="font-size: 26px; color: #003087;" />
        </p>
        <p>拖动到此上传</p>
        <p class="upload-hint">或点击选择 Excel 文件（仅支持 .xlsx）</p>
      </a-upload-dragger>

      <div class="import-modal-actions">
        <a-button type="link" @click="downloadImportTemplate">下载模板</a-button>
      </div>
    </a-modal>

    <!-- 新增/编辑弹窗 -->
    <a-modal v-model:open="modalVisible" :title="isEdit ? '编辑用户' : '新增用户'" :confirm-loading="submitting" @ok="handleSubmit" @cancel="modalVisible = false">
      <a-form :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="用户名" :required="!isEdit">
          <a-input v-model:value="form.username" :disabled="isEdit" placeholder="请输入用户名" />
        </a-form-item>
        <a-form-item v-if="!isEdit" label="密码" required>
          <a-input-password v-model:value="form.password" placeholder="请输入密码" />
        </a-form-item>
        <a-form-item label="姓名">
          <a-input v-model:value="form.nickname" placeholder="请输入姓名" />
        </a-form-item>
        <a-form-item label="角色">
          <a-select v-model:value="form.roleIds" mode="multiple" placeholder="请选择角色">
            <a-select-option v-for="r in roleList" :key="r.id" :value="r.id">{{ r.name }}</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="性别">
          <a-radio-group v-model:value="form.gender">
            <a-radio value="男">男</a-radio>
            <a-radio value="女">女</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="手机号">
          <a-input v-model:value="form.phone" placeholder="请输入手机号" />
        </a-form-item>
        <a-form-item label="警号">
          <a-input v-model:value="form.policeId" placeholder="请输入警号" />
        </a-form-item>
        <a-form-item label="邮箱">
          <a-input v-model:value="form.email" placeholder="请输入邮箱" />
        </a-form-item>
        <a-form-item label="入警日期">
          <a-date-picker v-model:value="form.joinDate" value-format="YYYY-MM-DD" placeholder="请选择入警日期" style="width:100%" />
        </a-form-item>
        <a-form-item label="所属单位">
          <a-select
            v-model:value="form.departmentIds"
            mode="tags"
            placeholder="搜索或输入后回车新建单位（可多选）"
            :options="departmentOptions"
            :filter-option="deptFilterOption"
            @change="onDepartmentChange"
            allow-clear
            show-search
            style="width:100%"
          />
        </a-form-item>
        <a-form-item label="警种">
          <a-select
            v-model:value="form.policeTypeIds"
            mode="multiple"
            placeholder="请选择警种"
            :options="policeTypeOptions"
            allow-clear
            style="width:100%"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 重置密码弹窗 -->
    <a-modal v-model:open="resetPwdVisible" title="重置密码" :confirm-loading="submitting" @ok="handleResetPwd" @cancel="resetPwdVisible = false">
      <p>正在为用户 <strong>{{ resetPwdUser?.nickname || resetPwdUser?.username }}</strong> 重置密码</p>
      <a-form :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="新密码" required>
          <a-input-password v-model:value="newPassword" placeholder="请输入新密码" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { PlusOutlined, InboxOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { getUsers, createUser, updateUser, updateUserRoles, updateUserDepartments, updateUserPoliceTypes, resetPassword, deleteUser, getRoles, getDepartments, getPoliceTypes, createDepartment, importPoliceBase } from '@/api/user'

const loading = ref(false)
const submitting = ref(false)
const searchText = ref('')
const filterRole = ref(undefined)
const userList = ref([])
const roleList = ref([])
const departmentList = ref([])
const importingPoliceBase = ref(false)
const importModalVisible = ref(false)
const importFileList = ref([])
const departmentOptions = computed(() => departmentList.value.map(d => ({ value: d.id, label: d.name })))

const policeTypeList = ref([])
const policeTypeOptions = computed(() => policeTypeList.value.map(pt => ({ value: pt.id, label: pt.name })))

const deptFilterOption = (input, option) => option.label.toLowerCase().includes(input.toLowerCase())

async function onDepartmentChange(values) {
  for (let i = 0; i < values.length; i++) {
    const val = values[i]
    if (typeof val === 'string') {
      try {
        const res = await createDepartment(val)
        const dept = res?.id ? res : res
        if (dept?.id) {
          departmentList.value.push(dept)
          // 替换掉文本值
          values[i] = dept.id
          message.success(`已自动新建单位「${val}」`)
        }
      } catch {
        message.error(`「${val}」新建失败`)
        // 移除失败的文本值
        values.splice(i, 1)
        i--
      }
    }
  }
}

const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

const columns = [
  { title: '用户名', dataIndex: 'username', key: 'username' },
  { title: '姓名', dataIndex: 'nickname', key: 'nickname' },
  { title: '角色', key: 'roles' },
  { title: '所属单位', key: 'departments' },
  { title: '警号', dataIndex: 'policeId', key: 'policeId' },
  { title: '手机号', dataIndex: 'phone', key: 'phone' },
  { title: '状态', key: 'isActive', width: 80 },
  { title: '操作', key: 'action', width: 200 },
]

function getRoleColor(code) {
  const map = { admin: 'red', instructor: 'blue', student: 'green' }
  return map[code] || 'default'
}

async function loadUsers() {
  loading.value = true
  try {
    const res = await getUsers({
      page: pagination.current,
      size: pagination.pageSize,
      search: searchText.value || undefined,
      role: filterRole.value || undefined,
    })
    userList.value = res.items || []
    pagination.total = res.total || 0
  } catch {
    userList.value = []
  } finally {
    loading.value = false
  }
}

async function loadRoles() {
  try {
    const res = await getRoles()
    roleList.value = res || []
  } catch { /* ignore */ }
}

async function loadDepartments() {
  try {
    const res = await getDepartments()
    departmentList.value = Array.isArray(res) ? res : (res.items || res || [])
  } catch { /* ignore */ }
}

async function loadPoliceTypes() {
  try {
    const res = await getPoliceTypes()
    policeTypeList.value = Array.isArray(res) ? res : (res.items || res?.data?.items || res || [])
  } catch { /* ignore */ }
}

function openImportModal() {
  importModalVisible.value = true
}

function handleImportCancel() {
  importModalVisible.value = false
  importFileList.value = []
}

function beforeImportUpload() {
  return false
}

function downloadImportTemplate() {
  const baseUrl = import.meta.env.BASE_URL || '/'
  const normalizedBase = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`
  const link = document.createElement('a')
  link.href = `${normalizedBase}templates/user-import-template.xlsx`
  link.download = '用户导入模板.xlsx'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

async function handleImportSubmit() {
  const selected = importFileList.value[0]
  const file = selected?.originFileObj || selected
  if (!file) {
    message.warning('请先选择导入文件')
    return
  }

  importingPoliceBase.value = true
  try {
    const result = await importPoliceBase(file, 'student')
    message.success(
      `导入完成：成功 ${result.successRows || 0} 行，新增账号 ${result.createdCount || 0} 个，更新 ${result.updatedCount || 0} 个`
    )
    importModalVisible.value = false
    importFileList.value = []
    loadUsers()
  } catch (e) {
    message.error(e?.message || '用户导入失败')
  } finally {
    importingPoliceBase.value = false
  }
}

function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadUsers()
}

onMounted(() => {
  loadRoles()
  loadDepartments()
  loadPoliceTypes()
  loadUsers()
})

// 新增/编辑
const modalVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const form = reactive({
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
})

function resetForm() {
  form.username = ''
  form.password = ''
  form.nickname = ''
  form.roleIds = []
  form.departmentIds = []
  form.policeTypeIds = []
  form.gender = undefined
  form.phone = ''
  form.policeId = ''
  form.email = ''
  form.joinDate = null
}

function openCreateModal() {
  isEdit.value = false
  editingId.value = null
  resetForm()
  modalVisible.value = true
}

function openEditModal(record) {
  isEdit.value = true
  editingId.value = record.id
  form.username = record.username
  form.password = ''
  form.nickname = record.nickname || ''
  form.roleIds = (record.roles || []).map(r => r.id)
  form.departmentIds = (record.departments || []).map(d => d.id)
  form.policeTypeIds = (record.policeTypes || []).map(p => p.id)
  form.gender = record.gender || undefined
  form.phone = record.phone || ''
  form.policeId = record.policeId || ''
  form.email = record.email || ''
  form.joinDate = record.join_date || record.joinDate || null
  modalVisible.value = true
}

async function handleSubmit() {
  if (!isEdit.value) {
    if (!form.username || !form.password) {
      message.warning('请填写用户名和密码')
      return
    }
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateUser(editingId.value, {
        nickname: form.nickname || undefined,
        gender: form.gender || undefined,
        phone: form.phone || undefined,
        policeId: form.policeId || undefined,
        email: form.email || undefined,
        join_date: form.joinDate || undefined,
      })
      await updateUserRoles(editingId.value, form.roleIds)
      // 同步更新所属单位
      if (form.departmentIds !== undefined) {
        try { await updateUserDepartments(editingId.value, form.departmentIds) } catch { /* ignore */ }
      }
      // 同步更新警种
      if (form.policeTypeIds !== undefined) {
        try { await updateUserPoliceTypes(editingId.value, form.policeTypeIds) } catch { /* ignore */ }
      }
      message.success('更新成功')
    } else {
      await createUser({
        username: form.username,
        password: form.password,
        nickname: form.nickname || undefined,
        gender: form.gender || undefined,
        phone: form.phone || undefined,
        policeId: form.policeId || undefined,
        email: form.email || undefined,
        join_date: form.joinDate || undefined,
        roleIds: form.roleIds,
        departmentIds: form.departmentIds,
        police_type_ids: form.policeTypeIds,
      })
      message.success('创建成功')
    }
    modalVisible.value = false
    loadUsers()
  } catch (e) {
    message.error(e?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function handleDelete(record) {
  try {
    await deleteUser(record.id)
    message.success('删除成功')
    loadUsers()
  } catch {
    message.error('删除失败')
  }
}

// 重置密码
const resetPwdVisible = ref(false)
const resetPwdUser = ref(null)
const newPassword = ref('')

function openResetPwdModal(record) {
  resetPwdUser.value = record
  newPassword.value = ''
  resetPwdVisible.value = true
}

async function handleResetPwd() {
  if (!newPassword.value) {
    message.warning('请输入新密码')
    return
  }
  submitting.value = true
  try {
    await resetPassword(resetPwdUser.value.id, newPassword.value)
    message.success('密码重置成功')
    resetPwdVisible.value = false
  } catch {
    message.error('密码重置失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.user-manage-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.upload-hint { font-size: 12px; color: #999; }
.import-modal-actions { margin-top: 12px; text-align: left; }
</style>
