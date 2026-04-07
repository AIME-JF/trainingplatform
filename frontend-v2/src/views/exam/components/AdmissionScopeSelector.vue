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
        全体学员都可以参加该考试。
      </div>

      <template v-else>
        <a-select
          v-model:value="localScopeTargetIds"
          mode="multiple"
          allow-clear
          show-search
          :filter-option="false"
          style="width: 100%"
          :loading="loadingMap[localScopeType]"
          :options="currentOptions"
          :placeholder="currentPlaceholder"
          @search="handleSearch"
          @focus="handleFocus"
        />
        <div class="scope-hint">{{ currentHint }}</div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getUsersApiV1UsersGet } from '@/api/generated/user-management/user-management'
import { getDepartmentListApiV1DepartmentsListGet } from '@/api/generated/department-management/department-management'
import { getRoleListApiV1RolesListGet } from '@/api/generated/role-management/role-management'

type ScopeType = 'all' | 'user' | 'department' | 'role'
type ScopeOption = { value: number; label: string }

const props = defineProps({
  scopeType: {
    type: String,
    default: 'all',
  },
  scopeTargetIds: {
    type: Array as () => number[],
    default: () => [],
  },
})

const emit = defineEmits<{
  'update:scopeType': [value: ScopeType]
  'update:scopeTargetIds': [value: number[]]
}>()

const authStore = useAuthStore()

const localScopeType = ref<ScopeType>('all')
const localScopeTargetIds = ref<number[]>([])

const optionMap = reactive<Record<'user' | 'department' | 'role', ScopeOption[]>>({
  user: [],
  department: [],
  role: [],
})

const selectedOptionMap = reactive<Record<'user' | 'department' | 'role', ScopeOption[]>>({
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
    label: '无用户列表查看权限，不能指定用户范围',
  },
  department: {
    enabled: authStore.hasPermission('GET_DEPARTMENTS'),
    label: '无部门列表查看权限，不能指定部门范围',
  },
  role: {
    enabled: authStore.hasPermission('GET_ROLES'),
    label: '无角色列表查看权限，不能指定角色范围',
  },
}))

const unavailableScopeTips = computed(() => (
  (['user', 'department', 'role'] as const)
    .filter((scopeType) => !scopeAvailability.value[scopeType].enabled)
    .map((scopeType) => scopeAvailability.value[scopeType].label)
))

const currentOptions = computed(() => {
  if (localScopeType.value === 'all') return []
  return mergeOptions(optionMap[localScopeType.value], selectedOptionMap[localScopeType.value])
})

const currentPlaceholder = computed(() => {
  if (localScopeType.value === 'user') return '请选择学员'
  if (localScopeType.value === 'department') return '请选择部门'
  if (localScopeType.value === 'role') return '请选择角色'
  return ''
})

const currentHint = computed(() => {
  if (localScopeType.value === 'user') return '仅选中的学员可以参加考试。'
  if (localScopeType.value === 'department') return '选中部门下的学员可以参加考试。'
  if (localScopeType.value === 'role') return '拥有选中角色的学员可以参加考试。'
  return ''
})

function normalizeScopeType(value?: string): ScopeType {
  return ['all', 'user', 'department', 'role'].includes(value || '') ? (value as ScopeType) : 'all'
}

function normalizeTargetIds(value: number[] = []) {
  return [...new Set(
    value
      .map((item) => Number(item))
      .filter((item) => Number.isInteger(item) && item > 0),
  )]
}

function mergeOptions(primary: ScopeOption[] = [], extra: ScopeOption[] = []) {
  const map = new Map<number, ScopeOption>()
  for (const item of [...primary, ...extra]) {
    if (!item?.value || !item?.label) continue
    map.set(item.value, item)
  }
  return [...map.values()]
}

function rememberCurrentSelections(scopeType: 'user' | 'department' | 'role') {
  const selected = mergeOptions(optionMap[scopeType], selectedOptionMap[scopeType])
    .filter((item) => localScopeTargetIds.value.includes(item.value))
  if (selected.length) {
    selectedOptionMap[scopeType] = mergeOptions(selectedOptionMap[scopeType], selected)
  }
}

async function loadScopeOptions(scopeType: 'user' | 'department' | 'role', keyword = '') {
  if (!scopeAvailability.value[scopeType].enabled) return
  loadingMap[scopeType] = true
  try {
    if (scopeType === 'user') {
      const res = await getUsersApiV1UsersGet({ page: 1, size: 20, role: 'student', search: keyword || undefined })
      optionMap.user = ((res as any)?.items || res?.items || []).map((item: any) => ({
        value: item.id,
        label: item.id_card_number
          ? `${item.nickname || item.username}（${item.id_card_number}）`
          : (item.nickname || item.username || `用户#${item.id}`),
      }))
    } else if (scopeType === 'department') {
      const res = await getDepartmentListApiV1DepartmentsListGet({ page: 1, size: 20, search: keyword || undefined })
      optionMap.department = ((res as any)?.items || res?.items || []).map((item: any) => ({
        value: item.id,
        label: item.name || `部门#${item.id}`,
      }))
    } else {
      const res = await getRoleListApiV1RolesListGet({ page: 1, size: 20, name: keyword || undefined, is_active: true })
      optionMap.role = ((res as any)?.items || res?.items || []).map((item: any) => ({
        value: item.id,
        label: item.name || `角色#${item.id}`,
      }))
    }
    rememberCurrentSelections(scopeType)
  } finally {
    loadingMap[scopeType] = false
  }
}

function handleFocus() {
  if (localScopeType.value === 'all') return
  if (!optionMap[localScopeType.value].length) {
    void loadScopeOptions(localScopeType.value)
  }
}

function handleSearch(keyword: string) {
  if (localScopeType.value === 'all') return
  if (searchTimerMap[localScopeType.value]) {
    clearTimeout(searchTimerMap[localScopeType.value])
  }
  searchTimerMap[localScopeType.value] = setTimeout(() => {
    void loadScopeOptions(localScopeType.value as 'user' | 'department' | 'role', keyword)
  }, 250)
}

watch(
  () => props.scopeType,
  (value) => {
    const normalized = normalizeScopeType(value)
    if (normalized !== localScopeType.value) {
      localScopeType.value = normalized
    }
  },
  { immediate: true },
)

watch(
  () => props.scopeTargetIds,
  (value) => {
    const normalized = normalizeTargetIds(value)
    if (JSON.stringify(normalized) !== JSON.stringify(localScopeTargetIds.value)) {
      localScopeTargetIds.value = normalized
    }
  },
  { immediate: true },
)

watch(localScopeType, (value) => {
  if (value !== 'all' && !scopeAvailability.value[value].enabled) {
    localScopeType.value = 'all'
    return
  }
  if (value === 'all') {
    localScopeTargetIds.value = []
  } else {
    void loadScopeOptions(value)
  }
  emit('update:scopeType', value)
})

watch(localScopeTargetIds, (value) => {
  const normalized = normalizeTargetIds(value)
  if (JSON.stringify(normalized) !== JSON.stringify(value)) {
    localScopeTargetIds.value = normalized
    return
  }
  if (localScopeType.value !== 'all') {
    rememberCurrentSelections(localScopeType.value)
  }
  emit('update:scopeTargetIds', normalized)
})

onBeforeUnmount(() => {
  for (const timer of Object.values(searchTimerMap)) {
    if (timer) clearTimeout(timer)
  }
})
</script>

<style scoped>
.admission-scope-selector {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.scope-type-group {
  width: fit-content;
}

.scope-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scope-permission-tip {
  color: var(--v2-text-secondary);
  font-size: 12px;
}

.scope-hint {
  color: var(--v2-text-secondary);
  font-size: 12px;
}
</style>
