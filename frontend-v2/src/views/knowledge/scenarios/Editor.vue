<template>
  <div class="page-content scenario-editor-page">
    <div class="editor-header">
      <a-button @click="router.push('/knowledge/scenarios')">返回</a-button>
      <h1 class="editor-title">{{ isEdit ? '编辑场景模板' : '创建场景模板' }}</h1>
    </div>

    <a-form :model="form" layout="vertical" class="editor-form" @finish="handleSubmit">
      <a-card :bordered="false" title="基本信息" class="editor-card">
        <a-form-item label="场景名称" name="title" :rules="[{ required: true, message: '请输入场景名称' }]">
          <a-input v-model:value="form.title" placeholder="如：醉驾查处现场处置" />
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="场景分类" name="category" :rules="[{ required: true, message: '请选择场景分类' }]">
              <a-select v-model:value="form.category" placeholder="选择分类">
                <a-select-option value="law_enforcement">执法场景对话</a-select-option>
                <a-select-option value="record_taking">笔录模拟训练</a-select-option>
                <a-select-option value="law_application">法律适用推演</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="难度等级" name="difficulty">
              <a-rate v-model:value="form.difficulty" :count="5" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="预计时长（分钟）" name="estimatedMinutes">
          <a-input-number v-model:value="form.estimatedMinutes" :min="5" :max="60" />
        </a-form-item>

        <a-form-item label="场景描述" name="description">
          <a-textarea v-model:value="form.description" :rows="2" placeholder="简要描述场景内容和训练目标" />
        </a-form-item>
      </a-card>

      <a-card :bordered="false" title="场景设定" class="editor-card">
        <a-form-item label="场景背景" name="background" :rules="[{ required: true, message: '请输入场景背景' }]">
          <a-textarea
            v-model:value="form.background"
            :rows="4"
            placeholder="详细描述场景背景信息，这段文字将在模拟开始时展示给学员。"
          />
        </a-form-item>

        <a-form-item label="AI扮演角色" name="npcRole" :rules="[{ required: true, message: '请描述 AI 扮演的角色' }]">
          <a-textarea
            v-model:value="form.npcRole"
            :rows="3"
            placeholder="描述 AI 角色特征和行为模式。"
          />
        </a-form-item>

        <a-form-item label="AI角色名称" name="npcName">
          <a-input v-model:value="form.npcName" placeholder="如：驾驶员、报警人、嫌疑人" />
        </a-form-item>

        <a-form-item label="AI开场白" name="npcOpening">
          <a-textarea
            v-model:value="form.npcOpening"
            :rows="2"
            placeholder="模拟开始时 AI 首先说的话。"
          />
        </a-form-item>
      </a-card>

      <a-card :bordered="false" title="考察要点与评判" class="editor-card">
        <div class="checkpoints-list">
          <div v-for="(cp, idx) in form.checkpoints" :key="idx" class="checkpoint-item">
            <a-input v-model:value="cp.label" placeholder="考察要点，如：是否出示执法证件" class="checkpoint-input" />
            <a-input-number v-model:value="cp.score" :min="1" :max="100" placeholder="分值" class="checkpoint-score" />
            <a-button type="text" danger @click="removeCheckpoint(idx)">删除</a-button>
          </div>
        </div>
        <a-button type="dashed" block style="margin-top: 12px" @click="addCheckpoint">
          + 添加考察要点
        </a-button>
      </a-card>

      <a-card :bordered="false" title="关联知识点" class="editor-card">
        <a-form-item label="知识点" name="knowledgeItemIds">
          <KnowledgeItemSelector
            v-model="form.knowledgeItemIds"
            placeholder="可多选知识点，场景模拟时会将这些知识点注入提示词"
          />
        </a-form-item>
        <p class="form-tip">关联知识点后，AI 会优先基于这些知识点进行场景对话和反馈。</p>
      </a-card>

      <div class="editor-actions">
        <a-button @click="router.push('/knowledge/scenarios')">取消</a-button>
        <a-button type="primary" html-type="submit" :loading="submitting">
          {{ isEdit ? '保存修改' : '创建模板' }}
        </a-button>
      </div>
    </a-form>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import KnowledgeItemSelector from '@/components/library/KnowledgeItemSelector.vue'
import {
  createScenarioTemplate,
  getScenarioTemplate,
  updateScenarioTemplate,
} from '@/api/knowledge'

const route = useRoute()
const router = useRouter()
const submitting = ref(false)
const isEdit = computed(() => !!route.params.id)

const form = reactive({
  title: '',
  category: undefined as string | undefined,
  difficulty: 3,
  estimatedMinutes: 15,
  description: '',
  background: '',
  npcRole: '',
  npcName: '',
  npcOpening: '',
  knowledgeItemIds: [] as number[],
  checkpoints: [
    { label: '', score: 10 },
  ] as { label: string; score: number }[],
})

onMounted(() => {
  if (isEdit.value) {
    void fetchScenario()
  }
})

async function fetchScenario() {
  try {
    const res = await getScenarioTemplate(Number(route.params.id))
    const data = res.data || res
    form.title = data.title || ''
    form.category = data.category
    form.difficulty = data.difficulty || 3
    form.estimatedMinutes = data.estimatedMinutes || 15
    form.description = data.description || ''
    form.background = data.background || ''
    form.npcRole = data.npcRole || ''
    form.npcName = data.npcName || ''
    form.npcOpening = data.npcOpening || ''
    form.knowledgeItemIds = data.knowledgeItemIds || []
    form.checkpoints = data.checkpoints?.length ? data.checkpoints : [{ label: '', score: 10 }]
  } catch (error) {
    message.error(error instanceof Error ? error.message : '获取场景详情失败')
  }
}

function addCheckpoint() {
  form.checkpoints.push({ label: '', score: 10 })
}

function removeCheckpoint(idx: number) {
  form.checkpoints.splice(idx, 1)
}

async function handleSubmit() {
  submitting.value = true
  try {
    const payload = { ...form }
    if (isEdit.value) {
      await updateScenarioTemplate(Number(route.params.id), payload)
    } else {
      await createScenarioTemplate(payload)
    }
    message.success(isEdit.value ? '保存成功' : '创建成功')
    void router.push('/knowledge/scenarios')
  } catch (error) {
    message.error(error instanceof Error ? error.message : '操作失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.scenario-editor-page {
  max-width: 800px;
  margin: 0 auto;
}

.editor-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.editor-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.editor-card {
  border-radius: var(--v2-radius-lg);
  margin-bottom: 16px;
}

.checkpoints-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.checkpoint-item {
  display: flex;
  gap: 10px;
  align-items: center;
}

.checkpoint-input {
  flex: 1;
}

.checkpoint-score {
  width: 100px;
}

.form-tip {
  font-size: 13px;
  color: var(--v2-text-muted);
  margin: 0;
}

.editor-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 24px 0;
}
</style>
