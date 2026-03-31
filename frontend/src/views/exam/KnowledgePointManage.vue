<template>
  <div class="knowledge-point-page">
    <div class="page-header">
      <div>
        <h2>知识点管理</h2>
        <p class="page-sub">统一维护题库知识点，题目与 AI 草稿都可复用这里的知识点</p>
      </div>
      <permissions-tooltip
        :allowed="canCreateKnowledgePoint"
        tips="需要 CREATE_KNOWLEDGE_POINT 权限"
        v-slot="{ disabled }"
      >
        <a-button type="primary" :disabled="disabled" @click="openCreateModal">
          新增知识点
        </a-button>
      </permissions-tooltip>
    </div>

    <a-card :bordered="false" style="margin-bottom:16px">
      <a-row :gutter="16">
        <a-col :span="10">
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索知识点名称"
            allow-clear
            @search="reloadKnowledgePoints"
          />
        </a-col>
        <a-col :span="6">
          <a-select v-model:value="statusFilter" style="width:100%" @change="reloadKnowledgePoints">
            <a-select-option value="all">全部状态</a-select-option>
            <a-select-option value="true">启用</a-select-option>
            <a-select-option value="false">停用</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </a-card>

    <a-card :bordered="false">
      <a-table
        :columns="columns"
        :data-source="knowledgePointList"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'isActive'">
            <a-tag :color="record.isActive ? 'green' : 'default'">
              {{ record.isActive ? '启用' : '停用' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'questionCount'">
            {{ record.questionCount || 0 }} 题
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <permissions-tooltip
                :allowed="canUpdateKnowledgePoint"
                tips="需要 UPDATE_KNOWLEDGE_POINT 权限"
                v-slot="{ disabled }"
              >
                <a-button type="link" size="small" :disabled="disabled" @click="openEditModal(record)">
                  编辑
                </a-button>
              </permissions-tooltip>
              <permissions-tooltip
                :allowed="canDeleteKnowledgePoint"
                tips="需要 DELETE_KNOWLEDGE_POINT 权限"
                v-slot="{ disabled }"
              >
                <a-button type="link" danger size="small" :disabled="disabled" @click="handleDelete(record)">
                  删除
                </a-button>
              </permissions-tooltip>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal
      :open="modalOpen"
      :title="editingKnowledgePoint ? '编辑知识点' : '新增知识点'"
      ok-text="保存"
      cancel-text="取消"
      @update:open="modalOpen = $event"
      @ok="handleSubmit"
      @cancel="modalOpen = false"
    >
      <a-form layout="vertical">
        <a-form-item label="知识点名称" required>
          <a-input v-model:value="form.name" :maxlength="100" show-count />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" :rows="4" :maxlength="500" show-count />
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="form.isActive" checked-children="启用" un-checked-children="停用" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import {
  createKnowledgePoint,
  deleteKnowledgePoint,
  getKnowledgePoints,
  updateKnowledgePoint,
} from '@/api/knowledgePoint'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

const authStore = useAuthStore()
const loading = ref(false)
const modalOpen = ref(false)
const editingKnowledgePoint = ref(null)
const knowledgePointList = ref([])
const searchText = ref('')
const statusFilter = ref('all')

const form = reactive({
  name: '',
  description: '',
  isActive: true,
})

const columns = [
  { title: '知识点名称', dataIndex: 'name', key: 'name', width: 220 },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '关联题目', key: 'questionCount', width: 120 },
  { title: '状态', key: 'isActive', width: 100 },
  { title: '操作', key: 'action', width: 140 },
]

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showTotal: (total) => `共 ${total} 个知识点`,
})

const canCreateKnowledgePoint = computed(() => authStore.hasPermission('CREATE_KNOWLEDGE_POINT'))
const canUpdateKnowledgePoint = computed(() => authStore.hasPermission('UPDATE_KNOWLEDGE_POINT'))
const canDeleteKnowledgePoint = computed(() => authStore.hasPermission('DELETE_KNOWLEDGE_POINT'))

function resolveStatusFilter() {
  if (statusFilter.value === 'all') {
    return undefined
  }
  return statusFilter.value === 'true'
}

function resetForm(record = null) {
  form.name = record?.name || ''
  form.description = record?.description || ''
  form.isActive = record?.isActive ?? true
}

function openCreateModal() {
  if (!canCreateKnowledgePoint.value) return
  editingKnowledgePoint.value = null
  resetForm()
  modalOpen.value = true
}

function openEditModal(record) {
  if (!canUpdateKnowledgePoint.value) return
  editingKnowledgePoint.value = record
  resetForm(record)
  modalOpen.value = true
}

function reloadKnowledgePoints() {
  pagination.current = 1
  loadKnowledgePoints()
}

async function loadKnowledgePoints() {
  loading.value = true
  try {
    const result = await getKnowledgePoints({
      page: pagination.current,
      size: pagination.pageSize,
      search: searchText.value || undefined,
      isActive: resolveStatusFilter(),
    })
    knowledgePointList.value = result.items || []
    pagination.total = result.total || 0
  } catch (error) {
    message.error(error.message || '加载知识点失败')
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  const name = form.name.trim()
  if (!name) {
    message.warning('请填写知识点名称')
    return
  }

  const payload = {
    name,
    description: form.description?.trim() || undefined,
    isActive: form.isActive,
  }
  try {
    if (editingKnowledgePoint.value?.id) {
      await updateKnowledgePoint(editingKnowledgePoint.value.id, payload)
      message.success('知识点已更新')
    } else {
      await createKnowledgePoint(payload)
      message.success('知识点已创建')
    }
    modalOpen.value = false
    editingKnowledgePoint.value = null
    await loadKnowledgePoints()
  } catch (error) {
    message.error(error.message || '保存失败')
  }
}

function handleDelete(record) {
  if (!canDeleteKnowledgePoint.value) return
  Modal.confirm({
    title: '确认删除知识点',
    content: '若该知识点已被题目引用，将无法删除。',
    okType: 'danger',
    async onOk() {
      try {
        await deleteKnowledgePoint(record.id)
        message.success('知识点已删除')
        await loadKnowledgePoints()
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadKnowledgePoints()
}

onMounted(() => {
  loadKnowledgePoints()
})
</script>

<style scoped>
.knowledge-point-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #001234;
}

.page-sub {
  margin: 6px 0 0;
  color: #8c8c8c;
  font-size: 13px;
}
</style>
