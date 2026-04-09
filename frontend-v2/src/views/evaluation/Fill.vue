<template>
  <div class="evaluation-fill">
    <div class="fill-header">
      <a-button type="text" @click="router.back()">← 返回</a-button>
      <h2 class="page-title">{{ taskDetail?.title || '问卷填写' }}</h2>
    </div>

    <a-spin :spinning="loading">
      <div v-if="taskDetail && taskDetail.items.length">
        <!-- 进度指示 -->
        <div class="fill-progress">
          <span>{{ currentStep + 1 }} / {{ taskDetail.items.length }}</span>
          <a-progress :percent="Math.round(((currentStep + 1) / taskDetail.items.length) * 100)" size="small" :show-info="false" />
        </div>

        <!-- 已全部完成 -->
        <div v-if="taskDetail.completed" class="fill-completed">
          <CheckCircleOutlined style="font-size: 48px; color: var(--v2-success); margin-bottom: 12px" />
          <p>您已完成本次评价，感谢参与！</p>
        </div>

        <!-- 任务已关闭 -->
        <div v-else-if="taskDetail.status !== 'active'" class="fill-completed">
          <p>该问卷已结束，无法填写</p>
        </div>

        <!-- 分步填写 -->
        <template v-else>
          <div class="fill-card">
            <div class="fill-card-type">
              <a-tag :color="targetTypeColor(currentItem.target_type)">{{ targetTypeLabel(currentItem.target_type) }}</a-tag>
              <span class="fill-card-name">{{ currentItem.target_name }}</span>
            </div>

            <div class="fill-dimensions">
              <div v-for="dim in currentItem.dimensions" :key="dim.id" class="fill-dim-row">
                <div class="fill-dim-name">{{ dim.name }}</div>
                <div v-if="dim.description" class="fill-dim-desc">{{ dim.description }}</div>
                <a-rate v-model:value="currentScores[dim.id]" :count="5" class="eval-rate" />
              </div>
            </div>

            <div class="fill-comment">
              <a-textarea
                v-model:value="currentComment"
                :rows="2"
                :maxlength="500"
                placeholder="评语（选填）"
              />
            </div>
          </div>

          <div class="fill-nav">
            <a-button v-if="currentStep > 0" @click="prevStep">上一项</a-button>
            <span v-else />
            <a-button v-if="currentStep < taskDetail.items.length - 1" type="primary" @click="nextStep">
              下一项
            </a-button>
            <a-button v-else type="primary" :loading="submitting" @click="handleSubmit">
              提交评价
            </a-button>
          </div>
        </template>
      </div>
      <a-empty v-else-if="!loading" description="问卷不存在或已删除" />
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { CheckCircleOutlined } from '@ant-design/icons-vue'
import axiosInstance from '@/api/custom-instance'

const route = useRoute()
const router = useRouter()
const taskId = Number(route.params.taskId)

const loading = ref(false)
const submitting = ref(false)
const taskDetail = ref<any>(null)
const currentStep = ref(0)

// 每个评价项的评分和评语
const allScores = reactive<Record<number, Record<number, number>>>({})  // itemIndex -> { dimId: score }
const allComments = reactive<Record<number, string>>({})  // itemIndex -> comment

const currentItem = computed(() => taskDetail.value?.items?.[currentStep.value])
const currentScores = computed(() => allScores[currentStep.value] || {})
const currentComment = computed({
  get: () => allComments[currentStep.value] || '',
  set: (val: string) => { allComments[currentStep.value] = val },
})

function targetTypeLabel(type: string) {
  const map: Record<string, string> = { course: '课程评价', instructor: '教官评价', training: '培训班评价', training_base: '基地评价' }
  return map[type] || type
}

function targetTypeColor(type: string) {
  const map: Record<string, string> = { course: 'blue', instructor: 'gold', training: 'green', training_base: 'purple' }
  return map[type] || 'default'
}

function validateCurrentStep(): boolean {
  const item = currentItem.value
  if (!item) return false
  const scores = allScores[currentStep.value] || {}
  const unrated = (item.dimensions || []).filter((d: any) => !scores[d.id])
  if (unrated.length) {
    message.warning(`还有 ${unrated.length} 个维度未评分`)
    return false
  }
  return true
}

function nextStep() {
  if (!validateCurrentStep()) return
  currentStep.value++
}

function prevStep() {
  currentStep.value--
}

async function fetchDetail() {
  loading.value = true
  try {
    const { data } = await axiosInstance.get(`/evaluations/tasks/${taskId}/detail`)
    taskDetail.value = data

    // 初始化每个评价项的评分
    for (let i = 0; i < (data?.items || []).length; i++) {
      if (!allScores[i]) allScores[i] = {}
      for (const dim of (data.items[i].dimensions || [])) {
        if (!allScores[i][dim.id]) allScores[i][dim.id] = 0
      }
    }

    // 跳到第一个未完成的项
    const firstIncomplete = (data?.items || []).findIndex((item: any) => !item.completed)
    if (firstIncomplete >= 0) currentStep.value = firstIncomplete
  } catch {
    taskDetail.value = null
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!validateCurrentStep()) return

  // 构建所有项的评分数据
  const items = (taskDetail.value?.items || []).map((item: any, idx: number) => ({
    target_type: item.target_type,
    target_id: item.target_id,
    scores: (item.dimensions || []).map((dim: any) => ({
      dimension_id: dim.id,
      score: Math.round(allScores[idx]?.[dim.id] || 0),
    })),
    comment: allComments[idx] || undefined,
  })).filter((item: any) => item.scores.some((s: any) => s.score > 0))

  if (!items.length) {
    message.warning('请至少完成一项评价')
    return
  }

  submitting.value = true
  try {
    await axiosInstance.post('/evaluations/submit', {
      task_id: taskId,
      items,
    })
    message.success('评价提交成功')
    taskDetail.value.completed = true
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(fetchDetail)
</script>

<style scoped>
.evaluation-fill {
  max-width: 640px;
  margin: 0 auto;
  padding: 24px 16px;
}

.fill-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 400;
  color: var(--v2-text-primary);
  margin: 0;
}

.fill-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.fill-progress .ant-progress { flex: 1; }

.fill-completed {
  text-align: center;
  padding: 40px 0;
  color: var(--v2-text-secondary);
  font-size: 15px;
}

.fill-card {
  background: var(--v2-bg-card);
  border: 1px solid var(--v2-border-light);
  border-radius: var(--v2-radius);
  padding: 20px;
  margin-bottom: 16px;
}

.fill-card-type {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.fill-card-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--v2-text-primary);
}

.fill-dimensions {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

.fill-dim-row {
  padding: 12px;
  background: var(--v2-bg);
  border-radius: var(--v2-radius-sm);
}

.fill-dim-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--v2-text-primary);
  margin-bottom: 4px;
}

.fill-dim-desc {
  font-size: 12px;
  color: var(--v2-text-muted);
  margin-bottom: 8px;
}

.eval-rate {
  font-size: 28px;
}

.eval-rate :deep(.ant-rate-star) {
  margin-inline-end: 12px;
}

.fill-comment {
  margin-bottom: 8px;
}

.fill-nav {
  display: flex;
  justify-content: space-between;
  padding-bottom: 24px;
}

@media (max-width: 768px) {
  .evaluation-fill { padding: 12px; }
  .page-title { font-size: 18px; text-align: center; }
  .fill-nav .ant-btn { min-height: 44px; }
}
</style>
