<template>
  <div class="page-content practice-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">刷题练习</h1>
        <p class="page-subtitle">选择知识点或题库，开启专项练习。</p>
      </div>
    </div>

    <!-- 筛选卡片 -->
    <a-card :bordered="false" class="filter-card">
      <div class="filter-shell">
        <div class="filter-top">
          <div class="filter-search">
            <a-input-search
              v-model:value="searchKeyword"
              placeholder="搜索知识点名称..."
              @search="handleSearch"
            />
          </div>
          <div class="filter-top-actions">
            <a-select v-model:value="questionLimitMode" class="sort-select">
              <a-select-option value="10">最多 10 题</a-select-option>
              <a-select-option value="20">最多 20 题</a-select-option>
              <a-select-option value="50">最多 50 题</a-select-option>
              <a-select-option value="all">题量不限</a-select-option>
            </a-select>
          </div>
        </div>

        <div class="filter-row">
          <a-select v-model:value="selectedQuestionType" placeholder="全部题型" allow-clear class="filter-select">
            <a-select-option value="single">单选题</a-select-option>
            <a-select-option value="multi">多选题</a-select-option>
            <a-select-option value="judge">判断题</a-select-option>
          </a-select>
          <a-select v-model:value="selectedDifficulty" placeholder="全部难度" allow-clear class="filter-select">
            <a-select-option value="1">难度 1</a-select-option>
            <a-select-option value="2">难度 2</a-select-option>
            <a-select-option value="3">难度 3</a-select-option>
            <a-select-option value="4">难度 4</a-select-option>
            <a-select-option value="5">难度 5</a-select-option>
          </a-select>
          <a-select v-model:value="selectedPoliceTypeId" placeholder="全部警种" allow-clear class="filter-select">
            <a-select-option v-for="item in policeTypes" :key="item.id" :value="String(item.id)">
              {{ item.name }}
            </a-select-option>
          </a-select>
        </div>
      </div>
    </a-card>

    <!-- 模式切换 -->
    <div class="category-tabs">
      <a-tag
        class="cat-tag"
        :class="{ active: activeSourceType === 'knowledge-point' }"
        @click="selectSourceType('knowledge-point')"
      >
        按知识点
      </a-tag>
      <a-tag
        class="cat-tag"
        :class="{ active: activeSourceType === 'question-folder' }"
        @click="selectSourceType('question-folder')"
      >
        按题库/科目
      </a-tag>
    </div>

    <!-- 统计 -->
    <div class="practice-stats">
      <span>共 <strong>{{ filteredSources.length }}</strong> 个{{ activeSourceType === 'knowledge-point' ? '知识点' : '题库' }}</span>
    </div>

    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" />
    </div>

    <a-empty v-else-if="!filteredSources.length" description="暂无符合条件的练习来源" class="empty-block" />

    <div v-else class="practice-grid">
      <div
        v-for="(item, index) in filteredSources"
        :key="item.id"
        class="practice-card"
        :style="{ '--card-accent': getCardAccent(index) }"
        @click="handleCardClick(item)"
      >
        <div class="card-cover" :style="{ background: getCardCoverBackground(index) }">
          <div class="cover-labels">
            <span class="cover-tag-label">{{ activeSourceType === 'knowledge-point' ? '知识点' : '题库' }}</span>
            <span class="cover-count-tag">{{ item.question_count || 0 }} 题</span>
          </div>

          <div class="cover-visual">
            <span class="cover-visual-ring">
              <NodeIndexOutlined v-if="activeSourceType === 'knowledge-point'" class="cover-visual-icon" />
              <FolderOutlined v-else class="cover-visual-icon" />
            </span>
          </div>

          <div class="cover-footer">
            <span v-if="activeSourceType === 'question-folder'" class="cover-footer-item">
              {{ item.category || '默认分类' }}
            </span>
            <span v-if="activeSourceType === 'knowledge-point' && item.police_type_name" class="cover-footer-item">
              {{ item.police_type_name }}
            </span>
          </div>
        </div>

        <div class="card-body">
          <div class="card-head">
            <h3>{{ item.name }}</h3>
            <p v-if="item.description">{{ item.description }}</p>
            <p v-else style="color: var(--v2-text-muted)">暂无描述</p>
          </div>

          <div class="meta-grid">
            <span v-if="item.question_count">
              <QuestionCircleOutlined />
              {{ item.question_count }} 题
            </span>
            <span v-if="item.difficulty_avg">
              <StarOutlined />
              平均难度 {{ item.difficulty_avg.toFixed(1) }}
            </span>
          </div>

          <div class="action-row">
            <a-button type="primary" block @click.stop="startPractice(item)">
              开始练习
            </a-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 练习设置弹窗 -->
    <a-modal
      v-model:open="settingsVisible"
      :title="null"
      :footer="null"
      :width="420"
      centered
      class="settings-modal"
    >
      <div class="settings-panel">
        <div class="settings-header">
          <div class="settings-icon">
            <EditOutlined />
          </div>
          <div class="settings-title-area">
            <h3 class="settings-title">设置练习参数</h3>
            <p class="settings-subtitle">{{ selectedPracticeItem?.name }}</p>
          </div>
        </div>

        <div class="settings-form">
          <div class="settings-field">
            <label class="settings-label">题目数量</label>
            <a-select v-model:value="settingsForm.questionLimit" class="settings-select">
              <a-select-option value="10">最多 10 题</a-select-option>
              <a-select-option value="20">最多 20 题</a-select-option>
              <a-select-option value="50">最多 50 题</a-select-option>
              <a-select-option value="all">题量不限</a-select-option>
            </a-select>
          </div>

          <div class="settings-field">
            <label class="settings-label">题目类型</label>
            <a-select v-model:value="settingsForm.questionType" placeholder="全部题型" allow-clear class="settings-select">
              <a-select-option value="single">单选题</a-select-option>
              <a-select-option value="multi">多选题</a-select-option>
              <a-select-option value="judge">判断题</a-select-option>
            </a-select>
          </div>

          <div class="settings-field">
            <label class="settings-label">题目难度</label>
            <a-select v-model:value="settingsForm.difficulty" placeholder="全部难度" allow-clear class="settings-select">
              <a-select-option value="1">难度 1</a-select-option>
              <a-select-option value="2">难度 2</a-select-option>
              <a-select-option value="3">难度 3</a-select-option>
              <a-select-option value="4">难度 4</a-select-option>
              <a-select-option value="5">难度 5</a-select-option>
            </a-select>
          </div>
        </div>

        <div class="settings-actions">
          <button class="btn-cancel" @click="settingsVisible = false">返回</button>
          <button class="btn-confirm" @click="confirmStartPractice">开始练习</button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import {
  EditOutlined,
  FolderOutlined,
  NodeIndexOutlined,
  QuestionCircleOutlined,
  StarOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getPracticeSources } from '@/api/practice'
import type { PoliceTypeSimpleResponse } from '@/api/generated/model'

const router = useRouter()

const loading = ref(false)
const activeSourceType = ref('knowledge-point')
const searchKeyword = ref('')
const questionLimitMode = ref('20')
const selectedQuestionType = ref(undefined)
const selectedDifficulty = ref(undefined)
const selectedPoliceTypeId = ref(undefined)

const knowledgePoints = ref<any[]>([])
const questionFolders = ref<any[]>([])
const policeTypes = ref<PoliceTypeSimpleResponse[]>([])

const settingsVisible = ref(false)
const selectedPracticeItem = ref<any>(null)

const settingsForm = reactive({
  questionLimit: '20',
  questionType: undefined as string | undefined,
  difficulty: undefined as string | undefined,
})

const coverGradients = [
  'linear-gradient(135deg, #edf1fb 0%, #e4eaf5 100%)',
  'linear-gradient(135deg, #edf3ee 0%, #e1eae3 100%)',
  'linear-gradient(135deg, #f6eee7 0%, #eee2d7 100%)',
  'linear-gradient(135deg, #edf4f3 0%, #e2ece9 100%)',
  'linear-gradient(135deg, #f3ede7 0%, #e8dfd6 100%)',
]

const cardAccents = [
  '#4B6EF5',
  '#34C759',
  '#FF9500',
  '#5856D6',
  '#FF2D55',
]

function getCardAccent(index: number) {
  return cardAccents[index % cardAccents.length]
}

function getCardCoverBackground(index: number) {
  return coverGradients[index % coverGradients.length]
}

const currentSources = computed(() => (
  activeSourceType.value === 'knowledge-point' ? knowledgePoints.value : questionFolders.value
))

const filteredSources = computed(() => {
  let items = currentSources.value

  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.trim().toLowerCase()
    items = items.filter((item) =>
      (item.name || '').toLowerCase().includes(keyword),
    )
  }

  return items
})

const selectedPoliceTypeName = computed(() =>
  policeTypes.value.find((item) => String(item.id) === String(selectedPoliceTypeId.value))?.name || ''
)

function normalizeQuestionCount(value: unknown) {
  return Number(value || 0)
}

function flattenFolderTree(folders: any[], depth = 0) {
  let flattened: any[] = []

  for (const folder of folders || []) {
    const questionCount = normalizeQuestionCount(folder.question_count ?? folder.questionCount)
    flattened.push({
      id: folder.id,
      name: folder.name,
      category: folder.category || '默认分类',
      question_count: questionCount,
      description: folder.description || '',
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
    const sourceResponse = await getPracticeSources()

    const rawKps = sourceResponse?.knowledge_points || []
    knowledgePoints.value = rawKps
      .filter((item: any) => normalizeQuestionCount(item.question_count) > 0)
      .map((item: any) => ({
        ...item,
        police_type_name: item.police_type?.name || '',
        difficulty_avg: item.difficulty_avg || null,
      }))

    questionFolders.value = flattenFolderTree(sourceResponse?.question_folders || []).filter(
      (item: any) => normalizeQuestionCount(item.question_count) > 0,
    )

    policeTypes.value = (sourceResponse?.police_types || []).filter((item: any) => item.is_active !== false)
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载练习来源失败')
  } finally {
    loading.value = false
  }
}

function selectSourceType(type: string) {
  if (activeSourceType.value === type) {
    return
  }
  activeSourceType.value = type
  searchKeyword.value = ''
}

function handleSearch() {
  // 搜索由 computed 属性自动处理
}

function handleCardClick(item: any) {
  startPractice(item)
}

function getResolvedQuestionLimit() {
  if (questionLimitMode.value === 'all') {
    return null
  }
  const parsed = Number(questionLimitMode.value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 20
}

function getSelectedPoliceTypeName() {
  return policeTypes.value.find((item) => String(item.id) === String(selectedPoliceTypeId.value))?.name || ''
}

function getPracticeSettingsText() {
  const parts: string[] = []

  const limit = getResolvedQuestionLimit()
  if (limit) {
    parts.push(`题量：${limit} 题`)
  } else {
    parts.push('题量：不限')
  }

  const typeMap: Record<string, string> = { single: '单选题', multi: '多选题', judge: '判断题' }
  if (selectedQuestionType.value && typeMap[selectedQuestionType.value]) {
    parts.push(`题型：${typeMap[selectedQuestionType.value]}`)
  } else {
    parts.push('题型：全部')
  }

  if (selectedDifficulty.value) {
    parts.push(`难度：${selectedDifficulty.value}`)
  } else {
    parts.push('难度：全部')
  }

  if (selectedPoliceTypeId.value) {
    const policeName = getSelectedPoliceTypeName()
    if (policeName) parts.push(`警种：${policeName}`)
  }

  return parts.join(' · ')
}

function startPractice(item: any) {
  selectedPracticeItem.value = item
  settingsForm.questionLimit = questionLimitMode.value
  settingsForm.questionType = selectedQuestionType.value
  settingsForm.difficulty = selectedDifficulty.value
  settingsVisible.value = true
}

function getSettingsResolvedLimit() {
  if (settingsForm.questionLimit === 'all') return null
  const parsed = Number(settingsForm.questionLimit)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 20
}

function confirmStartPractice() {
  if (!selectedPracticeItem.value) return
  settingsVisible.value = false
  router.push({
    path: '/practice/do',
    query: {
      sourceType: activeSourceType.value,
      sourceId: String(selectedPracticeItem.value.id),
      sourceName: selectedPracticeItem.value.name,
      questionLimit: getSettingsResolvedLimit() ? String(getSettingsResolvedLimit()) : 'all',
      questionType: settingsForm.questionType || undefined,
      difficulty: settingsForm.difficulty || undefined,
      policeTypeId: selectedPoliceTypeId.value || undefined,
      policeTypeName: getSelectedPoliceTypeName() || undefined,
      keyword: searchKeyword.value.trim() || undefined,
    },
  })
}

onMounted(() => {
  void loadPracticeSources()
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.page-title {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: 700;
  color: var(--v2-text-primary);
}

.page-subtitle {
  margin: 0;
  color: var(--v2-text-secondary);
}

.filter-card {
  margin-bottom: 20px;
  border-radius: 24px;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.06);
}

.filter-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.filter-top {
  display: flex;
  align-items: center;
  gap: 16px;
}

.filter-search {
  flex: 1;
}

.filter-top-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sort-select {
  width: 150px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.filter-select {
  min-width: 140px;
}

.category-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

:deep(.cat-tag.ant-tag) {
  cursor: pointer;
  margin: 0;
  padding: 7px 14px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  color: var(--v2-text-secondary);
  border: 1px solid rgba(75, 110, 245, 0.12);
  background: rgba(255, 255, 255, 0.92);
  transition:
    color 0.2s ease,
    border-color 0.2s ease,
    background 0.2s ease,
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

:deep(.cat-tag.ant-tag:hover),
:deep(.cat-tag.active.ant-tag) {
  color: var(--v2-primary);
  border-color: rgba(75, 110, 245, 0.28);
  background: var(--v2-primary-light);
  box-shadow: 0 10px 24px rgba(75, 110, 245, 0.12);
  transform: translateY(-1px);
}

.practice-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
  color: var(--v2-text-secondary);
}

.loading-wrapper,
.empty-block {
  padding: 80px 0;
}

.practice-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.practice-card {
  overflow: hidden;
  background: var(--v2-bg-card);
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(24, 39, 75, 0.08);
  cursor: pointer;
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease;
}

.practice-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 24px 48px rgba(75, 110, 245, 0.12);
}

.card-cover {
  position: relative;
  height: 180px;
  padding: 18px;
  overflow: hidden;
}

.card-cover::before {
  content: '';
  position: absolute;
  right: -34px;
  bottom: -70px;
  width: 210px;
  height: 210px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  filter: blur(8px);
}

.cover-labels {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.cover-tag-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--v2-text-secondary);
}

.cover-count-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  color: var(--v2-primary);
  background: rgba(75, 110, 245, 0.1);
  border: 1px solid rgba(75, 110, 245, 0.2);
}

.cover-visual {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-visual-ring {
  position: relative;
  width: 82px;
  height: 82px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.78);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.7));
  box-shadow:
    0 16px 28px var(--card-accent, rgba(75, 110, 245, 0.14)),
    inset 0 1px 0 rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
}

.cover-visual-icon {
  position: relative;
  z-index: 1;
  font-size: 34px;
  color: var(--card-accent, #4B6EF5);
}

.cover-footer {
  position: absolute;
  left: 12px;
  right: 22px;
  bottom: 10px;
  z-index: 2;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.cover-footer-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  padding: 0 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(18, 25, 38, 0.78);
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.72);
}

.card-body {
  padding: 22px 22px 24px;
}

.card-head {
  margin-bottom: 16px;
}

.card-head h3 {
  margin: 0 0 10px;
  font-size: 21px;
  line-height: 1.35;
  color: var(--v2-text-primary);
}

.card-head p {
  margin: 0;
  min-height: 44px;
  color: var(--v2-text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
  margin-bottom: 16px;
  color: var(--v2-text-secondary);
  font-size: 14px;
}

.meta-grid span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.action-row {
  padding-top: 4px;
}

@media (max-width: 768px) {
  .filter-top {
    flex-direction: column;
    align-items: flex-start;
  }

  .sort-select,
  .filter-select {
    width: 100%;
  }

  .practice-grid,
  .meta-grid {
    grid-template-columns: 1fr;
  }

  .card-cover {
    height: 164px;
  }
}

@media (max-width: 480px) {
  .practice-page {
    padding-bottom: 80px;
  }

  .practice-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .practice-card {
    border-radius: 16px;
  }

  .card-cover {
    height: 100px;
    padding: 12px;
  }

  .cover-labels {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .cover-tag-label {
    font-size: 10px;
  }

  .cover-count-tag {
    font-size: 10px;
    padding: 2px 8px;
  }

  .cover-visual-ring {
    width: 48px;
    height: 48px;
    border-radius: 14px;
  }

  .cover-visual-icon {
    font-size: 20px;
  }

  .cover-footer {
    display: none;
  }

  .card-body {
    padding: 12px;
  }

  .card-head h3 {
    font-size: 14px;
    margin-bottom: 6px;
  }

  .card-head p {
    font-size: 12px;
    min-height: auto;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .meta-grid {
    display: none;
  }

  .action-row :deep(.ant-btn) {
    font-size: 12px;
    height: 30px;
    padding: 0 10px;
  }

  .filter-row {
    flex-direction: column;
  }

  .filter-select {
    width: 100%;
  }
}

/* 设置弹窗 */
.settings-panel {
  padding: 8px 4px;
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.settings-icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background: linear-gradient(135deg, #4B6EF5, #3B5DE0);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 22px;
  flex-shrink: 0;
  box-shadow: 0 8px 20px rgba(75, 110, 245, 0.3);
}

.settings-title-area {
  flex: 1;
  min-width: 0;
}

.settings-title {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 700;
  color: var(--v2-text-primary);
}

.settings-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--v2-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.settings-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.settings-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--v2-text-secondary);
}

.settings-select {
  width: 100%;
}

.settings-actions {
  display: flex;
  gap: 12px;
}

.btn-cancel {
  flex: 1;
  height: 44px;
  border: 1.5px solid var(--v2-border);
  border-radius: 12px;
  background: transparent;
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: var(--v2-bg);
  border-color: var(--v2-primary);
  color: var(--v2-primary);
}

.btn-confirm {
  flex: 1;
  height: 44px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #4B6EF5, #3B5DE0);
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 16px rgba(75, 110, 245, 0.25);
}

.btn-confirm:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(75, 110, 245, 0.35);
}
</style>
