<template>
  <div class="training-report-content">
    <div class="report-header">
      <div>
        <div class="report-title">总结报告</div>
        <div class="report-subtitle">
          通过 AI 汇总培训执行、出勤与考试表现，生成可人工审核的班级总结报告。
        </div>
      </div>
      <a-space>
        <a-tag v-if="latestReportConfirmedAt" color="green">
          最新已确认：{{ formatDateTime(latestReportConfirmedAt) }}
        </a-tag>
        <a-tag v-else-if="hasPendingReportTask" color="orange">有待审核草稿</a-tag>
        <a-button type="primary" :loading="creating" :disabled="!canManage" @click="handleCreateTask">
          AI生成培训班总结报告
        </a-button>
      </a-space>
    </div>

    <div class="report-layout">
      <div class="report-side">
        <a-card size="small" title="待审核任务" :bordered="false">
          <a-spin :spinning="loadingTasks">
            <a-empty v-if="!draftTasks.length" description="暂无待审核任务" />
            <div v-else class="side-list">
              <button
                v-for="task in draftTasks"
                :key="task.id"
                class="side-item"
                :class="{ active: selectedTaskId === task.id }"
                @click="selectTask(task)"
              >
                <div class="side-item-title">{{ task.taskName || task.task_name }}</div>
                <div class="side-item-meta">
                  <span>{{ statusLabel(task.status) }}</span>
                  <span>{{ formatDateTime(task.createdAt || task.created_at) }}</span>
                </div>
              </button>
            </div>
          </a-spin>
        </a-card>

        <a-card size="small" title="历史版本" :bordered="false" style="margin-top: 16px">
          <a-spin :spinning="loadingSnapshots">
            <a-empty v-if="!snapshots.length" description="暂无已确认版本" />
            <div v-else class="side-list">
              <button
                v-for="snapshot in snapshots"
                :key="snapshot.id"
                class="side-item"
                :class="{ active: !selectedTaskId && selectedSnapshotId === snapshot.id }"
                @click="selectSnapshot(snapshot)"
              >
                <div class="side-item-title">
                  V{{ snapshot.versionNo || snapshot.version_no }} · {{ snapshot.title }}
                </div>
                <div class="side-item-meta">
                  <span>{{ formatDateTime(snapshot.confirmedAt || snapshot.confirmed_at) }}</span>
                </div>
              </button>
            </div>
          </a-spin>
        </a-card>
      </div>

      <div class="report-main">
        <a-card :bordered="false">
          <a-spin :spinning="loadingDetail || saving || confirming || deleting">
            <template v-if="selectedTask">
              <div class="editor-head">
                <div>
                  <div class="section-title">待审核草稿</div>
                  <div class="section-subtitle">
                    可修改报告标题和正文，KPI 指标仅作为审核参考。
                  </div>
                </div>
                <a-space>
                  <a-button @click="saveDraft">保存草稿</a-button>
                  <a-button type="primary" @click="confirmTask">确认发布</a-button>
                  <a-button danger @click="deleteTask">删除任务</a-button>
                </a-space>
              </div>

              <a-form layout="vertical">
                <a-form-item label="报告标题">
                  <a-input v-model:value="editorForm.title" :maxlength="200" />
                </a-form-item>
                <div class="kpi-grid">
                  <div v-for="item in currentKpis" :key="item.key" class="kpi-card">
                    <div class="kpi-label">{{ item.label }}</div>
                    <div class="kpi-value">
                      {{ item.value }}<span v-if="item.unit" class="kpi-unit">{{ item.unit }}</span>
                    </div>
                    <div v-if="item.highlight" class="kpi-highlight">{{ item.highlight }}</div>
                  </div>
                </div>
                <a-form-item label="报告正文（Markdown）" style="margin-top: 16px">
                  <a-textarea v-model:value="editorForm.reportMarkdown" :rows="18" />
                </a-form-item>
              </a-form>

              <div class="preview-section">
                <div class="section-title">预览</div>
                <div class="markdown-preview">{{ editorForm.reportMarkdown }}</div>
              </div>
            </template>

            <template v-else-if="selectedSnapshot">
              <div class="editor-head">
                <div>
                  <div class="section-title">{{ selectedSnapshot.title }}</div>
                  <div class="section-subtitle">
                    版本 V{{ selectedSnapshot.versionNo || selectedSnapshot.version_no }} · 已确认于
                    {{ formatDateTime(selectedSnapshot.confirmedAt || selectedSnapshot.confirmed_at) }}
                  </div>
                </div>
              </div>

              <div class="kpi-grid">
                <div v-for="item in currentKpis" :key="item.key" class="kpi-card">
                  <div class="kpi-label">{{ item.label }}</div>
                  <div class="kpi-value">
                    {{ item.value }}<span v-if="item.unit" class="kpi-unit">{{ item.unit }}</span>
                  </div>
                  <div v-if="item.highlight" class="kpi-highlight">{{ item.highlight }}</div>
                </div>
              </div>

              <div class="preview-section" style="margin-top: 16px">
                <div class="section-title">报告正文</div>
                <div class="markdown-preview">{{ selectedSnapshot.reportMarkdown || selectedSnapshot.report_markdown }}</div>
              </div>
            </template>

            <a-empty
              v-else
              description="暂无总结报告"
            >
              <a-button type="primary" :disabled="!canManage" @click="handleCreateTask">
                AI生成培训班总结报告
              </a-button>
            </a-empty>
          </a-spin>
        </a-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  confirmAiTrainingReportTask,
  createAiTrainingReportTask,
  deleteAiTrainingReportTask,
  getAiTrainingReportTaskDetail,
  getAiTrainingReportTasks,
  updateAiTrainingReportTaskResult,
} from '@/api/ai'
import { getTrainingReportSnapshots } from '@/api/training'

const props = defineProps({
  trainingId: {
    type: Number,
    required: true,
  },
  trainingName: {
    type: String,
    default: '',
  },
  canManage: {
    type: Boolean,
    default: false,
  },
  latestReportConfirmedAt: {
    type: [String, Date],
    default: null,
  },
  hasPendingReportTask: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['refresh'])

const loadingTasks = ref(false)
const loadingSnapshots = ref(false)
const loadingDetail = ref(false)
const creating = ref(false)
const saving = ref(false)
const confirming = ref(false)
const deleting = ref(false)

const tasks = ref([])
const snapshots = ref([])
const selectedTaskId = ref(null)
const selectedSnapshotId = ref(null)
const selectedTask = ref(null)

const editorForm = reactive({
  title: '',
  reportMarkdown: '',
})

const draftTasks = computed(() => tasks.value.filter((item) => item.status !== 'confirmed'))

const selectedSnapshot = computed(() => {
  if (!selectedSnapshotId.value) return snapshots.value[0] || null
  return snapshots.value.find((item) => item.id === selectedSnapshotId.value) || null
})

const currentKpis = computed(() => {
  if (selectedTask.value?.draft?.kpiOverview?.length) return selectedTask.value.draft.kpiOverview
  if (selectedTask.value?.draft?.kpi_overview?.length) return selectedTask.value.draft.kpi_overview
  if (selectedSnapshot.value?.kpiOverview?.length) return selectedSnapshot.value.kpiOverview
  return selectedSnapshot.value?.kpi_overview || []
})

async function loadTasks() {
  loadingTasks.value = true
  try {
    const data = await getAiTrainingReportTasks({ training_id: props.trainingId, size: -1 })
    tasks.value = data.items || []
    if (selectedTaskId.value && !tasks.value.some((item) => item.id === selectedTaskId.value)) {
      selectedTaskId.value = null
      selectedTask.value = null
    }
  } catch (error) {
    message.error(error.message || '加载报告任务失败')
  } finally {
    loadingTasks.value = false
  }
}

async function loadSnapshots() {
  loadingSnapshots.value = true
  try {
    snapshots.value = await getTrainingReportSnapshots(props.trainingId)
    if (!selectedSnapshotId.value && snapshots.value.length) {
      selectedSnapshotId.value = snapshots.value[0].id
    }
  } catch (error) {
    message.error(error.message || '加载报告版本失败')
  } finally {
    loadingSnapshots.value = false
  }
}

async function loadTaskDetail(taskId) {
  loadingDetail.value = true
  try {
    const detail = await getAiTrainingReportTaskDetail(taskId)
    selectedTask.value = detail
    selectedTaskId.value = detail.id
    selectedSnapshotId.value = null
    editorForm.title = detail.draft?.title || ''
    editorForm.reportMarkdown = detail.draft?.reportMarkdown || detail.draft?.report_markdown || ''
  } catch (error) {
    message.error(error.message || '加载任务详情失败')
  } finally {
    loadingDetail.value = false
  }
}

async function reloadAll(options = {}) {
  await Promise.all([loadTasks(), loadSnapshots()])
  const nextTaskId = options.taskId || selectedTaskId.value || draftTasks.value[0]?.id
  if (nextTaskId) {
    await loadTaskDetail(nextTaskId)
    return
  }
  selectedTask.value = null
}

async function handleCreateTask() {
  if (!props.canManage) return
  creating.value = true
  try {
    const result = await createAiTrainingReportTask({
      trainingId: props.trainingId,
      taskName: props.trainingName ? `${props.trainingName}总结报告` : undefined,
    })
    message.success('总结报告草稿已生成')
    await reloadAll({ taskId: result.id })
    emit('refresh')
  } catch (error) {
    message.error(error.message || '生成报告失败')
  } finally {
    creating.value = false
  }
}

function selectTask(task) {
  loadTaskDetail(task.id)
}

function selectSnapshot(snapshot) {
  selectedTaskId.value = null
  selectedTask.value = null
  selectedSnapshotId.value = snapshot.id
}

async function saveDraft() {
  if (!selectedTaskId.value) return
  saving.value = true
  try {
    const result = await updateAiTrainingReportTaskResult(selectedTaskId.value, {
      title: editorForm.title,
      reportMarkdown: editorForm.reportMarkdown,
    })
    selectedTask.value = result
    message.success('草稿已保存')
    await loadTasks()
  } catch (error) {
    message.error(error.message || '保存草稿失败')
  } finally {
    saving.value = false
  }
}

function confirmTask() {
  if (!selectedTaskId.value) return
  Modal.confirm({
    title: '确认发布总结报告',
    content: '发布后会生成新的正式版本，并保留在历史版本中。',
    async onOk() {
      confirming.value = true
      try {
        await saveDraft()
        await confirmAiTrainingReportTask(selectedTaskId.value)
        message.success('总结报告已确认发布')
        selectedTaskId.value = null
        selectedTask.value = null
        await reloadAll()
        emit('refresh')
      } catch (error) {
        message.error(error.message || '确认发布失败')
      } finally {
        confirming.value = false
      }
    },
  })
}

function deleteTask() {
  if (!selectedTaskId.value) return
  Modal.confirm({
    title: '删除当前草稿任务',
    content: '删除后当前未确认草稿将不可恢复。',
    async onOk() {
      deleting.value = true
      try {
        await deleteAiTrainingReportTask(selectedTaskId.value)
        message.success('草稿任务已删除')
        selectedTaskId.value = null
        selectedTask.value = null
        await reloadAll()
        emit('refresh')
      } catch (error) {
        message.error(error.message || '删除任务失败')
      } finally {
        deleting.value = false
      }
    },
  })
}

function formatDateTime(value) {
  if (!value) return '-'
  return String(value).replace('T', ' ').slice(0, 16)
}

function statusLabel(status) {
  return {
    pending: '排队中',
    processing: '生成中',
    completed: '待审核',
    confirmed: '已确认',
    failed: '失败',
  }[status] || status
}

watch(() => props.trainingId, () => {
  selectedTaskId.value = null
  selectedSnapshotId.value = null
  selectedTask.value = null
  reloadAll()
})

onMounted(() => {
  reloadAll()
})
</script>

<style scoped>
.training-report-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.report-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f1f1f;
}

.report-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
}

.report-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 16px;
}

.report-side {
  min-width: 0;
}

.report-main {
  min-width: 0;
}

.side-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.side-item {
  width: 100%;
  text-align: left;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
  padding: 12px;
  cursor: pointer;
  transition: border-color .2s ease, background .2s ease;
}

.side-item:hover,
.side-item.active {
  border-color: #93c5fd;
  background: #eff6ff;
}

.side-item-title {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  line-height: 1.5;
}

.side-item-meta {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  font-size: 12px;
  color: #64748b;
}

.editor-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}

.section-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.kpi-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
  padding: 14px;
}

.kpi-label {
  font-size: 12px;
  color: #64748b;
}

.kpi-value {
  margin-top: 6px;
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}

.kpi-unit {
  margin-left: 4px;
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
}

.kpi-highlight {
  margin-top: 6px;
  font-size: 12px;
  color: #64748b;
}

.preview-section {
  margin-top: 8px;
}

.markdown-preview {
  margin-top: 12px;
  padding: 16px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  white-space: pre-wrap;
  line-height: 1.7;
  color: #334155;
}

@media (max-width: 1200px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .report-header,
  .editor-head {
    flex-direction: column;
  }

  .report-layout {
    grid-template-columns: 1fr;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>
