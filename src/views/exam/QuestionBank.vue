<template>
  <div class="question-bank-page">
    <div class="page-header">
      <h2>题库管理</h2>
      <a-space>
        <a-button @click="$router.push('/ai/question-gen')">
          <template #icon><RobotOutlined /></template>AI 生成题目
        </a-button>
        <a-button type="primary">
          <template #icon><PlusOutlined /></template>手动添加
        </a-button>
      </a-space>
    </div>

    <!-- 统计 -->
    <a-row :gutter="16" style="margin-bottom:20px">
      <a-col :span="6" v-for="s in stats" :key="s.label">
        <a-card :bordered="false" size="small" style="text-align:center">
          <div style="font-size:24px;font-weight:700;color:var(--police-primary)">{{ s.value }}</div>
          <div style="font-size:12px;color:#888">{{ s.label }}</div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 过滤 -->
    <a-card :bordered="false" style="margin-bottom:16px">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-input-search v-model:value="searchText" placeholder="搜索题目内容..." allow-clear />
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterType" style="width:100%">
            <a-select-option value="all">全部题型</a-select-option>
            <a-select-option value="single">单选题</a-select-option>
            <a-select-option value="multi">多选题</a-select-option>
            <a-select-option value="judge">判断题</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="4">
          <a-select v-model:value="filterDiff" style="width:100%">
            <a-select-option value="all">全部难度</a-select-option>
            <a-select-option value="easy">简单</a-select-option>
            <a-select-option value="medium">中等</a-select-option>
            <a-select-option value="hard">困难</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <!-- 题目列表 -->
    <a-card :bordered="false">
      <a-table
        :dataSource="filteredQuestions"
        :columns="columns"
        :row-selection="rowSelection"
        size="small"
        :pagination="{ pageSize: 10, showTotal: t => `共 ${t} 道题` }"
        :expandable="{ expandedRowRender }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <a-tag :color="typeColors[record.type]" size="small">{{ typeLabels[record.type] }}</a-tag>
          </template>
          <template v-if="column.key === 'difficulty'">
            <a-tag :color="diffColors[record.difficulty]" size="small">{{ diffLabels[record.difficulty] }}</a-tag>
          </template>
          <template v-if="column.key === 'stem'">
            <div class="q-stem-preview">{{ record.stem }}</div>
          </template>
          <template v-if="column.key === 'action'">
            <a-space size="small">
              <a-button type="link" size="small">编辑</a-button>
              <a-button type="link" size="small" danger>删除</a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { PlusOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { MOCK_QUESTIONS } from '@/mock/exams'

const searchText = ref('')
const filterType = ref('all')
const filterDiff = ref('all')

const typeColors = { single: 'blue', multi: 'purple', judge: 'orange' }
const typeLabels = { single: '单选', multi: '多选', judge: '判断' }
const diffColors = { easy: 'green', medium: 'orange', hard: 'red' }
const diffLabels = { easy: '简单', medium: '中等', hard: '困难' }

const allQ = MOCK_QUESTIONS.map((q, i) => ({ ...q, key: i, difficulty: ['easy', 'medium', 'hard'][i % 3] }))

const filteredQuestions = computed(() => {
  let list = [...allQ]
  if (searchText.value) list = list.filter(q => q.stem.includes(searchText.value))
  if (filterType.value !== 'all') list = list.filter(q => q.type === filterType.value)
  if (filterDiff.value !== 'all') list = list.filter(q => q.difficulty === filterDiff.value)
  return list
})

const stats = [
  { label: '题目总数', value: allQ.length },
  { label: '单选题', value: allQ.filter(q => q.type === 'single').length },
  { label: '多选题', value: allQ.filter(q => q.type === 'multi').length },
  { label: '判断题', value: allQ.filter(q => q.type === 'judge').length },
]

const rowSelection = { type: 'checkbox' }

const columns = [
  { title: '题目内容', key: 'stem', ellipsis: true },
  { title: '题型', key: 'type', width: 80 },
  { title: '难度', key: 'difficulty', width: 80 },
  { title: '操作', key: 'action', width: 100 },
]

const expandedRowRender = ({ record }) => {
  return `答案：${record.answer}　解析：${record.explanation || '无'}`
}
</script>

<style scoped>
.question-bank-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--police-primary); }
.q-stem-preview { max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; }
</style>
