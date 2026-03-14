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

function compareByCode(a, b) {
  return String(a?.code || '').localeCompare(
    String(b?.code || ''),
    'zh-Hans-CN',
    { numeric: true, sensitivity: 'base' }
  )
}

const sortedPermissions = computed(() =>
  [...(props.permissions || [])].sort(compareByCode)
)

const keyOrderMap = computed(() => {
  const orderMap = new Map()
  sortedPermissions.value.forEach((permission, index) => {
    orderMap.set(String(permission?.id), index)
  })
  return orderMap
})

function sortTargetKeys(keys) {
  return [...(keys || [])]
    .map((key) => String(key))
    .sort((a, b) => {
      const aOrder = keyOrderMap.value.get(a)
      const bOrder = keyOrderMap.value.get(b)
      if (aOrder === undefined && bOrder === undefined) return a.localeCompare(b)
      if (aOrder === undefined) return 1
      if (bOrder === undefined) return -1
      return aOrder - bOrder
    })
}

const normalizedTargetKeys = computed(() =>
  sortTargetKeys(props.targetKeys)
)

const transferDataSource = computed(() =>
  sortedPermissions.value.map((permission) => {
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
  emit('update:targetKeys', sortTargetKeys(nextTargetKeys))
}
</script>
