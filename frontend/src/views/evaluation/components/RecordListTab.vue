<template>
  <div>
    <div class="tab-toolbar">
      <a-select v-model:value="filterType" placeholder="对象类型" allow-clear style="width: 140px" @change="fetchRecords">
        <a-select-option value="course">课程</a-select-option>
        <a-select-option value="instructor">教官</a-select-option>
        <a-select-option value="training">培训班</a-select-option>
        <a-select-option value="training_base">培训基地</a-select-option>
      </a-select>
    </div>

    <a-table :data-source="recordList" :columns="columns" :loading="loading" :pagination="false" row-key="id" size="small">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'targetType'">
          {{ targetTypeLabels[record.targetType] || record.targetType }}
        </template>
        <template v-if="column.key === 'avgScore'">
          <a-rate :value="record.avgScore" disabled allow-half :count="5" style="font-size: 14px" />
          <span style="margin-left: 4px; color: #faad14">{{ record.avgScore }}</span>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import request from '@/api/request'

const targetTypeLabels = { course: '课程', instructor: '教官', training: '培训班', training_base: '培训基地' }

const loading = ref(false)
const recordList = ref([])
const filterType = ref(undefined)

const columns = [
  { title: '评价人', dataIndex: 'userNickname', key: 'userNickname', width: 100, customRender: ({ record }) => record.userNickname || record.userName },
  { title: '对象类型', key: 'targetType', width: 100 },
  { title: '评分', key: 'avgScore', width: 200 },
  { title: '评语', dataIndex: 'comment', key: 'comment', ellipsis: true },
  { title: '时间', dataIndex: 'createdAt', key: 'createdAt', width: 160 },
]

async function fetchRecords() {
  loading.value = true
  try {
    const params = {}
    if (filterType.value) params.targetType = filterType.value
    recordList.value = await request.get('/evaluations/records', { params }) || []
  } catch { recordList.value = [] } finally { loading.value = false }
}

onMounted(fetchRecords)
</script>

<style scoped>
.tab-toolbar { display: flex; align-items: center; margin-bottom: 12px; }
</style>
