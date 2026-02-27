<template>
  <div class="instructor-list-page">
    <div class="page-header">
      <h2>教官库</h2>
      <a-button type="primary" v-if="authStore.isAdmin">
        <template #icon><PlusOutlined /></template>添加教官
      </a-button>
    </div>

    <a-card :bordered="false" style="margin-bottom:16px">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input-search v-model:value="searchText" placeholder="搜索教官姓名、专业领域..." allow-clear />
        </a-col>
        <a-col :span="16">
          <a-space>
            <span style="color:#888">专业方向：</span>
            <a-tag v-for="s in specialties" :key="s" :color="filterSpecialty === s ? 'blue' : 'default'" class="filter-tag" @click="filterSpecialty = s">{{ s }}</a-tag>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <div class="instructor-grid">
      <div v-for="inst in filteredInstructors" :key="inst.id" class="inst-card" @click="goDetail(inst)">
        <div class="inst-avatar-wrap">
          <a-avatar :size="72" :style="{ background: inst.avatarColor, fontSize: '28px' }">
            {{ inst.name.charAt(0) }}
          </a-avatar>
          <div class="inst-badge" :class="inst.level">{{ inst.levelLabel }}</div>
        </div>
        <div class="inst-name">{{ inst.name }}</div>
        <div class="inst-title">{{ inst.title }}</div>
        <div class="inst-unit">{{ inst.unit }}</div>

        <div class="inst-specialties">
          <a-tag v-for="s in inst.specialties.slice(0,2)" :key="s" size="small">{{ s }}</a-tag>
        </div>

        <div class="inst-stats">
          <div class="is-item">
            <div class="is-num">{{ inst.courseCount }}</div>
            <div class="is-label">课程数</div>
          </div>
          <div class="is-divider"></div>
          <div class="is-item">
            <div class="is-num">{{ inst.studentCount }}</div>
            <div class="is-label">培训人次</div>
          </div>
          <div class="is-divider"></div>
          <div class="is-item">
            <div class="is-num" style="color:#faad14">{{ inst.rating }}</div>
            <div class="is-label">评分</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { MOCK_INSTRUCTORS } from '@/mock/instructors'

const router = useRouter()
const authStore = useAuthStore()
const searchText = ref('')
const filterSpecialty = ref('全部')

const allSpecialties = new Set()
MOCK_INSTRUCTORS.forEach(i => i.specialties.forEach(s => allSpecialties.add(s)))
const specialties = ['全部', ...allSpecialties]

const filteredInstructors = computed(() => {
  let list = [...MOCK_INSTRUCTORS]
  if (searchText.value) list = list.filter(i => i.name.includes(searchText.value) || i.specialties.some(s => s.includes(searchText.value)))
  if (filterSpecialty.value !== '全部') list = list.filter(i => i.specialties.includes(filterSpecialty.value))
  return list
})

const goDetail = (inst) => router.push({ name: 'InstructorDetail', params: { id: inst.id } })
</script>

<style scoped>
.instructor-list-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.filter-tag { cursor: pointer; }
.instructor-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.inst-card { background: #fff; border-radius: 12px; border: 1px solid #e8e8e8; padding: 24px; text-align: center; cursor: pointer; transition: all 0.25s; }
.inst-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,48,135,0.12); border-color: var(--police-primary); }
.inst-avatar-wrap { position: relative; display: inline-block; margin-bottom: 12px; }
.inst-badge { position: absolute; bottom: 0; right: -4px; font-size: 10px; padding: 1px 6px; border-radius: 10px; font-weight: 700; }
.inst-badge.senior { background: #c8a84b; color: #fff; }
.inst-badge.expert { background: #003087; color: #fff; }
.inst-badge.standard { background: #888; color: #fff; }
.inst-name { font-size: 18px; font-weight: 700; color: #1a1a1a; }
.inst-title { font-size: 13px; color: var(--police-primary); margin: 4px 0; }
.inst-unit { font-size: 12px; color: #888; margin-bottom: 12px; }
.inst-specialties { display: flex; justify-content: center; gap: 4px; flex-wrap: wrap; margin-bottom: 16px; }
.inst-stats { display: flex; align-items: center; justify-content: space-around; padding: 12px 0 0; border-top: 1px solid #f0f0f0; }
.is-item { text-align: center; }
.is-num { font-size: 20px; font-weight: 700; color: #1a1a1a; }
.is-label { font-size: 11px; color: #888; }
.is-divider { width: 1px; height: 30px; background: #f0f0f0; }
</style>
