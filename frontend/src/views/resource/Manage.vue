<template>
  <div class="resource-manage-page">
    <div class="page-header">
      <h2>资源管理</h2>
      <a-button @click="fetchList">刷新</a-button>
    </div>

    <a-card :bordered="false" style="margin-bottom: 16px">
      <a-row :gutter="12">
        <a-col :xs="24" :sm="12" :md="8">
          <a-input-search
            v-model:value="query.search"
            placeholder="搜索资源标题"
            @search="handleSearch"
          />
        </a-col>
        <a-col :xs="12" :sm="6" :md="5">
          <a-select v-model:value="query.status" style="width: 100%" @change="handleSearch">
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="draft">草稿</a-select-option>
            <a-select-option value="pending_review">待审核</a-select-option>
            <a-select-option value="reviewing">审核中</a-select-option>
            <a-select-option value="published">已发布</a-select-option>
            <a-select-option value="rejected">已驳回</a-select-option>
            <a-select-option value="offline">已下线</a-select-option>
          </a-select>
        </a-col>
        <a-col :xs="12" :sm="6" :md="5">
          <a-select v-model:value="query.contentType" style="width: 100%" @change="handleSearch">
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="video">视频</a-select-option>
            <a-select-option value="image">图片</a-select-option>
            <a-select-option value="document">文档</a-select-option>
          </a-select>
        </a-col>
        <a-col :xs="24" :sm="24" :md="6">
          <a-space>
            <a-button type="primary" @click="handleSearch">搜索</a-button>
            <a-button @click="handleReset">重置</a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <a-card :bordered="false">
      <a-table
        :data-source="rows"
        :columns="columns"
        :loading="loading"
        :pagination="false"
        row-key="id"
        :scroll="{ x: 980 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColor(record.status)">{{ statusLabel(record.status) }}</a-tag>
          </template>
          <template v-if="column.key === 'contentType'">
            {{ contentTypeLabel(record.contentType) }}
          </template>
          <template v-if="column.key === 'createdAt'">
            {{ formatDate(record.createdAt) }}
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="viewDetail(record.id)">查看</a-button>
              <a-button
                v-if="record.status === 'published'"
                size="small"
                danger
                ghost
                @click="offline(record.id)"
              >
                下线
              </a-button>
              <a-popconfirm
                title="确认删除该资源吗？"
                ok-text="删除"
                cancel-text="取消"
                @confirm="removeResource(record.id)"
              >
                <a-button size="small" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>

      <div class="pager-wrap">
        <a-pagination
          :current="query.page"
          :page-size="query.size"
          :total="total"
          show-size-changer
          :page-size-options="['10', '20', '50']"
          @change="onPageChange"
          @showSizeChange="onSizeChange"
        />
      </div>
    </a-card>
  </div>
</template>

<script setup>
import dayjs from 'dayjs'
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { getResources, offlineResource, deleteResource } from '@/api/resource'

const router = useRouter()

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const query = reactive({
  page: 1,
  size: 10,
  search: '',
  status: '',
  contentType: '',
})

const columns = [
  { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
  { title: '状态', dataIndex: 'status', key: 'status', width: 110 },
  { title: '类型', dataIndex: 'contentType', key: 'contentType', width: 100 },
  { title: '上传者', dataIndex: 'uploaderName', key: 'uploaderName', width: 120 },
  { title: '归属部门', dataIndex: 'ownerDepartmentName', key: 'ownerDepartmentName', width: 140 },
  { title: '创建时间', dataIndex: 'createdAt', key: 'createdAt', width: 180 },
  { title: '操作', key: 'action', width: 220, fixed: 'right' },
]

onMounted(() => {
  fetchList()
})

function contentTypeLabel(type) {
  const map = {
    video: '视频',
    document: '文档',
    image: '图片',
    image_text: '图片',
  }
  return map[type] || type || '-'
}

function statusLabel(status) {
  const map = {
    draft: '草稿',
    pending_review: '待审核',
    reviewing: '审核中',
    published: '已发布',
    rejected: '已驳回',
    offline: '已下线',
  }
  return map[status] || status || '-'
}

function statusColor(status) {
  const map = {
    draft: 'default',
    pending_review: 'gold',
    reviewing: 'blue',
    published: 'green',
    rejected: 'red',
    offline: 'orange',
  }
  return map[status] || 'default'
}

function formatDate(value) {
  if (!value) return '-'
  return dayjs(value).format('YYYY-MM-DD HH:mm')
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getResources(query)
    rows.value = res.items || []
    total.value = res.total || 0
  } catch (e) {
    message.error(e.message || '加载资源失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  query.page = 1
  fetchList()
}

function handleReset() {
  query.page = 1
  query.size = 10
  query.search = ''
  query.status = ''
  query.contentType = ''
  fetchList()
}

function onPageChange(page, size) {
  query.page = page
  query.size = size
  fetchList()
}

function onSizeChange(_, size) {
  query.page = 1
  query.size = size
  fetchList()
}

function viewDetail(id) {
  router.push(`/resource/detail/${id}`)
}

async function offline(id) {
  try {
    await offlineResource(id)
    message.success('资源已下线')
    fetchList()
  } catch (e) {
    message.error(e.message || '下线失败')
  }
}

async function removeResource(id) {
  try {
    await deleteResource(id)
    message.success('删除成功')
    fetchList()
  } catch (e) {
    message.error(e.message || '删除失败')
  }
}
</script>

<style scoped>
.resource-manage-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.pager-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
