<template>
  <a-drawer
    :open="open"
    class="resource-comments-drawer"
    :class="{ mobile: isMobile }"
    :placement="drawerPlacement"
    :width="drawerWidth"
    :height="drawerHeight"
    :closable="!isMobile"
    :body-style="{ padding: 0 }"
    @update:open="handleOpenChange"
  >
    <template #title>
      <div class="comment-drawer-title" :class="{ mobile: isMobile }">
        <span v-if="isMobile" class="comment-sheet-handle" />
        <strong>资源评论</strong>
      </div>
    </template>

    <div class="comment-drawer-body">
      <div v-if="resourceTitle" class="comment-drawer-head">
        <strong>{{ resourceTitle }}</strong>
        <span>{{ formatCount(commentCount) }} 条评论</span>
      </div>

      <div class="comment-list-wrapper">
        <a-spin :spinning="loading">
          <a-empty v-if="!comments.length && !loading" description="还没有评论，先说点什么吧" />

          <div v-else class="comment-list">
            <div v-for="item in comments" :key="item.id" class="comment-card">
              <div class="comment-card-head">
                <div class="comment-user-meta">
                  <strong>{{ item.user_name || `用户#${item.user_id}` }}</strong>
                  <span>{{ formatDateTime(item.created_at) }}</span>
                </div>
                <a-popconfirm
                  v-if="item.can_delete"
                  title="确认删除这条评论吗？"
                  ok-text="删除"
                  cancel-text="取消"
                  @confirm="emit('delete', item.id)"
                >
                  <a-button type="link" danger size="small">删除</a-button>
                </a-popconfirm>
              </div>
              <p class="comment-card-content">{{ item.content }}</p>
            </div>
          </div>
        </a-spin>
      </div>

      <div class="comment-editor">
        <a-textarea
          :value="draft"
          :rows="4"
          :maxlength="1000"
          show-count
          placeholder="写下你的评论"
          @update:value="handleDraftChange"
        />
        <div class="comment-editor-actions">
          <span>当前支持查看评论、发表评论、删除自己的评论。</span>
          <a-button type="primary" :loading="submitting" @click="emit('submit')">发表评论</a-button>
        </div>
      </div>
    </div>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ResourceCommentResponse } from '@/api/learning-resource'
import { useMobile } from '@/composables/useMobile'
import { formatDateTime } from '@/utils/learning-resource'

interface Props {
  open: boolean
  resourceTitle?: string
  commentCount?: number | null
  comments?: ResourceCommentResponse[]
  loading?: boolean
  submitting?: boolean
  draft?: string
}

const props = withDefaults(defineProps<Props>(), {
  resourceTitle: '',
  commentCount: 0,
  comments: () => [],
  loading: false,
  submitting: false,
  draft: '',
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  'update:draft': [value: string]
  submit: []
  delete: [commentId: number]
}>()

const { isMobile } = useMobile()

const drawerPlacement = computed(() => isMobile.value ? 'bottom' : 'right')
const drawerWidth = computed(() => isMobile.value ? undefined : 420)
const drawerHeight = computed(() => isMobile.value ? '56dvh' : undefined)

function handleOpenChange(value: boolean) {
  emit('update:open', value)
}

function handleDraftChange(value: string) {
  emit('update:draft', value)
}

function formatCount(value?: number | null) {
  const count = Number(value || 0)
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}w`
  }
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k`
  }
  return String(count)
}
</script>

<style scoped>
.comment-drawer-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.comment-drawer-title strong {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.comment-drawer-title.mobile {
  width: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.comment-sheet-handle {
  width: 44px;
  height: 5px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.56);
}

.resource-comments-drawer :deep(.ant-drawer-header) {
  border-bottom: none;
  background: transparent;
}

.comment-drawer-body {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 1) 100%);
}

.comment-drawer-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 18px 20px 10px;
  border-bottom: none;
  background: transparent;
}

.comment-drawer-head strong {
  font-size: 18px;
  line-height: 1.25;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.comment-drawer-head span {
  color: rgba(71, 85, 105, 0.84);
  font-size: 13px;
}

.comment-list-wrapper {
  flex: 1;
  min-height: 0;
  padding: 6px 20px 18px;
  overflow-y: auto;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.comment-card {
  padding: 18px 0 16px;
  border: none;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.comment-card + .comment-card {
  box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.16);
}

.comment-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.comment-user-meta {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.comment-user-meta strong {
  font-size: 16px;
  line-height: 1.25;
  color: #0f172a;
  font-weight: 700;
}

.comment-user-meta span {
  color: rgba(100, 116, 139, 0.86);
  font-size: 12px;
}

.comment-card-head :deep(.ant-btn-link) {
  height: auto !important;
  padding: 0 !important;
  color: #ef4444 !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  line-height: 1.4 !important;
}

.comment-card-content {
  margin: 0;
  color: rgba(15, 23, 42, 0.94);
  font-size: 15px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
}

.comment-editor {
  padding: 16px 20px calc(18px + env(safe-area-inset-bottom));
  border-top: none;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 0.92) 14%, rgba(255, 255, 255, 0.98) 100%);
  backdrop-filter: blur(16px);
}

.comment-editor :deep(.ant-input-textarea) {
  display: block;
}

.comment-editor :deep(.ant-input-textarea-show-count::after) {
  margin-top: 8px;
  color: rgba(100, 116, 139, 0.9);
  font-size: 12px;
}

.comment-editor :deep(.ant-input-textarea textarea) {
  min-height: 112px !important;
  padding: 16px 18px !important;
  border: none !important;
  border-radius: 20px !important;
  background: rgba(248, 250, 252, 0.96) !important;
  box-shadow:
    inset 0 0 0 1px rgba(148, 163, 184, 0.14),
    0 14px 32px rgba(15, 23, 42, 0.06);
  color: #0f172a !important;
  line-height: 1.75 !important;
  resize: none;
}

.comment-editor :deep(.ant-input-textarea textarea::placeholder) {
  color: rgba(148, 163, 184, 0.96);
}

.comment-editor :deep(.ant-input-textarea textarea:hover),
.comment-editor :deep(.ant-input-textarea textarea:focus) {
  background: #fff !important;
  box-shadow:
    inset 0 0 0 1px rgba(59, 130, 246, 0.16),
    0 18px 40px rgba(37, 99, 235, 0.08);
}

.comment-editor-actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: 14px;
  margin-top: 14px;
  color: rgba(100, 116, 139, 0.92);
  font-size: 12px;
}

.comment-editor-actions span {
  line-height: 1.65;
}

.comment-editor-actions :deep(.ant-btn.ant-btn-primary) {
  min-width: 118px;
  height: 46px !important;
  padding: 0 22px !important;
  border: none !important;
  border-radius: 16px !important;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
  box-shadow: 0 14px 28px rgba(37, 99, 235, 0.22);
  font-size: 14px !important;
  font-weight: 700 !important;
}

.comment-editor-actions :deep(.ant-btn.ant-btn-primary:hover),
.comment-editor-actions :deep(.ant-btn.ant-btn-primary:focus) {
  background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
  box-shadow: 0 18px 34px rgba(37, 99, 235, 0.26);
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .resource-comments-drawer.mobile :deep(.ant-drawer-content-wrapper) {
    box-shadow: 0 -20px 44px rgba(15, 23, 42, 0.28);
  }

  .resource-comments-drawer.mobile :deep(.ant-drawer-content) {
    border-radius: 26px 26px 0 0;
    overflow: hidden;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.99), rgba(248, 250, 252, 1) 100%);
  }

  .resource-comments-drawer.mobile :deep(.ant-drawer-header) {
    padding: 12px 18px 10px;
    background: rgba(255, 255, 255, 0.98);
  }

  .resource-comments-drawer.mobile :deep(.ant-drawer-body) {
    background: transparent;
  }

  .comment-drawer-head {
    padding-top: 14px;
    gap: 4px;
    background: transparent;
  }

  .comment-list-wrapper,
  .comment-editor,
  .comment-drawer-head {
    padding-left: 16px;
    padding-right: 16px;
  }

  .comment-editor-actions {
    grid-template-columns: 1fr;
    align-items: stretch;
  }

  .comment-editor-actions :deep(.ant-btn.ant-btn-primary) {
    width: 100%;
  }
}
</style>
