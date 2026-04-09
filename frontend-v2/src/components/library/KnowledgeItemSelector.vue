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
        <span class="selector-option-title">{{ item.title }}</span>
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
import { listAccessibleKnowledgeItems, type LibraryItemResponse } from '@/api/library'

withDefaults(defineProps<{
  modelValue?: number[]
  placeholder?: string
  disabled?: boolean
  maxTagCount?: number | 'responsive'
}>(), {
  modelValue: () => [],
  placeholder: '选择知识点',
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
    return '正在加载知识点...'
  }
  return '当前没有可访问的知识点，请检查是否已发布公共资源或创建了自己的私人知识点'
})

onMounted(() => {
  void fetchOptions()
})

async function fetchOptions() {
  loading.value = true
  try {
    const response = await listAccessibleKnowledgeItems()
    options.value = response.items || []
  } catch (error) {
    options.value = []
    message.error(error instanceof Error ? error.message : '加载知识点列表失败')
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

function buildOptionLabel(item: LibraryItemResponse) {
  return `${item.title}${item.owner_name ? ` · ${item.owner_name}` : ''}`
}
</script>

<style scoped>
.knowledge-item-selector {
  width: 100%;
}

.selector-option {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.selector-option-title {
  color: var(--v2-text-primary);
}

.selector-option-meta {
  color: var(--v2-text-muted);
  font-size: 12px;
}
</style>
