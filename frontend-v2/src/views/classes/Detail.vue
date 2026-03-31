<template>
  <div class="detail-page">
    <!-- 深色头部横幅 -->
    <header class="detail-header">
      <div class="header-content">
        <div class="header-main">
          <h1 class="header-title">{{ detail?.name || '班级详情' }}</h1>
          <div class="header-meta">
            <span v-if="detail?.type" class="meta-badge">{{ typeLabels[detail.type] || detail.type }}</span>
            <span v-if="detail?.status" class="meta-badge" :class="'badge-' + detail.status">{{ statusLabels[detail.status] || detail.status }}</span>
            <span class="meta-item"><UserOutlined /> {{ detail?.instructor_name || '未指定' }}</span>
            <span class="meta-item"><EnvironmentOutlined /> {{ detail?.location || '未指定' }}</span>
          </div>
        </div>
        <div class="header-stats">
          <span>{{ formatDate(detail?.start_date) }} ~ {{ formatDate(detail?.end_date) }}</span>
          <span>{{ detail?.enrolled_count ?? 0 }}{{ detail?.capacity ? '/' + detail.capacity : '' }} 人</span>
        </div>
      </div>
    </header>

    <section class="page-content">
      <a-spin v-if="loading" size="large" style="display: block; text-align: center; padding: 80px 0" />
      <a-empty v-else-if="!detail" description="班级不存在" style="padding: 80px 0" />
      <div v-else>
        <a-card title="班级信息" :bordered="false" style="margin-bottom: 16px">
          <a-descriptions :column="{ xs: 1, sm: 2 }" size="small">
            <a-descriptions-item label="班级名称">{{ detail.name }}</a-descriptions-item>
            <a-descriptions-item label="类型">{{ typeLabels[detail.type] || detail.type || '-' }}</a-descriptions-item>
            <a-descriptions-item label="状态">{{ statusLabels[detail.status] || detail.status || '-' }}</a-descriptions-item>
            <a-descriptions-item label="教官">{{ detail.instructor_name || '-' }}</a-descriptions-item>
            <a-descriptions-item label="培训周期">{{ formatDate(detail.start_date) }} ~ {{ formatDate(detail.end_date) }}</a-descriptions-item>
            <a-descriptions-item label="地点">{{ detail.location || '-' }}</a-descriptions-item>
            <a-descriptions-item label="人数">{{ detail.enrolled_count ?? 0 }}{{ detail.capacity ? ' / ' + detail.capacity : '' }}</a-descriptions-item>
            <a-descriptions-item label="所属部门">{{ detail.department_name || '-' }}</a-descriptions-item>
          </a-descriptions>
        </a-card>

        <a-card v-if="detail.description" title="班级描述" :bordered="false">
          <p style="white-space: pre-wrap; color: var(--v2-text-secondary)">{{ detail.description }}</p>
        </a-card>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { UserOutlined, EnvironmentOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import axiosInstance from '@/api/custom-instance'

const route = useRoute()
const loading = ref(false)

interface ClassDetail {
  id: number
  name: string
  type: string
  status: string
  description: string
  start_date: string
  end_date: string
  location: string
  capacity: number | null
  enrolled_count: number
  instructor_name: string
  department_name: string
}

const detail = ref<ClassDetail | null>(null)

const statusLabels: Record<string, string> = {
  upcoming: '未开始',
  active: '进行中',
  ended: '已结束',
}

const typeLabels: Record<string, string> = {
  basic: '基础训练',
  special: '专项训练',
  promotion: '晋升培训',
  online: '线上培训',
}

function formatDate(val: string | null | undefined): string {
  if (!val) return '-'
  return val.slice(0, 10)
}

async function fetchDetail() {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    const res = await axiosInstance.get(`/trainings/${id}`)
    detail.value = res.data as ClassDetail
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '加载班级详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(fetchDetail)
</script>

<style scoped>
.detail-header {
  background: var(--v2-bg-header);
  padding: 32px;
}

@media (max-width: 768px) {
  .detail-header {
    padding: 20px 16px;
  }
}

.header-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--v2-text-white);
  margin-bottom: 12px;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.meta-badge {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: var(--v2-radius-full);
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.badge-active { background: var(--v2-success); }
.badge-upcoming { background: var(--v2-primary); }
.badge-ended { background: rgba(255, 255, 255, 0.25); }

.meta-item {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.header-stats {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
}
</style>
