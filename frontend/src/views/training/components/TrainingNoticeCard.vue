<template>
  <a-card title="班级公告" :bordered="false" style="margin-bottom:16px">
    <template #extra>
      <permissions-tooltip
        v-if="!isStudent"
        :allowed="canManageNotices"
        :tips="trainingManageTooltip"
        v-slot="{ disabled }"
      >
        <a-button type="link" size="small" style="padding:0" :disabled="disabled" @click="$emit('open-notice-modal')">
          发布公告
        </a-button>
      </permissions-tooltip>
    </template>
    <a-empty v-if="!notices || notices.length === 0" description="暂无公告" />
    <a-collapse v-else accordion :bordered="false" class="custom-notice-collapse sidebar-notice-collapse">
      <a-collapse-panel v-for="n in notices" :key="n.id" :header="n.title">
        <template #extra>
          <span class="notice-time">{{ n.time }}</span>
          <a-space style="margin-left: 12px" v-if="!isStudent" @click.stop>
            <permissions-tooltip
              :allowed="canManageNotices"
              :tips="trainingManageTooltip"
              v-slot="{ disabled }"
            >
              <a-button type="link" size="small" style="padding:0" :disabled="disabled" @click="$emit('edit-notice', n)">编辑</a-button>
            </permissions-tooltip>
            <permissions-tooltip
              :allowed="canManageNotices"
              :tips="trainingManageTooltip"
              v-slot="{ disabled }"
            >
              <a-popconfirm v-if="!disabled" title="确定删除该公告？" @confirm="$emit('delete-notice', n.id)">
                <a-button type="link" danger size="small" style="padding:0">删除</a-button>
              </a-popconfirm>
              <a-button v-else type="link" danger size="small" style="padding:0" :disabled="disabled">删除</a-button>
            </permissions-tooltip>
          </a-space>
        </template>
        <p class="notice-content">{{ n.content }}</p>
      </a-collapse-panel>
    </a-collapse>
  </a-card>
</template>

<script setup>
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

defineProps({
  notices: { type: Array, default: () => [] },
  isStudent: { type: Boolean, default: false },
  canManageNotices: { type: Boolean, default: false },
  trainingManageTooltip: { type: String, default: '' },
})

defineEmits(['open-notice-modal', 'edit-notice', 'delete-notice'])
</script>

<style scoped>
.custom-notice-collapse { background: transparent; }
.custom-notice-collapse :deep(.ant-collapse-item) { border-bottom: 1px solid #f0f0f0; background: #fafafa; margin-bottom: 8px; border-radius: 6px; overflow: hidden; }
.custom-notice-collapse :deep(.ant-collapse-header) { font-weight: 600; color: #1a1a1a; padding: 12px 16px; }
.notice-time { font-size: 12px; color: #888; font-weight: normal; }
.notice-content { font-size: 14px; color: #555; line-height: 1.6; margin: 0; padding: 4px 0; }
</style>
