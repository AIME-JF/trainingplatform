<template>
  <div class="notification-page">
    <div class="notification-header">
      <h2 class="page-title">通知中心</h2>
      <a-button v-if="hasUnread" type="link" size="small" @click="handleMarkAllRead">
        全部已读
      </a-button>
    </div>

    <div class="page-tabs">
      <span
        class="page-tab"
        :class="{ active: activeTab === 'reminder' }"
        @click="activeTab = 'reminder'; onTabChange()"
      >
        消息提醒
        <a-badge v-if="unreadCount.reminder" :count="unreadCount.reminder" :offset="[4, -2]" size="small" />
      </span>
      <span
        class="page-tab"
        :class="{ active: activeTab === 'system' }"
        @click="activeTab = 'system'; onTabChange()"
      >
        平台公告
        <a-badge v-if="unreadCount.system" :count="unreadCount.system" :offset="[4, -2]" size="small" />
      </span>
    </div>

    <div class="notification-body">
      <a-spin :spinning="loading">
        <div v-if="!list.length && !loading" class="notification-empty">
          <a-empty :description="activeTab === 'reminder' ? '暂无消息提醒' : '暂无平台公告'" />
        </div>
        <div v-else class="notification-list">
          <div
            v-for="item in list"
            :key="item.id"
            class="notification-item"
            :class="{ unread: !item.is_read }"
            @click="handleClickItem(item)"
          >
            <div class="notification-item-dot" />
            <div class="notification-item-body">
              <div class="notification-item-header">
                <span class="notification-item-title">{{ item.title }}</span>
                <a-tag v-if="item.reminder_type" size="small" color="blue">{{ getReminderTypeLabel(item.reminder_type) }}</a-tag>
              </div>
              <div class="notification-item-content">{{ item.content }}</div>
              <div class="notification-item-time">{{ formatNoticeTime(item.created_at) }}</div>
            </div>
          </div>
        </div>

        <div v-if="total > list.length" class="notification-load-more">
          <a-button type="link" :loading="loading" @click="loadMore">加载更多</a-button>
        </div>
      </a-spin>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getMyNotificationsApiV1NoticesMyGet,
  getUnreadCountApiV1NoticesUnreadCountGet,
  markAsReadApiV1NoticesNoticeIdReadPost,
  markAllAsReadApiV1NoticesReadAllPost,
} from '@/api/generated/notice-management/notice-management'
import type { NoticeResponse, NoticeUnreadCountResponse } from '@/api/generated/model'
import { formatNoticeTime, getReminderTypeLabel } from '@/utils/notice'

const activeTab = ref('reminder')
const loading = ref(false)
const list = ref<NoticeResponse[]>([])
const total = ref(0)
const page = ref(1)
const unreadCount = ref<NoticeUnreadCountResponse>({ total: 0, reminder: 0, system: 0 })

const hasUnread = ref(false)

async function fetchList(reset = false) {
  if (reset) {
    page.value = 1
    list.value = []
  }
  loading.value = true
  try {
    const data = await getMyNotificationsApiV1NoticesMyGet({
      page: page.value,
      size: 20,
      tab: activeTab.value,
    })
    const payload = data || { page: 1, size: 20, total: 0, items: [] }
    if (reset) {
      list.value = payload.items
    } else {
      list.value.push(...payload.items)
    }
    total.value = payload.total
  } catch { /* ignore */ } finally {
    loading.value = false
  }
}

async function fetchUnreadCount() {
  try {
    unreadCount.value = await getUnreadCountApiV1NoticesUnreadCountGet() || { total: 0, reminder: 0, system: 0 }
    hasUnread.value = (unreadCount.value.total ?? 0) > 0
  } catch { /* ignore */ }
}

function onTabChange() {
  fetchList(true)
}

function loadMore() {
  page.value++
  fetchList()
}

async function handleClickItem(item: NoticeResponse) {
  if (!item.is_read) {
    try {
      await markAsReadApiV1NoticesNoticeIdReadPost(item.id)
      item.is_read = true
      fetchUnreadCount()
    } catch { /* ignore */ }
  }
}

async function handleMarkAllRead() {
  try {
    await markAllAsReadApiV1NoticesReadAllPost({ tab: activeTab.value })
    list.value.forEach((item) => { item.is_read = true })
    fetchUnreadCount()
  } catch { /* ignore */ }
}

onMounted(() => {
  fetchList(true)
  fetchUnreadCount()
})
</script>

<style scoped>
.notification-page {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 16px;
}

.notification-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 400;
  color: var(--v2-text-primary);
  margin: 0;
}

.page-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 16px;
  border-radius: var(--v2-radius-sm);
  background: var(--v2-bg);
  padding: 4px;
}

.page-tab {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  font-size: 14px;
  color: var(--v2-text-secondary);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.page-tab.active {
  background: var(--v2-primary);
  color: #fff;
  font-weight: 500;
}

.notification-body {
  min-height: 300px;
}

.notification-empty {
  padding: 60px 0;
}

.notification-list {
  display: flex;
  flex-direction: column;
}

.notification-item {
  display: flex;
  gap: 12px;
  padding: 16px 12px;
  border-bottom: 1px solid var(--v2-border-light);
  cursor: pointer;
  transition: background 0.15s;
}

.notification-item:hover {
  background: var(--v2-bg);
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 7px;
  background: transparent;
}

.notification-item.unread .notification-item-dot {
  background: var(--v2-primary);
}

.notification-item-body {
  flex: 1;
  min-width: 0;
}

.notification-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.notification-item-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--v2-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-item.unread .notification-item-title {
  font-weight: 600;
}

.notification-item-content {
  font-size: 13px;
  color: var(--v2-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 4px;
}

.notification-item-time {
  font-size: 12px;
  color: var(--v2-text-muted);
}

.notification-load-more {
  text-align: center;
  padding: 12px 0;
}

@media (max-width: 768px) {
  .notification-page {
    padding: 16px 12px;
  }
  .page-title {
    font-size: 18px;
    width: 100%;
    text-align: center;
  }
  .notification-header {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
}
</style>
