<template>
  <div class="chapter-row">
    <div class="chapter-header">
      <span class="chapter-badge">第 {{ index + 1 }} 章</span>
      <a-button v-if="canRemove" size="small" danger type="text" @click="$emit('remove')">删除</a-button>
    </div>

    <a-row :gutter="[10, 10]">
      <a-col :span="24">
        <a-input v-model:value="chapter.title" :placeholder="`章节名称，如：第${index + 1}章`" />
      </a-col>
      <a-col :span="14">
        <a-select
          v-model:value="chapter.resource_id"
          show-search
          allow-clear
          :loading="resourceLoading"
          :options="resourceOptions"
          :filter-option="filterOption"
          placeholder="请选择当前用户自己的资源"
          @change="handleResourceChange"
        />
      </a-col>
      <a-col :span="10">
        <a-select
          v-model:value="chapter.file_id"
          show-search
          allow-clear
          :disabled="!chapter.resource_id"
          :loading="fileLoading"
          :options="fileOptions"
          :filter-option="filterOption"
          :placeholder="chapter.resource_id ? '文件类资源默认原始文件，知识点无需再选文件' : '请先选择资源'"
          @change="handleFileChange"
        />
      </a-col>
    </a-row>

    <div class="chapter-meta">
      <span v-if="summaryText" class="chapter-meta-item bound">已引用：{{ summaryText }}</span>
      <span v-else class="chapter-meta-item hint">每章从资源库选择当前用户自己的资源；文件类资源默认直接使用原始文件。</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface SelectOption {
  value: number
  label: string
}

interface ChapterModel {
  title: string
  file_id: number | null
  resource_id: number | null
  legacy_resource_id?: number | null
  resource_title?: string
  resource_file_name?: string
  resource_file_label?: string
  content_type?: string | null
}

const props = withDefaults(defineProps<{
  chapter: ChapterModel
  index: number
  canRemove?: boolean
  resourceOptions?: SelectOption[]
  fileOptions?: SelectOption[]
  resourceLoading?: boolean
  fileLoading?: boolean
}>(), {
  canRemove: false,
  resourceOptions: () => [],
  fileOptions: () => [],
  resourceLoading: false,
  fileLoading: false,
})

const emit = defineEmits<{
  remove: []
  'change-resource': [value: number | null]
  'change-file': [value: number | null]
}>()

const summaryText = computed(() => {
  const chapter = props.chapter || {}
  return [
    chapter.resource_title,
    chapter.resource_file_label,
    chapter.resource_file_name,
  ].filter(Boolean).join(' / ')
})

function filterOption(input: string, option?: SelectOption) {
  return String(option?.label || '').toLowerCase().includes(String(input || '').toLowerCase())
}

function handleResourceChange(value?: number | string | null) {
  emit('change-resource', typeof value === 'number' ? value : null)
}

function handleFileChange(value?: number | string | null) {
  emit('change-file', typeof value === 'number' ? value : null)
}
</script>

<style scoped>
.chapter-row {
  border: 1px solid var(--v2-border);
  border-radius: var(--v2-radius);
  padding: 14px;
  margin-bottom: 12px;
  background: var(--v2-bg-card);
}

.chapter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.chapter-badge {
  background: var(--v2-primary);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--v2-radius-full);
}

.chapter-meta {
  margin-top: 10px;
  color: var(--v2-text-secondary);
  font-size: 12px;
}

.chapter-meta-item.bound {
  color: var(--v2-primary);
}
</style>
