<template>
  <a-card title="常用入口" :bordered="false" style="margin-bottom:16px">
    <div class="quick-ops-grid">
      <a-button
        v-if="trainingData.status === 'active' && !isStudent"
        class="span-2"
        type="primary"
        @click="$emit('global-checkin')"
      >
        <template #icon><QrcodeOutlined /></template>开班/上课签到
      </a-button>
      <a-button
        v-if="trainingData.status === 'active' && isStudent && isEnrolled"
        class="span-2"
        type="primary"
        @click="$emit('global-checkin')"
      >
        <template #icon><QrcodeOutlined /></template>扫码签到
      </a-button>
      <a-button @click="$emit('view-schedule')">
        <template #icon><CalendarOutlined /></template>查看日程
      </a-button>
      <permissions-tooltip
        v-if="!isStudent"
        :allowed="canAiSchedule"
        :tips="aiScheduleTooltip"
        block
        v-slot="{ disabled }"
      >
        <a-button :disabled="disabled" @click="$emit('open-ai-schedule')">AI排课建议</a-button>
      </permissions-tooltip>
      <a-button @click="$emit('change-tab', 'schedule')">课程安排</a-button>
      <a-button v-if="!isStudent" @click="$emit('change-tab', 'students')">学员名单</a-button>
      <a-button @click="$emit('change-tab', 'exams')">考试安排</a-button>
      <permissions-tooltip
        v-if="!isStudent"
        :allowed="canEdit"
        :tips="trainingManageTooltip"
        block
        v-slot="{ disabled }"
      >
        <a-button :disabled="disabled" @click="$emit('open-edit')">
          <template #icon><EditOutlined /></template>编辑班级
        </a-button>
      </permissions-tooltip>
      <permissions-tooltip
        v-if="!isStudent"
        :allowed="canExportStudents"
        :tips="trainingManageTooltip"
        block
        v-slot="{ disabled }"
      >
        <a-button :disabled="disabled" @click="$emit('export-students')">
          <template #icon><DownloadOutlined /></template>导出学员
        </a-button>
      </permissions-tooltip>
    </div>
  </a-card>
</template>

<script setup>
import { CalendarOutlined, QrcodeOutlined, EditOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

defineProps({
  trainingData: { type: Object, required: true },
  isStudent: { type: Boolean, default: false },
  isEnrolled: { type: Boolean, default: false },
  canEdit: { type: Boolean, default: false },
  canAiSchedule: { type: Boolean, default: false },
  canExportStudents: { type: Boolean, default: false },
  trainingManageTooltip: { type: String, default: '' },
  aiScheduleTooltip: { type: String, default: '' },
})

defineEmits(['global-checkin', 'view-schedule', 'open-ai-schedule', 'change-tab', 'open-edit', 'export-students'])
</script>

<style scoped>
.quick-ops-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.quick-ops-grid :deep(.ant-btn) { width: 100%; }
.quick-ops-grid .span-2 { grid-column: span 2; }
</style>
