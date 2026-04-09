<template>
  <DarkPageHeader
    title="我的班级"
    search-placeholder="搜索班级名称"
    v-model="searchText"
    @search="onFilterChange"
  >
    <template #filters>
      <button type="button" class="dark-chip" :class="{ active: filterStatus.length === 0 }" @click="setStatus([])">全部</button>
      <button v-for="s in statusOptions" :key="s.value" type="button" class="dark-chip" :class="{ active: filterStatus.length === 1 && filterStatus[0] === s.value }" @click="setStatus([s.value])">{{ s.label }}</button>
      <span class="filter-spacer" />
      <button type="button" class="dark-chip scope-chip" :class="{ active: filterScope === 'mine' }" @click="setScope('mine')">我的培训班</button>
      <button type="button" class="dark-chip scope-chip" :class="{ active: filterScope === 'enrollable' }" @click="setScope('enrollable')">可报名培训班</button>
    </template>
    <template #actions>
      <a-select v-if="typeOptions.length" v-model:value="filterType" placeholder="全部类型" style="width: 140px" allow-clear popup-class-name="dark-select-popup" @change="onFilterChange">
        <a-select-option value="">全部类型</a-select-option>
        <a-select-option v-for="t in typeOptions" :key="t.value" :value="t.value">{{ t.label }}</a-select-option>
      </a-select>
    </template>

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
        <!-- 封面区 -->
        <div class="card-cover" :style="{ background: coverColors[index % coverColors.length] }">
          <!-- 线框图标 -->
          <svg class="cover-icon" viewBox="0 0 48 48" fill="none" stroke="rgba(255,255,255,0.55)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="6" y="10" width="36" height="28" rx="3" />
            <path d="M24 10V6" />
            <path d="M16 10V7" />
            <path d="M32 10V7" />
            <line x1="6" y1="18" x2="42" y2="18" />
            <circle cx="16" cy="26" r="2.5" />
            <circle cx="24" cy="26" r="2.5" />
            <circle cx="32" cy="26" r="2.5" />
            <line x1="16" y1="33" x2="16" y2="28.5" stroke-dasharray="1.5 1.5" />
            <line x1="24" y1="33" x2="24" y2="28.5" stroke-dasharray="1.5 1.5" />
            <line x1="32" y1="33" x2="32" y2="28.5" stroke-dasharray="1.5 1.5" />
          </svg>

          <!-- 状态标签（柔和底色） -->
          <span v-if="item.status" class="status-tag" :class="'status-' + item.status">
            {{ statusLabels[item.status] || item.status }}
          </span>
          <!-- 类型标签 -->
          <span v-if="item.type" class="type-tag">
            {{ item.training_type_name || typeLabels[item.type] || item.type }}
          </span>
        </div>

        <!-- 信息区 -->
        <div class="card-body">
          <h3 class="card-title">{{ item.name }}</h3>

          <div class="card-detail-row">
            <CalendarOutlined class="detail-icon" />
            <span>{{ formatDate(item.start_date) }} ~ {{ formatDate(item.end_date) }}</span>
          </div>

          <div class="card-detail-row">
            <UserOutlined class="detail-icon" />
            <span>{{ item.instructor_name || '未指定教官' }}</span>
            <span class="detail-sep">·</span>
            <TeamOutlined class="detail-icon" />
            <span>{{ item.enrolled_count ?? 0 }}{{ item.capacity ? '/' + item.capacity : '' }} 人</span>
          </div>

          <div v-if="item.location" class="card-detail-row">
            <EnvironmentOutlined class="detail-icon" />
            <span>{{ item.location }}</span>
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
  </DarkPageHeader>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  TeamOutlined,
  CalendarOutlined,
  UserOutlined,
  EnvironmentOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import axiosInstance from '@/api/custom-instance'
import DarkPageHeader from '@/components/common/DarkPageHeader.vue'

const router = useRouter()

const filterStatus = ref<string[]>(['upcoming', 'active'])
const filterType = ref('')
const filterScope = ref('mine')
const searchText = ref('')
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const loading = ref(false)

interface ClassItem {
  id: number
  name: string
  type: string
  training_type_name: string | null
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

interface TrainingTypeItem {
  id: number
  name: string
  code: string
}

const trainingTypeList = ref<TrainingTypeItem[]>([])

const typeOptions = computed(() =>
  trainingTypeList.value.map((t) => ({ value: t.code, label: t.name })),
)

const statusLabels: Record<string, string> = {
  upcoming: '未开始',
  active: '进行中',
  ended: '已结束',
}

const typeLabels = computed<Record<string, string>>(() => {
  const map: Record<string, string> = {}
  for (const t of trainingTypeList.value) {
    map[t.code] = t.name
  }
  return map
})

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

function setStatus(values: string[]) {
  filterStatus.value = values
  onFilterChange()
}

function setScope(value: string) {
  filterScope.value = filterScope.value === value ? '' : value
  onFilterChange()
}

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
    if (filterScope.value) {
      params.scope = filterScope.value
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

async function fetchTrainingTypes() {
  try {
    const res = await axiosInstance.get('/training-types', { params: { size: -1, is_active: true } })
    const data = res.data as { items: TrainingTypeItem[] }
    trainingTypeList.value = data.items || []
  } catch {
    trainingTypeList.value = []
  }
}

onMounted(() => {
  fetchTrainingTypes()
  fetchList()
})
</script>

<style scoped>
/* -- actions 区深色下拉适配 -- */
:deep(.ant-select:not(.ant-select-customize-input) .ant-select-selector) {
  background: rgba(255,255,255,0.08) !important;
  border-color: rgba(255,255,255,0.18) !important;
  color: rgba(255,255,255,0.88) !important;
  border-radius: 20px !important;
}
:deep(.ant-select-arrow) { color: rgba(255,255,255,0.58) !important; }
:deep(.ant-select-selection-placeholder) { color: rgba(255,255,255,0.50) !important; }
:deep(.ant-select-clear) { background: transparent !important; color: rgba(255,255,255,0.58) !important; }

/* -- 筛选间隔 -- */
.filter-spacer {
  flex: 1;
  min-width: 12px;
}

/* -- 加载 -- */
.loading-wrapper {
  display: flex;
  justify-content: center;
  padding: 80px 0;
}

/* -- 网格 -- */
.class-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

@media (min-width: 1100px) {
  .class-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1500px) {
  .class-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 768px) {
  .class-grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  /* 移动端：标题 → 搜索 → 类型筛选（覆盖 DarkPageHeader 默认的 leading+actions 同行） */
  :deep(.dark-header-main) {
    grid-template-columns: 1fr !important;
    grid-template-areas:
      'leading'
      'search'
      'actions' !important;
  }

  :deep(.dark-header-actions) {
    justify-self: start;
  }

  .filter-spacer {
    flex-basis: 100%;
    min-width: 0;
  }
}

/* -- 卡片 -- */
.class-card {
  background: var(--v2-bg-card);
  border-radius: var(--v2-radius);
  overflow: hidden;
  cursor: pointer;
  transition: box-shadow 0.25s, transform 0.25s;
}

.class-card:hover {
  box-shadow: var(--v2-shadow-lg);
  transform: translateY(-3px);
}

/* -- 封面区 -- */
.card-cover {
  height: 150px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-icon {
  width: 56px;
  height: 56px;
}

/* -- 状态标签：白色半透明底 -- */
.status-tag {
  position: absolute;
  left: 10px;
  bottom: 10px;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: var(--v2-radius-xs);
  font-weight: 500;
  letter-spacing: 0.2px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(4px);
}

.status-upcoming {
  color: var(--v2-text-secondary);
}
.status-active {
  color: var(--v2-text-secondary);
}
.status-ended {
  color: var(--v2-text-muted);
}

.type-tag {
  position: absolute;
  right: 10px;
  top: 10px;
  background: rgba(255, 255, 255, 0.72);
  color: var(--v2-text-secondary);
  font-size: 12px;
  padding: 3px 10px;
  border-radius: var(--v2-radius-xs);
  backdrop-filter: blur(4px);
}

/* -- 信息区 -- */
.card-body {
  padding: 18px 20px 20px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.card-detail-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--v2-text-muted);
  line-height: 1;
  margin-bottom: 8px;
}

.card-detail-row:last-child {
  margin-bottom: 0;
}

.detail-icon {
  font-size: 13px;
  color: var(--v2-text-muted);
  flex-shrink: 0;
}

.detail-sep {
  margin: 0 2px;
  color: var(--v2-border);
}

/* -- 分页 -- */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 28px 0;
}
</style>
