<template>
  <div class="talent-page">
    <div class="page-header">
      <div>
        <h2>人才库</h2>
        <p class="page-desc">基于学习数据与考核结果，自动识别优秀人才，为领导选拔提供数据支撑</p>
      </div>
      <a-tag color="blue">M3 智能体 · 人才识别</a-tag>
    </div>

    <!-- 统计概览 -->
    <a-row :gutter="16" style="margin-bottom:20px">
      <a-col :span="6" v-for="s in topStats" :key="s.label">
        <a-card :bordered="false" class="top-stat-card">
          <div class="ts-icon" :style="{ background: s.color + '15' }">{{ s.icon }}</div>
          <div class="ts-num" :style="{ color: s.color }">{{ s.value }}</div>
          <div class="ts-label">{{ s.label }}</div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 筛选 -->
    <a-card :bordered="false" style="margin-bottom:16px">
      <a-row :gutter="16" align="middle">
        <a-col :span="6">
          <a-input-search v-model:value="searchText" placeholder="搜索姓名、工号..." allow-clear />
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterTier" style="width:100%">
            <a-select-option value="all">全部层次</a-select-option>
            <a-select-option value="s">S级（拔尖）</a-select-option>
            <a-select-option value="a">A级（优秀）</a-select-option>
            <a-select-option value="b">B级（良好）</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterUnit" style="width:100%">
            <a-select-option value="all">全部单位</a-select-option>
            <a-select-option value="nanning">南宁市局</a-select-option>
            <a-select-option value="guilin">桂林市局</a-select-option>
            <a-select-option value="liuzhou">柳州市局</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <!-- 人才卡片 -->
    <div class="talent-grid">
      <div v-for="talent in filteredTalents" :key="talent.id" class="talent-card" :class="'tier-' + talent.tier">
        <div class="tc-tier-badge">{{ talent.tierLabel }}</div>
        <div class="tc-avatar-wrap">
          <a-avatar :size="64" :style="{ background: talent.avatarColor, fontSize: '22px' }">{{ (talent.name || '?').charAt(0) }}</a-avatar>
          <div class="tc-rank-badge">第{{ talent.rank }}名</div>
        </div>
        <div class="tc-name">{{ talent.name || '-' }}</div>
        <div class="tc-unit">{{ talent.unit }}</div>
        <div class="tc-score-row">
          <div class="tc-score-item">
            <div class="tsi-val">{{ talent.totalScore }}</div>
            <div class="tsi-key">综合评分</div>
          </div>
          <div class="tc-score-item">
            <div class="tsi-val">{{ talent.studyHours }}h</div>
            <div class="tsi-key">学习时长</div>
          </div>
          <div class="tc-score-item">
            <div class="tsi-val">{{ talent.passRate }}%</div>
            <div class="tsi-key">考试通过率</div>
          </div>
        </div>
        <div class="tc-tags">
          <a-tag v-for="t in talent.highlights" :key="t" size="small" :color="talent.tier === 's' ? 'gold' : 'blue'">{{ t }}</a-tag>
        </div>
        <div class="tc-ai-note">
          <RobotOutlined style="color:#aaa;margin-right:4px" />
          <span class="ai-note-text">{{ talent.aiNote }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RobotOutlined } from '@ant-design/icons-vue'
import { getTalents, getTalentStats } from '@/api/talent'

const searchText = ref('')
const filterTier = ref('all')
const filterUnit = ref('all')

const topStats = ref([
  { icon: '🏆', label: 'S级人才', value: 0, color: '#c8a84b' },
  { icon: '⭐', label: 'A级人才', value: 0, color: '#003087' },
  { icon: '✅', label: '本月新入库', value: 0, color: '#52c41a' },
  { icon: '📊', label: '评估覆盖率', value: '0%', color: '#722ed1' },
])

const talentList = ref([])

onMounted(async () => {
  try {
    const [talentRes, statsRes] = await Promise.all([
      getTalents({ size: -1 }),
      getTalentStats().catch(() => null),
    ])
    talentList.value = talentRes.items || talentRes || []
    if (statsRes) {
      topStats.value = [
        { icon: '🏆', label: 'S级人才', value: statsRes.sTier ?? 0, color: '#c8a84b' },
        { icon: '⭐', label: 'A级人才', value: statsRes.aTier ?? 0, color: '#003087' },
        { icon: '✅', label: '本月新入库', value: statsRes.newThisMonth ?? 0, color: '#52c41a' },
        { icon: '📊', label: '评估覆盖率', value: (statsRes.coverageRate ?? 0) + '%', color: '#722ed1' },
      ]
    }
  } catch { /* ignore */ }
})

const filteredTalents = computed(() => {
  let list = talentList.value.filter(t => t.name)
  if (searchText.value) list = list.filter(t => (t.name || '').includes(searchText.value))
  if (filterTier.value !== 'all') list = list.filter(t => t.tier === filterTier.value)
  return list
})
</script>

<style scoped>
.talent-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.page-desc { color: #888; font-size: 13px; margin: 4px 0 0; }
.top-stat-card { text-align: center; }
.ts-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 24px; margin: 0 auto 8px; }
.ts-num { font-size: 28px; font-weight: 800; }
.ts-label { font-size: 12px; color: #888; }
.talent-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.talent-card { background: #fff; border-radius: 12px; border: 2px solid #e8e8e8; padding: 20px; text-align: center; position: relative; transition: all 0.25s; }
.talent-card:hover { transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,48,135,0.1); }
.talent-card.tier-s { border-color: #c8a84b; background: linear-gradient(135deg, #fffbe6, #fff); }
.talent-card.tier-a { border-color: #003087; }
.tc-tier-badge { position: absolute; top: 12px; left: 12px; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 900; }
.tier-s .tc-tier-badge { background: #c8a84b; color: #fff; }
.tier-a .tc-tier-badge { background: #003087; color: #fff; }
.tier-b .tc-tier-badge { background: #888; color: #fff; }
.tc-avatar-wrap { position: relative; display: inline-block; margin-bottom: 10px; }
.tc-rank-badge { position: absolute; bottom: -4px; right: -8px; background: #f0f0f0; border-radius: 10px; font-size: 10px; padding: 1px 6px; color: #666; }
.tc-name { font-size: 18px; font-weight: 700; color: #1a1a1a; }
.tc-unit { font-size: 12px; color: #888; margin-bottom: 12px; }
.tc-score-row { display: flex; justify-content: space-around; padding: 10px 0; border-top: 1px solid #f0f0f0; border-bottom: 1px solid #f0f0f0; margin-bottom: 12px; }
.tc-score-item { text-align: center; }
.tsi-val { font-size: 16px; font-weight: 700; color: #1a1a1a; }
.tsi-key { font-size: 10px; color: #aaa; }
.tc-tags { display: flex; justify-content: center; flex-wrap: wrap; gap: 4px; margin-bottom: 10px; }
.tc-ai-note { text-align: left; font-size: 11px; color: #aaa; background: #f8f8f8; padding: 6px 8px; border-radius: 4px; }
.ai-note-text { line-height: 1.5; }
</style>
