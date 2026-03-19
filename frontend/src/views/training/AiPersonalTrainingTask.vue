<template>
  <ai-task-tabs-layout
    v-model:active-tab="activeTab"
    title="AI个训方案"
    subtitle="基于训历、考试和学习行为生成建议方案，确认后保存方案快照"
    tag-text="训练智能体"
    :task-list="taskList"
    :task-loading="taskLoading"
    :active-task-id="activeTask?.id || null"
    :status-labels="statusLabels"
    :status-colors="statusColors"
    @refresh-tasks="loadTasks"
    @select-task="selectTask"
  >
    <template #create>
      <div class="create-form-wrap">
        <a-form layout="vertical">
          <a-form-item label="任务名称" required>
            <a-input v-model:value="taskForm.taskName" placeholder="例：张三个训方案" />
          </a-form-item>
          <a-form-item label="培训班" required>
            <a-select v-model:value="taskForm.trainingId" :options="trainingOptions" placeholder="请选择培训班" @change="handleTrainingChange" />
          </a-form-item>
          <a-form-item label="目标学员" required>
            <a-select v-model:value="taskForm.targetUserId" :options="studentOptions" placeholder="请选择学员" :disabled="authStore.isStudent" />
          </a-form-item>
          <a-row :gutter="12">
            <a-col :span="12">
              <a-form-item label="方案周期（天）">
                <a-input-number v-model:value="taskForm.planCycleDays" :min="7" :max="90" style="width:100%" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="每周训练频次">
                <a-input-number v-model:value="taskForm.weeklySessions" :min="1" :max="14" style="width:100%" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-form-item label="聚焦方向">
            <a-select v-model:value="taskForm.focusMode">
              <a-select-option value="auto">自动判断</a-select-option>
              <a-select-option value="theory">理论强化</a-select-option>
              <a-select-option value="practice">实操强化</a-select-option>
              <a-select-option value="exam">考前强化</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="训练目标">
            <a-input v-model:value="taskForm.planGoal" />
          </a-form-item>
          <a-form-item label="补充说明">
            <a-textarea v-model:value="taskForm.notes" :rows="3" />
          </a-form-item>
          <a-button type="primary" block :loading="creating" @click="handleCreateTask">创建任务</a-button>
        </a-form>
      </div>
    </template>

    <template #task-description="{ item }">
      {{ item.targetUserName || '未指定学员' }} · {{ item.summaryText || '待查看方案' }}
    </template>

    <template #detail>
      <template v-if="activeTask">
        <div class="detail-header">
          <div>
            <div class="detail-title">{{ activeTask.taskName }}</div>
            <div class="detail-sub">{{ activeTask.targetUserName || '未指定学员' }} · {{ activeTask.trainingName || '未命名培训班' }}</div>
          </div>
          <a-space>
            <a-button @click="loadTaskDetail(activeTask.id)">刷新详情</a-button>
            <a-button :disabled="!canEditCurrentTask" :loading="saving" @click="handleSaveTask">保存修改</a-button>
            <a-button type="primary" :disabled="!canConfirmCurrentTask" :loading="confirming" @click="handleConfirmTask">
              确认方案
            </a-button>
          </a-space>
        </div>

        <ai-task-timeline
          :status="activeTask.status"
          :created-at="activeTask.createdAt"
          :completed-at="activeTask.completedAt"
          :confirmed-at="activeTask.confirmedAt"
        />

        <div class="detail-section" v-if="activeTask.portrait">
          <div class="detail-section-title">画像标签</div>
          <div class="tag-list">
            <a-tag v-for="item in activeTask.portrait.tags || []" :key="item.code" :color="levelColors[item.level] || 'blue'">
              {{ item.label }}
            </a-tag>
          </div>
          <a-list :data-source="activeTask.portrait.evidence || []" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :title="item.label" :description="item.value" />
              </a-list-item>
            </template>
          </a-list>
        </div>

        <div class="detail-section" v-if="activeTask.plan">
          <div class="detail-section-title">方案摘要</div>
          <a-textarea v-model:value="activeTask.plan.summary" :rows="3" :disabled="!canEditCurrentTask" />
        </div>

        <div class="detail-section" v-if="activeTask.plan">
          <div class="detail-section-title">训练目标</div>
          <a-textarea
            :value="(activeTask.plan.objectives || []).join('\n')"
            :disabled="!canEditCurrentTask"
            :rows="4"
            @change="handleObjectivesChange"
          />
        </div>

        <div class="detail-section" v-if="activeTask.plan">
          <div class="detail-section-title">训练动作</div>
          <div class="action-grid">
            <div v-for="(item, index) in activeTask.plan.actions || []" :key="index" class="action-card">
              <div class="action-title">{{ item.title }}</div>
              <div class="action-desc">{{ item.description }}</div>
              <div class="action-meta">{{ item.frequency }} · {{ item.durationMinutes }} 分钟</div>
              <div class="action-tip">{{ item.executionTips }}</div>
            </div>
          </div>
        </div>

        <div class="detail-section" v-if="activeTask.plan">
          <div class="detail-section-title">资源推荐</div>
          <div class="resource-grid">
            <div v-for="item in activeTask.plan.resourceRecommendations || []" :key="item.resourceId" class="resource-card">
              <div class="resource-title">{{ item.title }}</div>
              <div class="resource-desc">{{ item.reason }}</div>
              <div class="resource-tags">{{ (item.tagNames || []).join('、') || '无标签' }}</div>
            </div>
          </div>
        </div>
      </template>
      <a-empty v-else description="请选择任务查看详情" />
    </template>
  </ai-task-tabs-layout>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import {
  confirmAiPersonalTrainingTask,
  createAiPersonalTrainingTask,
  getAiPersonalTrainingTaskDetail,
  getAiPersonalTrainingTasks,
  updateAiPersonalTrainingTaskResult,
} from '@/api/ai'
import { getTrainingHistories, getTrainings } from '@/api/training'
import AiTaskTabsLayout from '@/views/exam/components/AiTaskTabsLayout.vue'
import AiTaskTimeline from '@/views/exam/components/AiTaskTimeline.vue'

const route = useRoute()
const authStore = useAuthStore()
const activeTab = ref('create')
const taskList = ref([])
const activeTask = ref(null)
const taskLoading = ref(false)
const creating = ref(false)
const saving = ref(false)
const confirming = ref(false)
const trainings = ref([])
const students = ref([])

const statusLabels = { pending: '待处理', processing: '处理中', completed: '已完成', confirmed: '已确认', failed: '处理失败' }
const statusColors = { pending: 'default', processing: 'processing', completed: 'blue', confirmed: 'green', failed: 'red' }
const levelColors = { low: 'green', medium: 'orange', high: 'red' }

const taskForm = reactive({
  taskName: '',
  trainingId: route.params.id ? Number(route.params.id) : undefined,
  targetUserId: route.query.userId ? Number(route.query.userId) : authStore.currentUser?.id,
  planGoal: '补齐短板，稳步提升',
  planCycleDays: 14,
  weeklySessions: 3,
  focusMode: 'auto',
  notes: '',
})

const trainingOptions = computed(() => (trainings.value || []).map(item => ({ label: item.name, value: item.id })))
const studentOptions = computed(() => (students.value || []).map(item => ({
  label: `${item.userNickname || item.userName} (${item.policeId || '无警号'})`,
  value: item.userId,
})))
const canEditCurrentTask = computed(() => activeTask.value?.status === 'completed' && activeTask.value?.createdBy === authStore.currentUser?.id)
const canConfirmCurrentTask = computed(() => canEditCurrentTask.value)

function cloneDeep(value) {
  return JSON.parse(JSON.stringify(value))
}

async function loadTrainings() {
  try {
    const result = await getTrainings({ size: -1 })
    trainings.value = result.items || result || []
  } catch {
    trainings.value = []
  }
}

async function loadStudents(trainingId) {
  if (!trainingId) {
    students.value = []
    return
  }
  try {
    const result = await getTrainingHistories(trainingId)
    students.value = result || []
  } catch {
    students.value = []
  }
}

async function loadTasks() {
  taskLoading.value = true
  try {
    const result = await getAiPersonalTrainingTasks({ size: -1 })
    taskList.value = result.items || []
    if (!activeTask.value && taskList.value.length) {
      await loadTaskDetail(taskList.value[0].id)
    }
  } catch (error) {
    message.error(error.message || '加载任务失败')
  } finally {
    taskLoading.value = false
  }
}

async function loadTaskDetail(taskId) {
  try {
    const result = await getAiPersonalTrainingTaskDetail(taskId)
    activeTask.value = cloneDeep(result)
  } catch (error) {
    message.error(error.message || '加载任务详情失败')
  }
}

async function selectTask(taskId) {
  await loadTaskDetail(taskId)
}

async function handleTrainingChange() {
  if (!authStore.isStudent) {
    await loadStudents(taskForm.trainingId)
  }
}

async function handleCreateTask() {
  if (!taskForm.taskName.trim() || !taskForm.trainingId || !taskForm.targetUserId) {
    message.warning('请填写任务名称并选择培训班和学员')
    return
  }
  creating.value = true
  try {
    const result = await createAiPersonalTrainingTask({
      taskName: taskForm.taskName,
      trainingId: taskForm.trainingId,
      targetUserId: taskForm.targetUserId,
      planGoal: taskForm.planGoal,
      planCycleDays: taskForm.planCycleDays,
      weeklySessions: taskForm.weeklySessions,
      focusMode: taskForm.focusMode,
      notes: taskForm.notes,
    })
    message.success('个训任务已创建')
    await loadTasks()
    await loadTaskDetail(result.id)
    activeTab.value = 'list'
  } catch (error) {
    message.error(error.message || '创建任务失败')
  } finally {
    creating.value = false
  }
}

function handleObjectivesChange(event) {
  if (!activeTask.value?.plan) return
  const value = event?.target?.value || ''
  activeTask.value.plan.objectives = value.split(/\r?\n/).map(item => item.trim()).filter(Boolean)
}

async function handleSaveTask() {
  if (!activeTask.value || !canEditCurrentTask.value) return false
  saving.value = true
  try {
    const result = await updateAiPersonalTrainingTaskResult(activeTask.value.id, {
      taskName: activeTask.value.taskName,
      portrait: activeTask.value.portrait,
      plan: activeTask.value.plan,
    })
    activeTask.value = cloneDeep(result)
    await loadTasks()
    message.success('方案已保存')
    return true
  } catch (error) {
    message.error(error.message || '保存失败')
    return false
  } finally {
    saving.value = false
  }
}

async function handleConfirmTask() {
  if (!activeTask.value || !canConfirmCurrentTask.value) return
  confirming.value = true
  try {
    const saved = await handleSaveTask()
    if (!saved) {
      return
    }
    const result = await confirmAiPersonalTrainingTask(activeTask.value.id)
    activeTask.value = cloneDeep(result)
    await loadTasks()
    message.success('个训方案已确认并保存快照')
  } catch (error) {
    message.error(error.message || '确认失败')
  } finally {
    confirming.value = false
  }
}

onMounted(async () => {
  await loadTrainings()
  if (!authStore.isStudent && taskForm.trainingId) {
    await loadStudents(taskForm.trainingId)
  }
  await loadTasks()
})
</script>

<style scoped>
.create-form-wrap { max-width: 880px; }
.detail-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 16px; }
.detail-title { font-size: 18px; font-weight: 600; color: #001234; }
.detail-sub { margin-top: 6px; color: #8c8c8c; }
.detail-section { margin-top: 20px; }
.detail-section-title { margin-bottom: 12px; font-size: 15px; font-weight: 600; color: #1f1f1f; }
.tag-list { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.action-grid, .resource-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.action-card, .resource-card { padding: 14px; border: 1px solid #eef0f5; border-radius: 10px; background: #fff; }
.action-title, .resource-title { font-size: 15px; font-weight: 600; color: #1f1f1f; }
.action-desc, .resource-desc { margin-top: 8px; color: #595959; line-height: 1.7; }
.action-meta, .resource-tags { margin-top: 10px; color: #8c8c8c; font-size: 12px; }
.action-tip { margin-top: 8px; color: #262626; font-size: 13px; }
@media (max-width: 960px) {
  .detail-header { flex-direction: column; }
  .action-grid, .resource-grid { grid-template-columns: 1fr; }
}
</style>
