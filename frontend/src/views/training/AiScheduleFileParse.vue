<template>
  <div class="schedule-file-parse-page">
    <div class="page-header">
      <div>
        <h2>智能解析课表创建</h2>
        <p class="page-sub">上传课表 Excel 文件，AI 智能解析班级信息与课程安排，快速创建培训班</p>
      </div>
      <a-space>
        <a-button type="primary" @click="showUpload = true"><PlusOutlined /> 新任务</a-button>
        <a-button @click="$router.push({ name: 'TrainingList' })">返回列表</a-button>
      </a-space>
    </div>

    <!-- 上传区（内联卡片） -->
    <a-card v-if="showUpload" :bordered="false" title="上传课表文件" style="margin-bottom:16px">
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
        <a-space>
          <a-button @click="showUpload = false">取消</a-button>
          <a-button type="primary" :loading="uploading" :disabled="fileList.length === 0" @click="handleUpload">
            开始智能解析
          </a-button>
        </a-space>
      </div>
    </a-card>

    <!-- 任务列表（横向填满） -->
    <a-card :bordered="false">
      <template #title>
        <div class="list-card-title">
          <span>任务列表</span>
          <a-button @click="loadList" size="small">刷新</a-button>
        </div>
      </template>
      <a-spin :spinning="listLoading">
        <a-empty v-if="taskList.length === 0 && !listLoading" description="暂无任务，请点击上方「新任务」按钮上传课表文件" />
        <div v-else class="task-list">
          <div v-for="t in taskList" :key="t.id" class="task-list-row" @click="openDetail(t.id)">
            <div class="task-row-content">
              <div class="task-row-name">{{ t.taskName }}</div>
              <div class="task-row-desc">{{ t.summaryText || '-' }}</div>
            </div>
            <div class="task-row-right">
              <a-tag :color="statusColor(t.status)" size="small">{{ statusLabel(t.status, t.taskStage) }}</a-tag>
              <span class="task-row-time">{{ formatTime(t.createdAt) }}</span>
            </div>
            <div class="task-row-actions">
              <a-button type="link" size="small">详情</a-button>
            </div>
          </div>
        </div>
      </a-spin>
    </a-card>

    <!-- 详情弹窗 -->
    <a-modal
      v-model:open="detailModalVisible"
      :title="detail?.taskName || '任务详情'"
      width="100%"
      wrap-class-name="fullscreen-modal"
      :footer="null"
      :destroy-on-close="false"
    >
      <template v-if="detail">
        <div style="margin-bottom:16px">
          <AiTaskTimeline
            :status="detail.status"
            :stage="detail.taskStage"
            mode="schedule-file-parse"
            :active-step="currentStep"
            :created-at="detail.createdAt"
            :completed-at="detail.completedAt"
            :confirmed-at="detail.confirmedAt"
          />
        </div>

        <!-- 步骤 0: 解析中 -->
        <div v-if="currentStep === 0">
          <a-result v-if="detail.status === 'processing' || detail.status === 'pending'" status="info" title="智能解析中" sub-title="正在使用 AI 分析课表文件，请稍候...">
            <template #extra><a-button @click="loadDetail(activeTaskId)">刷新状态</a-button></template>
          </a-result>
          <a-result v-else-if="detail.status === 'failed'" status="error" title="解析失败" :sub-title="detail.errorMessage || detail.parseError || '未知错误'">
            <template #extra><a-button type="primary" @click="detailModalVisible = false; showUpload = true">重新上传</a-button></template>
          </a-result>
        </div>

        <!-- 步骤 1: 确认班级信息 -->
        <div v-if="currentStep === 1">
          <a-alert v-if="!classInfoComplete" message="以下信息从文件中智能提取，请补全必填项后进入下一步" type="warning" show-icon style="margin-bottom:16px" />
          <a-form :label-col="{ span: 5 }" :wrapper-col="{ span: 16 }">
            <a-form-item label="班级名称" required>
              <a-input v-model:value="editClassInfo.name" placeholder="请输入班级名称" />
            </a-form-item>
            <a-form-item label="开始日期" required>
              <a-input v-model:value="editClassInfo.startDate" placeholder="YYYY-MM-DD" />
            </a-form-item>
            <a-form-item label="结束日期" required>
              <a-input v-model:value="editClassInfo.endDate" placeholder="YYYY-MM-DD" />
            </a-form-item>
            <a-form-item label="班级容量">
              <a-input-number v-model:value="editClassInfo.capacity" :min="1" :max="9999" style="width:200px" />
            </a-form-item>
            <a-form-item label="地点来源">
              <a-space>
                <a-checkbox :checked="locationSourceMode === 'base'" @change="() => setLocationSourceMode('base')">培训基地</a-checkbox>
                <a-checkbox :checked="locationSourceMode === 'manual'" @change="() => setLocationSourceMode('manual')">手动输入</a-checkbox>
              </a-space>
            </a-form-item>
            <a-form-item v-if="locationSourceMode === 'base'" label="培训基地" required>
              <a-select
                v-model:value="editClassInfo.trainingBaseId"
                allow-clear show-search option-filter-prop="label"
                placeholder="选择培训基地"
                @change="onTrainingBaseChange"
              >
                <a-select-option v-for="item in trainingBaseOptions" :key="item.id" :value="item.id" :label="`${item.name} ${item.location}`">
                  {{ item.name }} / {{ item.location }}
                </a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item :label="locationSourceMode === 'base' ? '培训地点（自动带出）' : '培训地点'" required>
              <a-input v-model:value="editClassInfo.location" :disabled="locationSourceMode === 'base'" placeholder="请输入培训地点" />
            </a-form-item>
            <a-form-item label="带班队长">
              <div v-for="(ht, idx) in editClassInfo.headteachers" :key="idx" style="margin-bottom:8px">
                <a-space>
                  <a-input :value="ht.name" disabled placeholder="未选择" style="width:160px" />
                  <a-tag v-if="ht.userId" color="green">已关联</a-tag>
                  <a-tag v-else-if="ht.autoCreate && ht.name" color="orange">将自动创建</a-tag>
                  <a-button type="link" size="small" @click="openUserPicker('headteacher', idx)">修改</a-button>
                  <a-button type="link" danger size="small" @click="editClassInfo.headteachers.splice(idx, 1)">删除</a-button>
                </a-space>
              </div>
              <a-button type="dashed" size="small" @click="openUserPicker('headteacher', -1)">
                <PlusOutlined /> 添加带班队长
              </a-button>
            </a-form-item>
          </a-form>
          <div style="text-align:right;margin-top:16px">
            <a-button type="primary" :disabled="!classInfoComplete" @click="submitClassInfo">下一步：确认课表</a-button>
          </div>
        </div>

        <!-- 步骤 2: 确认课表 -->
        <div v-if="currentStep === 2">
          <a-alert v-if="editCourses.length === 0" message="未解析到课程信息" type="warning" show-icon style="margin-bottom:16px" />

          <!-- 日历预览 -->
          <div v-if="calendarDays(editCourses).length" class="schedule-calendar" style="margin-bottom:16px">
            <div class="calendar-grid">
              <div v-for="day in calendarDays(editCourses)" :key="day.date" class="calendar-day">
                <div class="calendar-day-header">
                  <div class="calendar-day-name">{{ day.weekdayName }}</div>
                  <div class="calendar-day-date">{{ day.label }}</div>
                </div>
                <div class="calendar-day-body">
                  <div
                    v-for="(item, si) in day.sessions" :key="si"
                    class="calendar-item"
                    :style="{ borderLeftColor: courseColor(item.courseIndex) }"
                  >
                    <div class="calendar-item-name">{{ item.courseName }}</div>
                    <div class="calendar-item-time">{{ item.timeStart }}~{{ item.timeEnd }}</div>
                  </div>
                  <div v-if="!day.sessions.length" class="calendar-empty">无课程</div>
                </div>
              </div>
            </div>
          </div>

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
                    <a-input :value="course.primaryInstructor.name" disabled placeholder="未选择" style="width:160px" />
                    <a-tag v-if="course.primaryInstructor.userId" color="green">已关联</a-tag>
                    <a-tag v-else-if="course.primaryInstructor.autoCreate && course.primaryInstructor.name" color="orange">将自动创建</a-tag>
                    <a-tag v-else-if="!course.primaryInstructor.name" color="default">留空</a-tag>
                    <a-button type="link" size="small" @click="openUserPicker('primaryInstructor', ci)">修改</a-button>
                  </a-space>
                </a-form-item>
                <a-form-item label="辅助教官">
                  <div v-for="(ai, aidx) in course.assistantInstructors" :key="aidx" style="margin-bottom:4px">
                    <a-space>
                      <a-input :value="ai.name" disabled placeholder="未选择" style="width:140px" />
                      <a-tag v-if="ai.userId" color="green">已关联</a-tag>
                      <a-tag v-else-if="ai.autoCreate && ai.name" color="orange">将自动创建</a-tag>
                      <a-button type="link" size="small" @click="openUserPicker('assistantInstructor', ci, aidx)">修改</a-button>
                      <a-button type="link" danger size="small" @click="course.assistantInstructors.splice(aidx, 1)">删除</a-button>
                    </a-space>
                  </div>
                  <a-button type="dashed" size="small" @click="openUserPicker('assistantInstructor', ci, -1)">
                    <PlusOutlined /> 添加辅助教官
                  </a-button>
                </a-form-item>
                <a-form-item label="课次">
                  <table class="session-edit-table">
                    <thead>
                      <tr>
                        <th style="width:120px">日期</th>
                        <th style="width:90px">开始</th>
                        <th style="width:90px">结束</th>
                        <th style="width:120px">地点</th>
                        <th style="width:50px"></th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(sess, si) in course.sessions" :key="si">
                        <td @click="startEdit(ci, si, 'date')">
                          <a-date-picker
                            v-if="isEditing(ci, si, 'date')"
                            v-model:value="sess.date"
                            size="small" style="width:112px" value-format="YYYY-MM-DD"
                            :open="true" @blur="stopEdit" @change="stopEdit"
                          />
                          <span v-else class="cell-display">{{ sess.date || '点击设置' }}</span>
                        </td>
                        <td @click="startEdit(ci, si, 'timeStart')">
                          <a-time-picker
                            v-if="isEditing(ci, si, 'timeStart')"
                            v-model:value="sess.timeStart"
                            size="small" style="width:84px" format="HH:mm" value-format="HH:mm" :minute-step="5"
                            :open="true" @blur="stopEdit" @change="stopEdit"
                          />
                          <span v-else class="cell-display">{{ sess.timeStart || '点击设置' }}</span>
                        </td>
                        <td @click="startEdit(ci, si, 'timeEnd')">
                          <a-time-picker
                            v-if="isEditing(ci, si, 'timeEnd')"
                            v-model:value="sess.timeEnd"
                            size="small" style="width:84px" format="HH:mm" value-format="HH:mm" :minute-step="5"
                            :open="true" @blur="stopEdit" @change="stopEdit"
                          />
                          <span v-else class="cell-display">{{ sess.timeEnd || '点击设置' }}</span>
                        </td>
                        <td>
                          <a-input v-model:value="sess.location" size="small" placeholder="可选" />
                        </td>
                        <td style="text-align:center">
                          <a-button type="link" danger size="small" @click="course.sessions.splice(si, 1)">删除</a-button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                  <a-button type="dashed" size="small" style="margin-top:8px" @click="course.sessions.push({ date: '', timeStart: '', timeEnd: '', location: '' })">
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
              <a-button type="primary" :disabled="editCourses.length === 0" @click="submitCourses">下一步：预览</a-button>
            </a-space>
          </div>
        </div>

        <!-- 步骤 3: 预览 -->
        <div v-if="currentStep === 3">
          <a-descriptions bordered size="small" :column="2" style="margin-bottom:16px">
            <a-descriptions-item label="班级名称">{{ previewClassInfo?.name || '-' }}</a-descriptions-item>
            <a-descriptions-item label="培训类型">{{ typeLabel(previewConfig?.type) }}</a-descriptions-item>
            <a-descriptions-item label="开始日期">{{ previewClassInfo?.startDate || '-' }}</a-descriptions-item>
            <a-descriptions-item label="结束日期">{{ previewClassInfo?.endDate || '-' }}</a-descriptions-item>
            <a-descriptions-item label="容量">{{ previewClassInfo?.capacity || '-' }}</a-descriptions-item>
            <a-descriptions-item label="地点">{{ previewClassInfo?.location || '-' }}</a-descriptions-item>
            <a-descriptions-item label="带班队长" :span="2">
              <a-tag v-for="ht in (previewClassInfo?.headteachers || [])" :key="ht.name" :color="ht.userId ? 'green' : 'orange'">
                {{ ht.name }}{{ ht.userId ? '' : ' · 自动创建' }}
              </a-tag>
              <span v-if="!(previewClassInfo?.headteachers?.length)">-</span>
            </a-descriptions-item>
          </a-descriptions>

          <!-- 日历预览 -->
          <div v-if="calendarDays(previewCourses).length" class="schedule-calendar" style="margin-bottom:16px">
            <h4 style="margin:0 0 8px">课表日历</h4>
            <div class="calendar-grid">
              <div v-for="day in calendarDays(previewCourses)" :key="day.date" class="calendar-day">
                <div class="calendar-day-header">
                  <div class="calendar-day-name">{{ day.weekdayName }}</div>
                  <div class="calendar-day-date">{{ day.label }}</div>
                </div>
                <div class="calendar-day-body">
                  <div
                    v-for="(item, si) in day.sessions" :key="si"
                    class="calendar-item"
                    :style="{ borderLeftColor: courseColor(item.courseIndex) }"
                  >
                    <div class="calendar-item-name">{{ item.courseName }}</div>
                    <div class="calendar-item-time">{{ item.timeStart }}~{{ item.timeEnd }}</div>
                  </div>
                  <div v-if="!day.sessions.length" class="calendar-empty">无课程</div>
                </div>
              </div>
            </div>
          </div>

          <h4 style="margin:16px 0 8px">课程安排</h4>
          <table class="schedule-excel-table">
            <thead>
              <tr>
                <th style="width:100px">日期</th>
                <th style="width:110px">时间</th>
                <th>课程安排</th>
                <th style="width:150px">授课（主持）人</th>
              </tr>
            </thead>
            <tbody>
              <template v-for="day in scheduleTableRows(previewCourses)" :key="day.date">
                <tr v-for="(row, ri) in day.rows" :key="day.date + '-' + ri">
                  <td v-if="ri === 0" :rowspan="day.rows.length" class="schedule-date-cell">
                    <div class="schedule-date-main">{{ day.dateLabel }}</div>
                    <div class="schedule-date-weekday">（{{ day.weekdayName }}）</div>
                  </td>
                  <td class="schedule-time-cell">{{ row.timeRange }}</td>
                  <td class="schedule-course-cell">{{ row.courseName }}</td>
                  <td class="schedule-instructor-cell">{{ row.instructor || '-' }}</td>
                </tr>
              </template>
            </tbody>
          </table>

          <div style="text-align:right;margin-top:16px">
            <a-space>
              <a-button @click="goStep(2)">上一步</a-button>
              <a-button type="primary" @click="goStep(4)">下一步：完善信息</a-button>
            </a-space>
          </div>
        </div>

        <!-- 步骤 4: 完善班级信息 -->
        <div v-if="currentStep === 4">
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
              <a-input v-model:value="editConfig.classCode" placeholder="可选" />
            </a-form-item>
            <a-form-item label="准入考试">
              <a-radio-group v-model:value="needAdmissionExam" @change="() => { if (!needAdmissionExam) editConfig.admissionExamId = null }">
                <a-radio :value="false">不需要</a-radio>
                <a-radio :value="true">需要</a-radio>
              </a-radio-group>
            </a-form-item>
            <a-form-item v-if="needAdmissionExam" label="选择考试">
              <a-select
                v-model:value="editConfig.admissionExamId"
                allow-clear show-search option-filter-prop="label"
                placeholder="选择准入考试"
                :loading="admissionExamLoading"
                @focus="loadAdmissionExams"
              >
                <a-select-option v-for="e in admissionExamOptions" :key="e.id" :value="e.id" :label="e.title">
                  {{ e.title }}
                </a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="报名方式">
              <a-radio-group v-model:value="editConfig.enrollmentRequiresApproval">
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
              <a-button @click="goStep(3)">上一步</a-button>
              <a-popconfirm title="确认创建培训班？自动创建的教官账号默认密码为 Police@123456" @confirm="handleConfirm">
                <a-button type="primary" :loading="confirming">确认创建培训班</a-button>
              </a-popconfirm>
            </a-space>
          </div>
        </div>

        <!-- 步骤 5: 完成 -->
        <div v-if="currentStep === 5">
          <a-result status="success" title="培训班创建成功" sub-title="已根据解析结果自动创建培训班及课程安排">
            <template #extra>
              <a-space>
                <a-button type="primary" @click="goTrainingDetail">查看培训班</a-button>
                <a-button @click="detailModalVisible = false; showUpload = true">继续解析</a-button>
              </a-space>
            </template>
          </a-result>
        </div>
      </template>
    </a-modal>

    <!-- 用户选择弹窗 -->
    <UserPickerModal
      v-model:open="userPickerVisible"
      :title="userPickerTitle"
      :current-name="userPickerCurrentName"
      @select="handleUserPickerSelect"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { PlusOutlined, InboxOutlined } from '@ant-design/icons-vue'
import AiTaskTimeline from '../exam/components/AiTaskTimeline.vue'
import UserPickerModal from './components/UserPickerModal.vue'
import {
  getScheduleFileParseTaskList,
  createScheduleFileParseTask,
  getScheduleFileParseTaskDetail,
  updateScheduleFileParseTask,
  confirmScheduleFileParseTask,
} from '@/api/ai'
import { getTrainingBases } from '@/api/training'
import { getAdmissionExams } from '@/api/exam'

const router = useRouter()

// 列表
const taskList = ref([])
const listLoading = ref(false)
const activeTaskId = ref(null)
const detail = ref(null)
const showUpload = ref(false)
const detailModalVisible = ref(false)

// 上传
const fileList = ref([])
const uploading = ref(false)

// 培训基地选项
const trainingBaseOptions = ref([])
const locationSourceMode = ref('base')

// 编辑状态
const editClassInfo = reactive({
  name: '', startDate: '', endDate: '', capacity: null, location: '',
  locationSource: 'manual', trainingBaseId: null,
  headteachers: [],
})
const editCourses = ref([])
const editConfig = reactive({
  type: 'basic', departmentId: null, policeTypeId: null,
  visibilityScope: 'all', visibilityDepartmentIds: null,
  description: '', enrollmentRequiresApproval: true,
  admissionExamId: null, classCode: '',
})
const courseCollapseKeys = ref([])
const confirming = ref(false)
const saving = ref(false)
const needAdmissionExam = ref(false)
const admissionExamOptions = ref([])
const admissionExamLoading = ref(false)

// 用户选择弹窗状态
const userPickerVisible = ref(false)
const userPickerTitle = ref('选择用户')
const userPickerCurrentName = ref('')
const userPickerContext = reactive({ type: '', courseIndex: -1, assistantIndex: -1 })

// 点击编辑单元格：格式 `${courseIndex}-${sessionIndex}-${field}`
const editingCell = shallowRef(null)
function startEdit(ci, si, field) { editingCell.value = `${ci}-${si}-${field}` }
function stopEdit() { editingCell.value = null }
function isEditing(ci, si, field) { return editingCell.value === `${ci}-${si}-${field}` }

const previewCourseColumns = [
  { title: '课程名称', dataIndex: 'name', key: 'name' },
  { title: '类型', key: 'type', width: 80 },
  { title: '主讲教官', key: 'instructor', width: 120 },
  { title: '课次', key: 'sessions', width: 100 },
]

// 计算属性
const currentStep = computed(() => {
  if (!detail.value) return 0
  const { status, taskStage } = detail.value
  if (status === 'confirmed') return 5
  if (status === 'failed' || status === 'pending' || status === 'processing') return 0
  const stageMap = { class_info_confirmation: 1, course_confirmation: 2, preview: 3, training_config: 4 }
  return stageMap[taskStage] || 0
})

const classInfoComplete = computed(() => {
  const hasLocation = locationSourceMode.value === 'base'
    ? Boolean(editClassInfo.trainingBaseId && editClassInfo.location)
    : Boolean(editClassInfo.location)
  return editClassInfo.name && editClassInfo.startDate && editClassInfo.endDate && hasLocation
})

const previewClassInfo = computed(() => {
  return detail.value?.confirmedClassInfo || detail.value?.classInfo || null
})

const previewCourses = computed(() => {
  return detail.value?.confirmedCourses || detail.value?.courses || []
})

const previewConfig = computed(() => {
  return detail.value?.trainingConfig || editConfig
})

// 方法
async function loadList() {
  listLoading.value = true
  try {
    const res = await getScheduleFileParseTaskList({ page: 1, size: -1 })
    taskList.value = res?.items || []
  } finally {
    listLoading.value = false
  }
}

function openDetail(taskId) {
  loadDetail(taskId)
  detailModalVisible.value = true
}

async function loadDetail(taskId) {
  activeTaskId.value = taskId
  try {
    const res = await getScheduleFileParseTaskDetail(taskId)
    detail.value = res || null
    syncEditState()
  } catch {
    message.error('加载任务详情失败')
  }
}

function syncEditState() {
  if (!detail.value) return
  const d = detail.value
  const ci = d.confirmedClassInfo || d.classInfo || {}
  Object.assign(editClassInfo, {
    name: ci.name || '', startDate: ci.startDate || '', endDate: ci.endDate || '',
    capacity: ci.capacity || null, location: ci.location || '',
    locationSource: ci.locationSource || 'manual', trainingBaseId: ci.trainingBaseId || null,
    headteachers: (ci.headteachers || []).map(h => ({ ...h })),
  })
  locationSourceMode.value = editClassInfo.trainingBaseId ? 'base' : 'manual'
  editCourses.value = (d.confirmedCourses || d.courses || []).map(c => ({
    ...c,
    primaryInstructor: { ...(c.primaryInstructor || {}) },
    assistantInstructors: (c.assistantInstructors || []).map(a => ({ ...a })),
    sessions: (c.sessions || []).map(s => ({ ...s })),
  }))
  const cfg = d.trainingConfig || {}
  Object.assign(editConfig, {
    type: cfg.type || 'basic', departmentId: cfg.departmentId || null,
    policeTypeId: cfg.policeTypeId || null,
    visibilityScope: cfg.visibilityScope || 'all',
    visibilityDepartmentIds: cfg.visibilityDepartmentIds || null,
    description: cfg.description || '',
    enrollmentRequiresApproval: cfg.enrollmentRequiresApproval !== false,
    admissionExamId: cfg.admissionExamId || null,
    classCode: cfg.classCode || '',
  })
  needAdmissionExam.value = !!editConfig.admissionExamId
  courseCollapseKeys.value = editCourses.value.length > 0 ? [0] : []
}

async function fetchTrainingBaseOptions() {
  try {
    const result = await getTrainingBases({ size: -1 })
    trainingBaseOptions.value = result?.items || []
  } catch {
    trainingBaseOptions.value = []
  }
}

function setLocationSourceMode(mode) {
  locationSourceMode.value = mode
  if (mode === 'manual') {
    editClassInfo.trainingBaseId = null
    editClassInfo.locationSource = 'manual'
    return
  }
  editClassInfo.locationSource = 'base'
  if (editClassInfo.trainingBaseId) {
    onTrainingBaseChange(editClassInfo.trainingBaseId)
  } else {
    editClassInfo.location = ''
  }
}

function onTrainingBaseChange(baseId) {
  const base = trainingBaseOptions.value.find(item => item.id === baseId)
  editClassInfo.location = base ? (base.location || '') : ''
}

async function loadAdmissionExams() {
  if (admissionExamOptions.value.length) return
  admissionExamLoading.value = true
  try {
    const result = await getAdmissionExams({ size: 200, status: 'upcoming,active' })
    admissionExamOptions.value = (result?.items || []).filter(e => e?.id)
  } catch {
    admissionExamOptions.value = []
  } finally {
    admissionExamLoading.value = false
  }
}

function handleBeforeUpload(file) {
  fileList.value = [file]
  return false
}

async function handleUpload() {
  if (fileList.value.length === 0) return
  uploading.value = true
  try {
    const task = await createScheduleFileParseTask(fileList.value[0])
    if (task) {
      message.success('任务创建成功，开始解析...')
      fileList.value = []
      showUpload.value = false
      await loadList()
      openDetail(task.id)
      pollDetail(task.id)
    }
  } catch (e) {
    message.error(e.message || '创建任务失败')
  } finally {
    uploading.value = false
  }
}

function pollDetail(taskId) {
  const timer = setInterval(async () => {
    try {
      const d = await getScheduleFileParseTaskDetail(taskId)
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
  setTimeout(() => clearInterval(timer), 60000)
}

// ---- 用户选择弹窗 ----
function openUserPicker(type, courseIndexOrHtIndex, assistantIndex) {
  userPickerContext.type = type
  userPickerContext.courseIndex = courseIndexOrHtIndex
  userPickerContext.assistantIndex = assistantIndex ?? -1

  if (type === 'headteacher') {
    userPickerTitle.value = '选择带班队长'
    if (courseIndexOrHtIndex >= 0) {
      userPickerCurrentName.value = editClassInfo.headteachers[courseIndexOrHtIndex]?.name || ''
    } else {
      userPickerCurrentName.value = ''
    }
  } else if (type === 'primaryInstructor') {
    userPickerTitle.value = '选择主讲教官'
    userPickerCurrentName.value = editCourses.value[courseIndexOrHtIndex]?.primaryInstructor?.name || ''
  } else if (type === 'assistantInstructor') {
    userPickerTitle.value = '选择辅助教官'
    if (assistantIndex >= 0) {
      userPickerCurrentName.value = editCourses.value[courseIndexOrHtIndex]?.assistantInstructors?.[assistantIndex]?.name || ''
    } else {
      userPickerCurrentName.value = ''
    }
  }
  userPickerVisible.value = true
}

function handleUserPickerSelect({ mode, userId, name }) {
  const { type, courseIndex, assistantIndex } = userPickerContext

  if (type === 'headteacher') {
    if (mode === 'none') {
      if (courseIndex >= 0) editClassInfo.headteachers.splice(courseIndex, 1)
      return
    }
    const entry = { name, roleLabel: '带班队长', userId: userId || null, autoCreate: !userId && !!name }
    if (courseIndex >= 0) {
      editClassInfo.headteachers[courseIndex] = entry
    } else {
      editClassInfo.headteachers.push(entry)
    }
  } else if (type === 'primaryInstructor') {
    const course = editCourses.value[courseIndex]
    if (!course) return
    if (mode === 'none') {
      course.primaryInstructor = { name: '', userId: null, autoCreate: false }
    } else {
      course.primaryInstructor = { name, userId: userId || null, autoCreate: !userId && !!name }
    }
  } else if (type === 'assistantInstructor') {
    const course = editCourses.value[courseIndex]
    if (!course) return
    if (mode === 'none') {
      if (assistantIndex >= 0) course.assistantInstructors.splice(assistantIndex, 1)
      return
    }
    const entry = { name, userId: userId || null, autoCreate: !userId && !!name }
    if (assistantIndex >= 0) {
      course.assistantInstructors[assistantIndex] = entry
    } else {
      course.assistantInstructors.push(entry)
    }
  }
}

// ---- 步骤提交 ----
async function submitClassInfo() {
  saving.value = true
  try {
    await updateScheduleFileParseTask(activeTaskId.value, {
      confirmedClassInfo: { ...editClassInfo },
      currentStage: 'course_confirmation',
    })
    await loadDetail(activeTaskId.value)
  } catch (e) {
    message.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function submitCourses() {
  saving.value = true
  try {
    await updateScheduleFileParseTask(activeTaskId.value, {
      confirmedCourses: editCourses.value,
      currentStage: 'preview',
    })
    await loadDetail(activeTaskId.value)
  } catch (e) {
    message.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function submitConfig() {
  saving.value = true
  try {
    await updateScheduleFileParseTask(activeTaskId.value, {
      trainingConfig: { ...editConfig },
      currentStage: 'training_config',
    })
    await loadDetail(activeTaskId.value)
  } catch (e) {
    message.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function goStep(step) {
  const stageNames = ['parsing', 'class_info_confirmation', 'course_confirmation', 'preview', 'training_config']
  try {
    await updateScheduleFileParseTask(activeTaskId.value, { currentStage: stageNames[step] })
    await loadDetail(activeTaskId.value)
  } catch {
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
    message.error(e.message || '创建失败')
  } finally {
    confirming.value = false
  }
}

function goTrainingDetail() {
  const id = detail.value?.confirmedTrainingId
  if (id) {
    detailModalVisible.value = false
    router.push({ name: 'TrainingDetail', params: { id } })
  }
}

function addEmptyCourse() {
  editCourses.value.push({
    name: '', type: 'theory', location: '',
    primaryInstructor: { name: '', userId: null, autoCreate: false },
    assistantInstructors: [],
    sessions: [],
  })
  courseCollapseKeys.value.push(editCourses.value.length - 1)
}

// ---- 日历 ----
const WEEKDAY_NAMES = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
const COURSE_COLORS = ['#1890ff', '#52c41a', '#722ed1', '#fa8c16', '#eb2f96', '#13c2c2', '#faad14', '#2f54eb', '#f5222d', '#a0d911']

function courseColor(index) {
  return COURSE_COLORS[index % COURSE_COLORS.length]
}

function calendarDays(courses) {
  if (!courses || !courses.length) return []
  // 收集所有课次按日期分组
  const dateMap = {}
  courses.forEach((c, ci) => {
    ;(c.sessions || []).forEach(s => {
      const d = s.date
      if (!d) return
      if (!dateMap[d]) dateMap[d] = []
      dateMap[d].push({
        courseName: c.name || '未命名',
        courseIndex: ci,
        timeStart: s.timeStart || '',
        timeEnd: s.timeEnd || '',
      })
    })
  })
  // 排序日期
  const sortedDates = Object.keys(dateMap).sort()
  return sortedDates.map(date => {
    const dt = new Date(date + 'T00:00:00')
    const weekday = dt.getDay()
    const mm = String(dt.getMonth() + 1).padStart(2, '0')
    const dd = String(dt.getDate()).padStart(2, '0')
    // 排序课次按时间
    const sessions = dateMap[date].sort((a, b) => (a.timeStart || '').localeCompare(b.timeStart || ''))
    return {
      date,
      label: `${mm}/${dd}`,
      weekdayName: WEEKDAY_NAMES[weekday] || '',
      sessions,
    }
  })
}

function scheduleTableRows(courses) {
  if (!courses || !courses.length) return []
  const dateMap = {}
  courses.forEach(c => {
    ;(c.sessions || []).forEach(s => {
      const d = s.date
      if (!d) return
      if (!dateMap[d]) dateMap[d] = []
      dateMap[d].push({
        timeRange: `${s.timeStart || ''}~${s.timeEnd || ''}`,
        courseName: c.name || '未命名',
        instructor: c.primaryInstructor?.name || '',
        timeStart: s.timeStart || '',
      })
    })
  })
  return Object.keys(dateMap).sort().map(date => {
    const dt = new Date(date + 'T00:00:00')
    const m = dt.getMonth() + 1
    const d = dt.getDate()
    const rows = dateMap[date].sort((a, b) => a.timeStart.localeCompare(b.timeStart))
    return {
      date,
      dateLabel: `${m}月${d}日`,
      weekdayName: WEEKDAY_NAMES[dt.getDay()] || '',
      rows,
    }
  })
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
    preview: '待预览', training_config: '待完善信息',
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
  fetchTrainingBaseOptions()
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

.list-card-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.task-list-row {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.task-list-row:hover {
  background: #f5f5f5;
}

.task-row-content {
  flex: 1;
  min-width: 0;
}

.task-row-name {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-row-desc {
  font-size: 12px;
  color: #8c8c8c;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-row-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 24px;
  flex-shrink: 0;
}

.task-row-time {
  color: #999;
  font-size: 12px;
  white-space: nowrap;
}

.task-row-actions {
  flex-shrink: 0;
}

/* 点击编辑课次表格 */
.session-edit-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.session-edit-table th,
.session-edit-table td {
  border: 1px solid #f0f0f0;
  padding: 3px 6px;
  vertical-align: middle;
}

.session-edit-table thead th {
  background: #fafafa;
  color: #666;
  font-weight: 500;
  text-align: center;
}

.session-edit-table td {
  cursor: pointer;
}

.cell-display {
  display: block;
  min-height: 22px;
  padding: 2px 4px;
  border-radius: 4px;
  color: #333;
}

.cell-display:hover {
  background: #e6f4ff;
  color: #1677ff;
}

/* 日历 */
.schedule-calendar {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 12px;
  background: #fafafa;
}

.calendar-grid {
  display: flex;
  gap: 2px;
  overflow-x: auto;
}

.calendar-day {
  flex: 1;
  min-width: 140px;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
}

.calendar-day-header {
  text-align: center;
  padding: 6px 4px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
  border-radius: 6px 6px 0 0;
}

.calendar-day-name {
  font-size: 12px;
  font-weight: 500;
  color: #333;
}

.calendar-day-date {
  font-size: 11px;
  color: #999;
}

.calendar-day-body {
  padding: 4px;
  min-height: 60px;
}

.calendar-item {
  padding: 4px 6px;
  margin-bottom: 3px;
  border-left: 3px solid #1890ff;
  background: #f6f9ff;
  border-radius: 0 4px 4px 0;
  font-size: 11px;
}

.calendar-item-name {
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.calendar-item-time {
  color: #999;
  font-size: 10px;
}

.calendar-empty {
  text-align: center;
  color: #ccc;
  font-size: 11px;
  padding: 16px 0;
}

/* Excel 风格课表 */
.schedule-excel-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.schedule-excel-table th,
.schedule-excel-table td {
  border: 1px solid #d9d9d9;
  padding: 8px 12px;
  text-align: left;
  vertical-align: middle;
}

.schedule-excel-table thead th {
  background: #e6f4e6;
  color: #333;
  font-weight: 500;
  text-align: center;
}

.schedule-date-cell {
  text-align: center;
  background: #fafafa;
  font-weight: 500;
}

.schedule-date-main {
  font-size: 14px;
  color: #333;
}

.schedule-date-weekday {
  font-size: 12px;
  color: #999;
  font-weight: normal;
}

.schedule-time-cell {
  text-align: center;
  white-space: nowrap;
  color: #666;
}

.schedule-course-cell {
  color: #333;
}

.schedule-instructor-cell {
  text-align: center;
  color: #333;
  font-weight: 500;
}
</style>

<style>
.fullscreen-modal .ant-modal {
  max-width: 100vw;
  top: 0;
  padding: 0;
  margin: 0;
}

.fullscreen-modal .ant-modal-content {
  min-height: 100vh;
  border-radius: 0;
  display: flex;
  flex-direction: column;
}

.fullscreen-modal .ant-modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 48px;
  max-width: 960px;
  margin: 0 auto;
  width: 100%;
}
</style>
