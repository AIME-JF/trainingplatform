<template>
  <div class="instructor-list-page">
    <div class="page-header">
      <h2>教官库</h2>
    </div>

    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input-search v-model:value="searchText" placeholder="搜索教官姓名/用户名..." allow-clear @search="loadInstructors" />
        </a-col>
        <a-col :span="16">
          <div class="specialty-filter">
            <span style="color: #888; white-space: nowrap">警种：</span>
            <div class="specialty-tags">
              <a-tag
                v-for="s in specialtiesList"
                :key="s"
                :color="filterSpecialty === s ? 'blue' : 'default'"
                class="filter-tag"
                @click="filterSpecialty = s"
              >
                {{ s }}
              </a-tag>
            </div>
          </div>
        </a-col>
      </a-row>
    </a-card>

    <a-spin :spinning="loading">
      <div class="instructor-grid" v-if="filteredInstructors.length > 0">
        <div v-for="inst in filteredInstructors" :key="inst.id" class="inst-card" @click="goDetail(inst)">
          <div class="inst-avatar-wrap">
            <a-avatar :size="72" :style="{ background: inst.avatarColor, fontSize: '28px' }">
              {{ (inst.name || '').charAt(0) }}
            </a-avatar>
            <div class="inst-badge" :class="inst.levelClass">{{ inst.levelLabel }}</div>
          </div>

          <div class="inst-name">{{ inst.name }}</div>
          <div class="inst-title">{{ inst.title }}</div>
          <div class="inst-unit">{{ inst.unit }}</div>

          <div class="inst-specialties">
            <a-tag v-for="s in inst.specialties.slice(0, 2)" :key="s" size="small">{{ s }}</a-tag>
            <span v-if="inst.specialties.length === 0" style="color: #999; font-size: 12px">未设置</span>
          </div>

          <div class="inst-stats">
            <div class="is-item">
              <div class="is-num">{{ inst.examCount || 0 }}</div>
              <div class="is-label">考试数</div>
            </div>
            <div class="is-divider"></div>
            <div class="is-item">
              <div class="is-num">{{ Math.round(inst.studyHours || 0) }}</div>
              <div class="is-label">学习时长</div>
            </div>
            <div class="is-divider"></div>
            <div class="is-item">
              <div class="is-num" style="color: #faad14">{{ inst.avgScore || 0 }}</div>
              <div class="is-label">平均分</div>
            </div>
          </div>
        </div>
      </div>
      <a-empty v-else description="暂无教官数据" style="margin-top: 60px" />
    </a-spin>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getUsers } from '@/api/user'

const router = useRouter()
const searchText = ref('')
const filterSpecialty = ref('全部')
const loading = ref(false)
const instructorList = ref([])

const avatarColors = ['#003087', '#c8a84b', '#8B1A1A', '#1a5c2e', '#6b3a8a', '#2e86de']
function getAvatarColor(id) {
  return avatarColors[(id || 0) % avatarColors.length]
}

function getLevelClass(level) {
  if (!level) return 'standard'
  if (level.includes('高级') || level.includes('专家')) return 'expert'
  if (level.includes('中级')) return 'senior'
  return 'standard'
}

function getLevelLabel(level) {
  if (!level) return '教官'
  if (level.includes('高级') || level.includes('专家')) return '专家'
  if (level.includes('中级')) return '资深'
  return '教官'
}

async function loadInstructors() {
  loading.value = true
  try {
    const res = await getUsers({ role: 'instructor', size: -1, search: searchText.value || undefined })
    const items = res.items || []
    instructorList.value = items.map((u) => ({
      ...u,
      id: u.id,
      userId: u.id,
      name: u.nickname || u.username,
      title: u.instructorTitle || u.level || '教官',
      unit: (u.departments && u.departments.length > 0) ? u.departments[0].name : '未分配',
      specialties: (u.instructorSpecialties && u.instructorSpecialties.length > 0)
        ? u.instructorSpecialties
        : (u.policeTypes || []).map((p) => p.name).filter(Boolean),
      avatarColor: getAvatarColor(u.id),
      levelClass: getLevelClass(u.instructorLevel || u.level),
      levelLabel: getLevelLabel(u.instructorLevel || u.level),
    }))
  } catch {
    instructorList.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadInstructors)

let searchTimer = null
watch(searchText, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadInstructors(), 300)
})

const specialtiesList = computed(() => {
  const all = new Set()
  instructorList.value.forEach((i) => (i.specialties || []).forEach((s) => all.add(s)))
  return ['全部', ...all]
})

const filteredInstructors = computed(() => {
  let list = [...instructorList.value]
  if (filterSpecialty.value !== '全部') {
    list = list.filter((i) => (i.specialties || []).includes(filterSpecialty.value))
  }
  return list
})

function goDetail(inst) {
  router.push({ name: 'InstructorDetail', params: { id: inst.id } })
}
</script>

<style scoped>
.instructor-list-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.filter-tag { cursor: pointer; }
.specialty-filter { display: flex; align-items: flex-start; gap: 8px; }
.specialty-tags { display: flex; flex-wrap: wrap; gap: 4px 0; }
.instructor-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.inst-card { background: #fff; border-radius: 12px; border: 1px solid #e8e8e8; padding: 24px; text-align: center; cursor: pointer; transition: all 0.25s; }
.inst-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0, 48, 135, 0.12); border-color: var(--police-primary); }
.inst-avatar-wrap { position: relative; display: inline-block; margin-bottom: 12px; }
.inst-badge { position: absolute; bottom: 0; right: -4px; font-size: 10px; padding: 1px 6px; border-radius: 10px; font-weight: 700; }
.inst-badge.senior { background: #c8a84b; color: #fff; }
.inst-badge.expert { background: #003087; color: #fff; }
.inst-badge.standard { background: #888; color: #fff; }
.inst-name { font-size: 18px; font-weight: 700; color: #1a1a1a; }
.inst-title { font-size: 13px; color: var(--police-primary); margin: 4px 0; }
.inst-unit { font-size: 12px; color: #888; margin-bottom: 12px; }
.inst-specialties { display: flex; justify-content: center; gap: 4px; flex-wrap: wrap; margin-bottom: 16px; min-height: 24px; }
.inst-stats { display: flex; align-items: center; justify-content: space-around; padding: 12px 0 0; border-top: 1px solid #f0f0f0; }
.is-item { text-align: center; }
.is-num { font-size: 20px; font-weight: 700; color: #1a1a1a; }
.is-label { font-size: 11px; color: #888; }
.is-divider { width: 1px; height: 30px; background: #f0f0f0; }
</style>
