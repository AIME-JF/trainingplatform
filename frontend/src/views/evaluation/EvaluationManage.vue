<template>
  <div class="evaluation-manage-page">
    <div class="page-header">
      <h2>评价管理</h2>
    </div>

    <a-card :bordered="false">
      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="dimensions" tab="维度配置">
          <DimensionConfigTab />
        </a-tab-pane>
        <a-tab-pane key="tasks" tab="评价任务">
          <TaskListTab />
        </a-tab-pane>
        <a-tab-pane key="records" tab="评价记录">
          <RecordListTab />
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DimensionConfigTab from './components/DimensionConfigTab.vue'
import TaskListTab from './components/TaskListTab.vue'
import RecordListTab from './components/RecordListTab.vue'

const activeTab = ref('dimensions')
</script>

<style scoped>
.evaluation-manage-page { padding: 0; }
.page-header { margin-bottom: 16px; }
.page-header h2 { margin: 0; color: #001234; }
</style>
