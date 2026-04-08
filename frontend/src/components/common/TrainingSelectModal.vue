<template>
  <a-modal
    :open="open"
    :title="title"
    width="800px"
    :footer="null"
    @update:open="(val) => $emit('update:open', val)"
  >
    <div class="ts-toolbar">
      <a-input-search
        v-model:value="searchText"
        placeholder="搜索培训班名称"
        allow-clear
        style="width: 240px"
        @search="handleSearch"
      />
      <a-select v-model:value="statusFilter" placeholder="状态" mode="multiple" allow-clear style="min-width: 180px" @change="handleSearch">
        <a-select-option value="upcoming">待开班</a-select-option>
        <a-select-option value="active">进行中</a-select-option>
        <a-select-option value="ended">已结束</a-select-option>
      </a-select>
    </div>
    <div class="ts-table-wrap">
      <a-table
        :data-source="list"
        :columns="columns"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        size="small"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-button type="link" size="small" @click="handleSelect(record)">选择</a-button>
          </template>
        </template>
      </a-table>
    </div>
  </a-modal>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import request from '@/api/request'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '选择培训班' },
})

const emit = defineEmits(['update:open', 'select'])

const loading = ref(false)
const list = ref([])
const searchText = ref('')
const statusFilter = ref(['upcoming', 'active'])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (t) => `共 ${t} 条`,
})

const columns = [
  { title: '培训班名称', dataIndex: 'name', key: 'name', ellipsis: true },
  { title: '创建者', dataIndex: 'createdByName', key: 'createdByName', width: 100 },
  { title: '状态', key: 'status', width: 90 },
  { title: '开始日期', dataIndex: 'startDate', key: 'startDate', width: 110 },
  { title: '结束日期', dataIndex: 'endDate', key: 'endDate', width: 110 },
  { title: '操作', key: 'action', width: 80 },
]

function statusColor(s) {
  return { upcoming: 'blue', active: 'green', ended: 'default' }[s] || 'default'
}

function statusLabel(s) {
  return { upcoming: '待开班', active: '进行中', ended: '已结束' }[s] || s
}

function handleSearch() {
  page.value = 1
  pagination.current = 1
  fetchTrainings()
}

function handleTableChange(pag) {
  page.value = pag.current
  pageSize.value = pag.pageSize
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchTrainings()
}

async function fetchTrainings() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      size: pageSize.value,
      search: searchText.value.trim() || undefined,
    }
    if (statusFilter.value && statusFilter.value.length) {
      params.status = statusFilter.value.join(',')
    }
    const res = await request.get('/trainings', { params })
    list.value = res.items || []
    total.value = res.total || 0
    pagination.total = total.value
  } catch {
    list.value = []
    total.value = 0
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

function handleSelect(record) {
  emit('select', record)
  emit('update:open', false)
}

watch(() => props.open, (val) => {
  if (val) {
    searchText.value = ''
    statusFilter.value = ['upcoming', 'active']
    page.value = 1
    pagination.current = 1
    fetchTrainings()
  }
})
</script>

<style scoped>
.ts-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.ts-table-wrap {
  max-height: 420px;
  overflow-y: auto;
}
</style>
