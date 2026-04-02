<template>
  <div class="notice-manage-page">
    <div class="page-header">
      <div>
        <h2>通知管理</h2>
        <p class="page-sub">管理平台公告，发布后所有用户可在通知中心查看</p>
      </div>
      <a-button type="primary" @click="openCreateModal">
        <PlusOutlined /> 发布公告
      </a-button>
    </div>

    <a-card :bordered="false">
      <a-table
        :data-source="notices"
        :columns="columns"
        :loading="loading"
        row-key="id"
        :pagination="pagination"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'title'">
            <a @click="openDetail(record)">{{ record.title }}</a>
          </template>
          <template v-else-if="column.key === 'authorName'">
            {{ record.authorName || '-' }}
          </template>
          <template v-else-if="column.key === 'createdAt'">
            {{ formatTime(record.createdAt) }}
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="openEditModal(record)">编辑</a-button>
              <a-popconfirm title="确定要删除该公告吗？" @confirm="handleDelete(record.id)">
                <a-button type="link" size="small" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 创建/编辑弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingNotice ? '编辑公告' : '发布公告'"
      :confirm-loading="saving"
      ok-text="保存"
      width="640px"
      @ok="handleSave"
    >
      <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }" style="margin-top: 16px">
        <a-form-item label="标题" required>
          <a-input v-model:value="form.title" placeholder="请输入公告标题" :maxlength="200" show-count />
        </a-form-item>
        <a-form-item label="内容" required>
          <a-textarea v-model:value="form.content" placeholder="请输入公告内容" :rows="6" :maxlength="5000" show-count />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 详情弹窗 -->
    <a-modal v-model:open="detailVisible" :title="detailNotice?.title" :footer="null" width="640px">
      <div class="notice-detail">
        <div class="notice-detail-meta">
          <span v-if="detailNotice?.authorName">发布人：{{ detailNotice.authorName }}</span>
          <span>{{ formatTime(detailNotice?.createdAt) }}</span>
        </div>
        <div class="notice-detail-content">{{ detailNotice?.content }}</div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import dayjs from 'dayjs'
import { getNotices, createNotice, updateNotice, deleteNotice } from '@/api/notice'

const loading = ref(false)
const saving = ref(false)
const notices = ref([])
const modalVisible = ref(false)
const detailVisible = ref(false)
const editingNotice = ref(null)
const detailNotice = ref(null)

const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 条`,
})

const form = reactive({
  title: '',
  content: '',
})

const columns = [
  { title: '标题', key: 'title', ellipsis: true },
  { title: '发布人', key: 'authorName', width: 120 },
  { title: '发布时间', key: 'createdAt', width: 180 },
  { title: '操作', key: 'action', width: 140, fixed: 'right' },
]

function formatTime(time) {
  if (!time) return '-'
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

async function fetchNotices() {
  loading.value = true
  try {
    const res = await getNotices({
      page: pagination.current,
      size: pagination.pageSize,
      type: 'system',
    })
    notices.value = res.items || []
    pagination.total = res.total || 0
  } catch {
    notices.value = []
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag) {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchNotices()
}

function openCreateModal() {
  editingNotice.value = null
  form.title = ''
  form.content = ''
  modalVisible.value = true
}

function openEditModal(record) {
  editingNotice.value = record
  form.title = record.title
  form.content = record.content
  modalVisible.value = true
}

function openDetail(record) {
  detailNotice.value = record
  detailVisible.value = true
}

async function handleSave() {
  if (!form.title?.trim()) {
    message.warning('请输入公告标题')
    return
  }
  if (!form.content?.trim()) {
    message.warning('请输入公告内容')
    return
  }
  saving.value = true
  try {
    if (editingNotice.value) {
      await updateNotice(editingNotice.value.id, {
        title: form.title.trim(),
        content: form.content.trim(),
      })
      message.success('更新成功')
    } else {
      await createNotice({
        title: form.title.trim(),
        content: form.content.trim(),
        type: 'system',
      })
      message.success('发布成功')
    }
    modalVisible.value = false
    fetchNotices()
  } catch (err) {
    message.error(err?.message || '操作失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id) {
  try {
    await deleteNotice(id)
    message.success('删除成功')
    fetchNotices()
  } catch (err) {
    message.error(err?.message || '删除失败')
  }
}

onMounted(() => {
  fetchNotices()
})
</script>

<style scoped>
.notice-manage-page {
  padding: 24px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 600;
}

.page-sub {
  margin: 0;
  font-size: 13px;
  color: #8c8c8c;
}

.notice-detail {
  padding: 8px 0;
}

.notice-detail-meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #8c8c8c;
  margin-bottom: 16px;
}

.notice-detail-content {
  font-size: 14px;
  line-height: 1.8;
  color: #333;
  white-space: pre-wrap;
}
</style>
