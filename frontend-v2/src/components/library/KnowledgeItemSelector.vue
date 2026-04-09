<template>
  <a-select
    :value="modelValue"
    mode="multiple"
    allow-clear
    :disabled="disabled"
    :loading="loading"
    :placeholder="placeholder"
    :max-tag-count="maxTagCount"
    :not-found-content="notFoundContent"
    option-filter-prop="label"
    class="knowledge-item-selector"
    @change="handleChange"
  >
    <a-select-option
      v-for="item in options"
      :key="item.id"
      :value="item.id"
      :label="buildOptionLabel(item)"
    >
      <div class="selector-option">
        <div class="selector-option-main">
          <span class="selector-option-title">{{ item.title }}</span>
          <span class="selector-option-type">{{ getItemTypeLabel(item) }}</span>
        </div>
        <span class="selector-option-meta">
          {{ item.is_public ? '公共' : '私人' }}{{ item.owner_name ? ` · ${item.owner_name}` : '' }}
        </span>
      </div>
    </a-select-option>
  </a-select>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { listAccessibleAssistantItems, type LibraryItemResponse } from '@/api/library'
import { getLibraryTypeLabel } from '@/utils/library-browser'

withDefaults(defineProps<{
  modelValue?: number[]
  placeholder?: string
  disabled?: boolean
  maxTagCount?: number | 'responsive'
}>(), {
  modelValue: () => [],
  placeholder: '选择知识点或可解析资料',
  disabled: false,
  maxTagCount: 'responsive',
})

const emit = defineEmits<{
  'update:modelValue': [value: number[]]
}>()

const loading = ref(false)
const options = ref<LibraryItemResponse[]>([])

const notFoundContent = computed(() => {
  if (loading.value) {
    return '正在加载知识点与资料...'
  }
  return '当前没有可访问的知识点或可解析资料，请先创建知识点，或上传可解析的文档/图片资料'
})

onMounted(() => {
  void fetchOptions()
})

async function fetchOptions() {
  loading.value = true
  try {
    options.value = await listAccessibleAssistantItems()
  } catch (error) {
    options.value = []
    message.error(error instanceof Error ? error.message : '加载知识点与资料列表失败')
  } finally {
    loading.value = false
  }
}

function handleChange(value: Array<number | string>) {
  emit(
    'update:modelValue',
    (value || [])
      .map((item) => Number(item))
      .filter((item) => Number.isFinite(item) && item > 0),
  )
}

function getItemTypeLabel(item: LibraryItemResponse) {
  const baseLabel = getLibraryTypeLabel(item.content_type)
  if (item.content_type === 'knowledge') {
    return baseLabel
  }
  return `${baseLabel}资料`
}

function buildOptionLabel(item: LibraryItemResponse) {
  return `${item.title} ${getItemTypeLabel(item)} ${item.owner_name || ''}`.trim()
}
</script>

<style scoped>
.knowledge-item-selector {
  width: 100%;
}

.selector-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.selector-option-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.selector-option-title {
  color: var(--v2-text-primary);
}

.selector-option-type {
  color: var(--v2-primary);
  font-size: 12px;
  white-space: nowrap;
}

.selector-option-meta {
  color: var(--v2-text-muted);
  font-size: 12px;
  white-space: nowrap;
}
</style>
