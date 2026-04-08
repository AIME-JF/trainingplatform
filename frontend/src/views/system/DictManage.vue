<template>
  <div class="dict-manage-page">
    <div class="page-header">
      <h2>字典管理</h2>
    </div>

    <a-card :bordered="false">
      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="policeType" tab="警种">
          <div class="tab-toolbar">
            <a-input-search
              v-model:value="ptSearch"
              placeholder="搜索警种名称"
              style="width: 240px"
              allow-clear
              @search="fetchPoliceTypes"
            />
            <a-button type="primary" @click="openPtModal()">
              <template #icon><PlusOutlined /></template>
              新增警种
            </a-button>
          </div>

          <a-table
            :data-source="ptList"
            :columns="ptColumns"
            :loading="ptLoading"
            row-key="id"
            :pagination="{ current: ptPage, pageSize: ptSize, total: ptTotal, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }"
            @change="handlePtTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'isActive'">
                <a-tag :color="record.isActive ? 'green' : 'default'">{{ record.isActive ? '启用' : '停用' }}</a-tag>
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-button type="link" size="small" @click="openPtModal(record)">编辑</a-button>
                  <a-popconfirm title="确定删除该警种吗？" @confirm="handleDeletePt(record.id)">
                    <a-button type="link" size="small" danger>删除</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-tab-pane>
        <a-tab-pane key="instructorSpecialty" tab="教官专长方向">
          <div class="tab-toolbar">
            <span />
            <a-button type="primary" @click="openIsModal()">
              <template #icon><PlusOutlined /></template>
              新增专长方向
            </a-button>
          </div>

          <a-table
            :data-source="isList"
            :columns="isColumns"
            :loading="isLoading"
            row-key="id"
            :pagination="false"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'enabled'">
                <a-tag :color="record.enabled ? 'green' : 'default'">{{ record.enabled ? '启用' : '停用' }}</a-tag>
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-button type="link" size="small" @click="openIsModal(record)">编辑</a-button>
                  <a-popconfirm title="确定删除该专长方向吗？" @confirm="handleDeleteIs(record.id)">
                    <a-button type="link" size="small" danger>删除</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-tab-pane>
        <a-tab-pane key="trainingType" tab="培训班类型">
          <div class="tab-toolbar">
            <a-input-search
              v-model:value="ttSearch"
              placeholder="搜索培训班类型名称"
              style="width: 240px"
              allow-clear
              @search="fetchTrainingTypes"
            />
            <a-button type="primary" @click="openTtModal()">
              <template #icon><PlusOutlined /></template>
              新增培训班类型
            </a-button>
          </div>

          <a-table
            :data-source="ttList"
            :columns="ttColumns"
            :loading="ttLoading"
            row-key="id"
            :pagination="{ current: ttPage, pageSize: ttSize, total: ttTotal, showSizeChanger: true, showTotal: (t) => `共 ${t} 条` }"
            @change="handleTtTableChange"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'isActive'">
                <a-tag :color="record.isActive ? 'green' : 'default'">{{ record.isActive ? '启用' : '停用' }}</a-tag>
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-button type="link" size="small" @click="openTtModal(record)">编辑</a-button>
                  <a-popconfirm title="确定删除该培训班类型吗？" @confirm="handleDeleteTt(record.id)">
                    <a-button type="link" size="small" danger>删除</a-button>
                  </a-popconfirm>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- 新增/编辑弹窗 -->
    <a-modal
      v-model:open="ptModalVisible"
      :title="ptEditingId ? '编辑警种' : '新增警种'"
      :confirm-loading="ptSaving"
      ok-text="保存"
      @ok="handleSavePt"
    >
      <a-form layout="vertical">
        <a-form-item label="警种名称" required>
          <a-input v-model:value="ptForm.name" placeholder="请输入警种名称" :maxlength="100" />
        </a-form-item>
        <a-form-item v-if="!ptEditingId" label="警种编码" required>
          <a-input v-model:value="ptForm.code" placeholder="请输入唯一编码，如 zhian" :maxlength="50" />
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="ptForm.isActive" checked-children="启用" un-checked-children="停用" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="ptForm.description" :rows="3" :maxlength="500" placeholder="选填" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 培训班类型 新增/编辑弹窗 -->
    <a-modal
      v-model:open="ttModalVisible"
      :title="ttEditingId ? '编辑培训班类型' : '新增培训班类型'"
      :confirm-loading="ttSaving"
      ok-text="保存"
      @ok="handleSaveTt"
    >
      <a-form layout="vertical">
        <a-form-item label="类型名称" required>
          <a-input v-model:value="ttForm.name" placeholder="请输入类型名称" :maxlength="100" />
        </a-form-item>
        <a-form-item v-if="!ttEditingId" label="类型编码" required>
          <a-input v-model:value="ttForm.code" placeholder="请输入唯一编码" :maxlength="50" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="ttForm.description" :rows="3" :maxlength="500" placeholder="选填" />
        </a-form-item>
        <a-form-item label="排序">
          <a-input-number v-model:value="ttForm.sortOrder" :min="0" :max="9999" placeholder="数字越小越靠前" style="width: 100%" />
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="ttForm.isActive" checked-children="启用" un-checked-children="停用" />
        </a-form-item>
      </a-form>
    </a-modal>
    <!-- 教官专长方向 新增/编辑弹窗 -->
    <a-modal
      v-model:open="isModalVisible"
      :title="isEditingId ? '编辑专长方向' : '新增专长方向'"
      :confirm-loading="isSaving"
      ok-text="保存"
      @ok="handleSaveIs"
    >
      <a-form layout="vertical">
        <a-form-item label="专长方向名称" required>
          <a-input v-model:value="isForm.name" placeholder="请输入专长方向名称" :maxlength="50" />
        </a-form-item>
        <a-form-item label="排序">
          <a-input-number v-model:value="isForm.sortOrder" :min="0" :max="9999" placeholder="数字越小越靠前" style="width: 100%" />
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="isForm.enabled" checked-children="启用" un-checked-children="停用" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import {
  getPoliceTypes,
  createPoliceType,
  updatePoliceType,
  deletePoliceType,
} from '@/api/policeType'
import {
  getTrainingTypes,
  createTrainingType,
  updateTrainingType,
  deleteTrainingType,
} from '@/api/trainingType'
import request from '@/api/request'

const activeTab = ref('policeType')

// ===== 警种 =====
const ptSearch = ref('')
const ptLoading = ref(false)
const ptList = ref([])
const ptPage = ref(1)
const ptSize = ref(10)
const ptTotal = ref(0)
const ptModalVisible = ref(false)
const ptSaving = ref(false)
const ptEditingId = ref(null)
const ptForm = reactive({
  name: '',
  code: '',
  isActive: true,
  description: '',
})

const ptColumns = [
  { title: '序号', key: 'index', width: 70, customRender: ({ index }) => (ptPage.value - 1) * ptSize.value + index + 1 },
  { title: '警种名称', dataIndex: 'name', key: 'name' },
  { title: '编码', dataIndex: 'code', key: 'code', width: 140 },
  { title: '状态', key: 'isActive', width: 80 },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '操作', key: 'action', width: 140 },
]

async function fetchPoliceTypes() {
  ptLoading.value = true
  try {
    const result = await getPoliceTypes({
      page: ptPage.value,
      size: ptSize.value,
      name: ptSearch.value || undefined,
    })
    ptList.value = result.items || []
    ptTotal.value = result.total || 0
  } catch (error) {
    message.error(error.message || '加载警种失败')
  } finally {
    ptLoading.value = false
  }
}

function handlePtTableChange(pagination) {
  ptPage.value = pagination.current
  ptSize.value = pagination.pageSize
  fetchPoliceTypes()
}

function openPtModal(record) {
  if (record) {
    ptEditingId.value = record.id
    ptForm.name = record.name || ''
    ptForm.code = record.code || ''
    ptForm.isActive = record.isActive !== false
    ptForm.description = record.description || ''
  } else {
    ptEditingId.value = null
    ptForm.name = ''
    ptForm.code = ''
    ptForm.isActive = true
    ptForm.description = ''
  }
  ptModalVisible.value = true
}

async function handleSavePt() {
  if (!ptForm.name.trim()) {
    message.warning('请输入警种名称')
    return
  }
  ptSaving.value = true
  try {
    if (ptEditingId.value) {
      await updatePoliceType(ptEditingId.value, {
        name: ptForm.name.trim(),
        isActive: ptForm.isActive,
        description: ptForm.description?.trim() || '',
      })
      message.success('更新成功')
    } else {
      if (!ptForm.code.trim()) {
        message.warning('请输入警种编码')
        ptSaving.value = false
        return
      }
      await createPoliceType({
        name: ptForm.name.trim(),
        code: ptForm.code.trim(),
        description: ptForm.description?.trim() || '',
      })
      message.success('创建成功')
    }
    ptModalVisible.value = false
    fetchPoliceTypes()
  } catch (error) {
    message.error(error.message || '保存失败')
  } finally {
    ptSaving.value = false
  }
}

async function handleDeletePt(id) {
  try {
    await deletePoliceType(id)
    message.success('删除成功')
    fetchPoliceTypes()
  } catch (error) {
    message.error(error.message || '删除失败')
  }
}

// ===== 培训班类型 =====
const ttSearch = ref('')
const ttLoading = ref(false)
const ttList = ref([])
const ttPage = ref(1)
const ttSize = ref(10)
const ttTotal = ref(0)
const ttModalVisible = ref(false)
const ttSaving = ref(false)
const ttEditingId = ref(null)
const ttForm = reactive({
  name: '',
  code: '',
  description: '',
  sortOrder: 0,
  isActive: true,
})

const ttColumns = [
  { title: '序号', key: 'index', width: 70, customRender: ({ index }) => (ttPage.value - 1) * ttSize.value + index + 1 },
  { title: '类型名称', dataIndex: 'name', key: 'name' },
  { title: '编码', dataIndex: 'code', key: 'code', width: 140 },
  { title: '排序', dataIndex: 'sortOrder', key: 'sortOrder', width: 80 },
  { title: '状态', key: 'isActive', width: 80 },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '操作', key: 'action', width: 140 },
]

async function fetchTrainingTypes() {
  ttLoading.value = true
  try {
    const result = await getTrainingTypes({
      page: ttPage.value,
      size: ttSize.value,
      name: ttSearch.value || undefined,
    })
    ttList.value = result.items || []
    ttTotal.value = result.total || 0
  } catch (error) {
    message.error(error.message || '加载培训班类型失败')
  } finally {
    ttLoading.value = false
  }
}

function handleTtTableChange(pagination) {
  ttPage.value = pagination.current
  ttSize.value = pagination.pageSize
  fetchTrainingTypes()
}

function openTtModal(record) {
  if (record) {
    ttEditingId.value = record.id
    ttForm.name = record.name || ''
    ttForm.code = record.code || ''
    ttForm.description = record.description || ''
    ttForm.sortOrder = record.sortOrder ?? 0
    ttForm.isActive = record.isActive !== false
  } else {
    ttEditingId.value = null
    ttForm.name = ''
    ttForm.code = ''
    ttForm.description = ''
    ttForm.sortOrder = 0
    ttForm.isActive = true
  }
  ttModalVisible.value = true
}

async function handleSaveTt() {
  if (!ttForm.name.trim()) {
    message.warning('请输入类型名称')
    return
  }
  ttSaving.value = true
  try {
    if (ttEditingId.value) {
      await updateTrainingType(ttEditingId.value, {
        name: ttForm.name.trim(),
        description: ttForm.description?.trim() || '',
        sortOrder: ttForm.sortOrder,
        isActive: ttForm.isActive,
      })
      message.success('更新成功')
    } else {
      if (!ttForm.code.trim()) {
        message.warning('请输入类型编码')
        ttSaving.value = false
        return
      }
      await createTrainingType({
        name: ttForm.name.trim(),
        code: ttForm.code.trim(),
        description: ttForm.description?.trim() || '',
        sortOrder: ttForm.sortOrder,
        isActive: ttForm.isActive,
      })
      message.success('创建成功')
    }
    ttModalVisible.value = false
    fetchTrainingTypes()
  } catch (error) {
    message.error(error.message || '保存失败')
  } finally {
    ttSaving.value = false
  }
}

async function handleDeleteTt(id) {
  try {
    await deleteTrainingType(id)
    message.success('删除成功')
    fetchTrainingTypes()
  } catch (error) {
    message.error(error.message || '删除失败')
  }
}

// ===== 教官专长方向 =====
const isLoading = ref(false)
const isList = ref([])
const isModalVisible = ref(false)
const isSaving = ref(false)
const isEditingId = ref(null)
const isForm = reactive({
  name: '',
  sortOrder: 0,
  enabled: true,
})

const isColumns = [
  { title: '序号', key: 'index', width: 70, customRender: ({ index }) => index + 1 },
  { title: '专长方向名称', dataIndex: 'name', key: 'name' },
  { title: '排序', dataIndex: 'sortOrder', key: 'sortOrder', width: 80 },
  { title: '状态', key: 'enabled', width: 80 },
  { title: '操作', key: 'action', width: 140 },
]

async function fetchInstructorSpecialties() {
  isLoading.value = true
  try {
    isList.value = await request.get('/dict/instructor-specialties') || []
  } catch {
    isList.value = []
  } finally {
    isLoading.value = false
  }
}

function openIsModal(record) {
  if (record) {
    isEditingId.value = record.id
    isForm.name = record.name || ''
    isForm.sortOrder = record.sortOrder ?? 0
    isForm.enabled = record.enabled !== false
  } else {
    isEditingId.value = null
    isForm.name = ''
    isForm.sortOrder = 0
    isForm.enabled = true
  }
  isModalVisible.value = true
}

async function handleSaveIs() {
  if (!isForm.name.trim()) {
    message.warning('请输入专长方向名称')
    return
  }
  isSaving.value = true
  try {
    const payload = { name: isForm.name.trim(), sortOrder: isForm.sortOrder, enabled: isForm.enabled }
    if (isEditingId.value) {
      await request.put(`/dict/instructor-specialties/${isEditingId.value}`, payload)
      message.success('更新成功')
    } else {
      await request.post('/dict/instructor-specialties', payload)
      message.success('创建成功')
    }
    isModalVisible.value = false
    fetchInstructorSpecialties()
  } catch (error) {
    message.error(error.message || '保存失败')
  } finally {
    isSaving.value = false
  }
}

async function handleDeleteIs(id) {
  try {
    await request.delete(`/dict/instructor-specialties/${id}`)
    message.success('删除成功')
    fetchInstructorSpecialties()
  } catch (error) {
    message.error(error.message || '删除失败')
  }
}

onMounted(() => {
  fetchPoliceTypes()
  fetchTrainingTypes()
  fetchInstructorSpecialties()
})
</script>

<style scoped>
.dict-manage-page {
  padding: 0;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  color: #001234;
}

.tab-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
</style>
