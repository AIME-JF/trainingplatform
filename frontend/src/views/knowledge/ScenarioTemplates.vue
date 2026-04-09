<template>
  <div class="scenario-templates-page">
    <div class="page-header">
      <h2>场景模板管理</h2>
      <a-button type="primary" @click="openEditor()">创建场景模板</a-button>
    </div>

    <a-card :bordered="false">
      <div class="filters">
        <a-select
          v-model:value="query.category"
          placeholder="场景分类"
          allow-clear
          style="width: 180px"
          @change="fetchList"
        >
          <a-select-option value="law_enforcement">执法场景对话</a-select-option>
          <a-select-option value="record_taking">笔录模拟训练</a-select-option>
          <a-select-option value="law_application">法律适用推演</a-select-option>
        </a-select>
        <a-select
          v-model:value="query.status"
          placeholder="状态"
          allow-clear
          style="width: 140px"
          @change="fetchList"
        >
          <a-select-option value="draft">草稿</a-select-option>
          <a-select-option value="published">已发布</a-select-option>
          <a-select-option value="archived">已归档</a-select-option>
        </a-select>
      </div>

      <a-table
        :columns="columns"
        :data-source="list"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'category'">
            <a-tag :color="categoryColorMap[record.category]">{{ categoryLabelMap[record.category] }}</a-tag>
          </template>
          <template v-else-if="column.key === 'difficulty'">
            <a-rate :value="record.difficulty" disabled :count="5" style="font-size: 12px" />
          </template>
          <template v-else-if="column.key === 'status'">
            <a-badge :status="statusBadgeMap[record.status]" :text="statusLabelMap[record.status]" />
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a @click="openEditor(record.id)">编辑</a>
              <a-popconfirm
                v-if="record.status === 'draft'"
                title="确认发布该模板吗？"
                @confirm="handlePublish(record.id)"
              >
                <a style="color: #1677ff">发布</a>
              </a-popconfirm>
              <a-popconfirm title="确认删除该模板吗？" @confirm="handleDelete(record.id)">
                <a style="color: #ff4d4f">删除</a>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-drawer
      v-model:open="editorVisible"
      :title="editingId ? '编辑场景模板' : '创建场景模板'"
      width="720"
      @close="editorVisible = false"
    >
      <a-form :model="form" layout="vertical">
        <a-form-item label="场景名称" required>
          <a-input v-model:value="form.title" placeholder="如：醉驾查处现场处置" />
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="场景分类" required>
              <a-select v-model:value="form.category">
                <a-select-option value="law_enforcement">执法场景对话</a-select-option>
                <a-select-option value="record_taking">笔录模拟训练</a-select-option>
                <a-select-option value="law_application">法律适用推演</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="难度等级">
              <a-rate v-model:value="form.difficulty" :count="5" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="预计时长（分钟）">
          <a-input-number v-model:value="form.estimatedMinutes" :min="5" :max="90" style="width: 100%" />
        </a-form-item>
        <a-form-item label="场景描述">
          <a-textarea v-model:value="form.description" :rows="2" />
        </a-form-item>
        <a-form-item label="场景背景" required>
          <a-textarea v-model:value="form.background" :rows="4" placeholder="详细描述场景背景" />
        </a-form-item>
        <a-form-item label="AI扮演角色" required>
          <a-textarea v-model:value="form.npcRole" :rows="3" placeholder="描述 AI 角色特征、立场和行为风格" />
        </a-form-item>
        <a-form-item label="AI角色名称">
          <a-input v-model:value="form.npcName" placeholder="如：涉案人员、报警人、证人" />
        </a-form-item>
        <a-form-item label="AI开场白">
          <a-textarea v-model:value="form.npcOpening" :rows="2" />
        </a-form-item>
        <a-form-item label="关联知识点">
          <a-select
            v-model:value="form.knowledgeItemIds"
            mode="multiple"
            allow-clear
            :max-tag-count="4"
            placeholder="可多选知识点，不选则按通用场景进行模拟"
          >
            <a-select-option
              v-for="item in knowledgeItems"
              :key="item.id"
              :value="item.id"
            >
              {{ item.title }}{{ item.meta ? ` · ${item.meta}` : '' }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-divider>考察要点</a-divider>
        <div
          v-for="(checkpoint, index) in form.checkpoints"
          :key="index"
          class="checkpoint-row"
        >
          <a-input v-model:value="checkpoint.label" placeholder="考察要点" style="flex: 1" />
          <a-input-number v-model:value="checkpoint.score" :min="1" :max="100" placeholder="分值" style="width: 90px" />
          <a-button type="text" danger @click="form.checkpoints.splice(index, 1)">删除</a-button>
        </div>
        <a-button type="dashed" block @click="form.checkpoints.push({ label: '', score: 10 })">
          + 添加要点
        </a-button>
      </a-form>

      <template #footer>
        <a-space>
          <a-button @click="editorVisible = false">取消</a-button>
          <a-button type="primary" :loading="saving" @click="handleSave">
            {{ editingId ? '保存' : '创建' }}
          </a-button>
        </a-space>
      </template>
    </a-drawer>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  createScenarioTemplate,
  deleteScenarioTemplate,
  getScenarioTemplate,
  getScenarioTemplates,
  publishScenarioTemplate,
  updateScenarioTemplate,
} from '@/api/knowledge'
import { getLibraryItems } from '@/api/library'

const loading = ref(false)
const saving = ref(false)
const editorVisible = ref(false)
const editingId = ref(null)
const list = ref([])
const knowledgeItems = ref([])
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })
const query = reactive({ category: undefined, status: undefined })

const form = reactive({
  title: '',
  category: undefined,
  difficulty: 3,
  estimatedMinutes: 15,
  description: '',
  background: '',
  npcRole: '',
  npcName: '',
  npcOpening: '',
  knowledgeItemIds: [],
  checkpoints: [{ label: '', score: 10 }],
})

const columns = [
  { title: '场景名称', dataIndex: 'title', key: 'title' },
  { title: '分类', key: 'category', width: 120 },
  { title: '难度', key: 'difficulty', width: 160 },
  { title: '状态', key: 'status', width: 100 },
  { title: '使用次数', dataIndex: 'usageCount', key: 'usageCount', width: 100 },
  { title: '操作', key: 'actions', width: 220 },
]

const categoryLabelMap = {
  law_enforcement: '执法场景',
  record_taking: '笔录训练',
  law_application: '法律推演',
}
const categoryColorMap = {
  law_enforcement: 'blue',
  record_taking: 'green',
  law_application: 'orange',
}
const statusLabelMap = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档',
}
const statusBadgeMap = {
  draft: 'default',
  published: 'success',
  archived: 'warning',
}

onMounted(() => {
  void fetchKnowledgeItems()
  void fetchList()
})

async function fetchKnowledgeItems() {
  try {
    const response = await getLibraryItems({
      page: 1,
      size: -1,
      scope: 'accessible',
      category: 'knowledge',
    })
    knowledgeItems.value = (response.items || []).map((item) => ({
      id: item.id,
      title: item.title,
      meta: [item.ownerName, item.isPublic ? '公共' : '私人'].filter(Boolean).join(' · '),
    }))
  } catch {
    knowledgeItems.value = []
  }
}

async function fetchList() {
  loading.value = true
  try {
    const response = await getScenarioTemplates({
      page: pagination.current,
      size: pagination.pageSize,
      category: query.category,
      status: query.status,
    })
    list.value = response.items || []
    pagination.total = response.total || 0
  } finally {
    loading.value = false
  }
}

function handleTableChange(pag) {
  pagination.current = pag.current
  void fetchList()
}

function resetForm() {
  form.title = ''
  form.category = undefined
  form.difficulty = 3
  form.estimatedMinutes = 15
  form.description = ''
  form.background = ''
  form.npcRole = ''
  form.npcName = ''
  form.npcOpening = ''
  form.knowledgeItemIds = []
  form.checkpoints = [{ label: '', score: 10 }]
}

async function openEditor(id) {
  resetForm()
  editingId.value = id || null
  if (id) {
    try {
      const template = await getScenarioTemplate(id)
      Object.assign(form, {
        title: template.title,
        category: template.category,
        difficulty: template.difficulty,
        estimatedMinutes: template.estimatedMinutes,
        description: template.description || '',
        background: template.background,
        npcRole: template.npcRole,
        npcName: template.npcName || '',
        npcOpening: template.npcOpening || '',
        knowledgeItemIds: template.knowledgeItemIds || [],
        checkpoints: template.checkpoints?.length ? template.checkpoints : [{ label: '', score: 10 }],
      })
    } catch {
      message.error('获取模板详情失败')
      return
    }
  }
  editorVisible.value = true
}

async function handleSave() {
  if (!form.title || !form.category || !form.background || !form.npcRole) {
    message.warning('请填写必填项')
    return
  }

  saving.value = true
  try {
    const payload = {
      ...form,
      knowledgeItemIds: [...form.knowledgeItemIds],
      checkpoints: [...form.checkpoints],
    }
    if (editingId.value) {
      await updateScenarioTemplate(editingId.value, payload)
    } else {
      await createScenarioTemplate(payload)
    }
    message.success(editingId.value ? '保存成功' : '创建成功')
    editorVisible.value = false
    void fetchList()
  } catch (error) {
    message.error(error?.message || '操作失败')
  } finally {
    saving.value = false
  }
}

async function handlePublish(id) {
  try {
    await publishScenarioTemplate(id)
    message.success('发布成功')
    void fetchList()
  } catch {
    message.error('发布失败')
  }
}

async function handleDelete(id) {
  try {
    await deleteScenarioTemplate(id)
    message.success('删除成功')
    void fetchList()
  } catch {
    message.error('删除失败')
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
}

.filters {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.checkpoint-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
