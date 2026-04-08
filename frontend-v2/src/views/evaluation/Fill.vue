<template>
  <div class="evaluation-fill">
    <div class="fill-header">
      <a-button type="text" @click="router.back()">← 返回</a-button>
      <h2 class="fill-title">{{ task?.title || '问卷填写' }}</h2>
    </div>

    <a-spin :spinning="loading">
      <div v-if="task && template" class="fill-body">
        <div class="fill-info">
          <a-tag :color="task.status === 'active' ? 'green' : 'default'">
            {{ task.status === 'active' ? '进行中' : '已结束' }}
          </a-tag>
          <span class="fill-info-type">{{ targetTypeLabel(task.target_type) }}</span>
          <span v-if="task.end_time" class="fill-info-deadline">截止 {{ formatTime(task.end_time) }}</span>
        </div>

        <div v-if="alreadySubmitted" class="fill-submitted">
          <CheckCircleOutlined style="font-size: 48px; color: var(--v2-success); margin-bottom: 12px" />
          <p>您已完成本次评价，感谢参与！</p>
        </div>

        <template v-else-if="task.status === 'active'">
          <div class="fill-dimensions">
            <div v-for="dim in dimensions" :key="dim.id" class="fill-dim-row">
              <div class="fill-dim-name">{{ dim.name }}</div>
              <div v-if="dim.description" class="fill-dim-desc">{{ dim.description }}</div>
              <a-rate v-model:value="scores[dim.id]" :count="5" allow-half />
            </div>
          </div>

          <div class="fill-comment">
            <div class="fill-dim-name">总体评语</div>
            <a-textarea
              v-model:value="comment"
              :rows="3"
              :maxlength="1000"
              show-count
              placeholder="请输入您的评价（选填）"
            />
          </div>

          <div class="fill-actions">
            <a-button type="primary" block :loading="submitting" @click="handleSubmit">
              提交评价
            </a-button>
          </div>
        </template>

        <div v-else class="fill-submitted">
          <p>该问卷已结束，无法填写</p>
        </div>
      </div>
      <a-empty v-else-if="!loading" description="问卷不存在或已删除" />
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { CheckCircleOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import axiosInstance from '@/api/custom-instance'

const route = useRoute()
const router = useRouter()
const taskId = Number(route.params.taskId)

const loading = ref(false)
const submitting = ref(false)
const task = ref<any>(null)
const template = ref<any>(null)
const dimensions = ref<any[]>([])
const scores = reactive<Record<number, number>>({})
const comment = ref('')
const alreadySubmitted = ref(false)

function targetTypeLabel(type: string) {
  const map: Record<string, string> = {
    course: '课程评价',
    instructor: '教官评价',
    training: '培训班评价',
    training_base: '基地评价',
  }
  return map[type] || type
}

function formatTime(time: string) {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

async function fetchData() {
  loading.value = true
  try {
    // 获取任务列表找到当前任务
    const { data: tasks } = await axiosInstance.get('/evaluations/tasks')
    task.value = (tasks || []).find((t: any) => t.id === taskId)
    if (!task.value) return

    // 获取模板（含维度）
    const { data: tpl } = await axiosInstance.get(`/evaluations/templates/${task.value.template_id}`)
    template.value = tpl
    dimensions.value = tpl?.dimensions || []
    for (const dim of dimensions.value) {
      scores[dim.id] = 0
    }

    // 检查是否已评
    const { data: records } = await axiosInstance.get('/evaluations/records', {
      params: { task_id: taskId },
    })
    const userId = JSON.parse(localStorage.getItem('userInfo') || '{}')?.id
    if (userId && (records || []).some((r: any) => r.user_id === userId)) {
      alreadySubmitted.value = true
    }
  } catch {
    task.value = null
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  const unrated = dimensions.value.filter(d => !scores[d.id])
  if (unrated.length) {
    message.warning(`请完成所有维度的评分（还有 ${unrated.length} 项未评）`)
    return
  }

  submitting.value = true
  try {
    await axiosInstance.post('/evaluations/submit', {
      target_type: task.value.target_type,
      target_id: task.value.target_id,
      task_id: taskId,
      training_id: task.value.training_id || undefined,
      scores: dimensions.value.map(d => ({
        dimension_id: d.id,
        score: Math.round(scores[d.id]),
      })),
      comment: comment.value || undefined,
    })
    message.success('评价提交成功')
    alreadySubmitted.value = true
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '提交失败')
  } finally {
    submitting.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.evaluation-fill {
  padding: 16px;
  max-width: 640px;
  margin: 0 auto;
}

.fill-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.fill-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--v2-text-primary);
  margin: 0;
}

.fill-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  font-size: 13px;
  color: var(--v2-text-muted);
}

.fill-info-type {
  font-weight: 500;
  color: var(--v2-text-secondary);
}

.fill-submitted {
  text-align: center;
  padding: 40px 0;
  color: var(--v2-text-secondary);
  font-size: 15px;
}

.fill-dimensions {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 24px;
}

.fill-dim-row {
  padding: 16px;
  background: var(--v2-bg);
  border-radius: var(--v2-radius-sm);
}

.fill-dim-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin-bottom: 4px;
}

.fill-dim-desc {
  font-size: 12px;
  color: var(--v2-text-muted);
  margin-bottom: 8px;
}

.fill-comment {
  margin-bottom: 24px;
}

.fill-comment .fill-dim-name {
  margin-bottom: 8px;
}

.fill-actions {
  padding-bottom: 24px;
}

@media (max-width: 768px) {
  .evaluation-fill {
    padding: 12px;
  }

  .fill-actions .ant-btn {
    min-height: 44px;
  }
}
</style>
