<template>
  <div class="training-list-page">
    <div class="page-header">
      <h2>培训班管理</h2>
      <a-button type="primary" v-if="authStore.isAdmin || authStore.isInstructor">
        <template #icon><PlusOutlined /></template>新建培训班
      </a-button>
    </div>

    <!-- 统计卡 -->
    <a-row :gutter="16" style="margin-bottom:20px">
      <a-col :span="6" v-for="stat in stats" :key="stat.label">
        <a-card :bordered="false" class="stat-card">
          <div class="stat-icon" :style="{ background: stat.color + '20', color: stat.color }">{{ stat.icon }}</div>
          <div class="stat-num">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 过滤 -->
    <a-card :bordered="false" style="margin-bottom:16px">
      <a-space>
        <a-select v-model:value="filterStatus" style="width:120px">
          <a-select-option value="all">全部状态</a-select-option>
          <a-select-option value="active">进行中</a-select-option>
          <a-select-option value="upcoming">未开始</a-select-option>
          <a-select-option value="ended">已结束</a-select-option>
        </a-select>
        <a-input-search v-model:value="searchText" placeholder="搜索培训班..." style="width:240px" />
      </a-space>
    </a-card>

    <!-- 培训班列表 -->
    <div class="training-cards">
      <div v-for="t in filteredTrainings" :key="t.id" class="training-card">
        <div class="tc-header" :class="'status-' + t.status">
          <div class="tc-status-dot"></div>
          <span class="tc-status-text">{{ statusLabels[t.status] }}</span>
        </div>
        <div class="tc-body">
          <div class="tc-title">{{ t.title }}</div>
          <div class="tc-meta">
            <div class="tc-meta-item"><CalendarOutlined /> {{ t.startDate }} ~ {{ t.endDate }}</div>
            <div class="tc-meta-item"><TeamOutlined /> {{ t.enrolledCount }}/{{ t.capacity }} 人</div>
            <div class="tc-meta-item"><UserOutlined /> {{ t.instructor }}</div>
            <div class="tc-meta-item"><EnvironmentOutlined /> {{ t.location }}</div>
          </div>
          <a-progress
            :percent="Math.round(t.enrolledCount/t.capacity*100)"
            :stroke-color="t.enrolledCount >= t.capacity ? '#ff4d4f' : '#003087'"
            size="small"
            style="margin-top:12px"
          />
        </div>
        <div class="tc-footer">
          <a-button size="small" @click="goDetail(t)">查看详情</a-button>
          <a-button size="small" type="primary" @click="goCheckin(t)" v-if="t.status === 'active'">
            <template #icon><QrcodeOutlined /></template>扫码签到
          </a-button>
          <a-button size="small" @click="goSchedule(t)" v-if="authStore.isStudent">查看日程</a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { PlusOutlined, CalendarOutlined, TeamOutlined, UserOutlined, EnvironmentOutlined, QrcodeOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { MOCK_TRAININGS } from '@/mock/trainings'

const router = useRouter()
const authStore = useAuthStore()
const filterStatus = ref('all')
const searchText = ref('')

const statusLabels = { active: '进行中', upcoming: '未开始', ended: '已结束' }

const filteredTrainings = computed(() => {
  let list = [...MOCK_TRAININGS]
  if (filterStatus.value !== 'all') list = list.filter(t => t.status === filterStatus.value)
  if (searchText.value) list = list.filter(t => t.title.includes(searchText.value))
  return list
})

const stats = [
  { icon: '🏫', label: '全部培训班', value: MOCK_TRAININGS.length, color: '#003087' },
  { icon: '▶', label: '进行中', value: MOCK_TRAININGS.filter(t => t.status === 'active').length, color: '#52c41a' },
  { icon: '🕐', label: '未开始', value: MOCK_TRAININGS.filter(t => t.status === 'upcoming').length, color: '#faad14' },
  { icon: '✓', label: '已结束', value: MOCK_TRAININGS.filter(t => t.status === 'ended').length, color: '#888' },
]

const goDetail = (t) => router.push({ name: 'TrainingDetail', params: { id: t.id } })
const goCheckin = (t) => router.push({ name: 'TrainingCheckin', params: { id: t.id } })
const goSchedule = (t) => router.push('/training/schedule')
</script>

<style scoped>
.training-list-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.stat-card { text-align: center; }
.stat-icon { width: 48px; height: 48px; border-radius: 50%; margin: 0 auto 8px; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.stat-num { font-size: 28px; font-weight: 700; color: #1a1a1a; }
.stat-label { font-size: 12px; color: #888; }
.training-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.training-card { background: #fff; border-radius: 8px; border: 1px solid #e8e8e8; overflow: hidden; }
.tc-header { padding: 8px 16px; display: flex; align-items: center; gap: 8px; }
.tc-header.status-active { background: #f6ffed; }
.tc-header.status-upcoming { background: #fffbe6; }
.tc-header.status-ended { background: #f5f5f5; }
.tc-status-dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.status-active .tc-status-dot { background: #52c41a; }
.status-upcoming .tc-status-dot { background: #faad14; }
.status-ended .tc-status-dot { background: #bbb; }
.tc-status-text { font-size: 12px; font-weight: 600; }
.status-active .tc-status-text { color: #52c41a; }
.status-upcoming .tc-status-text { color: #faad14; }
.status-ended .tc-status-text { color: #888; }
.tc-body { padding: 14px 16px; }
.tc-title { font-size: 15px; font-weight: 600; color: #1a1a1a; margin-bottom: 12px; }
.tc-meta { display: flex; flex-direction: column; gap: 6px; }
.tc-meta-item { font-size: 13px; color: #666; display: flex; align-items: center; gap: 6px; }
.tc-footer { padding: 10px 16px; background: #fafafa; border-top: 1px solid #f0f0f0; display: flex; gap: 8px; }
</style>
