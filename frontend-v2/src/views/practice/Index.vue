<template>
  <div class="practice-page">
    <div class="page-header">
      <h1 class="page-title">刷题练习</h1>
      <p class="page-subtitle">选择知识点或题库开始练习</p>
    </div>

    <div class="mode-tabs">
      <button
        class="mode-tab"
        :class="{ active: activeSourceType === 'knowledge-point' }"
        @click="selectSourceType('knowledge-point')"
      >
        按知识点
      </button>
      <button
        class="mode-tab"
        :class="{ active: activeSourceType === 'question-folder' }"
        @click="selectSourceType('question-folder')"
      >
        按题库/科目
      </button>
    </div>

    <div class="filter-section">
      <div class="filter-item">
        <label class="filter-label">{{ currentSelectorLabel }}</label>
        <select v-model="selectedSourceId" class="filter-select">
          <option value="">{{ currentPlaceholder }}</option>
          <option
            v-for="item in currentSources"
            :key="item.id"
            :value="String(item.id)"
          >
            {{ item.display_name || item.name }} ({{ item.question_count || 0 }}题)
          </option>
        </select>
      </div>
      <p class="filter-hint">{{ currentHint }}</p>
    </div>

    <div v-if="selectedSource" class="question-preview">
      <div class="preview-header">
        <span class="preview-title">{{ selectedSourceTypeLabel }}</span>
        <span class="preview-count">{{ selectedSource.question_count || 0 }} 题</span>
      </div>
      <div class="preview-name">{{ selectedSource.name }}</div>
      <div v-if="selectedSourceMeta" class="preview-meta">{{ selectedSourceMeta }}</div>
      <div v-if="selectedSource.description" class="preview-desc">{{ selectedSource.description }}</div>
    </div>

    <p v-else-if="!loading && !currentSources.length" class="empty-tip">
      当前暂无可练习的{{ currentSelectorLabel }}
    </p>

    <div class="action-area">
      <button
        class="btn-start"
        :disabled="!selectedSourceId"
        @click="startPractice"
      >
        开始练习
      </button>
    </div>

    <div class="loading-overlay" v-if="loading">
      <a-spin size="large" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { getKnowledgePointsApiV1KnowledgePointsGet } from '@/api/generated/knowledge-point-management/knowledge-point-management'
import { getQuestionFoldersApiV1QuestionsFoldersGet } from '@/api/generated/question-management/question-management'

const router = useRouter()

const loading = ref(false)
const activeSourceType = ref('knowledge-point')
const selectedSourceId = ref('')
const knowledgePoints = ref([])
const questionFolders = ref([])

const currentSelectorLabel = computed(() => (
  activeSourceType.value === 'knowledge-point' ? '知识点' : '题库/科目'
))

const currentPlaceholder = computed(() => (
  activeSourceType.value === 'knowledge-point' ? '请选择知识点' : '请选择题库或科目'
))

const currentHint = computed(() => (
  activeSourceType.value === 'knowledge-point'
    ? '按知识点筛选题目进行专项练习。'
    : '按题库、科目或其下级分类递归加载题目。'
))

const selectedSourceTypeLabel = computed(() => (
  activeSourceType.value === 'knowledge-point' ? '已选知识点' : '已选题库/科目'
))

const currentSources = computed(() => (
  activeSourceType.value === 'knowledge-point' ? knowledgePoints.value : questionFolders.value
))

const selectedSource = computed(() => (
  currentSources.value.find((item) => String(item.id) === String(selectedSourceId.value))
))

const selectedSourceMeta = computed(() => {
  if (!selectedSource.value) {
    return ''
  }
  if (activeSourceType.value === 'question-folder') {
    return `${selectedSource.value.category || '默认分类'} · 递归包含子级题目`
  }
  return selectedSource.value.question_count ? `关联 ${selectedSource.value.question_count} 道题目` : ''
})

function normalizeQuestionCount(value) {
  return Number(value || 0)
}

function flattenFolderTree(folders, depth = 0) {
  let flattened = []

  for (const folder of folders || []) {
    const questionCount = normalizeQuestionCount(folder.question_count ?? folder.questionCount)
    flattened.push({
      id: folder.id,
      name: folder.name,
      display_name: depth > 0 ? `${'-- '.repeat(depth)}${folder.name}` : folder.name,
      category: folder.category || '默认分类',
      question_count: questionCount,
      description: '',
    })

    if (Array.isArray(folder.children) && folder.children.length > 0) {
      flattened = flattened.concat(flattenFolderTree(folder.children, depth + 1))
    }
  }

  return flattened
}

async function loadPracticeSources() {
  loading.value = true
  try {
    const [knowledgePointResponse, folderResponse] = await Promise.all([
      getKnowledgePointsApiV1KnowledgePointsGet({ size: -1 }),
      getQuestionFoldersApiV1QuestionsFoldersGet(),
    ])

    knowledgePoints.value = (knowledgePointResponse?.items || []).filter(
      (item) => normalizeQuestionCount(item.question_count) > 0,
    )

    questionFolders.value = flattenFolderTree(folderResponse || []).filter(
      (item) => normalizeQuestionCount(item.question_count) > 0,
    )
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载练习来源失败')
  } finally {
    loading.value = false
  }
}

function selectSourceType(type) {
  if (activeSourceType.value === type) {
    return
  }
  activeSourceType.value = type
  selectedSourceId.value = ''
}

function startPractice() {
  if (!selectedSource.value) {
    message.warning(`请先选择${currentSelectorLabel.value}`)
    return
  }

  router.push({
    path: '/practice/do',
    query: {
      sourceType: activeSourceType.value,
      sourceId: String(selectedSource.value.id),
      sourceName: selectedSource.value.name,
    },
  })
}

onMounted(() => {
  void loadPracticeSources()
})
</script>

<style scoped>
.practice-page {
  padding: 24px;
  max-width: 640px;
  margin: 0 auto;
  position: relative;
}

.page-header {
  text-align: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--v2-text-primary, #1E293B);
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--v2-text-secondary, #64748B);
  margin: 0;
}

.mode-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.mode-tab {
  height: 44px;
  border: 1px solid #D7E1F0;
  border-radius: 12px;
  background: #fff;
  color: #475569;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-tab.active {
  border-color: #2563EB;
  background: linear-gradient(135deg, #EFF6FF, #DBEAFE);
  color: #1D4ED8;
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.12);
}

.filter-section {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  min-width: 72px;
}

.filter-select {
  flex: 1;
  height: 44px;
  padding: 0 12px;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  font-size: 14px;
  color: #334155;
  background: #fff;
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.filter-hint {
  margin: 12px 0 0;
  font-size: 13px;
  color: #64748B;
}

.question-preview {
  background: linear-gradient(135deg, #2563EB, #1D4ED8);
  border-radius: 16px;
  padding: 20px;
  color: #fff;
  margin-bottom: 24px;
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.22);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.preview-title {
  font-size: 12px;
  opacity: 0.82;
}

.preview-count {
  font-size: 12px;
  background: rgba(255,255,255,0.18);
  padding: 2px 8px;
  border-radius: 999px;
}

.preview-name {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 6px;
}

.preview-meta {
  font-size: 13px;
  opacity: 0.88;
  margin-bottom: 4px;
}

.preview-desc {
  font-size: 13px;
  opacity: 0.8;
}

.empty-tip {
  padding: 18px;
  margin: 0 0 20px;
  text-align: center;
  color: #64748B;
  background: #F8FAFC;
  border: 1px dashed #CBD5E1;
  border-radius: 12px;
}

.action-area {
  text-align: center;
}

.btn-start {
  width: 100%;
  height: 48px;
  background: #2563EB;
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-start:hover:not(:disabled) {
  background: #1D4ED8;
  transform: translateY(-1px);
}

.btn-start:disabled {
  background: #CBD5E1;
  cursor: not-allowed;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.82);
  border-radius: 16px;
}
</style>
