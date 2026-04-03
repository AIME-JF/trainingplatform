<template>
  <div class="schedule-file-parse-page">
    <div class="page-header">
      <div>
        <h2>智能解析课表创建</h2>
        <p class="page-sub">上传课表 Excel 文件，AI 智能解析班级信息与课程安排，快速创建培训班</p>
      </div>
      <a-button @click="$router.push({ name: 'TrainingList' })">返回列表</a-button>
    </div>

    <a-row :gutter="16">
      <!-- 左侧：任务列表 -->
      <a-col :span="7">
        <a-card :bordered="false" title="任务列表" size="small">
          <template #extra>
            <a-button type="link" size="small" @click="showUpload = true">
              <PlusOutlined /> 新任务
            </a-button>
          </template>
          <a-spin :spinning="listLoading">
            <div v-if="taskList.length === 0" style="text-align:center;padding:40px 0;color:#999">暂无任务</div>
            <div
              v-for="t in taskList" :key="t.id"
              class="task-item" :class="{ active: activeTaskId === t.id }"
              @click="loadDetail(t.id)"
            >
              <div class="task-item-name">{{ t.task_name }}</div>
              <div class="task-item-meta">
                <a-tag :color="statusColor(t.status)" size="small">{{ statusLabel(t.status, t.task_stage) }}</a-tag>
                <span class="task-item-time">{{ formatTime(t.created_at) }}</span>
              </div>
            </div>
          </a-spin>
        </a-card>
      </a-col>

      <!-- 右侧：详情 -->
      <a-col :span="17">
        <!-- 上传区 -->
        <a-card v-if="showUpload || !activeTaskId" :bordered="false" title="上传课表文件">
          <a-upload-dragger
            :before-upload="handleBeforeUpload"
            :file-list="fileList"
            accept=".xlsx,.xls"
            :max-count="1"
            @remove="fileList = []"
          >
            <p class="ant-upload-drag-icon"><InboxOutlined /></p>
            <p class="ant-upload-text">点击或拖拽上传课表 Excel 文件</p>
            <p class="ant-upload-hint">支持 .xlsx / .xls 格式</p>
          </a-upload-dragger>
          <div style="margin-top:16px;text-align:right">
            <a-button type="primary" :loading="uploading" :disabled="fileList.length === 0" @click="handleUpload">
              开始智能解析
            </a-button>
          </div>
        </a-card>

        <!-- 详情区 -->
        <template v-if="activeTaskId && detail">
          <a-card :bordered="false" style="margin-bottom:16px">
            <AiTaskTimeline
              :status="detail.status"
              :stage="detail.task_stage"
              mode="schedule-file-parse"
              :active-step="currentStep"
              :created-at="detail.created_at"
              :completed-at="detail.completed_at"
              :confirmed-at="detail.confirmed_at"
            />
          </a-card>

          <!-- 步骤 0: 解析中 -->
          <a-card v-if="currentStep === 0" :bordered="false">
            <a-result v-if="detail.status === 'processing' || detail.status === 'pending'" status="info" title="智能解析中" sub-title="正在使用 AI 分析课表文件，请稍候...">
              <template #extra><a-button @click="loadDetail(activeTaskId)">刷新状态</a-button></template>
            </a-result>
            <a-result v-else-if="detail.status === 'failed'" status="error" :title="'解析失败'" :sub-title="detail.error_message || detail.parse_error || '未知错误'">
              <template #extra><a-button type="primary" @click="showUpload = true">重新上传</a-button></template>
            </a-result>
          </a-card>

          <!-- 步骤 1: 确认班级信息 -->
          <a-card v-if="currentStep === 1" :bordered="false" title="确认班级信息">
            <a-alert v-if="!classInfoComplete" message="以下信息从文件中智能提取，请补全必填项后进入下一步" type="warning" show-icon style="margin-bottom:16px" />
            <a-form :label-col="{ span: 5 }" :wrapper-col="{ span: 16 }">
              <a-form-item label="班级名称" required>
                <a-input v-model:value="editClassInfo.name" placeholder="请输入班级名称" />
              </a-form-item>
              <a-form-item label="开始日期" required>
                <a-input v-model:value="editClassInfo.start_date" placeholder="YYYY-MM-DD" />
              </a-form-item>
              <a-form-item label="结束日期" required>
                <a-input v-model:value="editClassInfo.end_date" placeholder="YYYY-MM-DD" />
              </a-form-item>
              <a-form-item label="班级容量">
                <a-input-number v-model:value="editClassInfo.capacity" :min="1" :max="9999" style="width:200px" />
              </a-form-item>
              <a-form-item label="培训地点" required>
                <template v-if="editClassInfo.location_source === 'base' && editClassInfo.training_base_id">
                  <a-tag color="blue">已匹配培训基地</a-tag>
                  <span style="margin-left:8px">{{ editClassInfo.location }}</span>
                  <a-button type="link" size="small" @click="editClassInfo.location_source = 'manual'; editClassInfo.training_base_id = null">切换手动输入</a-button>
                </template>
                <a-input v-else v-model:value="editClassInfo.location" placeholder="请输入培训地点" />
              </a-form-item>
              <a-form-item label="班主任">
                <div v-for="(ht, idx) in editClassInfo.headteachers" :key="idx" style="margin-bottom:8px">
                  <a-space>
                    <a-input v-model:value="ht.name" placeholder="姓名" style="width:120px" />
                    <a-input v-model:value="ht.role_label" placeholder="称呼" style="width:120px" />
                    <a-tag v-if="ht.user_id" color="green">已匹配</a-tag>
                    <a-tag v-else-if="ht.auto_create && ht.name" color="orange">将自动创建</a-tag>
                    <a-button type="link" danger size="small" @click="editClassInfo.headteachers.splice(idx, 1)">删除</a-button>
                  </a-space>
                </div>
                <a-button type="dashed" size="small" @click="editClassInfo.headteachers.push({ name: '', role_label: '班主任', user_id: null, auto_create: true })">
                  <PlusOutlined /> 添加班主任
                </a-button>
              </a-form-item>
            </a-form>
            <div style="text-align:right;margin-top:16px">
              <a-button type="primary" :disabled="!classInfoComplete" @click="submitClassInfo">下一步：确认课表</a-button>
            </div>
          </a-card>

          <!-- 步骤 2: 确认课表 -->
          <a-card v-if="currentStep === 2" :bordered="false" title="确认课表">
            <a-alert v-if="editCourses.length === 0" message="未解析到课程信息" type="warning" show-icon style="margin-bottom:16px" />
            <a-collapse v-model:activeKey="courseCollapseKeys">
              <a-collapse-panel v-for="(course, ci) in editCourses" :key="ci" :header="course.name || '未命名课程'">
                <template #extra>
                  <a-tag :color="course.type === 'practice' ? 'green' : 'blue'">{{ course.type === 'practice' ? '实操' : '理论' }}</a-tag>
                  <span style="margin-left:8px;color:#999">{{ course.sessions?.length || 0 }} 个课次</span>
                </template>
                <a-form :label-col="{ span: 5 }" :wrapper-col="{ span: 16 }" size="small">
                  <a-form-item label="课程名称">
                    <a-input v-model:value="course.name" />
                  </a-form-item>
                  <a-form-item label="课程类型">
                    <a-radio-group v-model:value="course.type">
                      <a-radio value="theory">理论</a-radio>
                      <a-radio value="practice">实操</a-radio>
                    </a-radio-group>
                  </a-form-item>
                  <a-form-item label="主讲教官">
                    <a-space>
                      <a-input v-model:value="course.primary_instructor.name" placeholder="教官姓名" style="width:160px" />
                      <a-tag v-if="course.primary_instructor.user_id" color="green">已匹配</a-tag>
                      <a-tag v-else-if="course.primary_instructor.auto_create && course.primary_instructor.name" color="orange">将自动创建</a-tag>
                      <a-tag v-else-if="!course.primary_instructor.name" color="default">留空</a-tag>
                    </a-space>
                  </a-form-item>
                  <a-form-item label="辅助教官">
                    <div v-for="(ai, aidx) in course.assistant_instructors" :key="aidx" style="margin-bottom:4px">
                      <a-space>
                        <a-input v-model:value="ai.name" placeholder="姓名" style="width:140px" />
                        <a-tag v-if="ai.user_id" color="green">已匹配</a-tag>
                        <a-tag v-else-if="ai.auto_create && ai.name" color="orange">将自动创建</a-tag>
                        <a-button type="link" danger size="small" @click="course.assistant_instructors.splice(aidx, 1)">删除</a-button>
                      </a-space>
                    </div>
                    <a-button type="dashed" size="small" @click="course.assistant_instructors.push({ name: '', user_id: null, auto_create: true })">
                      <PlusOutlined /> 添加辅助教官
                    </a-button>
                  </a-form-item>
                  <a-form-item label="课次">
                    <a-table :data-source="course.sessions" :columns="sessionColumns" size="small" :pagination="false" row-key="(_, i) => i">
                      <template #bodyCell="{ column, record, index }">
                        <template v-if="column.key === 'date'">
                          <a-input v-model:value="record.date" size="small" style="width:120px" />
                        </template>
                        <template v-if="column.key === 'time_start'">
                          <a-input v-model:value="record.time_start" size="small" style="width:80px" />
                        </template>
                        <template v-if="column.key === 'time_end'">
                          <a-input v-model:value="record.time_end" size="small" style="width:80px" />
                        </template>
                        <template v-if="column.key === 'location'">
                          <a-input v-model:value="record.location" size="small" style="width:120px" placeholder="可选" />
                        </template>
                        <template v-if="column.key === 'action'">
                          <a-button type="link" danger size="small" @click="course.sessions.splice(index, 1)">删除</a-button>
                        </template>
                      </template>
                    </a-table>
                    <a-button type="dashed" size="small" style="margin-top:8px" @click="course.sessions.push({ date: '', time_start: '', time_end: '', location: '' })">
                      <PlusOutlined /> 添加课次
                    </a-button>
                  </a-form-item>
                </a-form>
                <div style="text-align:right">
                  <a-popconfirm title="确定删除该课程？" @confirm="editCourses.splice(ci, 1)">
                    <a-button danger size="small">删除课程</a-button>
                  </a-popconfirm>
                </div>
              </a-collapse-panel>
            </a-collapse>
            <a-button type="dashed" block style="margin-top:12px" @click="addEmptyCourse"><PlusOutlined /> 添加课程</a-button>
            <div style="text-align:right;margin-top:16px">
              <a-space>
                <a-button @click="goStep(1)">上一步</a-button>
                <a-button type="primary" :disabled="editCourses.length === 0" @click="submitCourses">下一步：完善信息</a-button>
              </a-space>
            </div>
          </a-card>

          <!-- 步骤 3: 完善班级信息 -->
          <a-card v-if="currentStep === 3" :bordered="false" title="完善班级信息">
            <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 14 }">
              <a-form-item label="培训类型">
                <a-select v-model:value="editConfig.type">
                  <a-select-option value="basic">基础培训</a-select-option>
                  <a-select-option value="special">专项培训</a-select-option>
                  <a-select-option value="promotion">晋升培训</a-select-option>
                  <a-select-option value="online">线上培训</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="班级编号">
                <a-input v-model:value="editConfig.class_code" placeholder="可选" />
              </a-form-item>
              <a-form-item label="报名方式">
                <a-radio-group v-model:value="editConfig.enrollment_requires_approval">
                  <a-radio :value="true">申请审核</a-radio>
                  <a-radio :value="false">直接通过</a-radio>
                </a-radio-group>
              </a-form-item>
              <a-form-item label="培训简介">
                <a-textarea v-model:value="editConfig.description" :rows="3" placeholder="可选" />
              </a-form-item>
            </a-form>
            <div style="text-align:right;margin-top:16px">
              <a-space>
                <a-button @click="goStep(2)">上一步</a-button>
                <a-button type="primary" @click="submitConfig">下一步：预览</a-button>
              </a-space>
            </div>
          </a-card>

          <!-- 步骤 4: 预览 -->
          <a-card v-if="currentStep === 4" :bordered="false" title="预览">
            <a-descriptions bordered size="small" :column="2" style="margin-bottom:16px">
              <a-descriptions-item label="班级名称">{{ previewClassInfo?.name || '-' }}</a-descriptions-item>
              <a-descriptions-item label="培训类型">{{ typeLabel(previewConfig?.type) }}</a-descriptions-item>
              <a-descriptions-item label="开始日期">{{ previewClassInfo?.start_date || '-' }}</a-descriptions-item>
              <a-descriptions-item label="结束日期">{{ previewClassInfo?.end_date || '-' }}</a-descriptions-item>
              <a-descriptions-item label="容量">{{ previewClassInfo?.capacity || '-' }}</a-descriptions-item>
              <a-descriptions-item label="地点">{{ previewClassInfo?.location || '-' }}</a-descriptions-item>
              <a-descriptions-item label="班主任" :span="2">
                <a-tag v-for="ht in (previewClassInfo?.headteachers || [])" :key="ht.name" :color="ht.user_id ? 'green' : 'orange'">
                  {{ ht.name }}（{{ ht.role_label }}）{{ ht.user_id ? '' : ' · 自动创建' }}
                </a-tag>
                <span v-if="!(previewClassInfo?.headteachers?.length)">-</span>
              </a-descriptions-item>
            </a-descriptions>

            <h4 style="margin:16px 0 8px">课程安排（共 {{ previewCourses?.length || 0 }} 门）</h4>
            <a-table :data-source="previewCourses" :columns="previewCourseColumns" size="small" :pagination="false" row-key="name">
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'type'">
                  <a-tag :color="record.type === 'practice' ? 'green' : 'blue'">{{ record.type === 'practice' ? '实操' : '理论' }}</a-tag>
                </template>
                <template v-if="column.key === 'instructor'">
                  {{ record.primary_instructor?.name || '-' }}
                </template>
                <template v-if="column.key === 'sessions'">
                  {{ record.sessions?.length || 0 }} 个课次
                </template>
              </template>
            </a-table>

            <div style="text-align:right;margin-top:16px">
              <a-space>
                <a-button @click="goStep(3)">上一步</a-button>
                <a-popconfirm title="确认创建培训班？自动创建的教官账号默认密码为 Police@123456" @confirm="handleConfirm">
                  <a-button type="primary" :loading="confirming">确认创建培训班</a-button>
                </a-popconfirm>
              </a-space>
            </div>
          </a-card>

          <!-- 步骤 5: 完成 -->
          <a-card v-if="currentStep === 5" :bordered="false">
            <a-result status="success" title="培训班创建成功" sub-title="已根据解析结果自动创建培训班及课程安排">
              <template #extra>
                <a-space>
                  <a-button type="primary" @click="goTrainingDetail">查看培训班</a-button>
                  <a-button @click="showUpload = true">继续解析</a-button>
                </a-space>
              </template>
            </a-result>
          </a-card>
        </template>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined, InboxOutlined } from '@ant-design/icons-vue'
import AiTaskTimeline from '../exam/components/AiTaskTimeline.vue'
import {
  getScheduleFileParseTaskList,
  createScheduleFileParseTask,
  getScheduleFileParseTaskDetail,
  updateScheduleFileParseTask,
  confirmScheduleFileParseTask,
} from '@/api/ai'

const router = useRouter()

// 列表
const taskList = ref([])
const listLoading = ref(false)
const activeTaskId = ref(null)
const detail = ref(null)
const showUpload = ref(false)

// 上传
const fileList = ref([])
const uploading = ref(false)

// 编辑状态
const editClassInfo = reactive({
  name: '', start_date: '', end_date: '', capacity: null, location: '',
  location_source: 'manual', training_base_id: null,
  headteachers: [],
})
const editCourses = ref([])
const editConfig = reactive({
  type: 'basic', department_id: null, police_type_id: null,
  visibility_scope: 'all', visibility_department_ids: null,
  description: '', enrollment_requires_approval: true,
  admission_exam_id: null, class_code: '',
})
const courseCollapseKeys = ref([])
const confirming = ref(false)
const saving = ref(false)

const sessionColumns = [
  { title: '日期', key: 'date', width: 140 },
  { title: '开始', key: 'time_start', width: 100 },
  { title: '结束', key: 'time_end', width: 100 },
  { title: '地点', key: 'location', width: 140 },
  { title: '', key: 'action', width: 60 },
]

const previewCourseColumns = [
  { title: '课程名称', dataIndex: 'name', key: 'name' },
  { title: '类型', key: 'type', width: 80 },
  { title: '主讲教官', key: 'instructor', width: 120 },
  { title: '课次', key: 'sessions', width: 100 },
]

// 计算属性
const currentStep = computed(() => {
  if (!detail.value) return 0
  const { status, task_stage } = detail.value
  if (status === 'confirmed') return 5
  if (status === 'failed' || status === 'pending' || status === 'processing') return 0
  const stageMap = { class_info_confirmation: 1, course_confirmation: 2, training_config: 3, preview: 4 }
  return stageMap[task_stage] || 0
})

const classInfoComplete = computed(() => {
  return editClassInfo.name && editClassInfo.start_date && editClassInfo.end_date && editClassInfo.location
})

const previewClassInfo = computed(() => {
  const rp = detail.value
  return rp?.confirmed_class_info || rp?.class_info || null
})

const previewCourses = computed(() => {
  const rp = detail.value
  return rp?.confirmed_courses || rp?.courses || []
})

const previewConfig = computed(() => {
  return detail.value?.training_config || editConfig
})

// 方法
async function loadList() {
  listLoading.value = true
  try {
    const res = await getScheduleFileParseTaskList({ page: 1, size: -1 })
    taskList.value = res.data?.data?.items || []
  } finally {
    listLoading.value = false
  }
}

async function loadDetail(taskId) {
  activeTaskId.value = taskId
  showUpload.value = false
  try {
    const res = await getScheduleFileParseTaskDetail(taskId)
    detail.value = res.data?.data || null
    syncEditState()
  } catch {
    message.error('加载任务详情失败')
  }
}

function syncEditState() {
  if (!detail.value) return
  const d = detail.value
  const ci = d.confirmed_class_info || d.class_info || {}
  Object.assign(editClassInfo, {
    name: ci.name || '', start_date: ci.start_date || '', end_date: ci.end_date || '',
    capacity: ci.capacity || null, location: ci.location || '',
    location_source: ci.location_source || 'manual', training_base_id: ci.training_base_id || null,
    headteachers: (ci.headteachers || []).map(h => ({ ...h })),
  })
  editCourses.value = (d.confirmed_courses || d.courses || []).map(c => ({
    ...c,
    primary_instructor: { ...(c.primary_instructor || {}) },
    assistant_instructors: (c.assistant_instructors || []).map(a => ({ ...a })),
    sessions: (c.sessions || []).map(s => ({ ...s })),
  }))
  const cfg = d.training_config || {}
  Object.assign(editConfig, {
    type: cfg.type || 'basic', department_id: cfg.department_id || null,
    police_type_id: cfg.police_type_id || null,
    visibility_scope: cfg.visibility_scope || 'all',
    visibility_department_ids: cfg.visibility_department_ids || null,
    description: cfg.description || '',
    enrollment_requires_approval: cfg.enrollment_requires_approval !== false,
    admission_exam_id: cfg.admission_exam_id || null,
    class_code: cfg.class_code || '',
  })
  courseCollapseKeys.value = editCourses.value.map((_, i) => i)
}

function handleBeforeUpload(file) {
  fileList.value = [file]
  return false
}

async function handleUpload() {
  if (fileList.value.length === 0) return
  uploading.value = true
  try {
    const res = await createScheduleFileParseTask(fileList.value[0])
    const task = res.data?.data
    if (task) {
      message.success('任务创建成功，开始解析...')
      fileList.value = []
      showUpload.value = false
      await loadList()
      await loadDetail(task.id)
      // 轮询等待解析
      pollDetail(task.id)
    }
  } catch (e) {
    message.error(e.response?.data?.detail || '创建任务失败')
  } finally {
    uploading.value = false
  }
}

function pollDetail(taskId) {
  const timer = setInterval(async () => {
    try {
      const res = await getScheduleFileParseTaskDetail(taskId)
      const d = res.data?.data
      if (d && d.status !== 'pending' && d.status !== 'processing') {
        clearInterval(timer)
        detail.value = d
        syncEditState()
        await loadList()
      }
    } catch {
      clearInterval(timer)
    }
  }, 3000)
  // 60s 超时
  setTimeout(() => clearInterval(timer), 60000)
}

async function submitClassInfo() {
  saving.value = true
  try {
    await updateScheduleFileParseTask(activeTaskId.value, {
      confirmed_class_info: { ...editClassInfo },
      current_stage: 'course_confirmation',
    })
    await loadDetail(activeTaskId.value)
  } catch (e) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function submitCourses() {
  saving.value = true
  try {
    await updateScheduleFileParseTask(activeTaskId.value, {
      confirmed_courses: editCourses.value,
      current_stage: 'training_config',
    })
    await loadDetail(activeTaskId.value)
  } catch (e) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function submitConfig() {
  saving.value = true
  try {
    await updateScheduleFileParseTask(activeTaskId.value, {
      training_config: { ...editConfig },
      current_stage: 'preview',
    })
    await loadDetail(activeTaskId.value)
  } catch (e) {
    message.error(e.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function goStep(step) {
  const stageNames = ['parsing', 'class_info_confirmation', 'course_confirmation', 'training_config', 'preview']
  try {
    await updateScheduleFileParseTask(activeTaskId.value, { current_stage: stageNames[step] })
    await loadDetail(activeTaskId.value)
  } catch (e) {
    message.error('切换步骤失败')
  }
}

async function handleConfirm() {
  confirming.value = true
  try {
    await confirmScheduleFileParseTask(activeTaskId.value)
    message.success('培训班创建成功！')
    await loadDetail(activeTaskId.value)
    await loadList()
  } catch (e) {
    message.error(e.response?.data?.detail || '创建失败')
  } finally {
    confirming.value = false
  }
}

function goTrainingDetail() {
  const id = detail.value?.confirmed_training_id
  if (id) {
    router.push({ name: 'TrainingDetail', params: { id } })
  }
}

function addEmptyCourse() {
  editCourses.value.push({
    name: '', type: 'theory', location: '',
    primary_instructor: { name: '', user_id: null, auto_create: true },
    assistant_instructors: [],
    sessions: [],
  })
  courseCollapseKeys.value.push(editCourses.value.length - 1)
}

function statusColor(st) {
  return { pending: 'default', processing: 'processing', completed: 'blue', confirmed: 'green', failed: 'red' }[st] || 'default'
}

function statusLabel(st, stage) {
  if (st === 'confirmed') return '已创建'
  if (st === 'failed') return '失败'
  if (st === 'processing' || st === 'pending') return '解析中'
  const stageLabels = {
    class_info_confirmation: '待确认班级', course_confirmation: '待确认课表',
    training_config: '待完善信息', preview: '待确认',
  }
  return stageLabels[stage] || '已完成'
}

function typeLabel(t) {
  return { basic: '基础培训', special: '专项培训', promotion: '晋升培训', online: '线上培训' }[t] || t || '-'
}

function formatTime(v) {
  if (!v) return ''
  return String(v).replace('T', ' ').slice(0, 16)
}

onMounted(() => {
  loadList()
})
</script>

<style scoped>
.schedule-file-parse-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 4px;
  font-size: 20px;
}

.page-sub {
  color: #8c8c8c;
  margin: 0;
  font-size: 13px;
}

.task-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.task-item:hover {
  background: #f5f5f5;
}

.task-item.active {
  background: #e6f7ff;
  border-left: 3px solid #1890ff;
}

.task-item-name {
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.task-item-time {
  color: #999;
  font-size: 11px;
}
</style>
