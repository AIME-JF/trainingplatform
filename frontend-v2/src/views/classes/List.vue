<template>
  <div class="page-content">
    <h1 class="page-title">我的班级</h1>

    <!-- 筛选栏 -->
    <div class="toolbar">
      <div class="toolbar-filters">
        <a-select
          v-model:value="filterStatus"
          mode="multiple"
          placeholder="班级状态"
          style="min-width: 180px"
          allow-clear
          :max-tag-count="1"
          @change="onFilterChange"
        >
          <a-select-option v-for="s in statusOptions" :key="s.value" :value="s.value">
            {{ s.label }}
          </a-select-option>
        </a-select>

        <a-select
          v-model:value="filterType"
          placeholder="全部类型"
          style="width: 140px"
          allow-clear
          @change="onFilterChange"
        >
          <a-select-option value="">全部类型</a-select-option>
          <a-select-option v-for="t in typeOptions" :key="t.value" :value="t.value">
            {{ t.label }}
          </a-select-option>
        </a-select>
      </div>

      <a-input-search
        v-model:value="searchText"
        placeholder="搜索班级名称"
        style="width: 220px"
        allow-clear
        @search="onFilterChange"
      />
    </div>

    <!-- 加载 -->
    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" />
    </div>

    <!-- 空状态 -->
    <a-empty v-else-if="!list.length" description="暂无班级" style="padding: 80px 0" />

    <!-- 班级卡片网格 -->
    <div v-else class="class-grid">
      <div
        v-for="(item, index) in list"
        :key="item.id"
        class="class-card"
        @click="goDetail(item.id)"
      >
        <!-- 封面 -->
        <div class="card-cover" :style="{ background: coverColors[index % coverColors.length] }">
          <div class="cover-icon">
            <TeamOutlined />
          </div>
          <span v-if="item.status" class="status-tag" :class="'status-' + item.status">
            {{ statusLabels[item.status] || item.status }}
          </span>
          <span v-if="item.type" class="type-tag">
            {{ typeLabels[item.type] || item.type }}
          </span>
        </div>

        <!-- 信息 -->
        <div class="card-body">
          <h3 class="card-title">{{ item.name }}</h3>
          <div class="card-info">
            <span class="info-item">
              <CalendarOutlined />
              {{ formatDate(item.start_date) }} ~ {{ formatDate(item.end_date) }}
            </span>
          </div>
          <div class="card-meta">
            <span class="meta-item">
              <UserOutlined />
              {{ item.instructor_name || '未指定' }}
            </span>
            <span class="meta-item">
              <TeamOutlined />
              {{ item.enrolled_count ?? 0 }}{{ item.capacity ? '/' + item.capacity : '' }} 人
            </span>
          </div>
          <div v-if="item.location" class="card-location">
            <EnvironmentOutlined />
            {{ item.location }}
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination-wrapper">
      <a-pagination
        v-model:current="page"
        :total="total"
        :page-size="pageSize"
        show-size-changer
        :page-size-options="['12', '24', '48']"
        @change="fetchList"
        @showSizeChange="onPageSizeChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  TeamOutlined,
  CalendarOutlined,
  UserOutlined,
  EnvironmentOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import axiosInstance from '@/api/custom-instance'

const router = useRouter()

const filterStatus = ref<string[]>(['upcoming', 'active'])
const filterType = ref('')
const searchText = ref('')
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const loading = ref(false)

interface ClassItem {
  id: number
  name: string
  type: string
  status: string
  start_date: string
  end_date: string
  location: string
  capacity: number | null
  enrolled_count: number
  instructor_name: string
}

const list = ref<ClassItem[]>([])

const statusOptions = [
  { value: 'upcoming', label: '未开始' },
  { value: 'active', label: '进行中' },
  { value: 'ended', label: '已结束' },
]

const typeOptions = [
  { value: 'basic', label: '基础训练' },
  { value: 'special', label: '专项训练' },
  { value: 'promotion', label: '晋升培训' },
  { value: 'online', label: '线上培训' },
]

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

const coverColors = [
  'var(--v2-cover-blue)',
  'var(--v2-cover-green)',
  'var(--v2-cover-purple)',
  'var(--v2-cover-orange)',
  'var(--v2-cover-teal)',
  'var(--v2-cover-pink)',
  'var(--v2-cover-yellow)',
  'var(--v2-cover-rose)',
]

function onFilterChange() {
  page.value = 1
  fetchList()
}

async function fetchList() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: page.value,
      size: pageSize.value,
    }
    if (filterStatus.value.length) {
      params.status = filterStatus.value.join(',')
    }
    if (filterType.value) {
      params.type = filterType.value
    }
    if (searchText.value.trim()) {
      params.search = searchText.value.trim()
    }

    const res = await axiosInstance.get('/trainings', { params })
    const data = res.data as { items: ClassItem[]; total: number }
    list.value = data.items || []
    total.value = data.total || 0
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '加载班级列表失败')
  } finally {
    loading.value = false
  }
}

function onPageSizeChange(_current: number, size: number) {
  pageSize.value = size
  page.value = 1
  fetchList()
}

function goDetail(id: number) {
  router.push(`/classes/${id}`)
}

function formatDate(val: string | null | undefined): string {
  if (!val) return '-'
  return val.slice(0, 10)
}

onMounted(fetchList)
</script>

<style scoped>
.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--v2-text-primary);
  margin-bottom: 20px;
}

/* -- 工具栏 -- */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* -- 加载 -- */
.loading-wrapper {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

/* -- 班级网格 -- */
.class-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

@media (min-width: 1200px) {
  .class-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 768px) {
  .class-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}

/* -- 班级卡片 -- */
.class-card {
  background: var(--v2-bg-card);
  border-radius: var(--v2-radius);
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.2s, transform 0.2s;
}

.class-card:hover {
  box-shadow: var(--v2-shadow-lg);
  transform: translateY(-2px);
}

/* -- 封面 -- */
.card-cover {
  height: 110px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-icon {
  font-size: 44px;
  color: rgba(255, 255, 255, 0.65);
}

.status-tag {
  position: absolute;
  left: 10px;
  bottom: 10px;
  font-size: 11px;
  padding: 2px 10px;
  border-radius: var(--v2-radius-full);
  color: #fff;
  font-weight: 500;
}

.status-upcoming { background: var(--v2-primary); }
.status-active   { background: var(--v2-success); }
.status-ended    { background: var(--v2-text-muted); }

.type-tag {
  position: absolute;
  right: 10px;
  top: 10px;
  background: rgba(255, 255, 255, 0.88);
  color: var(--v2-text-secondary);
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--v2-radius-xs);
}

/* -- 卡片信息 -- */
.card-body {
  padding: 14px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-info {
  margin-bottom: 6px;
}

.card-info .info-item {
  font-size: 12px;
  color: var(--v2-text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 4px;
}

.meta-item {
  font-size: 12px;
  color: var(--v2-text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-location {
  font-size: 12px;
  color: var(--v2-text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
}

/* -- 分页 -- */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 24px 0;
}
</style>
