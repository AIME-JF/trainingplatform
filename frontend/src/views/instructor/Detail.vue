<template>
  <div class="instructor-detail-page">
    <a-breadcrumb style="margin-bottom: 16px">
      <a-breadcrumb-item @click="$router.push('/instructor')" style="cursor: pointer; color: var(--police-primary)">教官库</a-breadcrumb-item>
      <a-breadcrumb-item>{{ instructor.name || '教官详情' }}</a-breadcrumb-item>
    </a-breadcrumb>

    <a-spin :spinning="loading">
      <a-row :gutter="20">
        <!-- 左：教官信息卡 -->
        <a-col :span="8">
          <a-card :bordered="false" class="profile-card">
            <div class="profile-top">
              <a-avatar :size="96" :style="{ background: avatarColor, fontSize: '36px' }">
                {{ (instructor.name || '').charAt(0) }}
              </a-avatar>
              <div class="inst-badge-large" :class="levelClass">{{ levelLabel }}</div>
            </div>
            <div class="profile-name">{{ instructor.name }}</div>
            <div class="profile-title">{{ instructor.title }}</div>
            <div class="profile-unit">{{ instructor.unit }}</div>

            <div v-if="canEditInstructor" class="profile-actions">
              <a-button type="primary" ghost size="small" @click="openEditModal">编辑教官信息</a-button>
            </div>

            <a-divider />

            <div class="profile-stats">
              <div class="ps-item">
                <div class="ps-num">{{ instructor.examCount || 0 }}</div>
                <div class="ps-label">考试次数</div>
              </div>
              <div class="ps-divider"></div>
              <div class="ps-item">
                <div class="ps-num">{{ Math.round(instructor.studyHours || 0) }}</div>
                <div class="ps-label">学习时长</div>
              </div>
              <div class="ps-divider"></div>
              <div class="ps-item">
                <div class="ps-num" style="color: #faad14">{{ instructor.avgScore || 0 }}</div>
                <div class="ps-label">平均分</div>
              </div>
            </div>

            <a-divider />

            <div class="profile-info">
              <div class="pi-row">
                <span class="pi-label">身份证号</span>
                <span>{{ instructor.idCardNumber || '未设置' }}</span>
              </div>
              <div class="pi-row">
                <span class="pi-label">行政级别</span>
                <span>{{ instructor.instructorAdminLevel || '未设置' }}</span>
              </div>
              <div class="pi-row">
                <span class="pi-label">警种</span>
                <span>{{ specialtiesText }}</span>
              </div>
              <div class="pi-row">
                <span class="pi-label">联系方式</span>
                <span>{{ instructor.phone || '未设置' }}</span>
              </div>
              <div class="pi-row">
                <span class="pi-label">入警日期</span>
                <span>{{ instructor.joinDate || '未设置' }}</span>
              </div>
            </div>
          </a-card>
        </a-col>

        <!-- 右：详情 -->
        <a-col :span="16">
          <a-card :bordered="false">
            <a-tabs v-model:activeKey="activeTab">
              <a-tab-pane key="intro" tab="教官简介">
                <div class="intro-section">
                  <p class="bio-text">
                    {{ introText }}
                  </p>
                  <div class="specialty-section">
                    <h4>专业领域</h4>
                    <div class="specialty-tags">
                      <a-tag v-for="s in instructor.specialties" :key="s" color="blue">{{ s }}</a-tag>
                      <span v-if="!instructor.specialties || instructor.specialties.length === 0" style="color: #999">未设置</span>
                    </div>
                  </div>
                  <div class="specialty-section">
                    <h4>教官资质</h4>
                    <div class="specialty-tags">
                      <a-tag v-for="item in instructor.instructorQualification" :key="item" color="gold">{{ item }}</a-tag>
                      <span v-if="!instructor.instructorQualification || instructor.instructorQualification.length === 0" style="color: #999">未设置</span>
                    </div>
                  </div>
                </div>
              </a-tab-pane>

              <a-tab-pane key="courses" tab="授课档案">
                <a-empty v-if="!teachingRecords.length" description="暂无授课记录" />
                <a-table
                  v-else
                  :data-source="teachingRecords"
                  :columns="teachingColumns"
                  :pagination="false"
                  row-key="id"
                  size="small"
                />
              </a-tab-pane>

              <a-tab-pane key="reviews" tab="训历统计">
                <div v-if="teachingSummary" class="summary-grid">
                  <div class="summary-item">
                    <div class="summary-num">{{ teachingSummary.trainingCount }}</div>
                    <div class="summary-label">参与培训班</div>
                  </div>
                  <div class="summary-item">
                    <div class="summary-num">{{ teachingSummary.totalHours }}</div>
                    <div class="summary-label">总授课课时</div>
                  </div>
                  <div class="summary-item">
                    <div class="summary-num">{{ teachingSummary.studentTotal }}</div>
                    <div class="summary-label">累计学员</div>
                  </div>
                  <div class="summary-item">
                    <div class="summary-num" style="color: #faad14">{{ teachingSummary.evaluationAvg || '-' }}</div>
                    <div class="summary-label">教学评价</div>
                  </div>
                </div>
                <div v-if="teachingSummary && teachingSummary.courseNames.length" class="summary-courses">
                  <h4>授课课程</h4>
                  <div class="specialty-tags">
                    <a-tag v-for="name in teachingSummary.courseNames" :key="name" color="blue">{{ name }}</a-tag>
                  </div>
                </div>
                <a-empty v-if="!teachingSummary" description="暂无统计数据" />
              </a-tab-pane>
            </a-tabs>
          </a-card>
        </a-col>
      </a-row>
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
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import { getUser, updateUser } from '@/api/user'
import { getInstructorTeachingSummary, getInstructorTeachingRecords } from '@/api/training'
import InstructorEditModal from './components/InstructorEditModal.vue'

const route = useRoute()
const instructorId = Number(route.params.id)
const authStore = useAuthStore()

const loading = ref(false)
const activeTab = ref('intro')
const canEditInstructor = computed(() => authStore.hasPermission('UPDATE_USER'))
const editDialog = ref({
  open: false,
  submitting: false,
  user: null,
})
const instructor = ref({
  id: null,
  name: '',
  title: '',
  unit: '',
  idCardNumber: '',
  phone: '',
  joinDate: '',
  level: '',
  instructorAdminLevel: '',
  specialties: [],
  instructorQualification: [],
  instructorIntro: '',
  examCount: 0,
  studyHours: 0,
  avgScore: 0,
})

const teachingRecords = ref([])
const teachingSummary = ref(null)

const teachingColumns = [
  { title: '培训班', dataIndex: 'trainingName', key: 'trainingName', ellipsis: true },
  { title: '课程', dataIndex: 'courseName', key: 'courseName', ellipsis: true },
  { title: '角色', dataIndex: 'role', key: 'role', width: 80, customRender: ({ text }) => text === 'primary' ? '主讲' : '助教' },
  { title: '课时', dataIndex: 'hours', key: 'hours', width: 70 },
  { title: '学员数', dataIndex: 'studentCount', key: 'studentCount', width: 80 },
  { title: '评价', dataIndex: 'evaluationAvg', key: 'evaluationAvg', width: 70, customRender: ({ text }) => text ?? '-' },
  { title: '地点', dataIndex: 'location', key: 'location', ellipsis: true },
]

const avatarColors = ['#003087', '#c8a84b', '#8B1A1A', '#1a5c2e', '#6b3a8a', '#2e86de']
const avatarColor = computed(() => avatarColors[(instructor.value.id || 0) % avatarColors.length])

const levelClass = computed(() => {
  const level = instructor.value.level || ''
  if (level.includes('高级') || level.includes('专家')) return 'expert'
  if (level.includes('中级')) return 'senior'
  return 'standard'
})

const levelLabel = computed(() => {
  const level = instructor.value.level || ''
  if (level.includes('高级') || level.includes('专家')) return '专家'
  if (level.includes('中级')) return '资深'
  return '教官'
})

const specialtiesText = computed(() => {
  const arr = instructor.value.specialties || []
  return arr.length ? arr.join('、') : '未设置'
})

const introText = computed(() => {
  if (instructor.value.instructorIntro) {
    return instructor.value.instructorIntro
  }
  const n = instructor.value.name || '该教官'
  const unit = instructor.value.unit || '未分配单位'
  const level = instructor.value.level || '教官'
  return `${n}，当前级别：${level}，所属单位：${unit}。` +
    `累计学习时长 ${Math.round(instructor.value.studyHours || 0)} 小时，考试次数 ${instructor.value.examCount || 0} 次，平均成绩 ${instructor.value.avgScore || 0}。`
})

async function loadInstructorDetail() {
  loading.value = true
  try {
    const data = await getUser(instructorId)
    instructor.value = {
      ...data,
      id: data.id,
      name: data.nickname || data.username,
      title: data.instructorTitle || data.level || '教官',
      unit: (data.departments && data.departments.length > 0) ? data.departments[0].name : '未分配',
      idCardNumber: data.idCardNumber,
      phone: data.phone,
      joinDate: data.joinDate,
      level: data.instructorLevel || data.level || '',
      specialties: (data.instructorSpecialties && data.instructorSpecialties.length > 0)
        ? data.instructorSpecialties
        : (data.policeTypes || []).map((p) => p.name).filter(Boolean),
      instructorAdminLevel: data.instructorAdminLevel || '',
      instructorQualification: data.instructorQualification || [],
      instructorIntro: data.instructorIntro || '',
      examCount: data.examCount || 0,
      studyHours: data.studyHours || 0,
      avgScore: data.avgScore || 0,
    }
  } catch {
    instructor.value = {
      id: instructorId,
      name: '教官不存在',
      title: '',
      unit: '',
      idCardNumber: '',
      phone: '',
      joinDate: '',
      level: '',
      specialties: [],
      instructorQualification: [],
      instructorIntro: '',
      examCount: 0,
      studyHours: 0,
      avgScore: 0,
    }
  } finally {
    loading.value = false
  }
}

function openEditModal() {
  if (!canEditInstructor.value) return
  editDialog.value = {
    open: true,
    submitting: false,
    user: { ...instructor.value },
  }
}

async function handleEditSubmit(payload) {
  editDialog.value = { ...editDialog.value, submitting: true }
  try {
    await updateUser(instructorId, payload)
    message.success('教官信息已更新')
    editDialog.value = { open: false, submitting: false, user: null }
    await loadInstructorDetail()
  } catch (error) {
    editDialog.value = { ...editDialog.value, submitting: false }
    message.error(error.message || '教官信息更新失败')
  }
}

async function loadTeachingData() {
  try {
    const [summary, records] = await Promise.all([
      getInstructorTeachingSummary(instructorId),
      getInstructorTeachingRecords(instructorId),
    ])
    teachingSummary.value = summary
    teachingRecords.value = records || []
  } catch {
    teachingSummary.value = null
    teachingRecords.value = []
  }
}

onMounted(() => {
  loadInstructorDetail()
  loadTeachingData()
})
</script>

<style scoped>
.instructor-detail-page { padding: 0; }
.profile-card { text-align: center; }
.profile-top { position: relative; display: inline-block; margin-bottom: 12px; }
.inst-badge-large { position: absolute; bottom: -4px; right: -8px; font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 700; }
.inst-badge-large.senior { background: #c8a84b; color: #fff; }
.inst-badge-large.expert { background: #003087; color: #fff; }
.inst-badge-large.standard { background: #888; color: #fff; }
.profile-name { font-size: 22px; font-weight: 700; color: #1a1a1a; }
.profile-title { font-size: 14px; color: var(--police-primary); margin: 4px 0; }
.profile-unit { font-size: 12px; color: #888; }
.profile-actions { margin-top: 16px; }
.profile-stats { display: flex; justify-content: space-around; align-items: center; }
.ps-item { text-align: center; }
.ps-num { font-size: 22px; font-weight: 700; color: #1a1a1a; }
.ps-label { font-size: 11px; color: #888; }
.ps-divider { width: 1px; height: 32px; background: #f0f0f0; }
.profile-info { text-align: left; }
.pi-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; border-bottom: 1px solid #f8f8f8; }
.pi-label { color: #888; }
.bio-text { font-size: 14px; color: #555; line-height: 1.8; margin-bottom: 20px; }
.specialty-section h4 { margin-bottom: 8px; color: #333; }
.specialty-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.summary-grid { display: flex; gap: 24px; margin-bottom: 24px; }
.summary-item { text-align: center; flex: 1; padding: 16px; background: #fafafa; border-radius: 8px; }
.summary-num { font-size: 28px; font-weight: 700; color: #1a1a1a; }
.summary-label { font-size: 12px; color: #888; margin-top: 4px; }
.summary-courses { margin-top: 16px; }
.summary-courses h4 { margin-bottom: 8px; color: #333; }
</style>
