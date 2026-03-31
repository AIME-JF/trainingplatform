<template>
  <div class="admission-scope-selector">
    <a-radio-group v-model:value="localScopeType" button-style="solid" class="scope-type-group">
      <a-radio-button value="all">全部</a-radio-button>
      <a-radio-button value="user" :disabled="!scopeAvailability.user.enabled">指定用户</a-radio-button>
      <a-radio-button value="department" :disabled="!scopeAvailability.department.enabled">指定部门</a-radio-button>
      <a-radio-button value="role" :disabled="!scopeAvailability.role.enabled">指定角色</a-radio-button>
    </a-radio-group>

    <div v-if="unavailableScopeTips.length" class="scope-permission-tip">
      {{ unavailableScopeTips.join('；') }}
    </div>

    <div class="scope-content">
      <div v-if="localScopeType === 'all'" class="scope-hint">
        {{ allHint }}
      </div>

      <template v-else>
        <a-select
          v-model:value="localScopeTargetIds"
          mode="multiple"
          allow-clear
          show-search
          :filter-option="false"
          :loading="loadingMap[localScopeType]"
          :options="currentOptions"
          :placeholder="currentPlaceholder"
          style="width: 100%"
          @search="handleSearch"
        />
        <div class="scope-hint">{{ currentHint }}</div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { listDepartments, listRoles, listUsers } from '@/api/learning-resource'
import { getUserDisplayName } from '@/utils/learning-resource'

interface SelectOption {
  value: number
  label: string
}

const props = withDefaults(defineProps<{
  scopeType?: string
  scopeTargetIds?: number[]
  userRole?: string
  allHint?: string
  userPlaceholder?: string
  departmentPlaceholder?: string
  rolePlaceholder?: string
  userHint?: string
  departmentHint?: string
  roleHint?: string
}>(), {
  scopeType: 'all',
  scopeTargetIds: () => [],
  userRole: 'student',
  allHint: '全部用户都可以查看。',
  userPlaceholder: '请选择用户',
  departmentPlaceholder: '请选择部门',
  rolePlaceholder: '请选择角色',
  userHint: '仅选中的用户可以查看。',
  departmentHint: '选中部门下的用户可以查看。',
  roleHint: '拥有选中角色的用户可以查看。',
})

const emit = defineEmits<{
  'update:scopeType': [value: string]
  'update:scopeTargetIds': [value: number[]]
}>()

const authStore = useAuthStore()

const localScopeType = ref(normalizeScopeType(props.scopeType))
const localScopeTargetIds = ref(normalizeTargetIds(props.scopeTargetIds))
const optionMap = reactive<Record<'user' | 'department' | 'role', SelectOption[]>>({
  user: [],
  department: [],
  role: [],
})
const loadingMap = reactive<Record<'user' | 'department' | 'role', boolean>>({
  user: false,
  department: false,
  role: false,
})
const searchTimerMap: Partial<Record<'user' | 'department' | 'role', ReturnType<typeof setTimeout>>> = {}

const scopeAvailability = computed(() => ({
  user: {
    enabled: authStore.hasPermission('GET_USERS'),
    tip: '无用户列表查看权限，不能指定用户范围',
  },
  department: {
    enabled: authStore.hasPermission('GET_DEPARTMENTS'),
    tip: '无部门列表查看权限，不能指定部门范围',
  },
  role: {
    enabled: authStore.hasPermission('GET_ROLES'),
    tip: '无角色列表查看权限，不能指定角色范围',
  },
}))

const unavailableScopeTips = computed(() => (
  (['user', 'department', 'role'] as const)
    .filter((key) => !scopeAvailability.value[key].enabled)
    .map((key) => scopeAvailability.value[key].tip)
))

const currentPlaceholder = computed(() => {
  if (localScopeType.value === 'user') return props.userPlaceholder
  if (localScopeType.value === 'department') return props.departmentPlaceholder
  if (localScopeType.value === 'role') return props.rolePlaceholder
  return ''
})

const currentHint = computed(() => {
  if (localScopeType.value === 'user') return props.userHint
  if (localScopeType.value === 'department') return props.departmentHint
  if (localScopeType.value === 'role') return props.roleHint
  return ''
})

const currentOptions = computed(() => {
  const scopeType = localScopeType.value
  if (scopeType === 'all') {
    return []
  }
  return mergeSelectedFallbackOptions(optionMap[scopeType], localScopeTargetIds.value, scopeType)
})

watch(() => props.scopeType, (value) => {
  const normalized = normalizeScopeType(value)
  if (normalized !== localScopeType.value) {
    localScopeType.value = normalized
  }
})

watch(() => props.scopeTargetIds, (value) => {
  const normalized = normalizeTargetIds(value)
  if (JSON.stringify(normalized) !== JSON.stringify(localScopeTargetIds.value)) {
    localScopeTargetIds.value = normalized
  }
})

watch(localScopeType, async (value) => {
  if (value !== 'all' && !scopeAvailability.value[value].enabled) {
    localScopeType.value = 'all'
    return
  }
  if (value === 'all') {
    localScopeTargetIds.value = []
  } else {
    await fetchOptions(value)
  }
  emit('update:scopeType', localScopeType.value)
  emit('update:scopeTargetIds', localScopeTargetIds.value)
}, { immediate: true })

watch(localScopeTargetIds, (value) => {
  emit('update:scopeTargetIds', normalizeTargetIds(value))
}, { deep: true })

function normalizeScopeType(value?: string) {
  return (['all', 'user', 'department', 'role'].includes(value || '') ? value : 'all') as 'all' | 'user' | 'department' | 'role'
}

function normalizeTargetIds(value?: number[]) {
  const seen = new Set<number>()
  return (value || [])
    .map((item) => Number(item))
    .filter((item) => Number.isInteger(item) && item > 0 && !seen.has(item) && seen.add(item))
}

function mergeSelectedFallbackOptions(
  baseOptions: SelectOption[],
  selectedIds: number[],
  scopeType: 'user' | 'department' | 'role',
) {
  const map = new Map<number, SelectOption>()
  for (const option of baseOptions) {
    map.set(option.value, option)
  }
  for (const id of selectedIds) {
    if (!map.has(id)) {
      map.set(id, {
        value: id,
        label: `${getScopePrefix(scopeType)}#${id}`,
      })
    }
  }
  return Array.from(map.values())
}

function getScopePrefix(scopeType: 'user' | 'department' | 'role') {
  if (scopeType === 'user') return '用户'
  if (scopeType === 'department') return '部门'
  return '角色'
}

function handleSearch(keyword: string) {
  const scopeType = localScopeType.value
  if (scopeType === 'all') {
    return
  }
  const timer = searchTimerMap[scopeType]
  if (timer) {
    clearTimeout(timer)
  }
  searchTimerMap[scopeType] = setTimeout(() => {
    void fetchOptions(scopeType, keyword)
  }, 250)
}

async function fetchOptions(scopeType: 'user' | 'department' | 'role', keyword = '') {
  loadingMap[scopeType] = true
  try {
    if (scopeType === 'user') {
      const response = await listUsers({
        page: 1,
        size: 10,
        role: props.userRole || undefined,
        search: keyword.trim() || undefined,
      })
      optionMap.user = (response.items || []).map((item) => ({
        value: item.id,
        label: getUserDisplayName(item),
      }))
      return
    }
    if (scopeType === 'department') {
      const response = await listDepartments({
        page: 1,
        size: 10,
        search: keyword.trim() || undefined,
      })
      optionMap.department = (response.items || []).map((item) => ({
        value: item.id,
        label: item.name || `部门#${item.id}`,
      }))
      return
    }
    const response = await listRoles({
      page: 1,
      size: 10,
      name: keyword.trim() || undefined,
    })
    optionMap.role = (response.items || []).map((item) => ({
      value: item.id,
      label: item.name || `角色#${item.id}`,
    }))
  } finally {
    loadingMap[scopeType] = false
  }
}
</script>

<style scoped>
.admission-scope-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scope-type-group {
  display: flex;
  flex-wrap: wrap;
}

.scope-permission-tip {
  color: var(--v2-warning);
  font-size: 12px;
}

.scope-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scope-hint {
  color: var(--v2-text-secondary);
  font-size: 12px;
  line-height: 1.6;
}
</style>
