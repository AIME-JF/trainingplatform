<template>
  <div class="chapter-row">
    <div class="chapter-header">
      <span class="chapter-badge">第 {{ index + 1 }} 章</span>
      <a-button v-if="canRemove" size="small" danger type="text" @click="$emit('remove')">
        <template #icon><DeleteOutlined /></template>删除
      </a-button>
    </div>

    <a-row :gutter="[10, 10]">
      <a-col :span="24">
        <a-input
          v-model:value="chapter.title"
          :placeholder="`章节名称，如：第${index + 1}章`"
        />
      </a-col>
      <a-col :span="14">
        <a-select
          v-model:value="chapter.resourceId"
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
          v-model:value="chapter.fileId"
          show-search
          allow-clear
          :disabled="!chapter.resourceId"
          :loading="fileLoading"
          :options="fileOptions"
          :filter-option="filterOption"
          :placeholder="chapter.resourceId ? '文件类资源默认原始文件，知识点无需再选文件' : '请先选择资源'"
          @change="handleFileChange"
        />
      </a-col>
    </a-row>

    <div class="chapter-meta">
      <span v-if="chapter.legacyFileOnly" class="chapter-meta-item legacy">
        当前章节保留了历史资源引用；如需调整，请改为选择知识库中的新资源。
      </span>
      <span v-else-if="summaryText" class="chapter-meta-item bound">
        已引用：{{ summaryText }}
      </span>
      <span v-else class="chapter-meta-item hint">
        每章从知识库选择当前用户自己的资源；文件类资源默认直接使用原始文件。
      </span>
      <a-tag v-if="chapter.contentType === 'video'" color="purple">视频</a-tag>
      <a-tag v-else-if="chapter.contentType === 'audio'" color="magenta">音频</a-tag>
      <a-tag v-else-if="chapter.contentType === 'document'" color="cyan">文档</a-tag>
      <a-tag v-else-if="chapter.contentType === 'image'" color="green">图片</a-tag>
      <a-tag v-else-if="chapter.contentType === 'knowledge'" color="blue">知识点</a-tag>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { DeleteOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  chapter: {
    type: Object,
    required: true,
  },
  index: {
    type: Number,
    required: true,
  },
  canRemove: {
    type: Boolean,
    default: false,
  },
  resourceOptions: {
    type: Array,
    default: () => [],
  },
  fileOptions: {
    type: Array,
    default: () => [],
  },
  resourceLoading: {
    type: Boolean,
    default: false,
  },
  fileLoading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['remove', 'change-resource', 'change-file'])

const summaryText = computed(() => {
  const chapter = props.chapter || {}
  if (!chapter.resourceTitle && !chapter.resourceFileLabel && !chapter.resourceFileName) {
    return ''
  }
  return [
    chapter.resourceTitle,
    chapter.resourceFileLabel,
    chapter.resourceFileName,
  ].filter(Boolean).join(' / ')
})

function filterOption(input, option) {
  return String(option?.label || '').toLowerCase().includes(String(input || '').toLowerCase())
}

function handleResourceChange(value) {
  emit('change-resource', value)
}

function handleFileChange(value) {
  emit('change-file', value)
}
</script>

<style scoped>
.chapter-row {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 12px;
  background: #fafbfc;
}

.chapter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.chapter-badge {
  background: var(--police-primary, #003087);
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
}

.chapter-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.chapter-meta-item {
  font-size: 12px;
}

.chapter-meta-item.bound {
  color: #003087;
}

.chapter-meta-item.hint {
  color: #666;
}

.chapter-meta-item.legacy {
  color: #8b6d00;
}
</style>
