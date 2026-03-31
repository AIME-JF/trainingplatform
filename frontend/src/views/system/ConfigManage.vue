<template>
  <div class="setting-page">
    <div class="page-content">
      <a-row :gutter="20">
        <a-col :xs="24" :lg="6">
          <a-card class="config-groups-card" :bordered="false">
            <template #title>
              <span>配置分组</span>
            </template>
            <a-spin :spinning="groupsLoading">
              <div v-if="configGroups.length" class="config-groups-list">
                <div
                  v-for="group in configGroups"
                  :key="group.id"
                  class="config-group-item"
                  :class="{ active: selectedGroupId === group.id }"
                  @click="selectGroup(group.id)"
                >
                  <div class="group-name">{{ group.groupName }}</div>
                  <div class="group-description">{{ group.groupDescription || '暂无描述' }}</div>
                </div>
              </div>
              <a-empty v-else description="暂无配置组" />
            </a-spin>
          </a-card>
        </a-col>

        <a-col :xs="24" :lg="18">
          <a-card class="configs-card" :bordered="false">
            <template #title>
              <span>{{ selectedGroupName }}</span>
            </template>
            <template #extra>
              <a-space>
                <a-button :loading="configsLoading" @click="reloadCurrentGroup">刷新</a-button>
                <a-popconfirm
                  title="确认重置当前配置组吗？"
                  description="会用初始化配置覆盖当前配置组内容。"
                  ok-text="确认重置"
                  cancel-text="取消"
                  :disabled="!selectedGroupId"
                  @confirm="handleResetGroup"
                >
                  <a-button danger :disabled="!selectedGroupId" :loading="resettingGroup">
                    重置当前组
                  </a-button>
                </a-popconfirm>
              </a-space>
            </template>

            <a-spin :spinning="configsLoading">
              <div v-if="configs.length" class="configs-content">
                <a-table
                  :columns="columns"
                  :data-source="configs"
                  :show-header="true"
                  :pagination="false"
                  row-key="id"
                  class="config-table"
                >
                  <template #bodyCell="{ column, record }">
                    <template v-if="column.key === 'configInfo'">
                      <div class="config-info">
                        <div class="config-name">{{ record.configName }}</div>
                        <div class="config-description">{{ record.configDescription || '暂无描述' }}</div>
                      </div>
                    </template>

                    <template v-else-if="column.key === 'configValue'">
                      <a-input
                        v-if="record.configFormat === 'short_text'"
                        v-model:value="configValues[record.id]"
                        :placeholder="record.configDescription || '请输入内容'"
                        :disabled="!editingRows[record.id]"
                        @update:value="markAsChanged(record.id)"
                      />

                      <a-input-password
                        v-else-if="record.configFormat === 'password'"
                        v-model:value="configValues[record.id]"
                        :placeholder="record.configDescription || '请输入内容'"
                        :disabled="!editingRows[record.id]"
                        @update:value="markAsChanged(record.id)"
                      />

                      <a-textarea
                        v-else-if="record.configFormat === 'long_text'"
                        v-model:value="configValues[record.id]"
                        :rows="2"
                        :placeholder="record.configDescription || '请输入内容'"
                        :disabled="!editingRows[record.id]"
                        @update:value="markAsChanged(record.id)"
                      />

                      <a-input-number
                        v-else-if="record.configFormat === 'integer'"
                        v-model:value="configValues[record.id]"
                        :min="0"
                        :step="1"
                        :precision="0"
                        style="width: 200px"
                        :disabled="!editingRows[record.id]"
                        @change="markAsChanged(record.id)"
                      />

                      <a-input-number
                        v-else-if="record.configFormat === 'float'"
                        v-model:value="configValues[record.id]"
                        :min="0"
                        :step="0.1"
                        :precision="2"
                        style="width: 200px"
                        :disabled="!editingRows[record.id]"
                        @change="markAsChanged(record.id)"
                      />

                      <a-switch
                        v-else-if="record.configFormat === 'boolean'"
                        v-model:checked="configValues[record.id]"
                        checked-children="启用"
                        un-checked-children="禁用"
                        :disabled="!editingRows[record.id]"
                        @change="markAsChanged(record.id)"
                      />

                      <div v-else-if="record.configFormat === 'list'" class="list-input">
                        <a-tag
                          v-for="(item, index) in getListValue(record.id)"
                          :key="`${record.id}-${index}-${item}`"
                          :closable="editingRows[record.id]"
                          @close.prevent="removeListItem(record.id, index)"
                        >
                          {{ item }}
                        </a-tag>
                        <template v-if="editingRows[record.id]">
                          <a-input
                            v-if="showListInput[record.id]"
                            :ref="(el) => setListInputRef(record.id, el)"
                            v-model:value="listInputValue[record.id]"
                            size="small"
                            style="width: 100px"
                            @pressEnter="addListItem(record.id)"
                            @blur="hideListInput(record.id)"
                          />
                          <a-button v-else size="small" @click="showListInputBox(record.id)">
                            + 添加
                          </a-button>
                        </template>
                      </div>

                      <a-select
                        v-else-if="record.configFormat === 'select'"
                        v-model:value="configValues[record.id]"
                        :placeholder="record.configDescription || '请选择'"
                        :options="getSelectOptions(record.id)"
                        style="width: 100%"
                        :disabled="!editingRows[record.id]"
                        @change="markAsChanged(record.id)"
                      />

                      <a-input
                        v-else
                        v-model:value="configValues[record.id]"
                        :placeholder="record.configDescription || '请输入内容'"
                        :disabled="!editingRows[record.id]"
                        @update:value="markAsChanged(record.id)"
                      />
                    </template>

                    <template v-else-if="column.key === 'isPublic'">
                      <a-switch
                        v-model:checked="configPublicStatus[record.id]"
                        checked-children="公开"
                        un-checked-children="私有"
                        :loading="publicToggleLoading[record.id]"
                        @change="togglePublicStatus(record, $event)"
                      />
                    </template>

                    <template v-else-if="column.key === 'action'">
                      <a-button
                        v-if="!editingRows[record.id]"
                        type="primary"
                        size="small"
                        @click="startEdit(record)"
                      >
                        编辑
                      </a-button>
                      <a-button
                        v-else
                        type="primary"
                        size="small"
                        class="save-button"
                        :loading="saveLoading[record.id]"
                        :disabled="!hasRowChanges[record.id]"
                        @click="saveConfig(record)"
                      >
                        保存
                      </a-button>
                    </template>
                  </template>
                </a-table>
              </div>

              <a-empty v-else description="该配置组暂无配置项" />
            </a-spin>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { systemApi } from '@/api'

const configGroups = ref([])
const configs = ref([])
const selectedGroupId = ref(null)
const groupsLoading = ref(false)
const configsLoading = ref(false)
const resettingGroup = ref(false)

const editingRows = reactive({})
const saveLoading = reactive({})
const hasRowChanges = reactive({})

const publicToggleLoading = reactive({})
const configPublicStatus = reactive({})

const configValues = reactive({})
const originalValues = reactive({})

const showListInput = reactive({})
const listInputValue = reactive({})
const listInputRefs = reactive({})

const columns = [
  {
    title: '配置',
    key: 'configInfo',
    width: 200,
  },
  {
    title: '配置值',
    key: 'configValue',
  },
  {
    title: '是否公开',
    key: 'isPublic',
    width: 120,
    align: 'center',
  },
  {
    title: '操作',
    key: 'action',
    width: 100,
    align: 'center',
  },
]

const selectedGroup = computed(() => {
  if (!selectedGroupId.value) return null
  return configGroups.value.find((group) => group.id === selectedGroupId.value) || null
})

const selectedGroupName = computed(() => {
  return selectedGroup.value?.groupName || '请选择配置组'
})

onMounted(() => {
  loadConfigGroups()
})

async function loadConfigGroups(preferredGroupId) {
  groupsLoading.value = true
  try {
    const response = await systemApi.getConfigGroupList({ size: -1 })
    configGroups.value = response?.items || []

    const targetId = preferredGroupId || selectedGroupId.value || configGroups.value[0]?.id
    if (targetId) {
      await selectGroup(targetId)
      return
    }

    selectedGroupId.value = null
    clearConfigsState()
  } catch (error) {
    message.error(error?.message || '加载配置组失败')
  } finally {
    groupsLoading.value = false
  }
}

async function selectGroup(groupId) {
  if (!groupId) return
  selectedGroupId.value = groupId
  await loadConfigs(groupId)
}

async function loadConfigs(groupId) {
  configsLoading.value = true
  try {
    const response = await systemApi.getConfigGroupDetail(groupId)
    configs.value = Array.isArray(response?.configs)
      ? [...response.configs].sort((left, right) => left.id - right.id)
      : []
    initConfigValues()
    initConfigStates()
  } catch (error) {
    clearConfigsState()
    message.error(error?.message || '加载配置失败')
  } finally {
    configsLoading.value = false
  }
}

function clearConfigsState() {
  configs.value = []
  clearReactiveObject(editingRows)
  clearReactiveObject(saveLoading)
  clearReactiveObject(hasRowChanges)
  clearReactiveObject(publicToggleLoading)
  clearReactiveObject(configPublicStatus)
  clearReactiveObject(configValues)
  clearReactiveObject(originalValues)
  clearReactiveObject(showListInput)
  clearReactiveObject(listInputValue)
  clearReactiveObject(listInputRefs)
}

function initConfigValues() {
  clearReactiveObject(configValues)
  clearReactiveObject(originalValues)

  configs.value.forEach((config) => {
    let value
    let original

    if (config.configFormat === 'list') {
      value = parseListValue(config.configValue)
      original = [...value]
    } else if (config.configFormat === 'select') {
      value = config.configValue?.selected ?? undefined
      original = cloneValue(config.configValue || { selected: undefined, options: [] })
    } else if (config.configFormat === 'boolean') {
      value = normalizeBooleanValue(config.configValue)
      original = value
    } else if (config.configFormat === 'integer' || config.configFormat === 'float') {
      value = normalizeNumberValue(config.configValue)
      original = value
    } else {
      value = config.configValue ?? ''
      original = value
    }

    configValues[config.id] = cloneValue(value)
    originalValues[config.id] = cloneValue(original)
  })
}

function initConfigStates() {
  clearReactiveObject(editingRows)
  clearReactiveObject(saveLoading)
  clearReactiveObject(hasRowChanges)
  clearReactiveObject(publicToggleLoading)
  clearReactiveObject(configPublicStatus)
  clearReactiveObject(showListInput)
  clearReactiveObject(listInputValue)

  configs.value.forEach((config) => {
    editingRows[config.id] = false
    saveLoading[config.id] = false
    hasRowChanges[config.id] = false
    publicToggleLoading[config.id] = false
    configPublicStatus[config.id] = !!config.isPublic
    showListInput[config.id] = false
    listInputValue[config.id] = ''
  })
}

function clearReactiveObject(target) {
  Object.keys(target).forEach((key) => {
    delete target[key]
  })
}

function cloneValue(value) {
  if (Array.isArray(value) || (value && typeof value === 'object')) {
    return JSON.parse(JSON.stringify(value))
  }
  return value
}

function normalizeBooleanValue(value) {
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    if (['true', '1', 'yes', 'on'].includes(normalized)) {
      return true
    }
    if (['false', '0', 'no', 'off', ''].includes(normalized)) {
      return false
    }
  }
  return !!value
}

function normalizeNumberValue(value) {
  if (value === null || value === undefined || value === '') {
    return null
  }
  const num = Number(value)
  return Number.isNaN(num) ? null : num
}

function parseListValue(value) {
  if (!value) return []
  if (Array.isArray(value)) return [...value]
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }
  return []
}

function getListValue(configId) {
  return Array.isArray(configValues[configId]) ? configValues[configId] : []
}

function getSelectOptions(configId) {
  return Array.isArray(originalValues[configId]?.options) ? originalValues[configId].options : []
}

function setListInputRef(configId, element) {
  if (element) {
    listInputRefs[configId] = element
    return
  }
  delete listInputRefs[configId]
}

async function showListInputBox(configId) {
  showListInput[configId] = true
  await nextTick()
  listInputRefs[configId]?.focus?.()
}

function hideListInput(configId) {
  showListInput[configId] = false
  listInputValue[configId] = ''
}

function addListItem(configId) {
  const value = String(listInputValue[configId] || '').trim()
  if (!value) {
    hideListInput(configId)
    return
  }

  const currentList = getListValue(configId)
  if (!currentList.includes(value)) {
    configValues[configId] = [...currentList, value]
    markAsChanged(configId)
  }
  hideListInput(configId)
}

function removeListItem(configId, index) {
  const currentList = getListValue(configId)
  currentList.splice(index, 1)
  configValues[configId] = [...currentList]
  markAsChanged(configId)
}

function markAsChanged(configId) {
  hasRowChanges[configId] = true
}

function startEdit(config) {
  editingRows[config.id] = true
  hasRowChanges[config.id] = false

  if (config.configFormat === 'select') {
    configValues[config.id] = originalValues[config.id]?.selected ?? undefined
    return
  }

  configValues[config.id] = cloneValue(originalValues[config.id])
}

function buildConfigValue(config) {
  const currentValue = configValues[config.id]

  if (config.configFormat === 'list') {
    return Array.isArray(currentValue) ? currentValue : []
  }

  if (config.configFormat === 'select') {
    const originalValue = cloneValue(originalValues[config.id] || { options: [] })
    originalValue.selected = currentValue ?? null
    return originalValue
  }

  if (config.configFormat === 'boolean') {
    return normalizeBooleanValue(currentValue)
  }

  if (config.configFormat === 'integer' || config.configFormat === 'float') {
    return normalizeNumberValue(currentValue)
  }

  return currentValue ?? ''
}

async function saveConfig(config) {
  saveLoading[config.id] = true
  try {
    await systemApi.updateConfig(config.id, {
      configValue: buildConfigValue(config),
    })

    message.success(`${config.configName} 保存成功`)
    editingRows[config.id] = false
    hasRowChanges[config.id] = false
    hideListInput(config.id)

    if (selectedGroupId.value) {
      await loadConfigs(selectedGroupId.value)
    }
  } catch (error) {
    message.error(error?.message || `保存 ${config.configName} 失败`)
  } finally {
    saveLoading[config.id] = false
  }
}

async function togglePublicStatus(config, checked) {
  publicToggleLoading[config.id] = true
  try {
    await systemApi.updateConfig(config.id, {
      isPublic: checked,
    })
    configPublicStatus[config.id] = checked
    const target = configs.value.find((item) => item.id === config.id)
    if (target) {
      target.isPublic = checked
    }
    message.success(`${config.configName} ${checked ? '设为公开' : '设为私有'}`)
  } catch (error) {
    configPublicStatus[config.id] = !checked
    message.error(error?.message || `切换 ${config.configName} 公开状态失败`)
  } finally {
    publicToggleLoading[config.id] = false
  }
}

async function handleResetGroup() {
  if (!selectedGroupId.value) return
  resettingGroup.value = true
  try {
    await systemApi.resetConfigGroup(selectedGroupId.value)
    message.success('配置组已重置')
    await loadConfigs(selectedGroupId.value)
  } catch (error) {
    message.error(error?.message || '重置配置组失败')
  } finally {
    resettingGroup.value = false
  }
}

async function reloadCurrentGroup() {
  if (selectedGroupId.value) {
    await loadConfigs(selectedGroupId.value)
    return
  }
  await loadConfigGroups()
}
</script>

<style scoped>
.setting-page {
  padding: 24px;
}

.page-content {
  width: 100%;
}

.config-groups-card,
.configs-card {
  height: calc(100vh - 160px);
}

.config-groups-list {
  max-height: calc(100vh - 280px);
  overflow-y: auto;
}

.config-group-item {
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #e4e7ed;
}

.config-group-item:hover {
  background-color: #f5f7fa;
  border-color: #c0c4cc;
}

.config-group-item.active {
  background-color: #ecf5ff;
  border-color: #409eff;
  color: #409eff;
}

.group-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.group-description {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.configs-content {
  max-height: calc(100vh - 240px);
  overflow-y: auto;
}

.config-info {
  padding: 8px 0;
}

.config-name {
  font-weight: 500;
  margin-bottom: 4px;
  color: #303133;
}

.config-description {
  font-size: 12px;
  color: #909399;
  line-height: 1.4;
}

.list-input {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.config-table {
  border: none;
}

.save-button {
  background: #67c23a;
  border-color: #67c23a;
}

.save-button:hover,
.save-button:focus {
  background: #85ce61;
  border-color: #85ce61;
}

:deep(.ant-card-body) {
  height: calc(100% - 57px);
}

:deep(.ant-table) {
  border: none;
}

:deep(.ant-table-container) {
  border: none;
}

:deep(.ant-table-thead > tr > th) {
  border: none;
  background: transparent;
}

:deep(.ant-table-tbody > tr > td) {
  border: none;
}

:deep(.ant-table-tbody > tr.ant-table-row:hover > td) {
  background: transparent;
}

:deep(.ant-table-cell) {
  border: none !important;
}

@media (max-width: 992px) {
  .setting-page {
    padding: 0;
  }

  .config-groups-card,
  .configs-card {
    height: auto;
    min-height: 360px;
  }

  .config-groups-list,
  .configs-content {
    max-height: none;
  }
}
</style>
