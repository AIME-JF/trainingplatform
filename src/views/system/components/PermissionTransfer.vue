<template>
  <a-spin :spinning="loading">
    <a-transfer
      :data-source="transferDataSource"
      :target-keys="normalizedTargetKeys"
      :titles="['可选权限', '已选权限']"
      :show-search="true"
      :filter-option="filterPermissionOption"
      :render="renderPermissionItem"
      :disabled="disabled"
      :list-style="listStyle"
      @change="handleTransferChange"
    />
  </a-spin>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  permissions: {
    type: Array,
    default: () => [],
  },
  targetKeys: {
    type: Array,
    default: () => [],
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  height: {
    type: Number,
    default: 460,
  },
})

const emit = defineEmits(['update:targetKeys'])

const normalizedTargetKeys = computed(() =>
  (props.targetKeys || []).map((key) => String(key))
)

const transferDataSource = computed(() =>
  (props.permissions || []).map((permission) => {
    const code = permission?.code || '-'
    const name = permission?.name || permission?.description || '-'
    return {
      key: String(permission?.id),
      title: `${code}-${name}`,
      searchText: `${code} ${name}`.toLowerCase(),
    }
  })
)

const listStyle = computed(() => ({
  width: '45%',
  height: `${props.height}px`,
}))

function renderPermissionItem(item) {
  return item.title
}

function filterPermissionOption(inputValue, option) {
  const keyword = String(inputValue || '').trim().toLowerCase()
  if (!keyword) return true
  return String(option?.searchText || '').includes(keyword)
}

function handleTransferChange(nextTargetKeys) {
  emit('update:targetKeys', nextTargetKeys)
}
</script>
