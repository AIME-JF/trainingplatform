<template>
  <div>
    <div class="section-header" style="margin-bottom:16px">
      <h4 style="margin:0">课程变更记录</h4>
      <a-button size="small" @click="$emit('refresh')">刷新</a-button>
    </div>
    <a-table
      :data-source="courseChangeLogs"
      :loading="courseChangeLogsLoading"
      :pagination="{ pageSize: 10, showSizeChanger: false }"
      row-key="id"
      size="small"
    >
      <a-table-column title="时间" key="createdAt" width="180">
        <template #default="{ record }">
          {{ formatDateTime(record.createdAt, '-') }}
        </template>
      </a-table-column>
      <a-table-column title="操作人" key="actor" width="140">
        <template #default="{ record }">
          {{ record.actorName || '系统' }}
        </template>
      </a-table-column>
      <a-table-column title="来源" key="source" width="180">
        <template #default="{ record }">
          <a-space size="small">
            <a-tag>{{ courseChangeSourceLabelMap[record.source] || record.source }}</a-tag>
            <a-tag :color="courseChangeActionColorMap[record.action] || 'default'">
              {{ courseChangeActionLabelMap[record.action] || record.action }}
            </a-tag>
          </a-space>
        </template>
      </a-table-column>
      <a-table-column title="对象" key="target" width="260">
        <template #default="{ record }">
          <div>{{ courseChangeTargetLabelMap[record.targetType] || record.targetType }} · {{ record.courseName || '未命名课程' }}</div>
          <div v-if="record.sessionLabel" style="color:#999">{{ record.sessionLabel }}</div>
        </template>
      </a-table-column>
      <a-table-column title="摘要" data-index="summary" key="summary" />
    </a-table>
  </div>
</template>

<script setup>
defineProps({
  courseChangeLogs: { type: Array, default: () => [] },
  courseChangeLogsLoading: { type: Boolean, default: false },
  formatDateTime: { type: Function, required: true },
  courseChangeSourceLabelMap: { type: Object, default: () => ({}) },
  courseChangeActionColorMap: { type: Object, default: () => ({}) },
  courseChangeActionLabelMap: { type: Object, default: () => ({}) },
  courseChangeTargetLabelMap: { type: Object, default: () => ({}) },
})

defineEmits(['refresh'])
</script>

<style scoped>
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
</style>
