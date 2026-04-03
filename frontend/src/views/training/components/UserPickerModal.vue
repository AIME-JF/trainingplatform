<template>
  <a-modal
    :open="open"
    :title="title"
    width="600px"
    :footer="null"
    @cancel="$emit('update:open', false)"
  >
    <a-radio-group v-model:value="mode" style="margin-bottom:16px">
      <a-radio-button value="none">不选择</a-radio-button>
      <a-radio-button value="user">关联用户</a-radio-button>
      <a-radio-button value="custom">自定义输入</a-radio-button>
    </a-radio-group>

    <!-- 不选择 -->
    <div v-if="mode === 'none'" style="padding:24px 0;text-align:center;color:#999">
      <p>将清空当前选择</p>
      <a-button type="primary" @click="handleConfirmNone">确认清空</a-button>
    </div>

    <!-- 关联用户 -->
    <div v-if="mode === 'user'">
      <a-input-search
        v-model:value="searchText"
        placeholder="搜索姓名或用户名"
        style="margin-bottom:12px"
        allow-clear
        @search="handleSearch"
        @change="onSearchChange"
      />
      <a-table
        :data-source="userList"
        :columns="userColumns"
        :loading="userLoading"
        :pagination="pagination"
        size="small"
        row-key="id"
        :row-class-name="(record) => record.id === selectedUserId ? 'selected-row' : ''"
        @change="onTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            {{ record.nickname || record.username }}
          </template>
          <template v-if="column.key === 'dept'">
            {{ (record.departments && record.departments.length) ? record.departments[0].name : '-' }}
          </template>
          <template v-if="column.key === 'action'">
            <a-button
              type="link"
              size="small"
              :disabled="record.id === selectedUserId"
              @click="handleSelectUser(record)"
            >
              {{ record.id === selectedUserId ? '已选择' : '选择' }}
            </a-button>
          </template>
        </template>
      </a-table>
      <div v-if="selectedUserId" style="margin-top:12px;text-align:right">
        <a-space>
          <span style="color:#52c41a">已选择：{{ selectedUserName }}</span>
          <a-button type="primary" @click="handleConfirmUser">确认选择</a-button>
        </a-space>
      </div>
    </div>

    <!-- 自定义输入 -->
    <div v-if="mode === 'custom'" style="padding:16px 0">
      <a-form-item label="姓名" :label-col="{ span: 4 }" :wrapper-col="{ span: 16 }">
        <a-input v-model:value="customName" placeholder="请输入姓名" :maxlength="100" />
      </a-form-item>
      <div style="text-align:right;margin-top:12px">
        <a-button type="primary" :disabled="!customName.trim()" @click="handleConfirmCustom">确认输入</a-button>
      </div>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, watch, reactive } from 'vue'
import { getUsers } from '@/api/user'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '选择用户' },
  currentName: { type: String, default: '' },
})

const emit = defineEmits(['update:open', 'select'])

const mode = ref('user')
const searchText = ref('')
const userList = ref([])
const userLoading = ref(false)
const selectedUserId = ref(null)
const selectedUserName = ref('')
const customName = ref('')
let searchTimer = null

const pagination = reactive({
  current: 1,
  pageSize: 8,
  total: 0,
  showSizeChanger: false,
  showTotal: (total) => `共 ${total} 条`,
})

const userColumns = [
  { title: '姓名', key: 'name', ellipsis: true },
  { title: '用户名', dataIndex: 'username', key: 'username', width: 120, ellipsis: true },
  { title: '部门', key: 'dept', width: 120, ellipsis: true },
  { title: '操作', key: 'action', width: 80, align: 'center' },
]

watch(() => props.open, (val) => {
  if (val) {
    mode.value = 'user'
    searchText.value = ''
    selectedUserId.value = null
    selectedUserName.value = ''
    customName.value = props.currentName || ''
    pagination.current = 1
    loadUsers()
  }
})

async function loadUsers() {
  userLoading.value = true
  try {
    const res = await getUsers({
      page: pagination.current,
      size: pagination.pageSize,
      search: searchText.value || undefined,
    })
    userList.value = res?.items || []
    pagination.total = res?.total || 0
  } catch {
    userList.value = []
    pagination.total = 0
  } finally {
    userLoading.value = false
  }
}

function handleSearch() {
  pagination.current = 1
  loadUsers()
}

function onSearchChange() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    pagination.current = 1
    loadUsers()
  }, 400)
}

function onTableChange(pag) {
  pagination.current = pag.current
  loadUsers()
}

function handleSelectUser(record) {
  selectedUserId.value = record.id
  selectedUserName.value = record.nickname || record.username
}

function handleConfirmNone() {
  emit('select', { mode: 'none', userId: null, name: '' })
  emit('update:open', false)
}

function handleConfirmUser() {
  emit('select', { mode: 'user', userId: selectedUserId.value, name: selectedUserName.value })
  emit('update:open', false)
}

function handleConfirmCustom() {
  const name = customName.value.trim()
  if (!name) return
  emit('select', { mode: 'custom', userId: null, name })
  emit('update:open', false)
}
</script>

<style scoped>
:deep(.selected-row) {
  background-color: #e6f7ff;
}
</style>
