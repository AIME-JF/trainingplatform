<template>
  <div class="ai-task-page">
    <div class="page-header">
      <div>
        <h2>{{ title }}</h2>
        <p class="page-sub">{{ subtitle }}</p>
      </div>
      <a-tag color="blue">{{ tagText }}</a-tag>
    </div>

    <a-tabs :active-key="activeTab" class="task-tabs" @update:activeKey="emit('update:activeTab', $event)">
      <a-tab-pane key="create" tab="创建任务">
        <a-card :bordered="false" class="tab-card">
          <slot name="create" />
        </a-card>
      </a-tab-pane>

      <a-tab-pane key="list" tab="任务列表">
        <a-row :gutter="[16, 16]">
          <a-col :xs="24" :xl="8">
            <a-card :title="listTitle" :bordered="false" class="task-list-card">
              <template #extra>
                <a-button type="link" size="small" @click="emit('refresh-tasks')">刷新</a-button>
              </template>

              <a-list :data-source="taskList" :loading="taskLoading">
                <template #renderItem="{ item }">
                  <a-list-item
                    class="task-list-item"
                    :class="{ active: item.id === activeTaskId }"
                    @click="emit('select-task', item.id)"
                  >
                    <a-list-item-meta>
                      <template #title>
                        <slot name="task-title" :item="item">
                          {{ item.taskName }}
                        </slot>
                      </template>
                      <template #description>
                        <slot name="task-description" :item="item" />
                      </template>
                    </a-list-item-meta>
                    <a-tag :color="statusColors[item.status] || 'default'">
                      {{ statusLabels[item.status] || item.status }}
                    </a-tag>
                  </a-list-item>
                </template>
              </a-list>

              <a-empty v-if="!taskLoading && !taskList.length" :description="emptyText" />
            </a-card>
          </a-col>

          <a-col :xs="24" :xl="16">
            <a-card :bordered="false" class="task-detail-card">
              <slot name="detail" />
            </a-card>
          </a-col>
        </a-row>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, required: true },
  tagText: { type: String, default: '任务流' },
  activeTab: { type: String, default: 'create' },
  taskList: { type: Array, default: () => [] },
  taskLoading: { type: Boolean, default: false },
  activeTaskId: { type: Number, default: null },
  statusLabels: { type: Object, required: true },
  statusColors: { type: Object, required: true },
  listTitle: { type: String, default: '任务列表' },
  emptyText: { type: String, default: '暂无任务' },
})

const emit = defineEmits(['update:activeTab', 'refresh-tasks', 'select-task'])
</script>

<style scoped>
.ai-task-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #001234;
}

.page-sub {
  margin: 6px 0 0;
  color: #8c8c8c;
  font-size: 13px;
}

.task-tabs :deep(.ant-tabs-nav) {
  margin-bottom: 16px;
}

.tab-card,
.task-list-card,
.task-detail-card {
  border-radius: 12px;
}

.task-list-item {
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s, border-color 0.2s;
  padding-left: 10px;
  padding-right: 10px;
  border: 1px solid transparent;
}

.task-list-item:hover {
  background: #f7f9ff;
}

.task-list-item.active {
  background: #eef4ff;
  border-color: rgba(0, 48, 135, 0.12);
}

.task-detail-card {
  min-height: 100%;
}
</style>
