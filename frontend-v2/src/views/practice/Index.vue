<template>
  <div class="practice-page">
    <div class="practice-container">
      <!-- 页面标题区 -->
      <header class="page-header">
        <div class="header-content">
          <h1 class="page-title">刷题练习</h1>
          <p class="page-subtitle">选择知识点或题库开始练习</p>
        </div>
      </header>

      <!-- 模式切换 -->
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

      <!-- 筛选区域 -->
      <div class="filter-card">
        <!-- 知识点/题库选择 -->
        <div class="filter-block filter-block-main">
          <label class="filter-label">{{ currentSelectorLabel }}</label>
          <div class="select-wrapper">
            <select v-model="selectedSourceId" class="field-control">
              <option value="">{{ currentPlaceholder }}</option>
              <option
                v-for="item in currentSources"
                :key="item.id"
                :value="String(item.id)"
              >
                {{ item.display_name || item.name }} ({{ item.question_count || 0 }}题)
              </option>
            </select>
            <svg class="select-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </div>
          <p class="filter-hint">{{ currentHint }}</p>
        </div>

        <!-- 高级筛选 -->
        <div class="advanced-section">
          <div class="advanced-grid">
            <div class="filter-block">
              <label class="filter-label">题量</label>
              <div class="select-wrapper">
                <select v-model="questionLimitMode" class="field-control">
                  <option v-for="option in questionLimitOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <svg class="select-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            <div v-if="questionLimitMode === 'custom'" class="filter-block">
              <label class="filter-label">自定义题量</label>
              <input
                v-model="customQuestionLimit"
                class="field-control"
                type="number"
                min="1"
                step="1"
                placeholder="请输入题量"
              >
            </div>

            <div class="filter-block">
              <label class="filter-label">题型</label>
              <div class="select-wrapper">
                <select v-model="selectedQuestionType" class="field-control">
                  <option v-for="option in questionTypeOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <svg class="select-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            <div class="filter-block">
              <label class="filter-label">难度</label>
              <div class="select-wrapper">
                <select v-model="selectedDifficulty" class="field-control">
                  <option v-for="option in difficultyOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
                <svg class="select-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            <div class="filter-block">
              <label class="filter-label">警种</label>
              <div class="select-wrapper">
                <select v-model="selectedPoliceTypeId" class="field-control">
                  <option value="">全部警种</option>
                  <option v-for="item in policeTypes" :key="item.id" :value="String(item.id)">
                    {{ item.name }}
                  </option>
                </select>
                <svg class="select-arrow" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          <div class="filter-block filter-block-wide">
            <label class="filter-label">关键词</label>
            <input
              v-model="keyword"
              class="field-control"
              type="text"
              placeholder="可按题干或知识点关键词筛选"
            >
          </div>
        </div>
      </div>

      <!-- 预览区域 -->
      <div v-if="selectedSource" class="preview-card">
        <div class="preview-header">
          <span class="preview-tag">{{ selectedSourceTypeLabel }}</span>
          <span class="preview-count">{{ selectedSource.question_count || 0 }} 题</span>
        </div>
        <div class="preview-name">{{ selectedSource.name }}</div>
        <div v-if="selectedSourceMeta" class="preview-meta">{{ selectedSourceMeta }}</div>
        <div v-if="activeFilterTags.length" class="preview-tags">
          <span v-for="tag in activeFilterTags" :key="tag" class="preview-chip">{{ tag }}</span>
        </div>
        <div v-if="selectedSource.description" class="preview-desc">{{ selectedSource.description }}</div>
      </div>

      <p v-else-if="!loading && !currentSources.length" class="empty-tip">
        当前暂无可练习的{{ currentSelectorLabel }}
      </p>

      <!-- 底部操作区 -->
      <footer class="action-footer">
        <button
          class="btn-start"
          :disabled="!selectedSourceId"
          @click="startPractice"
        >
          开始练习
        </button>
      </footer>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-overlay">
        <a-spin size="large" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { getKnowledgePointsApiV1KnowledgePointsGet } from '@/api/generated/knowledge-point-management/knowledge-point-management'
import { getPoliceTypesApiV1PoliceTypesGet } from '@/api/generated/police-type-management/police-type-management'
import { getQuestionFoldersApiV1QuestionsFoldersGet } from '@/api/generated/question-management/question-management'

const router = useRouter()

const loading = ref(false)
const activeSourceType = ref('knowledge-point')
const selectedSourceId = ref('')
const questionLimitMode = ref('20')
const customQuestionLimit = ref('')
const selectedQuestionType = ref('')
const selectedDifficulty = ref('')
const selectedPoliceTypeId = ref('')
const keyword = ref('')

const knowledgePoints = ref([])
const questionFolders = ref([])
const policeTypes = ref([])

const questionLimitOptions = [
  { value: '10', label: '最多 10 题' },
  { value: '20', label: '最多 20 题' },
  { value: '50', label: '最多 50 题' },
  { value: 'all', label: '任意数量' },
  { value: 'custom', label: '自定义题量' },
]

const questionTypeOptions = [
  { value: '', label: '全部题型' },
  { value: 'single', label: '单选题' },
  { value: 'multi', label: '多选题' },
  { value: 'judge', label: '判断题' },
]

const difficultyOptions = [
  { value: '', label: '全部难度' },
  { value: '1', label: '难度 1' },
  { value: '2', label: '难度 2' },
  { value: '3', label: '难度 3' },
  { value: '4', label: '难度 4' },
  { value: '5', label: '难度 5' },
]

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

const selectedPoliceTypeName = computed(() => (
  policeTypes.value.find((item) => String(item.id) === String(selectedPoliceTypeId.value)))?.name || ''
))

const resolvedQuestionLimit = computed(() => {
  if (questionLimitMode.value === 'all') {
    return null
  }
  if (questionLimitMode.value === 'custom') {
    const parsed = Number(customQuestionLimit.value)
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null
  }
  const parsed = Number(questionLimitMode.value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 20
})

const questionLimitLabel = computed(() => {
  if (questionLimitMode.value === 'all') {
    return '题量不限'
  }
  if (questionLimitMode.value === 'custom') {
    return resolvedQuestionLimit.value ? `最多 ${resolvedQuestionLimit.value} 题` : '自定义题量'
  }
  return `最多 ${resolvedQuestionLimit.value} 题`
})

const selectedSourceMeta = computed(() => {
  if (!selectedSource.value) {
    return ''
  }
  if (activeSourceType.value === 'question-folder') {
    return `${selectedSource.value.category || '默认分类'} · 递归包含子级题目`
  }
  return selectedSource.value.question_count ? `关联 ${selectedSource.value.question_count} 道题目` : ''
})

const activeFilterTags = computed(() => {
  const tags = [questionLimitLabel.value]

  if (selectedQuestionType.value) {
    tags.push(questionTypeOptions.find((item) => item.value === selectedQuestionType.value)?.label || '')
  }
  if (selectedDifficulty.value) {
    tags.push(`难度 ${selectedDifficulty.value}`)
  }
  if (selectedPoliceTypeName.value) {
    tags.push(`警种：${selectedPoliceTypeName.value}`)
  }
  if (keyword.value.trim()) {
    tags.push(`关键词：${keyword.value.trim()}`)
  }

  return tags.filter(Boolean)
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
    const [knowledgePointResponse, folderResponse, policeTypeResponse] = await Promise.all([
      getKnowledgePointsApiV1KnowledgePointsGet({ size: -1 }),
      getQuestionFoldersApiV1QuestionsFoldersGet(),
      getPoliceTypesApiV1PoliceTypesGet({ size: -1 }),
    ])

    knowledgePoints.value = (knowledgePointResponse?.items || []).filter(
      (item) => normalizeQuestionCount(item.question_count) > 0,
    )

    questionFolders.value = flattenFolderTree(folderResponse || []).filter(
      (item) => normalizeQuestionCount(item.question_count) > 0,
    )

    policeTypes.value = (policeTypeResponse?.items || []).filter((item) => item.is_active !== false)
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

  if (questionLimitMode.value === 'custom' && !resolvedQuestionLimit.value) {
    message.warning('请输入有效的自定义题量')
    return
  }

  router.push({
    path: '/practice/do',
    query: {
      sourceType: activeSourceType.value,
      sourceId: String(selectedSource.value.id),
      sourceName: selectedSource.value.name,
      questionLimit: resolvedQuestionLimit.value ? String(resolvedQuestionLimit.value) : 'all',
      questionType: selectedQuestionType.value || undefined,
      difficulty: selectedDifficulty.value || undefined,
      policeTypeId: selectedPoliceTypeId.value || undefined,
      policeTypeName: selectedPoliceTypeName.value || undefined,
      keyword: keyword.value.trim() || undefined,
    },
  })
}

onMounted(() => {
  void loadPracticeSources()
})
</script>

<style scoped>
.practice-page {
  min-height: 100vh;
  background: var(--v2-bg, #F5F6FA);
  display: flex;
  align-items: stretch;
  justify-content: center;
}

.practice-container {
  width: 100%;
  max-width: 900px;
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 页面标题 */
.page-header {
  text-align: center;
  padding: 16px 0 8px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--v2-text-primary, #1D1D1F);
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--v2-text-secondary, #86868B);
  margin: 0;
}

/* 模式切换 */
.mode-tabs {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.mode-tab {
  height: 48px;
  border: 2px solid var(--v2-border, #E5E5EA);
  border-radius: var(--v2-radius, 12px);
  background: var(--v2-bg-card, #FFFFFF);
  color: var(--v2-text-secondary, #86868B);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-tab:hover {
  border-color: var(--v2-primary, #4B6EF5);
  color: var(--v2-primary, #4B6EF5);
}

.mode-tab.active {
  border-color: var(--v2-primary, #4B6EF5);
  background: var(--v2-primary-light, #EEF2FF);
  color: var(--v2-primary, #4B6EF5);
  box-shadow: 0 4px 16px rgba(75, 110, 245, 0.15);
}

/* 筛选卡片 */
.filter-card {
  background: var(--v2-bg-card, #FFFFFF);
  border-radius: var(--v2-radius-lg, 16px);
  padding: 24px;
  box-shadow: var(--v2-shadow, 0 2px 8px rgba(0, 0, 0, 0.06));
}

.filter-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-block-main {
  margin-bottom: 20px;
}

.filter-block-wide {
  grid-column: 1 / -1;
}

.filter-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--v2-text-primary, #1D1D1F);
}

.select-wrapper {
  position: relative;
}

.field-control {
  width: 100%;
  height: 48px;
  padding: 0 40px 0 14px;
  border: 1.5px solid var(--v2-border, #E5E5EA);
  border-radius: var(--v2-radius, 12px);
  font-size: 14px;
  color: var(--v2-text-primary, #1D1D1F);
  background: var(--v2-bg-card, #FFFFFF);
  transition: all 0.2s;
  appearance: none;
  cursor: pointer;
}

.field-control:focus {
  outline: none;
  border-color: var(--v2-primary, #4B6EF5);
  box-shadow: 0 0 0 3px var(--v2-primary-light, rgba(75, 110, 245, 0.1));
}

.select-arrow {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 16px;
  height: 16px;
  color: var(--v2-text-muted, #AEAEB2);
  pointer-events: none;
}

.filter-hint {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--v2-text-muted, #AEAEB2);
}

/* 高级筛选 */
.advanced-section {
  border-top: 1px solid var(--v2-border-light, #F2F2F7);
  padding-top: 20px;
}

.advanced-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

/* 预览卡片 */
.preview-card {
  background: linear-gradient(135deg, var(--v2-primary, #4B6EF5), #3B5DE0);
  border-radius: var(--v2-radius-lg, 16px);
  padding: 24px;
  color: #fff;
  box-shadow: 0 8px 24px rgba(75, 110, 245, 0.25);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.preview-tag {
  font-size: 12px;
  opacity: 0.85;
  font-weight: 500;
}

.preview-count {
  font-size: 12px;
  background: rgba(255, 255, 255, 0.2);
  padding: 3px 10px;
  border-radius: var(--v2-radius-full, 9999px);
}

.preview-name {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 6px;
}

.preview-meta {
  font-size: 13px;
  opacity: 0.85;
  margin-bottom: 12px;
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.preview-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: var(--v2-radius-full, 9999px);
  background: rgba(255, 255, 255, 0.18);
  font-size: 12px;
}

.preview-desc {
  font-size: 13px;
  opacity: 0.8;
  line-height: 1.5;
}

.empty-tip {
  padding: 20px;
  margin: 0;
  text-align: center;
  color: var(--v2-text-secondary, #86868B);
  background: var(--v2-bg, #F5F6FA);
  border: 1px dashed var(--v2-border, #E5E5EA);
  border-radius: var(--v2-radius, 12px);
}

/* 底部操作 */
.action-footer {
  padding: 8px 0;
}

.btn-start {
  width: 100%;
  height: 52px;
  background: var(--v2-primary, #4B6EF5);
  color: #fff;
  border: none;
  border-radius: var(--v2-radius, 12px);
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 16px rgba(75, 110, 245, 0.25);
}

.btn-start:hover:not(:disabled) {
  background: var(--v2-primary-hover, #3B5DE0);
  transform: translateY(-1px);
}

.btn-start:disabled {
  background: var(--v2-border, #E5E5EA);
  color: var(--v2-text-muted, #AEAEB2);
  cursor: not-allowed;
  box-shadow: none;
}

/* 加载状态 */
.loading-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
  z-index: 100;
}

/* =====================
   响应式设计
   ===================== */

/* 平板 */
@media (max-width: 768px) {
  .practice-container {
    padding: 20px 16px;
    gap: 16px;
  }

  .page-title {
    font-size: 24px;
  }

  .filter-card {
    padding: 20px;
  }

  .advanced-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .preview-card {
    padding: 20px;
  }

  .preview-name {
    font-size: 18px;
  }
}

/* 手机 */
@media (max-width: 480px) {
  .practice-container {
    padding: 16px 12px;
    gap: 14px;
  }

  .page-header {
    padding: 12px 0 4px;
  }

  .page-title {
    font-size: 22px;
  }

  .mode-tab {
    height: 44px;
    font-size: 14px;
  }

  .advanced-grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  .filter-card {
    padding: 16px;
  }

  .preview-card {
    padding: 16px;
  }

  .preview-name {
    font-size: 16px;
  }

  .preview-tags {
    gap: 6px;
  }

  .btn-start {
    height: 48px;
    font-size: 15px;
  }
}
</style>
