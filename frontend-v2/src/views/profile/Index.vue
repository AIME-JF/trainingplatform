<template>
  <section class="page-content profile-page">
    <a-spin :spinning="loading">
      <div class="profile-shell">
        <section class="profile-hero">
          <div class="profile-hero-top">
            <div class="profile-identity">
              <a-avatar :size="72" :src="profile?.avatar || authStore.currentUser?.avatar" class="profile-avatar">
                {{ avatarText }}
              </a-avatar>

              <div class="profile-copy">
                <div class="profile-name-row">
                  <h1 class="profile-name">{{ displayName }}</h1>
                  <a-tag v-if="primaryRole" color="blue">{{ primaryRole }}</a-tag>
                </div>

                <div class="profile-meta">
                  <span>{{ profile?.police_id || authStore.currentUser?.police_id || '未设置警号' }}</span>
                  <span>·</span>
                  <span>{{ primaryDepartment }}</span>
                </div>

                <div class="profile-submeta">
                  <span>{{ primaryPoliceType }}</span>
                  <span v-if="profile?.join_date">入警 {{ profile.join_date }}</span>
                </div>
              </div>
            </div>

            <button type="button" class="logout-button" @click="handleLogout">
              退出登录
            </button>
          </div>

          <div class="profile-contact-grid">
            <div class="profile-contact-card">
              <span class="contact-label">手机号</span>
              <strong>{{ profile?.phone || authStore.currentUser?.phone || '未设置' }}</strong>
            </div>
            <div class="profile-contact-card">
              <span class="contact-label">邮箱</span>
              <strong>{{ profile?.email || authStore.currentUser?.email || '未设置' }}</strong>
            </div>
          </div>
        </section>

        <section class="profile-section-grid">
          <article class="profile-card notice-card">
            <div class="section-head">
              <div>
                <h2>消息提醒</h2>
                <p>查看未读提醒与最近通知</p>
              </div>
              <button type="button" class="section-link" @click="navigateTo('/notifications')">
                查看全部
              </button>
            </div>

            <div class="notice-summary-grid">
              <div class="notice-summary-item">
                <span>全部未读</span>
                <strong>{{ overview?.notice_unread_count?.total ?? 0 }}</strong>
              </div>
              <div class="notice-summary-item">
                <span>消息提醒</span>
                <strong>{{ overview?.notice_unread_count?.reminder ?? 0 }}</strong>
              </div>
              <div class="notice-summary-item">
                <span>平台公告</span>
                <strong>{{ overview?.notice_unread_count?.system ?? 0 }}</strong>
              </div>
            </div>

            <div v-if="recentNotices.length" class="notice-list">
              <button
                v-for="item in recentNotices"
                :key="item.id"
                type="button"
                class="notice-item"
                :class="{ unread: !item.is_read }"
                @click="navigateTo('/notifications')"
              >
                <div class="notice-item-main">
                  <div class="notice-item-title-row">
                    <strong>{{ item.title }}</strong>
                    <a-tag v-if="item.reminder_type" color="blue">
                      {{ getReminderTypeLabel(item.reminder_type) }}
                    </a-tag>
                  </div>
                  <p>{{ item.content }}</p>
                </div>
                <span class="notice-item-time">{{ formatNoticeTime(item.created_at) }}</span>
              </button>
            </div>

            <a-empty v-else description="暂无消息提醒" />
          </article>

          <article class="profile-card stats-card">
            <div class="section-head">
              <div>
                <h2>学习统计</h2>
                <p>汇总课程、考试和证书情况</p>
              </div>
            </div>

            <div class="stats-grid">
              <div v-for="item in statsItems" :key="item.label" class="stat-item">
                <span>{{ item.label }}</span>
                <strong>{{ item.value }}</strong>
              </div>
            </div>
          </article>
        </section>

        <article class="profile-card quick-card">
          <div class="section-head">
            <div>
              <h2>常用入口</h2>
              <p>快速进入班级、通知、考试和资源模块</p>
            </div>
          </div>

          <div class="quick-grid">
            <button
              v-for="action in profileQuickActions"
              :key="action.path"
              type="button"
              class="quick-item"
              @click="navigateTo(action.path)"
            >
              <span class="quick-icon" :style="{ background: action.mobileBackground || action.background }">
                <component :is="action.mobileIcon || action.icon" />
              </span>
              <span class="quick-text">
                <strong>{{ action.title }}</strong>
                <span>{{ action.description }}</span>
              </span>
            </button>
          </div>
        </article>
      </div>
    </a-spin>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { NoticeResponse, ProfileOverviewResponse } from '@/api/generated/model'
import { getProfileOverviewApiV1ProfileOverviewGet } from '@/api/generated/profile/profile'
import { quickActionConfigs } from '@/constants/quickActions'
import { getReminderTypeLabel, formatNoticeTime } from '@/utils/notice'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const overview = ref<ProfileOverviewResponse | null>(null)

const profile = computed(() => overview.value?.profile ?? null)
const recentNotices = computed<NoticeResponse[]>(() => overview.value?.recent_notices || [])
const displayName = computed(() => profile.value?.nickname || authStore.currentUser?.name || profile.value?.username || '用户')
const avatarText = computed(() => (displayName.value || '用').slice(0, 1))
const primaryRole = computed(() => profile.value?.roles?.[0] || (authStore.isInstructor ? '教官' : authStore.isStudent ? '学员' : '用户'))
const primaryDepartment = computed(() => profile.value?.departments?.[0] || authStore.currentUser?.unit || '未设置单位')
const primaryPoliceType = computed(() => profile.value?.police_types?.[0] || authStore.currentUser?.level || '未设置警种')

const statsItems = computed(() => {
  const stats = overview.value?.study_stats
  return [
    { label: '总学时', value: formatMetric(stats?.total_study_hours, 'h') },
    { label: '完成课程', value: formatMetric(stats?.completed_courses, '门') },
    { label: '进行中课程', value: formatMetric(stats?.in_progress_courses, '门') },
    { label: '考试次数', value: formatMetric(stats?.total_exams, '次') },
    { label: '平均分', value: formatMetric(stats?.avg_score, '分') },
    { label: '证书数量', value: formatMetric(stats?.certificates_count, '张') },
  ]
})

const profileQuickActions = computed(() => quickActionConfigs.filter((item) => (
  item.surfaces.includes('profile') && authStore.hasAnyPermission(item.permissions)
)))

async function fetchOverview() {
  loading.value = true
  try {
    overview.value = await getProfileOverviewApiV1ProfileOverviewGet()
  } finally {
    loading.value = false
  }
}

function formatMetric(value: number | null | undefined, suffix: string): string {
  const normalized = typeof value === 'number' ? value : 0
  return `${Number.isInteger(normalized) ? normalized : normalized.toFixed(1)}${suffix}`
}

function navigateTo(path: string) {
  router.push(path)
}

function handleLogout() {
  authStore.logout()
  router.replace('/login')
}

onMounted(() => {
  void fetchOverview()
})
</script>

<style scoped>
.profile-page {
  background:
    radial-gradient(circle at top right, rgba(52, 101, 228, 0.14), transparent 30%),
    linear-gradient(180deg, #eef4fb 0%, #f6f8fc 100%);
}

.profile-shell {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.profile-hero {
  position: relative;
  overflow: hidden;
  padding: 22px 18px 18px;
  border-radius: 28px;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.16), transparent 24%),
    linear-gradient(135deg, #2045a0 0%, #2a5bc5 62%, #4f79df 100%);
  color: #fff;
  box-shadow: 0 18px 36px rgba(32, 69, 160, 0.18);
}

.profile-hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 18px;
}

.profile-identity {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.profile-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 2px solid rgba(255, 255, 255, 0.84);
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
  font-size: 30px;
  font-weight: 700;
}

.profile-avatar :deep(.ant-avatar-string) {
  position: static;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  line-height: 1;
  transform: none !important;
}

.profile-copy {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.profile-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.profile-name {
  margin: 0;
  font-size: 24px;
  line-height: 1.1;
  font-weight: 800;
  color: #fff;
}

.profile-meta,
.profile-submeta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 13px;
  line-height: 1.5;
  color: rgba(237, 244, 255, 0.9);
}

.profile-submeta {
  color: rgba(226, 236, 255, 0.76);
}

.logout-button {
  border: 0;
  border-radius: 999px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.14);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
}

.profile-contact-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.profile-contact-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.contact-label {
  font-size: 12px;
  color: rgba(224, 235, 255, 0.72);
}

.profile-contact-card strong {
  font-size: 16px;
  line-height: 1.4;
  font-weight: 700;
  color: #fff;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.profile-section-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.profile-card {
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.78);
  border-radius: 26px;
  padding: 18px 16px;
  box-shadow: 0 14px 28px rgba(43, 61, 108, 0.08);
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-head h2 {
  margin: 0 0 6px;
  font-size: 18px;
  line-height: 1.2;
  font-weight: 800;
  color: #172554;
}

.section-head p {
  margin: 0;
  color: var(--v2-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.section-link {
  border: 0;
  background: transparent;
  color: var(--v2-primary);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.notice-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.notice-summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 10px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(241, 245, 255, 0.98) 0%, rgba(248, 250, 255, 0.96) 100%);
  border: 1px solid rgba(224, 230, 246, 0.96);
}

.notice-summary-item span {
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.notice-summary-item strong {
  font-size: 22px;
  line-height: 1;
  color: #1a2b63;
}

.notice-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notice-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  padding: 12px 12px 12px 14px;
  border: 1px solid rgba(233, 237, 246, 0.96);
  border-radius: 16px;
  background: #fff;
  text-align: left;
  cursor: pointer;
}

.notice-item.unread {
  border-color: rgba(86, 116, 245, 0.2);
  background: linear-gradient(180deg, rgba(246, 248, 255, 0.96) 0%, #fff 100%);
}

.notice-item-main {
  min-width: 0;
  flex: 1;
}

.notice-item-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.notice-item-title-row strong {
  font-size: 14px;
  line-height: 1.4;
  color: var(--v2-text-primary);
}

.notice-item-main p {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--v2-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notice-item-time {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--v2-text-muted);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: flex-start;
  padding: 12px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(250, 251, 255, 0.98) 0%, rgba(241, 245, 255, 0.94) 100%);
  border: 1px solid rgba(228, 233, 246, 0.96);
}

.stat-item span {
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.stat-item strong {
  font-size: 20px;
  line-height: 1.15;
  color: #162255;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.quick-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(228, 233, 243, 0.96);
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 248, 252, 0.96) 100%);
  padding: 14px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.quick-item:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 28px rgba(40, 52, 88, 0.08);
}

.quick-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 15px;
  color: #24325f;
  font-size: 20px;
  margin-bottom: 10px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.quick-icon :deep(.anticon) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.quick-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-width: 0;
}

.quick-text strong {
  font-size: 15px;
  line-height: 1.35;
  color: var(--v2-text-primary);
  text-align: center;
}

.quick-text span {
  font-size: 12px;
  line-height: 1.45;
  color: var(--v2-text-secondary);
}

.notice-card :deep(.ant-empty) {
  margin-block: 16px 4px;
}

.notice-card :deep(.ant-empty-description) {
  font-size: 12px;
}

@media (max-width: 980px) {
  .profile-section-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .profile-page {
    padding-top: 14px;
  }

  .profile-shell {
    gap: 12px;
  }

  .profile-hero {
    padding: 18px 14px 14px;
    border-radius: 24px;
  }

  .profile-hero-top {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    margin-bottom: 12px;
  }

  .profile-identity {
    gap: 12px;
  }

  .profile-avatar {
    width: 60px !important;
    height: 60px !important;
    line-height: 60px !important;
    font-size: 24px !important;
  }

  .profile-copy {
    gap: 4px;
  }

  .profile-name {
    font-size: 20px;
  }

  .profile-meta,
  .profile-submeta {
    gap: 4px;
    font-size: 12px;
  }

  .logout-button {
    align-self: flex-start;
    padding: 8px 12px;
    font-size: 12px;
  }

  .profile-contact-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .profile-contact-card {
    gap: 4px;
    padding: 10px 12px;
    border-radius: 16px;
  }

  .profile-contact-card strong {
    font-size: 15px;
    line-height: 1.4;
  }

  .profile-card {
    padding: 16px 14px;
    border-radius: 22px;
  }

  .section-head {
    gap: 8px;
    margin-bottom: 12px;
  }

  .section-head h2 {
    margin-bottom: 2px;
    font-size: 17px;
  }

  .section-head p {
    display: none;
  }

  .notice-summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 10px;
  }

  .notice-summary-item {
    padding: 10px 8px;
    border-radius: 14px;
  }

  .notice-summary-item strong {
    font-size: 18px;
  }

  .notice-item {
    gap: 8px;
    padding: 10px 12px;
  }

  .notice-item-main p {
    font-size: 12px;
    line-height: 1.45;
    -webkit-line-clamp: 1;
  }

  .notice-item-time {
    font-size: 11px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .stat-item {
    gap: 6px;
    padding: 10px 11px;
    border-radius: 14px;
  }

  .stat-item strong {
    font-size: 18px;
  }

  .quick-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
  }

  .quick-item {
    min-height: 96px;
    padding: 12px 10px;
    border-radius: 16px;
    align-items: center;
    justify-content: center;
  }

  .quick-icon {
    width: 40px;
    height: 40px;
    border-radius: 14px;
    margin-bottom: 8px;
    font-size: 18px;
  }

  .quick-text strong {
    font-size: 14px;
    line-height: 1.4;
    font-weight: 700;
  }

  .quick-text span {
    display: none;
  }

  .notice-item {
    flex-direction: column;
  }

  .notice-item-time {
    margin-left: 0;
  }
}

@media (max-width: 380px) {
  .quick-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
