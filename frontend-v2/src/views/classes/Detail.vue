<template>
  <div class="detail-page">
    <a-spin v-if="loading" size="large" style="display: block; text-align: center; padding: 120px 0" />
    <a-empty v-else-if="!detail" description="班级不存在" style="padding: 120px 0" />

    <template v-else>
      <!-- ====== 深色头部横幅 ====== -->
      <header class="detail-header">
        <div class="header-body">
          <div class="header-left">
            <h1 class="header-title">{{ detail.name }}</h1>
            <div class="header-meta-row">
              <span v-if="detail.class_code" class="meta-chip">
                <svg class="chip-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.2"><rect x="2" y="3" width="12" height="10" rx="1.5"/><path d="M5 6h6M5 9h4"/></svg>
                {{ detail.class_code }}
              </span>
              <span class="meta-chip"><UserOutlined class="chip-icon-ant" /> {{ detail.instructor_name || '未指定教官' }}</span>
              <span class="meta-chip"><TeamOutlined class="chip-icon-ant" /> {{ detail.enrolled_count ?? 0 }}{{ detail.capacity ? '/' + detail.capacity : '' }} 人</span>
              <span v-if="detail.location" class="meta-chip"><EnvironmentOutlined class="chip-icon-ant" /> {{ detail.location }}</span>
            </div>
            <div class="header-sub-row">
              <span>{{ formatDate(detail.start_date) }} ~ {{ formatDate(detail.end_date) }}</span>
              <span v-if="detail.department_name">{{ detail.department_name }}</span>
              <span v-if="detail.training_base_name">{{ detail.training_base_name }}</span>
            </div>
            <p v-if="detail.description" class="header-desc">{{ detail.description }}</p>
          </div>

          <!-- 右侧快捷信息卡片 -->
          <div class="header-cards">
            <div class="info-card info-card--status">
              <div class="info-card-top">
                <span class="info-card-label">班级状态</span>
                <span class="info-card-badge" :class="'badge-' + detail.status">{{ statusLabels[detail.status] || detail.status }}</span>
              </div>
              <div class="info-card-num">{{ detail.training_type_name || detail.type || '-' }}</div>
              <div class="info-card-extra">
                <span>{{ detail.enrolled_count ?? 0 }}{{ detail.capacity ? '/' + detail.capacity : '' }} 人已报名</span>
                <span v-if="detail.is_locked">· 名单已锁定</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <!-- ====== 主体内容 ====== -->
      <section class="page-content detail-body">

        <!-- 操作按钮区 -->
        <div class="action-bar">
          <!-- 学员按钮 -->
          <template v-if="authStore.isStudent">
            <a-button v-if="canEnroll" type="primary" @click="handleEnroll">
              {{ detail.enrollment_requires_approval ? '报名申请' : '加入班级' }}
            </a-button>
            <a-button v-if="detail.current_enrollment_status === 'pending'" disabled>
              <ClockCircleOutlined /> 待审核
            </a-button>
            <a-button v-if="detail.current_enrollment_status === 'rejected'" disabled danger>
              审核未通过
            </a-button>
          </template>

          <!-- 通用按钮 -->
          <a-button v-if="hasFullAccess && (isEnrolled || authStore.isInstructor)" @click="router.push(`/classes/schedule/${detail.id}`)">
            <CalendarOutlined /> 查看课表
          </a-button>
          <a-button v-if="detail.status === 'ended'" @click="goHistory">
            <HistoryOutlined /> 训历
          </a-button>
        </div>

        <!-- Tab 内容区 -->
        <div class="content-tabs">
          <div class="tab-bar">
            <span
              v-for="tab in visibleTabs"
              :key="tab.key"
              class="tab-item"
              :class="{ active: activeTab === tab.key }"
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
            </span>
          </div>

          <!-- ========== 概览 ========== -->
          <div v-if="activeTab === 'overview'" class="tab-panel">

            <!-- 当前/下一节课次（仅本班人员可见） -->
            <div v-if="hasFullAccess && currentSession" class="overview-section">
              <h3 class="section-label">
                {{ currentSessionSchedule && isSessionActive(currentSessionSchedule) ? '正在进行' : '下一节课' }}
              </h3>
              <div class="current-session-card" :class="{ 'is-active': currentSessionSchedule && isSessionActive(currentSessionSchedule) }">
                <div class="cs-left">
                  <div class="cs-date-col">
                    <span class="cs-day">{{ dayjs(currentSession.date).date() }}</span>
                    <span class="cs-weekday">{{ ['周日','周一','周二','周三','周四','周五','周六'][dayjs(currentSession.date).day()] }}</span>
                  </div>
                  <div class="cs-body">
                    <div class="cs-header">
                      <strong class="cs-course">{{ currentSession.course_name }}</strong>
                      <a-tag :color="sessionTagColor(currentSession.status)" size="small">
                        {{ sessionStatusLabel(currentSession.status) }}
                      </a-tag>
                    </div>
                    <div class="cs-meta">
                      <span><ClockCircleOutlined /> {{ currentSession.time_range?.replace('~', ' - ') }}</span>
                      <span v-if="currentSession.location"><EnvironmentOutlined /> {{ currentSession.location }}</span>
                      <span v-if="currentSession.primary_instructor_name"><UserOutlined /> {{ currentSession.primary_instructor_name }}</span>
                    </div>
                  </div>
                </div>
                <div class="cs-actions">
                  <!-- 教官流程控制按钮（仅教官可见） -->
                  <template v-if="authStore.isInstructor && currentSession.action_permissions">
                    <a-button
                      v-if="currentSession.action_permissions.can_start_checkin"
                      type="primary"
                      size="small"
                      @click="openCheckinMgr"
                    >
                      开始签到
                    </a-button>
                    <a-button
                      v-if="currentSession.action_permissions.can_start_checkout"
                      type="primary"
                      size="small"
                      @click="doStartCheckout"
                    >
                      开始签退
                    </a-button>
                  </template>
                  <!-- 签到管理按钮 -->
                  <a-button
                    v-if="authStore.isInstructor && (hasActiveCheckin || currentSession?.status === 'checkin_closed')"
                    size="small"
                    @click="openCheckinMgr"
                  >
                    签到管理
                  </a-button>
                  <!-- 签退管理按钮 -->
                  <a-button
                    v-if="authStore.isInstructor && isCheckoutPhase"
                    size="small"
                    @click="openCheckoutMgr"
                  >
                    签退管理
                  </a-button>
                  <!-- 学员签到按钮 -->
                  <template v-if="authStore.isStudent && isEnrolled && hasActiveCheckin">
                    <template v-if="hasCheckedIn">
                      <span class="cs-checked-label"><CheckCircleOutlined /> 已签到</span>
                    </template>
                    <template v-else-if="currentSession.checkin_mode === 'qr'">
                      <span class="cs-qr-hint">请扫描教官展示的二维码进行签到</span>
                    </template>
                    <a-button
                      v-else
                      type="primary"
                      size="small"
                      @click="studentCheckinConfirmVisible = true"
                    >
                      <CheckCircleOutlined /> 签到
                    </a-button>
                  </template>
                  <!-- 学员签退按钮 -->
                  <template v-if="authStore.isStudent && isEnrolled && hasActiveCheckout">
                    <a-button
                      type="primary"
                      size="small"
                      @click="studentCheckoutConfirmVisible = true"
                    >
                      <CheckCircleOutlined /> 签退
                    </a-button>
                  </template>
                </div>
              </div>
            </div>

            <!-- 最近动态（仅本班人员可见） -->
            <div v-if="hasFullAccess" class="overview-section">
              <h3 class="section-label">最近动态</h3>
              <div class="activity-feed">
                <!-- 签到快捷提示 -->
                <div v-if="authStore.isStudent && isEnrolled && hasActiveCheckin && !hasCheckedIn" class="activity-checkin-prompt">
                  <span>当前课次正在签到中</span>
                  <a-button type="primary" size="small" @click="studentCheckinConfirmVisible = true">
                    立即签到
                  </a-button>
                </div>
                <!-- 签退快捷提示 -->
                <div v-if="authStore.isStudent && isEnrolled && hasActiveCheckout" class="activity-checkin-prompt activity-checkout-prompt">
                  <span>当前课次正在签退中</span>
                  <a-button type="primary" size="small" @click="studentCheckoutConfirmVisible = true">
                    立即签退
                  </a-button>
                </div>
                <div v-for="(a, idx) in activityList" :key="a.id ?? idx" class="activity-item">
                  <span class="activity-dot" :class="'dot-' + a.action_type" />
                  <div class="activity-body">
                    <span class="activity-content">{{ a.content }}</span>
                    <span class="activity-time">{{ formatRelativeTime(a.created_at) }}</span>
                  </div>
                </div>
                <div v-if="!activityList.length" class="activity-empty">暂无动态</div>
              </div>
            </div>

            <!-- 公告通知（仅本班人员可见） -->
            <div v-if="hasFullAccess" class="overview-section">
              <div class="section-header">
                <h3 class="section-label">公告通知</h3>
                <a-button v-if="canPublishNotice" size="small" type="primary" @click="openNoticeForm()">
                  <PlusOutlined /> 发布公告
                </a-button>
              </div>
              <a-empty v-if="!detail.notices?.length" description="暂无公告" :image="simpleImage" />
              <div v-else class="notice-list">
                <div
                  v-for="n in detail.notices"
                  :key="n.id"
                  class="notice-card"
                  @click="openNoticeDetail(n)"
                >
                  <div class="notice-card-main">
                    <h4 class="notice-card-title">{{ n.title }}</h4>
                    <p class="notice-card-summary">{{ truncate(n.content, 60) }}</p>
                  </div>
                  <div class="notice-card-side">
                    <span class="notice-card-author" v-if="n.author_name">{{ n.author_name }}</span>
                    <span class="notice-card-time">{{ formatDate(n.created_at) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ========== 课表 ========== -->
          <div v-if="activeTab === 'schedule'" class="tab-panel">
            <!-- 课表统计 -->
            <div v-if="detail.courses?.length" class="sched-stats">
              <div class="sched-stat">
                <span class="sched-stat-num">{{ detail.courses.length }}</span>
                <span class="sched-stat-label">门课程</span>
              </div>
              <div class="sched-stat">
                <span class="sched-stat-num">{{ totalSessions }}</span>
                <span class="sched-stat-label">个课次</span>
              </div>
              <div class="sched-stat">
                <span class="sched-stat-num">{{ totalHours }}</span>
                <span class="sched-stat-label">总课时</span>
              </div>
            </div>

            <a-empty v-if="!detail.courses?.length" description="暂无课程安排" />
            <div v-else class="sched-course-list">
              <div
                v-for="course in detail.courses"
                :key="course.course_key || course.name"
                class="sched-course-card"
                :class="`sched-type-${course.type || 'theory'}`"
              >
                <!-- 课程头 -->
                <div class="sched-course-top">
                  <div class="sched-course-info">
                    <h4 class="sched-course-name">{{ course.name }}</h4>
                    <div class="sched-course-meta">
                      <a-tag :color="course.type === 'practice' ? 'green' : 'blue'" size="small">
                        {{ course.type === 'practice' ? '实操' : '理论' }}
                      </a-tag>
                      <span v-if="course.instructor"><UserOutlined /> {{ course.instructor }}</span>
                      <span v-if="course.hours"><ClockCircleOutlined /> {{ course.hours }} 课时</span>
                      <span>共 {{ (course.schedules || []).length }} 个课次</span>
                    </div>
                  </div>
                </div>

                <!-- 课次时间线 -->
                <div v-if="course.schedules?.length" class="sched-timeline">
                  <div
                    v-for="(s, i) in course.schedules"
                    :key="i"
                    class="sched-session"
                    :class="{ 'is-past': isSessionPast(s), 'is-active': isSessionActive(s) }"
                  >
                    <div class="sched-dot-line">
                      <span class="sched-dot" />
                      <span v-if="i < course.schedules.length - 1" class="sched-line" />
                    </div>
                    <div class="sched-session-body">
                      <div class="sched-session-row">
                        <strong class="sched-session-date">{{ formatSessionDate(s.date) }}</strong>
                        <span class="sched-session-time">{{ s.time_range?.replace('~', ' - ') }}</span>
                        <a-tag v-if="s.status && s.status !== 'pending'" size="small" :color="sessionTagColor(s.status)">
                          {{ sessionStatusLabel(s.status) }}
                        </a-tag>
                      </div>
                      <div v-if="s.location" class="sched-session-location">
                        <EnvironmentOutlined /> {{ s.location }}
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="sched-no-session">暂无排课</div>
              </div>
            </div>
          </div>

          <!-- ========== 考试 ========== -->
          <div v-if="activeTab === 'exam'" class="tab-panel">
            <a-empty v-if="!detail.exam_sessions?.length" description="暂无考试安排" />
            <div v-else class="exam-list">
              <div v-for="exam in detail.exam_sessions" :key="exam.id" class="exam-row">
                <div class="exam-info">
                  <span class="exam-title">{{ exam.title || exam.paper_title || '考试' }}</span>
                  <span class="exam-time">{{ formatDateTime(exam.start_time) }}</span>
                </div>
                <a-button
                  v-if="authStore.isStudent && canTakeExam(exam)"
                  type="primary"
                  size="small"
                  @click="goExam(exam.id)"
                >
                  参加考试
                </a-button>
              </div>
            </div>
          </div>

          <!-- ========== 学员名单 ========== -->
          <div v-if="activeTab === 'students'" class="tab-panel">
            <div v-if="detail.students?.length" class="student-toolbar">
              <a-input-search
                v-model:value="studentSearch"
                placeholder="搜索学员姓名"
                style="width: 220px"
                allow-clear
              />
              <span class="student-count">共 {{ filteredStudents.length }} 人</span>
            </div>
            <a-empty v-if="!detail.students?.length" description="暂无学员" />
            <div v-else class="student-list">
              <div v-for="s in filteredStudents" :key="s.user_id" class="student-row">
                <a-avatar :size="32" class="student-avatar">{{ studentDisplayName(s).slice(0, 1) }}</a-avatar>
                <div class="student-info">
                  <span class="student-name">{{ studentDisplayName(s) }}</span>
                  <span v-if="s.departments?.length" class="student-dept">{{ s.departments.join(' / ') }}</span>
                </div>
                <span class="student-checkin-rate" :class="checkinRateClass(s.checkin_rate)">
                  {{ formatCheckinRate(s.checkin_rate) }}
                </span>
                <a-tag v-if="s.status && s.status !== 'approved'" size="small" :color="s.status === 'pending' ? 'orange' : 'red'">
                  {{ enrollStatusLabel(s.status) }}
                </a-tag>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ====== 公告详情弹窗 ====== -->
      <a-modal v-model:open="noticeDetailVisible" :title="noticeDetailData?.title" :footer="null" width="560px">
        <div v-if="noticeDetailData" class="notice-detail-modal">
          <div class="notice-detail-meta">
            <span v-if="noticeDetailData.author_name">{{ noticeDetailData.author_name }}</span>
            <span>{{ formatDateTime(noticeDetailData.created_at) }}</span>
          </div>
          <div class="notice-detail-content">{{ noticeDetailData.content }}</div>
        </div>
      </a-modal>

      <!-- ====== 发布/编辑公告弹窗 ====== -->
      <a-modal
        v-model:open="noticeFormVisible"
        :title="noticeFormId ? '编辑公告' : '发布公告'"
        @ok="handleNoticeSubmit"
        :confirm-loading="noticeSubmitting"
        ok-text="发布"
      >
        <a-form layout="vertical" style="margin-top: 16px">
          <a-form-item label="标题" required>
            <a-input v-model:value="noticeForm.title" placeholder="请输入公告标题" :maxlength="200" />
          </a-form-item>
          <a-form-item label="内容" required>
            <a-textarea v-model:value="noticeForm.content" placeholder="请输入公告内容" :rows="5" />
          </a-form-item>
        </a-form>
      </a-modal>

      <!-- ====== 签到管理弹窗（教官） ====== -->
      <a-modal
        v-model:open="checkinMgrVisible"
        title="签到管理"
        :footer="null"
        width="640px"
        :class="{ 'checkin-mgr-modal-mobile': isMobile }"
        :style="isMobile ? { top: 0, maxWidth: '100vw', margin: 0, paddingBottom: 0 } : {}"
        :bodyStyle="isMobile ? { height: 'calc(100vh - 55px)', overflow: 'auto' } : {}"
      >
        <!-- 上部：签到配置区 -->
        <div class="checkin-config">
          <div class="config-row">
            <span class="config-label">签到途径</span>
            <a-radio-group
              :value="checkinMode"
              :disabled="isCheckinOngoing"
              @change="onCheckinModeChange"
            >
              <a-radio value="direct">直接签到</a-radio>
              <a-radio value="qr">扫码签到</a-radio>
            </a-radio-group>
            <span style="font-size:11px;color:red;margin-left:8px">[debug: {{ checkinMode }}]</span>
          </div>
          <div class="config-row">
            <span class="config-label">签到限时</span>
            <a-select
              :value="checkinDuration"
              style="width: 120px"
              :disabled="isCheckinOngoing"
              @change="(val: number) => { checkinDuration = val }"
            >
              <a-select-option :value="5">5 分钟</a-select-option>
              <a-select-option :value="10">10 分钟</a-select-option>
              <a-select-option :value="15">15 分钟</a-select-option>
              <a-select-option :value="30">30 分钟</a-select-option>
            </a-select>
          </div>
          <div v-if="checkinMode === 'qr' && checkinQrUrl && isCheckinOngoing" class="qr-display">
            <QrcodeVue :value="checkinQrUrl" :size="200" level="M" />
            <span class="qr-hint">学员扫描此二维码完成签到</span>
          </div>
        </div>

        <!-- 中部：签到统计 -->
        <div class="checkin-stats">
          <div class="stat-progress">
            <span>已签到 {{ checkedInList.length }} / {{ totalStudents }} 人</span>
            <a-progress :percent="checkinPercent" size="small" :show-info="false" />
          </div>
          <div v-if="countdownText" class="stat-countdown">
            剩余 {{ countdownText }}
          </div>
        </div>

        <!-- 下部：签到名单 -->
        <a-tabs v-model:activeKey="checkinTab" size="small" style="margin-top: 8px">
          <a-tab-pane key="checked" :tab="`已签到 (${checkedInList.length})`">
            <a-empty v-if="!checkedInList.length" description="暂无签到记录" />
            <div v-else class="checkin-list">
              <div v-for="r in checkedInList" :key="r.user_id" class="checkin-row">
                <a-avatar :size="28" class="checkin-avatar">{{ (r.user_nickname || r.user_name || '').slice(0, 1) }}</a-avatar>
                <div class="checkin-info">
                  <span class="checkin-name">{{ r.user_nickname || r.user_name }}</span>
                  <span class="checkin-time">{{ r.time || '' }} {{ r.status === 'late' ? '(迟到)' : '' }}</span>
                </div>
                <a-button
                  v-if="canManageCheckin"
                  size="small"
                  danger
                  @click="toggleCheckin(r.user_id, 'absent')"
                  :loading="checkinToggleLoading === r.user_id"
                >
                  标记未签到
                </a-button>
              </div>
            </div>
          </a-tab-pane>
          <a-tab-pane key="unchecked" :tab="`未签到 (${uncheckedList.length})`">
            <a-empty v-if="!uncheckedList.length" description="全部已签到" />
            <div v-else class="checkin-list">
              <div v-for="s in uncheckedList" :key="s.user_id" class="checkin-row">
                <a-avatar :size="28" class="checkin-avatar absent">{{ (s.user_nickname || s.user_name || '').slice(0, 1) }}</a-avatar>
                <div class="checkin-info">
                  <span class="checkin-name">{{ s.user_nickname || s.user_name }}</span>
                  <span class="checkin-absent-label">未签到</span>
                </div>
                <a-button
                  v-if="canManageCheckin"
                  size="small"
                  type="primary"
                  @click="toggleCheckin(s.user_id, 'checkin')"
                  :loading="checkinToggleLoading === s.user_id"
                >
                  标记已签到
                </a-button>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>

        <!-- 底部按钮区 -->
        <div class="checkin-mgr-footer">
          <a-button
            v-if="currentSession?.action_permissions?.can_start_checkin"
            type="primary"
            :loading="sessionActionLoading"
            @click="doStartCheckin"
          >
            开始签到
          </a-button>
          <a-button
            v-if="currentSession?.action_permissions?.can_end_checkin"
            danger
            :loading="sessionActionLoading"
            @click="doSessionAction('checkin/end')"
          >
            结束签到
          </a-button>
          <a-button v-if="isCheckinEnded" @click="checkinMgrVisible = false">
            关闭
          </a-button>
        </div>
      </a-modal>

      <!-- ====== 签退管理弹窗（教官） ====== -->
      <a-modal
        v-model:open="checkoutMgrVisible"
        title="签退管理"
        :footer="null"
        width="640px"
        :class="{ 'checkin-mgr-modal-mobile': isMobile }"
        :style="isMobile ? { top: 0, maxWidth: '100vw', margin: 0, paddingBottom: 0 } : {}"
        :bodyStyle="isMobile ? { height: 'calc(100vh - 55px)', overflow: 'auto' } : {}"
      >
        <!-- 上部：签退配置区 -->
        <div class="checkin-config">
          <div class="config-row">
            <span class="config-label">签退途径</span>
            <a-radio-group
              :value="checkoutMode"
              :disabled="isCheckoutOngoing"
              @change="(e: any) => { checkoutMode = e.target.value }"
            >
              <a-radio value="direct">直接签退</a-radio>
              <a-radio value="qr">扫码签退</a-radio>
            </a-radio-group>
          </div>
          <div class="config-row">
            <span class="config-label">签退限时</span>
            <a-select
              :value="checkoutDurationMin"
              style="width: 120px"
              :disabled="isCheckoutOngoing"
              @change="(val: number) => { checkoutDurationMin = val }"
            >
              <a-select-option :value="5">5 分钟</a-select-option>
              <a-select-option :value="10">10 分钟</a-select-option>
              <a-select-option :value="15">15 分钟</a-select-option>
              <a-select-option :value="30">30 分钟</a-select-option>
            </a-select>
          </div>
          <div v-if="checkoutMode === 'qr' && checkinQrUrl && isCheckoutOngoing" class="qr-display">
            <QrcodeVue :value="checkinQrUrl" :size="200" level="M" />
            <span class="qr-hint">学员扫描此二维码完成签退</span>
          </div>
        </div>

        <!-- 中部：签退统计 -->
        <div class="checkin-stats">
          <div class="stat-progress">
            <span>已签退 {{ checkedOutList.length }} / {{ totalStudents }} 人</span>
            <a-progress :percent="checkoutPercent" size="small" :show-info="false" />
          </div>
        </div>

        <!-- 下部：签退名单 -->
        <a-tabs v-model:activeKey="checkoutTab" size="small" style="margin-top: 8px">
          <a-tab-pane key="checked" :tab="`已签退 (${checkedOutList.length})`">
            <a-empty v-if="!checkedOutList.length" description="暂无签退记录" />
            <div v-else class="checkin-list">
              <div v-for="r in checkedOutList" :key="r.user_id" class="checkin-row">
                <a-avatar :size="28" class="checkin-avatar">{{ (r.user_nickname || r.user_name || '').slice(0, 1) }}</a-avatar>
                <div class="checkin-info">
                  <span class="checkin-name">{{ r.user_nickname || r.user_name }}</span>
                  <span class="checkin-time">{{ r.checkout_time || '' }}</span>
                </div>
              </div>
            </div>
          </a-tab-pane>
          <a-tab-pane key="unchecked" :tab="`未签退 (${notCheckedOutList.length})`">
            <a-empty v-if="!notCheckedOutList.length" description="全部已签退" />
            <div v-else class="checkin-list">
              <div v-for="s in notCheckedOutList" :key="s.user_id" class="checkin-row">
                <a-avatar :size="28" class="checkin-avatar absent">{{ (s.user_nickname || s.user_name || '').slice(0, 1) }}</a-avatar>
                <div class="checkin-info">
                  <span class="checkin-name">{{ s.user_nickname || s.user_name }}</span>
                  <span class="checkin-absent-label">未签退</span>
                </div>
                <a-button
                  v-if="canManageCheckin"
                  size="small"
                  type="primary"
                  @click="toggleCheckout(s.user_id)"
                  :loading="checkoutToggleLoading === s.user_id"
                >
                  标记已签退
                </a-button>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>

        <!-- 底部按钮区 -->
        <div class="checkin-mgr-footer">
          <a-button
            v-if="currentSession?.action_permissions?.can_start_checkout && !isCheckoutOngoing"
            type="primary"
            :loading="sessionActionLoading"
            @click="doStartCheckoutAction"
          >
            开始签退
          </a-button>
          <a-button
            v-if="currentSession?.action_permissions?.can_end_checkout"
            danger
            :loading="sessionActionLoading"
            @click="doEndCheckoutAction"
          >
            结束签退
          </a-button>
          <a-button v-if="currentSession?.status === 'completed'" @click="checkoutMgrVisible = false">
            关闭
          </a-button>
        </div>
      </a-modal>

      <!-- ====== 学员签到确认弹窗 ====== -->
      <a-modal
        v-model:open="studentCheckinConfirmVisible"
        title="确认签到"
        :ok-text="'确认签到'"
        :confirm-loading="studentCheckinLoading"
        @ok="handleStudentCheckin"
        centered
        width="360px"
      >
        <div class="student-checkin-confirm">
          <CheckCircleOutlined class="student-checkin-icon" />
          <p>确认为当前课次进行签到？</p>
          <p class="student-checkin-session-info" v-if="currentSession">
            {{ currentSession.course_name }} · {{ currentSession.time_range?.replace('~', ' - ') }}
          </p>
        </div>
      </a-modal>

      <!-- ====== 学员签退确认弹窗 ====== -->
      <a-modal
        v-model:open="studentCheckoutConfirmVisible"
        title="确认签退"
        :ok-text="'确认签退'"
        :confirm-loading="studentCheckoutLoading"
        @ok="handleStudentCheckout"
        centered
        width="360px"
      >
        <div class="student-checkin-confirm">
          <CheckCircleOutlined class="student-checkin-icon" />
          <p>确认为当前课次进行签退？</p>
          <p class="student-checkin-session-info" v-if="currentSession">
            {{ currentSession.course_name }} · {{ currentSession.time_range?.replace('~', ' - ') }}
          </p>
        </div>
      </a-modal>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  UserOutlined,
  TeamOutlined,
  EnvironmentOutlined,
  CalendarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  HistoryOutlined,
  PlusOutlined,
} from '@ant-design/icons-vue'
import { Empty, message } from 'ant-design-vue'
import QrcodeVue from 'qrcode.vue'
import dayjs from 'dayjs'
import axiosInstance from '@/api/custom-instance'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const activeTab = ref('overview')
const simpleImage = Empty.PRESENTED_IMAGE_SIMPLE

// ---- interfaces ----

interface ScheduleItem {
  date: string
  time_range: string
  location?: string
  status?: string
  session_id?: string
  hours?: number
}

interface CourseItem {
  course_key?: string
  name: string
  type?: string
  instructor?: string
  hours?: number
  schedules?: ScheduleItem[]
}

interface ExamItem {
  id: number
  title?: string
  paper_title?: string
  start_time?: string
  end_time?: string
  status?: string
}

interface StudentItem {
  user_id: number
  user_name?: string
  user_nickname?: string
  departments?: string[]
  status?: string
  checkin_rate?: number | null
}

interface NoticeItem {
  id: number
  title: string
  content?: string
  author_name?: string
  created_at?: string
}

interface SessionActionPermissions {
  can_start_checkin: boolean
  can_end_checkin: boolean
  can_start_checkout: boolean
  can_end_checkout: boolean
  can_skip: boolean
}

interface CurrentSession {
  course_id: number
  course_name: string
  session_id: string
  session_label: string
  date: string
  time_range: string
  status: string
  location?: string
  primary_instructor_id?: number
  primary_instructor_name?: string
  action_permissions?: SessionActionPermissions
  checkin_mode?: 'direct' | 'qr' | null
  checkin_duration_minutes?: number | null
  checkin_deadline?: string | null
  checkin_qr_token?: string | null
}

interface CheckinRecord {
  user_id: number
  user_name?: string
  user_nickname?: string
  status: string
  time?: string
  date?: string
  session_key?: string
  checkout_time?: string
  checkout_status?: string
}

interface ActivityItem {
  id: number
  training_id: number
  user_id: number | null
  user_name: string | null
  action_type: string
  content: string
  extra_json: Record<string, unknown> | null
  created_at: string | null
}

interface ClassDetail {
  id: number
  name: string
  type: string
  training_type_name: string | null
  status: string
  publish_status: string
  description: string
  start_date: string
  end_date: string
  location: string
  capacity: number | null
  enrolled_count: number
  instructor_id: number | null
  instructor_name: string
  department_name: string
  training_base_name: string
  class_code: string
  is_locked: boolean
  enrollment_requires_approval: boolean
  current_enrollment_status: string | null
  can_enter_training: boolean
  current_step_key: string
  current_session: CurrentSession | null
  courses: CourseItem[]
  exam_sessions: ExamItem[]
  students: StudentItem[]
  notices: NoticeItem[]
  checkin_records: { session_key?: string; status?: string; user_id?: number }[]
}

const detail = ref<ClassDetail | null>(null)
const studentSearch = ref('')

// ---- 公告相关 ----
const noticeDetailVisible = ref(false)
const noticeDetailData = ref<NoticeItem | null>(null)
const noticeFormVisible = ref(false)
const noticeFormId = ref<number | null>(null)
const noticeSubmitting = ref(false)
const noticeForm = ref({ title: '', content: '' })

// ---- 签到相关 ----
const sessionActionLoading = ref(false)
const checkinMgrVisible = ref(false)
const checkinTab = ref('checked')
const checkinRecords = ref<CheckinRecord[]>([])
const checkinToggleLoading = ref<number | null>(null)
const checkinMode = ref<'direct' | 'qr'>('direct')
const checkinDuration = ref(10)
const countdownText = ref('')
const countdownTimer = ref<ReturnType<typeof setInterval> | null>(null)
const isMobile = ref(window.innerWidth <= 768)

// ---- 签退管理 ----
const checkoutMgrVisible = ref(false)
const checkoutTab = ref('checked')
const checkoutRecords = ref<CheckinRecord[]>([])
const checkoutToggleLoading = ref<number | null>(null)
const checkoutMode = ref<'direct' | 'qr'>('direct')
const checkoutDurationMin = ref(10)

// 学员签到相关
const studentCheckinConfirmVisible = ref(false)
const studentCheckinLoading = ref(false)
const studentCheckoutConfirmVisible = ref(false)
const studentCheckoutLoading = ref(false)

// ---- 最近动态 ----
const activityList = ref<ActivityItem[]>([])
let activityWs: WebSocket | null = null

async function fetchActivities() {
  try {
    const res = await axiosInstance.get(`/trainings/${route.params.id}/activities`, { params: { limit: 20 } })
    activityList.value = (res.data as ActivityItem[]) || []
  } catch { activityList.value = [] }
}

function connectActivityWs() {
  const token = localStorage.getItem('token')
  if (!token) return
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = import.meta.env.VITE_API_BASE_URL
    ? new URL(import.meta.env.VITE_API_BASE_URL as string).host
    : location.host
  const url = `${protocol}//${host}/ws/trainings/${route.params.id}/activities?token=${token}`

  activityWs = new WebSocket(url)
  activityWs.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as ActivityItem
      activityList.value.unshift(data)
      if (activityList.value.length > 50) activityList.value.pop()
    } catch { /* ignore malformed messages */ }
  }
  activityWs.onclose = () => { activityWs = null }
}

function disconnectActivityWs() {
  if (activityWs) { activityWs.close(); activityWs = null }
}

function formatRelativeTime(time: string | null | undefined): string {
  if (!time) return ''
  const diff = Date.now() - new Date(time).getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  return dayjs(time).format('MM/DD HH:mm')
}

// ---- computed ----

const filteredStudents = computed(() => {
  const list = detail.value?.students || []
  const kw = studentSearch.value.trim().toLowerCase()
  if (!kw) return list
  return list.filter((s) => {
    const name = (s.user_nickname || s.user_name || '').toLowerCase()
    return name.includes(kw)
  })
})

const statusLabels: Record<string, string> = {
  upcoming: '未开始',
  active: '进行中',
  ended: '已结束',
}

const isEnrolled = computed(() => detail.value?.current_enrollment_status === 'approved')

const canEnroll = computed(() => {
  const d = detail.value
  if (!d) return false
  if (d.current_enrollment_status) return false
  if (d.status === 'ended') return false
  if (d.publish_status !== 'published') return false
  if (d.is_locked) return false
  return true
})

const hasActiveCheckin = computed(() => detail.value?.current_session?.status === 'checkin_open')
const hasActiveCheckout = computed(() => detail.value?.current_session?.status === 'checkout_open')

// 当前用户是否已对当前课次签到（从 checkin_records 中判断）
const hasCheckedIn = computed(() => {
  const sess = detail.value?.current_session
  if (!sess) return false
  const records = detail.value?.checkin_records || []
  return records.some((r: { session_key?: string; status?: string }) =>
    r.session_key === sess.session_id && r.status !== 'absent',
  )
})

// 判断当前用户是否有完整访问权限（后端对非相关用户返回空课表/通知）
const hasFullAccess = computed(() => {
  const d = detail.value
  if (!d) return false
  return !!(d.courses?.length || d.notices?.length || d.exam_sessions?.length || isEnrolled.value)
})

// 教官可以在班级内发布公告（且需要有完整访问权限）
const canPublishNotice = computed(() => authStore.isInstructor && hasFullAccess.value)

// 课表统计
const totalSessions = computed(() =>
  (detail.value?.courses || []).reduce((sum, c) => sum + (c.schedules || []).length, 0),
)
const totalHours = computed(() => {
  const h = (detail.value?.courses || []).reduce((sum, c) => sum + (c.hours || 0), 0)
  return Number.isInteger(h) ? h : h.toFixed(1)
})

function isSessionPast(s: ScheduleItem): boolean {
  if (!s.date) return false
  return s.date < dayjs().format('YYYY-MM-DD')
}

function isSessionActive(s: ScheduleItem): boolean {
  if (!s.status) return false
  return ['checkin_open', 'checkin_closed', 'checkout_open'].includes(s.status)
}

function formatSessionDate(date: string | undefined): string {
  if (!date) return '-'
  const d = dayjs(date)
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${d.format('MM/DD')} ${weekdays[d.day()]}`
}

function sessionTagColor(status: string): string {
  const map: Record<string, string> = {
    checkin_open: 'processing', checkin_closed: 'processing', checkout_open: 'warning',
    completed: 'success', skipped: 'default', missed: 'error',
  }
  return map[status] || 'default'
}

const visibleTabs = computed(() => {
  if (!hasFullAccess.value) {
    return [{ key: 'overview', label: '概览' }]
  }
  const tabs = [
    { key: 'overview', label: '概览' },
    { key: 'schedule', label: '课程' },
    { key: 'exam', label: '考试' },
  ]
  if (authStore.isInstructor) {
    tabs.push({ key: 'students', label: '学员名单' })
  }
  return tabs
})

// 当前/下一节课次
const currentSession = computed(() => detail.value?.current_session || null)

const currentSessionSchedule = computed<ScheduleItem | null>(() => {
  if (!currentSession.value) return null
  return { date: currentSession.value.date, time_range: currentSession.value.time_range, status: currentSession.value.status }
})

const isCheckinOrCheckoutPhase = computed(() => {
  const s = currentSession.value?.status
  return s === 'checkin_open' || s === 'checkin_closed' || s === 'checkout_open'
})

const isCheckoutPhase = computed(() => {
  const s = currentSession.value?.status
  return s === 'checkout_open'
})

// 保留旧名兼容其他引用
const isCheckinStarted = isCheckinOrCheckoutPhase

// 二维码完整 URL
const checkinQrUrl = computed(() => {
  const token = currentSession.value?.checkin_qr_token
  const sessionId = currentSession.value?.session_id
  if (!token || !sessionId) return ''
  const base = window.location.origin
  return `${base}/mobile/checkin/${token}/${sessionId}`
})

const canManageCheckin = computed(() => {
  return authStore.isInstructor && currentSession.value?.action_permissions != null
})

// 签到进行中
const isCheckinOngoing = computed(() => currentSession.value?.status === 'checkin_open')

// 签到已结束（已关闭签到或后续状态）
const isCheckinEnded = computed(() => {
  const s = currentSession.value?.status
  return s === 'checkin_closed' || s === 'checkout_open' || s === 'completed'
})

// 已签到 / 未签到列表
const checkedInList = computed(() =>
  checkinRecords.value.filter((r) => r.status === 'on_time' || r.status === 'late'),
)

const uncheckedList = computed(() => {
  const checkedIds = new Set(checkedInList.value.map((r) => r.user_id))
  return (detail.value?.students || [])
    .filter((s) => !checkedIds.has(s.user_id))
    .map((s) => ({ user_id: s.user_id, user_name: s.user_name, user_nickname: s.user_nickname, status: 'absent', time: '' }))
})

const totalStudents = computed(() => detail.value?.students?.length || 0)

const checkinPercent = computed(() => {
  if (!totalStudents.value) return 0
  return Math.round((checkedInList.value.length / totalStudents.value) * 100)
})

// ---- 签退 computed ----
const isCheckoutOngoing = computed(() => currentSession.value?.status === 'checkout_open')

const checkedOutList = computed(() =>
  checkoutRecords.value.filter((r) => r.checkout_status === 'completed'),
)

const notCheckedOutList = computed(() => {
  const outIds = new Set(checkedOutList.value.map((r) => r.user_id))
  return (detail.value?.students || [])
    .filter((s) => !outIds.has(s.user_id))
    .map((s) => ({ user_id: s.user_id, user_name: s.user_name, user_nickname: s.user_nickname, status: '', time: '' }))
})

const checkoutPercent = computed(() => {
  if (!totalStudents.value) return 0
  return Math.round((checkedOutList.value.length / totalStudents.value) * 100)
})

// ---- methods ----

function studentDisplayName(s: StudentItem): string {
  return s.user_nickname || s.user_name || String(s.user_id)
}

function formatCheckinRate(rate: number | null | undefined): string {
  if (rate === null || rate === undefined) return '-'
  return `${Math.round(rate * 100)}%`
}

function checkinRateClass(rate: number | null | undefined): string {
  if (rate === null || rate === undefined) return 'rate-na'
  if (rate >= 0.9) return 'rate-good'
  if (rate >= 0.6) return 'rate-warn'
  return 'rate-bad'
}

function sessionStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待开始', checkin_open: '签到中', checkin_closed: '进行中',
    checkout_open: '签退中', completed: '已完成', skipped: '已跳过', missed: '已缺课',
  }
  return map[status] || status
}

function enrollStatusLabel(status: string): string {
  const map: Record<string, string> = { approved: '已通过', pending: '待审核', rejected: '未通过' }
  return map[status] || status
}

function canTakeExam(exam: ExamItem): boolean {
  if (!exam.start_time) return false
  const now = Date.now()
  const start = new Date(exam.start_time).getTime()
  const end = exam.end_time ? new Date(exam.end_time).getTime() : start + 2 * 3600 * 1000
  return now >= start && now <= end
}

function formatDate(val: string | null | undefined): string {
  if (!val) return '-'
  return String(val).slice(0, 10)
}

function formatDateTime(val: string | null | undefined): string {
  if (!val) return '-'
  return String(val).slice(0, 16).replace('T', ' ')
}

function truncate(text: string | undefined | null, len: number): string {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}

function handleEnroll() { router.push(`/classes/${route.params.id}/enroll`) }
function goCheckout() { router.push(`/classes/${route.params.id}/checkout`) }
function goHistory() { message.info('训历功能即将上线') }

// 课次操作（开始签到/结束签到/开始签退/结束签退）
async function doSessionAction(action: string) {
  const sess = currentSession.value
  if (!sess) return
  sessionActionLoading.value = true
  try {
    await axiosInstance.post(`/trainings/${route.params.id}/sessions/${sess.session_id}/${action}`)
    message.success('操作成功')
    await fetchDetail()
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    sessionActionLoading.value = false
  }
}

// 打开签到管理弹窗
async function openCheckinMgr() {
  const sess = currentSession.value
  if (!sess) return
  // 如果签到已开始，用后端返回的配置；否则用默认值
  if (sess.checkin_mode === 'direct' || sess.checkin_mode === 'qr') {
    checkinMode.value = sess.checkin_mode
  }
  if (sess.checkin_duration_minutes) {
    checkinDuration.value = sess.checkin_duration_minutes
  }
  checkinTab.value = 'checked'
  try {
    const res = await axiosInstance.get(`/trainings/${route.params.id}/checkin/records`, {
      params: { session_key: sess.session_id },
    })
    checkinRecords.value = (res.data as CheckinRecord[]) || []
  } catch {
    checkinRecords.value = []
  }
  startCountdown()
  checkinMgrVisible.value = true
}

function onCheckinModeChange(e: unknown) {
  const val = (e as { target?: { value?: string } })?.target?.value
  console.log('[DEBUG] onCheckinModeChange raw event:', e)
  console.log('[DEBUG] onCheckinModeChange target.value:', val)
  console.log('[DEBUG] checkinMode BEFORE:', checkinMode.value)
  if (val === 'direct' || val === 'qr') {
    checkinMode.value = val
  }
  console.log('[DEBUG] checkinMode AFTER:', checkinMode.value)
}

// 开始签到（带配置参数）
async function doStartCheckin() {
  const sess = currentSession.value
  if (!sess) return
  console.log('[DEBUG] doStartCheckin called, checkinMode.value:', checkinMode.value, 'checkinDuration.value:', checkinDuration.value)
  const url = `/trainings/${route.params.id}/sessions/${sess.session_id}/checkin/start?checkin_mode=${checkinMode.value}&checkin_duration_minutes=${checkinDuration.value}`
  console.log('[DEBUG] doStartCheckin URL:', url)
  sessionActionLoading.value = true
  try {
    await axiosInstance.post(url)
    message.success('签到已开始')
    await fetchDetail()
    // 刷新签到记录
    const res = await axiosInstance.get(`/trainings/${route.params.id}/checkin/records`, {
      params: { session_key: sess.session_id },
    })
    checkinRecords.value = (res.data as CheckinRecord[]) || []
    startCountdown()
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    sessionActionLoading.value = false
  }
}

async function doStartCheckout() {
  const sess = currentSession.value
  if (!sess) return
  checkoutMgrVisible.value = true
}

async function openCheckoutMgr() {
  const sess = currentSession.value
  if (!sess) return
  checkoutTab.value = 'checked'
  try {
    const res = await axiosInstance.get(`/trainings/${route.params.id}/checkin/records`, {
      params: { session_key: sess.session_id },
    })
    checkoutRecords.value = (res.data as CheckinRecord[]) || []
  } catch {
    checkoutRecords.value = []
  }
  checkoutMgrVisible.value = true
}

async function doStartCheckoutAction() {
  const sess = currentSession.value
  if (!sess) return
  sessionActionLoading.value = true
  try {
    await axiosInstance.post(`/trainings/${route.params.id}/sessions/${sess.session_id}/checkout/start`)
    message.success('签退已开始')
    await fetchDetail()
    // 刷新签退记录
    const res = await axiosInstance.get(`/trainings/${route.params.id}/checkin/records`, {
      params: { session_key: sess.session_id },
    })
    checkoutRecords.value = (res.data as CheckinRecord[]) || []
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    sessionActionLoading.value = false
  }
}

async function doEndCheckoutAction() {
  const sess = currentSession.value
  if (!sess) return
  sessionActionLoading.value = true
  try {
    await axiosInstance.post(`/trainings/${route.params.id}/sessions/${sess.session_id}/checkout/end`)
    message.success('签退已结束')
    await fetchDetail()
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    sessionActionLoading.value = false
  }
}

async function toggleCheckout(userId: number) {
  const sess = currentSession.value
  if (!sess) return
  checkoutToggleLoading.value = userId
  try {
    await axiosInstance.post(`/trainings/${route.params.id}/checkout`, {
      user_id: userId,
      session_key: sess.session_id,
    })
    // 刷新签退记录
    const res = await axiosInstance.get(`/trainings/${route.params.id}/checkin/records`, {
      params: { session_key: sess.session_id },
    })
    checkoutRecords.value = (res.data as CheckinRecord[]) || []
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    checkoutToggleLoading.value = null
  }
}

// 倒计时
function startCountdown() {
  stopCountdown()
  updateCountdown()
  countdownTimer.value = setInterval(updateCountdown, 1000)
}

function stopCountdown() {
  if (countdownTimer.value) {
    clearInterval(countdownTimer.value)
    countdownTimer.value = null
  }
  countdownText.value = ''
}

function updateCountdown() {
  const deadline = currentSession.value?.checkin_deadline
  if (!deadline) {
    countdownText.value = ''
    return
  }
  const remaining = dayjs(deadline).diff(dayjs(), 'second')
  if (remaining <= 0) {
    countdownText.value = '已截止'
    stopCountdown()
    return
  }
  const mins = Math.floor(remaining / 60)
  const secs = remaining % 60
  countdownText.value = `${mins}:${String(secs).padStart(2, '0')}`
}

// 学员签到
async function handleStudentCheckin() {
  const sess = currentSession.value
  if (!sess) return
  studentCheckinLoading.value = true
  try {
    await axiosInstance.post(`/trainings/${route.params.id}/checkin`, {
      session_key: sess.session_id,
    })
    message.success('签到成功')
    studentCheckinConfirmVisible.value = false
    await fetchDetail()
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '签到失败')
  } finally {
    studentCheckinLoading.value = false
  }
}

async function handleStudentCheckout() {
  const sess = currentSession.value
  if (!sess) return
  studentCheckoutLoading.value = true
  try {
    await axiosInstance.post(`/trainings/${route.params.id}/checkout`, {
      session_key: sess.session_id,
    })
    message.success('签退成功')
    studentCheckoutConfirmVisible.value = false
    await fetchDetail()
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '签退失败')
  } finally {
    studentCheckoutLoading.value = false
  }
}

// 响应式移动端检测
function handleResize() {
  isMobile.value = window.innerWidth <= 768
}

// 切换签到状态
async function toggleCheckin(userId: number, action: 'checkin' | 'absent') {
  const sess = currentSession.value
  if (!sess) return
  checkinToggleLoading.value = userId
  try {
    if (action === 'checkin') {
      await axiosInstance.post(`/trainings/${route.params.id}/checkin`, {
        user_id: userId,
        session_key: sess.session_id,
      })
    } else {
      // 标记为缺勤：用 checkin 接口 status=absent
      await axiosInstance.post(`/trainings/${route.params.id}/checkin`, {
        user_id: userId,
        session_key: sess.session_id,
        status: 'absent',
      })
    }
    // 刷新签到记录
    const res = await axiosInstance.get(`/trainings/${route.params.id}/checkin/records`, {
      params: { session_key: sess.session_id },
    })
    checkinRecords.value = (res.data as CheckinRecord[]) || []
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '操作失败')
  } finally {
    checkinToggleLoading.value = null
  }
}
function goExam(examId: number) { router.push(`/exam/do/${examId}`) }

// 公告详情弹窗
function openNoticeDetail(n: NoticeItem) {
  noticeDetailData.value = n
  noticeDetailVisible.value = true
}

// 发布公告
function openNoticeForm() {
  noticeFormId.value = null
  noticeForm.value = { title: '', content: '' }
  noticeFormVisible.value = true
}

async function handleNoticeSubmit() {
  if (!noticeForm.value.title.trim() || !noticeForm.value.content.trim()) {
    message.warning('请填写标题和内容')
    return
  }
  noticeSubmitting.value = true
  try {
    const payload = {
      title: noticeForm.value.title.trim(),
      content: noticeForm.value.content.trim(),
      type: 'training',
      training_id: Number(route.params.id),
    }
    await axiosInstance.post('/notices', payload)
    message.success('公告发布成功')
    noticeFormVisible.value = false
    await fetchDetail()
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '发布失败')
  } finally {
    noticeSubmitting.value = false
  }
}

async function fetchDetail() {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    const res = await axiosInstance.get(`/trainings/${id}`)
    detail.value = res.data as ClassDetail
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '加载班级详情失败')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchDetail()
  if (detail.value) {
    fetchActivities()
    connectActivityWs()
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  stopCountdown()
  disconnectActivityWs()
  window.removeEventListener('resize', handleResize)
})

// 弹窗关闭时停止倒计时
watch(checkinMgrVisible, (visible) => {
  if (!visible) stopCountdown()
})
</script>

<style scoped>
/* ====== 深色头部 ====== */
.detail-header {
  background: var(--v2-bg-header);
  padding: 28px 32px 24px;
}

@media (max-width: 768px) {
  .detail-header { padding: 20px 16px 16px; }
}

.header-body {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

@media (max-width: 900px) {
  .header-body { flex-direction: column; }
}

.header-left { flex: 1; min-width: 0; }

.header-title {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 14px;
  line-height: 1.2;
}

.header-meta-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: rgba(255,255,255,0.82);
}

.chip-icon { width: 14px; height: 14px; }
.chip-icon-ant { font-size: 13px; }

.header-sub-row {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: rgba(255,255,255,0.5);
  flex-wrap: wrap;
}

.header-desc {
  margin-top: 10px;
  font-size: 13px;
  color: rgba(255,255,255,0.55);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* -- 右侧信息卡片 -- */
.header-cards {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

@media (max-width: 900px) {
  .header-cards { width: 100%; }
}

.info-card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--v2-radius-sm);
  padding: 14px 18px;
  min-width: 120px;
  flex: 1;
  transition: background 0.2s;
}

.info-card:hover { background: rgba(255, 255, 255, 0.12); }

.info-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.info-card--status { flex: 1.6; min-width: 180px; }

.info-card-extra {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  display: flex;
  gap: 4px;
}

.info-card-label { font-size: 12px; color: rgba(255, 255, 255, 0.5); }

.info-card-badge {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: var(--v2-radius-full);
}

.badge-upcoming { background: rgba(75, 110, 245, 0.25); color: #8DA6F8; }
.badge-active   { background: rgba(52, 199, 89, 0.25);  color: #6EE49A; }
.badge-ended    { background: rgba(255, 255, 255, 0.1);  color: rgba(255, 255, 255, 0.4); }

.info-card-num { font-size: 18px; font-weight: 600; color: #fff; }
.info-unit { font-size: 12px; font-weight: 400; color: rgba(255, 255, 255, 0.45); }

/* ====== 主体 ====== */
.detail-body { padding-top: 20px; }

.action-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

/* -- Tab 栏 -- */
.content-tabs {
  background: var(--v2-bg-card);
  border-radius: var(--v2-radius);
  overflow: hidden;
}

.tab-bar {
  display: flex;
  border-bottom: 1px solid var(--v2-border-light);
  padding: 0 20px;
}

.tab-item {
  padding: 14px 18px;
  font-size: 14px;
  color: var(--v2-text-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s;
  white-space: nowrap;
}

.tab-item:hover { color: var(--v2-text-secondary); }

.tab-item.active {
  color: var(--v2-primary);
  font-weight: 500;
  border-bottom-color: var(--v2-primary);
}

.tab-panel { padding: 20px; min-height: 200px; }

/* ====== 概览 ====== */
.overview-section { margin-bottom: 28px; }
.overview-section:last-child { margin-bottom: 0; }

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-header .section-label { margin-bottom: 0; }

.section-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin-bottom: 12px;
}

.overview-desc-text {
  white-space: pre-wrap;
  color: var(--v2-text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.overview-desc-empty {
  color: var(--v2-text-muted);
  font-size: 14px;
}

/* -- 最近动态 -- */
.activity-feed {
  display: flex;
  flex-direction: column;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 8px 0;
}

.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
  background: var(--v2-text-muted);
}

.dot-checkin { background: var(--v2-success); }
.dot-checkout { background: var(--v2-primary); }
.dot-session_checkin_start,
.dot-session_checkin_end,
.dot-session_checkout_start,
.dot-session_checkout_end,
.dot-notice { background: var(--v2-warning); }
.dot-enroll { background: #8b5cf6; }

.activity-body {
  flex: 1;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  min-width: 0;
}

.activity-content {
  font-size: 13px;
  color: var(--v2-text-secondary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.activity-time {
  font-size: 12px;
  color: var(--v2-text-muted);
  flex-shrink: 0;
  text-align: right;
}

.activity-empty {
  padding: 16px 0;
  text-align: center;
  font-size: 13px;
  color: var(--v2-text-muted);
}

.activity-checkin-prompt {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  margin-bottom: 8px;
  border-radius: var(--v2-radius-sm);
  background: rgba(52, 199, 89, 0.08);
  font-size: 13px;
  color: var(--v2-success);
  font-weight: 500;
}

.activity-checkout-prompt {
  background: rgba(75, 110, 245, 0.08);
  color: var(--v2-primary);
}

@media (max-width: 768px) {
  .activity-body {
    flex-direction: column;
    gap: 2px;
  }
  .activity-time {
    text-align: left;
  }
}

/* -- 当前课次卡片 -- */
.current-session-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  border-radius: var(--v2-radius);
  background: var(--v2-bg);
  border: 1px solid var(--v2-border-light);
  flex-wrap: wrap;
}

.current-session-card.is-active {
  background: var(--v2-primary-light);
  border-color: rgba(75, 110, 245, 0.2);
}

.cs-left {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
  min-width: 0;
}

.cs-date-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 40px;
}

.cs-day {
  font-size: 22px;
  font-weight: 700;
  color: var(--v2-text-primary);
  line-height: 1;
}

.cs-weekday {
  font-size: 11px;
  color: var(--v2-text-muted);
  margin-top: 2px;
}

.cs-body { flex: 1; min-width: 0; }

.cs-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.cs-course {
  font-size: 15px;
  color: var(--v2-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cs-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--v2-text-muted);
  flex-wrap: wrap;
}

.cs-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.cs-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  flex-wrap: wrap;
}

/* -- 签到详情弹窗 -- */
.checkin-list {
  display: flex;
  flex-direction: column;
}

.checkin-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 4px;
  border-bottom: 1px solid var(--v2-border-light);
}

.checkin-row:last-child { border-bottom: none; }

.checkin-avatar {
  background: var(--v2-success);
  color: #fff;
  font-size: 12px;
  flex-shrink: 0;
}

.checkin-avatar.absent {
  background: var(--v2-text-muted);
}

.checkin-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.checkin-name {
  font-size: 14px;
  color: var(--v2-text-primary);
}

.checkin-time {
  font-size: 12px;
  color: var(--v2-text-muted);
}

.checkin-absent-label {
  font-size: 12px;
  color: var(--v2-danger);
}

/* -- 公告卡片 -- */
.notice-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.notice-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border-radius: var(--v2-radius-sm);
  border: 1px solid var(--v2-border-light);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.notice-card:hover {
  background: var(--v2-bg);
  border-color: var(--v2-border);
}

.notice-card-main { flex: 1; min-width: 0; }

.notice-card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin: 0 0 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notice-card-summary {
  font-size: 13px;
  color: var(--v2-text-muted);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notice-card-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}

.notice-card-author { font-size: 12px; color: var(--v2-text-secondary); }
.notice-card-time { font-size: 11px; color: var(--v2-text-muted); }

/* -- 公告详情弹窗 -- */
.notice-detail-meta {
  display: flex;
  gap: 12px;
  font-size: 13px;
  color: var(--v2-text-muted);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--v2-border-light);
}

.notice-detail-content {
  font-size: 14px;
  color: var(--v2-text-primary);
  line-height: 1.8;
  white-space: pre-wrap;
}

/* ====== 课表 ====== */
.sched-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.sched-stat {
  display: flex;
  align-items: baseline;
  gap: 4px;
  padding: 10px 16px;
  border-radius: var(--v2-radius-sm);
  background: var(--v2-bg);
}

.sched-stat-num { font-size: 20px; font-weight: 700; color: var(--v2-primary); }
.sched-stat-label { font-size: 12px; color: var(--v2-text-muted); }

.sched-course-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sched-course-card {
  border-radius: var(--v2-radius);
  border: 1px solid var(--v2-border-light);
  overflow: hidden;
}

.sched-course-top {
  padding: 16px 18px;
  border-bottom: 1px solid var(--v2-border-light);
}

.sched-type-theory .sched-course-top { background: linear-gradient(135deg, rgba(75,110,245,0.04) 0%, transparent 100%); }
.sched-type-practice .sched-course-top { background: linear-gradient(135deg, rgba(52,199,89,0.04) 0%, transparent 100%); }

.sched-course-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin: 0 0 8px;
}

.sched-course-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 12px;
  color: var(--v2-text-muted);
  flex-wrap: wrap;
}

.sched-course-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* -- 时间线 -- */
.sched-timeline {
  padding: 16px 18px 12px;
}

.sched-session {
  display: flex;
  gap: 14px;
  position: relative;
}

.sched-dot-line {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 12px;
  flex-shrink: 0;
  padding-top: 6px;
}

.sched-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--v2-border);
  flex-shrink: 0;
  z-index: 1;
}

.sched-session.is-active .sched-dot {
  background: var(--v2-primary);
  box-shadow: 0 0 0 3px rgba(75,110,245,0.2);
}

.sched-session.is-past .sched-dot { background: var(--v2-text-muted); }

.sched-line {
  width: 1px;
  flex: 1;
  background: var(--v2-border-light);
  margin: 4px 0;
}

.sched-session-body {
  flex: 1;
  padding-bottom: 16px;
  min-width: 0;
}

.sched-session:last-child .sched-session-body { padding-bottom: 4px; }

.sched-session-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 2px;
}

.sched-session-date {
  font-size: 14px;
  color: var(--v2-text-primary);
  min-width: 90px;
}

.sched-session.is-past .sched-session-date { color: var(--v2-text-muted); }

.sched-session-time {
  font-size: 13px;
  color: var(--v2-text-secondary);
  min-width: 110px;
  font-variant-numeric: tabular-nums;
}

.sched-session.is-past .sched-session-time { color: var(--v2-text-muted); }

.sched-session-location {
  font-size: 12px;
  color: var(--v2-text-muted);
  display: flex;
  align-items: center;
  gap: 4px;
}

.sched-no-session {
  padding: 20px 18px;
  font-size: 13px;
  color: var(--v2-text-muted);
  text-align: center;
}

@media (max-width: 768px) {
  .sched-stats { flex-wrap: wrap; }
  .sched-stat { flex: 1; min-width: 80px; }
}

/* ====== 考试 ====== */
.exam-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid var(--v2-border-light);
}

.exam-row:last-child { border-bottom: none; }
.exam-title { font-size: 14px; font-weight: 500; color: var(--v2-text-primary); }
.exam-time { font-size: 12px; color: var(--v2-text-muted); margin-top: 2px; }
.exam-info { display: flex; flex-direction: column; }

/* ====== 学员名单 ====== */
.student-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  gap: 12px;
}

.student-count { font-size: 13px; color: var(--v2-text-muted); white-space: nowrap; }

.student-list { display: flex; flex-direction: column; }

.student-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 8px;
  border-bottom: 1px solid var(--v2-border-light);
  transition: background 0.15s;
}

.student-row:last-child { border-bottom: none; }
.student-row:hover { background: var(--v2-bg); }

.student-avatar { background: var(--v2-primary); color: #fff; font-size: 13px; flex-shrink: 0; }

.student-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.student-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--v2-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.student-dept {
  font-size: 12px;
  color: var(--v2-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.student-checkin-rate {
  font-size: 13px;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  min-width: 40px;
  text-align: right;
  flex-shrink: 0;
}

.rate-na { color: var(--v2-text-muted); }
.rate-good { color: var(--v2-success); }
.rate-warn { color: var(--v2-warning); }
.rate-bad { color: var(--v2-danger); }

/* ====== 签到管理弹窗 ====== */
.checkin-config {
  padding: 16px;
  background: var(--v2-bg);
  border-radius: var(--v2-radius-sm);
  margin-bottom: 16px;
}

.config-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.config-row:last-child { margin-bottom: 0; }

.config-label {
  font-size: 14px;
  color: var(--v2-text-secondary);
  min-width: 70px;
  flex-shrink: 0;
}

.qr-display {
  margin-top: 16px;
  padding: 24px;
  background: #fff;
  border: 1px solid var(--v2-border-light);
  border-radius: var(--v2-radius);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.qr-hint {
  font-size: 13px;
  color: var(--v2-text-muted);
}

.checkin-stats {
  padding: 12px 16px;
  background: var(--v2-bg);
  border-radius: var(--v2-radius-sm);
  margin-bottom: 12px;
}

.stat-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: var(--v2-text-primary);
}

.stat-progress span { white-space: nowrap; flex-shrink: 0; }
.stat-progress .ant-progress { flex: 1; }

.stat-countdown {
  margin-top: 8px;
  font-size: 13px;
  color: var(--v2-warning);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}

.checkin-mgr-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--v2-border-light);
}

/* 学员签到确认弹窗 */
.student-checkin-confirm {
  text-align: center;
  padding: 16px 0;
}

.student-checkin-icon {
  font-size: 48px;
  color: var(--v2-primary);
  margin-bottom: 16px;
}

.student-checkin-confirm p {
  font-size: 15px;
  color: var(--v2-text-primary);
  margin: 0 0 8px;
}

.student-checkin-session-info {
  font-size: 13px;
  color: var(--v2-text-muted);
}

.cs-qr-hint {
  font-size: 12px;
  color: var(--v2-warning);
  display: flex;
  align-items: center;
}

.cs-checked-label {
  font-size: 13px;
  color: var(--v2-success);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 移动端签到管理弹窗 */
@media (max-width: 768px) {
  .checkin-config {
    padding: 12px;
  }

  .config-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }

  .checkin-list .checkin-row {
    padding: 8px 2px;
    gap: 8px;
  }

  .checkin-mgr-footer {
    flex-direction: column;
  }

  .checkin-mgr-footer .ant-btn {
    min-height: 44px;
    width: 100%;
  }

  .student-checkin-confirm .ant-btn {
    min-height: 44px;
  }
}
</style>
