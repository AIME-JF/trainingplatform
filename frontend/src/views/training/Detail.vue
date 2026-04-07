<template>
  <div class="training-detail-page">
    <div class="page-header-row">
      <a-breadcrumb class="page-breadcrumb">
        <a-breadcrumb-item @click="$router.push('/training')" style="cursor:pointer;color:var(--police-primary)">培训班管理</a-breadcrumb-item>
        <a-breadcrumb-item>{{ trainingData.name }}</a-breadcrumb-item>
      </a-breadcrumb>
      <a-button shape="circle" class="tour-trigger-button" title="查看页面引导" @click="openDetailTour">
        <template #icon><QuestionCircleOutlined /></template>
      </a-button>
    </div>

    <a-card :bordered="false" class="workflow-card" style="margin-bottom:16px">
      <div ref="workflowHeaderRef" class="workflow-header">
        <a-steps :current="workflowCurrentIndex" :items="workflowStepItems" size="small" />
      </div>
    </a-card>

    <!-- Banner with next action on right -->
    <div class="training-banner-bar">
      <div ref="trainingBannerRef" class="training-banner" :class="'status-' + trainingData.status">
        <div class="banner-content">
          <div class="training-title-row">
            <h2 class="training-title">{{ trainingData.name }}</h2>
            <a-tag :color="statusColorMap[trainingData.status]" class="status-tag">{{ statusLabels[trainingData.status] }}</a-tag>
          </div>
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
      <div class="banner-action" v-if="recommendedAction" ref="nextStepCardRef">
        <TrainingNextActionCard :recommended-action="recommendedAction" />
      </div>
    </div>

    <!-- Sidebar + Content -->
    <div class="detail-layout">
      <div class="detail-sidebar">
        <a-menu
          mode="inline"
          theme="light"
          v-model:selectedKeys="sidebarSelectedKeys"
          v-model:openKeys="sidebarOpenKeys"
          :style="{ border: 'none' }"
          @click="handleSidebarClick"
        >
          <a-menu-item key="overview">
            <template #icon><AppstoreOutlined /></template>
            班级概览
          </a-menu-item>
          <a-sub-menu key="students-group" v-if="!authStore.isStudent">
            <template #icon><TeamOutlined /></template>
            <template #title>学员管理</template>
            <a-menu-item key="enrollment-applications">
              <a-badge :dot="pendingEnrollmentCount > 0" :offset="[6, -2]">申请列表</a-badge>
            </a-menu-item>
            <a-menu-item key="students">学员名单</a-menu-item>
          </a-sub-menu>
          <a-menu-item key="schedule">
            <template #icon><ReadOutlined /></template>
            课程管理
          </a-menu-item>
          <a-menu-item key="resources">
            <template #icon><FolderOutlined /></template>
            资源
          </a-menu-item>
          <a-sub-menu key="exams-group">
            <template #icon><FileTextOutlined /></template>
            <template #title>考试测评</template>
            <a-menu-item key="exams">考试安排</a-menu-item>
          </a-sub-menu>
          <a-sub-menu key="config-group" v-if="!authStore.isStudent">
            <template #icon><SettingOutlined /></template>
            <template #title>班级配置</template>
            <a-menu-item key="basic-info">基本信息</a-menu-item>
            <a-menu-item key="scheduleRules">排课规则</a-menu-item>
            <a-menu-item key="courseChangeLogs" v-if="trainingData.canViewCourseChangeLogs">课程变更记录</a-menu-item>
          </a-sub-menu>
        </a-menu>
      </div>
      <div class="detail-content">
        <a-card :bordered="false">
          <!-- 班级概览 -->
          <div v-show="activeTab === 'overview'">
            <TrainingOverviewContent
              ref="overviewContentRef"
              :overview-stats="overviewStats"
              :show-overview-setup-guide="showOverviewSetupGuide"
              :setup-guide-items="setupGuideItems"
              :training-data="trainingData"
              :show-overview-current-course="showOverviewCurrentCourse"
              :current-session="currentSession"
              :current-session-status-label="currentSessionStatusLabel"
              :is-enrolled="isEnrolled"
              @go-schedule="activeTab = 'schedule'"
              @guide-click="handleGuideClick"
              @start-session-checkout="handleStartSessionCheckout"
              @end-session-checkout="handleEndSessionCheckout"
              @go-current-session-checkout="$router.push({ name: 'Checkout', params: { id: trainingData.id, sessionKey: currentSession?.sessionId } })"
              @skip-current-session="handleSkipCurrentSession"
            />
            <div ref="noticeCardRef" style="margin-top:16px">
              <TrainingNoticeCard
                :notices="notices"
                :is-student="authStore.isStudent"
                :can-manage-notices="canManageNotices"
                :training-manage-tooltip="trainingManageTooltip"
                @open-notice-modal="openNoticeModal"
                @edit-notice="editNotice"
                @delete-notice="deleteNotice"
              />
            </div>
            <div style="margin-top:16px">
              <TrainingAttendanceStatsCard :start-checkin-rate="startCheckinRate" :total-course-rate="totalCourseRate" />
            </div>
          </div>

          <!-- 申请列表 -->
          <div v-show="activeTab === 'enrollment-applications'" v-if="!authStore.isStudent">
            <div class="content-section-header">
              <h3>申请列表</h3>
              <a-button size="small" @click="loadEnrollmentApplications">刷新</a-button>
            </div>
            <div class="page-sub" style="margin-bottom:16px">待审核申请 {{ pendingEnrollmentCount }} 人</div>
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
              <a-table-column title="身份证号" data-index="idCardNumber" key="idCardNumber" width="180" />
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
          </div>

          <!-- 学员名单 -->
          <div v-show="activeTab === 'students'" v-if="!authStore.isStudent">
            <div class="content-section-header">
              <h3>学员名单</h3>
              <a-space>
                <a-button @click="openStudentImportModal">导入学员</a-button>
                <a-button type="primary" @click="openStudentModal"><PlusOutlined /> 添加学员</a-button>
              </a-space>
            </div>
            <TrainingStudentsContent
              :student-search="studentSearch"
              :filtered-students="filteredStudents"
              :student-columns-with-action="studentColumnsWithAction"
              :can-manage-enrollment-applications="canManageEnrollmentApplications"
              :can-manage-students="canManageStudents"
              :show-action-buttons="false"
              :training-manage-tooltip="trainingManageTooltip"
              :pending-enrollment-count="pendingEnrollmentCount"
              @update:studentSearch="studentSearch = $event"
              @go-trainee-detail="goTraineeDetail"
              @remove-student="removeStudent"
            />
          </div>

          <!-- 课程管理 -->
          <div v-show="activeTab === 'schedule'">
            <div class="content-section-header">
              <h3>课程管理</h3>
              <a-space>
                <a-button @click="openAiScheduleTask">智能排课</a-button>
                <a-button @click="openScheduleImportModal">导入课表</a-button>
                <a-button type="primary" @click="openCourseModal()"><PlusOutlined /> 添加课程</a-button>
              </a-space>
            </div>
            <TrainingScheduleContent
              ref="scheduleContentRef"
              :training-data="trainingData"
              :show-action-buttons="false"
              :is-student="authStore.isStudent"
              :schedule-view-mode="scheduleViewMode"
              :can-schedule-edit="canScheduleEdit"
              :schedule-edit-tooltip="scheduleEditTooltip"
              :schedule-rows="scheduleRows"
              :current-session="currentSession"
              :schedule-status-color-map="scheduleStatusColorMap"
              :schedule-status-label-map="scheduleStatusLabelMap"
              @update:scheduleViewMode="scheduleViewMode = $event"
              @open-ai-schedule="openAiScheduleTask"
              @open-schedule-import="openScheduleImportModal"
              @add-course="openCourseModal()"
              @edit-course="openCourseModal"
              @edit-course-sessions="openCourseSessionModal"
              @remove-course="removeCourse"
              @edit-schedule="openScheduleModal"
              @remove-schedule="removeSchedule"
              @start-session-checkout="handleStartSessionCheckout"
              @end-session-checkout="handleEndSessionCheckout"
              @skip-current-session="handleSkipCurrentSession"
            />
          </div>

          <!-- 资源 -->
          <div v-show="activeTab === 'resources'">
            <div class="content-section-header">
              <h3>课程资源</h3>
            </div>
            <TrainingResourcesContent
              :training-data="trainingData"
              :active="activeTab === 'resources'"
            />
          </div>

          <!-- 考试安排 -->
          <div v-show="activeTab === 'exams'">
            <TrainingExamsContent
              :is-student="authStore.isStudent"
              :can-quick-create-exam="canQuickCreateExam"
              :quick-create-exam-tooltip="quickCreateExamTooltip"
              :training-exam-sessions="trainingExamSessions"
              :exam-purpose-label-map="examPurposeLabelMap"
              :exam-status-color-map="examStatusColorMap"
              :exam-status-label-map="examStatusLabelMap"
              :format-date-time="formatDateTime"
              @quick-create="quickCreateTrainingExam"
              @go-manage="goTrainingExamManage"
            />
          </div>

          <!-- 基本信息 -->
          <div v-show="activeTab === 'basic-info'" v-if="!authStore.isStudent">
            <h3 style="margin:0 0 16px;font-size:16px;font-weight:600;color:#1f1f1f">基本信息</h3>
            <a-form layout="vertical" class="basic-info-form">
              <a-form-item label="培训班名称" required>
                <a-input v-model:value="editForm.name" />
              </a-form-item>
              <a-row :gutter="12">
                <a-col :span="12">
                  <a-form-item label="培训类型">
                    <a-select v-model:value="editForm.type" placeholder="请选择培训类型">
                      <a-select-option v-for="t in trainingTypeOptions" :key="t.code" :value="t.code">{{ t.name }}</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="班级容量">
                    <a-input-number v-model:value="editForm.capacity" :min="1" style="width:100%" />
                  </a-form-item>
                </a-col>
              </a-row>
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
              <a-form-item label="培训地点">
                <a-input v-model:value="editForm.location" placeholder="手动输入地点，或下方选择培训基地" />
              </a-form-item>
              <a-row :gutter="12">
                <a-col :span="12">
                  <a-form-item label="主管/班主任">
                    <a-select
                      v-model:value="editForm.instructorId"
                      placeholder="从教官库选定班主任"
                      show-search
                      option-filter-prop="label"
                      allow-clear
                      @change="onEditInstructorChange"
                    >
                      <a-select-option
                        v-for="inst in instructorList"
                        :key="inst.userId"
                        :value="inst.userId"
                        :label="inst.name"
                      >
                        {{ inst.name }}{{ inst.title ? ' · ' + inst.title : '' }}
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="培训基地">
                    <a-select v-model:value="editForm.trainingBaseId" placeholder="选择培训基地" allow-clear>
                      <a-select-option v-for="b in trainingBaseOptions" :key="b.id" :value="b.id">{{ b.name }}</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
              </a-row>
              <a-row :gutter="12">
                <a-col :span="12">
                  <a-form-item label="所属部门">
                    <a-select v-model:value="editForm.departmentId" placeholder="选择部门" show-search option-filter-prop="label" allow-clear>
                      <a-select-option v-for="d in departmentOptions" :key="d.id" :value="d.id" :label="d.name">{{ d.name }}</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="警种">
                    <a-select v-model:value="editForm.policeTypeId" placeholder="选择警种" allow-clear>
                      <a-select-option v-for="p in policeTypeOptions" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
                    </a-select>
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
                <a-textarea v-model:value="editForm.description" :rows="3" />
              </a-form-item>
              <div style="text-align:right">
                <a-button type="primary" @click="saveClassInfo">保存</a-button>
              </div>
            </a-form>
          </div>

          <!-- 排课规则 -->
          <div v-show="activeTab === 'scheduleRules'" v-if="!authStore.isStudent">
            <TrainingScheduleRuleContent
              :schedule-rule-config="trainingData.scheduleRuleConfig"
              :can-edit="canScheduleEdit"
              :edit-tooltip="scheduleEditTooltip"
              :saving="scheduleRuleSaving"
              @save="saveScheduleRuleConfig"
            />
          </div>

          <!-- 课程变更记录 -->
          <div v-show="activeTab === 'courseChangeLogs'" v-if="!authStore.isStudent && trainingData.canViewCourseChangeLogs">
            <TrainingCourseChangeLogsContent
              :course-change-logs="courseChangeLogs"
              :course-change-logs-loading="courseChangeLogsLoading"
              :format-date-time="formatDateTime"
              :course-change-source-label-map="courseChangeSourceLabelMap"
              :course-change-action-color-map="courseChangeActionColorMap"
              :course-change-action-label-map="courseChangeActionLabelMap"
              :course-change-target-label-map="courseChangeTargetLabelMap"
              @refresh="loadTrainingCourseChangeLogs"
            />
          </div>
        </a-card>
      </div>
    </div>

    <!-- Keep quickOpsCardRef for tour compatibility (hidden) -->
    <div ref="quickOpsCardRef" style="display:none"></div>

    <a-modal
      v-model:open="showCourseModal"
      :footer="null"
      width="760px"
      @cancel="closeCourseModal"
    >
      <div class="course-modal-shell">
        <div class="course-modal-head">
          <div>
            <div class="course-modal-kicker">{{ editingCourseIdx !== null ? '编辑课程' : '添加课程' }}</div>
            <div class="course-modal-title">课程维护基础信息与计划课时</div>
          </div>
        </div>

        <a-form layout="vertical" style="margin-top:12px">
          <!-- 课程来源 -->
          <a-form-item style="margin-bottom:12px">
            <a-radio-group v-model:value="courseForm.sourceMode" @change="onCourseSourceChange" button-style="solid" size="small">
              <a-radio-button value="resource">从课程资源选择</a-radio-button>
              <a-radio-button value="custom">自定义课程</a-radio-button>
            </a-radio-group>
          </a-form-item>

          <!-- 课程选择 / 名称 -->
          <a-form-item v-if="courseForm.sourceMode === 'resource'" label="课程资源" required>
            <a-input
              :value="courseForm.name"
              disabled
              placeholder="请点击选择课程资源"
            >
              <template #addonAfter>
                <a-button type="link" size="small" style="margin:-1px -11px" @click="showCourseResourcePicker = true">选择</a-button>
              </template>
            </a-input>
          </a-form-item>
          <a-form-item v-else label="课程名称" required>
            <a-input v-model:value="courseForm.name" placeholder="例：刑事诉讼法实务操作" />
          </a-form-item>

          <a-divider style="margin:8px 0 16px" />

          <!-- 教官 -->
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="授课教官" required>
                <a-select
                  v-model:value="courseForm.instructorId"
                  placeholder="选择授课教官"
                  show-search
                  option-filter-prop="label"
                  style="width:100%"
                  :disabled="courseForm.sourceMode === 'resource' && !!courseForm.instructorId"
                  @change="onInstructorChange"
                >
                  <a-select-option
                    v-for="inst in instructorList"
                    :key="inst.userId"
                    :value="inst.userId"
                    :label="inst.name"
                  >
                    {{ inst.name }}{{ inst.title ? ' · ' + inst.title : '' }}
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="带教教官">
                <a-select
                  v-model:value="courseForm.assistantInstructorIds"
                  mode="multiple"
                  placeholder="可多选"
                  show-search
                  option-filter-prop="label"
                  style="width:100%"
                >
                  <a-select-option
                    v-for="inst in instructorList.filter(i => i.userId !== courseForm.instructorId)"
                    :key="inst.userId"
                    :value="inst.userId"
                    :label="inst.name"
                  >
                    {{ inst.name }}{{ inst.title ? ' · ' + inst.title : '' }}
                  </a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <!-- 课程属性 -->
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item label="课程类型">
                <a-radio-group v-model:value="courseForm.type">
                  <a-radio value="theory">理论课</a-radio>
                  <a-radio value="practice">实操课</a-radio>
                </a-radio-group>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="计划课时">
                <a-input-number
                  v-model:value="courseForm.hours"
                  :min="0"
                  :step="0.5"
                  :precision="1"
                  style="width:100%"
                  placeholder="0"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="上课地点">
                <a-input v-model:value="courseForm.location" placeholder="教室/场地" />
              </a-form-item>
            </a-col>
          </a-row>

          <a-alert
            type="info"
            show-icon
            style="margin-top:-4px"
          >
            <template #message>
              <span style="font-size:12px">计划课时用于智能排课「按课时排」模式，不填时可在 AI 任务中选择排满模式。</span>
            </template>
          </a-alert>
        </a-form>

        <div class="wizard-footer">
          <div class="wizard-footer-tip">{{ courseModalFooterTip }}</div>
          <a-space>
            <a-button @click="closeCourseModal">取消</a-button>
            <a-button type="primary" @click="saveCourse">
              {{ editingCourseIdx !== null ? '保存课程' : '创建课程' }}
            </a-button>
          </a-space>
        </div>
      </div>
    </a-modal>

    <CourseResourcePicker
      v-model:open="showCourseResourcePicker"
      @select="onCourseResourceSelected"
    />

    <a-modal
      v-model:open="showCourseSessionModal"
      :title="editingSessionCourseIdx !== null ? `编辑课次 · ${courseForm.name || '未命名课程'}` : '编辑课次'"
      :footer="null"
      width="860px"
      @cancel="closeCourseSessionModal"
    >
      <div class="course-modal-shell" ref="courseSessionModalRef">
        <div class="course-session-header">
          <div>
            <div class="course-modal-kicker">编辑课次</div>
            <div class="course-modal-title">课次单独维护日期、开始时间和结束时间</div>
          </div>
          <a-tag color="blue">已排 {{ courseForm.schedules.length }} 个课次</a-tag>
        </div>
        <div ref="courseSessionSummaryRef" class="course-session-summary">
          <div class="summary-item">
            <span class="summary-label">课程</span>
            <span class="summary-value">{{ courseForm.name || '未命名课程' }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">教官</span>
            <span class="summary-value">{{ courseForm.instructor || '未指定' }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">计划课时状态</span>
            <span class="summary-value">{{ courseHoursStatusLabel }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">计划/已排课时</span>
            <span class="summary-value">{{ courseForm.hours || 0 }} / {{ courseFormScheduledHours }} 课时</span>
          </div>
        </div>
        <a-form layout="vertical" style="margin-top:12px">
          <a-form-item>
            <template #label>
              <div class="course-session-list-header">
                <span>详细排课清单</span>
                <a-tooltip :title="!canScheduleEdit ? scheduleEditTooltip : ''">
                  <a-button ref="courseSessionAddButtonRef" size="small" type="primary" :disabled="!canScheduleEdit" @click="openAddScheduleModal">
                    添加课次
                  </a-button>
                </a-tooltip>
              </div>
            </template>
            <div ref="courseSessionListRef">
              <div v-if="courseForm.schedules.length > 0" class="course-schedule-list">
                <div v-for="(sch, idx) in courseForm.schedules" :key="sch.sessionId || idx" class="course-schedule-item">
                  <div>
                    <div>{{ sch.date }} · {{ sch.timeRange }}</div>
                    <div style="color:#666;font-size:12px">
                      地点：{{ sch.location || courseForm.location || '未设置' }} · {{ sch.hours }}课时
                      <span v-if="sch.canEdit === false || sch.canDelete === false"> · 当前课次不可编辑删除</span>
                    </div>
                  </div>
                  <a-space size="small">
                    <a-button size="small" type="link" :disabled="sch.canEdit === false" @click="startEditCourseSchedule(idx)">编辑</a-button>
                    <a-button size="small" type="link" danger :disabled="sch.canDelete === false" @click="removeCourseSchedule(idx)">删除</a-button>
                  </a-space>
                </div>
              </div>
              <a-empty v-else description="当前还没有课次，请先添加第一节课次。" style="margin-bottom:12px" />
            </div>
          </a-form-item>
        </a-form>
        <div class="wizard-footer">
          <div class="wizard-footer-tip">课次保存后会直接同步到培训班课表中，后续仍可继续修改。</div>
          <a-space>
            <a-button @click="closeCourseSessionModal">取消</a-button>
            <span ref="courseSessionSaveButtonRef">
              <a-button type="primary" @click="saveCourseSessions">保存课次</a-button>
            </span>
          </a-space>
        </div>
      </div>
    </a-modal>

    <a-modal
      v-model:open="showScheduleModal"
      :title="scheduleForm.sessionId ? '编辑课次' : '添加课次'"
      @ok="saveSchedule"
      @cancel="resetScheduleModal"
      :ok-text="scheduleForm.sessionId ? '保存' : '添加'"
      cancel-text="取消"
      width="520px"
    >
      <a-form layout="vertical" style="margin-top:12px">
        <a-form-item label="所属课程">
          <a-input :value="scheduleForm.courseName || '-'" disabled />
        </a-form-item>
        <a-form-item label="课程地点">
          <a-input :value="scheduleForm.courseLocation || '未设置'" disabled />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="上课日期" required>
              <a-date-picker
                v-model:value="scheduleForm.date"
                style="width:100%"
                format="YYYY-MM-DD"
                placeholder="选择日期"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="课时数(按排课规则换算)">
              <a-input-number :value="scheduleModalHours" :min="0" disabled style="width:100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="上课时段" required>
          <a-time-range-picker
            v-model:value="scheduleFormTimeRange"
            style="width:100%"
            format="HH:mm"
            :minute-step="5"
            :placeholder="['开始', '结束']"
          />
        </a-form-item>
        <a-form-item label="课次地点">
          <a-input
            v-model:value="scheduleForm.location"
            placeholder="不填则使用课程地点"
          />
        </a-form-item>
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

    <ScheduleImportModal
      v-model:open="scheduleImportDialog.visible"
      :training-id="trainingId"
      :can-submit="canScheduleEdit"
      :can-download-template="canScheduleEdit"
      :submit-tooltip="scheduleEditTooltip"
      :download-template-tooltip="scheduleEditTooltip"
      @import-success="onScheduleImportSuccess"
    />

    <ExcelImportModal
      v-model:open="studentImportDialog.visible"
      title="学员导入"
      :confirm-loading="studentImportDialog.submitting"
      :can-submit="canManageStudents"
      :can-download-template="canManageStudents"
      :submit-tooltip="trainingManageTooltip"
      :download-template-tooltip="trainingManageTooltip"
      @submit="submitStudentImport"
      @download-template="handleDownloadStudentImportTemplate"
    />

    <!-- ===== 编辑班级信息弹窗 ===== -->
    <a-modal
      v-model:open="showEditModal"
      title="编辑班级信息"
      @ok="saveClassInfo"
      ok-text="保存"
      cancel-text="取消"
      width="720px"
    >
      <a-form layout="vertical" style="margin-top:12px">
        <a-form-item label="培训班名称" required>
          <a-input v-model:value="editForm.name" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="培训类型">
              <a-select v-model:value="editForm.type" placeholder="请选择培训类型">
                <a-select-option v-for="t in trainingTypeOptions" :key="t.code" :value="t.code">{{ t.name }}</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="班级容量">
              <a-input-number v-model:value="editForm.capacity" :min="1" style="width:100%" />
            </a-form-item>
          </a-col>
        </a-row>
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
        <a-form-item label="培训地点">
          <a-input v-model:value="editForm.location" placeholder="手动输入地点，或下方选择培训基地" />
        </a-form-item>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="主管/班主任">
              <a-select
                v-model:value="editForm.instructorId"
                placeholder="从教官库选定班主任"
                show-search
                option-filter-prop="label"
                allow-clear
                @change="onEditInstructorChange"
              >
                <a-select-option
                  v-for="inst in instructorList"
                  :key="inst.userId"
                  :value="inst.userId"
                  :label="inst.name"
                >
                  {{ inst.name }}{{ inst.title ? ' · ' + inst.title : '' }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="培训基地">
              <a-select v-model:value="editForm.trainingBaseId" placeholder="选择培训基地" allow-clear>
                <a-select-option v-for="b in trainingBaseOptions" :key="b.id" :value="b.id">{{ b.name }}</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="12">
          <a-col :span="12">
            <a-form-item label="所属部门">
              <a-select v-model:value="editForm.departmentId" placeholder="选择部门" show-search option-filter-prop="label" allow-clear>
                <a-select-option v-for="d in departmentOptions" :key="d.id" :value="d.id" :label="d.name">{{ d.name }}</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="警种">
              <a-select v-model:value="editForm.policeTypeId" placeholder="选择警种" allow-clear>
                <a-select-option v-for="p in policeTypeOptions" :key="p.id" :value="p.id">{{ p.name }}</a-select-option>
              </a-select>
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
          <a-textarea v-model:value="editForm.description" :rows="3" />
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
        <a-table-column title="身份证号" data-index="idCardNumber" key="idCardNumber" width="180" />
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

    <QuickCreateExamModal
      v-model:open="showQuickExamModal"
      :training-id="trainingId"
      @success="onQuickExamSuccess"
    />

    <a-tour
      v-model:current="detailTourCurrent"
      :open="detailTourOpen"
      :steps="detailTourSteps"
      @close="handleDetailTourClose"
    />
    <a-tour
      v-model:current="courseSessionTourCurrent"
      :open="courseSessionTourOpen"
      :steps="courseSessionTourSteps"
      @close="handleCourseSessionTourClose"
    />
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { CalendarOutlined, EnvironmentOutlined, UserOutlined, QuestionCircleOutlined, AppstoreOutlined, ReadOutlined, FileTextOutlined, SettingOutlined, PlusOutlined, TeamOutlined, FolderOutlined } from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import {
  getTraining,
  getTrainingCourseChangeLogs,
  getEnrollments,
  approveEnrollment,
  rejectEnrollment,
  manageTraining as apiManageTraining,
  updateTraining as apiUpdateTraining,
  publishTraining,
  lockTraining,
  startTraining,
  endTraining,
  startTrainingSessionCheckout,
  endTrainingSessionCheckout,
  skipTrainingSession,
  importTrainingStudents,
  downloadTrainingStudentImportTemplate,
  getStudents,
  getCheckinRecords,
  getTrainingCourses,
} from '@/api/training'
import { getUsers, getPoliceTypes } from '@/api/user'
import { getDepartmentList } from '@/api/department'
import { getTrainingBases } from '@/api/training'
import { getTrainingTypes } from '@/api/trainingType'
import { getNotices as apiGetNotices, createNotice as apiCreateNotice, updateNotice as apiUpdateNotice, deleteNotice as apiDeleteNotice } from '@/api/notice'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/datetime'
import { downloadBlob } from '@/utils/download'
import ExcelImportModal from '@/views/system/components/ExcelImportModal.vue'
import ScheduleImportModal from './components/ScheduleImportModal.vue'
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'
import TrainingOverviewContent from './components/TrainingOverviewContent.vue'
import TrainingScheduleContent from './components/TrainingScheduleContent.vue'
import TrainingScheduleRuleContent from './components/TrainingScheduleRuleContent.vue'
import TrainingExamsContent from './components/TrainingExamsContent.vue'
import QuickCreateExamModal from './components/QuickCreateExamModal.vue'
import TrainingStudentsContent from './components/TrainingStudentsContent.vue'
import CourseResourcePicker from './components/CourseResourcePicker.vue'
import TrainingCourseChangeLogsContent from './components/TrainingCourseChangeLogsContent.vue'
import TrainingResourcesContent from './components/TrainingResourcesContent.vue'
import TrainingNextActionCard from './components/TrainingNextActionCard.vue'
import TrainingQuickOpsCard from './components/TrainingQuickOpsCard.vue'
import TrainingNoticeCard from './components/TrainingNoticeCard.vue'
import TrainingAttendanceStatsCard from './components/TrainingAttendanceStatsCard.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const trainingId = route.params.id
const DETAIL_TOUR_VERSION = 'v2'
const workflowHeaderRef = ref(null)
const trainingBannerRef = ref(null)
const overviewContentRef = ref(null)
const scheduleContentRef = ref(null)
const nextStepCardRef = ref(null)
const quickOpsCardRef = ref(null)
const noticeCardRef = ref(null)
const detailTourOpen = ref(false)
const detailTourCurrent = ref(0)
const detailTourAutoChecked = ref(false)
const courseSessionTourOpen = ref(false)
const courseSessionTourCurrent = ref(0)
const pendingCourseSessionGuideIndex = ref(null)
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
  scheduleRuleConfig: {
    lessonUnitMinutes: 40,
    breakMinutes: 10,
    maxUnitsPerSession: 3,
    dailyMaxUnits: 6,
    preferredPlanningMode: 'fill_workdays',
    splitStrategy: 'balanced',
    teachingWindows: [],
  },
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
  canViewCourseChangeLogs: false,
  canReviewEnrollments: false,
  currentEnrollmentStatus: null,
  canEnterTraining: false,
})

const allUserList = ref([])
const rosterUserList = ref([])
const departmentOptions = ref([])
const policeTypeOptions = ref([])
const trainingBaseOptions = ref([])
const trainingTypeOptions = ref([])
const studentImportDialog = reactive({ visible: false, submitting: false })
const scheduleImportDialog = reactive({ visible: false })
const notices = ref([])
const courseChangeLogs = ref([])
const courseChangeLogsLoading = ref(false)
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
    idCardNumber: item.idCardNumber,
    departments: (item.departments || []).map((name) => ({ name })),
  }))
  rosterUserList.value = mappedStudents.length
    ? mappedStudents
    : (studentIds || []).map((userId) => ({ id: userId }))
}

function applyTrainingDetail(data) {
  const normalizedStudents = data.students || []
  const normalizedStudentIds = data.studentIds || normalizedStudents.map((item) => item.userId).filter((item) => item != null)
  const incomingScheduleRuleConfig = data.scheduleRuleConfig || {
    lessonUnitMinutes: 40,
    breakMinutes: 10,
    maxUnitsPerSession: 3,
    dailyMaxUnits: 6,
    preferredPlanningMode: 'fill_workdays',
    splitStrategy: 'balanced',
    teachingWindows: [],
  }
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
        hours: calculateScheduleUnitsFromTimeRange(
          schedule.timeRange || schedule.time_range || '',
          schedule.hours,
          incomingScheduleRuleConfig
        ),
      })),
    })),
    studentIds: normalizedStudentIds,
    students: normalizedStudents,
    enrolledCount: data.enrolledCount ?? normalizedStudentIds.length,
    enrolled: data.enrolledCount ?? normalizedStudentIds.length,
    enrollmentRequiresApproval: data.enrollmentRequiresApproval !== false,
    scheduleRuleConfig: incomingScheduleRuleConfig,
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
    canViewCourseChangeLogs: !!data.canViewCourseChangeLogs,
    canReviewEnrollments: !!data.canReviewEnrollments,
    currentEnrollmentStatus: data.currentEnrollmentStatus || null,
    canEnterTraining: !!data.canEnterTraining,
  })
  syncTrainingRoster(normalizedStudents, normalizedStudentIds)
  notices.value = normalizeNotices(data.notices || [])
  syncEditFormFromTraining()
}

async function fetchSubResources() {
  const promises = []

  // Fetch students
  promises.push(
    getStudents(trainingId, { size: -1 })
      .then((result) => {
        const students = result.items || result || []
        const studentIds = students.map((item) => item.userId).filter((item) => item != null)
        trainingData.students = students
        trainingData.studentIds = studentIds
        trainingData.enrolledCount = studentIds.length
        trainingData.enrolled = studentIds.length
        syncTrainingRoster(students, studentIds)
      })
      .catch(() => {})
  )

  // Fetch checkin records
  promises.push(
    getCheckinRecords(trainingId)
      .then((result) => {
        const records = result.items || result || []
        trainingData.checkinRecords = normalizeCheckinRecords(records)
      })
      .catch(() => {})
  )

  // Fetch courses
  promises.push(
    getTrainingCourses(trainingId)
      .then((result) => {
        const courses = result.items || result || []
        const ruleConfig = trainingData.scheduleRuleConfig || {}
        trainingData.courses = courses.map((course) => ({
          ...course,
          schedules: (course.schedules || []).map((schedule) => ({
            ...schedule,
            timeRange: schedule.timeRange || schedule.time_range || '',
            sessionId: schedule.sessionId || schedule.session_id,
            hours: calculateScheduleUnitsFromTimeRange(
              schedule.timeRange || schedule.time_range || '',
              schedule.hours,
              ruleConfig
            ),
          })),
        }))
      })
      .catch(() => {})
  )

  // Fetch notices
  promises.push(
    apiGetNotices({ training_id: trainingId, size: -1 })
      .then((result) => {
        const items = result.items || result || []
        notices.value = normalizeNotices(items)
      })
      .catch(() => {})
  )

  await Promise.all(promises)
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
    await fetchSubResources()
    if (authStore.isStudent || !data.canViewCourseChangeLogs) {
      courseChangeLogs.value = []
      if (activeTab.value === 'courseChangeLogs') {
        activeTab.value = 'overview'
      }
    } else if (activeTab.value === 'courseChangeLogs') {
      loadTrainingCourseChangeLogs()
    }
    await maybeAutoOpenDetailTour()
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

async function loadTrainingCourseChangeLogs() {
  if (authStore.isStudent || !trainingData.canViewCourseChangeLogs) {
    courseChangeLogs.value = []
    return
  }
  if (courseChangeLogsLoading.value) {
    return
  }
  courseChangeLogsLoading.value = true
  try {
    courseChangeLogs.value = await getTrainingCourseChangeLogs(trainingId)
  } catch (error) {
    message.error(error.message || '加载课程变更记录失败')
  } finally {
    courseChangeLogsLoading.value = false
  }
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

onMounted(async () => {
  await loadTrainingDetail()
  if (canManageEnrollmentApplications.value) {
    loadEnrollmentApplications()
  }
})

const activeTab = ref('overview')
const sidebarSelectedKeys = computed({
  get: () => [activeTab.value],
  set: (keys) => { if (keys.length) activeTab.value = keys[keys.length - 1] }
})
const sidebarOpenKeys = ref(['students-group', 'exams-group', 'config-group'])

function handleSidebarClick({ key }) {
  activeTab.value = key
}
const studentSearch = ref('')
const selectedSchedules = reactive({}) // { courseIdx: scheduleIdx }
const scheduleViewMode = ref('course')
const canEdit = computed(() => !!trainingData.canManageAll)
const canScheduleEdit = computed(() => !!trainingData.canEditCourses && trainingData.status !== 'ended')
const canManageStudents = computed(() => !!trainingData.canManageAll)
const canManageEnrollmentApplications = computed(() => !!trainingData.canReviewEnrollments)
const canManageNotices = computed(() => !!trainingData.canManageAll)
const canExportStudents = computed(() => !!trainingData.canManageAll)
const canQuickCreateExam = computed(() => canEdit.value && authStore.hasPermission('CREATE_EXAM'))
const trainingManageTooltip = computed(() => {
  if (authStore.hasPermission('MANAGE_TRAINING')) return '当前培训班不在可管理范围内'
  if (authStore.hasPermission('UPDATE_TRAINING')) return '仅培训班班主任可执行该操作'
  return '需要 MANAGE_TRAINING，或具备 UPDATE_TRAINING 且为班主任'
})
const scheduleEditTooltip = computed(() => (
  trainingData.status === 'ended' ? '已结班，不能再修改课程安排' : trainingManageTooltip.value
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
const workflowStageOrder = ['draft', 'published', 'locked', 'running', 'completed']
const workflowProcessKey = computed(() => {
  if (trainingData.currentStepKey) {
    return trainingData.currentStepKey
  }
  const processStep = (trainingData.workflowSteps || []).find((step) => step.status === 'process')
  const stepKeyMap = {
    发布招生: 'published',
    锁定名单: 'locked',
    开班进行中: 'running',
    结班归档: 'completed',
  }
  return stepKeyMap[processStep?.title] || trainingData.currentStepKey || 'draft'
})
const workflowProcessIndex = computed(() => {
  const index = workflowStageOrder.indexOf(workflowProcessKey.value)
  return index >= 0 ? index : 0
})
const showPublishWorkflowAction = computed(() => workflowProcessKey.value === 'draft')
const showLockWorkflowAction = computed(() => workflowProcessKey.value === 'published')
const showStartWorkflowAction = computed(() => workflowProcessKey.value === 'locked')
const showEndWorkflowAction = computed(() => workflowProcessKey.value === 'running')
const showOverviewSetupGuide = computed(() => (
  !authStore.isStudent && workflowProcessIndex.value < workflowStageOrder.indexOf('running')
))
const showOverviewCurrentCourse = computed(() => workflowProcessKey.value === 'running')
const canPublishWorkflowAction = computed(() => canEdit.value && showPublishWorkflowAction.value)
const canLockWorkflowAction = computed(() => canEdit.value && showLockWorkflowAction.value)
const canStartWorkflowAction = computed(() => canEdit.value && showStartWorkflowAction.value)
const canEndWorkflowAction = computed(() => canEdit.value && showEndWorkflowAction.value)
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
const courseChangeTargetLabelMap = {
  course: '课程',
  session: '课次',
}
const courseChangeActionLabelMap = {
  create: '新增',
  update: '更新',
  delete: '删除',
  statusChange: '状态变更',
}
const courseChangeActionColorMap = {
  create: 'green',
  update: 'blue',
  delete: 'red',
  statusChange: 'orange',
}
const courseChangeSourceLabelMap = {
  detailUpdate: '详情修改',
  importCourse: '课程导入',
  importSession: '课次导入',
  importSchedule: '课次导入',
  startCheckin: '开始签到',
  endCheckin: '结束签到',
  startCheckout: '开始签退',
  endCheckout: '结束签退',
  skipSession: '跳过课次',
  systemRefresh: '系统刷新',
}
const currentSessionStatusLabel = computed(() => {
  if (!currentSession.value) return '无'
  return scheduleStatusLabelMap[currentSession.value.status] || currentSession.value.status
})
const scheduleRows = computed(() => (trainingData.courses || []).flatMap((course, courseIndex) =>
  (course.schedules || []).map((schedule, scheduleIndex) => ({
    sessionId: schedule.sessionId,
    date: schedule.date,
    timeRange: schedule.timeRange,
    location: schedule.location || course.location || '',
    status: schedule.status,
    courseName: course.name,
    courseIndex,
    scheduleIndex,
    canEdit: !!schedule.canEdit,
    canDelete: !!schedule.canDelete,
    editLockMessage: schedule.editLockMessage || '',
    deleteLockMessage: schedule.deleteLockMessage || '',
    instructorText: [
      course.primaryInstructorName || course.instructor || '未指定',
      course.assistantInstructorNames?.length ? `带教：${course.assistantInstructorNames.join('、')}` : '',
    ].filter(Boolean).join(' / '),
  }))
))

watch(activeTab, (tab) => {
  if (tab === 'courseChangeLogs' && trainingData.canViewCourseChangeLogs && !authStore.isStudent) {
    loadTrainingCourseChangeLogs()
  }
  if (tab === 'basic-info' && !authStore.isStudent) {
    ensureEditLookups()
  }
  if (tab === 'enrollment-applications' && !authStore.isStudent) {
    loadEnrollmentApplications()
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
const courseCount = computed(() => (trainingData.courses || []).length)
const sessionCount = computed(() => (trainingData.courses || []).reduce((sum, course) => sum + (course.schedules || []).length, 0))
const coursesWithoutSessionsCount = computed(() => (
  (trainingData.courses || []).filter((course) => !(course.schedules || []).length).length
))
const firstCourseWithoutSessionsIndex = computed(() => {
  const courses = trainingData.courses || []
  const pendingIndex = courses.findIndex((course) => !(course.schedules || []).length)
  if (pendingIndex >= 0) return pendingIndex
  return courses.length > 0 ? 0 : -1
})
const hasBasicTrainingInfo = computed(() => Boolean(trainingData.name && trainingData.startDate && trainingData.endDate && trainingData.location))

const overviewStats = computed(() => [
  { label: '报名人数', value: trainingData.enrolledCount, color: '#003087' },
  { label: '班级容量', value: trainingData.capacity, color: '#555' },
  { label: '预计完成学员', value: completeCount, color: '#52c41a' },
  { label: '课程总学时', value: trainingData.courses.reduce((a, c) => a + (c.hours || 0), 0) || 0, color: '#faad14' },
])
const workflowGuideState = computed(() => {
  const guideMap = {
    draft: {
      description: '准备好学员、课程和课次后，再发布培训班。',
      status: 'todo',
      statusText: '待开始',
      statusColor: 'default',
    },
    published: {
      description: '培训班已发布，请先确认学员名单和课程安排，确认无误后再锁定名单。',
      status: 'progress',
      statusText: '待继续',
      statusColor: 'orange',
    },
    locked: {
      description: '名单已锁定，可以准备开班。',
      status: 'progress',
      statusText: '待继续',
      statusColor: 'orange',
    },
    running: {
      description: '培训班已开班，当前进入进行中状态。',
      status: 'progress',
      statusText: '进行中',
      statusColor: 'blue',
    },
    completed: {
      description: '培训班已结班归档。',
      status: 'done',
      statusText: '已归档',
      statusColor: 'green',
    },
  }
  return guideMap[workflowProcessKey.value] || guideMap.draft
})
const setupGuideItems = computed(() => ([
  {
    key: 'basic',
    index: '1',
    title: '完善班级信息',
    description: hasBasicTrainingInfo.value ? '班级名称、时间和地点已准备完成。' : '先把培训时间、地点和班级名称定下来。',
    status: hasBasicTrainingInfo.value ? 'done' : 'todo',
    statusText: hasBasicTrainingInfo.value ? '已完成' : '待补充',
    statusColor: hasBasicTrainingInfo.value ? 'green' : 'default',
  },
  {
    key: 'students',
    index: '2',
    title: '补充学员名单',
    description: trainingData.enrolledCount > 0 ? `当前已有 ${trainingData.enrolledCount} 名学员在班内。` : '建议先导入或添加学员，后续才能锁定名单。',
    status: trainingData.enrolledCount > 0 ? 'done' : 'todo',
    statusText: trainingData.enrolledCount > 0 ? '已完成' : '待补充',
    statusColor: trainingData.enrolledCount > 0 ? 'green' : 'default',
  },
  {
    key: 'courses',
    index: '3',
    title: '准备课程清单',
    description: courseCount.value > 0 ? `当前已添加 ${courseCount.value} 门课程。` : '先添加课程模板，再安排具体课次。',
    status: courseCount.value > 0 ? 'done' : 'todo',
    statusText: courseCount.value > 0 ? '已完成' : '待补充',
    statusColor: courseCount.value > 0 ? 'green' : 'default',
  },
  {
    key: 'sessions',
    index: '4',
    title: '安排课次时间',
    description: courseCount.value === 0
      ? '先添加课程模板，再安排具体课次。'
      : coursesWithoutSessionsCount.value === 0
        ? `全部 ${courseCount.value} 门课程都已安排课次。`
        : sessionCount.value > 0
          ? `还有 ${coursesWithoutSessionsCount.value} 门课程未安排课次。`
          : '课次才有日期和时间，建议尽快补齐课表。',
    status: courseCount.value > 0 && coursesWithoutSessionsCount.value === 0
      ? 'done'
      : sessionCount.value > 0
        ? 'progress'
        : 'todo',
    statusText: courseCount.value > 0 && coursesWithoutSessionsCount.value === 0
      ? '已完成'
      : sessionCount.value > 0
        ? '待继续'
        : '待补充',
    statusColor: courseCount.value > 0 && coursesWithoutSessionsCount.value === 0
      ? 'green'
      : sessionCount.value > 0
        ? 'orange'
        : 'default',
  },
  {
    key: 'workflow',
    index: '5',
    title: '执行开班流程',
    description: workflowGuideState.value.description,
    status: workflowGuideState.value.status,
    statusText: workflowGuideState.value.statusText,
    statusColor: workflowGuideState.value.statusColor,
  },
]))
const canSuggestPreparationActions = computed(() => workflowProcessIndex.value <= workflowStageOrder.indexOf('published'))
const dismissedPreparationSteps = ref(new Set())
function skipPreparationStep(stepKey) {
  dismissedPreparationSteps.value.add(stepKey)
}
const preparationAction = computed(() => {
  if (!canSuggestPreparationActions.value || authStore.isStudent) {
    return null
  }
  if ((trainingData.enrolledCount || 0) === 0 && !dismissedPreparationSteps.value.has('students')) {
    const secondaryActions = []
    if (showPublishWorkflowAction.value) {
      secondaryActions.push({
        key: 'publish-without-students',
        buttonText: '跳过，先发布培训班',
        onClick: handlePublish,
        allowed: canPublishWorkflowAction.value,
        tooltip: trainingManageTooltip.value,
      })
    }
    secondaryActions.push({
      key: 'skip-students',
      buttonText: '跳过',
      onClick: () => skipPreparationStep('students'),
      allowed: true,
    })
    return {
      title: '先补充学员名单',
      description: `当前班级还没有学员，建议先导入或添加学员；如果想先开放报名，也可以先发布培训班，让学员${trainingData.enrollmentRequiresApproval ? '通过申请进入' : '直接报名进入'}。`,
      buttonText: '去学员名单',
      onClick: () => { activeTab.value = 'students' },
      type: 'primary',
      allowed: canManageStudents.value,
      tooltip: trainingManageTooltip.value,
      secondaryActions,
    }
  }
  if (courseCount.value === 0 && !dismissedPreparationSteps.value.has('courses')) {
    return {
      title: '先添加课程',
      description: '培训班还没有课程，建议先把课程清单建起来。',
      buttonText: '去添加课程',
      onClick: () => {
        activeTab.value = 'schedule'
        openCourseModal()
      },
      type: 'primary',
      allowed: canScheduleEdit.value,
      tooltip: scheduleEditTooltip.value,
      secondaryActions: [{
        key: 'skip-courses',
        buttonText: '跳过',
        onClick: () => skipPreparationStep('courses'),
        allowed: true,
      }],
    }
  }
  if (coursesWithoutSessionsCount.value > 0 && !dismissedPreparationSteps.value.has('sessions')) {
    return {
      title: '继续安排课次',
      description: coursesWithoutSessionsCount.value === courseCount.value
        ? '课程已经有了，但还没有具体上课时间，建议先用智能排课生成建议方案。'
        : `还有 ${coursesWithoutSessionsCount.value} 门课程未安排课次，建议先用智能排课补齐。`,
      buttonText: '去智能排课',
      onClick: () => openAiScheduleTask({ openTour: true }),
      type: 'primary',
      allowed: canScheduleEdit.value,
      tooltip: scheduleEditTooltip.value,
      secondaryActions: [{
        key: 'skip-sessions',
        buttonText: '跳过',
        onClick: () => skipPreparationStep('sessions'),
        allowed: true,
      }],
    }
  }
  return null
})
const recommendedAction = computed(() => {
  if (authStore.isStudent) {
    if (trainingData.status === 'active' && isEnrolled.value) {
      return {
        title: '查看本班日程',
        description: '当前培训班正在进行中，优先查看当天课次和签到入口。',
        buttonText: '进入日程',
        onClick: () => router.push(`/training/schedule/${trainingData.id}`),
        type: 'primary',
      }
    }
    return null
  }
  if (preparationAction.value) {
    return preparationAction.value
  }
  if (showPublishWorkflowAction.value) {
    return {
      title: '可以发布培训班了',
      description: '学员、课程和课次已准备齐，可以把培训班发布出去，让招生流程正式开始。',
      buttonText: '发布培训班',
      onClick: handlePublish,
      type: 'primary',
      ghost: true,
      allowed: canPublishWorkflowAction.value,
      tooltip: trainingManageTooltip.value,
    }
  }
  if (showLockWorkflowAction.value) {
    return {
      title: '确认名单后再锁定',
      description: '培训班已经发布。开班前请确认学员名单无误，锁定后将不再允许继续增减学员。',
      buttonText: '去锁定名单',
      onClick: handleLock,
      danger: true,
      ghost: true,
      allowed: canLockWorkflowAction.value,
      tooltip: trainingManageTooltip.value,
    }
  }
  if (showStartWorkflowAction.value) {
    return {
      title: '准备开班',
      description: '名单已锁定，接下来可以正式开班并进入签到流程。',
      buttonText: '开班',
      onClick: handleStart,
      type: 'primary',
      allowed: canStartWorkflowAction.value,
      tooltip: trainingManageTooltip.value,
    }
  }
  if (trainingData.status === 'active' && !trainingExamSessions.value.length) {
    return {
      title: '安排班内考试',
      description: '当前培训班已经在进行中，如有考核安排，可以现在补充。',
      buttonText: '快捷添加考试',
      onClick: quickCreateTrainingExam,
      allowed: canQuickCreateExam.value,
      tooltip: quickCreateExamTooltip.value,
      secondaryActions: [
        {
          key: 'end-training',
          buttonText: '结班',
          danger: true,
          ghost: true,
          onClick: handleEnd,
          allowed: canEndWorkflowAction.value,
          tooltip: trainingManageTooltip.value,
        },
      ],
    }
  }
  if (showEndWorkflowAction.value) {
    return {
      title: '准备结班归档',
      description: '当课程、考试和签到都完成后，可以执行结班归档。',
      buttonText: '结班',
      onClick: handleEnd,
      danger: true,
      allowed: canEndWorkflowAction.value,
      tooltip: trainingManageTooltip.value,
    }
  }
  if (workflowProcessKey.value === 'completed') {
    return null
  }
  return {
    title: '继续查看课程安排',
    description: '当前培训班基础配置已齐全，可以继续优化课表、学员和考试安排。',
    buttonText: '进入课程安排',
    onClick: () => { activeTab.value = 'schedule' },
  }
})

const detailTourStorageKey = computed(() => (
  `training-detail-tour:${authStore.isStudent ? 'student' : 'manage'}:${DETAIL_TOUR_VERSION}`
))

function resolveTourTarget(targetSource) {
  const target = typeof targetSource === 'function' ? targetSource() : targetSource
  if (!target) return null
  if (target.nodeType === 1) return target
  if (target.$el) return resolveTourTarget(target.$el)
  if (Object.prototype.hasOwnProperty.call(target, 'value')) {
    return resolveTourTarget(target.value)
  }
  return null
}

function createTourStep(title, description, targetSource, placement = 'bottom') {
  if (!resolveTourTarget(targetSource)) return null
  return {
    title,
    description,
    placement,
    target: () => resolveTourTarget(targetSource),
  }
}

const detailTourSteps = computed(() => {
  const baseSteps = [
    createTourStep('看这里：培训班流程', '顶部步骤条会告诉你当前处在哪个阶段，也可以对照流程判断下一步该做什么。', workflowHeaderRef, 'bottom'),
    createTourStep('这里是班级概况', '班级名称、时间、地点和班主任都集中展示在这里，先确认基础信息是否正确。', trainingBannerRef, 'bottom'),
  ]

  if (authStore.isStudent) {
    return [
      ...baseSteps,
      createTourStep('这里看当前课次', '如果当前有正在进行或即将开始的课次，这里会直接告诉你课程、时间和签到状态。', () => overviewContentRef.value?.currentCourseSectionRef, 'top'),
      createTourStep('常用操作在右侧', '查看日程、扫码签到等高频入口都收在这里，不需要来回找标签页。', quickOpsCardRef, 'left'),
    ].filter(Boolean)
  }

  return [
    ...baseSteps,
    createTourStep('先按指引补齐准备项', '这里会把学员、课程、课次和开班流程按顺序列出来，适合第一次进页面时快速判断缺什么。', () => overviewContentRef.value?.setupGuideCardRef, 'right'),
    createTourStep('系统会提示推荐下一步', '这里会根据当前阶段提示最合适的动作，先补准备项，再发布、锁定和开班。', nextStepCardRef, 'left'),
    createTourStep('高频操作集中在这里', '常用入口把课程安排、学员名单、考试安排和编辑班级收在一起，避免在多个标签页间反复切换。', quickOpsCardRef, 'left'),
    createTourStep('公告改到右侧卡片', '班级公告不再单独占一个标签页，发布和查看都放到这里，信息更集中。', noticeCardRef, 'left'),
  ].filter(Boolean)
})

const courseSessionTourSteps = computed(() => {
  if (!showCourseSessionModal.value) {
    return [
      createTourStep(
        '先从这里进入课次维护',
        '每门课程都单独维护课次。先点击这门课程右侧的“编辑课次”。',
        () => scheduleContentRef.value?.getCourseSessionButtonRef?.(firstCourseWithoutSessionsIndex.value),
        'bottom'
      ),
    ].filter(Boolean)
  }
  return [
    createTourStep('先确认课程信息', '这里会展示课程名称、授课教官和当前课次数量，避免改错课程。', courseSessionSummaryRef, 'bottom'),
    createTourStep('这里查看已排课次', '已有课次会按时间列出来，可以继续改、删或补新的时间。', courseSessionListRef, 'bottom'),
    createTourStep('从这里添加新课次', '新增课次会打开独立弹窗，再填写日期、开始时间和结束时间。', courseSessionAddButtonRef, 'bottom'),
    createTourStep('完成后记得保存', '所有课次调整确认无误后，点这里提交到培训班。', courseSessionSaveButtonRef, 'top'),
  ].filter(Boolean)
})

function hasSeenDetailTour() {
  if (typeof window === 'undefined') return false
  return window.localStorage.getItem(detailTourStorageKey.value) === 'done'
}

function markDetailTourSeen() {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(detailTourStorageKey.value, 'done')
}

async function openDetailTour() {
  activeTab.value = 'overview'
  detailTourOpen.value = false
  detailTourCurrent.value = 0
  await nextTick()
  if (!detailTourSteps.value.length) return
  detailTourOpen.value = true
}

function handleDetailTourClose() {
  detailTourOpen.value = false
  markDetailTourSeen()
}

function handleCourseSessionTourClose() {
  courseSessionTourOpen.value = false
  courseSessionTourCurrent.value = 0
  pendingCourseSessionGuideIndex.value = null
}

async function maybeAutoOpenDetailTour() {
  if (detailTourAutoChecked.value) return
  detailTourAutoChecked.value = true
  if (hasSeenDetailTour()) return
  await openDetailTour()
}

// ===== 学员名单 =====
const mockStudents = computed(() => trainingData.studentIds.map(userId => {
  const u = userMap.value[userId] || {}
  const name = u.nickname || u.username || '未知学员'
  const idCardNumber = u.idCardNumber || String(userId)
  const unit = (u.departments && u.departments.length > 0) ? u.departments[0].name : '未分配'
  return { key: userId, name, idCardNumber, unit }
}))

const filteredStudents = computed(() =>
  studentSearch.value ? mockStudents.value.filter(s => s.name.includes(studentSearch.value) || (s.idCardNumber || '').includes(studentSearch.value)) : mockStudents.value
)

function goTrainingExamManage() {
  router.push({
    name: 'ExamManage',
    query: {
      kind: 'training',
      trainingId: String(trainingData.id),
    },
  })
}

function handleGuideClick(key) {
  const guideActionMap = {
    basic: () => { activeTab.value = 'basic-info' },
    students: () => { activeTab.value = 'students' },
    courses: () => { activeTab.value = 'schedule' },
    sessions: () => { openAiScheduleTask() },
    workflow: () => { /* 已在概览页，无需跳转 */ },
  }
  const action = guideActionMap[key]
  if (action) action()
}

function openAiScheduleTask(options = {}) {
  if (!canScheduleEdit.value) {
    message.warning(scheduleEditTooltip.value)
    return
  }
  const query = options.openTour ? { tour: 'smart-schedule' } : undefined
  router.push({ name: 'AiScheduleTask', params: { id: trainingData.id }, query })
}

const showQuickExamModal = ref(false)

function quickCreateTrainingExam() {
  if (!canQuickCreateExam.value) return
  showQuickExamModal.value = true
}

function onQuickExamSuccess() {
  loadTrainingDetail()
}

function getWorkflowMissingSteps(action) {
  const actionRequirements = {
    lock: ['published'],
    start: ['published', 'locked'],
  }
  const currentIndex = workflowProcessIndex.value
  return (actionRequirements[action] || []).filter((stepKey) => {
    const requiredIndex = workflowStageOrder.indexOf(stepKey)
    return requiredIndex > currentIndex
  })
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
  confirmWorkflowAction({
    title: `是否跳过${joinedLabels}环节`,
    content: `当前操作将跳过${joinedLabels}环节，跳过后${lockTargetText}将锁定。`,
    okText: actionLabel,
    onOk: async () => {
      await executeWorkflowAction(requestFn, successMessage, errorMessage, skipSteps)
    },
  })
}

function confirmWorkflowAction({ title, content, okText, okType = 'primary', cancelText = '取消', onOk }) {
  Modal.confirm({
    title,
    content,
    okText,
    okType,
    cancelText,
    async onOk() {
      await onOk()
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
  confirmWorkflowAction({
    title: '确认锁定名单',
    content: '锁定后将不再允许继续增减学员。确认名单无误后，再执行锁定名单。',
    okText: '锁定名单',
    okType: 'danger',
    onOk: async () => {
      await executeWorkflowAction(lockTraining, '名单已锁定', '锁定失败')
    },
  })
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
  confirmWorkflowAction({
    title: '确认结班归档',
    content: '结班后培训班将进入归档状态，通常不再继续调整流程。请确认课程、考试和签到都已完成。',
    okText: '结班归档',
    okType: 'danger',
    onOk: async () => {
      try {
        await endTraining(trainingId)
        message.success('培训班已结班')
        await loadTrainingDetail()
      } catch (error) {
        message.error(error.message || '结班失败')
      }
    },
  })
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
  { title: '身份证号', dataIndex: 'idCardNumber', key: 'idCardNumber' },
  { title: '单位', dataIndex: 'unit', key: 'unit' },
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
    idCardNumber: u.idCardNumber || '',
    unit: (u.departments && u.departments.length > 0) ? u.departments[0].name : '未分配'
  }))
  if (addStudentSearch.value) {
    const q = addStudentSearch.value.toLowerCase()
    list = list.filter(u => u.name.includes(q) || (u.idCardNumber || '').toLowerCase().includes(q))
  }
  return list
})

const addStudentColumns = [
  { title: '姓名', dataIndex: 'name', key: 'name' },
  { title: '身份证号', dataIndex: 'idCardNumber', key: 'idCardNumber' },
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

function openStudentImportModal() {
  if (!canManageStudents.value) return
  studentImportDialog.visible = true
}

async function handleDownloadStudentImportTemplate() {
  if (!canManageStudents.value) return
  try {
    const blob = await downloadTrainingStudentImportTemplate(trainingId)
    downloadBlob(blob, '培训班学员导入模板.xlsx')
  } catch (error) {
    message.error(error?.message || '下载模板失败')
  }
}

async function submitStudentImport(file) {
  if (!canManageStudents.value) {
    message.warning(trainingManageTooltip.value)
    return
  }
  studentImportDialog.submitting = true
  try {
    const result = await importTrainingStudents(trainingId, file)
    message.success(
      `导入完成：成功 ${result?.successRows || 0} 行，新增账号 ${result?.createdCount || 0} 个，加入培训班 ${result?.enrollmentAdded || 0} 人`
    )
    studentImportDialog.visible = false
    await loadTrainingDetail()
  } catch (error) {
    message.error(error?.message || '学员导入失败')
  } finally {
    studentImportDialog.submitting = false
  }
}

function openScheduleImportModal() {
  if (!canScheduleEdit.value) return
  scheduleImportDialog.visible = true
}

async function onScheduleImportSuccess() {
  await loadTrainingDetail()
}

// ===== 课程 CRUD =====

const showCourseModal = ref(false)
const showCourseSessionModal = ref(false)
const showScheduleModal = ref(false)
const editingCourseIdx = ref(null)
const editingSessionCourseIdx = ref(null)
const scheduleFormTimeRange = ref([])
const courseSessionModalRef = ref(null)
const courseSessionSummaryRef = ref(null)
const courseSessionListRef = ref(null)
const courseSessionAddButtonRef = ref(null)
const courseSessionSaveButtonRef = ref(null)

// 'schedules' will store objects like { date: 'YYYY-MM-DD', timeRange: 'HH:mm~HH:mm', hours: 2 }
const courseForm = reactive({
  courseId: null,
  courseKey: '',
  name: '',
  location: '',
  instructor: '',
  instructorId: null,
  assistantInstructorIds: [],
  hours: 0,
  type: 'theory',
  schedules: [],
  sourceMode: 'resource',
})
const showCourseResourcePicker = ref(false)
const scheduleForm = reactive({
  courseIndex: null,
  sessionId: '',
  courseName: '',
  courseLocation: '',
  date: null,
  location: '',
})
const courseFormScheduledHours = computed(() => roundCourseHours(courseForm.schedules.reduce((sum, sch) => sum + Number(sch.hours || 0), 0)))
const courseHoursStatusLabel = computed(() => {
  const plannedHours = Number(courseForm.hours || 0)
  if (plannedHours > 0) {
    return `${plannedHours} 课时，可用于AI按课时排`
  }
  return '未设置，如需AI按课时排请先补齐'
})
const courseModalFooterTip = computed(() => {
  if (Number(courseForm.hours || 0) > 0) {
    return `当前已设置计划课时 ${courseForm.hours || 0}，在 AI 任务选择“按课时排”时会按此值生成建议。`
  }
  return '当前未设置计划课时；如果后续 AI 任务选择“按课时排”，请先补充计划课时。'
})

function onInstructorChange(userId) {
  const inst = instructorList.value.find(i => i.userId == userId)
  if (inst) courseForm.instructor = inst.name
}

function roundCourseHours(value) {
  const numeric = Number(value || 0)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return 0
  }
  return Number(numeric.toFixed(1))
}

function getActiveScheduleRuleConfig(ruleConfig = null) {
  const config = ruleConfig || trainingData.scheduleRuleConfig || {}
  return {
    lessonUnitMinutes: Math.max(1, Number(config.lessonUnitMinutes || config.lesson_unit_minutes || 40)),
    breakMinutes: Math.max(0, Number(config.breakMinutes || config.break_minutes || 10)),
  }
}

function calculateScheduleUnitsFromDuration(durationMinutes, ruleConfig = null) {
  if (!Number.isFinite(Number(durationMinutes)) || Number(durationMinutes) <= 0) {
    return 0
  }
  const { lessonUnitMinutes, breakMinutes } = getActiveScheduleRuleConfig(ruleConfig)
  if (durationMinutes <= lessonUnitMinutes || breakMinutes <= 0) {
    return roundCourseHours(durationMinutes / lessonUnitMinutes)
  }
  const exactUnits = (durationMinutes + breakMinutes) / (lessonUnitMinutes + breakMinutes)
  const roundedUnits = Math.round(exactUnits)
  if (Math.abs(exactUnits - roundedUnits) <= 0.05) {
    return roundCourseHours(roundedUnits)
  }
  return roundCourseHours(exactUnits)
}

function calculateScheduleUnitsFromTimeRange(timeRange, fallbackHours = 0, ruleConfig = null) {
  const explicitHours = roundCourseHours(fallbackHours)
  if (explicitHours > 0) {
    return explicitHours
  }
  if (!timeRange || !String(timeRange).includes('~')) {
    return 0
  }
  const [startText = '', endText = ''] = String(timeRange).split('~')
  const start = dayjs(`2000-01-01 ${startText.trim()}`)
  const end = dayjs(`2000-01-01 ${endText.trim()}`)
  const diffMinutes = end.diff(start, 'minute')
  return calculateScheduleUnitsFromDuration(diffMinutes, ruleConfig)
}

function sortCourseSchedules(schedules) {
  schedules.sort((a, b) => {
    const dateCompare = (a.date || '').localeCompare(b.date || '')
    if (dateCompare !== 0) return dateCompare
    return (a.timeRange || '').localeCompare(b.timeRange || '')
  })
}

function buildScheduleTimePayload(rangeValue) {
  if (!rangeValue || rangeValue.length !== 2) {
    return null
  }
  const startText = rangeValue[0].format('HH:mm')
  const endText = rangeValue[1].format('HH:mm')
  const start = dayjs(`2000-01-01 ${startText}`)
  const end = dayjs(`2000-01-01 ${endText}`)
  const diffMinutes = end.diff(start, 'minute')
  return {
    timeRange: `${startText}~${endText}`,
    hours: calculateScheduleUnitsFromDuration(diffMinutes),
  }
}

const scheduleModalHours = computed(() => {
  const payload = buildScheduleTimePayload(scheduleFormTimeRange.value)
  return payload?.hours || 0
})

function cloneTrainingCourses() {
  return JSON.parse(JSON.stringify(trainingData.courses || []))
}

function getMutableCoursePayload(courseIndex) {
  const nextCourses = cloneTrainingCourses()
  const targetCourse = nextCourses[courseIndex]
  if (!targetCourse) {
    return { nextCourses, targetCourse: null }
  }
  targetCourse.schedules = [...(targetCourse.schedules || [])]
  return { nextCourses, targetCourse }
}

function resetScheduleModal() {
  showScheduleModal.value = false
  Object.assign(scheduleForm, {
    courseIndex: null,
    sessionId: '',
    courseName: '',
    courseLocation: '',
    date: null,
    location: '',
  })
  scheduleFormTimeRange.value = []
}

function resetCourseForm() {
  Object.assign(courseForm, {
    courseId: null,
    courseKey: '',
    name: '',
    location: '',
    instructor: '',
    instructorId: null,
    assistantInstructorIds: [],
    hours: 0,
    type: 'theory',
    schedules: [],
    sourceMode: 'resource',
  })
}

function hydrateCourseForm(course) {
  resetCourseForm()
  if (!course) return
  const c = JSON.parse(JSON.stringify(course))
  const inst = instructorList.value.find(i => i.userId === c.primaryInstructorId || i.name === c.instructor)
  Object.assign(courseForm, {
    courseId: c.courseId || null,
    courseKey: c.courseKey || '',
    name: c.name,
    location: c.location || '',
    instructor: c.instructor,
    instructorId: (c.primaryInstructorId || inst?.userId) ?? null,
    assistantInstructorIds: c.assistantInstructorIds || [],
    hours: roundCourseHours(c.hours),
    type: c.type,
    schedules: c.schedules || [],
    sourceMode: c.courseId ? 'resource' : 'custom',
  })

  if (courseForm.schedules.length === 0) {
    if (c.dates && c.timeRange) {
      const hrs = calculateScheduleUnitsFromTimeRange(c.timeRange, c.hours)
      c.dates.forEach((d) => {
        courseForm.schedules.push({ date: d, timeRange: c.timeRange, hours: hrs, location: c.location || '' })
      })
    } else if (c.date && c.timeRange) {
      courseForm.schedules.push({
        date: c.date,
        timeRange: c.timeRange,
        hours: calculateScheduleUnitsFromTimeRange(c.timeRange, c.hours),
        location: c.location || '',
      })
    } else if (c.startTime && c.endTime) {
      const timeRange = `${dayjs(c.startTime).format('HH:mm')}~${dayjs(c.endTime).format('HH:mm')}`
      courseForm.schedules.push({
        date: dayjs(c.startTime).format('YYYY-MM-DD'),
        timeRange,
        hours: calculateScheduleUnitsFromTimeRange(timeRange, c.hours),
        location: c.location || '',
      })
    }
  }
}

function closeCourseModal() {
  showCourseModal.value = false
  editingCourseIdx.value = null
  resetCourseForm()
}

function closeCourseSessionModal() {
  showCourseSessionModal.value = false
  editingSessionCourseIdx.value = null
  pendingCourseSessionGuideIndex.value = null
  resetScheduleModal()
  courseSessionTourOpen.value = false
  courseSessionTourCurrent.value = 0
  resetCourseForm()
}

function validateCourseBasicInfo(showMessage = true) {
  if (!courseForm.name || !(courseForm.instructorId || courseForm.instructor)) {
    if (showMessage) {
      message.warning('请先填写课程名称和教官')
    }
    return false
  }
  if (Number(courseForm.hours || 0) < 0) {
    if (showMessage) {
      message.warning('计划课时不能小于 0')
    }
    return false
  }
  return true
}

function startEditCourseSchedule(idx) {
  const schedule = courseForm.schedules[idx]
  if (!schedule) return
  if (schedule.canEdit === false) {
    message.warning(schedule.editLockMessage || '当前课次不能编辑')
    return
  }
  openScheduleModal({
    courseIndex: editingSessionCourseIdx.value,
    sessionId: schedule.sessionId,
    canEdit: schedule.canEdit,
  })
}

function removeCourseSchedule(idx) {
  const schedule = courseForm.schedules[idx]
  if (!schedule) return
  if (schedule.canDelete === false) {
    message.warning(schedule.deleteLockMessage || '当前课次不能删除')
    return
  }
  courseForm.schedules.splice(idx, 1)
}

function openCourseModal(idx = null) {
  if (!canScheduleEdit.value) return
  ensureInstructorOptionsLoaded(true)
  editingCourseIdx.value = idx
  resetScheduleModal()
  hydrateCourseForm(idx !== null ? trainingData.courses[idx] : null)
  showCourseModal.value = true
}

function openAddScheduleModal() {
  if (!canScheduleEdit.value || editingSessionCourseIdx.value === null) return
  const targetCourse = trainingData.courses?.[editingSessionCourseIdx.value]
  if (!targetCourse) return
  resetScheduleModal()
  Object.assign(scheduleForm, {
    courseIndex: editingSessionCourseIdx.value,
    sessionId: '',
    courseName: targetCourse.name || '',
    courseLocation: targetCourse.location || '',
    date: null,
    location: targetCourse.location || '',
  })
  showScheduleModal.value = true
}

async function startCourseSessionGuide() {
  if (!canScheduleEdit.value) {
    message.warning(scheduleEditTooltip.value)
    return
  }
  const targetIndex = firstCourseWithoutSessionsIndex.value
  if (targetIndex < 0 || !trainingData.courses[targetIndex]) {
    activeTab.value = 'schedule'
    scheduleViewMode.value = 'course'
    return
  }
  pendingCourseSessionGuideIndex.value = targetIndex
  activeTab.value = 'schedule'
  scheduleViewMode.value = 'course'
  courseSessionTourOpen.value = false
  courseSessionTourCurrent.value = 0
  await nextTick()
  if (!courseSessionTourSteps.value.length) {
    await openCourseSessionModal(targetIndex)
    return
  }
  courseSessionTourOpen.value = true
}

async function openCourseSessionModal(idx = null) {
  if (!canScheduleEdit.value || idx === null || !trainingData.courses[idx]) return
  const continueGuide = pendingCourseSessionGuideIndex.value === idx
  pendingCourseSessionGuideIndex.value = continueGuide ? idx : null
  courseSessionTourOpen.value = false
  editingSessionCourseIdx.value = idx
  resetScheduleModal()
  hydrateCourseForm(trainingData.courses[idx])
  showCourseSessionModal.value = true
  await nextTick()
  if (continueGuide) {
    pendingCourseSessionGuideIndex.value = null
    courseSessionTourCurrent.value = 0
    if (courseSessionTourSteps.value.length > 0) {
      courseSessionTourOpen.value = true
    }
  }
}

function openScheduleModal(record) {
  if (!canScheduleEdit.value || !record?.canEdit) return
  const targetCourse = trainingData.courses?.[record.courseIndex]
  const targetSchedule = targetCourse?.schedules?.find((item) => item.sessionId === record.sessionId)
  if (!targetCourse || !targetSchedule) {
    message.warning('未找到要编辑的课次')
    return
  }
  const [startText = '', endText = ''] = String(targetSchedule.timeRange || '').split('~')
  Object.assign(scheduleForm, {
    courseIndex: record.courseIndex,
    sessionId: record.sessionId,
    courseName: targetCourse.name || '',
    courseLocation: targetCourse.location || '',
    date: targetSchedule.date ? dayjs(targetSchedule.date) : null,
    location: targetSchedule.location || '',
  })
  scheduleFormTimeRange.value = startText && endText
    ? [dayjs(`2000-01-01 ${startText}`), dayjs(`2000-01-01 ${endText}`)]
    : []
  showScheduleModal.value = true
}

async function saveSchedule() {
  if (!canScheduleEdit.value) return
  const courseIndex = scheduleForm.courseIndex
  if (scheduleForm.courseIndex === null) {
    message.warning('缺少所属课程')
    return
  }
  if (!scheduleForm.date) {
    message.warning('请选择上课日期')
    return
  }
  const timePayload = buildScheduleTimePayload(scheduleFormTimeRange.value)
  if (!timePayload) {
    message.warning('请选择上课时段')
    return
  }
  if (timePayload.hours <= 0) {
    message.warning('时长太短或结束时间早于开始时间')
    return
  }

  const { nextCourses, targetCourse } = getMutableCoursePayload(scheduleForm.courseIndex)
  if (!targetCourse) {
    message.warning('未找到所属课程')
    return
  }
  const nextDate = scheduleForm.date.format('YYYY-MM-DD')
  const scheduleIdx = scheduleForm.sessionId
    ? targetCourse.schedules.findIndex((item) => item.sessionId === scheduleForm.sessionId)
    : -1
  if (scheduleForm.sessionId && scheduleIdx < 0) {
    message.warning('未找到要编辑的课次')
    return
  }
  const duplicate = targetCourse.schedules.some((item, idx) => (
    (scheduleIdx < 0 || idx !== scheduleIdx)
    && item.date === nextDate
    && item.timeRange === timePayload.timeRange
  ))
  if (duplicate) {
    message.warning('该课次时间段已存在')
    return
  }

  const schedulePayload = {
    ...(scheduleIdx >= 0 ? targetCourse.schedules[scheduleIdx] : {}),
    date: nextDate,
    timeRange: timePayload.timeRange,
    location: scheduleForm.location || targetCourse.location || '',
    hours: timePayload.hours,
  }
  if (scheduleIdx >= 0) {
    targetCourse.schedules.splice(scheduleIdx, 1, schedulePayload)
  } else {
    targetCourse.schedules.push(schedulePayload)
  }
  sortCourseSchedules(targetCourse.schedules)

  try {
    await submitTrainingUpdate({ courses: nextCourses })
    message.success(scheduleIdx >= 0 ? '课次已更新' : '课次已添加')
    resetScheduleModal()
    await loadTrainingDetail()
    if (showCourseSessionModal.value && courseIndex !== null && trainingData.courses?.[courseIndex]) {
      hydrateCourseForm(trainingData.courses[courseIndex])
    }
  } catch (error) {
    message.error(error.message || '课次保存失败')
  }
}

async function saveCourseSessions() {
  if (!canScheduleEdit.value) return
  if (editingSessionCourseIdx.value === null) {
    message.warning('未找到所属课程')
    return
  }
  const nextCourses = cloneTrainingCourses()
  const targetCourse = nextCourses[editingSessionCourseIdx.value]
  if (!targetCourse) {
    message.warning('未找到所属课程')
    return
  }
  targetCourse.schedules = JSON.parse(JSON.stringify(courseForm.schedules || []))
  targetCourse.hours = roundCourseHours(courseForm.hours)
  try {
    await submitTrainingUpdate({ courses: nextCourses })
    message.success('课次已保存')
    closeCourseSessionModal()
    await loadTrainingDetail()
  } catch (error) {
    message.error(error.message || '课次保存失败')
  }
}

function onCourseSourceChange() {
  if (courseForm.sourceMode === 'resource') {
    courseForm.courseId = null
    courseForm.name = ''
  } else {
    courseForm.courseId = null
    courseForm.name = ''
  }
}

function onCourseResourceSelected(item) {
  courseForm.courseId = item.id
  courseForm.name = item.title
  // 自动设置授课教官
  if (item.instructorId) {
    courseForm.instructorId = item.instructorId
    courseForm.instructor = item.instructorName || ''
    // 确保教官在选项列表中
    ensureInstructorOptionsLoaded(true)
  } else if (item.instructorName) {
    const matched = instructorList.value.find(i => i.name === item.instructorName)
    if (matched) {
      courseForm.instructorId = matched.userId
      courseForm.instructor = matched.name
    } else {
      courseForm.instructor = item.instructorName
    }
  }
}

async function saveCourse() {
  if (!canScheduleEdit.value) return
  if (!validateCourseBasicInfo()) {
    return
  }
  const courseData = { ...courseForm }
  courseData.hours = roundCourseHours(courseForm.hours)
  courseData.primaryInstructorId = courseForm.instructorId
  courseData.courseId = courseForm.courseId
  delete courseData.instructorId
  delete courseData.sourceMode
  const nextCourses = [...trainingData.courses]
  if (editingCourseIdx.value !== null) {
    nextCourses.splice(editingCourseIdx.value, 1, courseData)
  } else {
    nextCourses.push(courseData)
  }
  try {
    await submitTrainingUpdate({ courses: nextCourses })
    message.success(editingCourseIdx.value !== null ? '课程已更新' : '课程已添加')
    closeCourseModal()
    await loadTrainingDetail()
  } catch (error) {
    message.error(error.message || '课程保存失败')
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
      } catch (error) {
        message.error(error.message || '课程删除失败')
      }
    }
  })
}

function removeSchedule(record) {
  if (!canScheduleEdit.value || !record?.canDelete) return
  Modal.confirm({
    title: '确认删除课次',
    content: `确定删除课次「${record.courseName} ${record.date} ${record.timeRange}」吗？`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      const { nextCourses, targetCourse } = getMutableCoursePayload(record.courseIndex)
      if (!targetCourse) return
      targetCourse.schedules = targetCourse.schedules.filter((item) => item.sessionId !== record.sessionId)
      if (targetCourse.schedules.length > 0) {
        nextCourses.splice(record.courseIndex, 1, targetCourse)
      } else {
        nextCourses.splice(record.courseIndex, 1)
      }
      try {
        await submitTrainingUpdate({ courses: nextCourses })
        message.success(targetCourse.schedules.length > 0 ? '课次已删除' : '课次已删除，所属课程已同步移除')
        await loadTrainingDetail()
      } catch (error) {
        message.error(error.message || '课次删除失败')
      }
    },
  })
}

// ===== 编辑班级信息 =====
const showEditModal = ref(false)
const editFormDates = ref([null, null]) // dayjs values for date pickers
const editForm = reactive({
  name: trainingData.name, type: trainingData.type || 'basic',
  startDate: trainingData.startDate, endDate: trainingData.endDate,
  location: trainingData.location, instructorId: trainingData.instructorId || null, instructorName: trainingData.instructorName,
  capacity: trainingData.capacity, status: trainingData.status, description: trainingData.description || '',
  enrollmentRequiresApproval: true,
  departmentId: trainingData.departmentId || null,
  policeTypeId: trainingData.policeTypeId || null,
  trainingBaseId: trainingData.trainingBaseId || null,
})
const scheduleRuleSaving = ref(false)

function syncEditFormFromTraining() {
  editForm.name = trainingData.name
  editForm.type = trainingData.type || 'basic'
  editForm.startDate = trainingData.startDate
  editForm.endDate = trainingData.endDate
  editForm.location = trainingData.location
  editForm.instructorId = trainingData.instructorId || null
  editForm.instructorName = trainingData.instructorName
  editForm.capacity = trainingData.capacity
  editForm.status = trainingData.status
  editForm.description = trainingData.description || ''
  editForm.enrollmentRequiresApproval = trainingData.enrollmentRequiresApproval !== false
  editForm.departmentId = trainingData.departmentId || null
  editForm.policeTypeId = trainingData.policeTypeId || null
  editForm.trainingBaseId = trainingData.trainingBaseId || null
  editFormDates.value = [
    trainingData.startDate ? dayjs(trainingData.startDate) : null,
    trainingData.endDate ? dayjs(trainingData.endDate) : null,
  ]
}

function onEditInstructorChange(userId) {
  const inst = instructorList.value.find(i => i.userId == userId)
  if (inst) editForm.instructorName = inst.name
}

async function ensureEditLookups() {
  const loads = [ensureInstructorOptionsLoaded(true)]
  if (!departmentOptions.value.length) {
    loads.push(getDepartmentList({ size: -1 }).then(r => { departmentOptions.value = r.items || [] }).catch(() => {}))
  }
  if (!policeTypeOptions.value.length) {
    loads.push(getPoliceTypes().then(r => { policeTypeOptions.value = r || [] }).catch(() => {}))
  }
  if (!trainingBaseOptions.value.length) {
    loads.push(getTrainingBases({ size: -1 }).then(r => { trainingBaseOptions.value = r.items || r || [] }).catch(() => {}))
  }
  if (!trainingTypeOptions.value.length) {
    loads.push(getTrainingTypes({ size: -1, is_active: true }).then(r => { trainingTypeOptions.value = r.items || r || [] }).catch(() => {}))
  }
  await Promise.all(loads)
}

async function openEditModal() {
  if (!canEdit.value) return
  showEditModal.value = true
  await ensureEditLookups()
}

async function saveClassInfo() {
  if (!canEdit.value) return
  if (!editForm.name || !editForm.startDate || !editForm.endDate) { message.warning('请填写必填项'); return }
  try {
    await submitTrainingUpdate({ ...editForm })
    message.success('班级信息已更新')
    showEditModal.value = false
    await loadTrainingDetail()
  } catch {
    message.error('班级信息更新失败')
  }
}

async function saveScheduleRuleConfig(payload) {
  if (!canScheduleEdit.value) return
  scheduleRuleSaving.value = true
  try {
    await submitTrainingUpdate({ scheduleRuleConfig: payload })
    message.success('排课规则已更新')
    await loadTrainingDetail()
  } catch {
    message.error('排课规则更新失败')
  } finally {
    scheduleRuleSaving.value = false
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
  const headers = ['姓名', '身份证号', '单位']
  const rows = filteredStudents.value.map(s => [
    s.name,
    `\t${s.idCardNumber}`, // 防止长数字科学计数法
    s.unit,
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
.page-header-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 16px; }
.page-breadcrumb { min-width: 0; }
.workflow-header { margin-bottom: 16px; min-width: 0; }
.workflow-header :deep(.ant-steps) { width: 100%; }
.tour-trigger-button { flex-shrink: 0; border-color: #bfdbfe; color: #1d4ed8; background: #eff6ff; }
.tour-trigger-button:hover,
.tour-trigger-button:focus { color: #1e40af; border-color: #93c5fd; background: #dbeafe; }
.wizard-badge { padding: 6px 12px; border-radius: 999px; background: #eff6ff; color: #1d4ed8; font-size: 12px; font-weight: 600; white-space: nowrap; }
.wizard-section-title { font-size: 14px; font-weight: 600; color: #0f172a; }
.wizard-footer { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding-top: 8px; border-top: 1px solid #f1f5f9; }
.wizard-footer-tip { color: #64748b; font-size: 12px; line-height: 1.6; }
.exam-plan-section { display: flex; flex-direction: column; gap: 12px; }
.exam-plan-title { font-size: 14px; font-weight: 600; color: #1f2937; }
.exam-plan-list { display: flex; flex-direction: column; gap: 12px; }
.exam-plan-card { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; padding: 16px; border: 1px solid #eef2f7; border-radius: 10px; background: #fafcff; }
.admission-plan-card { background: #f5f9ff; border-color: #dbeafe; }
.exam-plan-main { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.exam-plan-name { font-size: 15px; font-weight: 600; color: #111827; }
.exam-plan-meta { display: flex; flex-wrap: wrap; gap: 8px 16px; color: #6b7280; font-size: 13px; }

/* Banner bar layout */
.training-banner-bar { display: flex; gap: 16px; margin-bottom: 16px; align-items: stretch; }
.training-banner-bar .training-banner { flex: 1; min-width: 0; margin-bottom: 0; }
.banner-action { width: 320px; flex-shrink: 0; }
.banner-action :deep(.ant-card) { height: 100%; }

.training-banner { padding: 24px; border-radius: 8px; margin-bottom: 4px; }
.training-banner.status-active { background: linear-gradient(135deg, #001a50, #003087); }
.training-banner.status-upcoming { background: linear-gradient(135deg, #78350f, #b45309); }
.training-banner.status-ended { background: linear-gradient(135deg, #374151, #6b7280); }
.training-title-row { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.status-tag { flex-shrink: 0; }
.training-title { color: #fff; font-size: 20px; margin: 0; }
.training-meta-row { display: flex; gap: 20px; color: rgba(255,255,255,0.8); font-size: 13px; flex-wrap: wrap; }
.secondary-meta { color: rgba(255,255,255,0.92); margin-bottom: 8px; }

/* Sidebar + Content layout */
.detail-layout { display: flex; gap: 16px; }
.detail-sidebar { width: 200px; flex-shrink: 0; background: #fff; border-radius: 8px; border: 1px solid #f0f0f0; padding: 8px 0; align-self: flex-start; }
.detail-sidebar :deep(.ant-menu) { background: transparent !important; color: #333; }
.detail-sidebar :deep(.ant-menu-item),
.detail-sidebar :deep(.ant-menu-submenu-title) { margin: 2px 8px; border-radius: 6px; height: 40px; line-height: 40px; color: #333 !important; background: transparent !important; }
.detail-sidebar :deep(.ant-menu-item:hover),
.detail-sidebar :deep(.ant-menu-submenu-title:hover) { color: #003087 !important; background: transparent !important; }
.detail-sidebar :deep(.ant-menu-item-selected) { background: #e6f0ff !important; color: #003087 !important; font-weight: 600; }
.detail-sidebar :deep(.ant-menu-submenu-selected > .ant-menu-submenu-title) { color: #003087 !important; font-weight: 600; }
.detail-sidebar :deep(.ant-menu-sub.ant-menu-inline) { background: transparent !important; }
.detail-sidebar :deep(.ant-menu-submenu-arrow) { color: #333 !important; }
.detail-sidebar :deep(.ant-menu-item-active:not(.ant-menu-item-selected)) { background: transparent !important; }
.detail-content { flex: 1; min-width: 0; }
.content-section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.content-section-header h3 { margin: 0; font-size: 16px; font-weight: 600; color: #1f1f1f; }
.basic-info-form { max-width: 800px; }

.overview-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
.ov-stat { text-align: center; padding: 16px; background: #f8f9ff; border-radius: 8px; }
.ov-num { font-size: 28px; font-weight: 700; }
.ov-label { font-size: 12px; color: #888; margin-top: 4px; }
.setup-guide-card { margin-bottom: 16px; padding: 16px; border: 1px solid #e2e8f0; border-radius: 12px; background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%); }
.setup-guide-list { display: flex; flex-direction: column; gap: 10px; }
.setup-guide-item { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; padding: 12px 14px; border-radius: 10px; border: 1px solid #e5e7eb; background: #fff; transition: box-shadow 0.2s, border-color 0.2s; }
.setup-guide-item.clickable { cursor: pointer; }
.setup-guide-item.clickable:hover { border-color: #b0c4de; box-shadow: 0 2px 8px rgba(0, 48, 135, 0.08); }
.setup-guide-item.status-done { border-color: #d1fae5; background: #f0fdf4; }
.setup-guide-item.status-progress { border-color: #fde68a; background: #fffbeb; }
.setup-guide-main { min-width: 0; }
.setup-guide-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.setup-guide-step { display: inline-flex; width: 22px; height: 22px; align-items: center; justify-content: center; border-radius: 999px; background: #dbeafe; color: #1d4ed8; font-size: 12px; font-weight: 700; }
.setup-guide-title { font-size: 14px; font-weight: 600; color: #111827; }
.setup-guide-desc { color: #64748b; font-size: 12px; line-height: 1.6; }
.training-base-info { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 16px; margin-bottom: 12px; }
.info-row { display: flex; flex-direction: column; gap: 4px; padding: 12px 14px; background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 8px; }
.info-label { font-size: 12px; color: #6b7280; }
.info-value { font-size: 14px; color: #111827; font-weight: 500; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.section-header h4 { margin: 0; color: #333; }
.section-title-wrap { display: flex; flex-direction: column; gap: 8px; }
.section-helper { color: #64748b; font-size: 12px; line-height: 1.6; }
.schedule-section-header { align-items: flex-start; }
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
.next-step-card { background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%); border: 1px solid #dbeafe; }
.next-step-kicker { font-size: 12px; font-weight: 700; color: #2563eb; letter-spacing: 0.08em; text-transform: uppercase; }
.next-step-title { margin-top: 8px; font-size: 20px; font-weight: 700; color: #0f172a; }
.next-step-desc { margin: 10px 0 16px; color: #475569; line-height: 1.7; font-size: 13px; }
.quick-ops-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.quick-ops-grid :deep(.ant-btn) { width: 100%; }
.quick-ops-grid .span-2 { grid-column: span 2; }
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

.course-modal-shell { display: flex; flex-direction: column; gap: 16px; }
.course-modal-head { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }
.course-modal-kicker { font-size: 12px; font-weight: 700; color: #1677ff; letter-spacing: 0.08em; text-transform: uppercase; }
.course-modal-title { margin-top: 6px; font-size: 18px; font-weight: 700; color: #0f172a; }
.course-session-header { display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; margin-bottom: 12px; }
.course-session-list-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; width: 100%; }
.course-session-summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 12px; }
.summary-item { display: flex; flex-direction: column; gap: 4px; padding: 12px 14px; border-radius: 10px; border: 1px solid #e2e8f0; background: #f8fafc; }
.summary-label { font-size: 12px; color: #64748b; }
.summary-value { font-size: 14px; font-weight: 600; color: #111827; }
.schedule-editor-box {
  border: 1px dashed #d9d9d9;
  padding: 12px;
  border-radius: 6px;
}

.course-schedule-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.course-schedule-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 6px;
  background: #f9f9f9;
}

.schedule-mode-row {
  margin-bottom: 8px;
}

.schedule-editor-row {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.schedule-date-picker {
  flex: 1;
}

.schedule-time-range {
  width: 220px;
}

.schedule-location-input {
  width: 200px;
}

.ci-rate {
  color: #52c41a;
  min-width: 60px;
}

@media (max-width: 768px) {
  .training-banner-bar {
    flex-direction: column;
  }
  .banner-action {
    width: 100%;
  }
  .detail-layout {
    flex-direction: column;
  }
  .detail-sidebar {
    display: none;
  }
  .detail-content {
    width: 100%;
  }
  .page-header-row {
    align-items: flex-start;
  }
  .workflow-header {
    margin-bottom: 12px;
  }
  .wizard-footer {
    flex-direction: column;
    align-items: stretch;
  }
  .overview-stats { grid-template-columns: 1fr 1fr !important; }
  .training-base-info { grid-template-columns: 1fr; }
  .training-banner { padding: 16px !important; }
  .training-title { font-size: 18px !important; }
  .section-header,
  .content-section-header {
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }
  .setup-guide-item,
  .course-modal-head,
  .course-session-header {
    flex-direction: column;
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
  .student-search-input {
    width: 100%;
  }
  .quick-ops-grid,
  .course-session-summary {
    grid-template-columns: 1fr;
  }
  .quick-ops-grid .span-2 {
    grid-column: span 1;
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
