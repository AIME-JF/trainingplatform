<template>
  <div class="admission-scope-selector">
    <a-radio-group v-model:value="localScopeType" button-style="solid" class="scope-type-group">
      <a-radio-button value="all">全部</a-radio-button>
      <a-radio-button value="user" :disabled="!scopeAvailabilityMap.user.enabled">指定用户</a-radio-button>
      <a-radio-button value="department" :disabled="!scopeAvailabilityMap.department.enabled">指定部门</a-radio-button>
      <a-radio-button value="role" :disabled="!scopeAvailabilityMap.role.enabled">指定角色</a-radio-button>
    </a-radio-group>
    <div v-if="unavailableScopeTips.length" class="scope-permission-tip">
      {{ unavailableScopeTips.join('；') }}
    </div>

    <div class="scope-content">
      <div v-if="localScopeType === 'all'" class="scope-hint">
        {{ props.allHint }}
      </div>

      <template v-else>
        <a-select
          v-model:value="localScopeTargetIds"
          mode="multiple"
          allow-clear
          show-search
          :filter-option="false"
          style="width: 100%"
          :disabled="!isScopeSelectable(localScopeType)"
          :loading="loadingMap[localScopeType]"
          :options="currentOptions"
          :placeholder="currentPlaceholder"
          @search="handleSearch"
        />
        <div class="scope-hint">{{ currentHint }}</div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch, onBeforeUnmount } from 'vue'
import { getUser, getUsers } from '@/api/user'
import { getDepartmentDetail, getDepartmentList } from '@/api/department'
import { getRoleDetail, getRoleList } from '@/api/role'
import { useAuthStore } from '@/stores/auth'

const REMOTE_PAGE_SIZE = 10

const props = defineProps({
  scopeType: {
    type: String,
    default: 'all',
  },
  scopeTargetIds: {
    type: Array,
    default: () => [],
  },
  userRole: {
    type: String,
    default: 'student',
  },
  allHint: {
    type: String,
    default: '全体学员都可以参加该准入考试。',
  },
  userPlaceholder: {
    type: String,
    default: '请选择学员',
  },
  departmentPlaceholder: {
    type: String,
    default: '请选择部门',
  },
  rolePlaceholder: {
    type: String,
    default: '请选择角色',
  },
  userHint: {
    type: String,
    default: '仅选中的学员可以参加考试。',
  },
  departmentHint: {
    type: String,
    default: '选中部门下的学员可以参加考试。',
  },
  roleHint: {
    type: String,
    default: '拥有选中角色的学员可以参加考试。',
  },
})

const emit = defineEmits(['update:scopeType', 'update:scopeTargetIds'])
const authStore = useAuthStore()

const localScopeType = ref('all')
const localScopeTargetIds = ref([])

const optionMap = reactive({
  user: [],
  department: [],
  role: [],
})

const loadingMap = reactive({
  user: false,
  department: false,
  role: false,
})

const selectedOptionMap = reactive({
  user: [],
  department: [],
  role: [],
})

const requestIdMap = reactive({
  user: 0,
  department: 0,
  role: 0,
})

const searchTimerMap = {
  user: null,
  department: null,
  role: null,
}

function getScopedOptions(scopeType) {
  return mergeOptions(optionMap[scopeType], selectedOptionMap[scopeType])
}

const scopeAvailabilityMap = computed(() => ({
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
  ['user', 'department', 'role']
    .filter((scopeType) => !scopeAvailabilityMap.value[scopeType].enabled)
    .map((scopeType) => scopeAvailabilityMap.value[scopeType].label)
))

const currentOptions = computed(() => getScopedOptions(localScopeType.value))
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

function normalizeScopeType(value) {
  return ['all', 'user', 'department', 'role'].includes(value) ? value : 'all'
}

function isScopeSelectable(scopeType) {
  if (scopeType === 'all') {
    return true
  }
  return !!scopeAvailabilityMap.value[scopeType]?.enabled
}

function normalizeTargetIds(value) {
  const normalized = []
  const seen = new Set()
  for (const rawItem of value || []) {
    const item = Number(rawItem)
    if (!Number.isInteger(item) || item <= 0 || seen.has(item)) {
      continue
    }
    seen.add(item)
    normalized.push(item)
  }
  return normalized
}

function normalizeOptions(options) {
  const normalized = []
  const seen = new Set()
  for (const option of options || []) {
    const value = Number(option?.value)
    const label = String(option?.label || '').trim()
    if (!Number.isInteger(value) || value <= 0 || !label || seen.has(value)) {
      continue
    }
    seen.add(value)
    normalized.push({ value, label })
  }
  return normalized
}

function mergeOptions(primary = [], extra = []) {
  return normalizeOptions([...(primary || []), ...(extra || [])])
}

function syncLocalTargetIds(value) {
  const normalized = normalizeTargetIds(value)
  if (JSON.stringify(normalized) !== JSON.stringify(localScopeTargetIds.value)) {
    localScopeTargetIds.value = normalized
  }
}

function buildUserOption(item) {
  if (!item?.id) {
    return null
  }
  return {
    value: item.id,
    label: item.idCardNumber ? `${item.nickname || item.username}（${item.idCardNumber}）` : (item.nickname || item.username || `用户#${item.id}`),
  }
}

function buildDepartmentOption(item) {
  if (!item?.id) {
    return null
  }
  return {
    value: item.id,
    label: item.name || `部门#${item.id}`,
  }
}

function buildRoleOption(item) {
  if (!item?.id) {
    return null
  }
  return {
    value: item.id,
    label: item.name || `角色#${item.id}`,
  }
}

function findKnownOption(scopeType, id) {
  const options = getScopedOptions(scopeType)
  return options.find((item) => item.value === id) || null
}

function rememberSelectedOptions(scopeType, options) {
  if (!['user', 'department', 'role'].includes(scopeType)) {
    return
  }
  selectedOptionMap[scopeType] = mergeOptions(selectedOptionMap[scopeType], options)
}

function rememberCurrentSelections(scopeType, selectedIds) {
  const options = getScopedOptions(scopeType).filter((item) => selectedIds.includes(item.value))
  if (options.length) {
    rememberSelectedOptions(scopeType, options)
  }
}

async function fetchOptions(scopeType, keyword = '') {
  if (!['user', 'department', 'role'].includes(scopeType) || !isScopeSelectable(scopeType)) {
    return
  }

  const requestId = requestIdMap[scopeType] + 1
  requestIdMap[scopeType] = requestId
  loadingMap[scopeType] = true

  try {
    let options = []
    const normalizedKeyword = String(keyword || '').trim()

    if (scopeType === 'user') {
      const params = {
        page: 1,
        size: REMOTE_PAGE_SIZE,
        search: normalizedKeyword || undefined,
      }
      if (props.userRole) {
        params.role = props.userRole
      }
      const result = await getUsers(params)
      options = (result.items || []).map(buildUserOption).filter(Boolean)
    }

    if (scopeType === 'department') {
      const result = await getDepartmentList({
        page: 1,
        size: REMOTE_PAGE_SIZE,
        search: normalizedKeyword || undefined,
      })
      options = (result.items || []).map(buildDepartmentOption).filter(Boolean)
    }

    if (scopeType === 'role') {
      const result = await getRoleList({
        page: 1,
        size: REMOTE_PAGE_SIZE,
        name: normalizedKeyword || undefined,
      })
      options = (result.items || [])
        .filter((item) => item.isActive !== false)
        .map(buildRoleOption)
        .filter(Boolean)
    }

    if (requestId !== requestIdMap[scopeType]) {
      return
    }
    optionMap[scopeType] = normalizeOptions(options)
    rememberCurrentSelections(scopeType, normalizeTargetIds(localScopeTargetIds.value))
  } catch {
    if (requestId === requestIdMap[scopeType]) {
      optionMap[scopeType] = []
    }
  } finally {
    if (requestId === requestIdMap[scopeType]) {
      loadingMap[scopeType] = false
    }
  }
}

async function fetchOptionById(scopeType, id) {
  if (!isScopeSelectable(scopeType)) {
    return null
  }
  if (scopeType === 'user') {
    return buildUserOption(await getUser(id))
  }
  if (scopeType === 'department') {
    return buildDepartmentOption(await getDepartmentDetail(id))
  }
  if (scopeType === 'role') {
    return buildRoleOption(await getRoleDetail(id))
  }
  return null
}

async function ensureSelectedOptions(scopeType, targetIds) {
  if (!['user', 'department', 'role'].includes(scopeType) || !isScopeSelectable(scopeType)) {
    return
  }

  const missingIds = normalizeTargetIds(targetIds).filter((id) => !findKnownOption(scopeType, id))
  if (!missingIds.length) {
    return
  }

  const results = await Promise.allSettled(missingIds.map((id) => fetchOptionById(scopeType, id)))
  const options = results
    .filter((item) => item.status === 'fulfilled' && item.value)
    .map((item) => item.value)
  if (options.length) {
    rememberSelectedOptions(scopeType, options)
  }
}

function handleSearch(value) {
  const scopeType = localScopeType.value
  if (!['user', 'department', 'role'].includes(scopeType) || !isScopeSelectable(scopeType)) {
    return
  }

  if (searchTimerMap[scopeType]) {
    clearTimeout(searchTimerMap[scopeType])
  }
  searchTimerMap[scopeType] = setTimeout(() => {
    fetchOptions(scopeType, value).catch(() => {})
  }, 300)
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
    syncLocalTargetIds(value)
    if (['user', 'department', 'role'].includes(localScopeType.value)) {
      ensureSelectedOptions(localScopeType.value, value).catch(() => {})
    }
  },
  { immediate: true },
)

watch(
  localScopeType,
  async (value, oldValue) => {
    const normalized = normalizeScopeType(value)
    if (normalized !== value) {
      localScopeType.value = normalized
      return
    }
    emit('update:scopeType', normalized)
    if (normalized === 'all') {
      if (localScopeTargetIds.value.length) {
        localScopeTargetIds.value = []
      }
      emit('update:scopeTargetIds', [])
      return
    }
    if (oldValue && oldValue !== normalized && localScopeTargetIds.value.length) {
      localScopeTargetIds.value = []
      emit('update:scopeTargetIds', [])
    }
    await ensureSelectedOptions(normalized, localScopeTargetIds.value)
    await fetchOptions(normalized)
  },
  { immediate: true },
)

watch(
  localScopeTargetIds,
  (value) => {
    const normalized = normalizeTargetIds(value)
    if (JSON.stringify(normalized) !== JSON.stringify(value)) {
      localScopeTargetIds.value = normalized
      return
    }
    if (['user', 'department', 'role'].includes(localScopeType.value)) {
      rememberCurrentSelections(localScopeType.value, normalized)
      ensureSelectedOptions(localScopeType.value, normalized).catch(() => {})
    }
    emit('update:scopeTargetIds', normalized)
  },
  { deep: true },
)

onBeforeUnmount(() => {
  Object.values(searchTimerMap).forEach((timer) => {
    if (timer) {
      clearTimeout(timer)
    }
  })
})
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

.scope-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scope-permission-tip,
.scope-hint {
  font-size: 12px;
  color: #8c8c8c;
}
</style>
