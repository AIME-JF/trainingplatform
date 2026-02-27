<template>
  <div class="instructor-detail-page">
    <a-breadcrumb style="margin-bottom:16px">
      <a-breadcrumb-item @click="$router.push('/instructor')" style="cursor:pointer;color:var(--police-primary)">教官库</a-breadcrumb-item>
      <a-breadcrumb-item>{{ inst.name }}</a-breadcrumb-item>
    </a-breadcrumb>

    <a-row :gutter="20">
      <!-- 左：教官信息卡 -->
      <a-col :span="8">
        <a-card :bordered="false" class="profile-card">
          <div class="profile-top">
            <a-avatar :size="96" :style="{ background: inst.avatarColor, fontSize: '36px' }">
              {{ inst.name.charAt(0) }}
            </a-avatar>
            <div class="inst-badge-large" :class="inst.level">{{ inst.levelLabel }}</div>
          </div>
          <div class="profile-name">{{ inst.name }}</div>
          <div class="profile-title">{{ inst.title }}</div>
          <div class="profile-unit">{{ inst.unit }}</div>

          <a-divider />

          <div class="profile-stats">
            <div class="ps-item">
              <div class="ps-num">{{ inst.courseCount }}</div>
              <div class="ps-label">主讲课程</div>
            </div>
            <div class="ps-divider"></div>
            <div class="ps-item">
              <div class="ps-num">{{ inst.studentCount }}</div>
              <div class="ps-label">培训人次</div>
            </div>
            <div class="ps-divider"></div>
            <div class="ps-item">
              <div class="ps-num" style="color:#faad14">{{ inst.rating }}</div>
              <div class="ps-label">综合评分</div>
            </div>
          </div>

          <a-divider />

          <div class="profile-info">
            <div class="pi-row">
              <span class="pi-label">警种</span>
              <span>{{ inst.policeType }}</span>
            </div>
            <div class="pi-row">
              <span class="pi-label">从警年限</span>
              <span>{{ inst.years }} 年</span>
            </div>
            <div class="pi-row">
              <span class="pi-label">联系方式</span>
              <span>{{ inst.phone }}</span>
            </div>
          </div>

          <a-divider />

          <div class="cert-section">
            <div class="cert-title">资质证书</div>
            <div class="cert-list">
              <a-tag v-for="cert in inst.certificates" :key="cert" color="gold" style="margin-bottom:6px">🏅 {{ cert }}</a-tag>
            </div>
          </div>
        </a-card>
      </a-col>

      <!-- 右：详情 Tabs -->
      <a-col :span="16">
        <a-card :bordered="false">
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane key="intro" tab="教官简介">
              <div class="intro-section">
                <p class="bio-text">{{ inst.bio }}</p>
                <div class="specialty-section">
                  <h4>专业领域</h4>
                  <div class="specialty-tags">
                    <a-tag v-for="s in inst.specialties" :key="s" color="blue">{{ s }}</a-tag>
                  </div>
                </div>
              </div>
            </a-tab-pane>

            <a-tab-pane key="courses" tab="主讲课程">
              <div class="inst-courses">
                <div v-for="c in instCourses" :key="c.id" class="course-row">
                  <div class="cr-cover" :style="{ background: c.coverColor }">{{ getCoverIcon(c.category) }}</div>
                  <div class="cr-info">
                    <div class="cr-title">{{ c.title }}</div>
                    <div class="cr-meta">{{ c.duration }}分钟 · {{ c.studentCount.toLocaleString() }} 人学过</div>
                  </div>
                  <div class="cr-rating">
                    <StarFilled style="color:#faad14" /> {{ c.rating }}
                  </div>
                </div>
              </div>
            </a-tab-pane>

            <a-tab-pane key="reviews" tab="学员评价">
              <div class="reviews-section">
                <div class="rating-overview">
                  <div class="rating-big">{{ inst.rating }}</div>
                  <div class="rating-stars">
                    <StarFilled v-for="i in 5" :key="i" :style="{ color: i <= Math.round(inst.rating) ? '#faad14' : '#ddd' }" />
                  </div>
                  <div class="rating-count">共 {{ mockReviews.length }} 条评价</div>
                </div>
                <a-divider />
                <div class="review-list">
                  <div v-for="r in mockReviews" :key="r.id" class="review-item">
                    <div class="review-header">
                      <a-avatar size="small" :style="{ background: '#003087' }">{{ r.user.charAt(0) }}</a-avatar>
                      <span class="rv-user">{{ r.user }}</span>
                      <span class="rv-stars">
                        <StarFilled v-for="i in r.rating" :key="i" style="color:#faad14;font-size:12px" />
                      </span>
                      <span class="rv-date">{{ r.date }}</span>
                    </div>
                    <div class="review-content">{{ r.content }}</div>
                    <div class="review-tags">
                      <a-tag v-for="t in r.tags" :key="t" size="small">{{ t }}</a-tag>
                    </div>
                  </div>
                </div>
              </div>
            </a-tab-pane>

            <a-tab-pane key="training" tab="培训记录">
              <a-table :dataSource="trainingHistory" :columns="historyColumns" size="small" />
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { StarFilled } from '@ant-design/icons-vue'
import { MOCK_INSTRUCTORS } from '@/mock/instructors'
import { MOCK_COURSES } from '@/mock/courses'

const route = useRoute()
const instId = parseInt(route.params.id) || 1
const inst = computed(() => MOCK_INSTRUCTORS.find(i => i.id === instId) || MOCK_INSTRUCTORS[0])
const activeTab = ref('intro')

const instCourses = computed(() => MOCK_COURSES.filter(c => c.instructor === inst.value.name))
const getCoverIcon = (cat) => ({ law: '⚖️', skill: '🔧', traffic: '🚗', community: '🏘️', cyber: '💻', physical: '💪' })[cat] ?? '📚'

const mockReviews = [
  { id: 1, user: '张民警', rating: 5, date: '2025-03-01', content: '讲课深入浅出，案例生动，学完很有收获，强烈推荐！', tags: ['内容丰富', '互动性强', '实用性高'] },
  { id: 2, user: '李警官', rating: 4, date: '2025-02-20', content: '理论知识讲解很扎实，实操环节还可以再多一些。', tags: ['理论扎实', '专业权威'] },
  { id: 3, user: '王同学', rating: 5, date: '2025-02-10', content: '老师很有耐心，答疑及时，遇到问题都能快速解答。', tags: ['耐心负责', '答疑及时'] },
]

const trainingHistory = [
  { key: 1, title: '2025年春季刑侦技能培训班', period: '2025-03-01 ~ 2025-03-15', students: 28, score: 4.8 },
  { key: 2, title: '基层民警法律素养提升班', period: '2024-11-10 ~ 2024-11-20', students: 35, score: 4.9 },
  { key: 3, title: '执法规范化专项培训', period: '2024-09-01 ~ 2024-09-07', students: 42, score: 4.7 },
]

const historyColumns = [
  { title: '培训班名称', dataIndex: 'title', key: 'title' },
  { title: '时间', dataIndex: 'period', key: 'period' },
  { title: '学员数', dataIndex: 'students', key: 'students' },
  { title: '评分', dataIndex: 'score', key: 'score' },
]
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
.profile-stats { display: flex; justify-content: space-around; align-items: center; }
.ps-item { text-align: center; }
.ps-num { font-size: 22px; font-weight: 700; color: #1a1a1a; }
.ps-label { font-size: 11px; color: #888; }
.ps-divider { width: 1px; height: 32px; background: #f0f0f0; }
.profile-info { text-align: left; }
.pi-row { display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px; border-bottom: 1px solid #f8f8f8; }
.pi-label { color: #888; }
.cert-title { font-weight: 600; color: #333; margin-bottom: 8px; text-align: left; }
.cert-list { display: flex; flex-wrap: wrap; gap: 4px; }
.bio-text { font-size: 14px; color: #555; line-height: 1.8; margin-bottom: 20px; }
.specialty-section h4 { margin-bottom: 8px; color: #333; }
.specialty-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.inst-courses { display: flex; flex-direction: column; gap: 12px; }
.course-row { display: flex; align-items: center; gap: 12px; padding: 10px; border: 1px solid #f0f0f0; border-radius: 6px; }
.cr-cover { width: 48px; height: 48px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 24px; flex-shrink: 0; }
.cr-info { flex: 1; }
.cr-title { font-size: 14px; font-weight: 500; color: #1a1a1a; }
.cr-meta { font-size: 12px; color: #888; margin-top: 2px; }
.rating-overview { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 16px 0; }
.rating-big { font-size: 52px; font-weight: 900; color: var(--police-primary); }
.rating-count { font-size: 12px; color: #888; }
.review-list { display: flex; flex-direction: column; gap: 16px; }
.review-item { padding: 14px; background: #fafafa; border-radius: 8px; }
.review-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.rv-user { font-weight: 600; font-size: 13px; }
.rv-date { font-size: 11px; color: #aaa; margin-left: auto; }
.review-content { font-size: 13px; color: #555; line-height: 1.6; margin-bottom: 8px; }
.review-tags { display: flex; gap: 4px; flex-wrap: wrap; }
</style>
