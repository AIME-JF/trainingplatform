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

onMounted(() => {
  fetchPoliceTypes()
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
