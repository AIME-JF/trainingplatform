<template>
  <div class="instructor-list-page">
    <div class="page-header">
      <h2>教官库</h2>
    </div>

    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-row :gutter="16" align="middle">
        <a-col :span="6">
          <a-input-search v-model:value="searchText" placeholder="搜索教官姓名/用户名..." allow-clear @search="loadInstructors" />
        </a-col>
        <a-col :span="5">
          <a-select v-model:value="filterAdminLevel" placeholder="行政级别" allow-clear style="width:100%" @change="loadInstructors">
            <a-select-option value="县级">县级</a-select-option>
            <a-select-option value="市级">市级</a-select-option>
            <a-select-option value="厅级">厅级</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="5">
          <a-select v-model:value="filterProfessionalLevel" placeholder="专业等级" allow-clear style="width:100%" @change="loadInstructors">
            <a-select-option value="初级">初级教官</a-select-option>
            <a-select-option value="中级">中级教官</a-select-option>
            <a-select-option value="高级">高级教官</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="5">
          <a-select
            v-model:value="filterSpecialtyId"
            placeholder="专长方向"
            allow-clear
            show-search
            option-filter-prop="label"
            style="width:100%"
            @change="loadInstructors"
          >
            <a-select-option v-for="s in specialtyOptions" :key="s.id" :value="s.id" :label="s.name">
              {{ s.name }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="3">
          <a-button @click="resetFilters">重置</a-button>
        </a-col>
      </a-row>
    </a-card>

    <a-spin :spinning="loading">
      <div class="instructor-grid" v-if="instructorList.length > 0">
        <div v-for="inst in instructorList" :key="inst.id" class="inst-card" @click="goDetail(inst)">
          <div class="inst-avatar-wrap">
            <a-avatar :size="72" :style="{ background: inst.avatarColor, fontSize: '28px' }">
              {{ (inst.name || '').charAt(0) }}
            </a-avatar>
            <div class="inst-badge" :class="inst.levelClass">{{ inst.levelLabel }}</div>
          </div>

          <div class="inst-name">{{ inst.name }}</div>
          <div class="inst-title">{{ inst.title }}</div>
          <div class="inst-unit">{{ inst.unit }}</div>

          <div class="inst-tags" v-if="inst.instructorTags && inst.instructorTags.length">
            <div v-for="tag in inst.instructorTags.slice(0, 2)" :key="tag.id" class="inst-tag-row">
              <a-tag size="small" color="blue">{{ tag.adminLevel }}</a-tag>
              <a-tag size="small" color="gold">{{ tag.professionalLevel }}</a-tag>
              <a-tag size="small" color="green">{{ tag.specialtyName }}</a-tag>
            </div>
          </div>
          <div v-else class="inst-tags"><span style="color: #999; font-size: 12px">未设置标签</span></div>

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

          <div v-if="canEditInstructor" class="inst-card-actions" @click.stop>
            <a-button type="link" size="small" @click="openEditModal(inst)">编辑教官信息</a-button>
          </div>
        </div>
      </div>
      <a-empty v-else description="暂无教官数据" style="margin-top: 60px" />
    </a-spin>

    <InstructorEditModal
      v-model:open="editDialog.open"
      :user="editDialog.user"
      :submitting="editDialog.submitting"
      @submit="handleEditSubmit"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import { getUsers, updateUser } from '@/api/user'
import request from '@/api/request'
import InstructorEditModal from './components/InstructorEditModal.vue'

const router = useRouter()
const authStore = useAuthStore()
const searchText = ref('')
const filterAdminLevel = ref(undefined)
const filterProfessionalLevel = ref(undefined)
const filterSpecialtyId = ref(undefined)
const specialtyOptions = ref([])
const loading = ref(false)
const instructorList = ref([])
const canEditInstructor = computed(() => authStore.hasPermission('UPDATE_USER'))
const editDialog = ref({
  open: false,
  submitting: false,
  user: null,
})

const avatarColors = ['#003087', '#c8a84b', '#8B1A1A', '#1a5c2e', '#6b3a8a', '#2e86de']
function getAvatarColor(id) {
  return avatarColors[(id || 0) % avatarColors.length]
}

function getLevelFromTags(tags) {
  if (!tags || !tags.length) return { levelClass: 'standard', levelLabel: '教官' }
  if (tags.some((t) => t.professionalLevel === '高级')) return { levelClass: 'expert', levelLabel: '高级' }
  if (tags.some((t) => t.professionalLevel === '中级')) return { levelClass: 'senior', levelLabel: '中级' }
  return { levelClass: 'standard', levelLabel: '初级' }
}

async function fetchSpecialties() {
  try {
    specialtyOptions.value = await request.get('/dict/instructor-specialties', { params: { enabled: true } }) || []
  } catch {
    specialtyOptions.value = []
  }
}

async function loadInstructors() {
  loading.value = true
  try {
    const params = { role: 'instructor', size: -1, search: searchText.value || undefined }
    if (filterAdminLevel.value) params.adminLevel = filterAdminLevel.value
    if (filterProfessionalLevel.value) params.professionalLevel = filterProfessionalLevel.value
    if (filterSpecialtyId.value) params.specialtyId = filterSpecialtyId.value
    const res = await getUsers(params)
    const items = res.items || []
    instructorList.value = items.map((u) => {
      const { levelClass, levelLabel } = getLevelFromTags(u.instructorTags)
      return {
        ...u,
        id: u.id,
        name: u.nickname || u.username,
        title: u.instructorTitle || '教官',
        unit: (u.departments && u.departments.length > 0) ? u.departments[0].name : '未分配',
        instructorTags: u.instructorTags || [],
        avatarColor: getAvatarColor(u.id),
        levelClass,
        levelLabel,
      }
    })
  } catch {
    instructorList.value = []
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  searchText.value = ''
  filterAdminLevel.value = undefined
  filterProfessionalLevel.value = undefined
  filterSpecialtyId.value = undefined
  loadInstructors()
}

onMounted(() => {
  fetchSpecialties()
  loadInstructors()
})

let searchTimer = null
watch(searchText, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => loadInstructors(), 300)
})

function goDetail(inst) {
  router.push({ name: 'InstructorDetail', params: { id: inst.id } })
}

function openEditModal(inst) {
  if (!canEditInstructor.value) return
  editDialog.value = {
    open: true,
    submitting: false,
    user: { ...inst },
  }
}

async function handleEditSubmit(payload) {
  const userId = editDialog.value.user?.id
  if (!userId) return
  editDialog.value = { ...editDialog.value, submitting: true }
  try {
    const { tags, ...userPayload } = payload
    await updateUser(userId, userPayload)

    if (tags !== undefined) {
      const existingTags = await request.get(`/instructors/${userId}/tags`) || []
      for (const existing of existingTags) {
        const stillExists = tags.some((t) =>
          t.adminLevel === existing.adminLevel
          && t.professionalLevel === existing.professionalLevel
          && t.specialtyId === existing.specialtyId
        )
        if (!stillExists) {
          await request.delete(`/instructors/${userId}/tags/${existing.id}`)
        }
      }
      for (const tag of tags) {
        const alreadyExists = existingTags.some((e) =>
          e.adminLevel === tag.adminLevel
          && e.professionalLevel === tag.professionalLevel
          && e.specialtyId === tag.specialtyId
        )
        if (!alreadyExists) {
          await request.post(`/instructors/${userId}/tags`, tag)
        }
      }
    }

    message.success('教官信息已更新')
    editDialog.value = { open: false, submitting: false, user: null }
    await loadInstructors()
  } catch (error) {
    editDialog.value = { ...editDialog.value, submitting: false }
    message.error(error.message || '教官信息更新失败')
  }
}
</script>

<style scoped>
.instructor-list-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
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
.inst-tags { display: flex; flex-direction: column; align-items: center; gap: 4px; margin-bottom: 16px; min-height: 24px; }
.inst-tag-row { display: flex; gap: 2px; }
.inst-stats { display: flex; align-items: center; justify-content: space-around; padding: 12px 0 0; border-top: 1px solid #f0f0f0; }
.is-item { text-align: center; }
.is-num { font-size: 20px; font-weight: 700; color: #1a1a1a; }
.is-label { font-size: 11px; color: #888; }
.is-divider { width: 1px; height: 30px; background: #f0f0f0; }
.inst-card-actions { margin-top: 12px; padding-top: 8px; border-top: 1px solid #f0f0f0; text-align: right; }
</style>
