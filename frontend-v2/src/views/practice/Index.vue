<template>
  <div class="practice-page">
    <div class="page-header">
      <h1 class="page-title">刷题练习</h1>
      <p class="page-subtitle">选择知识点开始练习</p>
    </div>

    <div class="filter-section">
      <div class="filter-item">
        <label class="filter-label">知识点</label>
        <select v-model="selectedKpId" class="filter-select">
          <option value="">全部知识点</option>
          <option v-for="kp in knowledgePoints" :key="kp.id" :value="kp.id">
            {{ kp.name }} ({{ kp.question_count || 0 }}题)
          </option>
        </select>
      </div>
    </div>

    <div class="question-preview" v-if="selectedKpId">
      <div class="preview-header">
        <span class="preview-title">已选知识点</span>
        <span class="preview-count">{{ selectedKp?.question_count || 0 }} 题</span>
      </div>
      <div class="preview-name">{{ selectedKp?.name }}</div>
      <div class="preview-desc" v-if="selectedKp?.description">{{ selectedKp.description }}</div>
    </div>

    <div class="action-area">
      <button
        class="btn-start"
        :disabled="!selectedKpId"
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { getKnowledgePointsApiV1KnowledgePointsGet } from '@/api/generated/knowledge-point-management/knowledge-point-management'

const router = useRouter()
const loading = ref(false)
const knowledgePoints = ref([])
const selectedKpId = ref('')

const selectedKp = computed(() => {
  return knowledgePoints.value.find(kp => kp.id === Number(selectedKpId.value))
})

async function loadKnowledgePoints() {
  loading.value = true
  try {
    const res = await getKnowledgePointsApiV1KnowledgePointsGet({ size: -1 })
    knowledgePoints.value = res.data?.items || []
  } catch (e) {
    message.error('加载知识点失败')
  } finally {
    loading.value = false
  }
}

function startPractice() {
  if (!selectedKpId.value) {
    message.warning('请先选择知识点')
    return
  }
  router.push({
    path: '/practice/do',
    query: { kpId: selectedKpId.value }
  })
}

onMounted(() => {
  loadKnowledgePoints()
})
</script>

<style scoped>
.practice-page {
  padding: 24px;
  max-width: 600px;
  margin: 0 auto;
  position: relative;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
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

.filter-section {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
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
  min-width: 60px;
}

.filter-select {
  flex: 1;
  height: 40px;
  padding: 0 12px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
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

.question-preview {
  background: linear-gradient(135deg, #2563EB, #1D4ED8);
  border-radius: 12px;
  padding: 20px;
  color: #fff;
  margin-bottom: 24px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.preview-title {
  font-size: 12px;
  opacity: 0.8;
}

.preview-count {
  font-size: 12px;
  background: rgba(255,255,255,0.2);
  padding: 2px 8px;
  border-radius: 999px;
}

.preview-name {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 4px;
}

.preview-desc {
  font-size: 13px;
  opacity: 0.8;
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
  transform: scale(0.98);
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
  background: rgba(255,255,255,0.8);
  border-radius: 12px;
}
</style>
