<template>
  <div class="exam-page">
    <!-- 移动端顶部 Header -->
    <header class="exam-mobile-header">
      <div class="exam-mobile-header-left">
        <span class="exam-mobile-header-mark"></span>
        <div class="exam-mobile-header-copy">
          <span class="exam-mobile-title">在线考试</span>
          <span class="exam-mobile-subtitle">共 {{ exams.length }} 场考试</span>
        </div>
      </div>
      <div class="exam-mobile-avatar">{{ avatarText }}</div>
    </header>

    <!-- 主布局 -->
    <div class="exam-layout">
      <!-- 顶部功能控制区 -->
      <header class="exam-header">
        <!-- 上半部：标题与操作 -->
        <div class="exam-header-top">
          <div class="exam-header-title">
            <h1>在线考试</h1>
            <p>检验学习成果，提升实战能力。</p>
          </div>
          <div class="exam-header-controls">
            <div class="exam-search-wrapper">
              <svg class="exam-search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
              <input
                type="text"
                class="exam-search-input"
                :placeholder="searchPlaceholder"
                v-model="filters.search"
                @keyup.enter="fetchExams"
              />
            </div>
            <div class="exam-header-btns">
              <a-select v-model:value="filters.sort" class="exam-sort-select" @change="fetchExams">
                <a-select-option value="latest">按最新</a-select-option>
                <a-select-option value="upcoming">即将开始</a-select-option>
                <a-select-option value="active">进行中</a-select-option>
              </a-select>
              <a-button v-if="!isStudentView" type="primary" class="exam-create-btn" @click="openWizardModal">
                <template #icon>
                  <svg class="icon-sm" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
                  </svg>
                </template>
                创建考试
              </a-button>
            </div>
          </div>
        </div>

        <!-- 下半部：Tab与过滤栏 -->
        <div class="exam-header-bottom">
          <div class="exam-tabs">
            <button class="exam-tab" :class="{ active: activeTab === 'all' }" @click="switchTab('all')">全部考试</button>
            <button class="exam-tab" :class="{ active: activeTab === 'standalone' }" @click="switchTab('standalone')">独立考试</button>
            <button class="exam-tab" :class="{ active: activeTab === 'training' }" @click="switchTab('training')">培训班考试</button>
          </div>
          <div class="exam-status-filter">
            <button
              v-for="tab in statusTabs"
              :key="tab.key"
              class="exam-status-btn"
              :class="{ active: filters.status === tab.key }"
              @click="selectStatus(tab.key)"
            >{{ tab.label }}</button>
          </div>
        </div>
      </header>

      <!-- 数据统计摘要 -->
      <div class="exam-stats">
        <span class="exam-stats-item exam-stats-item-primary">共 <strong>{{ exams.length }}</strong> 场考试</span>
        <span v-if="ongoingCount > 0" class="exam-stats-item">进行中 <strong>{{ ongoingCount }}</strong> 场</span>
        <span v-if="upcomingCount > 0" class="exam-stats-item">即将开始 <strong>{{ upcomingCount }}</strong> 场</span>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="exam-loading">
        <a-spin size="large" />
      </div>

      <!-- 空状态 -->
      <a-empty v-else-if="!exams.length" description="暂无考试" class="exam-empty" />

      <!-- 考试数据列表 -->
      <div v-else class="exam-list">
        <!-- PC端列表头 -->
        <div class="exam-list-header">
          <div class="exam-list-col exam-list-col-main">考试基本信息</div>
          <div class="exam-list-col exam-list-col-dur">时长</div>
          <div class="exam-list-col exam-list-col-qty">题量</div>
          <div class="exam-list-col exam-list-col-score">满分</div>
          <div class="exam-list-col exam-list-col-time">时间安排</div>
          <div class="exam-list-col exam-list-col-action">操作</div>
        </div>

        <!-- 列表行 -->
        <div
          v-for="exam in exams"
          :key="exam.id"
          class="exam-row"
          :class="{ 'exam-row-ended': normalizeExamStatus(exam.status) === 'ended' }"
          @click="handleExamClick(exam)"
        >
          <div class="exam-row-accent" :style="{ background: getStatusAccentColor(exam.status) }"></div>

          <!-- 考试信息 -->
          <div class="exam-row-main">
            <div class="exam-row-tags">
              <span class="exam-tag" :class="getStatusTagClass(exam.status)">
                {{ getDisplayStatusText(exam) }}
              </span>
              <span class="exam-tag exam-tag-kind">
                {{ getExamKindLabel(exam) }}
              </span>
            </div>
            <h3 class="exam-row-title">{{ exam.title }}</h3>
            <div class="exam-row-class">
              <svg class="icon-sm" :style="{ color: getStatusAccentColor(exam.status) }" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 4a2 2 0 012-2h6a2 2 0 012 2v14l-5-2.5L5 18V4z"></path>
              </svg>
              <span>{{ exam.training_name ? `所属班级: ${exam.training_name}` : exam.course_names?.length ? `关联课程: ${exam.course_names.join('、')}` : '' }}</span>
            </div>
            <!-- 移动端表格信息 -->
            <div class="exam-row-mobile-table">
              <div class="exam-row-mobile-cell">
                <span class="exam-row-mobile-label">时长</span>
                <span class="exam-row-mobile-value">{{ exam.duration || 0 }} 分钟</span>
              </div>
              <div class="exam-row-mobile-cell">
                <span class="exam-row-mobile-label">题量</span>
                <span class="exam-row-mobile-value">{{ exam.question_count || 0 }} 题</span>
              </div>
              <div class="exam-row-mobile-cell">
                <span class="exam-row-mobile-label">满分</span>
                <span class="exam-row-mobile-value">{{ exam.total_score || 0 }}</span>
              </div>
              <div class="exam-row-mobile-cell exam-row-mobile-cell-wide">
                <span class="exam-row-mobile-label">开考时间</span>
                <span class="exam-row-mobile-value">{{ exam.start_time ? formatDate(exam.start_time) : '--' }}</span>
              </div>
              <div class="exam-row-mobile-cell exam-row-mobile-cell-wide">
                <span class="exam-row-mobile-label">及格线</span>
                <span class="exam-row-mobile-value">{{ exam.passing_score || 0 }} 分</span>
              </div>
            </div>
          </div>

          <!-- PC端指标 -->
          <div class="exam-row-metrics">
            <div class="exam-metric">
              <span class="exam-metric-value">{{ exam.duration || 0 }}</span>
              <span class="exam-metric-label">分钟</span>
            </div>
            <div class="exam-metric">
              <span class="exam-metric-value">{{ exam.question_count || 0 }}</span>
              <span class="exam-metric-label">题</span>
            </div>
            <div class="exam-metric">
              <span class="exam-metric-value">{{ exam.total_score || 0 }}</span>
              <span class="exam-metric-label">分</span>
            </div>
          </div>

          <!-- 时间安排 -->
          <div class="exam-row-time">
            <div class="exam-row-time-block">
              <span class="exam-time-label">开考时间</span>
              <span class="exam-time-date">{{ exam.start_time ? formatDate(exam.start_time) : '--' }}</span>
            </div>
            <div class="exam-row-time-block">
              <span class="exam-time-label">及格线</span>
              <span class="exam-time-pass">{{ exam.passing_score || 0 }} 分</span>
            </div>
          </div>

          <!-- 操作 -->
          <div class="exam-row-action">
            <a-button
              v-if="!isStudentView"
              class="exam-action-btn"
              @click.stop="goToExamOverview(exam)"
            >
              {{ normalizeExamStatus(exam.status) === 'active' ? '监考' : normalizeExamStatus(exam.status) === 'ended' ? '成绩' : '查看' }}
            </a-button>
            <template v-else>
              <a-button
                v-if="shouldShowResult(exam)"
                type="primary"
                @click.stop="goToExamResult(exam)"
              >查看结果</a-button>
              <a-button
                v-else-if="exam.can_join"
                type="primary"
                @click.stop="goToExamOverview(exam)"
              >进入考试</a-button>
              <a-button
                v-else
                disabled
              >{{ getDisplayStatusText(exam) }}</a-button>
            </template>
          </div>
        </div>
      </div>

    <!-- ===== 选题弹窗 ===== -->
    <a-modal
      v-model:open="questionBankModalVisible"
      title="选题"
      width="900px"
      :footer="null"
      @cancel="questionBankModalVisible = false"
    >
      <div class="modal-section">
        <div class="modal-filter-row">
          <a-select v-model:value="questionFilters.folderId" placeholder="选择题库" allow-clear style="width: 200px" @change="loadQuestionsForPicker">
            <a-select-option v-for="f in questionFolders" :key="f.id" :value="f.id">{{ f.name }}</a-select-option>
          </a-select>
          <a-select v-model:value="questionFilters.type" placeholder="题型" allow-clear style="width: 140px" @change="loadQuestionsForPicker">
            <a-select-option value="single">单选题</a-select-option>
            <a-select-option value="multi">多选题</a-select-option>
            <a-select-option value="judge">判断题</a-select-option>
          </a-select>
          <a-input-search v-model:value="questionFilters.search" placeholder="搜索题目内容..." style="width: 240px" @search="loadQuestionsForPicker" />
        </div>
        <div class="modal-picker-layout">
          <div class="picker-left">
            <div v-if="questionLoading" class="text-center" style="padding: 40px">加载中...</div>
            <a-table
              v-else
              :dataSource="questionList"
              :columns="questionPickerColumns"
              :pagination="{ pageSize: 10 }"
              :scroll="{ y: 320 }"
              row-key="id"
              size="small"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'select'">
                  <a-checkbox :checked="isQuestionSelected(record.id)" @change="toggleQuestionSelect(record)" />
                </template>
                <template v-else-if="column.key === 'type'">
                  <a-tag :color="record.type === 'single' ? 'blue' : record.type === 'multi' ? 'purple' : 'orange'">
                    {{ record.type === 'single' ? '单选' : record.type === 'multi' ? '多选' : '判断' }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'content'">
                  <div class="table-q-content">{{ record.content }}</div>
                </template>
              </template>
            </a-table>
          </div>
          <div class="picker-right">
            <div class="picker-right-header">已选 <strong>{{ selectedQuestions.length }}</strong> 题</div>
            <div class="picker-right-list">
              <div v-for="q in selectedQuestions" :key="q.id" class="picker-right-item">
                <span class="picker-right-q-type">{{ q.type === 'single' ? '单' : q.type === 'multi' ? '多' : '判' }}</span>
                <span class="picker-right-q-text">{{ q.content?.slice(0, 20) }}...</span>
                <a-button type="text" size="small" danger @click="toggleQuestionSelect(q)">
                  <template #icon><CloseOutlined /></template>
                </a-button>
              </div>
              <div v-if="selectedQuestions.length === 0" class="text-center text-muted" style="padding: 20px; color: #94a3b8">未选择题目</div>
            </div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <a-button @click="questionBankModalVisible = false">取消</a-button>
        <a-button type="primary" :disabled="selectedQuestions.length === 0" @click="confirmQuestionSelection">
          确认选择 {{ selectedQuestions.length }} 题
        </a-button>
      </div>
    </a-modal>

    <!-- ===== 建卷弹窗 ===== -->
    <a-modal
      v-model:open="paperModalVisible"
      title="创建试卷"
      width="700px"
      :footer="null"
      @cancel="paperModalVisible = false"
    >
      <div class="modal-section">
        <div class="form-field">
          <label class="field-label required">试卷标题</label>
          <a-input v-model:value="paperForm.title" placeholder="请输入试卷标题" />
        </div>
        <div class="form-row">
          <div class="form-field">
            <label class="field-label">考试时长（分钟）</label>
            <a-input-number v-model:value="paperForm.duration" :min="10" :max="300" style="width: 100%" />
          </div>
          <div class="form-field">
            <label class="field-label">及格分数</label>
            <a-input-number v-model:value="paperForm.passingScore" :min="1" style="width: 100%" />
          </div>
        </div>
        <div class="form-field">
          <label class="field-label">试卷说明</label>
          <a-textarea v-model:value="paperForm.description" placeholder="选填" :rows="2" />
        </div>
        <div class="form-field">
          <label class="field-label">关联题目</label>
          <div class="selected-questions-summary">
            <span v-if="wizardSelectedQuestions.length > 0">已选 {{ wizardSelectedQuestions.length }} 题</span>
            <a-button type="link" size="small" @click="openQuestionBankModalForPaper">+ 继续选题</a-button>
            <a-button type="link" size="small" @click="wizardSelectedQuestions = []">清空</a-button>
          </div>
          <div v-if="wizardSelectedQuestions.length === 0" class="text-muted" style="color: #94a3b8; font-size: 13px">请先在「选题」中选择题目录入题目</div>
        </div>
      </div>
      <div class="modal-footer">
        <a-button @click="paperModalVisible = false">取消</a-button>
        <a-button type="primary" :loading="paperSubmitting" :disabled="!canSubmitPaper" @click="handleCreatePaper">
          创建并发布试卷
        </a-button>
      </div>
    </a-modal>

    <!-- ===== 建场次弹窗 ===== -->
    <a-modal
      v-model:open="examModalVisible"
      :title="activeTab === 'training' ? '创建培训班考试' : '创建独立考试'"
      width="700px"
      :footer="null"
      @cancel="examModalVisible = false"
    >
      <div class="modal-section">
        <div class="form-field">
          <label class="field-label required">场次名称</label>
          <a-input v-model:value="examForm.title" placeholder="请输入考试场次名称" />
        </div>
        <div class="form-field">
          <label class="field-label required">考试类型</label>
          <a-select v-model:value="examForm.purpose" style="width: 100%">
            <a-select-option v-for="item in examPurposeOptions" :key="item.value" :value="item.value">{{ item.label }}</a-select-option>
          </a-select>
        </div>
        <div class="form-field">
          <label class="field-label required">关联试卷</label>
          <a-select v-model:value="examForm.paperId" placeholder="请选择已发布试卷" show-search style="width: 100%">
            <a-select-option v-for="p in availablePapers" :key="p.id" :value="p.id">{{ p.title }}</a-select-option>
          </a-select>
        </div>
        <div class="form-field">
          <label class="field-label">考试时间</label>
          <a-range-picker v-model:value="examDateRange" show-time format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width: 100%" />
        </div>
        <div class="form-row">
          <div class="form-field">
            <label class="field-label">状态</label>
            <a-select v-model:value="examForm.status" style="width: 100%">
              <a-select-option value="upcoming">未开始</a-select-option>
              <a-select-option value="active">进行中</a-select-option>
              <a-select-option value="ended">已结束</a-select-option>
            </a-select>
          </div>
          <div class="form-field">
            <label class="field-label">最大次数</label>
            <a-input-number v-model:value="examForm.maxAttempts" :min="1" :max="10" style="width: 100%" />
          </div>
        </div>
        <div v-if="activeTab === 'training'" class="form-field">
          <label class="field-label required">所属培训班</label>
          <a-select
            v-model:value="selectedTrainingId"
            placeholder="请选择培训班"
            show-search
            option-filter-prop="label"
            style="width: 100%"
            :disabled="isRouteTrainingLocked"
            :options="availableTrainings.map((item) => ({ value: item.id, label: item.name }))"
          />
        </div>
        <div v-if="activeTab !== 'training'" class="form-field">
          <label class="field-label">关联课程</label>
          <a-select
            v-model:value="examForm.courseIds"
            mode="multiple"
            placeholder="可选，支持将考试与课程建立关联"
            style="width: 100%"
            allow-clear
          >
            <a-select-option v-for="c in availableCourses" :key="c.id" :value="c.id">{{ c.title || c.name }}</a-select-option>
          </a-select>
          <div class="paper-hint">
            <span class="hint-text">独立考试创建后，请到管理端导入 Excel 名单完成参试对象配置。</span>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <a-button @click="examModalVisible = false">取消</a-button>
        <a-button type="primary" :loading="examSubmitting" :disabled="!canSubmitExam" @click="handleCreateExam">
          创建考试
        </a-button>
      </div>
    </a-modal>

    <!-- ===== 创建考试向导 ===== -->
    <a-modal
      v-model:open="wizardModalVisible"
      :title="null"
      width="900px"
      :footer="null"
      centered
      class="wizard-modal"
      @cancel="wizardModalVisible = false"
    >
      <div class="wizard-header">
        <h2 class="wizard-title">创建考试</h2>
        <p class="wizard-subtitle">选择题目 → 创建试卷 → 创建考试场次</p>
      </div>
      <a-steps :current="wizardStep - 1" size="small" class="wizard-steps">
        <a-step title="选题" />
        <a-step title="创建试卷" />
        <a-step title="创建场次" />
      </a-steps>

      <!-- Step 1: 选题 -->
      <div v-show="wizardStep === 1" class="wizard-step-content">
        <!-- 模式切换 -->
        <div class="step1-mode-tabs">
          <a-radio-group v-model:value="wizardSelectMode" size="small">
            <a-radio-button value="manual">手动选题</a-radio-button>
            <a-radio-button value="ai">智能组卷</a-radio-button>
          </a-radio-group>
          <a-input v-model:value="paperForm.title" placeholder="请输入试卷标题" style="width: 240px; margin-left: 12px" />
        </div>

        <!-- 手动选题模式 -->
        <div v-if="wizardSelectMode === 'manual'" class="manual-select-section">
          <div class="modal-filter-row">
            <a-select v-model:value="questionFilters.folderId" placeholder="选择题库" allow-clear style="width: 200px" @change="loadQuestionsForPicker">
              <a-select-option v-for="f in questionFolders" :key="f.id" :value="f.id">{{ f.name }}</a-select-option>
            </a-select>
            <a-select v-model:value="questionFilters.type" placeholder="题型" allow-clear style="width: 140px" @change="loadQuestionsForPicker">
              <a-select-option value="single">单选题</a-select-option>
              <a-select-option value="multi">多选题</a-select-option>
              <a-select-option value="judge">判断题</a-select-option>
            </a-select>
            <a-input-search v-model:value="questionFilters.search" placeholder="搜索题目内容..." style="width: 240px" @search="loadQuestionsForPicker" />
          </div>
          <div class="modal-picker-layout">
            <div class="picker-left">
              <div v-if="questionLoading" class="text-center" style="padding: 40px">加载中...</div>
              <a-table
                v-else
                :dataSource="questionList"
                :columns="questionPickerColumns"
                :pagination="{ pageSize: 10 }"
                :scroll="{ y: 280 }"
                row-key="id"
                size="small"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'select'">
                    <a-checkbox :checked="isQuestionSelected(record.id)" @change="toggleQuestionSelect(record)" />
                  </template>
                  <template v-else-if="column.key === 'type'">
                    <a-tag :color="record.type === 'single' ? 'blue' : record.type === 'multi' ? 'purple' : 'orange'">
                      {{ record.type === 'single' ? '单选' : record.type === 'multi' ? '多选' : '判断' }}
                    </a-tag>
                  </template>
                  <template v-else-if="column.key === 'content'">
                    <div class="table-q-content">{{ record.content }}</div>
                  </template>
                </template>
              </a-table>
            </div>
            <div class="picker-right">
              <div class="picker-right-header">已选 <strong>{{ wizardSelectedQuestions.length }}</strong> 题</div>
              <div class="picker-right-list">
                <div v-for="q in wizardSelectedQuestions" :key="q.id" class="picker-right-item">
                  <span class="picker-right-q-type">{{ q.type === 'single' ? '单' : q.type === 'multi' ? '多' : '判' }}</span>
                  <span class="picker-right-q-text">{{ q.content?.slice(0, 18) }}...</span>
                  <a-button type="text" size="small" danger @click="toggleQuestionSelect(q)">
                    <template #icon><CloseOutlined /></template>
                  </a-button>
                </div>
                <div v-if="wizardSelectedQuestions.length === 0" class="text-center" style="padding: 20px; color: #94a3b8">请选择题目</div>
              </div>
            </div>
          </div>

          <!-- 手动模式：题型分值配置 -->
          <div class="type-config-section">
            <div class="type-config-header">题型分值设置</div>
            <a-table
              :dataSource="manualTypeScoreConfigs"
              :columns="manualScoreColumns"
              :pagination="false"
              size="small"
              row-key="type"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'type'">
                  <a-tag :color="record.type === 'single' ? 'blue' : record.type === 'multi' ? 'purple' : 'orange'">
                    {{ record.type === 'single' ? '单选题' : record.type === 'multi' ? '多选题' : '判断题' }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'score'">
                  <a-input-number v-model:value="record.score" :min="1" :max="10" size="small" style="width: 70px" />
                </template>
                <template v-else-if="column.key === 'count'">
                  <span>{{ getSelectedCountByType(record.type) }}</span>
                </template>
                <template v-else-if="column.key === 'subtotal'">
                  <span class="type-subtotal">{{ getSelectedCountByType(record.type) * record.score }} 分</span>
                </template>
              </template>
            </a-table>
          </div>

          <div class="ai-summary">
            <span>已选 <strong>{{ wizardSelectedQuestions.length }}</strong> 题</span>
            <span>总分 <strong>{{ manualTotalScore }}</strong> 分</span>
          </div>
        </div>

        <!-- 智能组卷模式 -->
        <div v-if="wizardSelectMode === 'ai'" class="ai-select-section">
          <div class="modal-filter-row">
            <a-select
              v-model:value="aiKnowledgePointIds"
              mode="multiple"
              placeholder="选择知识点范围"
              allow-clear
              style="width: 260px"
            >
              <a-select-option v-for="item in availableKnowledgePoints" :key="item.id" :value="item.id">
                {{ item.name }}
              </a-select-option>
            </a-select>
            <a-select v-model:value="assemblyMode" placeholder="出卷模式" style="width: 180px">
              <a-select-option value="balanced">均衡抽题</a-select-option>
              <a-select-option value="practice">练习导向</a-select-option>
              <a-select-option value="exam">考试导向</a-select-option>
            </a-select>
          </div>

          <div class="ai-input-grid">
            <div class="ai-requirements-card" style="margin-left: 20px;">
              <div class="type-config-header">智能组卷要求</div>
              <a-textarea
                v-model:value="aiRequirements"
                :rows="6"
                placeholder="请输入补充要求或提示词，例如：突出执法程序规范、增加案例分析场景、优先覆盖新修订制度等"
              />
              <div class="ai-requirements-hint">
                提示词会和知识点、题型配置一起用于筛题；上传的附件会先解析为文本，再自动并入 AI 组卷要求。
              </div>
            </div>

            <div class="ai-attachments-card">
              <div class="type-config-header">参考附件</div>
              <a-upload-dragger
                v-model:file-list="aiAttachmentList"
                :before-upload="handleAiAttachmentBeforeUpload"
                :multiple="true"
                :max-count="5"
                :accept="aiAttachmentAccept"
              >
                <p class="ant-upload-drag-icon">
                  <FileTextOutlined />
                </p>
                <p class="ant-upload-text">点击或拖拽上传参考材料</p>
              </a-upload-dragger>
            </div>
          </div>

          <div class="type-config-section">
            <div class="type-config-header">题型配置</div>
            <a-table
              :dataSource="aiTypeConfigs"
              :columns="typeConfigColumns"
              :pagination="false"
              size="small"
              row-key="type"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'type'">
                  <a-tag :color="record.type === 'single' ? 'blue' : record.type === 'multi' ? 'purple' : 'orange'">
                    {{ record.type === 'single' ? '单选题' : record.type === 'multi' ? '多选题' : '判断题' }}
                  </a-tag>
                </template>
                <template v-else-if="column.key === 'count'">
                  <a-input-number v-model:value="record.count" :min="0" :max="50" size="small" style="width: 70px" />
                </template>
                <template v-else-if="column.key === 'score'">
                  <a-input-number v-model:value="record.score" :min="1" :max="10" size="small" style="width: 70px" />
                </template>
                <template v-else-if="column.key === 'difficulty'">
                  <a-select v-model:value="record.difficulty" size="small" style="width: 80px">
                    <a-select-option :value="1">1级</a-select-option>
                    <a-select-option :value="2">2级</a-select-option>
                    <a-select-option :value="3">3级</a-select-option>
                  </a-select>
                </template>
              </template>
            </a-table>
          </div>

          <div class="ai-summary">
            <span>总题数：<strong>{{ aiTotalCount }}</strong> 题</span>
            <span>总分：<strong>{{ aiTotalScore }}</strong> 分</span>
            <span>附件：<strong>{{ aiAttachmentList.length }}</strong> 份</span>
          </div>

          <!-- AI 生成状态 -->
          <div v-if="aiGenerating" class="ai-generating">
            <a-spin size="small" />
            <span>{{ aiGenerationStatusText }}</span>
          </div>
        </div>

        <div class="modal-footer">
          <a-button @click="wizardModalVisible = false">取消</a-button>
          <a-button type="primary" :loading="aiGenerating" :disabled="!canProceedStep1" @click="handleProceedStep1">
            {{ wizardSelectMode === 'manual' ? '下一步：创建试卷' : 'AI 生成试卷' }}
          </a-button>
        </div>
      </div>

      <!-- Step 2: 创建试卷（手动）/ 确认预览（AI） -->
      <div v-show="wizardStep === 2" class="wizard-step-content">
        <!-- AI 模式：试卷草稿预览 -->
        <div v-if="wizardSelectMode === 'ai'">
          <div v-if="aiPaperDraft" class="paper-draft-preview">
            <div class="paper-draft-header">
              <h3 class="paper-draft-title">{{ aiPaperDraft.title }}</h3>
              <div class="paper-draft-meta">
                <a-tag v-if="aiPaperDraft.type === 'formal'" color="blue">正式考试</a-tag>
                <a-tag v-else color="green">测验</a-tag>
                <span>时长：{{ aiPaperDraft.duration || 60 }} 分钟</span>
                <span>总分：{{ aiPaperDraft.total_score || aiTotalScore }} 分</span>
                <span>及格分：{{ Math.round((aiPaperDraft.total_score || aiTotalScore) * 0.6) }} 分</span>
              </div>
            </div>
            <div class="paper-draft-questions">
              <div v-for="(q, idx) in (aiPaperDraft.questions || [])" :key="idx" class="paper-draft-q-item">
                <span class="paper-draft-q-num">{{ Number(idx) + 1 }}.</span>
                <a-tag :color="q.type === 'single' ? 'blue' : q.type === 'multi' ? 'purple' : 'orange'" size="small">
                  {{ q.type === 'single' ? '单选' : q.type === 'multi' ? '多选' : '判断' }}
                </a-tag>
                <span class="paper-draft-q-text">{{ q.content }}</span>
                <span class="paper-draft-q-score">{{ q.score || 0 }}分</span>
              </div>
              <div v-if="!aiPaperDraft.questions?.length" class="text-center text-muted" style="padding: 40px">
                暂无题目数据
              </div>
            </div>
          </div>
          <div v-else class="text-center text-muted" style="padding: 60px">
            暂无试卷预览数据，请返回重新生成
          </div>
          <div class="modal-footer">
            <a-button @click="wizardModalVisible = false">取消</a-button>
            <a-button @click="handleBackToStep1">返回修改</a-button>
            <a-button type="primary" :loading="paperSubmitting" :disabled="!aiPaperDraft" @click="handleConfirmAndPublish">
              确认并发布
            </a-button>
          </div>
        </div>

        <!-- 手动模式：创建试卷表单 -->
        <div v-if="wizardSelectMode === 'manual'" class="modal-section">
          <div class="form-field">
            <label class="field-label required">试卷标题</label>
            <a-input v-model:value="paperForm.title" placeholder="请输入试卷标题" />
          </div>
          <div class="form-row">
            <div class="form-field">
              <label class="field-label">考试时长（分钟）</label>
              <a-input-number v-model:value="paperForm.duration" :min="10" :max="300" style="width: 100%" />
            </div>
            <div class="form-field">
              <label class="field-label">及格分数</label>
              <a-input-number v-model:value="paperForm.passingScore" :min="1" :max="manualTotalScore || undefined" style="width: 100%" />
            </div>
          </div>
          <div class="form-field">
            <label class="field-label">试卷说明</label>
            <a-textarea v-model:value="paperForm.description" placeholder="选填" :rows="2" />
          </div>
          <div class="selected-questions-summary">
            已选 <strong>{{ wizardSelectedQuestions.length }}</strong> 题（单选 {{ getSelectedCountByType('single') }} 题，多选 {{ getSelectedCountByType('multi') }} 题，判断 {{ getSelectedCountByType('judge') }} 题），
            总分 <strong>{{ manualTotalScore }}</strong> 分，当前及格分 <strong>{{ paperForm.passingScore }}</strong> 分
            <a-button type="link" size="small" @click="wizardStep = 1">返回修改</a-button>
          </div>
          <div class="modal-footer">
            <a-button @click="wizardModalVisible = false">取消</a-button>
            <a-button @click="wizardStep = 1">上一步</a-button>
            <a-button type="primary" :loading="paperSubmitting" :disabled="!canSubmitPaper" @click="handleWizardCreatePaper">创建并发布试卷</a-button>
          </div>
        </div>
      </div>

      <!-- Step 3: 创建考试场次 -->
      <div v-show="wizardStep === 3" class="wizard-step-content">
        <div class="form-field">
          <label class="field-label required">考试名称</label>
          <a-input v-model:value="examForm.title" placeholder="请输入考试名称" />
        </div>
        <div class="form-field">
          <label class="field-label required">考试类型</label>
          <a-select v-model:value="examForm.purpose" style="width: 100%">
            <a-select-option v-for="item in examPurposeOptions" :key="item.value" :value="item.value">{{ item.label }}</a-select-option>
          </a-select>
        </div>
        <div class="form-field">
          <label class="field-label required">关联试卷</label>
          <a-select
            v-model:value="examForm.paperId"
            placeholder="请选择已发布试卷"
            show-search
            option-filter-prop="label"
            style="width: 100%"
            :options="availablePapers.map((item) => ({ value: item.id, label: item.title }))"
            @change="handleWizardPaperChange"
          />
          <div class="paper-hint">
            <span class="hint-text">默认带入刚创建并发布的试卷，也可切换为其他已发布试卷</span>
          </div>
        </div>
        <div class="paper-preview-card">
          <template v-if="currentWizardPaperSummary">
            <div class="paper-preview-head">
              <div>
                <div class="paper-preview-title">{{ currentWizardPaperSummary.title }}</div>
                <div class="paper-preview-meta">
                  <span>{{ currentWizardPaperSummary.status === 'published' ? '已发布试卷' : '试卷' }}</span>
                  <span>{{ currentWizardPaperSummary.question_count || 0 }} 题</span>
                  <span>总分 {{ currentWizardPaperSummary.total_score || 0 }} 分</span>
                </div>
              </div>
              <div class="paper-preview-stats">
                <span>时长 {{ currentWizardPaperSummary.duration || 60 }} 分钟</span>
                <span>及格 {{ currentWizardPaperSummary.passing_score || 0 }} 分</span>
              </div>
            </div>
          </template>
          <span v-else class="paper-preview-empty">请选择已发布试卷后继续配置考试。</span>
        </div>
        <div class="form-row">
          <div class="form-field">
            <label class="field-label">展示类型</label>
            <a-select v-model:value="examForm.type" style="width: 100%">
              <a-select-option value="formal">正式考试</a-select-option>
              <a-select-option value="quiz">测验</a-select-option>
            </a-select>
          </div>
          <div class="form-field">
            <label class="field-label">状态</label>
            <a-select v-model:value="examForm.status" style="width: 100%">
              <a-select-option value="upcoming">未开始</a-select-option>
              <a-select-option value="active">进行中</a-select-option>
              <a-select-option value="ended">已结束</a-select-option>
            </a-select>
          </div>
        </div>
        <div v-if="activeTab === 'training'" class="form-field">
          <label class="field-label required">所属培训班</label>
          <a-select
            v-model:value="selectedTrainingId"
            placeholder="请选择培训班"
            show-search
            option-filter-prop="label"
            style="width: 100%"
            :disabled="isRouteTrainingLocked"
            :options="availableTrainings.map((item) => ({ value: item.id, label: item.name }))"
          />
        </div>
        <div class="form-field">
          <label class="field-label">关联课程</label>
          <a-select
            v-model:value="examForm.courseIds"
            mode="multiple"
            placeholder="请选择关联课程（可选）"
            style="width: 100%"
            allow-clear
          >
            <a-select-option v-for="c in availableCourses" :key="c.id" :value="c.id">{{ c.title || c.name }}</a-select-option>
          </a-select>
          <div v-if="activeTab !== 'training'" class="paper-hint">
            <span class="hint-text">独立考试创建后，请到管理端导入 Excel 名单完成参试对象配置。</span>
          </div>
        </div>
        <div class="form-field">
          <label class="field-label">考试时间</label>
          <a-range-picker v-model:value="examDateRange" show-time format="YYYY-MM-DD HH:mm" value-format="YYYY-MM-DD HH:mm" style="width: 100%" />
        </div>
        <div class="form-row">
          <div class="form-field">
            <label class="field-label">考试时长（分钟）</label>
            <a-input-number v-model:value="examForm.duration" :min="10" :max="300" style="width: 100%" />
          </div>
          <div class="form-field">
            <label class="field-label">及格分数</label>
            <a-input-number v-model:value="examForm.passingScore" :min="1" style="width: 100%" />
          </div>
        </div>
        <div class="form-field">
          <label class="field-label">最大次数</label>
          <a-input-number v-model:value="examForm.maxAttempts" :min="1" :max="10" style="width: 100%" />
        </div>
        <div class="form-field">
          <label class="field-label">考试说明</label>
          <a-textarea v-model:value="examForm.description" placeholder="选填" :rows="2" />
        </div>
        <div class="selected-questions-summary">
          <template v-if="currentWizardPaperSummary">
            试卷预览：{{ currentWizardPaperSummary.question_count || 0 }} 题，总分 {{ currentWizardPaperSummary.total_score || 0 }} 分，当前及格分 {{ examForm.passingScore }} 分
          </template>
          <template v-else>
            请选择已发布试卷后继续完成考试配置
          </template>
        </div>
        <div class="modal-footer">
          <a-button @click="wizardModalVisible = false">取消</a-button>
          <a-button @click="wizardStep = 2">上一步</a-button>
          <a-button type="primary" :loading="examSubmitting" :disabled="!canSubmitWizardExam" @click="handleWizardCreateExam">
            创建考试
          </a-button>
        </div>
      </div>
    </a-modal>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  BookOutlined,
  CalendarOutlined,
  FileTextOutlined,
  SafetyCertificateOutlined,
  SafetyOutlined,
  CloseOutlined,
} from '@ant-design/icons-vue'
import dayjs from 'dayjs'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Upload } from 'ant-design-vue'
import type { UploadFile } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import type {
  ExamPaperResponse,
  ExamResponse,
  KnowledgePointResponse,
  QuestionResponse,
  TrainingListResponse,
} from '@/api/generated/model'
import {
  getExamPapersApiV1ExamsPapersGet,
  createExamPaperApiV1ExamsPapersPost,
  publishExamPaperApiV1ExamsPapersPaperIdPublishPost,
} from '@/api/generated/exam-management/exam-management'
import { createUnifiedExam, getUnifiedExams } from '@/api/exam'
import {
  getQuestionsApiV1QuestionsGet,
  getQuestionFoldersApiV1QuestionsFoldersGet,
} from '@/api/generated/question-management/question-management'
import {
  getCoursesApiV1CoursesGet,
} from '@/api/generated/course-management/course-management'
import {
  getTrainingsApiV1TrainingsGet,
} from '@/api/generated/training-management/training-management'
import {
  getKnowledgePointsApiV1KnowledgePointsGet,
} from '@/api/generated/knowledge-point-management/knowledge-point-management'
import {
  createPaperAssemblyTaskApiV1AiPaperAssemblyTasksPost,
  getPaperAssemblyTaskDetailApiV1AiPaperAssemblyTasksTaskIdGet,
  confirmPaperAssemblyTaskApiV1AiPaperAssemblyTasksTaskIdConfirmPost,
  parseDocumentFileApiV1AiFilesParsePost,
} from '@/api/generated/ai-tasks/ai-tasks'
import type { AIPaperAssemblyTaskDetailResponse } from '@/api/generated/model'
import {
  getExamStatusClass,
  getExamStatusText,
  normalizeExamStatus,
  resolveExamKind,
} from './examDisplay'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const loading = ref(false)
const activeTab = ref<'all' | 'standalone' | 'training'>('all')
const exams = ref<ExamResponse[]>([])
const isStudentView = computed(() => authStore.isStudent)
const avatarText = computed(() => {
  const name = authStore.currentUser?.nickname || authStore.currentUser?.name || authStore.currentUser?.username || ''
  return name.charAt(0).toUpperCase()
})
const searchPlaceholder = computed(() => (
  activeTab.value === 'training' ? '搜索考试名称或班级名称...' : '搜索考试名称、考试类型或说明...'
))

const filters = reactive({
  search: '',
  status: 'all',
  sort: 'latest',
})

const statusTabs = [
  { key: 'all', label: '全部' },
  { key: 'active', label: '进行中' },
  { key: 'upcoming', label: '即将开始' },
  { key: 'ended', label: '已结束' },
]

const examPurposeOptions = [
  { value: 'admission', label: '准入制考试' },
  { value: 'completion', label: '结课考试' },
  { value: 'quiz', label: '随堂测验' },
  { value: 'makeup', label: '补考' },
  { value: 'special', label: '专项考试' },
  { value: 'other', label: '其他考试' },
]

const ongoingCount = computed(() => exams.value.filter((e) => normalizeExamStatus(e.status) === 'active').length)
const upcomingCount = computed(() => exams.value.filter((e) => normalizeExamStatus(e.status) === 'upcoming').length)

// ===== 选题状态 =====
const questionBankModalVisible = ref(false)
const questionList = ref<QuestionResponse[]>([])
const questionFolders = ref<any[]>([])
const selectedQuestions = ref<QuestionResponse[]>([])
const wizardSelectedQuestions = ref<QuestionResponse[]>([])
const questionFilters = reactive({ search: '', type: '', folderId: null })
const questionLoading = ref(false)

const questionPickerColumns = [
  { title: '', key: 'select', width: 50 },
  { title: '题型', key: 'type', width: 80 },
  { title: '题目内容', key: 'content' },
]

const typeConfigColumns = [
  { title: '题型', key: 'type', width: 100 },
  { title: '数量', key: 'count', width: 100 },
  { title: '分/题', key: 'score', width: 100 },
  { title: '目标难度', key: 'difficulty', width: 120 },
]

const manualScoreColumns = [
  { title: '题型', key: 'type', width: 120 },
  { title: '已选', key: 'count', width: 80 },
  { title: '分/题', key: 'score', width: 100 },
  { title: '小计', key: 'subtotal', width: 100 },
]

const manualTypeScoreConfigs = reactive([
  { type: 'single', score: 2 },
  { type: 'multi', score: 3 },
  { type: 'judge', score: 1 },
])

function getSelectedCountByType(type: string) {
  return wizardSelectedQuestions.value.filter((q) => q.type === type).length
}

const manualTotalScore = computed(() => {
  return wizardSelectedQuestions.value.reduce((sum, q) => {
    const config = manualTypeScoreConfigs.find((c) => c.type === q.type)
    return sum + (config?.score || 0)
  }, 0)
})

// ===== 建卷状态 =====
const paperModalVisible = ref(false)
const paperForm = reactive({ title: '', duration: 60, passingScore: 60, description: '' })
const paperSubmitting = ref(false)

// ===== 建场次状态 =====
const examModalVisible = ref(false)
const examForm = reactive({
  paperId: undefined as number | undefined,
  status: 'upcoming',
  purpose: 'special',
  courseIds: [] as number[],
  maxAttempts: 1,
  title: '',
  type: 'formal',
  duration: 60,
  passingScore: 60,
  description: '',
})
const examDateRange = ref<[string, string] | null>(null)
const availablePapers = ref<ExamPaperResponse[]>([])
const availableCourses = ref<any[]>([])
const availableTrainings = ref<TrainingListResponse[]>([])
const availableKnowledgePoints = ref<KnowledgePointResponse[]>([])
const selectedTrainingId = ref<number | undefined>(undefined)
const examSubmitting = ref(false)

// ===== 向导状态 =====
const wizardModalVisible = ref(false)
const wizardStep = ref(1)
const wizardPaperId = ref<number | null>(null)
const wizardSelectMode = ref<'manual' | 'ai'>('manual')
const aiKnowledgePointIds = ref<number[]>([])

function parsePositiveInt(raw: unknown) {
  const value = Number(Array.isArray(raw) ? raw[0] : raw)
  return Number.isInteger(value) && value > 0 ? value : undefined
}

const routeTrainingId = computed(() => parsePositiveInt(route.query.trainingId))
const isRouteTrainingLocked = computed(() => !!routeTrainingId.value)
const effectiveTrainingId = computed(() => routeTrainingId.value ?? selectedTrainingId.value)

const canProceedStep1 = computed(() => {
  if (wizardSelectMode.value === 'manual') {
    return wizardSelectedQuestions.value.length > 0
  }
  return aiTotalCount.value > 0
})

// ===== AI 智能组卷状态 =====
const aiTaskId = ref<number | null>(null)
const aiTaskStatus = ref<string>('pending')
const aiPaperDraft = ref<any>(null)
const assemblyMode = ref('balanced')
const aiGenerating = ref(false)
const aiAttachmentParsing = ref(false)
const aiPollTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const aiRequirements = ref('')
const aiAttachmentList = ref<UploadFile[]>([])

const aiAttachmentAccept = '.pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.md,.ppt,.pptx'
const supportedAiAttachmentExtensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt', 'md', 'ppt', 'pptx']

const aiTypeConfigs = reactive([
  { type: 'single', count: 5, difficulty: 3, score: 2 },
  { type: 'multi', count: 3, difficulty: 3, score: 3 },
  { type: 'judge', count: 2, difficulty: 2, score: 1 },
])

const aiTotalCount = computed(() => aiTypeConfigs.reduce((sum, c) => sum + c.count, 0))
const aiTotalScore = computed(() => aiTypeConfigs.reduce((sum, c) => sum + c.count * c.score, 0))
const aiGenerationStatusText = computed(() => (
  aiAttachmentParsing.value ? '正在解析附件内容，请稍候...' : 'AI 正在生成试卷，请稍候...'
))

const canSubmitPaper = computed(() => paperForm.title.trim() && wizardSelectedQuestions.value.length > 0)
const canSubmitExam = computed(() => {
  if (!examForm.title.trim() || !examForm.paperId) return false
  if (activeTab.value === 'training' && !effectiveTrainingId.value) return false
  return true
})
const currentWizardPaperId = computed(() => examForm.paperId ?? wizardPaperId.value ?? undefined)
const currentWizardPaperSummary = computed(() => getSelectedPaperSummary(currentWizardPaperId.value))
const canSubmitWizardExam = computed(() => {
  if (!examForm.title.trim() || !currentWizardPaperId.value) return false
  if (activeTab.value === 'training' && !effectiveTrainingId.value) return false
  return true
})

function getFileExtension(fileName: string) {
  return fileName.includes('.') ? fileName.split('.').pop()?.toLowerCase() || '' : ''
}

function handleAiAttachmentBeforeUpload(file: File) {
  const extension = getFileExtension(file.name)
  if (!supportedAiAttachmentExtensions.includes(extension)) {
    message.warning('仅支持上传 PDF、DOC、DOCX、XLS、XLSX、CSV、TXT、MD、PPT、PPTX 文件')
    return Upload.LIST_IGNORE
  }
  return false
}

function extractParsedDocumentText(payload: unknown): string {
  if (typeof payload === 'string') return payload.trim()
  if (!payload || typeof payload !== 'object') return ''

  const record = payload as Record<string, unknown>
  const preferredKeys = ['text', 'content', 'markdown', 'parsed_text', 'result']
  for (const key of preferredKeys) {
    const candidate = record[key]
    if (typeof candidate === 'string' && candidate.trim()) {
      return candidate.trim()
    }
  }

  const textParts = Object.values(record).filter((item): item is string => typeof item === 'string' && item.trim().length > 0)
  return textParts.join('\n').trim()
}

async function buildAiRequirementsPayload() {
  const sections: string[] = []
  const trimmedRequirements = aiRequirements.value.trim()
  if (trimmedRequirements) {
    sections.push(`补充要求：\n${trimmedRequirements}`)
  }

  const uploadFiles = aiAttachmentList.value
    .map((item) => item.originFileObj)
    .filter((item): item is NonNullable<UploadFile['originFileObj']> => !!item)

  if (uploadFiles.length === 0) {
    return sections.join('\n\n')
  }

  aiAttachmentParsing.value = true
  try {
    const parsedSections: string[] = []
    for (const file of uploadFiles) {
      const res = await parseDocumentFileApiV1AiFilesParsePost({ file })
      const parsedText = extractParsedDocumentText((res as any)?.data ?? res)
      if (!parsedText) {
        throw new Error(`${file.name} 解析结果为空`)
      }
      parsedSections.push(`附件《${file.name}》：\n${parsedText}`)
    }
    if (parsedSections.length > 0) {
      sections.push(parsedSections.join('\n\n'))
    }
    return sections.join('\n\n')
  } finally {
    aiAttachmentParsing.value = false
  }
}

onMounted(() => {
  if (routeTrainingId.value) {
    activeTab.value = 'training'
  }
  void fetchExams()
})

async function fetchExams() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: 1, size: 50, search: filters.search || undefined }
    if (activeTab.value === 'standalone' || activeTab.value === 'training') {
      params.scene = activeTab.value
    }
    const response = await getUnifiedExams(params)

    let items: any[] = response?.items || []

    if (filters.status !== 'all') {
      items = items.filter((item) => normalizeExamStatus(item.status) === filters.status)
    }

    if (filters.sort === 'upcoming') {
      items = items.filter((item) => normalizeExamStatus(item.status) === 'upcoming')
    } else if (filters.sort === 'active') {
      items = items.filter((item) => normalizeExamStatus(item.status) === 'active')
    }

    const statusRank = { active: 0, upcoming: 1, ended: 2, unknown: 3 } as const
    exams.value = [...items].sort((left, right) => {
      const leftStatus = normalizeExamStatus(left.status)
      const rightStatus = normalizeExamStatus(right.status)
      const statusDiff = statusRank[leftStatus] - statusRank[rightStatus]
      if (statusDiff !== 0) return statusDiff
      // 同状态内按时间排序
      const leftTime = left.start_time ? dayjs(left.start_time).valueOf() : 0
      const rightTime = right.start_time ? dayjs(right.start_time).valueOf() : 0
      return rightTime - leftTime
    })
  } catch (error) {
    message.error(error instanceof Error ? error.message : '考试列表加载失败')
  } finally {
    loading.value = false
  }
}

function selectStatus(status: string) {
  filters.status = status
  void fetchExams()
}

function switchTab(tab: 'all' | 'standalone' | 'training') {
  activeTab.value = tab
  void fetchExams()
}

function handleExamClick(exam: ExamResponse) {
  if (!isStudentView.value) {
    void goToExamOverview(exam)
  } else if (exam.can_join) {
    void goToExamOverview(exam)
  } else if (shouldShowResult(exam)) {
    void goToExamResult(exam)
  }
}

function getStatusClass(status?: string | null) {
  return getExamStatusClass(status)
}

function getStatusText(exam: ExamResponse) {
  return getExamStatusText(exam)
}

function getDisplayStatusText(exam: ExamResponse) {
  if (isStudentView.value) return getStatusText(exam)
  const normalizedStatus = normalizeExamStatus(exam.status)
  if (normalizedStatus === 'active') return '进行中'
  if (normalizedStatus === 'upcoming') return '即将开始'
  if (normalizedStatus === 'ended') return '已结束'
  return '状态未知'
}

function getExamKindLabel(exam: ExamResponse) {
  return resolveExamKind(exam.kind, 'training') === 'training' ? '培训班考试' : '独立考试'
}

// 获取状态指示条颜色
function getStatusAccentColor(status?: string | null) {
  const normalizedStatus = normalizeExamStatus(status)
  if (normalizedStatus === 'active') return '#059669' // 绿色 - 进行中
  if (normalizedStatus === 'upcoming') return '#1A56DB' // 蓝色 - 即将开始
  return '#94A3B8' // 灰色 - 已结束
}

// 获取状态标签样式类
function getStatusTagClass(status?: string | null) {
  const normalizedStatus = normalizeExamStatus(status)
  if (normalizedStatus === 'active') return 'exam-tag-active'
  if (normalizedStatus === 'upcoming') return 'exam-tag-upcoming'
  return 'exam-tag-ended'
}

function formatDate(date?: string | null) {
  if (!date) return ''
  return dayjs(date).format('MM/DD HH:mm')
}

function shouldShowResult(exam: ExamResponse) {
  // 只有确实存在考试记录（attempt_count > 0）时才显示结果按钮
  return Number(exam.attempt_count || 0) > 0
}

function goToExamOverview(exam: ExamResponse) {
  const kind = resolveExamKind(exam.kind, 'training')
  // 教官直接跳转成绩表格页面
  if (!authStore.isStudent) {
    return router.push({
      path: `/exam/result/${exam.id}`,
      query: { kind },
    })
  }
  return router.push({
    path: `/exam/overview/${exam.id}`,
    query: { kind },
  })
}

function goToExamResult(exam: ExamResponse) {
  return router.push({
    path: `/exam/result/${exam.id}`,
    query: { kind: resolveExamKind(exam.kind, 'training') },
  })
}

const coverGradients = [
  'linear-gradient(135deg, #edf1fb 0%, #e4eaf5 100%)',
  'linear-gradient(135deg, #edf3ee 0%, #e1eae3 100%)',
  'linear-gradient(135deg, #f6eee7 0%, #eee2d7 100%)',
  'linear-gradient(135deg, #edf4f3 0%, #e2ece9 100%)',
]

const statusAccents: Record<string, string> = {
  active: '#34C759',
  upcoming: '#4B6EF5',
  ended: '#8E8E93',
}

function getExamAccent(status?: string) {
  return statusAccents[normalizeExamStatus(status)] || '#4B6EF5'
}

function getExamCoverBackground(exam: ExamResponse, index: number) {
  const normalizedStatus = normalizeExamStatus(exam.status)
  if (normalizedStatus === 'active') {
    return 'linear-gradient(135deg, #edf7ed 0%, #e3f0e6 100%)'
  }
  if (normalizedStatus === 'upcoming') {
    return 'linear-gradient(135deg, #edf1fb 0%, #e4eaf5 100%)'
  }
  if (normalizedStatus === 'ended') {
    return 'linear-gradient(135deg, #f5f5f7 0%, #ececed 100%)'
  }
  return coverGradients[index % coverGradients.length]
}

// ===== 选题相关 =====
async function loadQuestionsForPicker() {
  questionLoading.value = true
  try {
    const params: any = {}
    if (questionFilters.folderId) params.folder_id = questionFilters.folderId
    if (questionFilters.type) params.type = questionFilters.type
    if (questionFilters.search) params.search = questionFilters.search
    const res = await getQuestionsApiV1QuestionsGet(params)
    questionList.value = (res as any)?.items || res?.items || []
  } catch {
    questionList.value = []
  } finally {
    questionLoading.value = false
  }
}

async function loadQuestionFolders() {
  try {
    const res = await getQuestionFoldersApiV1QuestionsFoldersGet()
    questionFolders.value = (res as any)?.data || res || []
  } catch {
    questionFolders.value = []
  }
}

function toggleQuestionSelect(q: QuestionResponse) {
  const idx = wizardSelectedQuestions.value.findIndex((item) => item.id === q.id)
  if (idx >= 0) {
    wizardSelectedQuestions.value.splice(idx, 1)
  } else {
    wizardSelectedQuestions.value.push(q)
  }
}

function isQuestionSelected(id: number) {
  return wizardSelectedQuestions.value.some((q) => q.id === id)
}

function confirmQuestionSelection() {
  selectedQuestions.value = [...wizardSelectedQuestions.value]
  questionBankModalVisible.value = false
}

function openQuestionBankModal() {
  wizardSelectedQuestions.value = [...selectedQuestions.value]
  questionBankModalVisible.value = true
  loadQuestionFolders()
  loadQuestionsForPicker()
}

function openQuestionBankModalForPaper() {
  paperModalVisible.value = false
  wizardModalVisible.value = true
  if (wizardStep.value < 1) wizardStep.value = 1
  loadQuestionFolders()
  loadQuestionsForPicker()
}

// ===== 建卷相关 =====
async function loadAvailablePapers() {
  try {
    const res = await getExamPapersApiV1ExamsPapersGet({ page: 1, size: 100, status: 'published' })
    availablePapers.value = (res as any)?.items || res?.items || []
  } catch {
    availablePapers.value = []
  }
}

async function loadCourses() {
  try {
    const res = await getCoursesApiV1CoursesGet({ size: 100 })
    availableCourses.value = (res as any)?.items || res?.items || []
  } catch {
    availableCourses.value = []
  }
}

async function loadTrainings() {
  try {
    const res = await getTrainingsApiV1TrainingsGet({ page: 1, size: 100 })
    availableTrainings.value = (res as any)?.items || res?.items || []
  } catch {
    availableTrainings.value = []
  }
}

async function loadKnowledgePoints() {
  try {
    const res = await getKnowledgePointsApiV1KnowledgePointsGet({ page: 1, size: 200 })
    availableKnowledgePoints.value = (res as any)?.items || res?.items || []
  } catch {
    availableKnowledgePoints.value = []
  }
}

function syncTrainingContext() {
  if (routeTrainingId.value) {
    selectedTrainingId.value = routeTrainingId.value
  }
}

function getSelectedPaperSummary(paperId?: number) {
  if (!paperId) return null
  return availablePapers.value.find((item) => item.id === paperId) || null
}

function resolveValidPassingScore(totalScore: number, configuredPassingScore?: number) {
  const configured = Number(configuredPassingScore || 0)
  if (Number.isFinite(configured) && configured > 0 && (totalScore <= 0 || configured <= totalScore)) {
    return configured
  }
  if (totalScore > 0) {
    return Math.max(1, Math.ceil(totalScore * 0.6))
  }
  return 60
}

function resolveRecommendedPassingScore(totalScore: number) {
  if (totalScore > 0) {
    return Math.max(1, Math.ceil(totalScore * 0.6))
  }
  return 60
}

function applyExamDefaultsFromPaper(paperId?: number, shouldResetPassingScore = false) {
  const paper = getSelectedPaperSummary(paperId)
  if (!paper) return

  const totalScore = Number(paper.total_score || 0)
  const nextDuration = Math.min(300, Math.max(10, Math.floor(Number(paper.duration) || 60)))
  const nextPassingScore = resolveValidPassingScore(totalScore, paper.passing_score)

  if (paper.type) {
    examForm.type = paper.type
  }
  examForm.duration = nextDuration

  if (
    shouldResetPassingScore
    || Number(examForm.passingScore) < 1
    || (totalScore > 0 && Number(examForm.passingScore) > totalScore)
  ) {
    examForm.passingScore = nextPassingScore
  }
}

function bindWizardPaper(paperId: number, paper?: Partial<ExamPaperResponse> | null) {
  if (paper?.id) {
    const index = availablePapers.value.findIndex((item) => item.id === paper.id)
    if (index >= 0) {
      availablePapers.value.splice(index, 1, {
        ...availablePapers.value[index],
        ...paper,
      } as ExamPaperResponse)
    } else {
      availablePapers.value = [paper as ExamPaperResponse, ...availablePapers.value]
    }
  }

  wizardPaperId.value = paperId
  examForm.paperId = paperId
  applyExamDefaultsFromPaper(paperId, true)
}

function handleWizardPaperChange(paperId?: number) {
  if (!paperId) return
  applyExamDefaultsFromPaper(paperId, true)
}

function validateExamForm(paperId: number) {
  if (!examForm.title.trim()) {
    message.warning('请输入考试名称')
    return false
  }
  if (activeTab.value === 'training' && !effectiveTrainingId.value) {
    message.warning('请选择所属培训班')
    return false
  }
  if (Number(examForm.duration) < 10) {
    message.warning('考试时长不能少于10分钟')
    return false
  }
  if (Number(examForm.passingScore) < 1) {
    message.warning('及格分不能小于1分')
    return false
  }
  const paper = getSelectedPaperSummary(paperId)
  const totalScore = Number(paper?.total_score ?? 0)
  if (totalScore > 0 && Number(examForm.passingScore) > totalScore) {
    message.warning('及格分不能超过试卷总分')
    return false
  }
  return true
}

function buildExamPayload(paperId: number) {
  const isTrainingExam = activeTab.value === 'training'
  const payload: any = {
    title: examForm.title.trim(),
    paper_id: paperId,
    scene: isTrainingExam ? 'training' : 'standalone',
    participant_mode: isTrainingExam ? 'training_enrollment' : 'excel_import',
    purpose: examForm.purpose,
    status: examForm.status,
    type: examForm.type,
    max_attempts: examForm.maxAttempts,
    start_time: examDateRange.value?.[0] || null,
    end_time: examDateRange.value?.[1] || null,
    duration: examForm.duration,
    passing_score: examForm.passingScore,
    description: examForm.description || undefined,
    course_ids: examForm.courseIds.length > 0 ? examForm.courseIds : undefined,
  }
  if (isTrainingExam) {
    payload.training_id = effectiveTrainingId.value
  }
  return payload
}

function openPaperModal() {
  wizardSelectedQuestions.value = []
  paperForm.title = ''
  paperForm.duration = 60
  paperForm.passingScore = 60
  paperForm.description = ''
  paperModalVisible.value = true
}

async function handleCreatePaper() {
  if (!paperForm.title.trim()) { message.warning('请输入试卷标题'); return }
  if (wizardSelectedQuestions.value.length === 0) { message.warning('请先选择题目'); return }
  paperSubmitting.value = true
  try {
    const res = await createExamPaperApiV1ExamsPapersPost({
      title: paperForm.title,
      duration: paperForm.duration,
      passing_score: paperForm.passingScore,
      description: paperForm.description || undefined,
      question_ids: wizardSelectedQuestions.value.map((q) => q.id),
    } as any)
    const paperId = (res as any)?.data?.id || (res as any)?.id
    if (paperId) {
      await publishExamPaperApiV1ExamsPapersPaperIdPublishPost(paperId)
    }
    message.success('试卷创建并发布成功')
    paperModalVisible.value = false
    await void fetchExams()
  } catch (e: any) {
    message.error(e?.message || '创建试卷失败')
  } finally {
    paperSubmitting.value = false
  }
}

// ===== 建场次相关 =====
function openExamModal() {
  syncTrainingContext()
  examForm.title = ''
  examForm.paperId = undefined
  examForm.status = 'upcoming'
  examForm.purpose = activeTab.value === 'training' ? 'completion' : 'special'
  examForm.courseIds = []
  examForm.maxAttempts = 1
  examForm.type = 'formal'
  examForm.duration = 60
  examForm.passingScore = 60
  examForm.description = ''
  examDateRange.value = null
  examSubmitting.value = false
  loadAvailablePapers()
  loadCourses()
  if (activeTab.value === 'training') {
    loadTrainings()
  }
  examModalVisible.value = true
}

async function handleCreateExam() {
  if (!examForm.paperId) { message.warning('请选择试卷'); return }
  if (!validateExamForm(examForm.paperId)) return
  examSubmitting.value = true
  try {
    const payload = buildExamPayload(examForm.paperId)
    await createUnifiedExam(payload as any)
    message.success('考试创建成功')
    examModalVisible.value = false
    await void fetchExams()
  } catch (e: any) {
    message.error(e?.message || '创建考试失败')
  } finally {
    examSubmitting.value = false
  }
}

// ===== 向导相关 =====
function openWizardModal() {
  syncTrainingContext()
  wizardStep.value = 1
  wizardSelectMode.value = 'manual'
  paperForm.title = ''
  paperForm.duration = 60
  paperForm.passingScore = 60
  paperForm.description = ''
  examForm.title = ''
  examForm.paperId = undefined
  examForm.status = 'upcoming'
  examForm.purpose = activeTab.value === 'training' ? 'completion' : 'special'
  examForm.courseIds = []
  examForm.maxAttempts = 1
  examForm.type = 'formal'
  examForm.duration = 60
  examForm.passingScore = 60
  examForm.description = ''
  examDateRange.value = null
  wizardPaperId.value = null
  wizardSelectedQuestions.value = []
  assemblyMode.value = 'balanced'
  aiKnowledgePointIds.value = []
  aiTaskId.value = null
  aiTaskStatus.value = 'pending'
  aiPaperDraft.value = null
  aiRequirements.value = ''
  aiAttachmentList.value = []
  aiGenerating.value = false
  aiAttachmentParsing.value = false
  if (aiPollTimer.value) clearTimeout(aiPollTimer.value)
  loadQuestionFolders()
  loadAvailablePapers()
  loadCourses()
  loadKnowledgePoints()
  if (activeTab.value === 'training') {
    loadTrainings()
  }
  wizardModalVisible.value = true
}

async function handleProceedStep1() {
  if (!paperForm.title.trim()) { message.warning('请输入试卷标题'); return }
  if (wizardSelectMode.value === 'manual') {
    // 手动选题模式 → 跳到 Step 2 创建试卷
    wizardStep.value = 2
  } else {
    // 智能组卷模式 → AI 生成
    await handleAiGeneratePaper()
  }
}

async function handleWizardCreatePaper() {
  if (!paperForm.title.trim()) { message.warning('请输入试卷标题'); return }
  if (wizardSelectedQuestions.value.length === 0) { message.warning('请先选择题目'); return }
  paperSubmitting.value = true
  try {
    // 计算总分：按各题型分值 × 已选数量
    const totalScore = manualTotalScore.value
    const finalPassingScore = paperForm.passingScore && paperForm.passingScore <= totalScore
      ? paperForm.passingScore
      : resolveValidPassingScore(totalScore)

    const res = await createExamPaperApiV1ExamsPapersPost({
      title: paperForm.title,
      duration: paperForm.duration,
      passing_score: finalPassingScore,
      description: paperForm.description || undefined,
      question_ids: wizardSelectedQuestions.value.map((q) => q.id),
    } as any)
    const paperId = (res as any)?.data?.id || (res as any)?.id
    if (paperId) {
      const publishedPaper = await publishExamPaperApiV1ExamsPapersPaperIdPublishPost(paperId)
      await loadAvailablePapers()
      bindWizardPaper(paperId, ((publishedPaper as any)?.data || publishedPaper || (res as any)?.data || res) as Partial<ExamPaperResponse>)
      examForm.passingScore = finalPassingScore
    }
    wizardStep.value = 3
  } catch (e: any) {
    message.error(e?.message || '创建试卷失败')
  } finally {
    paperSubmitting.value = false
  }
}

async function handleAiGeneratePaper() {
  if (aiTotalCount.value === 0) { message.warning('请设置题型数量'); return }
  if (aiPollTimer.value) clearTimeout(aiPollTimer.value)
  aiGenerating.value = true
  aiAttachmentParsing.value = false
  aiPaperDraft.value = null
  aiTaskId.value = null
  try {
    const taskName = `组卷任务-${Date.now()}`
    const requirements = await buildAiRequirementsPayload()
    const res = await createPaperAssemblyTaskApiV1AiPaperAssemblyTasksPost({
      task_name: taskName,
      paper_title: paperForm.title || `试卷-${Date.now()}`,
      paper_type: examForm.type,
      assembly_mode: assemblyMode.value,
      knowledge_point_ids: aiKnowledgePointIds.value.length > 0 ? aiKnowledgePointIds.value : undefined,
      type_configs: aiTypeConfigs.map((c) => ({
        type: c.type,
        count: c.count,
        difficulty: c.difficulty,
        score: c.score,
      })),
      duration: examForm.duration,
      passing_score: examForm.passingScore,
      requirements: requirements || undefined,
    } as any)
    const taskId = (res as any)?.data?.id || (res as any)?.id
    if (!taskId) throw new Error('创建任务失败')
    aiTaskId.value = taskId
    aiTaskStatus.value = 'processing'
    pollAiTaskStatus(taskId)
  } catch (e: any) {
    message.error(e?.message || 'AI 生成试卷失败')
    aiGenerating.value = false
    aiAttachmentParsing.value = false
  }
}

function pollAiTaskStatus(taskId: number) {
  if (aiPollTimer.value) clearTimeout(aiPollTimer.value)
  aiPollTimer.value = setTimeout(async () => {
    try {
      const res = await getPaperAssemblyTaskDetailApiV1AiPaperAssemblyTasksTaskIdGet(taskId) as any
      const data = res?.data || res
      aiTaskStatus.value = data?.status || 'processing'
      if (data?.status === 'completed') {
        aiPaperDraft.value = data?.paper_draft || null
        paperForm.title = data?.paper_title || data?.paper_draft?.title || ''
        aiGenerating.value = false
        wizardStep.value = 2
      } else if (data?.status === 'failed') {
        message.error(data?.error_message || 'AI 生成失败')
        aiGenerating.value = false
      } else {
        pollAiTaskStatus(taskId)
      }
    } catch {
      pollAiTaskStatus(taskId)
    }
  }, 2000)
}

async function handleConfirmAndPublish() {
  if (!aiTaskId.value) { message.warning('无有效任务'); return }
  paperSubmitting.value = true
  try {
    const res = await confirmPaperAssemblyTaskApiV1AiPaperAssemblyTasksTaskIdConfirmPost(aiTaskId.value) as any
    const confirmedPaperId = res?.data?.confirmed_paper_id || res?.confirmed_paper_id
    if (!confirmedPaperId) throw new Error('确认失败，未返回试卷ID')
    await loadAvailablePapers()
    bindWizardPaper(confirmedPaperId)
    wizardStep.value = 3
  } catch (e: any) {
    message.error(e?.message || '确认发布失败')
  } finally {
    paperSubmitting.value = false
  }
}

function handleBackToStep1() {
  wizardStep.value = 1
  aiPaperDraft.value = null
  aiTaskId.value = null
}

async function handleWizardCreateExam() {
  const paperId = currentWizardPaperId.value
  if (!paperId) { message.warning('请先确认并发布试卷'); return }
  if (!validateExamForm(paperId)) return
  examSubmitting.value = true
  try {
    const payload = buildExamPayload(paperId)
    await createUnifiedExam(payload as any)
    message.success('考试创建成功')
    wizardModalVisible.value = false
    await void fetchExams()
  } catch (e: any) {
    message.error(e?.message || '创建考试失败')
  } finally {
    examSubmitting.value = false
  }
}

watch(routeTrainingId, () => {
  syncTrainingContext()
}, { immediate: true })

watch(manualTotalScore, (totalScore) => {
  if (wizardSelectMode.value !== 'manual' || totalScore <= 0) return
  const recommendedPassingScore = resolveRecommendedPassingScore(totalScore)
  if (recommendedPassingScore !== paperForm.passingScore) {
    paperForm.passingScore = recommendedPassingScore
  }
})
</script>

<style scoped>
/* =============================================
   全局字体统一（强制覆盖所有字体）
   ============================================= */
.exam-page,
.exam-layout,
.exam-page *,
.exam-layout * {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', sans-serif !important;
}

/* Ant Design 组件字体覆盖 */
.exam-page :deep(*) {
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', sans-serif !important;
}

/* =============================================
   SVG 图标全局兜底样式（防止图标放大）
   ============================================= */
.exam-page svg,
.exam-layout svg {
  display: block !important;
  flex-shrink: 0 !important;
  width: 16px !important;
  height: 16px !important;
}

.icon-xs { width: 14px !important; height: 14px !important; }
.icon-sm { width: 16px !important; height: 16px !important; }
.icon-md { width: 20px !important; height: 20px !important; }
.icon-lg { width: 24px !important; height: 24px !important; }
.icon-xl { width: 32px !important; height: 32px !important; }

/* =============================================
   Ant Design 图标尺寸修复（强制限制尺寸）
   ============================================= */
.exam-page :deep(.anticon),
.exam-layout :deep(.anticon) {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  flex-shrink: 0 !important;
  width: 16px !important;
  height: 16px !important;
  font-size: 16px !important;
  line-height: 16px !important;
}

.exam-page :deep(.anticon svg),
.exam-layout :deep(.anticon svg) {
  display: block !important;
  width: 16px !important;
  height: 16px !important;
  flex-shrink: 0 !important;
}

/* =============================================
   按钮兜底样式
   ============================================= */
.exam-page :deep(.ant-btn),
.exam-layout :deep(.ant-btn) {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.2s;
}

.exam-page :deep(.ant-btn svg),
.exam-layout :deep(.ant-btn svg) {
  flex-shrink: 0;
}

/* =============================================
   常用 utility class 兜底
   ============================================= */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.flex-1 { flex: 1; min-width: 0; }

.shrink-0 { flex-shrink: 0; }

/* =============================================
   页面基础布局
   ============================================= */
.exam-page {
  display: flex;
  flex-direction: row;
  width: 100%;
  min-height: 100vh;
  overflow: hidden;
  background: #F4F8FC;
}

/* =============================================
   移动端顶部 Header
   ============================================= */
.exam-mobile-header {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 58px;
  background: linear-gradient(135deg, #123A7A 0%, #1A56DB 100%);
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 50;
  color: #fff;
  box-shadow: 0 12px 32px rgba(13, 44, 96, 0.2);
}

.exam-mobile-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.exam-mobile-header-mark {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #7DD3FC;
  box-shadow: 0 0 0 6px rgba(125, 211, 252, 0.14);
  flex-shrink: 0;
}

.exam-mobile-header-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.exam-mobile-title {
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.1;
}

.exam-mobile-subtitle {
  font-size: 11px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.78);
  white-space: nowrap;
}

.exam-mobile-avatar {
  width: 34px;
  height: 34px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.22);
  color: #FFFFFF;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
}

/* =============================================
   主布局
   ============================================= */
.exam-layout {
  flex: 1;
  width: 100%;
  min-width: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

@media (max-width: 768px) {
  .exam-page {
    flex-direction: column;
    background: linear-gradient(180deg, #EEF5FF 0%, #F4F8FC 180px, #F4F8FC 100%);
  }

  .exam-mobile-header {
    display: flex;
  }

  .exam-layout {
    flex: 1;
    padding-top: 58px;
    min-width: 0;
  }
}

/* =============================================
   顶部功能控制区
   ============================================= */
.exam-header {
  background: #FFFFFF;
  border-bottom: 1px solid #E8F1F8;
  padding: 24px 40px 0;
}

.exam-header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding-bottom: 20px;
  gap: 24px;
}

.exam-header-title h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 900;
  color: #1E3A5F;
  letter-spacing: -0.5px;
}

.exam-header-title p {
  margin: 6px 0 0;
  font-size: 14px;
  font-weight: 500;
  color: #64748B;
}

.exam-header-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.exam-search-wrapper {
  position: relative;
  width: 320px;
}

.exam-search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: #64748B;
  pointer-events: none;
}

.exam-search-input {
  width: 100%;
  height: 44px;
  padding: 0 16px 0 44px;
  border: 1px solid #CDE0F5;
  border-radius: 8px;
  background: #FFFFFF;
  font-size: 14px;
  color: #1E3A5F;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.exam-search-input:focus {
  border-color: #1A56DB;
  box-shadow: 0 0 0 3px rgba(26, 86, 219, 0.1);
}

.exam-search-input::placeholder {
  color: #64748B;
}

.exam-header-btns {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 排序选择器 */
.exam-sort-select {
  width: 130px;
}

.exam-sort-select :deep(.ant-select-selector) {
  height: 40px !important;
  line-height: 38px !important;
  border: 1px solid #CDE0F5 !important;
  border-radius: 8px !important;
  background: #FFFFFF !important;
}

.exam-sort-select :deep(.ant-select-selection-item) {
  color: #1E3A5F !important;
  font-weight: 600 !important;
}

/* 创建考试按钮 */
.exam-create-btn {
  height: 40px;
  padding: 0 20px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 14px;
  background: #1A56DB !important;
  border-color: #1A56DB !important;
  display: flex;
  align-items: center;
  gap: 8px;
}

.exam-create-btn:hover {
  background: #1546B5 !important;
  border-color: #1546B5 !important;
}

/* =============================================
   Tab与过滤栏
   ============================================= */
.exam-header-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 0;
}

.exam-tabs {
  display: flex;
  align-items: center;
  gap: 0;
}

.exam-tab {
  padding: 12px 16px;
  font-size: 15px;
  font-weight: 500;
  color: #64748B;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  margin-right: 24px;
}

.exam-tab:hover {
  color: #1E3A5F;
}

.exam-tab.active {
  color: #1A56DB;
  font-weight: 700;
  border-bottom-color: #1A56DB;
}

/* 状态筛选器 */
.exam-status-filter {
  display: flex;
  background: #F0F5FA;
  border: 1px solid #CDE0F5;
  border-radius: 8px;
  padding: 4px;
  gap: 4px;
}

.exam-status-btn {
  padding: 8px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 700;
  color: #64748B;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.exam-status-btn:hover {
  color: #1E3A5F;
}

.exam-status-btn.active {
  background: #FFFFFF;
  color: #1A56DB;
  box-shadow: 0 1px 3px rgba(30, 58, 95, 0.1);
}

/* =============================================
   数据统计摘要
   ============================================= */
.exam-stats {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  padding: 16px 40px;
  background: #F8FBFF;
  border-bottom: 1px solid #E8F1F8;
  font-size: 14px;
  color: #64748B;
}

.exam-stats-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 8px 14px;
  background: #FFFFFF;
  border: 1px solid #D9E7F3;
  border-radius: 999px;
}

.exam-stats-item-primary {
  background: #ECF3FF;
  border-color: #CFE0FF;
}

.exam-stats strong {
  color: #1E3A5F;
  font-size: 18px;
  margin: 0 4px;
}

.exam-stats-sep {
  color: #CDE0F5;
}

@media (max-width: 768px) {
  .exam-stats {
    padding: 12px 16px;
    font-size: 13px;
  }
  .exam-stats strong {
    font-size: 16px;
  }
  .exam-stats-sep {
    display: none;
  }
}

/* =============================================
   加载 & 空状态
   ============================================= */
.exam-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80px 0;
}

.exam-empty {
  padding: 80px 0;
}

@media (max-width: 768px) {
  .exam-loading,
  .exam-empty {
    padding: 40px 0;
  }
}

/* =============================================
   考试列表
   ============================================= */
.exam-list {
  flex: 1;
  background: #F4F8FC;
  padding-bottom: 24px;
}

/* PC端列表头 */
.exam-list-header {
  display: flex;
  align-items: center;
  padding: 12px 40px;
  background: #FFFFFF;
  border-bottom: 1px solid #E8F1F8;
  font-size: 13px;
  font-weight: 700;
  color: #64748B;
  letter-spacing: 0.5px;
}

.exam-list-col {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.exam-list-col-main {
  flex: 1;
  padding-right: 24px;
}

.exam-list-col-dur,
.exam-list-col-qty,
.exam-list-col-score {
  width: 80px;
  text-align: center;
  padding: 0 8px;
  border-left: 1px solid #E8F1F8;
}

.exam-list-col-time {
  width: 160px;
  padding-left: 32px;
}

.exam-list-col-action {
  width: 100px;
  text-align: right;
}

/* 列表行 */
.exam-row {
  position: relative;
  display: flex;
  align-items: stretch;
  padding: 0 40px;
  background: #FFFFFF;
  border-bottom: 1px solid #E8F1F8;
  cursor: pointer;
  transition: background-color 0.15s;
}

.exam-row:hover {
  background: #F8FBFF;
}

.exam-row-ended {
  opacity: 0.8;
}

.exam-row-ended:hover {
  opacity: 1;
}

/* 状态指示条 */
.exam-row-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

/* 考试信息 */
.exam-row-main {
  flex: 1;
  padding: 20px 24px 20px 0;
  min-width: 0;
}

.exam-row-tags {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.exam-tag {
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-radius: 4px;
  border: 1px solid;
}

.exam-tag-active {
  background: #ECFDF5;
  color: #059669;
  border-color: #A7F3D0;
}

.exam-tag-upcoming {
  background: #EFF6FF;
  color: #1A56DB;
  border-color: #BFDBFE;
}

.exam-tag-ended {
  background: #F1F5F9;
  color: #64748B;
  border-color: #E2E8F0;
}

.exam-tag-kind {
  background: #F8FBFF;
  color: #45637D;
  border-color: #D6E4F1;
}

.exam-row-title {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 700;
  color: #1E3A5F;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.exam-row:hover .exam-row-title {
  color: #1A56DB;
}

.exam-row-class {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #64748B;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* PC端指标 */
.exam-row-metrics {
  display: flex;
  align-items: center;
  text-align: center;
}

.exam-metric {
  width: 80px;
  padding: 20px 8px;
  border-left: 1px solid #E8F1F8;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.exam-metric-value {
  font-size: 18px;
  font-weight: 700;
  color: #1E3A5F;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.exam-metric-label {
  font-size: 12px;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 4px;
}

/* 时间安排 */
.exam-row-time {
  width: 160px;
  padding-left: 32px;
  padding-right: 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 12px;
}

.exam-row-time-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.exam-time-label {
  font-size: 12px;
  color: #94A3B8;
  letter-spacing: 0.3px;
}

.exam-time-date {
  font-size: 14px;
  font-weight: 700;
  color: #1E3A5F;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.exam-time-pass {
  font-size: 12px;
  color: #64748B;
  margin-top: 6px;
}

/* 操作按钮 */
.exam-row-action {
  width: 100px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.exam-action-btn {
  padding: 8px 20px;
  height: auto;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
  border: 1px solid #CDE0F5;
  background: #F0F5FA;
  color: #1A56DB;
}

.exam-action-btn:hover {
  background: #1A56DB;
  color: #FFFFFF;
  border-color: #1A56DB;
}

/* 移动端表格信息 */
.exam-row-mobile-table {
  display: none;
  margin-top: 16px;
  overflow: hidden;
  border: 1px solid #D9E5F2;
  border-radius: 16px;
  background: #F8FBFF;
}

.exam-row-mobile-cell {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  min-height: 72px;
  padding: 12px 10px;
  border-right: 1px solid #E2EBF5;
  border-bottom: 1px solid #E2EBF5;
  text-align: center;
}

.exam-row-mobile-label {
  font-size: 12px;
  color: #7A8CA5;
  line-height: 1;
}

.exam-row-mobile-value {
  font-size: 16px;
  font-weight: 700;
  color: #17365D;
  line-height: 1.25;
}

.exam-row-mobile-cell-wide {
  align-items: flex-start;
  text-align: left;
}

/* =============================================
   移动端适配
   ============================================= */
@media (max-width: 768px) {
  .exam-header {
    margin: 12px 12px 0;
    padding: 18px 16px 14px;
    border: 1px solid rgba(205, 224, 245, 0.8);
    border-radius: 22px;
    box-shadow: 0 18px 40px rgba(30, 58, 95, 0.08);
  }

  .exam-header-top {
    flex-direction: column;
    align-items: stretch;
    gap: 14px;
    padding-bottom: 16px;
  }

  .exam-header-title h1 {
    font-size: 24px;
    letter-spacing: -0.4px;
  }

  .exam-header-title p {
    font-size: 13px;
    line-height: 1.5;
  }

  .exam-header-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .exam-search-wrapper {
    width: 100%;
  }

  .exam-header-btns {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 10px;
  }

  .exam-header-bottom {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
    padding-bottom: 0;
    overflow: visible;
  }

  .exam-tabs {
    width: calc(100% + 32px);
    margin: 0 -16px;
    padding: 0 16px 6px;
    overflow-x: auto;
    scrollbar-width: none;
  }

  .exam-tabs::-webkit-scrollbar {
    display: none;
  }

  .exam-tab {
    padding: 10px 14px;
    margin-right: 8px;
    font-size: 14px;
    border: 1px solid #DCE7F2;
    border-radius: 999px;
    background: #F4F7FB;
  }

  .exam-tab.active {
    color: #FFFFFF;
    background: #1A56DB;
    border-color: #1A56DB;
    box-shadow: 0 10px 20px rgba(26, 86, 219, 0.18);
  }

  .exam-status-filter {
    width: 100%;
    overflow-x: auto;
    padding: 4px;
    gap: 6px;
    scrollbar-width: none;
  }

  .exam-status-filter::-webkit-scrollbar {
    display: none;
  }

  .exam-status-btn {
    flex: 0 0 auto;
    padding: 9px 14px;
  }

  .exam-sort-select {
    width: 100%;
  }

  .exam-create-btn {
    justify-content: center;
    padding: 0 16px;
  }

  .exam-stats {
    padding: 12px;
    gap: 8px;
    background: transparent;
    border-bottom: none;
  }

  .exam-stats-item {
    font-size: 13px;
  }

  .exam-list-header {
    display: none;
  }

  .exam-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 0 12px 92px;
    background: transparent;
  }

  .exam-row {
    flex-direction: column;
    padding: 16px;
    position: relative;
    border: 1px solid #DDE8F3;
    border-radius: 20px;
    box-shadow: 0 14px 30px rgba(30, 58, 95, 0.08);
    overflow: hidden;
  }

  .exam-row-accent {
    display: block;
    left: 0;
    right: 0;
    top: 0;
    bottom: auto;
    width: auto;
    height: 4px;
  }

  .exam-row-main {
    padding: 4px 0 0;
  }

  .exam-row-title {
    font-size: 17px;
    line-height: 1.4;
    white-space: normal;
  }

  .exam-row-class {
    align-items: flex-start;
    white-space: normal;
    line-height: 1.6;
  }

  .exam-row-class span {
    overflow: visible;
    text-overflow: initial;
    white-space: normal;
  }

  .exam-row-metrics {
    display: none;
  }

  .exam-row-time {
    display: none;
  }

  .exam-row-mobile-table {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }

  .exam-row-mobile-cell {
    min-height: 64px;
    padding: 10px 8px;
  }

  .exam-row-mobile-cell:nth-child(3),
  .exam-row-mobile-cell:nth-child(5) {
    border-right: none;
  }

  .exam-row-mobile-cell:nth-child(4),
  .exam-row-mobile-cell:nth-child(5) {
    border-bottom: none;
  }

  .exam-row-mobile-cell:nth-child(-n+3) {
    grid-column: span 2;
  }

  .exam-row-mobile-cell-wide {
    grid-column: span 3;
  }

  .exam-row-action {
    width: 100%;
    justify-content: stretch;
    padding: 14px 0 0;
    border-top: 1px solid #E8F1F8;
    margin-top: 14px;
  }

  .exam-row-action :deep(.ant-btn) {
    width: 100%;
    height: 42px;
    border-radius: 12px;
    font-weight: 700;
  }

  .exam-action-btn {
    padding: 10px 20px;
    width: 100%;
  }
}

@media (max-width: 480px) {
  .exam-header {
    margin: 10px 10px 0;
    padding: 16px 14px 12px;
    border-radius: 18px;
  }

  .exam-header-title h1 {
    font-size: 22px;
  }

  .exam-header-title p {
    display: none;
  }

  .exam-mobile-subtitle {
    font-size: 10px;
  }

  .exam-header-btns {
    grid-template-columns: 1fr;
  }

  .exam-list {
    padding: 0 10px 88px;
  }

  .exam-row {
    padding: 14px;
    border-radius: 18px;
  }

  .exam-row-mobile-label {
    font-size: 11px;
  }

  .exam-row-mobile-value {
    font-size: 14px;
  }
}

/* =============================================
   弹窗通用样式（保留原有逻辑）
   ============================================= */
.modal-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-filter-row {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.modal-picker-layout {
  display: flex;
  gap: 16px;
}

.picker-left {
  flex: 1;
  min-width: 0;
}

.picker-right {
  width: 220px;
  flex-shrink: 0;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  padding: 12px;
  max-height: 420px;
  overflow-y: auto;
}

.picker-right-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--v2-text-secondary);
  margin-bottom: 12px;
}

.picker-right-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.picker-right-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: #f8f9ff;
  border-radius: 6px;
  font-size: 12px;
}

.picker-right-q-type {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  background: #2563EB;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
}

.picker-right-q-text {
  flex: 1;
  color: var(--v2-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.table-q-content {
  font-size: 13px;
  color: var(--v2-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 400px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

/* 表单字段 */
.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.field-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--v2-text-secondary);
}

.field-label.required::after {
  content: ' *';
  color: #ef4444;
}

.selected-questions-summary {
  font-size: 13px;
  color: var(--v2-text-secondary);
  padding: 8px 12px;
  background: #f8f9ff;
  border-radius: 8px;
}

.paper-hint {
  margin-top: 6px;
}

.hint-text {
  font-size: 12px;
  color: var(--v2-text-muted);
}

.paper-preview-card {
  padding: 14px 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f8faff 0%, #eef3ff 100%);
  border: 1px solid rgba(37, 99, 235, 0.12);
}

.paper-preview-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.paper-preview-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--v2-text-primary);
}

.paper-preview-meta,
.paper-preview-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.paper-preview-empty {
  font-size: 13px;
  color: var(--v2-text-muted);
}

.text-center {
  text-align: center;
}

.text-muted {
  color: var(--v2-text-muted);
}

/* 向导弹窗 */
.wizard-header {
  text-align: center;
  margin-bottom: 24px;
}

.wizard-title {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 700;
  color: var(--v2-text-primary);
}

.wizard-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.wizard-steps {
  margin-bottom: 24px;
}

.wizard-step-content {
  min-height: 400px;
}

.step1-mode-tabs {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.manual-select-section,
.ai-select-section {
  min-height: 380px;
}

.ai-select-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.ai-input-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
  gap: 16px;
  align-items: stretch;
}

.ai-requirements-card,
.ai-attachments-card {
  padding: 12px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(13, 110, 253, 0.06), rgba(255, 255, 255, 0.96));
  border: 1px solid rgba(13, 110, 253, 0.12);
}

.ai-requirements-card {
  display: flex;
  flex-direction: column;
}

.ai-requirements-hint {
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--v2-text-secondary);
}

.type-config-section {
  margin: 16px 0;
}

.type-config-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--v2-text-secondary);
  margin-bottom: 10px;
}

.ai-summary {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: var(--v2-text-secondary);
  padding: 10px 14px;
  background: #f8f9ff;
  border-radius: 8px;
  margin-bottom: 8px;
}

.ai-summary strong {
  color: var(--v2-primary);
}

.ai-generating {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  background: #fff7e6;
  border: 1px solid #ffd591;
  border-radius: 8px;
  color: #d46b08;
  font-size: 13px;
  margin: 12px 0;
}

.paper-draft-preview {
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  overflow: hidden;
  max-height: 420px;
  overflow-y: auto;
}

.paper-draft-header {
  padding: 16px 20px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.paper-draft-title {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 700;
  color: var(--v2-text-primary);
}

.paper-draft-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 13px;
  color: var(--v2-text-secondary);
  align-items: center;
}

.paper-draft-questions {
  padding: 12px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.paper-draft-q-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px 10px;
  background: #f8f9ff;
  border-radius: 6px;
  font-size: 13px;
}

.paper-draft-q-num {
  flex-shrink: 0;
  font-weight: 700;
  color: var(--v2-text-secondary);
  min-width: 24px;
}

.paper-draft-q-text {
  flex: 1;
  color: var(--v2-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.paper-draft-q-score {
  flex-shrink: 0;
  color: var(--v2-primary);
  font-weight: 600;
}

/* 响应式调整 */
@media (max-width: 960px) {
  .ai-input-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .exam-header-btns {
    width: 100%;
    justify-content: flex-end;
  }

  .form-row,
  .modal-picker-layout,
  .paper-preview-head {
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .picker-right {
    width: 100%;
  }
}

/* Ant Design 覆盖样式 */
:deep(.ai-requirements-card .ant-input) {
  flex: 1;
}

:deep(.ai-attachments-card .ant-upload-wrapper .ant-upload-drag) {
  background: rgba(255, 255, 255, 0.78);
  border-radius: 10px;
  border-color: rgba(13, 110, 253, 0.18);
  height: 42px !important;
  min-height: 42px !important;
  padding: 4px 8px !important;
  overflow: hidden;
}

:deep(.ai-attachments-card .ant-upload-wrapper .ant-upload-drag .ant-upload.ant-upload-btn) {
  display: block;
  min-height: 42px;
  padding: 5px 8px !important;
}

:deep(.ai-attachments-card .ant-upload-wrapper .ant-upload-drag .ant-upload-drag-icon) {
  display: none !important;
}

:deep(.ai-attachments-card .ant-upload-wrapper .ant-upload-drag .ant-upload-drag-icon .anticon) {
  display: none !important;
}

:deep(.ai-attachments-card .ant-upload-wrapper .ant-upload-drag .ant-upload-text) {
  margin: 0 !important;
  font-size: 13px;
  line-height: 1.4;
}

:deep(.ai-attachments-card .ant-upload-wrapper .ant-upload-drag .ant-upload-hint) {
  display: none !important;
}

:deep(.ai-attachments-card .ant-upload-wrapper .ant-upload-drag p) {
  margin-bottom: 0 !important;
}

:deep(.ai-attachments-card .ant-upload-list) {
  margin-top: 10px;
}
</style>
