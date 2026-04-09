<template>
  <div class="class-report-tab">
    <div class="report-toolbar">
      <div>
        <div class="report-title">总结报告</div>
        <div class="report-desc">汇总班级执行、出勤和考试数据，生成可人工审核的班级总结报告。</div>
      </div>
      <a-space>
        <a-tag v-if="latestReportConfirmedAt" color="green">
          最新已确认：{{ formatDateTime(latestReportConfirmedAt) }}
        </a-tag>
        <a-tag v-else-if="hasPendingReportTask" color="orange">有待审核草稿</a-tag>
        <a-button v-if="canManage" type="primary" :loading="creating" @click="createTask">
          AI生成总结报告
        </a-button>
      </a-space>
    </div>

    <div class="report-shell">
      <aside class="report-sidebar">
        <div class="sidebar-block">
          <div class="sidebar-title">待审核任务</div>
          <a-spin :spinning="loadingTasks">
            <a-empty v-if="!draftTasks.length" description="暂无待审核任务" />
            <div v-else class="sidebar-list">
              <button
                v-for="task in draftTasks"
                :key="task.id"
                class="sidebar-item"
                :class="{ active: selectedTaskId === task.id }"
                @click="openTask(task.id)"
              >
                <div class="sidebar-item-title">{{ task.task_name || task.taskName }}</div>
                <div class="sidebar-item-meta">
                  <span>{{ statusLabel(task.status) }}</span>
                  <span>{{ formatDateTime(task.created_at || task.createdAt) }}</span>
                </div>
              </button>
            </div>
          </a-spin>
        </div>

        <div class="sidebar-block">
          <div class="sidebar-title">历史版本</div>
          <a-spin :spinning="loadingSnapshots">
            <a-empty v-if="!snapshots.length" description="暂无版本" />
            <div v-else class="sidebar-list">
              <button
                v-for="snapshot in snapshots"
                :key="snapshot.id"
                class="sidebar-item"
                :class="{ active: !selectedTaskId && selectedSnapshotId === snapshot.id }"
                @click="selectSnapshot(snapshot.id)"
              >
                <div class="sidebar-item-title">
                  V{{ snapshot.version_no || snapshot.versionNo }} · {{ snapshot.title }}
                </div>
                <div class="sidebar-item-meta">
                  <span>{{ formatDateTime(snapshot.confirmed_at || snapshot.confirmedAt) }}</span>
                </div>
              </button>
            </div>
          </a-spin>
        </div>
      </aside>

      <section class="report-main">
        <a-card :bordered="false">
          <a-spin :spinning="loadingDetail || saving || confirming || deleting">
            <template v-if="selectedTask">
              <template v-if="isEditableTask">
                <div class="main-head">
                  <div>
                    <div class="main-title">待审核草稿</div>
                    <div class="main-subtitle">可编辑标题和正文，确认后将沉淀为正式版本。</div>
                  </div>
                  <a-space v-if="canManage">
                    <a-button @click="saveTask">保存草稿</a-button>
                    <a-button type="primary" @click="confirmTask">确认发布</a-button>
                    <a-button danger @click="removeTask">删除任务</a-button>
                  </a-space>
                </div>

                <a-form layout="vertical">
                  <a-form-item label="报告标题">
                    <a-input v-model:value="editor.title" :maxlength="200" />
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
                    <a-button type="link" @click="openMarkdownModal">编辑报告正文</a-button>
                  </a-form-item>
                </a-form>

                <div class="preview-box">
                  <div class="main-title">预览</div>
                  <div class="markdown-box">{{ editor.reportMarkdown }}</div>
                </div>
              </template>

              <template v-else-if="isRunningTask">
                <div class="state-box">
                  <div class="main-title">{{ statusLabel(selectedTask.status) }}</div>
                  <div class="main-subtitle">报告正在后台异步生成，页面会自动刷新任务状态。</div>
                  <div class="state-meta">
                    <span>任务名称：{{ selectedTask.task_name || selectedTask.taskName }}</span>
                    <span>创建时间：{{ formatDateTime(selectedTask.created_at || selectedTask.createdAt) }}</span>
                  </div>
                </div>
              </template>

              <template v-else-if="isFailedTask">
                <div class="state-box state-box-error">
                  <div class="main-title">生成失败</div>
                  <div class="main-subtitle">
                    {{ selectedTask.error_message || selectedTask.errorMessage || 'AI 报告生成失败，请稍后重试。' }}
                  </div>
                  <a-space v-if="canManage" style="margin-top: 12px">
                    <a-button type="primary" :loading="creating" @click="createTask">重新生成</a-button>
                    <a-button danger @click="removeTask">删除任务</a-button>
                  </a-space>
                </div>
              </template>
            </template>

            <template v-else-if="activeSnapshot">
              <div class="main-head">
                <div>
                  <div class="main-title">{{ activeSnapshot.title }}</div>
                  <div class="main-subtitle">
                    版本 V{{ activeSnapshot.version_no || activeSnapshot.versionNo }} ·
                    {{ formatDateTime(activeSnapshot.confirmed_at || activeSnapshot.confirmedAt) }}
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

              <div class="preview-box">
                <div class="main-title">报告正文</div>
                <div class="markdown-box">{{ activeSnapshot.report_markdown || activeSnapshot.reportMarkdown }}</div>
              </div>
            </template>

            <a-empty v-else description="暂无总结报告">
              <a-button v-if="canManage" type="primary" @click="createTask">AI生成总结报告</a-button>
            </a-empty>
          </a-spin>
        </a-card>

        <!-- 报告正文编辑弹窗 -->
        <a-modal
          v-model:open="markdownModalVisible"
          title="编辑报告正文"
          :width="800"
          :footer="null"
          centered
        >
          <div class="markdown-edit-modal">
            <a-textarea
              v-model:value="markdownModalContent"
              :rows="20"
              placeholder="请输入报告正文（支持 Markdown 格式）..."
            />
            <div class="markdown-edit-actions">
              <a-button @click="markdownModalVisible = false">取消</a-button>
              <a-button type="primary" @click="saveMarkdownModal">保存</a-button>
            </div>
          </div>
        </a-modal>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  confirmTrainingReportTask,
  createTrainingReportTask,
  deleteTrainingReportTask,
  getTrainingReportSnapshots,
  getTrainingReportTaskDetail,
  getTrainingReportTasks,
  updateTrainingReportTask,
} from '@/api/training-report'

const props = defineProps<{
  trainingId: number
  trainingName?: string
  canManage: boolean
  latestReportConfirmedAt?: string | null
  hasPendingReportTask?: boolean
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

type ReportTask = Record<string, any>
type ReportSnapshot = Record<string, any>

const loadingTasks = ref(false)
const loadingSnapshots = ref(false)
const loadingDetail = ref(false)
const creating = ref(false)
const saving = ref(false)
const confirming = ref(false)
const deleting = ref(false)
const markdownModalVisible = ref(false)
const markdownModalContent = ref('')

const tasks = ref<ReportTask[]>([])
const snapshots = ref<ReportSnapshot[]>([])
const selectedTaskId = ref<number | null>(null)
const selectedSnapshotId = ref<number | null>(null)
const selectedTask = ref<ReportTask | null>(null)
const pollingTimer = ref<number | null>(null)

const editor = reactive({
  title: '',
  reportMarkdown: '',
})

const draftTasks = computed(() => tasks.value.filter((item) => item.status !== 'confirmed'))
const isEditableTask = computed(() => selectedTask.value?.status === 'completed')
const isRunningTask = computed(() => ['pending', 'processing'].includes(selectedTask.value?.status))
const isFailedTask = computed(() => selectedTask.value?.status === 'failed')

const activeSnapshot = computed<ReportSnapshot | null>(() => {
  if (!selectedSnapshotId.value) return snapshots.value[0] || null
  return snapshots.value.find((item) => item.id === selectedSnapshotId.value) || null
})

const currentKpis = computed<Record<string, any>[]>(() => {
  const draft = selectedTask.value?.draft
  if (draft?.kpi_overview?.length) return draft.kpi_overview
  if (draft?.kpiOverview?.length) return draft.kpiOverview
  if (activeSnapshot.value?.kpi_overview?.length) return activeSnapshot.value.kpi_overview
  return activeSnapshot.value?.kpiOverview || []
})

async function loadTasks(options: { silent?: boolean } = {}) {
  loadingTasks.value = true
  try {
    const data = await getTrainingReportTasks({ training_id: props.trainingId, size: -1 })
    tasks.value = data.items || []
  } catch (error: any) {
    if (!options.silent) {
      message.error(error?.message || '加载报告任务失败')
    }
  } finally {
    loadingTasks.value = false
  }
}

async function loadSnapshots(options: { silent?: boolean } = {}) {
  loadingSnapshots.value = true
  try {
    snapshots.value = await getTrainingReportSnapshots(props.trainingId)
    if (!selectedSnapshotId.value && snapshots.value.length) {
      selectedSnapshotId.value = snapshots.value[0].id
    }
  } catch (error: any) {
    if (!options.silent) {
      message.error(error?.message || '加载报告版本失败')
    }
  } finally {
    loadingSnapshots.value = false
  }
}

function clearPolling() {
  if (pollingTimer.value !== null) {
    window.clearTimeout(pollingTimer.value)
    pollingTimer.value = null
  }
}

function startPolling(taskId: number) {
  clearPolling()
  pollingTimer.value = window.setTimeout(async () => {
    try {
      await Promise.all([loadTasks({ silent: true }), loadSnapshots({ silent: true })])
      if (selectedTaskId.value === taskId) {
        await openTask(taskId, true)
      }
    } catch {
      startPolling(taskId)
    }
  }, 3000)
}

async function openTask(taskId: number, silent = false) {
  loadingDetail.value = true
  try {
    const detail = await getTrainingReportTaskDetail(taskId)
    selectedTaskId.value = detail.id
    selectedTask.value = detail
    selectedSnapshotId.value = null
    editor.title = detail.draft?.title || ''
    editor.reportMarkdown = detail.draft?.report_markdown || detail.draft?.reportMarkdown || ''
    if (['pending', 'processing'].includes(detail.status)) {
      startPolling(detail.id)
    } else {
      clearPolling()
    }
  } catch (error: any) {
    if (!silent) {
      message.error(error?.message || '加载任务详情失败')
    }
    clearPolling()
  } finally {
    loadingDetail.value = false
  }
}

function selectSnapshot(snapshotId: number) {
  selectedTaskId.value = null
  selectedTask.value = null
  selectedSnapshotId.value = snapshotId
  clearPolling()
}

async function reload(taskId?: number) {
  await Promise.all([loadTasks(), loadSnapshots()])
  const nextTaskId = taskId ?? selectedTaskId.value ?? draftTasks.value[0]?.id
  if (nextTaskId) {
    await openTask(nextTaskId)
    return
  }
  selectedTask.value = null
}

async function createTask() {
  if (!props.canManage) return
  creating.value = true
  try {
    const detail = await createTrainingReportTask({
      training_id: props.trainingId,
      task_name: props.trainingName ? `${props.trainingName}总结报告` : undefined,
    })
    message.success('已提交 AI 生成任务，系统正在后台生成报告')
    await reload(detail.id)
    emit('refresh')
  } catch (error: any) {
    message.error(error?.message || '生成报告失败')
  } finally {
    creating.value = false
  }
}

async function saveTask() {
  if (!selectedTaskId.value) return
  saving.value = true
  try {
    const detail = await updateTrainingReportTask(selectedTaskId.value, {
      title: editor.title,
      report_markdown: editor.reportMarkdown,
    })
    selectedTask.value = detail
    message.success('草稿已保存')
    await loadTasks()
  } catch (error: any) {
    message.error(error?.message || '保存草稿失败')
  } finally {
    saving.value = false
  }
}

function confirmTask() {
  if (!selectedTaskId.value) return
  Modal.confirm({
    title: '确认发布总结报告',
    content: '确认后会生成新的正式版本，并出现在历史版本中。',
    async onOk() {
      confirming.value = true
      try {
        await saveTask()
        await confirmTrainingReportTask(selectedTaskId.value as number)
        message.success('总结报告已确认发布')
        selectedTaskId.value = null
        selectedTask.value = null
        await reload()
        emit('refresh')
      } catch (error: any) {
        message.error(error?.message || '确认发布失败')
      } finally {
        confirming.value = false
      }
    },
  })
}

function removeTask() {
  if (!selectedTaskId.value) return
  Modal.confirm({
    title: '删除当前草稿任务',
    content: '删除后当前未确认草稿将不可恢复。',
    async onOk() {
      deleting.value = true
      try {
        await deleteTrainingReportTask(selectedTaskId.value as number)
        message.success('草稿任务已删除')
        selectedTaskId.value = null
        selectedTask.value = null
        await reload()
        emit('refresh')
      } catch (error: any) {
        message.error(error?.message || '删除任务失败')
      } finally {
        deleting.value = false
      }
    },
  })
}

function openMarkdownModal() {
  markdownModalContent.value = editor.reportMarkdown
  markdownModalVisible.value = true
}

function saveMarkdownModal() {
  editor.reportMarkdown = markdownModalContent.value
  markdownModalVisible.value = false
}

function formatDateTime(value?: string | null) {
  if (!value) return '-'
  return String(value).replace('T', ' ').slice(0, 16)
}

function statusLabel(status?: string) {
  return {
    pending: '排队中',
    processing: '生成中',
    completed: '待审核',
    confirmed: '已确认',
    failed: '失败',
  }[status || ''] || status || '-'
}

watch(() => props.trainingId, () => {
  clearPolling()
  selectedTaskId.value = null
  selectedSnapshotId.value = null
  selectedTask.value = null
  reload()
})

onMounted(() => {
  reload()
})

onBeforeUnmount(() => {
  clearPolling()
})
</script>

<style scoped>
.class-report-tab {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.report-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.report-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--v2-text-primary);
}

.report-desc {
  margin-top: 6px;
  color: var(--v2-text-muted);
  font-size: 13px;
  line-height: 1.7;
}

.report-shell {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 16px;
}

.report-sidebar,
.report-main {
  min-width: 0;
}

.sidebar-block {
  padding: 16px;
  border-radius: var(--v2-radius);
  background: var(--v2-bg-card);
  border: 1px solid var(--v2-border-light);
}

.sidebar-block + .sidebar-block {
  margin-top: 16px;
}

.sidebar-title {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--v2-text-primary);
}

.sidebar-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sidebar-item {
  width: 100%;
  text-align: left;
  padding: 12px;
  border-radius: var(--v2-radius-sm);
  border: 1px solid var(--v2-border-light);
  background: var(--v2-bg);
  cursor: pointer;
  transition: border-color .2s ease, transform .2s ease;
}

.sidebar-item:hover,
.sidebar-item.active {
  border-color: var(--v2-primary);
  transform: translateY(-1px);
}

.sidebar-item-title {
  color: var(--v2-text-primary);
  font-size: 13px;
  font-weight: 600;
  line-height: 1.5;
}

.sidebar-item-meta {
  margin-top: 6px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  font-size: 12px;
  color: var(--v2-text-muted);
}

.main-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.main-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--v2-text-primary);
}

.main-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: var(--v2-text-muted);
  line-height: 1.6;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.kpi-card {
  padding: 14px;
  border-radius: var(--v2-radius-sm);
  background: var(--v2-bg);
  border: 1px solid var(--v2-border-light);
}

.kpi-label {
  color: var(--v2-text-muted);
  font-size: 12px;
}

.kpi-value {
  margin-top: 6px;
  color: var(--v2-text-primary);
  font-size: 22px;
  font-weight: 700;
  line-height: 1.2;
}

.kpi-unit {
  margin-left: 4px;
  font-size: 13px;
  font-weight: 500;
  color: var(--v2-text-muted);
}

.kpi-highlight {
  margin-top: 6px;
  color: var(--v2-text-muted);
  font-size: 12px;
}

.preview-box {
  margin-top: 18px;
}

.state-box {
  padding: 24px;
  border-radius: var(--v2-radius);
  background: #f8fbff;
  border: 1px solid #dbeafe;
}

.state-box-error {
  background: #fff7f7;
  border-color: #fecaca;
}

.state-meta {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  color: var(--v2-text-muted);
  font-size: 13px;
}

.markdown-box {
  margin-top: 12px;
  padding: 16px;
  border-radius: var(--v2-radius-sm);
  background: var(--v2-bg);
  border: 1px solid var(--v2-border-light);
  white-space: pre-wrap;
  line-height: 1.75;
  color: var(--v2-text-secondary);
}

.markdown-edit-modal {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.markdown-edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 1200px) {
  .kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .report-toolbar,
  .main-head {
    flex-direction: column;
  }

  .report-shell {
    grid-template-columns: 1fr;
  }

  .kpi-grid {
    grid-template-columns: 1fr;
  }
}
</style>
