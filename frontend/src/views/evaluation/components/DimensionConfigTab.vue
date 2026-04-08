<template>
  <div>
    <a-tabs v-model:activeKey="activeTargetType" size="small" type="card" style="margin-bottom: 16px">
      <a-tab-pane key="course" tab="课程评价" />
      <a-tab-pane key="instructor" tab="教官评价" />
      <a-tab-pane key="training" tab="培训班评价" />
      <a-tab-pane key="training_base" tab="培训基地评价" />
    </a-tabs>

    <a-spin :spinning="loading">
      <div v-if="currentTemplate" class="template-info">
        <a-descriptions :column="2" size="small" bordered>
          <a-descriptions-item label="模板名称">{{ currentTemplate.name }}</a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-switch
              :checked="currentTemplate.enabled"
              checked-children="启用"
              un-checked-children="停用"
              @change="(val) => handleToggleTemplate(val)"
            />
          </a-descriptions-item>
          <a-descriptions-item label="说明" :span="2">{{ currentTemplate.description || '未设置' }}</a-descriptions-item>
        </a-descriptions>
      </div>

      <div class="dim-toolbar">
        <span class="dim-title">评价维度</span>
        <a-button type="primary" size="small" @click="openDimModal()">添加维度</a-button>
      </div>

      <a-table :data-source="currentDimensions" :columns="dimColumns" :pagination="false" row-key="id" size="small">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="openDimModal(record)">编辑</a-button>
              <a-popconfirm title="确定删除该维度？" @confirm="handleDeleteDim(record.id)">
                <a-button type="link" size="small" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-spin>

    <a-modal
      v-model:open="dimModalVisible"
      :title="dimEditingId ? '编辑维度' : '添加维度'"
      :confirm-loading="dimSaving"
      ok-text="保存"
      @ok="handleSaveDim"
    >
      <a-form layout="vertical">
        <a-form-item label="维度名称" required>
          <a-input v-model:value="dimForm.name" placeholder="如：教学质量" :maxlength="100" />
        </a-form-item>
        <a-form-item label="维度说明">
          <a-input v-model:value="dimForm.description" placeholder="选填" :maxlength="500" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="排序">
              <a-input-number v-model:value="dimForm.sortOrder" :min="0" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="权重">
              <a-input-number v-model:value="dimForm.weight" :min="0" :step="0.1" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import request from '@/api/request'

const loading = ref(false)
const templates = ref([])
const activeTargetType = ref('course')

const currentTemplate = computed(() =>
  templates.value.find((t) => t.targetType === activeTargetType.value) || null,
)
const currentDimensions = computed(() => currentTemplate.value?.dimensions || [])

const dimColumns = [
  { title: '排序', dataIndex: 'sortOrder', key: 'sortOrder', width: 70 },
  { title: '维度名称', dataIndex: 'name', key: 'name' },
  { title: '说明', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '权重', dataIndex: 'weight', key: 'weight', width: 80 },
  { title: '操作', key: 'action', width: 140 },
]

async function fetchTemplates() {
  loading.value = true
  try {
    templates.value = await request.get('/evaluations/templates') || []
  } catch {
    templates.value = []
  } finally {
    loading.value = false
  }
}

async function handleToggleTemplate(enabled) {
  if (!currentTemplate.value) return
  try {
    await request.put(`/evaluations/templates/${currentTemplate.value.id}`, { enabled })
    message.success(enabled ? '已启用' : '已停用')
    fetchTemplates()
  } catch (err) {
    message.error(err.message || '操作失败')
  }
}

const dimModalVisible = ref(false)
const dimSaving = ref(false)
const dimEditingId = ref(null)
const dimForm = reactive({ name: '', description: '', sortOrder: 0, weight: 1.0 })

function openDimModal(record) {
  if (record) {
    dimEditingId.value = record.id
    dimForm.name = record.name || ''
    dimForm.description = record.description || ''
    dimForm.sortOrder = record.sortOrder ?? 0
    dimForm.weight = record.weight ?? 1.0
  } else {
    dimEditingId.value = null
    dimForm.name = ''
    dimForm.description = ''
    dimForm.sortOrder = currentDimensions.value.length
    dimForm.weight = 1.0
  }
  dimModalVisible.value = true
}

async function handleSaveDim() {
  if (!dimForm.name.trim()) { message.warning('请输入维度名称'); return }
  dimSaving.value = true
  try {
    const payload = { name: dimForm.name.trim(), description: dimForm.description?.trim() || undefined, sortOrder: dimForm.sortOrder, weight: dimForm.weight }
    if (dimEditingId.value) {
      await request.put(`/evaluations/dimensions/${dimEditingId.value}`, payload)
      message.success('维度已更新')
    } else {
      await request.post(`/evaluations/templates/${currentTemplate.value.id}/dimensions`, payload)
      message.success('维度已添加')
    }
    dimModalVisible.value = false
    fetchTemplates()
  } catch (err) {
    message.error(err.message || '保存失败')
  } finally {
    dimSaving.value = false
  }
}

async function handleDeleteDim(dimId) {
  try {
    await request.delete(`/evaluations/dimensions/${dimId}`)
    message.success('已删除')
    fetchTemplates()
  } catch (err) {
    message.error(err.message || '删除失败')
  }
}

onMounted(fetchTemplates)
</script>

<style scoped>
.template-info { margin-bottom: 16px; }
.dim-toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.dim-title { font-size: 15px; font-weight: 600; color: #1f1f1f; }
</style>
