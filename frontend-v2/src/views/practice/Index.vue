<template>
  <div class="practice-page">
    <!-- 移动端顶部 Header -->
    <header class="practice-mobile-header">
      <div class="practice-mobile-header-left">
        <button class="practice-mobile-menu-btn">
          <svg class="w-6 h-6 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
        </button>
        <span class="practice-mobile-title">{{ isInstructor ? '题库管理' : '刷题练习' }}</span>
      </div>
      <div class="practice-mobile-avatar">{{ avatarText }}</div>
    </header>

    <!-- 主布局 -->
    <div class="practice-layout">
      <!-- 顶部功能控制区 -->
      <header class="practice-header">
        <!-- 上半部：标题与操作 -->
        <div class="practice-header-top">
          <div class="practice-header-title">
            <h1>{{ isInstructor ? '题库管理' : '刷题练习' }}</h1>
            <p>{{ isInstructor ? '管理个人题库，上传材料生成题目。' : '选择知识点或题库，开启专项练习。' }}</p>
          </div>
          <div class="practice-header-controls">
            <div class="practice-search-wrapper">
              <svg class="practice-search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
              </svg>
              <input
                type="text"
                class="practice-search-input"
                :placeholder="isInstructor ? '搜索题库名称...' : '搜索知识点名称...'"
                v-model="searchKeyword"
              />
            </div>
            <div class="practice-header-btns">
              <template v-if="isInstructor">
                <a-select v-model:value="instructorCourseId" placeholder="按课程筛选" allow-clear class="practice-course-select" @change="handleCourseSelectChange">
                  <a-select-option v-for="item in courses" :key="item.id" :value="item.id">{{ item.title }}</a-select-option>
                </a-select>
                <a-button ghost @click="openAiTaskListModal">任务列表</a-button>
                <a-button type="primary" class="practice-create-btn" @click="openCreateAiModal">
                  <template #icon>
                    <svg class="icon-sm" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
                    </svg>
                  </template>
                  新建题库
                </a-button>
              </template>
              <template v-else>
                <a-select v-model:value="questionLimitMode" class="practice-sort-select">
                  <a-select-option value="10">最多 10 题</a-select-option>
                  <a-select-option value="20">最多 20 题</a-select-option>
                  <a-select-option value="50">最多 50 题</a-select-option>
                  <a-select-option value="all">题量不限</a-select-option>
                </a-select>
              </template>
            </div>
          </div>
        </div>

        <!-- 下半部：Tab与过滤栏 -->
        <div class="practice-header-bottom">
          <template v-if="isInstructor">
            <!-- 教官模式：无Tab，统计在下方practice-stats区域显示 -->
          </template>
          <template v-else>
            <!-- 学员模式：切换来源类型 -->
            <div class="practice-tabs">
              <button class="practice-tab" :class="{ active: activeSourceType === 'knowledge-point' }" @click="selectSourceType('knowledge-point')">按知识点</button>
              <button class="practice-tab" :class="{ active: activeSourceType === 'question-folder' }" @click="selectSourceType('question-folder')">按题库/科目</button>
            </div>
            <div class="practice-filter-row">
              <a-select v-model:value="selectedQuestionType" mode="multiple" placeholder="全部题型" allow-clear class="practice-filter-select">
                <a-select-option value="single">单选题</a-select-option>
                <a-select-option value="multi">多选题</a-select-option>
                <a-select-option value="judge">判断题</a-select-option>
              </a-select>
              <a-select v-model:value="selectedDifficulty" mode="multiple" placeholder="全部难度" allow-clear class="practice-filter-select">
                <a-select-option value="1">难度 1</a-select-option>
                <a-select-option value="2">难度 2</a-select-option>
                <a-select-option value="3">难度 3</a-select-option>
                <a-select-option value="4">难度 4</a-select-option>
                <a-select-option value="5">难度 5</a-select-option>
              </a-select>
              <a-select v-model:value="selectedPoliceTypeId" placeholder="全部警种" allow-clear class="practice-filter-select">
                <a-select-option v-for="item in policeTypes" :key="item.id" :value="String(item.id)">{{ item.name }}</a-select-option>
              </a-select>
              <a-select v-model:value="selectedCourseId" placeholder="全部课程" allow-clear class="practice-filter-select">
                <a-select-option v-for="item in courses" :key="item.id" :value="String(item.id)">{{ item.title }}</a-select-option>
              </a-select>
            </div>
          </template>
        </div>
      </header>

      <!-- 数据统计摘要 -->
      <div class="practice-stats" v-if="isInstructor">
        <span>共 <strong>{{ filteredInstructorFolders.length }}</strong> 个题库</span>
      </div>
      <div class="practice-stats" v-else>
        <span>共 <strong>{{ filteredSources.length }}</strong> 个{{ activeSourceType === 'knowledge-point' ? '知识点' : '题库' }}</span>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="practice-loading">
        <a-spin size="large" />
      </div>

      <!-- 空状态 -->
      <a-empty v-else-if="(isInstructor ? filteredInstructorFolders.length : filteredSources.length) === 0" :description="isInstructor ? '暂无题库，点击上方按钮新建' : '暂无符合条件的练习来源'" class="practice-empty" />

      <!-- 题库/练习数据列表 -->
      <div v-else class="practice-list">
        <!-- PC端列表头 -->
        <div class="practice-list-header">
          <div class="practice-list-col practice-list-col-main">{{ isInstructor ? '题库基本信息' : '练习来源' }}</div>
          <div class="practice-list-col practice-list-col-qty">题量</div>
          <div class="practice-list-col practice-list-col-info">{{ isInstructor ? '关联课程' : '难度/警种' }}</div>
          <div class="practice-list-col practice-list-col-status">{{ isInstructor ? '状态' : '描述' }}</div>
          <div class="practice-list-col practice-list-col-action">操作</div>
        </div>

        <!-- 教官模式列表行 -->
        <template v-if="isInstructor">
          <div
            v-for="(item, index) in filteredInstructorFolders"
            :key="item.id"
            class="practice-row"
            :style="{ '--row-accent': getCardAccent(index) }"
          >
            <div class="practice-row-accent" :style="{ background: getCardAccent(index) }"></div>

            <!-- 题库信息 -->
            <div class="practice-row-main">
              <h3 class="practice-row-title">{{ item.name }}</h3>
              <div class="practice-row-sub">
                <span class="practice-row-tag">题库</span>
                <span class="practice-row-category">{{ item.category || '默认分类' }}</span>
              </div>
            </div>

            <!-- 题量 -->
            <div class="practice-row-qty">
              <span class="practice-qty-value">{{ item.question_count || 0 }}</span>
              <span class="practice-qty-label">题</span>
            </div>

            <!-- 关联课程 -->
            <div class="practice-row-info">
              <span v-if="item.course_names?.length" class="practice-info-text">{{ item.course_names.join('、') }}</span>
              <span v-else-if="item.course_name" class="practice-info-text">{{ item.course_name }}</span>
              <span v-else class="practice-info-empty">未关联课程</span>
            </div>

            <!-- 状态 -->
            <div class="practice-row-status">
              <span class="practice-status-tag">{{ item.status || '未使用' }}</span>
            </div>

            <!-- 操作 -->
            <div class="practice-row-action">
              <a-button class="practice-action-btn" @click.stop="openQuestionDetailModal(item.id)">
                <template #icon><EyeOutlined /></template>
                查看题目
              </a-button>
              <a-button class="practice-action-btn" @click.stop="openEditFolderModal(item)">
                <template #icon><EditOutlined /></template>
                编辑
              </a-button>
            </div>
          </div>
        </template>

        <!-- 学员模式列表行 -->
        <template v-else>
          <div
            v-for="(item, index) in filteredSources"
            :key="item.id"
            class="practice-row"
            :style="{ '--row-accent': getCardAccent(index) }"
            @click="handleCardClick(item)"
          >
            <div class="practice-row-accent" :style="{ background: getCardAccent(index) }"></div>

            <!-- 练习来源信息 -->
            <div class="practice-row-main">
              <h3 class="practice-row-title">{{ item.name }}</h3>
              <div class="practice-row-sub">
                <span class="practice-row-tag">{{ activeSourceType === 'knowledge-point' ? '知识点' : '题库' }}</span>
                <span v-if="activeSourceType === 'question-folder' && item.category" class="practice-row-category">{{ item.category }}</span>
                <span v-if="activeSourceType === 'knowledge-point' && item.police_type_name" class="practice-row-category">{{ item.police_type_name }}</span>
              </div>
            </div>

            <!-- 题量 -->
            <div class="practice-row-qty">
              <span class="practice-qty-value">{{ item.question_count || 0 }}</span>
              <span class="practice-qty-label">题</span>
            </div>

            <!-- 难度/警种 -->
            <div class="practice-row-info">
              <span v-if="item.difficulty_avg" class="practice-info-text">
                <StarOutlined /> 平均难度 {{ item.difficulty_avg.toFixed(1) }}
              </span>
              <span v-else-if="item.police_type_name" class="practice-info-text">{{ item.police_type_name }}</span>
              <span v-else class="practice-info-empty">--</span>
            </div>

            <!-- 描述 -->
            <div class="practice-row-status">
              <span v-if="item.description" class="practice-desc-text">{{ item.description }}</span>
              <span v-else class="practice-info-empty">暂无描述</span>
            </div>

            <!-- 操作 -->
            <div class="practice-row-action">
              <a-button type="primary" class="practice-action-btn primary" @click.stop="startPractice(item)">
                开始练习
              </a-button>
            </div>
          </div>
        </template>
      </div>
    </div>

  <!-- 练习设置弹窗 -->
    <a-modal
      v-model:open="settingsVisible"
      :title="null"
      :footer="null"
      :width="420"
      centered
      class="settings-modal"
    >
      <div class="settings-panel">
        <div class="settings-header">
          <div class="settings-icon">
            <EditOutlined />
          </div>
          <div class="settings-title-area">
            <h3 class="settings-title">设置练习参数</h3>
            <p class="settings-subtitle">{{ selectedPracticeItem?.name }}</p>
          </div>
        </div>

        <div class="settings-form">
          <div class="settings-field">
            <label class="settings-label">题目数量</label>
            <a-select v-model:value="settingsForm.questionLimit" class="settings-select">
              <a-select-option value="10">最多 10 题</a-select-option>
              <a-select-option value="20">最多 20 题</a-select-option>
              <a-select-option value="50">最多 50 题</a-select-option>
              <a-select-option value="all">题量不限</a-select-option>
            </a-select>
          </div>

          <div class="settings-field">
            <label class="settings-label">题目类型</label>
            <a-select v-model:value="settingsForm.questionType" mode="multiple" placeholder="全部题型" allow-clear class="settings-select">
              <a-select-option value="single">单选题</a-select-option>
              <a-select-option value="multi">多选题</a-select-option>
              <a-select-option value="judge">判断题</a-select-option>
            </a-select>
          </div>

          <div class="settings-field">
            <label class="settings-label">题目难度</label>
            <a-select v-model:value="settingsForm.difficulty" mode="multiple" placeholder="全部难度" allow-clear class="settings-select">
              <a-select-option value="1">难度 1</a-select-option>
              <a-select-option value="2">难度 2</a-select-option>
              <a-select-option value="3">难度 3</a-select-option>
              <a-select-option value="4">难度 4</a-select-option>
              <a-select-option value="5">难度 5</a-select-option>
            </a-select>
          </div>
        </div>

        <div class="settings-actions">
          <button class="btn-cancel" @click="settingsVisible = false">返回</button>
          <button class="btn-confirm" @click="confirmStartPractice">开始练习</button>
        </div>
      </div>
    </a-modal>

    <!-- 确认保存弹窗 (AI题目确认) -->
    <a-modal
      v-model:open="aiConfirmModalVisible"
      title="确认保存题目"
      :footer="null"
      :width="900"
      centered
      class="ai-confirm-modal"
    >
      <div class="ai-confirm-form">
        <div class="confirm-header">
          <div class="confirm-task-info">
            <span class="confirm-label">任务名称：</span>
            <span class="confirm-value">{{ aiConfirmTaskName }}</span>
          </div>
          <div class="confirm-task-info">
            <span class="confirm-label">出题主题：</span>
            <span class="confirm-value">{{ aiConfirmTopic }}</span>
          </div>
        </div>

        <div class="confirm-questions">
          <div class="confirm-questions-header">
            <span class="confirm-questions-title">生成的题目（共 {{ editingQuestions.length }} 题）</span>
            <span class="confirm-questions-hint">可编辑后保存到个人题库</span>
          </div>
          <div class="confirm-questions-list">
            <div v-for="(q, idx) in editingQuestions" :key="idx" class="confirm-question-item">
              <div class="confirm-question-header">
                <div class="confirm-question-type">
                  <a-select v-model:value="q.type" style="width: 100px" size="small">
                    <a-select-option value="single">单选题</a-select-option>
                    <a-select-option value="multi">多选题</a-select-option>
                    <a-select-option value="judge">判断题</a-select-option>
                  </a-select>
                </div>
                <span class="confirm-question-num">第 {{ idx + 1 }} 题</span>
              </div>
              <div class="confirm-question-content">
                <a-textarea
                  v-model:value="q.content"
                  placeholder="请输入题目内容"
                  :rows="2"
                />
              </div>
              <div v-if="q.type !== 'judge'" class="confirm-question-options">
                <div v-for="(opt, optIdx) in q.options" :key="optIdx" class="confirm-option-row">
                  <span class="confirm-option-key">{{ opt.key }}.</span>
                  <a-input v-model:value="opt.text" placeholder="选项内容" style="flex: 1" />
                  <a-button type="text" danger size="small" @click="removeOption(q, Number(optIdx))">
                    <CloseOutlined />
                  </a-button>
                </div>
                <a-button v-if="q.options.length < 6" type="link" size="small" @click="addOption(q)">
                  <PlusOutlined /> 添加选项
                </a-button>
              </div>
              <div class="confirm-question-answer">
                <span class="answer-label">正确答案：</span>
                <template v-if="q.type === 'judge'">
                  <a-radio-group v-model:value="q.answer">
                    <a-radio value="A">正确</a-radio>
                    <a-radio value="B">错误</a-radio>
                  </a-radio-group>
                </template>
                <template v-else-if="q.type === 'multi'">
                  <a-checkbox-group v-model:value="q.answer">
                    <a-checkbox v-for="opt in q.options" :key="opt.key" :value="opt.key">{{ opt.key }}</a-checkbox>
                  </a-checkbox-group>
                </template>
                <template v-else>
                  <a-radio-group v-model:value="q.answer">
                    <a-radio v-for="opt in q.options" :key="opt.key" :value="opt.key">{{ opt.key }}</a-radio>
                  </a-radio-group>
                </template>
              </div>
              <div class="confirm-question-explanation">
                <span class="explanation-label">解析：</span>
                <a-textarea v-model:value="q.explanation" placeholder="请输入答案解析（可选）" :rows="2" />
              </div>
            </div>
          </div>
        </div>

        <div class="confirm-actions">
          <a-space>
            <a-button @click="aiConfirmModalVisible = false">取消</a-button>
            <a-button @click="handleSaveEditedQuestions">保存修改</a-button>
          </a-space>
          <a-button type="primary" :loading="aiConfirmSaving" @click="handleConfirmSaveQuestions">
            确认保存到题库
          </a-button>
        </div>
      </div>
    </a-modal>

    <!-- 新建题库弹窗 (AI智能出题) -->
    <a-modal
      v-model:open="aiCreateModalVisible"
      title="新建题库"
      :footer="null"
      :width="800"
      centered
    >
      <div class="ai-create-form">
        <!-- Tab 切换 -->
        <div class="modal-tabs">
          <div
            class="modal-tab"
            :class="{ active: aiModalTab === 'create' }"
            @click="switchAiModalTab('create')"
          >
            创建任务
          </div>
          <div
            class="modal-tab"
            :class="{ active: aiModalTab === 'list' }"
            @click="switchAiModalTab('list')"
          >
            任务列表
          </div>
        </div>

        <!-- 创建任务表单 -->
        <div v-show="aiModalTab === 'create'" class="tab-content">
          <div class="form-row">
            <div class="form-field">
              <label class="field-label">任务名称</label>
              <a-input v-model:value="aiForm.taskName" placeholder="自动生成" />
            </div>
            <div class="form-field">
              <label class="field-label required">题库名称 / 出题主题</label>
              <a-input
                v-model:value="aiForm.topic"
                placeholder="如：刑事诉讼法"
                @blur="syncTopicToTaskName"
              />
            </div>
            <div class="form-field">
              <label class="field-label">关联课程</label>
              <a-select
                v-model:value="aiForm.courseIds"
                allow-clear
                show-search
                mode="multiple"
                placeholder="选择关联课程（可多选）"
                style="width: 100%"
              >
                <a-select-option v-for="item in courses" :key="item.id" :value="item.id">
                  {{ item.title }}
                </a-select-option>
              </a-select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-field">
              <label class="field-label">题目数量</label>
              <a-input-number v-model:value="aiForm.questionCount" :min="1" :max="50" style="width: 100%" />
            </div>
            <div class="form-field">
              <label class="field-label">题型</label>
              <a-select v-model:value="aiForm.questionTypes[0]" style="width: 100%">
                <a-select-option value="single">单选题</a-select-option>
                <a-select-option value="multi">多选题</a-select-option>
                <a-select-option value="judge">判断题</a-select-option>
              </a-select>
            </div>
            <div class="form-field">
              <label class="field-label">难度</label>
              <a-select v-model:value="aiForm.difficulty" style="width: 100%">
                <a-select-option v-for="level in [1,2,3,4,5]" :key="level" :value="level">{{ level }}级</a-select-option>
              </a-select>
            </div>
          </div>
          <div class="form-field">
            <label class="field-label">上传材料</label>
            <input
              ref="fileInputRef"
              type="file"
              class="hidden-file-input"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt"
              @change="handleSourceFileChange"
            />
            <a-button :loading="parsingFile" @click="triggerSourceFileSelect" class="upload-btn">
              <template #icon><FileTextOutlined /></template>
              添加附件
            </a-button>
            <div v-if="aiForm.sourceMaterials.length > 0" class="file-list">
              <div v-for="(file, index) in aiForm.sourceMaterials" :key="index" class="file-item">
                <FileTextOutlined class="file-icon" />
                <span class="file-name">{{ file.name }}</span>
                <span class="file-size">{{ formatFileSize(file.size) }}</span>
                <a-button type="text" danger size="small" @click="removeSourceFile(index)">
                  <template #icon><CloseOutlined /></template>
                </a-button>
              </div>
            </div>
            <div v-else class="file-list-empty">
              支持 PDF、Word、Excel、CSV、TXT 格式
            </div>
          </div>
          <div class="form-field">
            <label class="field-label">参考文本 <span class="field-hint">（上传文件后自动填充）</span></label>
            <a-textarea
              v-model:value="aiForm.sourceText"
              placeholder="粘贴相关法律条文、教材段落，或上传材料自动提取..."
              :rows="3"
            />
          </div>
          <div class="form-field">
            <label class="field-label">补充要求</label>
            <a-textarea
              v-model:value="aiForm.requirements"
              placeholder="如：侧重实战程序，选项需具有迷惑性..."
              :rows="2"
            />
          </div>
          <div class="form-actions">
            <a-button @click="aiCreateModalVisible = false">取消</a-button>
            <a-button type="primary" :loading="aiFormCreating" @click="handleCreateAiTask">创建任务</a-button>
          </div>
        </div>

        <!-- 任务列表 -->
        <div v-show="aiModalTab === 'list'" class="tab-content">
          <div class="task-list-header">
            <span class="task-list-title">任务列表</span>
            <a-button type="link" size="small" @click="loadAiTasks">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </div>
          <a-table
            :dataSource="aiTasks"
            :columns="aiTaskColumns"
            :loading="aiTasksLoading"
            :pagination="{ pageSize: 5 }"
            row-key="id"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="getAiTaskStatusColor(record.status)">
                  {{ getAiTaskStatusText(record.status) }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'action'">
                <a-button type="link" size="small" @click="viewAiTaskDetail(record)">
                  查看
                </a-button>
              </template>
            </template>
          </a-table>
        </div>

        <!-- 任务详情 -->
        <div v-show="aiModalTab === 'detail'" class="tab-content">
          <div class="task-detail-header">
            <a-button type="link" size="small" @click="switchAiModalTab('list')">
              <template #icon><LeftOutlined /></template>
              返回列表
            </a-button>
            <a-button
              v-if="aiTaskDetail?.status === 'completed' && aiTaskDetail?.questions?.length > 0"
              type="primary"
              size="small"
              @click="openAiConfirmModal"
            >
              <template #icon><CheckOutlined /></template>
              确认保存到题库
            </a-button>
          </div>
          <a-spin :spinning="aiTaskDetailLoading">
            <div v-if="aiTaskDetail" class="task-detail-content">
              <div class="detail-info">
                <div class="detail-row">
                  <span class="detail-label">任务名称：</span>
                  <span class="detail-value">{{ aiTaskDetail.task_name }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">出题主题：</span>
                  <span class="detail-value">{{ aiTaskDetail.request_payload?.topic || '-' }}</span>
                </div>
                <div class="detail-row">
                  <span class="detail-label">状态：</span>
                  <a-tag :color="getAiTaskStatusColor(aiTaskDetail.status)">
                    {{ getAiTaskStatusText(aiTaskDetail.status) }}
                  </a-tag>
                </div>
                <div class="detail-row">
                  <span class="detail-label">题目数量：</span>
                  <span class="detail-value">{{ aiTaskDetail.item_count || 0 }}</span>
                </div>
                <div v-if="aiTaskDetail.error_message" class="detail-row">
                  <span class="detail-label">错误信息：</span>
                  <span class="detail-value error">{{ aiTaskDetail.error_message }}</span>
                </div>
              </div>

              <!-- 题目列表 -->
              <div v-if="aiTaskDetail.questions?.length > 0" class="questions-section">
                <div class="section-title">生成的题目</div>
                <div v-for="(q, idx) in aiTaskDetail.questions" :key="idx" class="question-item">
                  <div class="question-type-tag">
                    {{ q.type === 'single' ? '单选题' : q.type === 'multi' ? '多选题' : '判断题' }}
                  </div>
                  <div class="question-content">{{ Number(idx) + 1 }}. {{ q.content }}</div>
                  <div class="question-options" v-if="q.options?.length">
                    <div v-for="opt in q.options" :key="opt.key" class="option-item">
                      {{ opt.key }}. {{ opt.text }}
                    </div>
                  </div>
                  <div class="question-answer">
                    <strong>答案：</strong>{{ Array.isArray(q.answer) ? q.answer.join(', ') : q.answer }}
                  </div>
                  <div v-if="q.explanation" class="question-explanation">
                    <strong>解析：</strong>{{ q.explanation }}
                  </div>
                </div>
              </div>
              <div v-else-if="!aiTaskDetailLoading" class="no-questions">
                <a-empty description="暂无生成的题目" />
              </div>
            </div>
          </a-spin>
        </div>
      </div>
    </a-modal>

    <!-- 编辑题库弹窗 -->
    <a-modal
      v-model:open="editFolderModalVisible"
      title="编辑题库"
      :footer="null"
      :width="420"
      centered
    >
      <div class="edit-folder-form">
        <div class="form-field">
          <label class="field-label required">题库名称</label>
          <a-input v-model:value="editFolderForm.name" placeholder="请输入题库名称" />
        </div>
        <div class="form-field">
          <label class="field-label">关联课程</label>
          <a-select
            v-model:value="editFolderForm.courseIds"
            allow-clear
            show-search
            mode="multiple"
            placeholder="选择关联课程（可多选）"
            style="width: 100%"
          >
            <a-select-option v-for="item in courses" :key="item.id" :value="item.id">
              {{ item.title }}
            </a-select-option>
          </a-select>
        </div>
        <div class="form-actions">
          <a-button @click="editFolderModalVisible = false">取消</a-button>
          <a-button type="primary" :loading="editFolderSaving" @click="handleUpdateFolder">保存</a-button>
        </div>
      </div>
    </a-modal>

    <!-- 题目详情弹窗 -->
    <a-modal
      v-model:open="questionDetailModalVisible"
      title="题目详情"
      :footer="null"
      :width="1400"
      centered
      class="question-detail-modal"
    >
      <div class="question-detail-content">
        <a-table
          :dataSource="folderQuestions"
          :columns="questionDetailColumns"
          :pagination="{ pageSize: 10 }"
          row-key="id"
          size="middle"
          :scroll="{ x: 500, y: 450 }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'index'">
              {{ folderQuestions.indexOf(record) + 1 }}
            </template>
            <template v-else-if="column.key === 'type'">
              <a-tag :color="record.type === 'single' ? 'blue' : record.type === 'multi' ? 'purple' : 'orange'">
                {{ record.type === 'single' ? '单选' : record.type === 'multi' ? '多选' : '判断' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'content'">
              <div class="table-question-content">{{ record.content }}</div>
            </template>
            <template v-else-if="column.key === 'options'">
              <div v-if="record.options?.length" class="table-question-options">
                <div v-for="opt in record.options" :key="opt.key" class="table-option-item">
                  <span class="option-key">{{ opt.key }}.</span>
                  <span>{{ opt.text || opt.value }}</span>
                </div>
              </div>
              <span v-else>-</span>
            </template>
            <template v-else-if="column.key === 'answer'">
              <a-tag v-if="record.type === 'judge'" :color="record.answer === 'A' ? 'green' : 'red'">
                {{ record.answer === 'A' ? '正确' : '错误' }}
              </a-tag>
              <template v-else>
                <a-tag v-for="ans in (Array.isArray(record.answer) ? record.answer : [record.answer])" :key="ans" color="green">{{ ans }}</a-tag>
              </template>
            </template>
            <template v-else-if="column.key === 'explanation'">
              <span class="explanation-text">{{ record.explanation || '-' }}</span>
            </template>
            <template v-else-if="column.key === 'difficulty'">
              <a-rate :value="record.difficulty" disabled :count="5" />
            </template>
            <template v-else-if="column.key === 'action'">
              <a-space>
                <a-button type="link" size="small" @click="openQuestionEditModal(record)">
                  <template #icon><EditOutlined /></template>
                  编辑
                </a-button>
                <a-popconfirm
                  title="确定要删除这道题目吗？"
                  ok-text="确定"
                  cancel-text="取消"
                  @confirm="handleDeleteQuestion(record.id)"
                >
                  <a-button type="link" danger size="small">
                    <template #icon><DeleteOutlined /></template>
                    删除
                  </a-button>
                </a-popconfirm>
              </a-space>
            </template>
          </template>
        </a-table>
      </div>
    </a-modal>

    <!-- 编辑题目弹窗 -->
    <a-modal
      v-model:open="questionEditModalVisible"
      title="编辑题目"
      :footer="null"
      :width="700"
      centered
      class="question-edit-modal"
    >
      <div v-if="editQuestionForm.id" class="question-edit-form">
        <div class="form-row">
          <div class="form-field">
            <label class="field-label required">题型</label>
            <a-select v-model:value="editQuestionForm.type" style="width: 100%">
              <a-select-option value="single">单选题</a-select-option>
              <a-select-option value="multi">多选题</a-select-option>
              <a-select-option value="judge">判断题</a-select-option>
            </a-select>
          </div>
          <div class="form-field">
            <label class="field-label">难度</label>
            <a-select v-model:value="editQuestionForm.difficulty" style="width: 100%">
              <a-select-option v-for="level in [1,2,3,4,5]" :key="level" :value="level">{{ level }}级</a-select-option>
            </a-select>
          </div>
        </div>
        <div class="form-field">
          <label class="field-label required">题目内容</label>
          <a-textarea v-model:value="editQuestionForm.content" placeholder="请输入题目内容" :rows="3" />
        </div>
        <div v-if="editQuestionForm.type !== 'judge'" class="form-field">
          <label class="field-label required">选项</label>
          <div class="options-edit-list">
            <div v-for="(opt, idx) in editQuestionForm.options" :key="idx" class="option-edit-row">
              <span class="option-edit-key">{{ opt.key }}.</span>
              <a-input v-model:value="opt.text" placeholder="选项内容" style="flex: 1" />
              <a-button type="text" danger size="small" @click="removeEditOption(idx)" :disabled="editQuestionForm.options.length <= 2">
                <CloseOutlined />
              </a-button>
            </div>
            <a-button v-if="editQuestionForm.options.length < 6" type="link" size="small" @click="addEditOption">
              <PlusOutlined /> 添加选项
            </a-button>
          </div>
        </div>
        <div class="form-field">
          <label class="field-label required">正确答案</label>
          <div class="answer-edit-section">
            <template v-if="editQuestionForm.type === 'judge'">
              <a-radio-group v-model:value="editQuestionForm.answer">
                <a-radio value="A">正确</a-radio>
                <a-radio value="B">错误</a-radio>
              </a-radio-group>
            </template>
            <template v-else-if="editQuestionForm.type === 'multi'">
              <a-checkbox-group v-model:value="editQuestionForm.answer">
                <a-checkbox v-for="opt in editQuestionForm.options" :key="opt.key" :value="opt.key">{{ opt.key }}</a-checkbox>
              </a-checkbox-group>
            </template>
            <template v-else>
              <a-radio-group v-model:value="editQuestionForm.answer">
                <a-radio v-for="opt in editQuestionForm.options" :key="opt.key" :value="opt.key">{{ opt.key }}</a-radio>
              </a-radio-group>
            </template>
          </div>
        </div>
        <div class="form-field">
          <label class="field-label">答案解析</label>
          <a-textarea v-model:value="editQuestionForm.explanation" placeholder="请输入答案解析（可选）" :rows="2" />
        </div>
        <div class="form-actions">
          <a-button @click="questionEditModalVisible = false">取消</a-button>
          <a-button type="primary" :loading="editQuestionSaving" @click="handleUpdateQuestion">保存</a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import {
  EditOutlined,
  FolderOutlined,
  NodeIndexOutlined,
  PlusOutlined,
  QuestionCircleOutlined,
  StarOutlined,
  CloseOutlined,
  FileTextOutlined,
  ReloadOutlined,
  LeftOutlined,
  CheckOutlined,
  EyeOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import axios from 'axios'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getPracticeSources } from '@/api/practice'
import { listCourses } from '@/api/learning-resource'
import { getQuestionFoldersApiV1QuestionsFoldersGet, getQuestionsApiV1QuestionsGet, updateQuestionFolderApiV1QuestionsFoldersFolderIdPut, updateQuestionApiV1QuestionsQuestionIdPut, deleteQuestionApiV1QuestionsQuestionIdDelete } from '@/api/generated/question-management/question-management'
import { getAiQuestionTasks, getAiQuestionTaskDetail, createAiQuestionTask, updateAiQuestionTaskResult, confirmAiQuestionTask } from '@/api/ai'
import type { PoliceTypeSimpleResponse } from '@/api/generated/model'
import type { CourseListResponse } from '@/api/generated/model'
import type { QuestionResponse } from '@/api/generated/model'
import { useAuthStore } from '@/stores/auth'
import DarkPageHeader from '@/components/common/DarkPageHeader.vue'

const router = useRouter()
const authStore = useAuthStore()

// ============ 角色判断 ============
const isInstructor = computed(() => authStore.isInstructor || authStore.role === 'instructor')
const isStudent = computed(() => authStore.isStudent || authStore.role === 'student')
const avatarText = computed(() => {
  const user = authStore.currentUser
  const name = user?.nickname || user?.name || user?.username || ''
  return name.charAt(0).toUpperCase()
})

// ============ 通用状态 ============
const loading = ref(false)
const searchKeyword = ref('')

// ============ 学员模式状态 ============
const activeSourceType = ref('knowledge-point')
const questionLimitMode = ref('20')
const selectedQuestionType = ref<string[]>([])
const selectedDifficulty = ref<string[]>([])
const selectedPoliceTypeId = ref(undefined)
const selectedCourseId = ref<string | undefined>(undefined)

const knowledgePoints = ref<any[]>([])
const practiceQuestionFolders = ref<any[]>([])
const policeTypes = ref<PoliceTypeSimpleResponse[]>([])
const courses = ref<CourseListResponse[]>([])

// ============ 教官模式状态 ============
const instructorFolders = ref<any[]>([])
const instructorCourseId = ref<number | undefined>(undefined)
const expandedFolderId = ref<number | null>(null)
const folderQuestions = ref<QuestionResponse[]>([])
const folderQuestionsLoading = ref(false)

// ============ 弹窗状态 ============
const settingsVisible = ref(false)
const selectedPracticeItem = ref<any>(null)
const aiCreateModalVisible = ref(false)
const editFolderModalVisible = ref(false)
const viewingFolderQuestions = ref<any>(null)
const questionDetailModalVisible = ref(false)
const questionEditModalVisible = ref(false)
const currentQuestion = ref<any>(null)
const editQuestionSaving = ref(false)

// ============ AI 创建题库表单 ============
const aiForm = reactive({
  taskName: '',
  topic: '',
  targetBankName: '',
  courseIds: [] as number[],
  sourceText: '',
  sourceMaterials: [] as { name: string; size: number; type: string }[],
  knowledgePoints: [] as string[],
  questionCount: 10,
  questionTypes: ['single'] as string[],
  difficulty: 3,
  policeTypeId: undefined as number | undefined,
  score: 2,
  requirements: '',
})
const aiFormCreating = ref(false)
const aiTasks = ref<any[]>([])
const aiTasksLoading = ref(false)
const aiTaskDetail = ref<any>(null)
const aiTaskDetailLoading = ref(false)
const aiModalTab = ref('create')
const aiConfirmModalVisible = ref(false)
const aiConfirmSaving = ref(false)
const editingQuestions = ref<any[]>([])
const aiConfirmTaskName = ref('')
const aiConfirmTopic = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)
const parsingFile = ref(false)

const aiTaskColumns = [
  { title: '任务名称', dataIndex: 'task_name', key: 'task_name' },
  { title: '出题主题', dataIndex: 'task_name', key: 'topic' },
  { title: '题目数量', dataIndex: 'item_count', key: 'item_count' },
  { title: '状态', key: 'status' },
  { title: '创建时间', dataIndex: 'created_at', key: 'created_at' },
  { title: '操作', key: 'action', width: 80 },
]

const questionDetailColumns = [
  { title: '序号', key: 'index', width: 60 },
  { title: '题型', key: 'type', width: 80 },
  { title: '题目内容', key: 'content', width: 300 },
  { title: '选项', key: 'options', width: 280 },
  { title: '答案', key: 'answer', width: 80 },
  { title: '解析', key: 'explanation', width: 180 },
  { title: '难度', key: 'difficulty', width: 100 },
  { title: '操作', key: 'action', width: 100 },
]

// ============ 编辑题库表单 ============
const editFolderForm = reactive({
  id: 0,
  name: '',
  courseIds: [] as number[],
})
const editFolderSaving = ref(false)

// ============ 编辑题目表单 ============
const editQuestionForm = reactive({
  id: 0,
  type: 'single',
  content: '',
  options: [] as { key: string; text: string }[],
  answer: '' as string | string[],
  explanation: '',
  difficulty: 3,
})

// ============ 学员模式表单 ============
const settingsForm = reactive({
  questionLimit: '20',
  questionType: [] as string[],
  difficulty: [] as string[],
})

const coverGradients = [
  'linear-gradient(135deg, #edf1fb 0%, #e4eaf5 100%)',
  'linear-gradient(135deg, #edf3ee 0%, #e1eae3 100%)',
  'linear-gradient(135deg, #f6eee7 0%, #eee2d7 100%)',
  'linear-gradient(135deg, #edf4f3 0%, #e2ece9 100%)',
  'linear-gradient(135deg, #f3ede7 0%, #e8dfd6 100%)',
]

const cardAccents = [
  '#4B6EF5',
  '#34C759',
  '#FF9500',
  '#5856D6',
  '#FF2D55',
]

function getCardAccent(index: number) {
  return cardAccents[index % cardAccents.length]
}

function getCardCoverBackground(index: number) {
  return coverGradients[index % coverGradients.length]
}

const currentSources = computed(() => (
  activeSourceType.value === 'knowledge-point' ? knowledgePoints.value : practiceQuestionFolders.value
))

const filteredSources = computed(() => {
  let items = currentSources.value

  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.trim().toLowerCase()
    items = items.filter((item) =>
      (item.name || '').toLowerCase().includes(keyword),
    )
  }

  return items
})

const selectedPoliceTypeName = computed(() =>
  policeTypes.value.find((item) => String(item.id) === String(selectedPoliceTypeId.value))?.name || ''
)

// ============ 教官模式计算属性 ============
const filteredInstructorFolders = computed(() => {
  let folders = instructorFolders.value
  if (instructorCourseId.value) {
    folders = folders.filter((f: any) => f.course_id === instructorCourseId.value)
  }
  if (searchKeyword.value.trim()) {
    const keyword = searchKeyword.value.trim().toLowerCase()
    folders = folders.filter((f: any) => (f.name || '').toLowerCase().includes(keyword))
  }
  return folders
})

// ============ 教官模式方法 ============
async function loadInstructorFolders() {
  loading.value = true
  try {
    const res = await getQuestionFoldersApiV1QuestionsFoldersGet()
    const folders = (res as any)?.data ?? res
    instructorFolders.value = Array.isArray(folders) ? folders : []
  } catch (error) {
    message.error('加载题库失败')
  } finally {
    loading.value = false
  }
}

async function loadCourses() {
  try {
    const res = await listCourses({ page: 1, size: -1 })
    courses.value = res?.items || []
  } catch (error) {
    console.error('加载课程失败', error)
  }
}

async function toggleFolderExpand(folderId: number) {
  if (expandedFolderId.value === folderId) {
    expandedFolderId.value = null
    folderQuestions.value = []
    return
  }
  expandedFolderId.value = folderId
  folderQuestionsLoading.value = true
  try {
    const res = await getQuestionsApiV1QuestionsGet({ folder_id: folderId, size: -1 })
    folderQuestions.value = (res as any)?.data?.items || res?.items || []
  } catch (error) {
    message.error('加载题目失败')
    folderQuestions.value = []
  } finally {
    folderQuestionsLoading.value = false
  }
}

function openAiTaskListModal() {
  aiModalTab.value = 'list'
  loadAiTasks()
  aiCreateModalVisible.value = true
}

function openCreateAiModal() {
  // 重置表单
  aiForm.taskName = ''
  aiForm.topic = ''
  aiForm.courseIds = []
  aiForm.sourceText = ''
  aiForm.sourceMaterials = []
  aiForm.knowledgePoints = []
  aiForm.questionCount = 10
  aiForm.questionTypes = ['single']
  aiForm.difficulty = 3
  aiForm.policeTypeId = undefined
  aiForm.score = 2
  aiForm.requirements = ''
  aiModalTab.value = 'create'
  aiCreateModalVisible.value = true
}

function syncTopicToTaskName() {
  // 自动生成任务名称：题库名称 + 日期
  if (!aiForm.taskName.trim() && aiForm.topic.trim()) {
    const now = new Date()
    const date = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`
    aiForm.taskName = `${aiForm.topic}-${date}`
  }
}

function triggerSourceFileSelect() {
  fileInputRef.value?.click()
}

function formatFileSize(size: number): string {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / (1024 * 1024)).toFixed(1) + ' MB'
}

function removeSourceFile(index: number) {
  aiForm.sourceMaterials.splice(index, 1)
}

async function handleSourceFileChange(event: Event) {
  const file = (event.target as HTMLInputElement)?.files?.[0]
  if (!file) return

  parsingFile.value = true
  try {
    // 直接使用 axios 上传，设置 120 秒超时
    const formData = new FormData()
    formData.append('file', file)

    const token = localStorage.getItem('token')
    const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
    const response = await axios.post(`${baseURL}/ai/files/parse`, formData, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 120 秒超时
    })

    const result = response.data
    // 将文件添加到列表
    aiForm.sourceMaterials.push({
      name: file.name,
      size: file.size,
      type: file.type || '',
    })
    // 如果是第一个文件，提取文本内容
    if (aiForm.sourceMaterials.length === 1) {
      aiForm.sourceText = result?.data?.text || ''
    } else {
      // 多个文件时追加文本
      const additionalText = result?.data?.text || ''
      if (additionalText) {
        aiForm.sourceText = aiForm.sourceText ? aiForm.sourceText + '\n\n' + additionalText : additionalText
      }
    }
    message.success(`已添加文件：${file.name}`)
  } catch (error: any) {
    message.error(error?.message || '材料解析失败')
  } finally {
    parsingFile.value = false
    if (event.target) {
      (event.target as HTMLInputElement).value = ''
    }
  }
}

async function handleCreateAiTask() {
  if (!aiForm.topic.trim()) {
    message.warning('请填写出题主题')
    return
  }
  aiFormCreating.value = true
  try {
    const taskName = aiForm.taskName.trim() || `${aiForm.topic} - ${new Date().toLocaleString()}`
    const sourceMaterialName = aiForm.sourceMaterials.length > 0
      ? aiForm.sourceMaterials.map((f: any) => f.name).join(', ')
      : undefined

    await createAiQuestionTask({
      task_name: taskName,
      topic: aiForm.topic,
      source_text: aiForm.sourceText || undefined,
      knowledge_points: [...aiForm.knowledgePoints],
      question_count: aiForm.questionCount,
      question_types: [...aiForm.questionTypes],
      difficulty: aiForm.difficulty,
      police_type_id: aiForm.policeTypeId || undefined,
      score: aiForm.score,
      requirements: aiForm.requirements || undefined,
      target_bank_name: aiForm.topic,
      course_id: aiForm.courseIds[0] || undefined,
      source_material_name: sourceMaterialName,
    })
    message.success('创建成功，请稍后查看生成结果')
    aiCreateModalVisible.value = false
    await loadAiTasks()
  } catch (error: any) {
    message.error(error?.message || '创建失败')
  } finally {
    aiFormCreating.value = false
  }
}

async function loadAiTasks() {
  aiTasksLoading.value = true
  try {
    const res = await getAiQuestionTasks({ size: -1 })
    console.log('任务列表响应:', res)
    // custom-instance 返回的是 axios 响应对象，解包后 data 是 { page, size, total, items }
    aiTasks.value = res?.data?.items || res?.items || []
  } catch (error) {
    console.error('加载任务列表失败', error)
  } finally {
    aiTasksLoading.value = false
  }
}

function getAiTaskStatusColor(status: string) {
  const colors: Record<string, string> = {
    pending: 'default',
    processing: 'processing',
    completed: 'blue',
    confirmed: 'green',
    failed: 'red',
  }
  return colors[status] || 'default'
}

function getAiTaskStatusText(status: string) {
  const labels: Record<string, string> = {
    pending: '排队中',
    processing: '处理中',
    completed: '已完成',
    confirmed: '已确认',
    failed: '失败',
  }
  return labels[status] || status
}

function viewAiTaskDetail(record: any) {
  aiModalTab.value = 'detail'
  aiTaskDetailLoading.value = true
  aiTaskDetail.value = null
  getAiQuestionTaskDetail(record.id)
    .then((res: any) => {
      console.log('任务详情响应:', res)
      aiTaskDetail.value = res?.data || res || null
    })
    .catch((err: any) => {
      message.error('加载任务详情失败')
      console.error(err)
    })
    .finally(() => {
      aiTaskDetailLoading.value = false
    })
}

function switchAiModalTab(tab: 'create' | 'list' | 'detail') {
  aiModalTab.value = tab
  if (tab === 'list') {
    loadAiTasks()
  } else if (tab === 'create') {
    // 切换到创建表单时刷新题库列表
    loadInstructorFolders()
  } else if (tab === 'detail') {
    aiTaskDetail.value = null
  }
}

function openAiConfirmModal() {
  if (!aiTaskDetail.value) return
  // 复制题目数据用于编辑
  aiConfirmTaskName.value = aiTaskDetail.value.task_name || ''
  aiConfirmTopic.value = aiTaskDetail.value.request_payload?.topic || ''
  editingQuestions.value = (aiTaskDetail.value.questions || []).map((q: any) => {
    // 标准化题目数据
    let normalizedAnswer: any = q.answer
    if (q.type === 'multi' && !Array.isArray(q.answer)) {
      normalizedAnswer = q.answer ? [q.answer] : []
    }
    return {
      ...q,
      answer: normalizedAnswer,
      options: (q.options || []).map((opt: any) => ({
        key: opt.key || opt.text?.charAt(0) || 'A',
        text: opt.text || opt.value || '',
      })),
    }
  })
  aiConfirmModalVisible.value = true
}

function addOption(question: any) {
  const keys = ['A', 'B', 'C', 'D', 'E', 'F']
  const usedKeys = question.options.map((o: any) => o.key)
  const nextKey = keys.find(k => !usedKeys.includes(k)) || 'A'
  question.options.push({ key: nextKey, text: '' })
}

function removeOption(question: any, index: number) {
  if (question.options.length <= 2) {
    message.warning('至少需要保留两个选项')
    return
  }
  question.options.splice(index, 1)
}

function handleSaveEditedQuestions() {
  if (!aiTaskDetail.value) return
  // 保存修改到任务结果
  aiConfirmSaving.value = true
  const updatedQuestions = editingQuestions.value.map((q, idx) => {
    let answer = q.answer
    if (q.type === 'multi' && Array.isArray(answer)) {
      answer = answer.join(',')
    }
    return {
      temp_id: q.temp_id || `temp_${idx}_${Date.now()}`,
      type: q.type,
      content: q.content,
      options: q.options.map((opt: any) => ({ key: opt.key, text: opt.text })),
      answer: String(answer || ''),
      explanation: q.explanation || '',
    }
  })
  updateAiQuestionTaskResult(aiTaskDetail.value.id, { questions: updatedQuestions })
    .then(() => {
      message.success('保存修改成功')
      aiConfirmModalVisible.value = false
      // 刷新任务详情
      return getAiQuestionTaskDetail(aiTaskDetail.value.id).then((res: any) => {
        aiTaskDetail.value = res?.data || res || null
      })
    })
    .catch((err: any) => {
      message.error(err?.message || '保存失败')
    })
    .finally(() => {
      aiConfirmSaving.value = false
    })
}

function handleConfirmSaveQuestions() {
  if (!aiTaskDetail.value) return
  // 先验证题目
  for (let i = 0; i < editingQuestions.value.length; i++) {
    const q = editingQuestions.value[i]
    if (!q.content?.trim()) {
      message.warning(`第 ${i + 1} 题题目内容不能为空`)
      return
    }
    if (q.type !== 'judge') {
      for (const opt of q.options) {
        if (!opt.text?.trim()) {
          message.warning(`第 ${i + 1} 题选项内容不能为空`)
          return
        }
      }
    }
    if (!q.answer) {
      message.warning(`第 ${i + 1} 题正确答案不能为空`)
      return
    }
  }
  aiConfirmSaving.value = true
  // 先保存编辑的题目
  const updatedQuestions = editingQuestions.value.map((q, idx) => {
    let answer = q.answer
    if (q.type === 'multi' && Array.isArray(answer)) {
      answer = answer.join(',')
    }
    return {
      temp_id: q.temp_id || `temp_${idx}_${Date.now()}`,
      type: q.type,
      content: q.content,
      options: q.options.map((opt: any) => ({ key: opt.key, text: opt.text })),
      answer: String(answer || ''),
      explanation: q.explanation || '',
    }
  })
  updateAiQuestionTaskResult(aiTaskDetail.value.id, { questions: updatedQuestions })
    .then((res) => {
      console.log('更新题目结果成功:', res)
      // 然后确认保存到题库
      return confirmAiQuestionTask(aiTaskDetail.value.id)
    })
    .then((res) => {
      console.log('确认保存到题库成功:', res)
      message.success('已确认保存到题库')
      aiConfirmModalVisible.value = false
      aiCreateModalVisible.value = false
      // 刷新题库列表
      loadInstructorFolders()
    })
    .catch((err: any) => {
      console.error('保存失败:', err)
      message.error(err?.message || '保存失败')
    })
    .finally(() => {
      aiConfirmSaving.value = false
    })
}

function openEditFolderModal(folder: any) {
  editFolderForm.id = folder.id
  editFolderForm.name = folder.name
  // 优先使用 course_ids 数组，兼容旧的 course_id
  editFolderForm.courseIds = folder.course_ids || (folder.course_id ? [folder.course_id] : [])
  editFolderModalVisible.value = true
}

async function handleUpdateFolder() {
  if (!editFolderForm.name.trim()) {
    message.warning('请填写题库名称')
    return
  }
  editFolderSaving.value = true
  try {
    await updateQuestionFolderApiV1QuestionsFoldersFolderIdPut(editFolderForm.id, {
      name: editFolderForm.name,
      course_ids: editFolderForm.courseIds.length > 0 ? editFolderForm.courseIds : undefined,
    } as any)
    message.success('更新成功')
    editFolderModalVisible.value = false
    await loadInstructorFolders()
  } catch (error: any) {
    message.error(error?.message || '更新失败')
  } finally {
    editFolderSaving.value = false
  }
}

// ============ 题目操作 ============
function openQuestionDetailModal(folderId?: number) {
  // 如果传入了 folderId，则加载对应题库题目
  if (folderId) {
    folderQuestionsLoading.value = true
    expandedFolderId.value = folderId
    getQuestionsApiV1QuestionsGet({ folder_id: folderId, size: -1 })
      .then((res: any) => {
        folderQuestions.value = res?.data?.items || res?.items || []
      })
      .catch(() => {
        folderQuestions.value = []
      })
      .finally(() => {
        folderQuestionsLoading.value = false
      })
  }
  questionDetailModalVisible.value = true
}

function openQuestionEditModal(question: any) {
  currentQuestion.value = question
  // 初始化编辑表单
  editQuestionForm.id = question.id
  editQuestionForm.type = question.type || 'single'
  editQuestionForm.content = question.content || ''
  editQuestionForm.explanation = question.explanation || ''
  editQuestionForm.difficulty = question.difficulty || 3

  // 处理选项
  if (question.options && Array.isArray(question.options)) {
    editQuestionForm.options = question.options.map((opt: any) => ({
      key: opt.key || 'A',
      text: opt.text || opt.value || '',
    }))
  } else {
    editQuestionForm.options = [
      { key: 'A', text: '' },
      { key: 'B', text: '' },
    ]
  }

  // 处理答案
  if (question.type === 'multi') {
    editQuestionForm.answer = Array.isArray(question.answer) ? question.answer : question.answer ? [question.answer] : []
  } else {
    editQuestionForm.answer = String(question.answer || 'A')
  }

  questionEditModalVisible.value = true
}

function openQuestionEditModalFromDetail() {
  questionDetailModalVisible.value = false
  openQuestionEditModal(currentQuestion.value)
}

function addEditOption() {
  const keys = ['A', 'B', 'C', 'D', 'E', 'F']
  const usedKeys = editQuestionForm.options.map(o => o.key)
  const nextKey = keys.find(k => !usedKeys.includes(k)) || 'A'
  editQuestionForm.options.push({ key: nextKey, text: '' })
}

function removeEditOption(index: number) {
  if (editQuestionForm.options.length <= 2) {
    message.warning('至少需要保留两个选项')
    return
  }
  editQuestionForm.options.splice(index, 1)
}

async function handleUpdateQuestion() {
  if (!editQuestionForm.content.trim()) {
    message.warning('题目内容不能为空')
    return
  }

  if (editQuestionForm.type !== 'judge') {
    for (const opt of editQuestionForm.options) {
      if (!opt.text?.trim()) {
        message.warning('选项内容不能为空')
        return
      }
    }
  }

  if (!editQuestionForm.answer) {
    message.warning('请选择正确答案')
    return
  }

  editQuestionSaving.value = true
  try {
    // 构建选项对象
    const options: { [key: string]: unknown } = {}
    editQuestionForm.options.forEach(opt => {
      options[opt.key] = opt.text
    })

    // 处理答案格式
    let answer = editQuestionForm.answer
    if (editQuestionForm.type === 'multi' && Array.isArray(answer)) {
      answer = answer.join(',')
    }

    await updateQuestionApiV1QuestionsQuestionIdPut(editQuestionForm.id, {
      type: editQuestionForm.type,
      content: editQuestionForm.content,
      options,
      answer,
      explanation: editQuestionForm.explanation || null,
      difficulty: editQuestionForm.difficulty,
    } as any)

    message.success('更新成功')
    questionEditModalVisible.value = false

    // 刷新题目列表
    if (expandedFolderId.value) {
      const res = await getQuestionsApiV1QuestionsGet({ folder_id: expandedFolderId.value, size: -1 })
      folderQuestions.value = (res as any)?.data?.items || res?.items || []
    }
  } catch (error: any) {
    message.error(error?.message || '更新失败')
  } finally {
    editQuestionSaving.value = false
  }
}

async function handleDeleteQuestion(questionId: number) {
  try {
    await deleteQuestionApiV1QuestionsQuestionIdDelete(questionId)
    message.success('删除成功')

    // 从列表中移除
    folderQuestions.value = folderQuestions.value.filter((q: any) => q.id !== questionId)

    // 刷新题库统计
    await loadInstructorFolders()
  } catch (error: any) {
    message.error(error?.message || '删除失败')
  }
}

function handleCourseSelectChange(value: number | undefined) {
  instructorCourseId.value = value
}

function normalizeQuestionCount(value: unknown) {
  return Number(value || 0)
}

function flattenFolderTree(folders: any[], depth = 0) {
  let flattened: any[] = []

  for (const folder of folders || []) {
    const questionCount = normalizeQuestionCount(folder.question_count ?? folder.questionCount)
    flattened.push({
      id: folder.id,
      name: folder.name,
      category: folder.category || '默认分类',
      question_count: questionCount,
      description: folder.description || '',
    })

    if (Array.isArray(folder.children) && folder.children.length > 0) {
      flattened = flattened.concat(flattenFolderTree(folder.children, depth + 1))
    }
  }

  return flattened
}

async function loadPracticeSources() {
  loading.value = true
  try {
    const sourceResponse = await getPracticeSources()

    const rawKps = sourceResponse?.knowledge_points || []
    knowledgePoints.value = rawKps
      .filter((item: any) => normalizeQuestionCount(item.question_count) > 0)
      .map((item: any) => ({
        ...item,
        police_type_name: item.police_type?.name || '',
        difficulty_avg: item.difficulty_avg || null,
      }))

    practiceQuestionFolders.value = flattenFolderTree(sourceResponse?.question_folders || []).filter(
      (item: any) => normalizeQuestionCount(item.question_count) > 0,
    )

    policeTypes.value = (sourceResponse?.police_types || []).filter((item: any) => item.is_active !== false)

    // 加载课程列表
    const courseResponse = await listCourses({ page: 1, size: -1 })
    courses.value = courseResponse?.items || []
  } catch (error) {
    message.error(error instanceof Error ? error.message : '加载练习来源失败')
  } finally {
    loading.value = false
  }
}

function selectSourceType(type: string) {
  if (activeSourceType.value === type) {
    return
  }
  activeSourceType.value = type
  searchKeyword.value = ''
}

function handleSearch() {
  // 搜索由 computed 属性自动处理
}

function handleCardClick(item: any) {
  startPractice(item)
}

function getResolvedQuestionLimit() {
  if (questionLimitMode.value === 'all') {
    return null
  }
  const parsed = Number(questionLimitMode.value)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 20
}

function getSelectedPoliceTypeName() {
  return policeTypes.value.find((item) => String(item.id) === String(selectedPoliceTypeId.value))?.name || ''
}

function getPracticeSettingsText() {
  const parts: string[] = []

  const limit = getResolvedQuestionLimit()
  if (limit) {
    parts.push(`题量：${limit} 题`)
  } else {
    parts.push('题量：不限')
  }

  const typeMap: Record<string, string> = { single: '单选题', multi: '多选题', judge: '判断题' }
  const selectedTypeLabels = selectedQuestionType.value
    .map((item) => typeMap[item])
    .filter(Boolean)
  if (selectedTypeLabels.length) {
    parts.push(`题型：${selectedTypeLabels.join(' / ')}`)
  } else {
    parts.push('题型：全部')
  }

  if (selectedDifficulty.value.length) {
    parts.push(`难度：${selectedDifficulty.value.join(' / ')}`)
  } else {
    parts.push('难度：全部')
  }

  if (selectedPoliceTypeId.value) {
    const policeName = getSelectedPoliceTypeName()
    if (policeName) parts.push(`警种：${policeName}`)
  }

  return parts.join(' · ')
}

function startPractice(item: any) {
  selectedPracticeItem.value = item
  settingsForm.questionLimit = questionLimitMode.value
  settingsForm.questionType = [...selectedQuestionType.value]
  settingsForm.difficulty = [...selectedDifficulty.value]
  settingsVisible.value = true
}

function getSettingsResolvedLimit() {
  if (settingsForm.questionLimit === 'all') return null
  const parsed = Number(settingsForm.questionLimit)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 20
}

function confirmStartPractice() {
  if (!selectedPracticeItem.value) return
  settingsVisible.value = false
  const questionTypes = settingsForm.questionType.filter(Boolean)
  const difficulties = settingsForm.difficulty.filter(Boolean)
  router.push({
    path: '/practice/do',
    query: {
      sourceType: activeSourceType.value,
      sourceId: String(selectedPracticeItem.value.id),
      sourceName: selectedPracticeItem.value.name,
      questionLimit: getSettingsResolvedLimit() ? String(getSettingsResolvedLimit()) : 'all',
      questionType: questionTypes.length ? questionTypes.join(',') : undefined,
      difficulty: difficulties.length ? difficulties.join(',') : undefined,
      policeTypeId: selectedPoliceTypeId.value || undefined,
      policeTypeName: getSelectedPoliceTypeName() || undefined,
      keyword: searchKeyword.value.trim() || undefined,
      courseId: selectedCourseId.value || undefined,
      courseName: getSelectedCourseName() || undefined,
    },
  })
}

function getSelectedCourseName() {
  return courses.value.find((item) => String(item.id) === String(selectedCourseId.value))?.title || ''
}

onMounted(() => {
  if (isInstructor.value) {
    loadInstructorFolders()
    loadCourses()
  } else {
    loadPracticeSources()
  }
})
</script>

<style scoped>
/* ── dark select overrides (actions + extra) ── */
.dark-sort-select { width: 140px; }
.dark-course-select { width: 180px; }
.dark-adv-row { display: flex; flex-wrap: wrap; gap: 10px; }
.dark-adv-select { width: 150px; }

:deep(.dark-sort-select .ant-select-selector),
:deep(.dark-course-select .ant-select-selector),
.dark-adv-row :deep(.ant-select:not(.ant-select-customize-input) .ant-select-selector) {
  background: rgba(255,255,255,0.08) !important;
  border-color: rgba(255,255,255,0.16) !important;
  color: rgba(255,255,255,0.88) !important;
  border-radius: 20px !important;
}
:deep(.dark-sort-select .ant-select-arrow),
:deep(.dark-course-select .ant-select-arrow),
.dark-adv-row :deep(.ant-select-arrow) { color: rgba(255,255,255,0.5) !important; }
:deep(.dark-sort-select .ant-select-selection-item),
:deep(.dark-course-select .ant-select-selection-item) { color: rgba(255,255,255,0.88) !important; }
:deep(.dark-sort-select .ant-select-selection-placeholder),
:deep(.dark-course-select .ant-select-selection-placeholder),
.dark-adv-row :deep(.ant-select-selection-placeholder) { color: rgba(255,255,255,0.44) !important; }
.dark-adv-row :deep(.ant-select-clear),
:deep(.dark-course-select .ant-select-clear) { background: transparent !important; color: rgba(255,255,255,0.5) !important; }

/* ── 移动端顶部 Header ── */
.practice-mobile-header {
  display: none;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 16px;
  background: #1A56DB;
  color: #fff;
}

.practice-mobile-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.practice-mobile-menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  color: #fff;
  cursor: pointer;
  border-radius: 8px;
}

.practice-mobile-menu-btn:hover {
  background: rgba(255,255,255,0.1);
}

.practice-mobile-title {
  font-size: 16px;
  font-weight: 700;
}

.practice-mobile-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: #fff;
}

/* ── 主布局 ── */
.practice-page {
  display: flex;
  flex-direction: row;
  min-height: 100vh;
  overflow: hidden;
  background: #F4F8FC;
}

.practice-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* ── 顶部功能控制区 ── */
.practice-header {
  background: #fff;
  border-bottom: 1px solid #E8F1F8;
  padding: 24px 40px 0;
}

.practice-header-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 20px;
}

.practice-header-title h1 {
  margin: 0 0 4px;
  font-size: 24px;
  font-weight: 800;
  color: #1E3A5F;
}

.practice-header-title p {
  margin: 0;
  font-size: 14px;
  color: #64748B;
}

.practice-header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

/* 搜索框 */
.practice-search-wrapper {
  position: relative;
  width: 280px;
}

.practice-search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: #64748B;
  pointer-events: none;
}

.practice-search-input {
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

.practice-search-input:focus {
  border-color: #1A56DB;
  box-shadow: 0 0 0 3px rgba(26, 86, 219, 0.1);
}

.practice-search-input::placeholder {
  color: #94A3B8;
}

/* 按钮组 */
.practice-header-btns {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 课程选择器 */
.practice-course-select {
  width: 180px;
}

.practice-course-select :deep(.ant-select-selector) {
  height: 40px !important;
  line-height: 38px !important;
  border: 1px solid #CDE0F5 !important;
  border-radius: 8px !important;
  background: #FFFFFF !important;
}

.practice-course-select :deep(.ant-select-selection-item) {
  color: #1E3A5F !important;
  font-weight: 600 !important;
}

/* 排序选择器 */
.practice-sort-select {
  width: 130px;
}

.practice-sort-select :deep(.ant-select-selector) {
  height: 40px !important;
  line-height: 38px !important;
  border: 1px solid #CDE0F5 !important;
  border-radius: 8px !important;
  background: #FFFFFF !important;
}

.practice-sort-select :deep(.ant-select-selection-item) {
  color: #1E3A5F !important;
  font-weight: 600 !important;
}

/* 创建按钮 */
.practice-create-btn {
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

.practice-create-btn:hover {
  background: #1546B5 !important;
  border-color: #1546B5 !important;
}

/* ── Tab与过滤栏 ── */
.practice-header-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 0;
}

.practice-source-type-hint {
  font-size: 14px;
  color: #64748B;
  padding: 12px 0;
}

.practice-source-type-hint strong {
  color: #1E3A5F;
  font-size: 18px;
  margin: 0 4px;
}

.practice-tabs {
  display: flex;
  align-items: center;
  gap: 0;
}

.practice-tab {
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

.practice-tab:hover {
  color: #1E3A5F;
}

.practice-tab.active {
  color: #1A56DB;
  font-weight: 700;
  border-bottom-color: #1A56DB;
}

/* 过滤行 */
.practice-filter-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.practice-filter-select {
  width: 130px;
}

.practice-filter-select :deep(.ant-select-selector) {
  height: 36px !important;
  line-height: 34px !important;
  border: 1px solid #E8F1F8 !important;
  border-radius: 8px !important;
  background: #F8FBFF !important;
}

.practice-filter-select :deep(.ant-select-selection-item) {
  color: #4B5563 !important;
  font-size: 13px !important;
}

/* ── 数据统计摘要 ── */
.practice-stats {
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

.practice-stats strong {
  color: #1E3A5F;
  font-size: 18px;
  margin: 0 4px;
}

/* ── 加载 & 空状态 ── */
.practice-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80px 0;
}

.practice-empty {
  padding: 80px 0;
}

/* ── 列表 ── */
.practice-list {
  flex: 1;
  background: #F4F8FC;
}

/* PC端列表头 */
.practice-list-header {
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

.practice-list-col {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.practice-list-col-main {
  flex: 1;
  padding-right: 24px;
}

.practice-list-col-qty {
  width: 104px;
  text-align: center;
  padding: 0 8px;
  border-left: 1px solid #E8F1F8;
}

.practice-list-col-info {
  width: 182px;
  padding-left: 24px;
  border-left: 1px solid #E8F1F8;
}

.practice-list-col-status {
  width: 130px;
  padding-left: 24px;
  border-left: 1px solid #E8F1F8;
}

.practice-list-col-action {
  width: 200px;
  text-align: right;
  padding-left: 24px;
  border-left: 1px solid #E8F1F8;
}

/* 列表行 */
.practice-row {
  position: relative;
  display: flex;
  align-items: stretch;
  padding: 0 40px;
  background: #FFFFFF;
  border-bottom: 1px solid #E8F1F8;
  cursor: pointer;
  transition: background-color 0.15s;
}

.practice-row:hover {
  background: #F8FBFF;
}

/* 状态指示条 */
.practice-row-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

/* 主要信息 */
.practice-row-main {
  flex: 1;
  padding: 20px 24px 20px 0;
  min-width: 0;
}

.practice-row-title {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 700;
  color: #1E3A5F;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.practice-row:hover .practice-row-title {
  color: #1A56DB;
}

.practice-row-sub {
  display: flex;
  align-items: center;
  gap: 12px;
}

.practice-row-tag {
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-radius: 4px;
  background: #EFF6FF;
  color: #1A56DB;
  border: 1px solid #BFDBFE;
}

.practice-row-category {
  font-size: 13px;
  color: #64748B;
}

/* 题量 */
.practice-row-qty {
  width: 104px;
  padding: 20px 8px;
  border-left: 1px solid #E8F1F8;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.practice-qty-value {
  font-size: 18px;
  font-weight: 700;
  color: #1E3A5F;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.practice-qty-label {
  font-size: 12px;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 4px;
}

/* 关联信息 */
.practice-row-info {
  width: 182px;
  padding-left: 24px;
  padding-right: 8px;
  border-left: 1px solid #E8F1F8;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.practice-info-text {
  font-size: 13px;
  color: #4B5563;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.practice-info-empty {
  font-size: 13px;
  color: #94A3B8;
}

/* 状态 */
.practice-row-status {
  width: 130px;
  padding-left: 24px;
  padding-right: 8px;
  border-left: 1px solid #E8F1F8;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.practice-status-tag {
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
  border-radius: 4px;
  background: #F1F5F9;
  color: #64748B;
  border: 1px solid #E2E8F0;
  width: fit-content;
}

.practice-desc-text {
  font-size: 13px;
  color: #64748B;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 操作 */
.practice-row-action {
  width: 200px;
  padding-left: 24px;
  padding-right: 16px;
  border-left: 1px solid #E8F1F8;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.practice-action-btn {
  height: 32px;
  padding: 0 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid #E2E8F0;
  background: #FFFFFF;
  color: #4B5563;
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.practice-action-btn:hover {
  border-color: #1A56DB;
  color: #1A56DB;
}

.practice-action-btn.primary {
  background: #1A56DB !important;
  border-color: #1A56DB !important;
  color: #FFFFFF !important;
}

.practice-action-btn.primary:hover {
  background: #1546B5 !important;
  border-color: #1546B5 !important;
}

/* SVG icon sizing */
svg.icon-sm {
  display: block;
  flex-shrink: 0;
  width: 16px;
  height: 16px;
}

/* ── 响应式 ── */
@media (max-width: 768px) {
  .practice-page {
    flex-direction: column;
  }

  .practice-mobile-header {
    display: flex;
  }

  .practice-header {
    padding: 16px 16px 0;
  }

  .practice-header-top {
    flex-direction: column;
    gap: 16px;
  }

  .practice-header-title h1 {
    font-size: 20px;
  }

  .practice-search-wrapper {
    width: 100%;
  }

  .practice-header-btns {
    width: 100%;
    flex-wrap: wrap;
  }

  .practice-course-select,
  .practice-sort-select {
    width: 100%;
    flex: 1;
  }

  .practice-header-bottom {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
    padding-bottom: 12px;
  }

  .practice-filter-row {
    flex-wrap: wrap;
    width: 100%;
  }

  .practice-filter-select {
    width: calc(50% - 5px);
  }

  .practice-stats {
    padding: 12px 16px;
    font-size: 13px;
  }

  .practice-stats strong {
    font-size: 16px;
  }

  .practice-list-header {
    display: none;
  }

  .practice-row {
    flex-direction: column;
    padding: 16px;
    gap: 12px;
  }

  .practice-row-accent {
    display: none;
  }

  .practice-row-main {
    padding: 0;
  }

  .practice-row-title {
    font-size: 15px;
  }

  .practice-row-qty,
  .practice-row-info,
  .practice-row-status {
    width: 100%;
    padding: 0;
    border: none;
    flex-direction: row;
    gap: 8px;
  }

  .practice-qty-value,
  .practice-info-text,
  .practice-desc-text {
    font-size: 14px;
  }

  .practice-row-action {
    width: 100%;
    padding: 0;
    border: none;
    justify-content: flex-start;
  }

  .practice-loading,
  .practice-empty {
    padding: 40px 0;
  }
}

/* 设置弹窗 */
.settings-panel {
  padding: 8px 4px;
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.settings-icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background: linear-gradient(135deg, #4B6EF5, #3B5DE0);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 22px;
  flex-shrink: 0;
  box-shadow: 0 8px 20px rgba(75, 110, 245, 0.3);
}

.settings-title-area {
  flex: 1;
  min-width: 0;
}

.settings-title {
  margin: 0 0 4px;
  font-size: 18px;
  font-weight: 700;
  color: var(--v2-text-primary);
}

.settings-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--v2-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.settings-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.settings-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--v2-text-secondary);
}

.settings-select {
  width: 100%;
}

.settings-actions {
  display: flex;
  gap: 12px;
}

.btn-cancel {
  flex: 1;
  height: 44px;
  border: 1.5px solid var(--v2-border);
  border-radius: 12px;
  background: transparent;
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-cancel:hover {
  background: var(--v2-bg);
  border-color: var(--v2-primary);
  color: var(--v2-primary);
}

.btn-confirm {
  flex: 1;
  height: 44px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #4B6EF5, #3B5DE0);
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 16px rgba(75, 110, 245, 0.25);
}

.btn-confirm:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(75, 110, 245, 0.35);
}

/* 题库展开样式 */
.folder-questions {
  margin-top: 16px;
  padding: 16px;
  background: #f7f9ff;
  border-radius: 12px;
  max-height: 400px;
  overflow-y: auto;
}

.folder-questions-loading,
.folder-questions-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: var(--v2-text-secondary);
}

.folder-questions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.question-item {
  padding: 12px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #eef0f5;
}

.question-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.question-index {
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.question-item-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--v2-text-primary);
  margin-bottom: 8px;
}

.question-item-answer {
  font-size: 13px;
  color: var(--v2-text-secondary);
}

/* AI创建表单 */

/* 确认保存弹窗 */
.ai-confirm-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.confirm-header {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: #f5f7ff;
  border-radius: 8px;
}

.confirm-task-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.confirm-label {
  font-size: 13px;
  color: #666;
}

.confirm-value {
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.confirm-questions {
  max-height: 60vh;
  overflow-y: auto;
}

.confirm-questions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.confirm-questions-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
}

.confirm-questions-hint {
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.confirm-questions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.confirm-question-item {
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
}

.confirm-question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.confirm-question-num {
  font-size: 13px;
  font-weight: 600;
  color: #666;
}

.confirm-question-content {
  margin-bottom: 12px;
}

.confirm-question-options {
  margin-bottom: 12px;
  padding-left: 20px;
}

.confirm-option-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.confirm-option-key {
  width: 20px;
  font-weight: 600;
  color: #333;
}

.confirm-question-answer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f0f7ff;
  border-radius: 6px;
}

.answer-label {
  font-size: 13px;
  font-weight: 600;
  color: #333;
}

.confirm-question-explanation {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.explanation-label {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  flex-shrink: 0;
}

.confirm-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.task-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.ai-create-form,
.edit-folder-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.form-grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.field-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--v2-text-secondary);
}

.field-label.required::after {
  content: ' *';
  color: #ff4d4f;
}

.field-hint {
  font-size: 12px;
  font-weight: 400;
  color: var(--v2-text-secondary);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}

.upload-btn {
  margin-bottom: 8px;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f7f9ff;
  border: 1px solid #e8efff;
  border-radius: 8px;
}

.file-icon {
  color: var(--v2-primary);
  font-size: 18px;
}

.file-name {
  flex: 1;
  font-size: 14px;
  color: var(--v2-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 12px;
  color: var(--v2-text-secondary);
}

.file-list-empty {
  margin-top: 8px;
  font-size: 13px;
  color: var(--v2-text-secondary);
}

.modal-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.modal-tab {
  padding: 10px 24px;
  font-size: 14px;
  font-weight: 600;
  color: var(--v2-text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.modal-tab:hover {
  color: var(--v2-primary);
}

.modal-tab.active {
  color: var(--v2-primary);
  border-bottom-color: var(--v2-primary);
}

.tab-content {
  max-height: 60vh;
  overflow-y: auto;
}

.task-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-list-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
}

.task-detail-header {
  margin-bottom: 12px;
}

.task-detail-content {
  padding: 8px 0;
}

.detail-info {
  background: #f5f5f5;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 8px;
  font-size: 14px;
}

.detail-row:last-child {
  margin-bottom: 0;
}

.detail-label {
  color: #666;
  min-width: 80px;
}

.detail-value {
  color: #333;
  flex: 1;
}

.detail-value.error {
  color: #ff4d4f;
}

.questions-section {
  margin-top: 16px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--v2-text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.question-item {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
}

.question-type-tag {
  display: inline-block;
  background: #e6f7ff;
  color: #1890ff;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  margin-bottom: 8px;
}

.question-content {
  font-size: 14px;
  color: #333;
  line-height: 1.6;
  margin-bottom: 8px;
}

.question-options {
  margin-left: 20px;
  margin-bottom: 8px;
}

.option-item {
  font-size: 13px;
  color: #555;
  line-height: 1.8;
}

.question-answer {
  font-size: 13px;
  color: #52c41a;
  margin-bottom: 4px;
}

.question-explanation {
  font-size: 13px;
  color: #888;
  margin-top: 4px;
}

.no-questions {
  text-align: center;
  padding: 24px 0;
}

.hidden-file-input {
  display: none;
}

/* 题目操作按钮 */
.question-item-actions {
  display: flex;
  gap: 4px;
  margin-left: auto;
}

/* 题目详情弹窗表格样式 */
.question-detail-content {
  padding: 8px 0;
}

.table-question-content {
  word-break: break-word;                                                                                                                                                                                                                                                                      
  white-space: normal;                                                                                                                                                                                                                                                                         
  line-height: 1.5; 
}

.table-question-options {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 13px;
}

.table-option-item {
  display: flex;
  gap: 4px;
}

.option-key {
  font-weight: 600;
  flex-shrink: 0;
}

.explanation-text {
  font-size: 13px;
  color: var(--v2-text-secondary);
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.folder-questions-more {
  display: flex;
  justify-content: center;
  padding: 12px;
  border-top: 1px dashed #e8e8e8;
  margin-top: 8px;
}

/* 编辑题目弹窗 */
.question-edit-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.options-edit-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: #f7f9ff;
  border-radius: 8px;
}

.option-edit-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.option-edit-key {
  width: 24px;
  font-weight: 600;
  color: var(--v2-text-primary);
  flex-shrink: 0;
}

.answer-edit-section {
  padding: 12px;
  background: #f0f7ff;
  border-radius: 8px;
}
</style>
