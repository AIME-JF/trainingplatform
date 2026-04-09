<template>
  <div class="resource-action-group" :class="{ compact }">
    <a-button class="action-btn" :size="buttonSize" @click="emit('view', record.id)">查看</a-button>
    <a-button class="action-btn" :size="buttonSize" @click="emit('workflow', record.id)">轨迹</a-button>

    <PermissionsTooltip
      v-if="['draft', 'rejected'].includes(record.status)"
      :allowed="canSubmitReview"
      :block="compact"
      tips="需要同时具备 CREATE_RESOURCE 和 SUBMIT_RESOURCE_REVIEW 权限"
    >
      <template #default="{ disabled }">
        <a-button class="action-btn primary-btn" :size="buttonSize" :disabled="disabled" @click="emit('submit-review', record.id)">
          提交审核
        </a-button>
      </template>
    </PermissionsTooltip>

    <PermissionsTooltip
      v-if="['offline', 'rejected'].includes(record.status)"
      :allowed="canManage"
      :block="compact"
      tips="仅资源上传者或具备 UPDATE_RESOURCE / VIEW_RESOURCE_ALL 权限可执行该操作"
    >
      <template #default="{ disabled }">
        <a-button class="action-btn" :size="buttonSize" :disabled="disabled" @click="emit('publish', record.id)">
          重新发布
        </a-button>
      </template>
    </PermissionsTooltip>

    <PermissionsTooltip
      v-if="record.status === 'published'"
      :allowed="canManage"
      :block="compact"
      tips="仅资源上传者或具备 UPDATE_RESOURCE / VIEW_RESOURCE_ALL 权限可执行该操作"
    >
      <template #default="{ disabled }">
        <a-button class="action-btn danger-btn" :size="buttonSize" :disabled="disabled" @click="emit('offline', record.id)">
          下线
        </a-button>
      </template>
    </PermissionsTooltip>

    <PermissionsTooltip
      :allowed="canManage"
      :block="compact"
      tips="仅资源上传者或具备 UPDATE_RESOURCE / VIEW_RESOURCE_ALL 权限可执行该操作"
    >
      <template #default="{ disabled }">
        <a-popconfirm v-if="!disabled" title="确认删除该资源吗？" @confirm="emit('delete', record.id)">
          <a-button class="action-btn danger-btn" :size="buttonSize">删除</a-button>
        </a-popconfirm>
        <a-button v-else class="action-btn danger-btn" :size="buttonSize" :disabled="disabled">删除</a-button>
      </template>
    </PermissionsTooltip>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ResourceListItemResponse } from '@/api/learning-resource'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

interface Props {
  record: ResourceListItemResponse
  canSubmitReview: boolean
  canManage: boolean
  compact?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  compact: false,
})

const emit = defineEmits<{
  view: [resourceId: number]
  workflow: [resourceId: number]
  'submit-review': [resourceId: number]
  publish: [resourceId: number]
  offline: [resourceId: number]
  delete: [resourceId: number]
}>()

const buttonSize = computed<'middle' | 'small'>(() => props.compact ? 'middle' : 'small')
</script>

<style scoped>
.resource-action-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.resource-action-group.compact {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.resource-action-group.compact :deep(.permission-tooltip-wrapper-block) {
  width: 100%;
}

.action-btn {
  min-width: 72px;
  border-radius: 999px !important;
  border-color: rgba(255, 255, 255, 0.12) !important;
  background: rgba(255, 255, 255, 0.04) !important;
  color: rgba(255, 255, 255, 0.88) !important;
  box-shadow: none !important;
}

.action-btn:hover:not(:disabled),
.action-btn:focus:not(:disabled) {
  border-color: rgba(255, 255, 255, 0.2) !important;
  background: rgba(255, 255, 255, 0.08) !important;
  color: #fff !important;
}

.primary-btn {
  border-color: rgba(76, 110, 245, 0.24) !important;
  background: rgba(76, 110, 245, 0.18) !important;
  color: #dfe7ff !important;
}

.primary-btn:hover:not(:disabled),
.primary-btn:focus:not(:disabled) {
  border-color: rgba(98, 130, 255, 0.34) !important;
  background: rgba(98, 130, 255, 0.24) !important;
  color: #fff !important;
}

.danger-btn {
  border-color: rgba(255, 124, 124, 0.2) !important;
  background: rgba(255, 124, 124, 0.12) !important;
  color: #ffb4b4 !important;
}

.danger-btn:hover:not(:disabled),
.danger-btn:focus:not(:disabled) {
  border-color: rgba(255, 124, 124, 0.34) !important;
  background: rgba(255, 124, 124, 0.18) !important;
  color: #ffd6d6 !important;
}

.resource-action-group.compact .action-btn {
  width: 100%;
  min-width: 0;
  height: 40px !important;
}
</style>
