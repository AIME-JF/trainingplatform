<template>
  <div class="evaluation-center">
    <div class="page-header">
      <h2 class="page-title">问卷中心</h2>
    </div>

    <div class="eval-tabs">
      <span
        class="eval-tab"
        :class="{ active: activeTab === 'active' }"
        @click="activeTab = 'active'"
      >正在进行</span>
      <span
        class="eval-tab"
        :class="{ active: activeTab === 'closed' }"
        @click="activeTab = 'closed'"
      >已结束</span>
    </div>

    <a-spin :spinning="loading">
      <div v-if="filteredTasks.length" class="eval-list">
        <div
          v-for="task in filteredTasks"
          :key="task.id"
          class="eval-card"
          @click="goFill(task)"
        >
          <div class="eval-card-header">
            <span class="eval-card-title">{{ task.title }}</span>
            <a-tag v-if="task.user_completed" color="blue" size="small">已填写</a-tag>
            <a-tag v-else-if="task.status === 'active'" color="green" size="small">进行中</a-tag>
            <a-tag v-else color="default" size="small">已结束</a-tag>
          </div>
          <div class="eval-card-meta">
            <span v-if="task.training_name"><TagOutlined /> {{ task.training_name }}</span>
            <span v-if="task.end_time"><ClockCircleOutlined /> 截止 {{ formatTime(task.end_time) }}</span>
          </div>
          <div class="eval-card-footer">
            <span>共 {{ task.item_count || 0 }} 项评价</span>
            <span v-if="task.user_completed" class="eval-card-action muted">已完成</span>
            <span v-else-if="task.status === 'active'" class="eval-card-action">去填写 →</span>
            <span v-else class="eval-card-action muted">已结束</span>
          </div>
        </div>
      </div>
      <a-empty v-else :description="activeTab === 'active' ? '暂无进行中的问卷' : '暂无已结束的问卷'" />
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { TagOutlined, ClockCircleOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import axiosInstance from '@/api/custom-instance'

const router = useRouter()
const loading = ref(false)
const activeTab = ref<'active' | 'closed'>('active')
const tasks = ref<any[]>([])

const filteredTasks = computed(() =>
  tasks.value.filter(t => {
    if (activeTab.value === 'active') return t.status === 'active' && !t.user_completed
    return t.status === 'closed' || t.user_completed
  })
)

function targetTypeLabel(type: string) {
  const map: Record<string, string> = {
    course: '课程评价',
    instructor: '教官评价',
    training: '培训班评价',
    training_base: '基地评价',
  }
  return map[type] || type
}

function formatTime(time: string) {
  return dayjs(time).format('MM/DD HH:mm')
}

function goFill(task: any) {
  router.push({ name: 'EvaluationFill', params: { taskId: task.id } })
}

async function fetchTasks() {
  loading.value = true
  try {
    const { data } = await axiosInstance.get('/evaluations/tasks')
    tasks.value = data || []
  } catch {
    tasks.value = []
  } finally {
    loading.value = false
  }
}

onMounted(fetchTasks)
</script>

<style scoped>
.evaluation-center {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 16px;
}

.page-header {
  margin-bottom: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 400;
  color: var(--v2-text-primary);
  margin: 0;
}

@media (max-width: 768px) {
  .page-title {
    font-size: 18px;
    text-align: center;
  }
}

.eval-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 16px;
  border-radius: var(--v2-radius-sm);
  background: var(--v2-bg);
  padding: 4px;
}

.eval-tab {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  font-size: 14px;
  color: var(--v2-text-secondary);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.eval-tab.active {
  background: var(--v2-primary);
  color: #fff;
  font-weight: 500;
}

.eval-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.eval-card {
  padding: 16px;
  background: var(--v2-bg-card);
  border: 1px solid var(--v2-border-light);
  border-radius: var(--v2-radius);
  cursor: pointer;
  transition: all 0.2s;
}

.eval-card:active {
  transform: scale(0.98);
}

@media (min-width: 769px) {
  .eval-card:hover {
    border-color: var(--v2-primary);
    box-shadow: var(--v2-shadow);
  }
}

.eval-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.eval-card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 8px;
}

.eval-card-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--v2-text-muted);
  margin-bottom: 10px;
}

.eval-card-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.eval-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.eval-card-action {
  color: var(--v2-primary);
  font-weight: 500;
}

.eval-card-action.muted {
  color: var(--v2-text-muted);
}
</style>
