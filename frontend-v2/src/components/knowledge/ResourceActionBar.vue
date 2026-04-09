<template>
  <div class="resource-action-bar" :class="`theme-${theme}`">
    <button
      type="button"
      class="action-item"
      :class="{ active: liked }"
      :disabled="liking"
      @click="emit('like')"
    >
      <component :is="liked ? HeartFilled : HeartOutlined" class="action-icon" />
      <span class="action-label">{{ liked ? '已点赞' : '点赞' }}</span>
      <span class="action-count">{{ formatCount(likeCount) }}</span>
    </button>

    <button
      type="button"
      class="action-item"
      @click="emit('comment')"
    >
      <MessageOutlined class="action-icon" />
      <span class="action-label">评论</span>
      <span class="action-count">{{ formatCount(commentCount) }}</span>
    </button>

    <button
      type="button"
      class="action-item"
      :disabled="sharing"
      @click="emit('share')"
    >
      <ShareAltOutlined class="action-icon" />
      <span class="action-label">转发</span>
      <span class="action-count">{{ formatCount(shareCount) }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import {
  HeartFilled,
  HeartOutlined,
  MessageOutlined,
  ShareAltOutlined,
} from '@ant-design/icons-vue'

interface Props {
  liked?: boolean
  likeCount?: number | null
  commentCount?: number | null
  shareCount?: number | null
  liking?: boolean
  sharing?: boolean
  theme?: 'default' | 'dark'
}

withDefaults(defineProps<Props>(), {
  liked: false,
  likeCount: 0,
  commentCount: 0,
  shareCount: 0,
  liking: false,
  sharing: false,
  theme: 'default',
})

const emit = defineEmits<{
  like: []
  comment: []
  share: []
}>()

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
.resource-action-bar {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  width: 100%;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  min-height: 58px;
  padding: 10px 8px;
  border-radius: 16px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(245, 247, 250, 0.96);
  color: #334155;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    background 0.2s ease,
    border-color 0.2s ease,
    color 0.2s ease,
    box-shadow 0.2s ease;
}

.action-item:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(59, 130, 246, 0.2);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.08);
}

.action-item:disabled {
  cursor: not-allowed;
  opacity: 0.68;
}

.action-item.active {
  color: #dc2626;
}

.action-icon {
  font-size: 18px;
}

.action-label {
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
}

.action-count {
  font-size: 12px;
  line-height: 1;
  opacity: 0.72;
}

.theme-dark .action-item {
  border-color: rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.9);
}

.theme-dark .action-item:hover:not(:disabled) {
  border-color: rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 18px 34px rgba(0, 0, 0, 0.18);
}

.theme-dark .action-item.active {
  color: #ff8fa3;
}

@media (max-width: 768px) {
  .resource-action-bar {
    gap: 8px;
  }

  .action-item {
    min-height: 54px;
    border-radius: 14px;
    padding: 8px 6px;
  }

  .action-label {
    font-size: 12px;
  }

  .action-count {
    font-size: 11px;
  }
}
</style>
