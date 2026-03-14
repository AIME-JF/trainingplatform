<template>
  <div class="trainee-detail-page">
    <a-breadcrumb style="margin-bottom:16px">
      <a-breadcrumb-item @click="$router.push('/trainee')" style="cursor:pointer;color:var(--police-primary)">学员库</a-breadcrumb-item>
      <a-breadcrumb-item>{{ trainee.nickname || trainee.username || '学员详情' }}</a-breadcrumb-item>
    </a-breadcrumb>

    <a-spin :spinning="loading">
      <a-row :gutter="20">
        <!-- 左：学员信息卡 -->
        <a-col :span="8">
          <a-card :bordered="false" class="profile-card">
            <div class="profile-top">
              <a-avatar :size="96" :style="{ background: getAvatarColor(trainee.id), fontSize: '36px' }">
                {{ (trainee.nickname || trainee.username || '').charAt(0) }}
              </a-avatar>
              <div class="traineebadge-large" :class="getLevelClass(trainee.level)">{{ trainee.level || '学员' }}</div>
            </div>
            <div class="profile-name">{{ trainee.nickname || trainee.username }}</div>
            <div class="profile-title">{{ trainee.policeId }}</div>

            <a-divider />

            <div class="profile-stats">
              <div class="ps-item">
                <div class="ps-num">{{ trainee.examCount || 0 }}</div>
                <div class="ps-label">考试次数</div>
              </div>
              <div class="ps-divider"></div>
              <div class="ps-item">
                <div class="ps-num" style="font-size: 16px;">{{ getDepartment(trainee) }}</div>
                <div class="ps-label">所属单位</div>
              </div>
              <div class="ps-divider"></div>
              <div class="ps-item">
                <div class="ps-num" style="color:#faad14">{{ trainee.avgScore || 0 }}</div>
                <div class="ps-label">平均分</div>
              </div>
            </div>

            <a-divider />

            <div class="profile-info">
              <div class="pi-row">
                <span class="pi-label">警种</span>
                <span>{{ getPoliceTypes(trainee) }}</span>
              </div>
              <div class="pi-row">
                <span class="pi-label">入警日期</span>
                <span>{{ trainee.joinDate || '未填写' }}</span>
              </div>
              <div class="pi-row">
                <span class="pi-label">联系方式</span>
                <span>{{ trainee.phone || '未填写' }}</span>
              </div>
              <div class="pi-row">
                <span class="pi-label">学习时长</span>
                <span>{{ trainee.studyHours || 0 }} 小时</span>
              </div>
            </div>
          </a-card>
        </a-col>

        <!-- 右：详情 Tabs -->
        <a-col :span="16">
          <a-card :bordered="false">
            <a-tabs v-model:activeKey="activeTab">
              <a-tab-pane key="intro" tab="学员简介">
                <div class="intro-section">
                  <p class="bio-text">{{ trainee.email ? `邮箱: ${trainee.email}` : '' }}</p>
                  <p class="bio-text">该学员累计学习 {{ trainee.studyHours || 0 }} 小时，参加考试 {{ trainee.examCount || 0 }} 次，平均成绩 {{ trainee.avgScore || 0 }} 分。</p>
                </div>
              </a-tab-pane>

              <a-tab-pane key="courses" tab="已学课程">
                <a-empty description="暂无课程数据" />
              </a-tab-pane>

              <a-tab-pane key="training" tab="培训记录">
                <a-empty description="暂无培训记录" />
              </a-tab-pane>
            </a-tabs>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getUser } from '@/api/user'

const route = useRoute()
const traineeId = Number(route.params.id)
const activeTab = ref('intro')
const loading = ref(false)
const trainee = ref({})

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

function getDepartment(t) {
  if (t.departments && t.departments.length > 0) return t.departments[0].name
  return '未分配'
}

function getPoliceTypes(t) {
  if (t.policeTypes && t.policeTypes.length > 0) return t.policeTypes.map(p => p.name).join('、')
  return '未分配'
}

onMounted(async () => {
  loading.value = true
  try {
    const data = await getUser(traineeId)
    trainee.value = data || {}
  } catch {
    trainee.value = {}
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.trainee-detail-page { padding: 0; }
.profile-card { text-align: center; }
.profile-top { position: relative; display: inline-block; margin-bottom: 12px; }
.traineebadge-large { position: absolute; bottom: -4px; right: -8px; font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 700; }
.traineebadge-large.senior { background: #c8a84b; color: #fff; }
.traineebadge-large.expert { background: #003087; color: #fff; }
.traineebadge-large.standard { background: #888; color: #fff; }
.profile-name { font-size: 22px; font-weight: 700; color: #1a1a1a; }
.profile-title { font-size: 14px; color: var(--police-primary); margin: 4px 0; }
.profile-stats { display: flex; justify-content: space-around; align-items: center; }
.ps-item { text-align: center; }
.ps-num { font-size: 22px; font-weight: 700; color: #1a1a1a; }
.ps-label { font-size: 11px; color: #888; }
.ps-divider { width: 1px; height: 32px; background: #f0f0f0; }
.profile-info { text-align: left; }
.pi-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; border-bottom: 1px solid #f8f8f8; }
.pi-label { color: #888; }
.bio-text { font-size: 14px; color: #555; line-height: 1.8; margin-bottom: 20px; }
</style>
