<template>
  <DarkPageHeader
    title="在线考试"
    subtitle="检验学习成果，提升执法能力。"
    :search-placeholder="searchPlaceholder"
    v-model="filters.search"
    @search="fetchExams"
  >
    <template #filters>
      <button type="button" class="dark-chip" :class="{ active: activeTab === 'admission' }" @click="switchTab('admission')">准入考试</button>
      <button type="button" class="dark-chip" :class="{ active: activeTab === 'training' }" @click="switchTab('training')">培训班考试</button>
      <span class="dark-chip-sep" />
      <button v-for="tab in statusTabs" :key="tab.key" type="button" class="dark-chip" :class="{ active: filters.status === tab.key }" @click="selectStatus(tab.key)">{{ tab.label }}</button>
    </template>
    <template #actions>
      <div class="header-actions">
        <a-select v-model:value="filters.sort" class="dark-sort-select" @change="fetchExams">
          <a-select-option value="latest">按最新</a-select-option>
          <a-select-option value="upcoming">即将开始</a-select-option>
          <a-select-option value="active">进行中</a-select-option>
        </a-select>
        <a-button v-if="!isStudentView" type="primary" @click="openWizardModal">
          一站式创建
        </a-button>
      </div>
    </template>
  </DarkPageHeader>

    <div class="exam-stats">
      <span>共 <strong>{{ exams.length }}</strong> 场考试</span>
      <span v-if="ongoingCount > 0">进行中 <strong>{{ ongoingCount }}</strong> 场</span>
      <span v-if="upcomingCount > 0">即将开始 <strong>{{ upcomingCount }}</strong> 场</span>
    </div>

    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" />
    </div>

    <a-empty v-else-if="!exams.length" description="暂无考试" class="empty-block" />

    <div v-else class="exam-grid">
      <div
        v-for="(exam, index) in exams"
        :key="exam.id"
        class="exam-card"
        :style="{ '--card-accent': getExamAccent(exam.status) }"
        @click="handleExamClick(exam)"
      >
        <div class="card-cover" :style="{ background: getExamCoverBackground(exam, index) }">
            <div class="cover-labels">
            <a-tag class="cover-tag cover-tag-status" :class="getStatusClass(exam.status)">
              {{ getDisplayStatusText(exam) }}
            </a-tag>
            <div class="cover-tag-stack">
              <a-tag v-if="isStudentView && exam.can_join" class="cover-tag cover-tag-action">可参加</a-tag>
              <a-tag v-if="exam.attempt_count && exam.attempt_count > 0" class="cover-tag cover-tag-attempt">
                已考 {{ exam.attempt_count }} 次
              </a-tag>
            </div>
          </div>

          <div class="cover-visual">
            <span class="cover-visual-ring">
              <FileTextOutlined class="cover-visual-icon" />
            </span>
          </div>

          <div class="cover-footer">
            <span class="cover-footer-item">
              <ClockCircleOutlined />
              {{ exam.duration || 0 }} 分钟
            </span>
            <span class="cover-footer-item">
              <QuestionCircleOutlined />
              {{ exam.question_count || 0 }} 题
            </span>
            <span class="cover-footer-item">
              <SafetyCertificateOutlined />
              满分 {{ exam.total_score || 0 }}
            </span>
          </div>
        </div>

        <div class="card-body">
          <div class="card-head">
            <div class="card-head-main">
              <div v-if="exam.training_name" class="course-tag">
                <BookOutlined /> 所属班级：{{ exam.training_name }}
              </div>
              <div v-if="exam.course_names?.length" class="course-tag">
                <BookOutlined /> 关联课程：{{ exam.course_names.join('、') }}
              </div>
              <h3>{{ exam.title }}</h3>
              <p>{{ exam.description || '暂无考试说明' }}</p>
            </div>
          </div>

          <div class="meta-grid">
            <span>
              <CalendarOutlined />
              {{ exam.start_time ? formatDate(exam.start_time) : '不限时' }}
            </span>
            <span>
              <SafetyOutlined />
              及格 {{ exam.passing_score || 0 }} 分
            </span>
          </div>

          <div class="action-row">
            <template v-if="!isStudentView">
              <a-button type="primary" block @click.stop="goToExamOverview(exam)">
                查看考试情况
              </a-button>
            </template>
            <template v-else-if="shouldShowResult(exam)">
              <a-button type="primary" block @click.stop="goToExamResult(exam)">
                查看结果
              </a-button>
            </template>
            <template v-else-if="exam.can_join">
              <a-button type="primary" block @click.stop="goToExamOverview(exam)">
                进入考试
              </a-button>
            </template>
            <template v-else>
              <a-button type="primary" block disabled>
                {{ getDisplayStatusText(exam) }}
              </a-button>
            </template>
          </div>
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
      :title="activeTab === 'admission' ? '创建准入考试' : '创建培训班考试'"
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
        <div v-if="activeTab === 'admission'" class="form-field">
          <label class="field-label required">关联课程</label>
          <a-select
            v-model:value="examForm.courseIds"
            mode="multiple"
            placeholder="请选择关联课程，用于关联学员"
            style="width: 100%"
            allow-clear
          >
            <a-select-option v-for="c in availableCourses" :key="c.id" :value="c.id">{{ c.title || c.name }}</a-select-option>
          </a-select>
          <div class="paper-hint">
            <span class="hint-text">准入考试将根据所关联课程同步关联学员</span>
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

    <!-- ===== 一站式创建向导 ===== -->
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
        <h2 class="wizard-title">一站式创建考试</h2>
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
            <div class="ai-requirements-card">
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
                <p class="ant-upload-hint">
                  支持 PDF、DOC、DOCX、XLS、XLSX、CSV、TXT、MD、PPT、PPTX，上传后会自动解析文本。
                </p>
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
          <label class="field-label" :class="{ required: activeTab === 'admission' }">关联课程</label>
          <a-select
            v-model:value="examForm.courseIds"
            mode="multiple"
            :placeholder="activeTab === 'admission' ? '请选择关联课程，用于关联学员' : '请选择关联课程（可选）'"
            style="width: 100%"
            allow-clear
          >
            <a-select-option v-for="c in availableCourses" :key="c.id" :value="c.id">{{ c.title || c.name }}</a-select-option>
          </a-select>
          <div v-if="activeTab === 'admission'" class="paper-hint">
            <span class="hint-text">准入考试将根据所关联课程同步关联学员</span>
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
</template>

<script setup lang="ts">
import {
  BookOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  QuestionCircleOutlined,
  SafetyCertificateOutlined,
  SafetyOutlined,
  CloseOutlined,
} from '@ant-design/icons-vue'
import DarkPageHeader from '@/components/common/DarkPageHeader.vue'
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
  getAdmissionExamsApiV1ExamsAdmissionGet,
  getExamsApiV1ExamsGet,
  getExamPapersApiV1ExamsPapersGet,
  createExamPaperApiV1ExamsPapersPost,
  publishExamPaperApiV1ExamsPapersPaperIdPublishPost,
  createExamApiV1ExamsPost,
  createAdmissionExamApiV1ExamsAdmissionPost,
} from '@/api/generated/exam-management/exam-management'
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
const activeTab = ref<'admission' | 'training'>('admission')
const exams = ref<ExamResponse[]>([])
const isStudentView = computed(() => authStore.isStudent)
const searchPlaceholder = computed(() => (
  activeTab.value === 'training' ? '搜索考试名称或班级名称...' : '搜索考试名称...'
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
  if (activeTab.value === 'admission' && examForm.courseIds.length === 0) return false
  return true
})
const currentWizardPaperId = computed(() => examForm.paperId ?? wizardPaperId.value ?? undefined)
const currentWizardPaperSummary = computed(() => getSelectedPaperSummary(currentWizardPaperId.value))
const canSubmitWizardExam = computed(() => {
  if (!examForm.title.trim() || !currentWizardPaperId.value) return false
  if (activeTab.value === 'training' && !effectiveTrainingId.value) return false
  if (activeTab.value === 'admission' && examForm.courseIds.length === 0) return false
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
    .filter((item): item is File => item instanceof File)

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
  void fetchExams()
})

async function fetchExams() {
  loading.value = true
  try {
    const params = { page: 1, size: 50, search: filters.search || undefined }
    const response = activeTab.value === 'admission'
      ? await getAdmissionExamsApiV1ExamsAdmissionGet(params)
      : await getExamsApiV1ExamsGet(params)

    let items = response?.items || []

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

function switchTab(tab: 'admission' | 'training') {
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

function formatDate(date?: string | null) {
  if (!date) return ''
  return dayjs(date).format('MM/DD HH:mm')
}

function shouldShowResult(exam: ExamResponse) {
  // 只有确实存在考试记录（attempt_count > 0）时才显示结果按钮
  return Number(exam.attempt_count || 0) > 0
}

function goToExamOverview(exam: ExamResponse) {
  const kind = resolveExamKind(exam.kind, activeTab.value)
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
    query: { kind: resolveExamKind(exam.kind, activeTab.value) },
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
  if (activeTab.value === 'admission' && examForm.courseIds.length === 0) {
    message.warning('请选择关联课程')
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
  const totalScore = Number(paper?.total_score ?? paper?.totalScore ?? 0)
  if (totalScore > 0 && Number(examForm.passingScore) > totalScore) {
    message.warning('及格分不能超过试卷总分')
    return false
  }
  return true
}

function buildExamPayload(paperId: number) {
  const payload: any = {
    title: examForm.title.trim(),
    paper_id: paperId,
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
  if (activeTab.value !== 'admission') {
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
    if (activeTab.value === 'admission') {
      await createAdmissionExamApiV1ExamsAdmissionPost(payload as any)
    } else {
      await createExamApiV1ExamsPost(payload as any)
    }
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
    if (activeTab.value === 'admission') {
      await createAdmissionExamApiV1ExamsAdmissionPost(payload as any)
    } else {
      await createExamApiV1ExamsPost(payload as any)
    }
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
/* ── dark chip separator ── */
.dark-chip-sep {
  display: inline-block; width: 1px; height: 20px;
  background: rgba(255,255,255,0.16); margin: 0 4px;
  flex-shrink: 0; align-self: center;
}

/* ── dark sort select ── */
.dark-sort-select { width: 130px; }
:deep(.dark-sort-select .ant-select-selector) {
  background: rgba(255,255,255,0.08) !important; border-color: rgba(255,255,255,0.18) !important;
  color: rgba(255,255,255,0.88) !important; border-radius: 20px !important;
}
:deep(.dark-sort-select .ant-select-arrow) { color: rgba(255,255,255,0.5) !important; }
:deep(.dark-sort-select .ant-select-selection-item) { color: rgba(255,255,255,0.88) !important; }

.exam-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
  color: var(--v2-text-secondary);
}

.loading-wrapper,
.empty-block {
  padding: 80px 0;
}

.exam-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.exam-card {
  overflow: hidden;
  background: var(--v2-bg-card);
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(24, 39, 75, 0.08);
  cursor: pointer;
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease;
}

.exam-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 24px 48px rgba(75, 110, 245, 0.12);
}

.card-cover {
  position: relative;
  height: 180px;
  padding: 18px;
  overflow: hidden;
}

.card-cover::before {
  content: '';
  position: absolute;
  right: -34px;
  bottom: -70px;
  width: 210px;
  height: 210px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  filter: blur(8px);
}

.cover-labels {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.cover-tag-stack {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

:deep(.cover-tag.ant-tag) {
  margin: 0;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.35;
  border: 1px solid rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

:deep(.cover-tag-status.ant-tag) {
  color: #405f7f;
}

:deep(.cover-tag-action.ant-tag) {
  color: #2DA44E;
  border-color: rgba(52, 199, 89, 0.48);
  background: rgba(52, 199, 89, 0.08);
}

:deep(.cover-tag-attempt.ant-tag) {
  color: #7867c6;
}

.cover-visual {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-visual-ring {
  position: relative;
  width: 82px;
  height: 82px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.78);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.7));
  box-shadow:
    0 16px 28px var(--card-accent, rgba(75, 110, 245, 0.14)),
    inset 0 1px 0 rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
}

.cover-visual-icon {
  position: relative;
  z-index: 1;
  font-size: 34px;
  color: var(--card-accent, #4B6EF5);
}

.cover-footer {
  position: absolute;
  left: 12px;
  right: 22px;
  bottom: 10px;
  z-index: 2;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.cover-footer-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  padding: 0 11px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(18, 25, 38, 0.78);
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.72);
}

.card-body {
  padding: 22px 22px 24px;
}

.card-head {
  margin-bottom: 16px;
}

.card-head-main .course-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 600;
  color: var(--v2-primary);
  background: var(--v2-primary-light);
  border: 1px solid rgba(75, 110, 245, 0.2);
  padding: 4px 12px;
  border-radius: 999px;
  margin-bottom: 10px;
}

.card-head-main h3 {
  margin: 0 0 10px;
  font-size: 21px;
  line-height: 1.35;
  color: var(--v2-text-primary);
}

.card-head-main p {
  margin: 0;
  min-height: 44px;
  color: var(--v2-text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px 14px;
  margin-bottom: 16px;
  color: var(--v2-text-secondary);
  font-size: 14px;
}

.meta-grid span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.action-row {
  padding-top: 4px;
}

:deep(.status-ongoing) {
  color: #2DA44E;
  background: rgba(52, 199, 89, 0.1);
  border: none;
}

:deep(.status-upcoming) {
  color: #4B6EF5;
  background: rgba(75, 110, 245, 0.1);
  border: none;
}

:deep(.status-finished) {
  color: #8E8E93;
  background: rgba(142, 142, 147, 0.1);
  border: none;
}

@media (max-width: 768px) {
  .exam-grid,
  .meta-grid {
    grid-template-columns: 1fr;
  }

  .dark-chip-sep { display: none; }

  .card-cover {
    height: 164px;
  }

  .cover-labels {
    flex-direction: column;
  }

  .cover-tag-stack {
    justify-content: flex-start;
  }
}

/* ===== header 操作按钮 ===== */
.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.header-actions :deep(.ant-btn) {
  border-radius: 8px;
  font-weight: 600;
  height: 36px;
  padding: 0 20px;
  border: 1px solid rgba(37, 99, 235, 0.3);
  color: var(--v2-primary);
  background: rgba(255, 255, 255, 0.9);
}

.header-actions :deep(.ant-btn:hover) {
  border-color: var(--v2-primary);
  background: var(--v2-primary-light);
}

.header-actions :deep(.ant-btn-primary) {
  background: #2563EB;
  color: white;
  border-color: #2563EB;
}

.header-actions :deep(.ant-btn-primary:hover) {
  background: #1d4ed8;
  border-color: #1d4ed8;
}

/* ===== 弹窗通用 ===== */
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

/* ===== 表单字段 ===== */
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

/* ===== 向导弹窗 ===== */
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

/* ===== Step 1 模式切换 ===== */
.step1-mode-tabs {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.manual-select-section,
.ai-select-section {
  min-height: 380px;
}

@media (max-width: 768px) {
  .header-actions {
    width: 100%;
    justify-content: flex-end;
    flex-wrap: wrap;
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

/* ===== AI 智能组卷 ===== */
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
  padding: 16px;
  border-radius: 12px;
  background:
    linear-gradient(135deg, rgba(13, 110, 253, 0.06), rgba(255, 255, 255, 0.96));
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

:deep(.ai-requirements-card .ant-input) {
  flex: 1;
}

:deep(.ai-attachments-card .ant-upload-wrapper .ant-upload-drag) {
  background: rgba(255, 255, 255, 0.78);
  border-radius: 10px;
  border-color: rgba(13, 110, 253, 0.18);
  min-height: 104px;
}

:deep(.ai-attachments-card .ant-upload-wrapper .ant-upload-drag .ant-upload) {
  padding: 14px 12px;
}

:deep(.ai-attachments-card .ant-upload-wrapper .ant-upload-drag .ant-upload-drag-icon) {
  margin-bottom: 6px;
}

:deep(.ai-attachments-card .ant-upload-wrapper .ant-upload-drag .ant-upload-drag-icon .anticon) {
  font-size: 24px;
}

:deep(.ai-attachments-card .ant-upload-wrapper .ant-upload-drag .ant-upload-text) {
  margin-bottom: 2px;
  font-size: 14px;
}

:deep(.ai-attachments-card .ant-upload-wrapper .ant-upload-drag .ant-upload-hint) {
  font-size: 12px;
  line-height: 1.5;
}

:deep(.ai-attachments-card .ant-upload-list) {
  margin-top: 10px;
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

/* ===== 试卷草稿预览 ===== */
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

@media (max-width: 960px) {
  .ai-input-grid {
    grid-template-columns: 1fr;
  }
}
</style>
