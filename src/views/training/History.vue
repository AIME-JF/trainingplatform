<template>
  <div class="history-page">
    <div class="page-header">
      <div>
        <h2>{{ authStore.isStudent ? '我的训历' : '培训训历' }}</h2>
        <p class="page-sub">{{ trainingName }}</p>
      </div>
      <a-button @click="$router.back()">返回</a-button>
    </div>

    <a-card :bordered="false">
      <a-table :columns="columns" :data-source="histories" row-key="id" :pagination="{ pageSize: 10 }">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'departments'">
            {{ (record.departments || []).join(' / ') }}
          </template>
          <template v-if="column.key === 'attendanceRate'">
            <a-progress :percent="Math.round(record.attendanceRate || 0)" size="small" />
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { getTraining, getTrainingHistories } from '@/api/training'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const authStore = useAuthStore()
const trainingId = route.params.id

const trainingName = ref('')
const histories = ref([])

const columns = computed(() => {
  const base = [
    { title: '姓名', dataIndex: 'userNickname', key: 'userNickname', width: 120 },
    { title: '警号', dataIndex: 'policeId', key: 'policeId', width: 120 },
    { title: '单位', key: 'departments' },
    { title: '出勤率', key: 'attendanceRate', width: 180 },
    { title: '完成课次', dataIndex: 'completedSessions', key: 'completedSessions', width: 100 },
    { title: '总课次', dataIndex: 'totalSessions', key: 'totalSessions', width: 100 },
    { title: '评课均分', dataIndex: 'evaluationScore', key: 'evaluationScore', width: 100 },
    { title: '通过考试', dataIndex: 'passedExamCount', key: 'passedExamCount', width: 100 },
  ]
  return authStore.isStudent ? base.filter(item => !['userNickname', 'policeId', 'departments'].includes(item.key)) : base
})

async function loadData() {
  try {
    const training = await getTraining(trainingId)
    trainingName.value = training.name
    const result = await getTrainingHistories(trainingId, authStore.isStudent ? { userId: authStore.currentUser?.id } : undefined)
    histories.value = result || []
  } catch (error) {
    message.error(error.message || '加载训历失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.history-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-header h2 { margin: 0; color: #001234; }
.page-sub { margin: 6px 0 0; color: #8c8c8c; font-size: 13px; }
</style>
