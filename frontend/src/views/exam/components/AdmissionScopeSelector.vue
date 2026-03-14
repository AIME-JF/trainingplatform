<template>
  <div class="admission-scope-selector">
    <a-radio-group v-model:value="localScopeType" button-style="solid" class="scope-type-group">
      <a-radio-button value="all">全部</a-radio-button>
      <a-radio-button value="user">指定用户</a-radio-button>
      <a-radio-button value="department">指定部门</a-radio-button>
      <a-radio-button value="role">指定角色</a-radio-button>
    </a-radio-group>

    <div class="scope-content">
      <div v-if="localScopeType === 'all'" class="scope-hint">
        全体学员都可以参加该准入考试。
      </div>

      <template v-else>
        <a-select
          v-model:value="localScopeTargetIds"
          mode="multiple"
          allow-clear
          show-search
          option-filter-prop="label"
          style="width: 100%"
          :loading="loadingMap[localScopeType]"
          :options="currentOptions"
          :placeholder="currentPlaceholder"
        />
        <div class="scope-hint">{{ currentHint }}</div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { getUsers } from '@/api/user'
import { getDepartmentList } from '@/api/department'
import { getRoleList } from '@/api/role'

const props = defineProps({
  scopeType: {
    type: String,
    default: 'all',
  },
  scopeTargetIds: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['update:scopeType', 'update:scopeTargetIds'])

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

const loadedMap = reactive({
  user: false,
  department: false,
  role: false,
})

const currentOptions = computed(() => optionMap[localScopeType.value] || [])
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

function normalizeScopeType(value) {
  return ['all', 'user', 'department', 'role'].includes(value) ? value : 'all'
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

function syncLocalTargetIds(value) {
  const normalized = normalizeTargetIds(value)
  if (JSON.stringify(normalized) !== JSON.stringify(localScopeTargetIds.value)) {
    localScopeTargetIds.value = normalized
  }
}

async function ensureOptions(scopeType) {
  if (!['user', 'department', 'role'].includes(scopeType) || loadedMap[scopeType] || loadingMap[scopeType]) {
    return
  }

  loadingMap[scopeType] = true
  try {
    if (scopeType === 'user') {
      const result = await getUsers({ size: -1, role: 'student' })
      optionMap.user = (result.items || []).map((item) => ({
        value: item.id,
        label: item.policeId ? `${item.nickname || item.username}（${item.policeId}）` : (item.nickname || item.username),
      }))
    }
    if (scopeType === 'department') {
      const result = await getDepartmentList({ size: -1 })
      optionMap.department = (result.items || []).map((item) => ({
        value: item.id,
        label: item.name,
      }))
    }
    if (scopeType === 'role') {
      const result = await getRoleList({ size: -1 })
      optionMap.role = (result.items || [])
        .filter((item) => item.isActive !== false)
        .map((item) => ({
          value: item.id,
          label: item.name,
        }))
    }
    loadedMap[scopeType] = true
  } catch {
    optionMap[scopeType] = []
  } finally {
    loadingMap[scopeType] = false
  }
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
    await ensureOptions(normalized)
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
    emit('update:scopeTargetIds', normalized)
  },
  { deep: true },
)
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

.scope-hint {
  font-size: 12px;
  color: #8c8c8c;
}
</style>
