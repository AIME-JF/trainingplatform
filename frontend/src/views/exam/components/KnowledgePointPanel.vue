<template>
  <div class="knowledge-point-panel">
    <div class="toolbar-row">
      <div class="toolbar-left">
        <button class="btn-primary" @click="openCreateModal">
          新增知识点
        </button>
        <div class="search-wrapper">
          <svg class="search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
          <input
            v-model="searchText"
            type="text"
            class="input-minimal"
            placeholder="搜索知识点名称..."
            @input="handleSearch"
          >
        </div>
      </div>
      <div class="toolbar-right">
        <select class="input-minimal filter-select" v-model="statusFilter" @change="reloadKnowledgePoints">
          <option value="all">全部状态</option>
          <option value="true">启用</option>
          <option value="false">停用</option>
        </select>
      </div>
    </div>

    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th class="col-index text-center">序号</th>
            <th class="col-name">知识点名称</th>
            <th class="col-desc">描述</th>
            <th class="col-count text-center">关联题目</th>
            <th class="col-status text-center">状态</th>
            <th class="col-action text-right">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in displayedList" :key="item.id" class="table-row">
            <td class="text-center">{{ (pagination.current - 1) * pagination.pageSize + index + 1 }}</td>
            <td>
              <span class="name-text">{{ item.name }}</span>
            </td>
            <td class="col-desc-cell">
              <span class="desc-text">{{ item.description || '-' }}</span>
            </td>
            <td class="text-center">
              <span class="count-badge clickable" @click="openQuestionList(item)">{{ item.questionCount || 0 }} 题</span>
            </td>
            <td class="text-center">
              <span :class="['status-pill', item.isActive ? 'status-active' : 'status-inactive']">
                {{ item.isActive ? '启用' : '停用' }}
              </span>
            </td>
            <td class="text-right">
              <div class="action-btns">
                <button class="btn-link" @click="openEditModal(item)">编辑</button>
                <button class="btn-link btn-link-danger" @click="handleDelete(item)">删除</button>
              </div>
            </td>
          </tr>
          <tr v-if="displayedList.length === 0 && !loading">
            <td colspan="6" class="empty-row">
              <div class="empty-state">
                <svg class="empty-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                <span>暂无知识点</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="loading" class="loading-overlay">
        <a-spin size="large" />
      </div>
    </div>

    <div class="footer-area">
      <div class="footer-left">
        <span class="page-info">共 {{ pagination.total }} 个知识点</span>
      </div>
      <div class="footer-right">
        <div class="page-size-selector">
          <span class="page-size-label">每页显示</span>
          <select class="page-size-select" :value="pagination.pageSize" @change="handlePageSizeChange(Number($event.target.value))">
            <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}条</option>
          </select>
        </div>
        <div class="pagination-btns">
          <button class="page-btn" :disabled="pagination.current <= 1" @click="changePage(pagination.current - 1)">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/></svg>
          </button>
          <button v-for="page in visiblePages" :key="page" class="page-btn" :class="{ 'page-btn-active': page === pagination.current }" @click="changePage(page)">{{ page }}</button>
          <button class="page-btn" :disabled="pagination.current >= totalPages" @click="changePage(pagination.current + 1)">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>
          </button>
        </div>
      </div>
    </div>

    <a-modal
      :open="modalOpen"
      :title="editingKnowledgePoint ? '编辑知识点' : '新增知识点'"
      ok-text="保存"
      cancel-text="取消"
      width="520px"
      @update:open="modalOpen = $event"
      @ok="handleSubmit"
      @cancel="modalOpen = false"
    >
      <a-form layout="vertical">
        <a-form-item label="知识点名称" required>
          <a-input v-model:value="form.name" :maxlength="100" show-count placeholder="如：行政处罚程序、接处警规范" />
          <div class="field-hint">仅维护可复用于题目与 AI 组卷的细粒度知识点</div>
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="form.description" :rows="3" :maxlength="500" show-count placeholder="请输入描述信息" />
        </a-form-item>
        <a-form-item label="状态">
          <a-switch v-model:checked="form.isActive" checked-children="启用" un-checked-children="停用" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 题目列表弹窗 -->
    <a-modal
      :open="questionModalOpen"
      :title="`知识点「${selectedKp?.name}」关联题目`"
      :footer="null"
      width="800px"
      @update:open="questionModalOpen = $event"
      @cancel="questionModalOpen = false"
    >
      <div v-if="questionLoading" class="question-loading">
        <a-spin size="large" />
      </div>
      <div v-else-if="kpQuestions.length === 0" class="empty-questions">
        <span>暂无关联题目</span>
      </div>
      <div v-else class="question-list">
        <div v-for="(q, idx) in kpQuestions" :key="q.id" class="question-item">
          <div class="question-header">
            <span class="question-num">{{ idx + 1 }}</span>
            <span :class="['question-type', `type-${q.type}`]">{{ getTypeText(q.type) }}</span>
          </div>
          <div class="question-content">{{ q.content }}</div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  createKnowledgePoint,
  deleteKnowledgePoint,
  getKnowledgePoints,
  updateKnowledgePoint,
} from '@/api/knowledgePoint'
import { getQuestions } from '@/api/question'

const loading = ref(false)
const modalOpen = ref(false)
const editingKnowledgePoint = ref(null)
const knowledgePointList = ref([])
const searchText = ref('')
const statusFilter = ref('all')
const questionModalOpen = ref(false)
const selectedKp = ref(null)
const kpQuestions = ref([])
const questionLoading = ref(false)

const form = reactive({
  name: '',
  description: '',
  isActive: true,
})

const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
})

const pageSizeOptions = [10, 20, 50]

const filteredList = computed(() => {
  let list = [...knowledgePointList.value]
  if (searchText.value) {
    const keyword = searchText.value.toLowerCase()
    list = list.filter((item) => item.name.toLowerCase().includes(keyword) || (item.description || '').toLowerCase().includes(keyword))
  }
  if (statusFilter.value !== 'all') {
    const active = statusFilter.value === 'true'
    list = list.filter((item) => item.isActive === active)
  }
  return list
})

const displayedList = computed(() => {
  const start = (pagination.current - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filteredList.value.slice(start, end)
})

const totalPages = computed(() => Math.ceil(filteredList.value.length / pagination.pageSize) || 1)

const visiblePages = computed(() => {
  const pages = []
  const total = totalPages.value
  const current = pagination.current
  let start = Math.max(1, current - 2)
  let end = Math.min(total, start + 4)
  if (end - start < 4) start = Math.max(1, end - 4)
  for (let i = start; i <= end; i += 1) {
    pages.push(i)
  }
  return pages
})

function resolveStatusFilter() {
  if (statusFilter.value === 'all') return undefined
  return statusFilter.value === 'true'
}

function resetForm(record = null) {
  form.name = record?.name || ''
  form.description = record?.description || ''
  form.isActive = record?.isActive ?? true
}

function openCreateModal() {
  editingKnowledgePoint.value = null
  resetForm()
  modalOpen.value = true
}

function openEditModal(record) {
  editingKnowledgePoint.value = record
  resetForm(record)
  modalOpen.value = true
}

function handleSearch() {
  pagination.current = 1
}

function changePage(page) {
  if (page < 1 || page > totalPages.value) return
  pagination.current = page
}

function handlePageSizeChange(size) {
  pagination.pageSize = size
  pagination.current = 1
}

async function loadKnowledgePoints() {
  loading.value = true
  try {
    const result = await getKnowledgePoints({
      page: 1,
      size: -1,
      search: searchText.value || undefined,
      isActive: resolveStatusFilter(),
    })
    knowledgePointList.value = result.items || []
    pagination.total = filteredList.value.length
  } catch (error) {
    message.error(error.message || '加载知识点失败')
  } finally {
    loading.value = false
  }
}

function reloadKnowledgePoints() {
  pagination.current = 1
  loadKnowledgePoints()
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

async function openQuestionList(kp) {
  selectedKp.value = kp
  questionModalOpen.value = true
  questionLoading.value = true
  kpQuestions.value = []
  try {
    const result = await getQuestions({ knowledgePointId: kp.id, size: -1 })
    kpQuestions.value = result.items || []
  } catch (error) {
    message.error(error.message || '加载题目失败')
    kpQuestions.value = []
  } finally {
    questionLoading.value = false
  }
}

function getTypeText(type) {
  const map = { single: '单选', multi: '多选', judge: '判断' }
  return map[type] || type
}

onMounted(() => {
  loadKnowledgePoints()
})
</script>

<style scoped>
.knowledge-point-panel {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 100%;
}

.toolbar-row {
  padding: 24px 32px;
  border-bottom: 1px solid #F1F5F9;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-primary {
  background: #2563EB;
  color: white;
  font-size: 18px;
  font-weight: 700;
  padding: 10px 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  box-shadow: 0 4px 6px rgba(37, 99, 235, 0.1);
}

.btn-primary:hover {
  background: #1D4ED8;
  transform: scale(0.98);
}

.search-wrapper {
  position: relative;
  width: 280px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 10px;
  width: 16px;
  height: 16px;
  color: #94A3B8;
  pointer-events: none;
}

.input-minimal {
  background-color: transparent;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 18px;
  color: #1E293B;
  transition: all 0.2s;
  outline: none;
  height: 36px;
}

.input-minimal:hover {
  border-color: #CBD5E1;
}

.input-minimal:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-wrapper .input-minimal {
  padding-left: 36px;
  width: 100%;
}

.filter-select {
  width: 140px;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2220%22%20height%3D%2220%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M5%207l5%205%205-5%22%20stroke%3D%22%2394A3B8%22%20stroke-width%3D%221.5%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  font-size: 16px;
  font-weight: 500;
  color: #64748B;
  cursor: pointer;
}

.table-wrapper {
  flex: 1;
  overflow-x: auto;
  position: relative;
}

.data-table {
  width: 100%;
  text-align: left;
  border-collapse: collapse;
  table-layout: fixed;
}

.data-table thead tr {
  background: #F8FAFC;
  border-bottom: 1px solid #F1F5F9;
}

.data-table th {
  padding: 14px 12px;
  font-size: 14px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  white-space: nowrap;
}

.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

.col-index {
  width: 60px;
}

.col-name {
  width: 160px;
}

.col-desc {
  width: 160px;
}

.col-desc-cell {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-count {
  width: 90px;
}

.col-status {
  width: 80px;
}

.col-action {
  width: 100px;
}

.table-row {
  transition: background-color 0.2s;
  border-bottom: 1px solid #F8FAFC;
}

.table-row:hover {
  background-color: #F8FAFC;
}

.data-table td {
  padding: 14px 12px;
  vertical-align: middle;
}

.name-text {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.desc-text {
  font-size: 16px;
  color: #64748B;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 15px;
  font-weight: 600;
  background: #EFF6FF;
  color: #2563EB;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 15px;
  font-weight: 600;
}

.status-active {
  background: #DCFCE7;
  color: #16A34A;
}

.status-inactive {
  background: #F1F5F9;
  color: #94A3B8;
}

.action-btns {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-link {
  background: none;
  border: none;
  color: #2563EB;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 0;
  transition: color 0.2s;
}

.btn-link:hover {
  color: #1D4ED8;
  text-decoration: underline;
}

.btn-link-danger {
  color: #EF4444;
}

.btn-link-danger:hover {
  color: #DC2626;
}

.empty-row {
  text-align: center;
  padding: 60px;
  color: #94A3B8;
  font-size: 18px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: #CBD5E1;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.7);
}

.footer-area {
  padding: 20px 32px;
  border-top: 1px solid #F1F5F9;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.page-info {
  font-size: 16px;
  color: #64748B;
  font-weight: 500;
}

.pagination-btns {
  display: flex;
  gap: 4px;
}

.page-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
  font-weight: 600;
  color: #64748B;
}

.page-btn:hover:not(:disabled) {
  background: #F1F5F9;
}

.page-btn:disabled {
  color: #CBD5E1;
  cursor: not-allowed;
}

.page-btn-active {
  background: #1E293B;
  color: white;
  border-color: #1E293B;
}

.page-size-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-size-label {
  font-size: 16px;
  color: #94A3B8;
  font-weight: 500;
}

.page-size-select {
  font-size: 16px;
  color: #64748B;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  padding: 4px 28px 4px 8px;
  background: white;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2220%22%20height%3D%2220%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M5%207l5%205%205-5%22%20stroke%3D%22%2394A3B8%22%20stroke-width%3D%221.5%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 4px center;
  background-size: 16px;
  transition: all 0.2s;
}

.page-size-select:hover {
  border-color: #CBD5E1;
}

.field-hint {
  margin-top: 6px;
  color: #94A3B8;
  font-size: 16px;
  line-height: 1.5;
}

.clickable {
  cursor: pointer;
  transition: all 0.2s;
}

.clickable:hover {
  background: #DBEAFE;
  color: #1D4ED8;
}

.empty-questions {
  text-align: center;
  padding: 40px;
  color: #94A3B8;
  font-size: 14px;
}

.question-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 180px;
}

.question-list {
  max-height: 500px;
  overflow-y: auto;
}

.question-item {
  padding: 12px;
  border-bottom: 1px solid #F1F5F9;
}

.question-item:last-child {
  border-bottom: none;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.question-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #E2E8F0;
  font-size: 12px;
  font-weight: 600;
  color: #64748B;
}

.question-type {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.type-single {
  background: #EFF6FF;
  color: #2563EB;
}

.type-multi {
  background: #F0FDF4;
  color: #16A34A;
}

.type-judge {
  background: #FEF3C7;
  color: #D97706;
}

.question-content {
  font-size: 14px;
  color: #334155;
  line-height: 1.6;
}
</style>
