<template>
  <div class="training-detail-page">
    <a-breadcrumb style="margin-bottom:16px">
      <a-breadcrumb-item @click="$router.push('/training')" style="cursor:pointer;color:var(--police-primary)">培训班管理</a-breadcrumb-item>
      <a-breadcrumb-item>{{ trainingData.name }}</a-breadcrumb-item>
    </a-breadcrumb>

    <a-card :bordered="false" class="workflow-card" style="margin-bottom:16px">
      <div class="workflow-header">
        <a-steps :current="workflowCurrentIndex" :items="workflowStepItems" size="small" />
      </div>
    </a-card>

    <a-row :gutter="20">
      <a-col :xs="24" :md="16">
        <a-card :bordered="false" class="main-card">
          <div class="training-banner" :class="'status-' + trainingData.status">
            <div class="banner-content">
              <a-tag :color="statusColorMap[trainingData.status]" class="status-tag">{{ statusLabels[trainingData.status] }}</a-tag>
              <h2 class="training-title">{{ trainingData.name }}</h2>
              <div class="training-meta-row" style="margin-bottom:8px">
                <span><CalendarOutlined /> {{ trainingData.startDate }} ~ {{ trainingData.endDate }}</span>
                <span><EnvironmentOutlined /> {{ trainingData.location }}</span>
                <span><UserOutlined /> 主管/班主任：{{ trainingData.instructorName }}</span>
              </div>
              <div class="training-meta-row secondary-meta">
                <span>培训基地：{{ trainingData.trainingBaseName || '手动输入地点' }}</span>
                <span>部门：{{ trainingData.departmentName || '未设置' }}</span>
                <span>警种：{{ trainingData.policeTypeName || '未设置' }}</span>
              </div>
              <div class="training-desc" v-if="trainingData.description">
                {{ trainingData.description }}
              </div>
            </div>
          </div>

          <a-tabs v-model:activeKey="activeTab" style="margin-top:16px">
            <!-- ===== 班级概览 + 课程管理 ===== -->
            <a-tab-pane key="overview" tab="班级概览">
              <div class="overview-stats">
                <div class="ov-stat" v-for="s in overviewStats" :key="s.label">
                  <div class="ov-num" :style="{ color: s.color }">{{ s.value }}</div>
                  <div class="ov-label">{{ s.label }}</div>
                </div>
              </div>
              <div class="training-base-info">
                <div class="info-row">
                  <span class="info-label">培训基地</span>
                  <span class="info-value">{{ trainingData.trainingBaseName || '手动输入地点' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">部门</span>
                  <span class="info-value">{{ trainingData.departmentName || '未设置' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">警种</span>
                  <span class="info-value">{{ trainingData.policeTypeName || '未设置' }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">准入考试</span>
                  <span class="info-value">{{ trainingData.admissionExamTitle || '无' }}</span>
                </div>
              </div>
              <a-divider />
              <div class="course-schedule">
                <div class="section-header">
                  <h4>当前课程</h4>
                </div>
                <a-empty v-if="!currentSession" description="当前没有可操作课次" />
                <div v-else class="course-item current-course-card">
                  <div class="ci-left">
                    <div class="ci-name">{{ currentSession.courseName }}</div>
                    <div class="ci-instructor">
                      主讲：{{ currentSession.primaryInstructorName || '未指定' }}
                      <template v-if="currentSession.assistantInstructorNames?.length">
                        / 带教：{{ currentSession.assistantInstructorNames.join('、') }}
                      </template>
                    </div>
                    <div class="ci-time">{{ currentSession.date }} {{ currentSession.timeRange }}</div>
                    <div class="ci-time">地点：{{ currentSession.location || '未设置' }} · 状态：{{ currentSessionStatusLabel }}</div>
                  </div>
                  <div class="ci-right">
                    <a-space wrap>
                      <a-button v-if="currentSession.actionPermissions?.canStartCheckin" size="small" type="primary" @click="handleStartSessionCheckin">开始签到</a-button>
                      <a-button v-if="currentSession.actionPermissions?.canEndCheckin" size="small" @click="handleEndSessionCheckin">结束签到</a-button>
                      <a-button v-if="currentSession.actionPermissions?.canStartCheckout" size="small" type="primary" ghost @click="handleStartSessionCheckout">开始签退</a-button>
                      <a-button v-if="currentSession.actionPermissions?.canEndCheckout" size="small" @click="handleEndSessionCheckout">结束签退</a-button>
                      <a-button
                        v-if="isEnrolled && currentSession.status === 'checkin_open'"
                        size="small"
                        type="primary"
                        ghost
                        @click="goCurrentSessionCheckin"
                      >
                        学员签到
                      </a-button>
                      <a-button
                        v-if="isEnrolled && currentSession.status === 'checkout_open'"
                        size="small"
                        @click="$router.push({ name: 'Checkout', params: { id: trainingData.id, sessionKey: currentSession.sessionId } })"
                      >
                        学员签退
                      </a-button>
                      <a-button v-if="currentSession.actionPermissions?.canSkip" size="small" danger ghost @click="handleSkipCurrentSession">跳过课程</a-button>
                    </a-space>
                  </div>
                </div>
              </div>
            </a-tab-pane>

            <a-tab-pane key="schedule" tab="课程安排">
              <div class="section-header" style="margin-bottom:16px">
                <a-space>
                  <h4 style="margin:0">课程安排</h4>
                  <a-radio-group v-model:value="scheduleViewMode" size="small">
                    <a-radio-button value="course">按课程展示</a-radio-button>
                    <a-radio-button value="timetable">按课表展示</a-radio-button>
                  </a-radio-group>
                </a-space>
                <permissions-tooltip
                  v-if="!authStore.isStudent"
                  :allowed="canScheduleEdit"
                  :tips="scheduleEditTooltip"
                  v-slot="{ disabled }"
                >
                  <a-button size="small" type="primary" :disabled="disabled" @click="openCourseModal()">
                    <template #icon><PlusOutlined /></template>添加课程
                  </a-button>
                </permissions-tooltip>
              </div>

              <template v-if="scheduleViewMode === 'course'">
                <a-empty v-if="!trainingData.courses || trainingData.courses.length === 0" description="暂无课程安排，请点击添加" />
                <div class="course-item" v-for="(c, idx) in trainingData.courses" :key="idx">
                  <div class="ci-left">
                    <div class="ci-name">{{ c.name }}</div>
                    <div class="ci-instructor">
                      {{ c.primaryInstructorName || c.instructor || '未指定教官' }}
                      <template v-if="c.assistantInstructorNames?.length">
                        / 带教：{{ c.assistantInstructorNames.join('、') }}
                      </template>
                    </div>
                    <div class="ci-time" v-if="c.schedules?.length">{{ c.schedules.length }} 个课次 · {{ c.hours }} 课时</div>
                  </div>
                  <div class="ci-right">
                    <a-tag :color="c.type === 'theory' ? 'blue' : 'green'" size="small">{{ c.type === 'theory' ? '理论' : '实操' }}</a-tag>
                    <template v-if="!authStore.isStudent">
                      <permissions-tooltip
                        :allowed="canScheduleEdit"
                        :tips="scheduleEditTooltip"
                        v-slot="{ disabled }"
                      >
                        <a-button size="small" type="link" :disabled="disabled" @click="openCourseModal(idx)">编辑</a-button>
                      </permissions-tooltip>
                      <permissions-tooltip
                        :allowed="canScheduleEdit"
                        :tips="scheduleEditTooltip"
                        v-slot="{ disabled }"
                      >
                        <a-button size="small" type="link" danger :disabled="disabled" @click="removeCourse(idx)">删除</a-button>
                      </permissions-tooltip>
                    </template>
                  </div>
                </div>
              </template>

              <a-table
                v-else
                :data-source="scheduleRows"
                :pagination="false"
                row-key="sessionId"
                size="small"
              >
                <a-table-column title="日期" data-index="date" key="date" width="120" />
                <a-table-column title="时间" data-index="timeRange" key="timeRange" width="140" />
                <a-table-column title="课程" data-index="courseName" key="courseName" />
                <a-table-column title="教官" data-index="instructorText" key="instructorText" width="220" />
                <a-table-column title="状态" key="status" width="140">
                  <template #default="{ record }">
                    <a-tag :color="scheduleStatusColorMap[record.status] || 'default'">{{ scheduleStatusLabelMap[record.status] || record.status }}</a-tag>
                  </template>
                </a-table-column>
                <a-table-column title="操作" key="action" width="200">
                  <template #default="{ record }">
                    <a-space v-if="currentSession && currentSession.sessionId === record.sessionId">
                      <a-button v-if="currentSession.actionPermissions?.canStartCheckin" size="small" type="link" @click="handleStartSessionCheckin">开始签到</a-button>
                      <a-button v-if="currentSession.actionPermissions?.canEndCheckin" size="small" type="link" @click="handleEndSessionCheckin">结束签到</a-button>
                      <a-button v-if="currentSession.actionPermissions?.canStartCheckout" size="small" type="link" @click="handleStartSessionCheckout">开始签退</a-button>
                      <a-button v-if="currentSession.actionPermissions?.canEndCheckout" size="small" type="link" @click="handleEndSessionCheckout">结束签退</a-button>
                      <a-button v-if="currentSession.actionPermissions?.canSkip" size="small" type="link" danger @click="handleSkipCurrentSession">跳过</a-button>
                    </a-space>
                    <span v-else style="color:#999">仅当前课次可操作</span>
                  </template>
                </a-table-column>
              </a-table>
            </a-tab-pane>

            <a-tab-pane key="exams" tab="考试安排">
              <div class="section-header" style="margin-bottom:16px">
                <h4>考试安排</h4>
                <a-space v-if="!authStore.isStudent">
                  <permissions-tooltip
                    :allowed="canQuickCreateExam"
                    :tips="quickCreateExamTooltip"
                    v-slot="{ disabled }"
                  >
                    <a-button size="small" type="primary" :disabled="disabled" @click="quickCreateTrainingExam">
                      快捷添加考试
                    </a-button>
                  </permissions-tooltip>
                  <a-button size="small" @click="goTrainingExamManage">
                    前往考试管理
                  </a-button>
                </a-space>
              </div>

              <a-empty v-if="!trainingExamSessions.length" description="当前培训班暂无考试安排" />
              <div v-else class="exam-plan-list">
                <div class="exam-plan-card" v-for="exam in trainingExamSessions" :key="exam.id">
                  <div class="exam-plan-main">
                    <div class="exam-plan-name">{{ exam.title }}</div>
                    <div class="exam-plan-meta">
                      <span>用途：{{ examPurposeLabelMap[exam.purpose] || exam.purpose }}</span>
                      <span>题目数：{{ exam.questionCount || 0 }}</span>
                      <span>及格分：{{ exam.passingScore || 60 }}</span>
                      <span>开始：{{ formatDateTime(exam.startTime) }}</span>
                      <span>结束：{{ formatDateTime(exam.endTime) }}</span>
                    </div>
                  </div>
                  <a-space wrap>
                    <a-tag :color="examStatusColorMap[exam.status] || 'default'">
                      {{ examStatusLabelMap[exam.status] || exam.status }}
                    </a-tag>
                    <a-button size="small" type="link" @click="goTrainingExamManage">
                      前往管理
                    </a-button>
                  </a-space>
                </div>
              </div>
            </a-tab-pane>

            <!-- ===== 学员名单 (Admin/Instructor 可管理) ===== -->
            <a-tab-pane key="students" tab="学员名单" v-if="!authStore.isStudent">
              <div class="section-header" style="margin-bottom:16px">
                <a-input-search v-model:value="studentSearch" placeholder="搜索学员..." class="student-search-input" />
                <a-space>
                  <permissions-tooltip
                    :allowed="canManageEnrollmentApplications"
                    :tips="trainingManageTooltip"
                    v-slot="{ disabled }"
                  >
                    <a-button size="small" :disabled="disabled" @click="openEnrollmentApplicationModal">
                      申请管理<span v-if="pendingEnrollmentCount > 0">（{{ pendingEnrollmentCount }}）</span>
                    </a-button>
                  </permissions-tooltip>
                  <permissions-tooltip
                    :allowed="canManageStudents"
                    :tips="trainingManageTooltip"
                    v-slot="{ disabled }"
                  >
                    <a-button type="primary" size="small" :disabled="disabled" @click="openStudentModal">
                      <template #icon><PlusOutlined /></template>添加学员
                    </a-button>
                  </permissions-tooltip>
                </a-space>
              </div>
              <a-table :dataSource="filteredStudents" :columns="studentColumnsWithAction" size="small" :pagination="{ pageSize: 10 }">
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'name'">
                    <a-button type="link" size="small" style="padding:0" @click="goTraineeDetail(record.key)">
                      {{ record.name }}
                    </a-button>
                  </template>
                  <template v-if="column.key === 'progress'">
                    <a-progress :percent="record.progress" size="small" />
                  </template>
                  <template v-if="column.key === 'checkin'">
                    <span :style="{ color: record.checkinRate >= 90 ? '#52c41a' : record.checkinRate >= 70 ? '#faad14' : '#ff4d4f' }">
                      {{ record.checkinRate }}%
                    </span>
                  </template>
                  <template v-if="column.key === 'action'">
                    <permissions-tooltip
                      :allowed="canManageStudents"
                      :tips="trainingManageTooltip"
                      v-slot="{ disabled }"
                    >
                      <a-popconfirm v-if="!disabled" title="确定移除该学员？" @confirm="removeStudent(record.key)">
                        <a-button size="small" type="link" danger>移除</a-button>
                      </a-popconfirm>
                      <a-button v-else size="small" type="link" danger :disabled="disabled">移除</a-button>
                    </permissions-tooltip>
                  </template>
                </template>
              </a-table>
            </a-tab-pane>

            <a-tab-pane key="resources" tab="培训资源" v-if="!authStore.isStudent">
              <div class="section-header" style="margin-bottom:16px">
                <h4>资源绑定</h4>
                <a-space>
                  <a-select
                    v-model:value="selectedTrainingResourceId"
                    show-search
                    :options="trainingResourceOptions"
                    :filter-option="(input, option) => (option?.label || '').toLowerCase().includes(input.toLowerCase())"
                    placeholder="选择已发布资源"
                    :disabled="!canManageResources"
                    class="training-resource-select"
                  />
                  <permissions-tooltip
                    :allowed="canManageResources"
                    :tips="trainingManageTooltip"
                    v-slot="{ disabled }"
                  >
                    <a-button type="primary" size="small" :disabled="disabled" @click="bindSelectedTrainingResource">绑定</a-button>
                  </permissions-tooltip>
                  <a-button size="small" @click="loadTrainingDetail">刷新</a-button>
                </a-space>
              </div>

              <a-empty v-if="trainingResources.length === 0" description="暂无绑定资源" />
              <a-table v-else :data-source="trainingResources" :columns="trainingResourceColumns" row-key="id" :pagination="false">
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'tags'">
                    <a-space wrap>
                      <a-tag v-for="tag in (record.tags || [])" :key="tag">{{ tag }}</a-tag>
                    </a-space>
                  </template>
                  <template v-if="column.key === 'action'">
                    <permissions-tooltip
                      :allowed="canManageResources"
                      :tips="trainingManageTooltip"
                      v-slot="{ disabled }"
                    >
                      <a-popconfirm v-if="!disabled" title="确认解绑该资源？" @confirm="removeTrainingResource(record.id)">
                        <a-button size="small" danger type="link">解绑</a-button>
                      </a-popconfirm>
                      <a-button v-else size="small" danger type="link" :disabled="disabled">解绑</a-button>
                    </permissions-tooltip>
                  </template>
                </template>
              </a-table>
            </a-tab-pane>

            <!-- ===== 公告 ===== -->
            <a-tab-pane key="notice" tab="公告">
              <div class="section-header" style="margin-bottom:16px" v-if="!authStore.isStudent">
                <h4>班级公告栏</h4>
                <permissions-tooltip
                  :allowed="canManageNotices"
                  :tips="trainingManageTooltip"
                  v-slot="{ disabled }"
                >
                  <a-button type="primary" size="small" :disabled="disabled" @click="openNoticeModal">
                    <template #icon><PlusOutlined /></template>发布新公告
                  </a-button>
                </permissions-tooltip>
              </div>
              <a-empty v-if="!notices || notices.length === 0" description="暂无公告" />
              <a-collapse v-else accordion :bordered="false" class="custom-notice-collapse">
                <a-collapse-panel v-for="n in notices" :key="n.id" :header="n.title">
                  <template #extra>
                    <span class="notice-time">{{ n.time }}</span>
                    <a-space style="margin-left: 12px" v-if="!authStore.isStudent" @click.stop>
                      <permissions-tooltip
                        :allowed="canManageNotices"
                        :tips="trainingManageTooltip"
                        v-slot="{ disabled }"
                      >
                        <a-button type="link" size="small" style="padding:0" :disabled="disabled" @click="editNotice(n)">编辑</a-button>
                      </permissions-tooltip>
                      <permissions-tooltip
                        :allowed="canManageNotices"
                        :tips="trainingManageTooltip"
                        v-slot="{ disabled }"
                      >
                        <a-popconfirm v-if="!disabled" title="确定删除该公告？" @confirm="deleteNotice(n.id)">
                          <a-button type="link" danger size="small" style="padding:0">删除</a-button>
                        </a-popconfirm>
                        <a-button v-else type="link" danger size="small" style="padding:0" :disabled="disabled">删除</a-button>
                      </permissions-tooltip>
                    </a-space>
                  </template>
                  <p class="notice-content">{{ n.content }}</p>
                </a-collapse-panel>
              </a-collapse>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>

      <a-col :xs="24" :md="8">
        <a-card title="流程操作" :bordered="false" style="margin-bottom:16px" v-if="showWorkflowActionCard">
          <a-space direction="vertical" size="small" class="workflow-action-list">
            <permissions-tooltip
              v-if="showPublishWorkflowAction"
              :allowed="canPublishWorkflowAction"
              :tips="trainingManageTooltip"
              block
              v-slot="{ disabled }"
            >
              <a-button block type="primary" ghost :disabled="disabled" @click="handlePublish">发布</a-button>
            </permissions-tooltip>
            <permissions-tooltip
              v-if="showLockWorkflowAction"
              :allowed="canLockWorkflowAction"
              :tips="trainingManageTooltip"
              block
              v-slot="{ disabled }"
            >
              <a-button block danger ghost :disabled="disabled" @click="handleLock">锁定名单</a-button>
            </permissions-tooltip>
            <permissions-tooltip
              v-if="showStartWorkflowAction"
              :allowed="canStartWorkflowAction"
              :tips="trainingManageTooltip"
              block
              v-slot="{ disabled }"
            >
              <a-button block type="primary" :disabled="disabled" @click="handleStart">开班</a-button>
            </permissions-tooltip>
            <permissions-tooltip
              v-if="showEndWorkflowAction"
              :allowed="canEndWorkflowAction"
              :tips="trainingManageTooltip"
              block
              v-slot="{ disabled }"
            >
              <a-button block danger :disabled="disabled" @click="handleEnd">结班</a-button>
            </permissions-tooltip>
          </a-space>
        </a-card>

        <a-card title="快捷操作" :bordered="false" style="margin-bottom:16px">
          <div class="quick-ops">
            <a-button block style="margin-bottom:8px" @click="handleGlobalCheckin" type="primary" v-if="trainingData.status === 'active' && !authStore.isStudent">
              <template #icon><QrcodeOutlined /></template>开班/上课签到
            </a-button>
            <a-button block style="margin-bottom:8px" @click="handleGlobalCheckin" type="primary" v-if="trainingData.status === 'active' && authStore.isStudent && isEnrolled">
              <template #icon><QrcodeOutlined /></template>扫码签到
            </a-button>
            <a-button block style="margin-bottom:8px" @click="$router.push('/training/schedule/' + trainingData.id)">
              <template #icon><CalendarOutlined /></template>查看日程
            </a-button>
            <permissions-tooltip
              v-if="!authStore.isStudent"
              :allowed="canEdit"
              :tips="trainingManageTooltip"
              block
              v-slot="{ disabled }"
            >
              <a-button block style="margin-bottom:8px" :disabled="disabled" @click="openEditModal">
                <template #icon><EditOutlined /></template>编辑班级信息
              </a-button>
            </permissions-tooltip>
            <permissions-tooltip
              v-if="!authStore.isStudent"
              :allowed="canExportStudents"
              :tips="trainingManageTooltip"
              block
              v-slot="{ disabled }"
            >
              <a-button block :disabled="disabled" @click="exportMsg">
                <template #icon><DownloadOutlined /></template>导出学员名单
              </a-button>
            </permissions-tooltip>
          </div>
        </a-card>

        <a-card title="签到率统计" :bordered="false">
          <div class="checkin-summary" style="display: flex; justify-content: space-around; align-items: center">
            <div style="text-align: center">
              <a-progress type="circle" :percent="startCheckinRate" :size="100" />
              <div style="margin-top: 8px; font-weight: 500">开班签到率</div>
            </div>
            <div style="text-align: center">
              <a-progress type="circle" :percent="totalCourseRate" :size="100" :stroke-color="{ '0%': '#003087', '100%': '#52c41a' }" />
              <div style="margin-top: 8px; font-weight: 500">课程总签到率</div>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <a-modal
      v-model:open="showCourseModal"
      :title="editingCourseIdx !== null ? '编辑课程' : '添加课程'"
      @ok="saveCourse"
      ok-text="保存"
      cancel-text="取消"
    >
      <a-form layout="vertical" style="margin-top:12px">
        <a-form-item label="课程名称" required>
          <a-input v-model:value="courseForm.name" placeholder="例：刑事诉讼法实务操作" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="授课教官" required>
              <a-select
                v-model:value="courseForm.instructorId"
                placeholder="从教官库中选择"
                show-search
                option-filter-prop="label"
                style="width:100%"
                @change="onInstructorChange"
              >
                <a-select-option
                  v-for="inst in instructorList"
                  :key="inst.userId"
                  :value="inst.userId"
                  :label="inst.name"
                >
                  {{ inst.name }} · {{ inst.title }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="带教教官">
              <a-select
                v-model:value="courseForm.assistantInstructorIds"
                mode="multiple"
                placeholder="可多选带教教官"
                show-search
                option-filter-prop="label"
                style="width:100%"
              >
                <a-select-option
                  v-for="inst in instructorList"
                  :key="inst.userId"
                  :value="inst.userId"
                  :label="inst.name"
                >
                  {{ inst.name }} · {{ inst.title }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="12">
          <a-col :span="24">
            <a-form-item label="详细排课清单" required>
              <div v-if="courseForm.schedules.length > 0" style="margin-bottom: 12px; display: flex; flex-wrap: wrap; gap: 8px; background: #f9f9f9; padding: 12px; border-radius: 6px;">
                <a-tag
                  v-for="(sch, idx) in courseForm.schedules"
                  :key="idx"
                  closable
                  color="blue"
                  @close="removeCourseSchedule(idx)"
                >
                  {{ sch.date }} ({{ sch.timeRange }}) · {{ sch.hours }}课时
                </a-tag>
              </div>
              <div class="schedule-editor-box">
                <div class="schedule-mode-row">
                  <a-radio-group v-model:value="dateAddMode" size="small">
                    <a-radio-button value="single">单日排课</a-radio-button>
                    <a-radio-button value="range">多日同段连排</a-radio-button>
                  </a-radio-group>
                </div>
                <div class="schedule-editor-row">
                  <a-date-picker
                    v-if="dateAddMode === 'single'"
                    v-model:value="tempDate"
                    class="schedule-date-picker"
                    format="YYYY-MM-DD"
                    placeholder="选择日期"
                  />
                  <a-range-picker
                    v-else
                    v-model:value="tempDateRange"
                    class="schedule-date-picker"
                    format="YYYY-MM-DD"
                    :placeholder="['开始日期', '结束日期']"
                  />
                  <a-time-range-picker
                    v-model:value="tempTimeRange"
                    class="schedule-time-range"
                    format="HH:mm"
                    :minute-step="5"
                    :placeholder="['开始', '结束']"
                  />
                  <a-button type="primary" size="small" @click="addCourseSchedule">
                    添加
                  </a-button>
                </div>
              </div>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="课时数(自动计算取整)" required>
              <a-input-number v-model:value="courseForm.hours" :min="0" :step="1" style="width:100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="课程类型">
              <a-radio-group v-model:value="courseForm.type">
                <a-radio value="theory">理论课</a-radio>
                <a-radio value="practice">实操课</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <!-- ===== 添加学员弹窗 ===== -->
    <a-modal
      v-model:open="showStudentModal"
      title="添加学员"
      @ok="addSelectedStudents"
      ok-text="确认添加"
      cancel-text="取消"
      width="600px"
    >
      <div style="margin-bottom:12px">
        <a-input-search v-model:value="addStudentSearch" placeholder="搜索学员姓名或工号..." allow-clear />
      </div>
      <a-table
        :dataSource="availableStudents"
        :columns="addStudentColumns"
        size="small"
        :pagination="{ pageSize: 8 }"
        :row-selection="{ selectedRowKeys: selectedStudentKeys, onChange: (keys) => selectedStudentKeys = keys }"
        row-key="id"
      />
    </a-modal>

    <!-- ===== 编辑班级信息弹窗 ===== -->
    <a-modal
      v-model:open="showEditModal"
      title="编辑班级信息"
      @ok="saveClassInfo"
      ok-text="保存"
      cancel-text="取消"
      width="640px"
    >
      <a-form layout="vertical" style="margin-top:12px">
        <a-form-item label="培训班名称" required>
          <a-input v-model:value="editForm.name" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="开始日期" required>
              <a-date-picker
                v-model:value="editFormDates[0]"
                style="width:100%"
                format="YYYY-MM-DD"
                @change="(_, s) => editForm.startDate = s"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="结束日期" required>
              <a-date-picker
                v-model:value="editFormDates[1]"
                style="width:100%"
                format="YYYY-MM-DD"
                @change="(_, s) => editForm.endDate = s"
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="培训地点" required>
          <a-input v-model:value="editForm.location" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="主管/班主任">
              <a-select
                v-model:value="editForm.instructorId"
                placeholder="从教官库选定班主任"
                show-search
                option-filter-prop="label"
                @change="onEditInstructorChange"
              >
                <a-select-option
                  v-for="inst in instructorList"
                  :key="inst.userId"
                  :value="inst.userId"
                  :label="inst.name"
                >
                  {{ inst.name }} · {{ inst.title }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="班级容量">
              <a-input-number v-model:value="editForm.capacity" :min="1" style="width:100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="状态">
          <a-select v-model:value="editForm.status">
            <a-select-option value="upcoming">未开始</a-select-option>
            <a-select-option value="active">进行中</a-select-option>
            <a-select-option value="ended">已结束</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="报名方式">
          <a-radio-group v-model:value="editForm.enrollmentRequiresApproval">
            <a-radio :value="true">申请审核</a-radio>
            <a-radio :value="false">直接通过</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="培训简介">
          <a-textarea v-model:value="editForm.description" :rows="2" />
        </a-form-item>
      </a-form>
    </a-modal>

    <a-modal
      v-model:open="showEnrollmentApplicationModal"
      title="申请管理"
      :footer="null"
      width="860px"
    >
      <div class="section-header" style="margin-bottom:16px">
        <div class="page-sub">待审核申请 {{ pendingEnrollmentCount }} 人</div>
        <a-button size="small" @click="loadEnrollmentApplications">刷新</a-button>
      </div>
      <a-empty v-if="!pendingEnrollmentApplications.length && !enrollmentApplicationsLoading" description="暂无待审核申请" />
      <a-table
        v-else
        :loading="enrollmentApplicationsLoading"
        :data-source="pendingEnrollmentApplications"
        :pagination="{ pageSize: 6 }"
        row-key="id"
        size="small"
      >
        <a-table-column title="姓名" data-index="userNickname" key="userNickname" />
        <a-table-column title="警号" data-index="policeId" key="policeId" width="120" />
        <a-table-column title="单位" key="departments" :custom-render="({ record }) => (record.departments || []).join(' / ') || '-'" />
        <a-table-column title="联系电话" data-index="contactPhone" key="contactPhone" width="140" />
        <a-table-column title="住宿" key="needAccommodation" width="80" :custom-render="({ record }) => (record.needAccommodation ? '需要' : '无需')" />
        <a-table-column title="报名备注" key="note" :custom-render="({ record }) => record.note || '-'" />
        <a-table-column title="操作" key="action" width="180">
          <template #default="{ record }">
            <a-space>
              <permissions-tooltip
                :allowed="canManageEnrollmentApplications && authStore.hasPermission('APPROVE_ENROLLMENT')"
                :tips="approveEnrollmentTooltip"
                v-slot="{ disabled }"
              >
                <a-button type="primary" size="small" :disabled="disabled" @click="handleApproveEnrollment(record)">通过</a-button>
              </permissions-tooltip>
              <permissions-tooltip
                :allowed="canManageEnrollmentApplications && authStore.hasPermission('REJECT_ENROLLMENT')"
                :tips="rejectEnrollmentTooltip"
                v-slot="{ disabled }"
              >
                <a-button size="small" danger :disabled="disabled" @click="openRejectEnrollmentModal(record)">拒绝</a-button>
              </permissions-tooltip>
            </a-space>
          </template>
        </a-table-column>
      </a-table>
    </a-modal>

    <a-modal
      v-model:open="showRejectEnrollmentModal"
      title="拒绝报名申请"
      @ok="submitRejectEnrollment"
      @cancel="closeRejectEnrollmentModal"
      ok-text="确认拒绝"
      cancel-text="取消"
      width="520px"
    >
      <a-form layout="vertical" style="margin-top:12px">
        <a-form-item label="拒绝理由" required>
          <a-textarea
            v-model:value="rejectEnrollmentNote"
            :rows="4"
            placeholder="请输入拒绝理由，学员会在报名结果中看到该说明"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- ===== 发布公告弹窗 ===== -->
    <a-modal
      v-model:open="showNoticeModal"
      :title="editingNoticeId ? '编辑公告' : '发布新公告'"
      @ok="saveNotice"
      ok-text="保存"
      cancel-text="取消"
      width="600px"
    >
      <a-form layout="vertical" style="margin-top:12px">
        <a-form-item label="公告标题" required>
          <a-input v-model:value="noticeForm.title" placeholder="请输入标题" />
        </a-form-item>
        <a-form-item label="公告内容" required>
          <a-textarea v-model:value="noticeForm.content" :rows="5" placeholder="请输入公告详细内容..." />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { CalendarOutlined, EnvironmentOutlined, UserOutlined, QrcodeOutlined, DownloadOutlined, PlusOutlined, EditOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import {
  getTraining,
  getEnrollments,
  approveEnrollment,
  rejectEnrollment,
  manageTraining as apiManageTraining,
  updateTraining as apiUpdateTraining,
  publishTraining,
  lockTraining,
  startTraining,
  endTraining,
  startTrainingSessionCheckin,
  endTrainingSessionCheckin,
  startTrainingSessionCheckout,
  endTrainingSessionCheckout,
  skipTrainingSession,
  bindTrainingResource,
  unbindTrainingResource,
} from '@/api/training'
import { getResources } from '@/api/resource'
import { getUsers } from '@/api/user'
import { createNotice as apiCreateNotice, updateNotice as apiUpdateNotice, deleteNotice as apiDeleteNotice } from '@/api/notice'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/datetime'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const trainingId = route.params.id
const instructorList = ref([])
const instructorOptionsLoaded = ref(false)
const instructorOptionsLoading = ref(false)
const studentCandidatesLoaded = ref(false)
const studentCandidatesLoading = ref(false)

// 使用 reactive 使数据可编辑
const trainingData = reactive({
  id: trainingId,
  name: '',
  status: 'upcoming',
  publishStatus: 'draft',
  isLocked: false,
  progressPercent: 0,
  startDate: '',
  endDate: '',
  location: '',
  departmentId: null,
  departmentName: '',
  policeTypeId: null,
  policeTypeName: '',
  trainingBaseId: null,
  trainingBaseName: '',
  instructorId: null,
  instructorName: '',
  description: '',
  enrollmentRequiresApproval: true,
  courses: [],
  studentIds: [],
  students: [],
  capacity: 0,
  enrolledCount: 0,
  enrolled: 0,
  checkinRecords: [],
  examSessions: [],
  admissionExamId: null,
  admissionExamTitle: '',
  workflowSteps: [],
  currentStepKey: 'draft',
  currentSession: null,
  canManageAll: false,
  canManageTraining: false,
  canEditTraining: false,
  canEditCourses: false,
  canReviewEnrollments: false,
  currentEnrollmentStatus: null,
  canEnterTraining: false,
})

const allUserList = ref([])
const rosterUserList = ref([])
const notices = ref([])
const userMap = computed(() => {
  const map = {}
  rosterUserList.value.forEach(u => { map[u.id] = u })
  return map
})

function normalizeCheckinRecords(records = []) {
  return records.map((record) => ({
    ...record,
    studentId: record.userId,
    name: record.userNickname || record.userName || record.userId,
    sessionKey: record.sessionKey || 'start',
  }))
}

function normalizeNotices(items = []) {
  return items.map((item) => ({
    ...item,
    time: formatDateTime(item.createdAt, ''),
  }))
}

function syncTrainingRoster(students = [], studentIds = []) {
  const mappedStudents = (students || []).map((item) => ({
    id: item.userId,
    username: item.userName,
    nickname: item.userNickname,
    policeId: item.policeId,
    departments: (item.departments || []).map((name) => ({ name })),
  }))
  rosterUserList.value = mappedStudents.length
    ? mappedStudents
    : (studentIds || []).map((userId) => ({ id: userId }))
}

function applyTrainingDetail(data) {
  const normalizedStudents = data.students || []
  const normalizedStudentIds = data.studentIds || normalizedStudents.map((item) => item.userId).filter((item) => item != null)
  Object.assign(trainingData, data, {
    progressPercent: data.progressPercent || 0,
    instructorId: data.instructorId || null,
    publishStatus: data.publishStatus || 'draft',
    isLocked: !!data.isLocked,
    courses: (data.courses || []).map((course) => ({
      ...course,
      schedules: (course.schedules || []).map((schedule) => ({
        ...schedule,
        timeRange: schedule.timeRange || schedule.time_range || '',
        sessionId: schedule.sessionId || schedule.session_id,
      })),
    })),
    studentIds: normalizedStudentIds,
    students: normalizedStudents,
    enrolledCount: data.enrolledCount ?? normalizedStudentIds.length,
    enrolled: data.enrolledCount ?? normalizedStudentIds.length,
    enrollmentRequiresApproval: data.enrollmentRequiresApproval !== false,
    checkinRecords: normalizeCheckinRecords(data.checkinRecords || []),
    workflowSteps: data.workflowSteps || [],
    currentStepKey: data.currentStepKey || 'draft',
    currentSession: data.currentSession
      ? {
          ...data.currentSession,
          timeRange: data.currentSession.timeRange || data.currentSession.time_range || '',
          sessionId: data.currentSession.sessionId || data.currentSession.session_id,
        }
      : null,
    canManageAll: !!data.canManageAll,
    canManageTraining: !!data.canManageTraining,
    canEditTraining: !!data.canEditTraining,
    canEditCourses: !!data.canEditCourses,
    canReviewEnrollments: !!data.canReviewEnrollments,
    currentEnrollmentStatus: data.currentEnrollmentStatus || null,
    canEnterTraining: !!data.canEnterTraining,
  })
  syncTrainingRoster(normalizedStudents, normalizedStudentIds)
  trainingResources.value = data.resources || []
  notices.value = normalizeNotices(data.notices || [])
  syncEditFormFromTraining()
}

async function loadTrainingDetail() {
  try {
    const data = await getTraining(trainingId)
    if (authStore.isStudent && !data.canEnterTraining) {
      if (data.currentEnrollmentStatus === 'pending') {
        message.warning('报名审核通过后才能进入培训班')
        router.replace({ name: 'Enroll', params: { id: trainingId } })
        return
      }
      if (data.currentEnrollmentStatus === 'rejected') {
        message.warning('当前报名未通过，不能进入培训班')
        router.replace({ name: 'Enroll', params: { id: trainingId } })
        return
      }
      if (data.publishStatus === 'published') {
        message.warning('请先报名并通过审核后再进入培训班')
        router.replace({ name: 'Enroll', params: { id: trainingId } })
        return
      }
      message.warning('当前用户尚未被录取到该培训班')
      router.replace('/training')
      return
    }
    applyTrainingDetail(data)
  } catch (e) {
    message.error('加载培训班详情失败')
  }
}

async function submitTrainingUpdate(payload) {
  if (trainingData.canManageTraining) {
    return apiManageTraining(trainingId, payload)
  }
  return apiUpdateTraining(trainingId, payload)
}

async function ensureInstructorOptionsLoaded(force = false) {
  if (instructorOptionsLoading.value) return
  if (instructorOptionsLoaded.value && !force) return

  instructorOptionsLoading.value = true
  try {
    const result = await getUsers({ role: 'instructor', size: -1 })
    instructorList.value = (result.items || []).map((item) => ({
      ...item,
      id: item.id,
      userId: item.id,
      name: item.nickname || item.username,
    }))
    instructorOptionsLoaded.value = true
  } catch (error) {
    instructorList.value = []
    instructorOptionsLoaded.value = false
    if (force) {
      message.warning(error?.message || '暂无权限加载教官候选列表')
    }
  } finally {
    instructorOptionsLoading.value = false
  }
}

async function ensureStudentCandidatesLoaded(force = false) {
  if (studentCandidatesLoading.value) return
  if (studentCandidatesLoaded.value && !force) return

  studentCandidatesLoading.value = true
  try {
    const result = await getUsers({ role: 'student', size: -1 })
    allUserList.value = result.items || []
    studentCandidatesLoaded.value = true
  } catch (error) {
    allUserList.value = []
    studentCandidatesLoaded.value = false
    if (force) {
      message.warning(error?.message || '暂无权限加载可添加学员列表')
    }
  } finally {
    studentCandidatesLoading.value = false
  }
}

onMounted(() => {
  loadTrainingDetail()
})

const activeTab = ref('overview')
const studentSearch = ref('')
const selectedSchedules = reactive({}) // { courseIdx: scheduleIdx }
const scheduleViewMode = ref('course')
const canEdit = computed(() => !!trainingData.canManageAll)
const canScheduleEdit = computed(() => !!trainingData.canEditCourses)
const canManageStudents = computed(() => !!trainingData.canManageAll)
const canManageEnrollmentApplications = computed(() => !!trainingData.canReviewEnrollments)
const canManageResources = computed(() => !!trainingData.canManageAll)
const canManageNotices = computed(() => !!trainingData.canManageAll)
const canExportStudents = computed(() => !!trainingData.canManageAll)
const canQuickCreateExam = computed(() => canEdit.value && authStore.hasPermission('CREATE_EXAM'))
const trainingManageTooltip = computed(() => {
  if (authStore.hasPermission('MANAGE_TRAINING')) return '当前培训班不在可管理范围内'
  if (authStore.hasPermission('UPDATE_TRAINING')) return '仅培训班班主任可执行该操作'
  return '需要 MANAGE_TRAINING，或具备 UPDATE_TRAINING 且为班主任'
})
const scheduleEditTooltip = computed(() => (
  canEdit.value ? '当前角色不能编辑课程安排' : trainingManageTooltip.value
))
const quickCreateExamTooltip = computed(() => (
  !authStore.hasPermission('CREATE_EXAM') ? '需要 CREATE_EXAM 权限' : trainingManageTooltip.value
))
const approveEnrollmentTooltip = computed(() => (
  !authStore.hasPermission('APPROVE_ENROLLMENT')
    ? '需要 APPROVE_ENROLLMENT 权限'
    : trainingManageTooltip.value
))
const rejectEnrollmentTooltip = computed(() => (
  !authStore.hasPermission('REJECT_ENROLLMENT')
    ? '需要 REJECT_ENROLLMENT 权限'
    : trainingManageTooltip.value
))
const currentSession = computed(() => trainingData.currentSession)
const showPublishWorkflowAction = computed(() => trainingData.status === 'upcoming' && trainingData.publishStatus !== 'published')
const showLockWorkflowAction = computed(() => trainingData.status === 'upcoming' && !trainingData.isLocked)
const showStartWorkflowAction = computed(() => trainingData.status === 'upcoming')
const showEndWorkflowAction = computed(() => trainingData.status === 'active')
const canPublishWorkflowAction = computed(() => canEdit.value && showPublishWorkflowAction.value)
const canLockWorkflowAction = computed(() => canEdit.value && showLockWorkflowAction.value)
const canStartWorkflowAction = computed(() => canEdit.value && showStartWorkflowAction.value)
const canEndWorkflowAction = computed(() => canEdit.value && showEndWorkflowAction.value)
const showWorkflowActionCard = computed(() => (
  !authStore.isStudent && (
    showPublishWorkflowAction.value ||
    showLockWorkflowAction.value ||
    showStartWorkflowAction.value ||
    showEndWorkflowAction.value
  )
))
const workflowSkipLabelMap = {
  published: '发布招生',
  locked: '锁定名单',
}
const examStatusLabelMap = { upcoming: '即将开始', active: '进行中', ended: '已结束' }
const examStatusColorMap = { upcoming: 'orange', active: 'green', ended: 'default' }
const examPurposeLabelMap = {
  class_assessment: '班内考核',
  final_assessment: '结业考核',
  quiz: '随堂测验',
}
const trainingExamSessions = computed(() => trainingData.examSessions || [])
const workflowStepItems = computed(() => (trainingData.workflowSteps || []).map((step) => ({
  title: step.title,
  description: step.description,
  status: step.status,
})))
const workflowCurrentIndex = computed(() => {
  const steps = trainingData.workflowSteps || []
  const processIndex = steps.findIndex((step) => step.status === 'process')
  if (processIndex >= 0) return processIndex
  const lastFinishIndex = [...steps].reverse().findIndex((step) => step.status === 'finish')
  return lastFinishIndex >= 0 ? steps.length - lastFinishIndex - 1 : 0
})
const scheduleStatusLabelMap = {
  pending: '未开始',
  checkin_open: '签到中',
  checkin_closed: '进行中',
  checkout_open: '签退中',
  completed: '已完成',
  skipped: '已跳过',
  missed: '已错过',
}
const scheduleStatusColorMap = {
  pending: 'default',
  checkin_open: 'blue',
  checkin_closed: 'gold',
  checkout_open: 'purple',
  completed: 'green',
  skipped: 'red',
  missed: 'volcano',
}
const currentSessionStatusLabel = computed(() => {
  if (!currentSession.value) return '无'
  return scheduleStatusLabelMap[currentSession.value.status] || currentSession.value.status
})
const scheduleRows = computed(() => (trainingData.courses || []).flatMap((course) =>
  (course.schedules || []).map((schedule) => ({
    sessionId: schedule.sessionId,
    date: schedule.date,
    timeRange: schedule.timeRange,
    status: schedule.status,
    courseName: course.name,
    instructorText: [
      course.primaryInstructorName || course.instructor || '未指定',
      course.assistantInstructorNames?.length ? `带教：${course.assistantInstructorNames.join('、')}` : '',
    ].filter(Boolean).join(' / '),
  }))
))

const trainingResources = ref([])
const resourceCandidates = ref([])
const selectedTrainingResourceId = ref(undefined)
const trainingResourceColumns = [
  { title: '标题', dataIndex: 'title', key: 'title' },
  { title: '类型', dataIndex: 'contentType', key: 'contentType', width: 120 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 120 },
  { title: '标签', key: 'tags' },
  { title: '操作', key: 'action', width: 100 },
]
const trainingResourceOptions = computed(() => (resourceCandidates.value || []).map(r => ({
  value: r.id,
  label: `${r.title}（${r.status || '-'}）`,
})))

watch(activeTab, (tab) => {
  if (tab === 'resources' && canManageResources.value) {
    loadResourceCandidates()
  }
})

const statusLabels = { active: '进行中', upcoming: '未开始', ended: '已结束' }
const statusColorMap = { active: 'green', upcoming: 'orange', ended: 'default' }

// 签到统计 (双轨 - 响应式 computed)
const startRecords = computed(() => (trainingData.checkinRecords || []).filter(r => !r.sessionKey || r.sessionKey === 'start'))
const courseRecords = computed(() => (trainingData.checkinRecords || []).filter(r => r.sessionKey && r.sessionKey !== 'start'))

// 开班签到率：分母为应签到人数 enrolledCount
const startCheckinRate = computed(() => {
  const total = trainingData.enrolledCount || trainingData.studentIds.length || 0
  if (total === 0) return 0
  const onTime = startRecords.value.filter(r => r.status === 'on_time').length
  const late = startRecords.value.filter(r => r.status === 'late').length
  return Math.round(((onTime + late) / total) * 100)
})

// 课程总签到率：分母为应签到总人次（课程场次数 × 应签人数）
const totalCourseRate = computed(() => {
  const enrolled = trainingData.enrolledCount || trainingData.studentIds.length || 0
  if (enrolled === 0) return 0
  // 计算总课程场次数
  let totalSessions = 0
  ;(trainingData.courses || []).forEach(c => {
    totalSessions += (c.schedules || []).length
  })
  if (totalSessions === 0) return 0
  const expectedTotal = totalSessions * enrolled
  const onTime = courseRecords.value.filter(r => r.status === 'on_time').length
  const late = courseRecords.value.filter(r => r.status === 'late').length
  return Math.round(((onTime + late) / expectedTotal) * 100)
})

const completeCount = computed(() => {
  const enrolled = trainingData.enrolledCount || 0
  return enrolled > 0 ? Math.floor(enrolled * (totalCourseRate.value / 100)) : 0
})
const isEnrolled = computed(() => trainingData.studentIds.includes(authStore.currentUser?.id))

const overviewStats = computed(() => [
  { label: '报名人数', value: trainingData.enrolledCount, color: '#003087' },
  { label: '班级容量', value: trainingData.capacity, color: '#555' },
  { label: '预计完成学员', value: completeCount, color: '#52c41a' },
  { label: '课程总学时', value: trainingData.courses.reduce((a, c) => a + (c.hours || 0), 0) || 0, color: '#faad14' },
])

// ===== 学员名单 =====
const mockStudents = computed(() => trainingData.studentIds.map(userId => {
  const u = userMap.value[userId] || {}
  const name = u.nickname || u.username || '未知学员'
  const policeId = u.policeId || String(userId)
  const unit = (u.departments && u.departments.length > 0) ? u.departments[0].name : '未分配'
  // 计算该学员所有的记录
  const records = (trainingData.checkinRecords || []).filter(cr => cr.studentId === userId)
  let cRate = 0
  if (records.length > 0) {
    const score = records.reduce((acc, r) => acc + (r.status === 'on_time' ? 100 : r.status === 'late' ? 80 : 0), 0)
    cRate = Math.round(score / records.length)
  }
  return { key: userId, name, policeId, unit, progress: Math.floor(Math.random() * 20 + 80), checkinRate: cRate }
}))

const filteredStudents = computed(() =>
  studentSearch.value ? mockStudents.value.filter(s => s.name.includes(studentSearch.value) || s.policeId.includes(studentSearch.value)) : mockStudents.value
)

function handleGlobalCheckin() {
  if (!currentSession.value?.sessionId) {
    message.warning('当前没有可签到的课次')
    return
  }
  router.push(`/training/${trainingData.id}/checkin/${currentSession.value.sessionId}`)
}

function goCurrentSessionCheckin() {
  handleGlobalCheckin()
}

function goTrainingExamManage() {
  router.push({
    name: 'ExamManage',
    query: {
      kind: 'training',
      trainingId: String(trainingData.id),
    },
  })
}

function quickCreateTrainingExam() {
  if (!canQuickCreateExam.value) return
  router.push({
    name: 'ExamManage',
    query: {
      kind: 'training',
      trainingId: String(trainingData.id),
      quickCreate: '1',
    },
  })
}

function getWorkflowMissingSteps(action) {
  const missingSteps = []
  if ((action === 'lock' || action === 'start') && trainingData.publishStatus !== 'published') {
    missingSteps.push('published')
  }
  if (action === 'start' && !trainingData.isLocked) {
    missingSteps.push('locked')
  }
  return missingSteps
}

async function executeWorkflowAction(requestFn, successMessage, errorMessage, skipSteps = []) {
  try {
    await requestFn(trainingId, skipSteps.length ? { skipSteps } : undefined)
    message.success(successMessage)
    await loadTrainingDetail()
  } catch (error) {
    message.error(error.message || errorMessage)
  }
}

function confirmWorkflowSkip(actionLabel, skipSteps, requestFn, successMessage, errorMessage) {
  const stepLabels = skipSteps.map((step) => workflowSkipLabelMap[step] || step)
  const joinedLabels = stepLabels.join('、')
  const lockTargetText = stepLabels.length > 1 ? '上述环节' : `${joinedLabels}环节`
  Modal.confirm({
    title: `是否跳过${joinedLabels}环节`,
    content: `当前操作将跳过${joinedLabels}环节，跳过后${lockTargetText}将锁定。`,
    okText: actionLabel,
    cancelText: '取消',
    async onOk() {
      await executeWorkflowAction(requestFn, successMessage, errorMessage, skipSteps)
    },
  })
}

async function handlePublish() {
  if (!canPublishWorkflowAction.value) return
  await executeWorkflowAction(publishTraining, '培训班已发布', '发布失败')
}

async function handleLock() {
  if (!canLockWorkflowAction.value) return
  const skipSteps = getWorkflowMissingSteps('lock')
  if (skipSteps.length) {
    confirmWorkflowSkip('锁定名单', skipSteps, lockTraining, '名单已锁定', '锁定失败')
    return
  }
  await executeWorkflowAction(lockTraining, '名单已锁定', '锁定失败')
}

async function handleStart() {
  if (!canStartWorkflowAction.value) return
  const skipSteps = getWorkflowMissingSteps('start')
  if (skipSteps.length) {
    confirmWorkflowSkip('开班', skipSteps, startTraining, '培训班已开班', '开班失败')
    return
  }
  await executeWorkflowAction(startTraining, '培训班已开班', '开班失败')
}

async function handleEnd() {
  if (!canEndWorkflowAction.value) return
  try {
    await endTraining(trainingId)
    message.success('培训班已结班')
    await loadTrainingDetail()
  } catch (error) {
    message.error(error.message || '结班失败')
  }
}

async function handleStartSessionCheckin() {
  if (!currentSession.value?.sessionId) return
  try {
    await startTrainingSessionCheckin(trainingId, currentSession.value.sessionId)
    message.success('已开始签到')
    await loadTrainingDetail()
  } catch (error) {
    message.error(error.message || '开始签到失败')
  }
}

async function handleEndSessionCheckin() {
  if (!currentSession.value?.sessionId) return
  try {
    await endTrainingSessionCheckin(trainingId, currentSession.value.sessionId)
    message.success('已结束签到')
    await loadTrainingDetail()
  } catch (error) {
    message.error(error.message || '结束签到失败')
  }
}

async function handleStartSessionCheckout() {
  if (!currentSession.value?.sessionId) return
  try {
    await startTrainingSessionCheckout(trainingId, currentSession.value.sessionId)
    message.success('已开始签退')
    await loadTrainingDetail()
  } catch (error) {
    message.error(error.message || '开始签退失败')
  }
}

async function handleEndSessionCheckout() {
  if (!currentSession.value?.sessionId) return
  try {
    await endTrainingSessionCheckout(trainingId, currentSession.value.sessionId)
    message.success('已结束签退')
    await loadTrainingDetail()
  } catch (error) {
    message.error(error.message || '结束签退失败')
  }
}

function handleSkipCurrentSession() {
  if (!currentSession.value?.sessionId) return
  Modal.confirm({
    title: '跳过当前课程',
    content: `确定跳过当前课程「${currentSession.value.courseName}」吗？`,
    okText: '跳过',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        await skipTrainingSession(trainingId, currentSession.value.sessionId, {})
        message.success('已跳过当前课程')
        await loadTrainingDetail()
      } catch (error) {
        message.error(error.message || '跳过课程失败')
      }
    },
  })
}

const baseStudentColumns = [
  { title: '姓名', dataIndex: 'name', key: 'name' },
  { title: '工号', dataIndex: 'policeId', key: 'policeId' },
  { title: '单位', dataIndex: 'unit', key: 'unit' },
  { title: '学习进度', key: 'progress', width: 120 },
  { title: '签到率', key: 'checkin', width: 80 },
]
const studentColumnsWithAction = computed(() =>
  !authStore.isStudent ? [...baseStudentColumns, { title: '操作', key: 'action', width: 80 }] : baseStudentColumns
)

const showEnrollmentApplicationModal = ref(false)
const enrollmentApplicationsLoading = ref(false)
const enrollmentApplications = ref([])
const showRejectEnrollmentModal = ref(false)
const rejectEnrollmentTarget = ref(null)
const rejectEnrollmentNote = ref('')

const pendingEnrollmentApplications = computed(() => (
  (enrollmentApplications.value || []).filter((item) => item.status === 'pending')
))
const pendingEnrollmentCount = computed(() => pendingEnrollmentApplications.value.length)

function goTraineeDetail(userId) {
  router.push({ name: 'TraineeDetail', params: { id: userId } })
}

async function removeStudent(userId) {
  if (!canManageStudents.value) return
  const nextStudentIds = trainingData.studentIds.filter((item) => item !== userId)
  try {
    await submitTrainingUpdate({ studentIds: nextStudentIds })
    message.success('已移除该学员')
    await loadTrainingDetail()
  } catch {
    message.error('移除学员失败')
  }
}

async function loadEnrollmentApplications() {
  enrollmentApplicationsLoading.value = true
  try {
    const result = await getEnrollments(trainingId, { size: -1 })
    enrollmentApplications.value = result.items || []
  } catch (error) {
    message.error(error.message || '加载报名申请失败')
  } finally {
    enrollmentApplicationsLoading.value = false
  }
}

async function openEnrollmentApplicationModal() {
  if (!canManageEnrollmentApplications.value) return
  showEnrollmentApplicationModal.value = true
  await loadEnrollmentApplications()
}

async function handleApproveEnrollment(record) {
  if (!canManageEnrollmentApplications.value || !authStore.hasPermission('APPROVE_ENROLLMENT')) return
  try {
    await approveEnrollment(trainingId, record.id)
    message.success('已通过报名申请')
    await Promise.all([loadEnrollmentApplications(), loadTrainingDetail()])
  } catch (error) {
    message.error(error.message || '审批失败')
  }
}

function openRejectEnrollmentModal(record) {
  if (!canManageEnrollmentApplications.value || !authStore.hasPermission('REJECT_ENROLLMENT')) return
  rejectEnrollmentTarget.value = record
  rejectEnrollmentNote.value = record?.note || ''
  showRejectEnrollmentModal.value = true
}

function closeRejectEnrollmentModal() {
  showRejectEnrollmentModal.value = false
  rejectEnrollmentTarget.value = null
  rejectEnrollmentNote.value = ''
}

async function submitRejectEnrollment() {
  if (!rejectEnrollmentTarget.value) return
  if (!rejectEnrollmentNote.value.trim()) {
    message.warning('请输入拒绝理由')
    return
  }
  try {
    await rejectEnrollment(trainingId, rejectEnrollmentTarget.value.id, rejectEnrollmentNote.value.trim())
    message.success('已拒绝报名申请')
    closeRejectEnrollmentModal()
    await Promise.all([loadEnrollmentApplications(), loadTrainingDetail()])
  } catch (error) {
    message.error(error.message || '拒绝失败')
  }
}

// ===== 添加学员弹窗 =====
const showStudentModal = ref(false)
const addStudentSearch = ref('')
const selectedStudentKeys = ref([])

const availableStudents = computed(() => {
  const existing = new Set(trainingData.studentIds)
  let list = allUserList.value.filter(u => !existing.has(u.id)).map(u => ({
    id: u.id,
    name: u.nickname || u.username,
    policeId: u.policeId || '',
    unit: (u.departments && u.departments.length > 0) ? u.departments[0].name : '未分配'
  }))
  if (addStudentSearch.value) {
    const q = addStudentSearch.value.toLowerCase()
    list = list.filter(u => u.name.includes(q) || u.policeId.toLowerCase().includes(q))
  }
  return list
})

const addStudentColumns = [
  { title: '姓名', dataIndex: 'name', key: 'name' },
  { title: '工号', dataIndex: 'policeId', key: 'policeId' },
  { title: '单位', dataIndex: 'unit', key: 'unit' },
]

async function openStudentModal() {
  if (!canManageStudents.value) return
  showStudentModal.value = true
  await ensureStudentCandidatesLoaded(true)
}

async function addSelectedStudents() {
  if (!canManageStudents.value) return
  if (selectedStudentKeys.value.length === 0) { message.warning('请先选择要添加的学员'); return }
  const merged = new Set([...trainingData.studentIds, ...selectedStudentKeys.value])
  try {
    await submitTrainingUpdate({ studentIds: Array.from(merged) })
    await loadTrainingDetail()
    message.success(`已添加 ${selectedStudentKeys.value.length} 名学员`)
    selectedStudentKeys.value = []
    addStudentSearch.value = ''
    showStudentModal.value = false
  } catch {
    message.error('添加学员失败')
  }
}

// ===== 课程 CRUD =====

const showCourseModal = ref(false)
const editingCourseIdx = ref(null)
const dateAddMode = ref('single')
const tempDate = ref(null)
const tempDateRange = ref([])
const tempTimeRange = ref([])

// 'schedules' will store objects like { date: 'YYYY-MM-DD', timeRange: 'HH:mm~HH:mm', hours: 2 }
const courseForm = reactive({
  name: '',
  instructor: '',
  instructorId: null,
  assistantInstructorIds: [],
  hours: 0,
  type: 'theory',
  schedules: [],
})

function onInstructorChange(userId) {
  const inst = instructorList.value.find(i => i.userId == userId)
  if (inst) courseForm.instructor = inst.name
}

function calcTotalHours() {
  courseForm.hours = Math.round(courseForm.schedules.reduce((sum, sch) => sum + (sch.hours || 0), 0))
}

function addCourseSchedule() {
  if (!tempTimeRange.value || tempTimeRange.value.length !== 2) {
    message.warning('请选择上课时段')
    return
  }

  const tStr1 = tempTimeRange.value[0].format('HH:mm')
  const tStr2 = tempTimeRange.value[1].format('HH:mm')
  const tRange = `${tStr1}~${tStr2}`

  const startT = dayjs(`2000-01-01 ${tStr1}`)
  const endT = dayjs(`2000-01-01 ${tStr2}`)
  const diffMs = endT.diff(startT)
  const hrs = diffMs > 0 ? Math.round(diffMs / (1000 * 60 * 60)) : 0

  if (hrs <= 0) {
    message.warning('时长太短或结束时间早于开始时间')
    return
  }

  let datesToAdd = []
  if (dateAddMode.value === 'single') {
    if (!tempDate.value) { message.warning('请选择上课日期'); return }
    datesToAdd.push(tempDate.value.format('YYYY-MM-DD'))
  } else {
    if (!tempDateRange.value || tempDateRange.value.length !== 2) { message.warning('请选择上课日期范围'); return }
    let current = tempDateRange.value[0]
    const end = tempDateRange.value[1]
    while (current.isBefore(end) || current.isSame(end, 'day')) {
      datesToAdd.push(current.format('YYYY-MM-DD'))
      current = current.add(1, 'day')
    }
  }

  let addedCount = 0
  datesToAdd.forEach(dStr => {
    // Avoid exact duplicate
    const exists = courseForm.schedules.some(s => s.date === dStr && s.timeRange === tRange)
    if (!exists) {
      courseForm.schedules.push({ date: dStr, timeRange: tRange, hours: hrs })
      addedCount++
    }
  })

  if (addedCount > 0) {
    courseForm.schedules.sort((a, b) => {
      const db = a.date.localeCompare(b.date)
      if (db !== 0) return db
      return a.timeRange.localeCompare(b.timeRange)
    })
    calcTotalHours()
    message.success(`成功添加 ${addedCount} 节排课`)
  } else {
    message.warning('所选排课已存在，未重复添加')
  }

  // Clear temps
  tempDate.value = null
  tempDateRange.value = []
  tempTimeRange.value = []
}

function removeCourseSchedule(idx) {
  courseForm.schedules.splice(idx, 1)
  calcTotalHours()
}

function openCourseModal(idx = null) {
  if (!canScheduleEdit.value) return
  ensureInstructorOptionsLoaded(true)
  editingCourseIdx.value = idx
  tempDate.value = null
  tempDateRange.value = []
  tempTimeRange.value = []
  dateAddMode.value = 'single'
  
  if (idx !== null && trainingData.courses[idx]) {
    const c = JSON.parse(JSON.stringify(trainingData.courses[idx]))
    const inst = instructorList.value.find(i => i.userId === c.primaryInstructorId || i.name === c.instructor)
    Object.assign(courseForm, {
      name: c.name,
      instructor: c.instructor,
      instructorId: (c.primaryInstructorId || inst?.userId) ?? null,
      assistantInstructorIds: c.assistantInstructorIds || [],
      hours: c.hours,
      type: c.type,
      schedules: c.schedules || [],
    })

    // Migrate old legacy formats into 'schedules' array (if course has dates but no schedules)
    if (courseForm.schedules.length === 0) {
      if (c.dates && c.timeRange) {
        let hrs = 0
        const [st, ed] = c.timeRange.split('~')
        if (st && ed) {
          const diff = dayjs(`2000-01-01 ${ed}`).diff(dayjs(`2000-01-01 ${st}`))
          if (diff > 0) hrs = Number((diff / (1000 * 60 * 60)).toFixed(1))
        }
        c.dates.forEach(d => {
          courseForm.schedules.push({ date: d, timeRange: c.timeRange, hours: hrs })
        })
      } else if (c.date && c.timeRange) {
        courseForm.schedules.push({ date: c.date, timeRange: c.timeRange, hours: c.hours })
      } else if (c.startTime && c.endTime) {
         courseForm.schedules.push({ 
           date: dayjs(c.startTime).format('YYYY-MM-DD'), 
           timeRange: `${dayjs(c.startTime).format('HH:mm')}~${dayjs(c.endTime).format('HH:mm')}`, 
           hours: c.hours 
        })
      }
    }
  } else {
    Object.assign(courseForm, { name: '', instructor: '', instructorId: null, assistantInstructorIds: [], hours: 0, type: 'theory', schedules: [] })
  }
  showCourseModal.value = true
}

async function saveCourse() {
  if (!canScheduleEdit.value) return
  if (!courseForm.name || !courseForm.instructor || courseForm.schedules.length === 0) { 
    message.warning('请填写课程名称、教官，并至少添加一节排课')
    return 
  }
  const courseData = { ...courseForm }
  courseData.primaryInstructorId = courseForm.instructorId
  delete courseData.instructorId
  const nextCourses = [...trainingData.courses]
  if (editingCourseIdx.value !== null) {
    nextCourses.splice(editingCourseIdx.value, 1, courseData)
  } else {
    nextCourses.push(courseData)
  }
  try {
    await submitTrainingUpdate({ courses: nextCourses })
    message.success(editingCourseIdx.value !== null ? '课程已更新' : '课程已添加')
    showCourseModal.value = false
    await loadTrainingDetail()
  } catch {
    message.error('课程保存失败')
  }
}

function removeCourse(idx) {
  if (!canScheduleEdit.value) return
  Modal.confirm({
    title: '确认删除', content: `确定删除课程「${trainingData.courses[idx]?.name}」吗？`,
    okText: '删除', okType: 'danger', cancelText: '取消',
    onOk: async () => {
      const nextCourses = [...trainingData.courses]
      nextCourses.splice(idx, 1)
      try {
        await submitTrainingUpdate({ courses: nextCourses })
        message.success('课程已删除')
        await loadTrainingDetail()
      } catch {
        message.error('课程删除失败')
      }
    }
  })
}

// ===== 编辑班级信息 =====
const showEditModal = ref(false)
const editFormDates = ref([null, null]) // dayjs values for date pickers
const editForm = reactive({
  name: trainingData.name, startDate: trainingData.startDate, endDate: trainingData.endDate,
  location: trainingData.location, instructorId: trainingData.instructorId || null, instructorName: trainingData.instructorName,
  capacity: trainingData.capacity, status: trainingData.status, description: trainingData.description || '',
  enrollmentRequiresApproval: true,
})

function syncEditFormFromTraining() {
  editForm.name = trainingData.name
  editForm.startDate = trainingData.startDate
  editForm.endDate = trainingData.endDate
  editForm.location = trainingData.location
  editForm.instructorId = trainingData.instructorId || null
  editForm.instructorName = trainingData.instructorName
  editForm.capacity = trainingData.capacity
  editForm.status = trainingData.status
  editForm.description = trainingData.description || ''
  editForm.enrollmentRequiresApproval = trainingData.enrollmentRequiresApproval !== false
  editFormDates.value = [
    trainingData.startDate ? dayjs(trainingData.startDate) : null,
    trainingData.endDate ? dayjs(trainingData.endDate) : null,
  ]
}

function onEditInstructorChange(userId) {
  const inst = instructorList.value.find(i => i.userId == userId)
  if (inst) editForm.instructorName = inst.name
}

async function openEditModal() {
  if (!canEdit.value) return
  showEditModal.value = true
  await ensureInstructorOptionsLoaded(true)
}

async function saveClassInfo() {
  if (!canEdit.value) return
  if (!editForm.name || !editForm.startDate || !editForm.endDate || !editForm.location) { message.warning('请填写必填项'); return }
  try {
    await submitTrainingUpdate({ ...editForm })
    message.success('班级信息已更新')
    showEditModal.value = false
    await loadTrainingDetail()
  } catch {
    message.error('班级信息更新失败')
  }
}

const showNoticeModal = ref(false)
const editingNoticeId = ref(null)
const noticeForm = reactive({ title: '', content: '' })

function openNoticeModal() {
  if (!canManageNotices.value) return
  editingNoticeId.value = null
  noticeForm.title = ''
  noticeForm.content = ''
  showNoticeModal.value = true
}

function editNotice(notice) {
  if (!canManageNotices.value) return
  editingNoticeId.value = notice.id
  noticeForm.title = notice.title
  noticeForm.content = notice.content
  showNoticeModal.value = true
}

async function deleteNotice(id) {
  if (!canManageNotices.value) return
  try {
    await apiDeleteNotice(id)
    notices.value = notices.value.filter(n => n.id !== id)
    message.success('公告已删除')
  } catch {
    message.error('删除失败')
  }
}

async function saveNotice() {
  if (!canManageNotices.value) return
  if (!noticeForm.title || !noticeForm.content) { message.warning('请填写公告标题和内容'); return }

  try {
    if (editingNoticeId.value) {
      await apiUpdateNotice(editingNoticeId.value, { title: noticeForm.title, content: noticeForm.content })
      const localNotice = notices.value.find(n => n.id === editingNoticeId.value)
      if (localNotice) {
        localNotice.title = noticeForm.title
        localNotice.content = noticeForm.content
      }
      message.success('公告已更新')
    } else {
      const res = await apiCreateNotice({ title: noticeForm.title, content: noticeForm.content, type: 'training', trainingId: trainingId })
      notices.value.unshift({ ...res, time: formatDateTime(res.createdAt, '') })
      message.success('公告已发布')
    }
    showNoticeModal.value = false
  } catch {
    message.error('操作失败')
  }
}

async function loadResourceCandidates() {
  if (!canManageResources.value) return
  try {
    const res = await getResources({ page: 1, size: 200, status: 'published' })
    resourceCandidates.value = res.items || []
  } catch {
    resourceCandidates.value = []
  }
}

async function bindSelectedTrainingResource() {
  if (!canManageResources.value) return
  if (!selectedTrainingResourceId.value) {
    message.warning('请选择资源')
    return
  }
  try {
    const resource = await bindTrainingResource(trainingId, {
      resourceId: selectedTrainingResourceId.value,
      usageType: 'required',
      sortOrder: 0,
    })
    message.success('资源绑定成功')
    selectedTrainingResourceId.value = undefined
    trainingResources.value = [
      ...trainingResources.value.filter((item) => item.id !== resource.id),
      resource,
    ]
  } catch (e) {
    message.error(e.message || '资源绑定失败')
  }
}

async function removeTrainingResource(resourceId) {
  if (!canManageResources.value) return
  try {
    await unbindTrainingResource(trainingId, resourceId)
    message.success('资源解绑成功')
    trainingResources.value = trainingResources.value.filter((item) => item.id !== resourceId)
  } catch (e) {
    message.error(e.message || '资源解绑失败')
  }
}

function exportMsg() {
  if (!canExportStudents.value) return
  if (filteredStudents.value.length === 0) {
    message.warning('暂无学员数据可导出')
    return
  }
  
  // 构造 CSV 内容
  const metaRows = [
    ['培训班名称', trainingData.name || ''],
    ['培训地点', trainingData.location || ''],
    ['培训基地', trainingData.trainingBaseName || '手动输入地点'],
    ['部门', trainingData.departmentName || '未设置'],
    ['警种', trainingData.policeTypeName || '未设置'],
    ['准入考试', trainingData.admissionExamTitle || '无'],
    [],
  ]
  const headers = ['姓名', '警号/工号', '单位', '学习进度', '总签到率']
  const rows = filteredStudents.value.map(s => [
    s.name, 
    `\t${s.policeId}`, // 防止长数字科学计数法
    s.unit, 
    `${s.progress}%`, 
    `${s.checkinRate}%`
  ])
  
  const csvContent = [...metaRows, headers, ...rows].map(e => e.join(",")).join("\n")
  const blob = new Blob(["\ufeff" + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement("a")
  const url = URL.createObjectURL(blob)
  link.setAttribute("href", url)
  link.setAttribute("download", `${trainingData.name}_学员名单_${dayjs().format('YYYYMMDD')}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  message.success('学员名单及签到数据已导出下载')
}
</script>

<style scoped>
.training-detail-page { padding: 0; }
.workflow-header { margin-bottom: 16px; }
.workflow-header :deep(.ant-steps) { width: 100%; }
.workflow-action-list { width: 100%; }
.exam-plan-section { display: flex; flex-direction: column; gap: 12px; }
.exam-plan-title { font-size: 14px; font-weight: 600; color: #1f2937; }
.exam-plan-list { display: flex; flex-direction: column; gap: 12px; }
.exam-plan-card { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; padding: 16px; border: 1px solid #eef2f7; border-radius: 10px; background: #fafcff; }
.admission-plan-card { background: #f5f9ff; border-color: #dbeafe; }
.exam-plan-main { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.exam-plan-name { font-size: 15px; font-weight: 600; color: #111827; }
.exam-plan-meta { display: flex; flex-wrap: wrap; gap: 8px 16px; color: #6b7280; font-size: 13px; }
.training-banner { padding: 24px; border-radius: 8px; margin-bottom: 4px; }
.training-banner.status-active { background: linear-gradient(135deg, #001a50, #003087); }
.training-banner.status-upcoming { background: linear-gradient(135deg, #78350f, #b45309); }
.training-banner.status-ended { background: linear-gradient(135deg, #374151, #6b7280); }
.status-tag { margin-bottom: 8px; }
.training-title { color: #fff; font-size: 20px; margin: 8px 0; }
.training-meta-row { display: flex; gap: 20px; color: rgba(255,255,255,0.8); font-size: 13px; flex-wrap: wrap; }
.secondary-meta { color: rgba(255,255,255,0.92); margin-bottom: 8px; }
.overview-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
.ov-stat { text-align: center; padding: 16px; background: #f8f9ff; border-radius: 8px; }
.ov-num { font-size: 28px; font-weight: 700; }
.ov-label { font-size: 12px; color: #888; margin-top: 4px; }
.training-base-info { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 16px; margin-bottom: 12px; }
.info-row { display: flex; flex-direction: column; gap: 4px; padding: 12px 14px; background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 8px; }
.info-label { font-size: 12px; color: #6b7280; }
.info-value { font-size: 14px; color: #111827; font-weight: 500; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-header h4 { margin: 0; color: #333; }
.course-item { display: flex; justify-content: space-between; align-items: flex-start; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
.current-course-card { background: #f8fbff; border: 1px solid #dbeafe; border-radius: 8px; padding: 16px; }
.ci-name { font-size: 14px; font-weight: 500; }
.ci-instructor { font-size: 12px; color: #888; }
.ci-time { margin-top: 6px; display: flex; flex-direction: column; gap: 4px; }
.sch-item { font-size: 12px; color: #666; background: #f5f5f5; padding: 2px 6px; border-radius: 4px; display: inline-block; width: max-content; }
.ci-hours { font-size: 14px; color: var(--police-primary); font-weight: 600; margin-right: 8px; margin-top: 2px; }
.ci-right { display: flex; align-items: center; gap: 4px; }
.training-desc { background: rgba(255,255,255,0.1); padding: 12px 16px; border-radius: 6px; color: rgba(255,255,255,0.9); font-size: 13px; line-height: 1.5; margin-top: 12px; }
.custom-notice-collapse { background: transparent; }
.custom-notice-collapse :deep(.ant-collapse-item) { border-bottom: 1px solid #f0f0f0; background: #fafafa; margin-bottom: 8px; border-radius: 6px; overflow: hidden; }
.custom-notice-collapse :deep(.ant-collapse-header) { font-weight: 600; color: #1a1a1a; padding: 12px 16px; }
.notice-time { font-size: 12px; color: #888; font-weight: normal; }
.notice-content { font-size: 14px; color: #555; line-height: 1.6; margin: 0; padding: 4px 0; }
.checkin-summary { display: flex; align-items: center; gap: 20px; }
.checkin-detail { display: flex; flex-direction: column; gap: 8px; }
.cd-item { font-size: 14px; }
.cd-item.green { color: #52c41a; }
.cd-item.orange { color: #faad14; }
.cd-item.red { color: #ff4d4f; }

.course-schedule-select {
  width: 260px;
}

.student-search-input {
  width: 240px;
}

.training-resource-select {
  width: 320px;
}

.schedule-editor-box {
  border: 1px dashed #d9d9d9;
  padding: 12px;
  border-radius: 6px;
}

.schedule-mode-row {
  margin-bottom: 8px;
}

.schedule-editor-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.schedule-date-picker {
  flex: 1;
}

.schedule-time-range {
  width: 220px;
}

.ci-rate {
  color: #52c41a;
  min-width: 60px;
}

@media (max-width: 768px) {
  .workflow-header {
    margin-bottom: 12px;
  }
  .overview-stats { grid-template-columns: 1fr 1fr !important; }
  .training-base-info { grid-template-columns: 1fr; }
  .training-banner { padding: 16px !important; }
  .training-title { font-size: 18px !important; }
  .section-header {
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }
  .course-item {
    flex-direction: column;
    gap: 8px;
  }
  .exam-plan-card {
    flex-direction: column;
  }
  .ci-right {
    width: 100%;
    flex-wrap: wrap;
    justify-content: flex-start;
  }
  .ci-rate {
    min-width: 0;
  }
  .course-schedule-select,
  .student-search-input,
  .training-resource-select {
    width: 100%;
  }
  .schedule-editor-row {
    flex-wrap: wrap;
  }
  .schedule-date-picker,
  .schedule-time-range,
  .schedule-editor-row :deep(.ant-btn) {
    width: 100%;
  }
  .checkin-summary {
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px;
  }
}
</style>
