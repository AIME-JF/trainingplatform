<template>
  <a-input
    :value="value"
    :placeholder="placeholder"
    :allow-clear="allowClear"
    :disabled="disabled"
    class="resource-search-input"
    @update:value="handleUpdate"
    @pressEnter="emitSearch"
  >
    <template #prefix>
      <SearchOutlined />
    </template>
  </a-input>
</template>

<script setup lang="ts">
import { SearchOutlined } from '@ant-design/icons-vue'

interface Props {
  value?: string
  placeholder?: string
  allowClear?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  value: '',
  placeholder: '请输入关键词搜索',
  allowClear: true,
  disabled: false,
})

const emit = defineEmits<{
  'update:value': [value: string]
  search: [value: string]
}>()

function handleUpdate(value: string) {
  emit('update:value', value)
}

function emitSearch() {
  emit('search', props.value || '')
}
</script>

<style scoped>
.resource-search-input {
  width: 100%;
}

.resource-search-input :deep(.ant-input-prefix) {
  margin-inline-end: 10px;
  color: rgba(35, 49, 81, 0.5);
}

.resource-search-input :deep(.ant-input-prefix .anticon) {
  font-size: 16px;
}
</style>
