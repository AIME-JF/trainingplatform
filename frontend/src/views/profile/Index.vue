<template>
  <div class="profile-page">
    <!-- 顶部个人信息 banner -->
    <div class="profile-banner">
      <div class="banner-left">
        <a-avatar :size="80" :style="{ background: '#c8a84b', fontSize: '30px', border: '3px solid rgba(255,255,255,0.4)' }">
          {{ user.name.charAt(0) }}
        </a-avatar>
        <div class="banner-info">
          <h2 class="banner-name">{{ user.name }}</h2>
          <div class="banner-meta">
            <a-tag color="blue">{{ user.roleLabel }}</a-tag>
            <span>{{ user.unit }}</span>
            <span>警号 {{ user.policeId }}</span>
          </div>
          <div class="banner-sub">{{ user.policeType }} · 入警 {{ user.joinDate }}</div>
        </div>
      </div>
      <div class="banner-right">
        <a-button ghost @click="editMode = !editMode">{{ editMode ? '取消编辑' : '编辑资料' }}</a-button>
      </div>
    </div>

    <a-row :gutter="20" style="margin-top:20px">
      <!-- 左：学习数据 -->
      <a-col :span="16">
        <a-tabs v-model:activeKey="activeTab">
          <a-tab-pane key="study" tab="学习记录">
            <!-- 学习统计 -->
            <div class="study-stats">
              <div class="ss-item" v-for="s in studyStats" :key="s.label">
                <div class="ss-icon" :style="{ color: s.color }">{{ s.icon }}</div>
                <div class="ss-num">{{ s.value }}</div>
                <div class="ss-label">{{ s.label }}</div>
              </div>
            </div>

            <!-- 月度完成趋势 -->
            <a-card :bordered="false" style="margin-top:16px">
              <template #title>本月学习进度</template>
              <a-progress
                :percent="68"
                :stroke-color="{ from: '#003087', to: '#c8a84b' }"
                status="active"
              />
              <div class="month-detail">
                <span>本月目标：15课时</span>
                <span style="color:var(--police-primary);font-weight:600">已完成：10.2课时</span>
              </div>
            </a-card>

            <!-- 近期课程 -->
            <a-card :bordered="false" style="margin-top:16px" title="最近学习">
              <div class="recent-courses">
                <div v-for="c in recentCourses" :key="c.id" class="rc-item">
                  <div class="rc-cover" :style="{ background: c.color }">{{ c.icon }}</div>
                  <div class="rc-info">
                    <div class="rc-title">{{ c.title }}</div>
                    <div class="rc-time">上次学习：{{ c.lastTime }}</div>
                  </div>
                  <div class="rc-right">
                    <a-progress type="circle" :percent="c.progress" :width="44" :stroke-color="c.progress === 100 ? '#52c41a' : '#003087'" />
                  </div>
                </div>
              </div>
            </a-card>
          </a-tab-pane>

          <a-tab-pane key="exam" tab="考试记录">
            <a-table :dataSource="examHistory" :columns="examColumns" size="small">
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'score'">
                  <span :style="{ color: record.score >= 60 ? '#52c41a' : '#ff4d4f', fontWeight: 700 }">
                    {{ record.score }}分
                  </span>
                </template>
                <template v-if="column.key === 'result'">
                  <a-tag :color="record.passed ? 'green' : 'red'" size="small">{{ record.passed ? '通过' : '未通过' }}</a-tag>
                </template>
              </template>
            </a-table>
          </a-tab-pane>

          <a-tab-pane key="cert" tab="荣誉证书">
            <div class="cert-grid">
              <div v-for="cert in certList" :key="cert.id" class="cert-card">
                <div class="cert-seal">🏅</div>
                <div class="cert-name">{{ cert.name }}</div>
                <div class="cert-issuer">{{ cert.issuer }}</div>
                <div class="cert-date">{{ cert.date }}</div>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </a-col>

      <!-- 右：能力雷达 + 积分 -->
      <a-col :span="8">
        <a-card title="能力画像" :bordered="false" style="margin-bottom:16px">
          <v-chart class="radar-chart" :option="radarOption" autoresize />
          <div class="ability-list">
            <div v-for="ab in abilities" :key="ab.label" class="ab-row">
              <span class="ab-label">{{ ab.label }}</span>
              <a-progress :percent="ab.score" :stroke-color="ab.score >= 80 ? '#52c41a' : '#faad14'" size="small" style="flex:1;margin:0 8px" />
              <span class="ab-score">{{ ab.score }}</span>
            </div>
          </div>
        </a-card>

        <a-card title="积分与排名" :bordered="false">
          <div class="points-display">
            <div class="points-num">{{ points }}</div>
            <div class="points-label">学习积分</div>
          </div>
          <a-divider />
          <div class="rank-info">
            <div class="rank-row">
              <span class="rr-label">单位排名</span>
              <span class="rr-val">第 <strong style="color:var(--police-primary)">{{ rank }}</strong> 名</span>
            </div>
            <div class="rank-row">
              <span class="rr-label">全区排名</span>
              <span class="rr-val">Top <strong style="color:var(--police-gold)">{{ globalRankPercent }}%</strong></span>
            </div>
          </div>
          <a-divider />
          <div class="point-history">
            <div v-for="ph in pointHistory" :key="ph.id" class="ph-item">
              <span class="ph-action">{{ ph.action }}</span>
              <span :class="ph.points > 0 ? 'ph-positive' : 'ph-negative'">{{ ph.points > 0 ? '+' : '' }}{{ ph.points }}</span>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart } from 'echarts/charts'
import { TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { useAuthStore } from '@/stores/auth'
import { getProfile, getStudyStats, getExamHistory } from '@/api/profile'
import { getCertificates } from '@/api/certificate'
import { MOCK_ABILITIES, MOCK_POINT_HISTORY } from '@/mock/profile'

use([CanvasRenderer, RadarChart, TooltipComponent])

const authStore = useAuthStore()
const user = authStore.currentUser
const activeTab = ref('study')
const editMode = ref(false)
const points = user.studyHours ? user.studyHours * 10 + 6 : 1286
const rank = user.role === 'student' ? 3 : 1
const globalRankPercent = user.role === 'student' ? 12 : 5

const studyStats = [
  { icon: '📚', label: '已学课程', value: (user.examCount || 12) + '门', color: '#003087' },
  { icon: '⏱', label: '总学时', value: (user.studyHours || 48) + 'h', color: '#52c41a' },
  { icon: '✅', label: '平均分', value: (user.avgScore || 86) + '分', color: '#faad14' },
  { icon: '🏆', label: '通过考试', value: Math.round((user.examCount || 8) * 0.6) + '次', color: '#c8a84b' },
]

const abilities = MOCK_ABILITIES

const radarOption = {
  radar: {
    indicator: abilities.map(a => ({ name: a.label, max: 100 })),
    splitNumber: 4,
    axisName: { color: '#555', fontSize: 11 },
    splitArea: { areaStyle: { color: ['#f8f9ff', '#eef2ff', '#e3eaff', '#d8e3ff'] } },
  },
  series: [{
    type: 'radar',
    data: [{
      value: abilities.map(a => a.score),
      name: '能力评分',
      areaStyle: { color: 'rgba(200,168,75,0.15)' },
      lineStyle: { color: '#c8a84b', width: 2 },
      itemStyle: { color: '#c8a84b' },
    }]
  }]
}

const recentCourses = ref([])
const examHistory = ref([])

onMounted(async () => {
  try {
    const [studyRes, examRes, certRes] = await Promise.all([
      getStudyStats().catch(() => null),
      getExamHistory().catch(() => []),
      getCertificates({ userId: user?.id }).catch(() => ({ items: [] })),
    ])
    if (studyRes?.recentCourses) {
      recentCourses.value = studyRes.recentCourses
    }
    examHistory.value = examRes?.items || examRes || []
    certList.value = certRes?.items || certRes || []
  } catch { /* ignore */ }
})

const examColumns = [
  { title: '考试名称', dataIndex: 'title', key: 'title' },
  { title: '日期', dataIndex: 'date', key: 'date' },
  { title: '得分', key: 'score' },
  { title: '结果', key: 'result' },
]

const certList = ref([])

const pointHistory = MOCK_POINT_HISTORY
</script>

<style scoped>
.profile-page { padding: 0; }
.profile-banner { background: linear-gradient(135deg, #001849, #003087); border-radius: 10px; padding: 24px 28px; display: flex; justify-content: space-between; align-items: center; }
.banner-left { display: flex; align-items: center; gap: 20px; }
.banner-name { margin: 0 0 6px; font-size: 22px; font-weight: 700; color: #fff; }
.banner-meta { display: flex; align-items: center; gap: 10px; color: rgba(255,255,255,0.8); font-size: 13px; margin-bottom: 4px; }
.banner-sub { color: rgba(255,255,255,0.6); font-size: 12px; }
.study-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.ss-item { background: #fff; border-radius: 8px; padding: 16px; text-align: center; border: 1px solid #f0f0f0; }
.ss-icon { font-size: 28px; margin-bottom: 6px; }
.ss-num { font-size: 20px; font-weight: 700; color: #1a1a1a; }
.ss-label { font-size: 11px; color: #888; }
.month-detail { display: flex; justify-content: space-between; margin-top: 8px; font-size: 13px; color: #888; }
.recent-courses { display: flex; flex-direction: column; gap: 12px; }
.rc-item { display: flex; align-items: center; gap: 12px; }
.rc-cover { width: 44px; height: 44px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.rc-info { flex: 1; }
.rc-title { font-size: 13px; font-weight: 500; color: #1a1a1a; }
.rc-time { font-size: 11px; color: #aaa; }
.cert-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.cert-card { border: 2px solid #c8a84b; border-radius: 8px; padding: 20px; text-align: center; background: linear-gradient(135deg, #fffbe6, #fff); }
.cert-seal { font-size: 36px; margin-bottom: 8px; }
.cert-name { font-size: 16px; font-weight: 700; color: #333; }
.cert-issuer { font-size: 12px; color: #888; margin: 4px 0; }
.cert-date { font-size: 11px; color: #aaa; }
.radar-chart { height: 200px; }
.ability-list { margin-top: 12px; display: flex; flex-direction: column; gap: 8px; }
.ab-row { display: flex; align-items: center; }
.ab-label { font-size: 12px; color: #555; min-width: 56px; }
.ab-score { font-size: 12px; font-weight: 700; color: var(--police-primary); min-width: 28px; text-align: right; }
.points-display { text-align: center; padding: 12px 0; }
.points-num { font-size: 48px; font-weight: 900; color: var(--police-gold); }
.points-label { font-size: 13px; color: #888; }
.rank-info { display: flex; flex-direction: column; gap: 10px; }
.rank-row { display: flex; justify-content: space-between; font-size: 13px; }
.rr-label { color: #888; }
.point-history { display: flex; flex-direction: column; gap: 8px; }
.ph-item { display: flex; justify-content: space-between; font-size: 12px; color: #666; }
.ph-positive { color: #52c41a; font-weight: 600; }
.ph-negative { color: #ff4d4f; font-weight: 600; }
</style>
