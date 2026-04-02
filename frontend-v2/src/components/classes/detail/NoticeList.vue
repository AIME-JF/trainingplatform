<template>
  <div>
    <div class="section-header">
      <h3 class="section-label">公告通知</h3>
      <a-button v-if="canPublish" size="small" type="primary" @click="openNoticeForm()">
        <PlusOutlined /> 发布公告
      </a-button>
    </div>
    <a-empty v-if="!notices?.length" description="暂无公告" :image="simpleImage" />
    <div v-else class="notice-list">
      <div
        v-for="n in notices"
        :key="n.id"
        class="notice-card"
        @click="openNoticeDetail(n)"
      >
        <div class="notice-card-main">
          <h4 class="notice-card-title">{{ n.title }}</h4>
          <p class="notice-card-summary">{{ truncate(n.content, 60) }}</p>
        </div>
        <div class="notice-card-side">
          <span class="notice-card-author" v-if="n.author_name">{{ n.author_name }}</span>
          <span class="notice-card-time">{{ formatDate(n.created_at) }}</span>
        </div>
      </div>
    </div>

    <!-- 公告详情弹窗 -->
    <a-modal v-model:open="noticeDetailVisible" :title="noticeDetailData?.title" :footer="null" width="560px">
      <div v-if="noticeDetailData" class="notice-detail-modal">
        <div class="notice-detail-meta">
          <span v-if="noticeDetailData.author_name">{{ noticeDetailData.author_name }}</span>
          <span>{{ formatDateTime(noticeDetailData.created_at) }}</span>
        </div>
        <div class="notice-detail-content">{{ noticeDetailData.content }}</div>
      </div>
    </a-modal>

    <!-- 发布公告弹窗 -->
    <a-modal
      v-model:open="noticeFormVisible"
      title="发布公告"
      @ok="handleNoticeSubmit"
      :confirm-loading="noticeSubmitting"
      ok-text="发布"
    >
      <a-form layout="vertical" style="margin-top: 16px">
        <a-form-item label="标题" required>
          <a-input v-model:value="noticeForm.title" placeholder="请输入公告标题" :maxlength="200" />
        </a-form-item>
        <a-form-item label="内容" required>
          <a-textarea v-model:value="noticeForm.content" placeholder="请输入公告内容" :rows="5" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { Empty, message } from 'ant-design-vue'
import axiosInstance from '@/api/custom-instance'
import type { NoticeItem } from './types'

interface Props {
  notices: NoticeItem[]
  canPublish: boolean
  trainingId: number | string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

const simpleImage = Empty.PRESENTED_IMAGE_SIMPLE

// 公告详情
const noticeDetailVisible = ref(false)
const noticeDetailData = ref<NoticeItem | null>(null)

// 发布公告表单
const noticeFormVisible = ref(false)
const noticeSubmitting = ref(false)
const noticeForm = ref({ title: '', content: '' })

function openNoticeDetail(n: NoticeItem) {
  noticeDetailData.value = n
  noticeDetailVisible.value = true
}

function openNoticeForm() {
  noticeForm.value = { title: '', content: '' }
  noticeFormVisible.value = true
}

async function handleNoticeSubmit() {
  if (!noticeForm.value.title.trim() || !noticeForm.value.content.trim()) {
    message.warning('请填写标题和内容')
    return
  }
  noticeSubmitting.value = true
  try {
    const payload = {
      title: noticeForm.value.title.trim(),
      content: noticeForm.value.content.trim(),
      type: 'training',
      training_id: Number(props.trainingId),
    }
    await axiosInstance.post('/notices', payload)
    message.success('公告发布成功')
    noticeFormVisible.value = false
    emit('refresh')
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '发布失败')
  } finally {
    noticeSubmitting.value = false
  }
}

function formatDate(val: string | null | undefined): string {
  if (!val) return '-'
  return String(val).slice(0, 10)
}

function formatDateTime(val: string | null | undefined): string {
  if (!val) return '-'
  return String(val).slice(0, 16).replace('T', ' ')
}

function truncate(text: string | undefined | null, len: number): string {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-header .section-label { margin-bottom: 0; }

.section-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin-bottom: 12px;
}

.notice-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.notice-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-radius: var(--v2-radius-sm);
  border: 1px solid var(--v2-border-light);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.notice-card:hover {
  background: var(--v2-bg);
  border-color: var(--v2-border);
}

.notice-card-main { flex: 1; min-width: 0; }

.notice-card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin: 0 0 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notice-card-summary {
  font-size: 13px;
  color: var(--v2-text-muted);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notice-card-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}

.notice-card-author { font-size: 12px; color: var(--v2-text-secondary); }
.notice-card-time { font-size: 11px; color: var(--v2-text-muted); }

.notice-detail-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: var(--v2-text-muted);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--v2-border-light);
}

.notice-detail-content {
  font-size: 14px;
  color: var(--v2-text-primary);
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
