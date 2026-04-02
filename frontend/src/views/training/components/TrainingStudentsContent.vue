<template>
  <div>
    <div class="section-header" style="margin-bottom:16px">
      <a-input-search :value="studentSearch" placeholder="搜索学员..." class="student-search-input" @update:value="$emit('update:studentSearch', $event)" />
      <a-space v-if="showActionButtons">
        <permissions-tooltip
          :allowed="canManageEnrollmentApplications"
          :tips="trainingManageTooltip"
          v-slot="{ disabled }"
        >
          <a-badge :dot="pendingEnrollmentCount > 0" :offset="[6, -2]">
            <a-button size="small" :disabled="disabled" @click="$emit('open-enrollment-application-modal')">
              申请管理<span v-if="pendingEnrollmentCount > 0">（{{ pendingEnrollmentCount }}）</span>
            </a-button>
          </a-badge>
        </permissions-tooltip>
        <permissions-tooltip
          :allowed="canManageStudents"
          :tips="trainingManageTooltip"
          v-slot="{ disabled }"
        >
          <a-button size="small" :disabled="disabled" @click="$emit('open-student-import-modal')">
            导入学员
          </a-button>
        </permissions-tooltip>
        <permissions-tooltip
          :allowed="canManageStudents"
          :tips="trainingManageTooltip"
          v-slot="{ disabled }"
        >
          <a-button type="primary" size="small" :disabled="disabled" @click="$emit('open-student-modal')">
            <template #icon><PlusOutlined /></template>添加学员
          </a-button>
        </permissions-tooltip>
      </a-space>
    </div>
    <a-table :data-source="filteredStudents" :columns="studentColumnsWithAction" size="small" :pagination="{ pageSize: 10 }">
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'name'">
          <a-button type="link" size="small" style="padding:0" @click="$emit('go-trainee-detail', record.key)">
            {{ record.name }}
          </a-button>
        </template>
        <template v-if="column.key === 'checkin'">
          <span :style="{ color: record.checkinRate >= 90 ? '#52c41a' : record.checkinRate >= 70 ? '#faad14' : '#ff4d4f' }">
            {{ record.checkinRate }}%
          </span>
        </template>
        <template v-if="column.key === 'action'">
          <permissions-tooltip
            :allowed="canManageStudents"
            :tips="trainingManageTooltip"
            v-slot="{ disabled }"
          >
            <a-popconfirm v-if="!disabled" title="确定移除该学员？" @confirm="$emit('remove-student', record.key)">
              <a-button size="small" type="link" danger>移除</a-button>
            </a-popconfirm>
            <a-button v-else size="small" type="link" danger :disabled="disabled">移除</a-button>
          </permissions-tooltip>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup>
import { PlusOutlined } from '@ant-design/icons-vue'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

defineProps({
  studentSearch: { type: String, default: '' },
  filteredStudents: { type: Array, default: () => [] },
  studentColumnsWithAction: { type: Array, default: () => [] },
  canManageEnrollmentApplications: { type: Boolean, default: false },
  canManageStudents: { type: Boolean, default: false },
  showActionButtons: { type: Boolean, default: true },
  trainingManageTooltip: { type: String, default: '' },
  pendingEnrollmentCount: { type: Number, default: 0 },
})

defineEmits([
  'update:studentSearch',
  'open-enrollment-application-modal',
  'open-student-import-modal',
  'open-student-modal',
  'go-trainee-detail',
  'remove-student',
])
</script>

<style scoped>
.section-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; }
.student-search-input { width: 240px; }
</style>
