<template>
  <div class="permission-manager">
    <!-- 筛选栏 -->
    <div class="pm-toolbar">
      <a-input-search
        v-model:value="searchText"
        placeholder="搜索权限名称或编码..."
        style="width: 300px"
        allow-clear
      />
      <a-select
        v-model:value="filterGroup"
        placeholder="全部权限组"
        style="width: 200px"
        allow-clear
      >
        <a-select-option v-for="g in groupList" :key="g.groupKey" :value="g.groupKey">{{ g.groupName }}</a-select-option>
      </a-select>
      <a-button type="primary" :disabled="disabled" @click="showAddModal = true">
        <PlusOutlined /> 添加权限
      </a-button>
      <a-button :disabled="assignedPermissions.length === 0 || !resourceId" :loading="exporting" @click="handleExport">
        <ExportOutlined /> 导出权限
      </a-button>
      <a-upload
        :before-upload="handleImportFile"
        :show-upload-list="false"
        accept=".xlsx"
        :disabled="disabled || !resourceId"
      >
        <a-button :disabled="disabled || !resourceId" :loading="importing">
          <ImportOutlined /> 导入权限
        </a-button>
      </a-upload>
    </div>

    <!-- 已分配权限列表 -->
    <a-spin :spinning="loading">
      <a-table
        :data-source="filteredAssigned"
        :columns="assignedColumns"
        size="small"
        :pagination="{ pageSize: 12, showTotal: (total) => `共 ${total} 项` }"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'description'">
            {{ record.description || record.name || '-' }}
          </template>
          <template v-if="column.key === 'groupName'">
            <a-tag>{{ groupNameMap[record.group] || record.group || '未分组' }}</a-tag>
          </template>
          <template v-if="column.key === 'action'">
            <a-button type="link" size="small" danger :disabled="disabled" @click="removePermission(record)">
              移除
            </a-button>
          </template>
        </template>
      </a-table>
    </a-spin>

    <!-- 添加权限弹窗 -->
    <a-modal
      v-model:open="showAddModal"
      title="添加权限"
      width="900px"
      :footer="null"
    >
      <div class="add-perm-modal">
        <div class="add-perm-toolbar">
          <a-input-search
            v-model:value="addSearchText"
            placeholder="搜索权限名称或编码..."
            style="width: 280px"
            allow-clear
          />
        </div>

        <!-- 左侧分组导航 + 右侧列表 -->
        <div class="add-perm-layout">
          <div class="add-perm-groups">
            <div
              class="group-nav-item"
              :class="{ active: !addFilterGroup }"
              @click="addFilterGroup = undefined"
            >
              全部
              <span class="group-nav-count">{{ permissions.length }}</span>
            </div>
            <div
              v-for="g in addGroupNav"
              :key="g.key"
              class="group-nav-item"
              :class="{ active: addFilterGroup === g.key }"
              @click="addFilterGroup = g.key"
            >
              {{ g.label }}
              <span class="group-nav-count">{{ g.count }}</span>
            </div>
          </div>
          <div class="add-perm-list">
            <a-table
              :data-source="filteredAddList"
              :columns="addColumns"
              size="small"
              :pagination="{ pageSize: 10, showSizeChanger: false, current: addPageCurrent }"
              row-key="id"
              :row-class-name="(record) => isAssigned(record) ? 'row-assigned' : ''"
              @change="(pag) => addPageCurrent = pag.current"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'description'">
                  <span :class="{ 'text-muted': isAssigned(record) }">{{ record.description || record.name || '-' }}</span>
                </template>
                <template v-if="column.key === 'code'">
                  <span class="perm-code" :class="{ 'text-muted': isAssigned(record) }">{{ record.code }}</span>
                </template>
                <template v-if="column.key === 'action'">
                  <span v-if="isAssigned(record)" class="already-added">已添加</span>
                  <a-button v-else type="link" size="small" @click="addPermission(record)">
                    添加
                  </a-button>
                </template>
              </template>
            </a-table>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, ExportOutlined, ImportOutlined } from '@ant-design/icons-vue'
import { getPermissionGroups } from '@/api/permission'
import { exportRolePermissions, importRolePermissions } from '@/api/role'
import { exportDepartmentPermissions, importDepartmentPermissions } from '@/api/department'
import { downloadBlob } from '@/utils/download'

const props = defineProps({
  loading: { type: Boolean, default: false },
  permissions: { type: Array, default: () => [] },
  targetKeys: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
  // 导入导出所需
  resourceType: { type: String, default: '' }, // 'role' | 'department'
  resourceId: { type: Number, default: null },
})

const emit = defineEmits(['update:targetKeys', 'imported'])

const searchText = ref('')
const filterGroup = ref(undefined)
const showAddModal = ref(false)
const addSearchText = ref('')
const addFilterGroup = ref(undefined)
const addPageCurrent = ref(1)
const groupList = ref([])
const exporting = ref(false)
const importing = ref(false)

// 切换分组或搜索时重置页码
watch([addFilterGroup, addSearchText], () => { addPageCurrent.value = 1 })

onMounted(async () => {
  try {
    const res = await getPermissionGroups()
    groupList.value = res || []
  } catch { groupList.value = [] }
})

// group_key -> group_name 映射
const groupNameMap = computed(() => {
  const map = {}
  groupList.value.forEach(g => { map[g.groupKey] = g.groupName })
  return map
})

const targetKeySet = computed(() => new Set(props.targetKeys.map(String)))

const assignedPermissions = computed(() =>
  props.permissions.filter(p => targetKeySet.value.has(String(p.id)))
)

function isAssigned(record) {
  return targetKeySet.value.has(String(record.id))
}

// 添加弹窗左侧分组导航（使用全部权限计数）
const addGroupNav = computed(() => {
  const countMap = {}
  props.permissions.forEach(p => {
    const g = p.group || 'UNKNOWN'
    countMap[g] = (countMap[g] || 0) + 1
  })
  return groupList.value
    .filter(g => countMap[g.groupKey] > 0)
    .map(g => ({ key: g.groupKey, label: g.groupName, count: countMap[g.groupKey] || 0 }))
})

function matchSearch(perm, keyword) {
  if (!keyword) return true
  const kw = keyword.toLowerCase()
  return (perm.code || '').toLowerCase().includes(kw)
    || (perm.description || '').toLowerCase().includes(kw)
    || (perm.name || '').toLowerCase().includes(kw)
    || (groupNameMap.value[perm.group] || '').toLowerCase().includes(kw)
}

const filteredAssigned = computed(() => {
  return assignedPermissions.value.filter(p => {
    if (!matchSearch(p, searchText.value)) return false
    if (filterGroup.value && p.group !== filterGroup.value) return false
    return true
  })
})

// 添加弹窗列表：全部权限，已添加的排最后
const filteredAddList = computed(() => {
  const filtered = props.permissions.filter(p => {
    if (!matchSearch(p, addSearchText.value)) return false
    if (addFilterGroup.value && p.group !== addFilterGroup.value) return false
    return true
  })
  // 未添加的在前，已添加的在后
  const notAssigned = filtered.filter(p => !isAssigned(p))
  const assigned = filtered.filter(p => isAssigned(p))
  return [...notAssigned, ...assigned]
})

const assignedColumns = [
  { title: '权限名称', key: 'description', ellipsis: true },
  { title: '权限组', key: 'groupName', width: 160 },
  { title: '操作', key: 'action', width: 80, align: 'center' },
]

const addColumns = [
  { title: '权限名称', key: 'description', ellipsis: true },
  { title: '权限编码', key: 'code', width: 280 },
  { title: '操作', key: 'action', width: 80, align: 'center' },
]

function addPermission(record) {
  emit('update:targetKeys', [...props.targetKeys, String(record.id)])
}

function removePermission(record) {
  emit('update:targetKeys', props.targetKeys.filter(k => String(k) !== String(record.id)))
}

async function handleExport() {
  if (!props.resourceId) return
  exporting.value = true
  try {
    let blob
    if (props.resourceType === 'role') {
      blob = await exportRolePermissions(props.resourceId)
    } else {
      blob = await exportDepartmentPermissions(props.resourceId)
    }
    downloadBlob(blob, `permissions_${props.resourceType}_${props.resourceId}.xlsx`)
  } catch (e) {
    message.error(e?.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

async function handleImportFile(file) {
  if (!props.resourceId) return false
  importing.value = true
  try {
    let res
    if (props.resourceType === 'role') {
      res = await importRolePermissions(props.resourceId, file)
    } else {
      res = await importDepartmentPermissions(props.resourceId, file)
    }
    message.success(res?.message || '导入成功')
    emit('imported', res)
  } catch (e) {
    message.error(e?.message || '导入失败')
  } finally {
    importing.value = false
  }
  return false // 阻止 a-upload 默认上传
}
</script>

<style scoped>
.permission-manager { display: flex; flex-direction: column; gap: 14px; }
.pm-toolbar { display: flex; gap: 12px; align-items: center; }

.add-perm-modal { display: flex; flex-direction: column; gap: 14px; }
.add-perm-toolbar { display: flex; gap: 12px; }
.add-perm-layout { display: flex; gap: 0; border: 1px solid #f0f0f0; border-radius: 8px; overflow: hidden; min-height: 460px; }
.add-perm-groups { width: 180px; flex-shrink: 0; border-right: 1px solid #f0f0f0; background: #fafafa; padding: 8px 0; overflow-y: auto; max-height: 480px; }
.group-nav-item { padding: 10px 16px; font-size: 13px; color: #333; cursor: pointer; display: flex; justify-content: space-between; align-items: center; transition: background 0.15s; }
.group-nav-item:hover { background: #f0f5ff; }
.group-nav-item.active { background: #e6f4ff; color: #1677ff; font-weight: 500; border-left: 3px solid #1677ff; padding-left: 13px; }
.group-nav-count { font-size: 12px; color: #999; }
.group-nav-item.active .group-nav-count { color: #1677ff; }
.add-perm-list { flex: 1; min-width: 0; padding: 8px 12px; }

.perm-code { font-family: monospace; font-size: 12px; color: #666; background: #f5f5f5; padding: 2px 6px; border-radius: 3px; }
.perm-code.text-muted { color: #bbb; background: #fafafa; }
.text-muted { color: #bbb; }
.already-added { font-size: 12px; color: #bbb; }

.add-perm-list :deep(.row-assigned) { background: #fafafa; }
.add-perm-list :deep(.row-assigned:hover > td) { background: #fafafa !important; }

/* 分页固定在底部 */
.add-perm-list { display: flex; flex-direction: column; }
.add-perm-list :deep(.ant-table-wrapper) { flex: 1; display: flex; flex-direction: column; }
.add-perm-list :deep(.ant-spin-nested-loading),
.add-perm-list :deep(.ant-spin-container) { flex: 1; display: flex; flex-direction: column; }
.add-perm-list :deep(.ant-table) { flex: 1; }
.add-perm-list :deep(.ant-table-pagination) { margin-top: auto; }
</style>
