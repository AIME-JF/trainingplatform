<template>
  <div class="ai-paper-page">
    <!-- 顶栏 -->
    <header class="page-header">
      <div class="header-title">
        <h1 class="header-h1">{{ viewMode === 'list' ? '任务列表' : '智能出卷' }}</h1>
        <p class="header-desc">{{ viewMode === 'list' ? '查看和管理您的智能出卷任务' : '选择生成模式并设定规则，AI 将自动为您生成高质量试卷草稿。' }}</p>
      </div>
      <div class="header-right">
        <a-button v-if="viewMode === 'create'" @click="viewMode = 'list'; loadTasks()">任务列表</a-button>
        <a-button v-else @click="viewMode = 'create'">返回创建</a-button>
        <a-button v-if="viewMode === 'create'" type="primary" :loading="creating" @click="handleCreateTask">创建任务</a-button>
      </div>
    </header>

    <!-- 内容画布 -->
    <div class="page-content">
      <div class="content-container">
        <!-- 任务列表页面 -->
        <div v-if="viewMode === 'list'" class="task-list-page">
          <div class="main-card">
            <section class="basic-section">
              <h2 class="section-title">
                <span class="section-indicator"></span> 任务列表
              </h2>
              <div class="task-filter">
                <a-select
                  v-model:value="taskTypeFilter"
                  allow-clear
                  placeholder="筛选任务类型"
                  style="width: 140px"
                  @change="loadTasks"
                >
                  <a-select-option value="assembly">知识点AI组卷</a-select-option>
                  <a-select-option value="topic">AI提示词生成</a-select-option>
                  <a-select-option value="document">文档AI生成</a-select-option>
                </a-select>
                <a-space>
                  <a-button type="link" size="small" @click="loadTasks">刷新</a-button>
                  <a-button
                    type="primary"
                    size="small"
                    :disabled="!hasSelectedConfirmable"
                    :loading="batchConfirming"
                    @click="handleBatchConfirm"
                  >
                    <template #icon><svg style="width: 10px; height: 10px;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg></template>
                    批量确认
                  </a-button>
                  <a-button
                    danger
                    size="small"
                    :disabled="selectedTaskIds.length === 0"
                    :loading="batchDeleting"
                    @click="handleBatchDelete"
                  >
                    <template #icon><svg style="width: 10px; height: 10px;" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg></template>
                    批量删除
                  </a-button>
                </a-space>
              </div>

              <!-- 选中计数提示 -->
              <div v-if="selectedTaskIds.length > 0" class="selection-hint">
                已选择 {{ selectedTaskIds.length }} 项
                <a-button type="link" size="small" @click="selectedTaskIds = []">取消选择</a-button>
              </div>

              <a-list :data-source="taskList" :loading="taskLoading" class="task-list">
                <template #renderItem="{ item }">
                  <a-list-item
                    class="task-item"
                    :class="{ active: activeTask?.id === item.id, selected: selectedTaskIds.includes(item.id) }"
                    @click="selectTask(item)"
                  >
                    <a-checkbox
                      class="task-checkbox"
                      :checked="selectedTaskIds.includes(item.id)"
                      @click.stop
                      @change="toggleSelect(item.id, $event)"
                    />
                    <a-list-item-meta>
                      <template #title>
                        <span>{{ item.taskName }}</span>
                        <a-tag :color="getTaskTypeColor(item.taskType)" size="small" style="margin-left: 8px">
                          {{ getTaskTypeLabel(item.taskType) }}
                        </a-tag>
                      </template>
                      <template #description>
                        <span>{{ item.paperTitle || '未命名试卷' }}</span>
                      </template>
                    </a-list-item-meta>
                    <template #actions>
                      <a-tag :color="statusColors[item.status]">{{ statusLabels[item.status] }}</a-tag>
                      <a-space>
                        <a-button
                          v-if="item.status === 'completed'"
                          type="link"
                          size="small"
                          @click.stop="handleConfirmSingleTask(item)"
                        >确认</a-button>
                        <a-button
                          danger
                          type="link"
                          size="small"
                          @click.stop="handleDeleteSingleTask(item)"
                        >删除</a-button>
                      </a-space>
                    </template>
                  </a-list-item>
                </template>
              </a-list>

              <a-empty v-if="!taskLoading && !taskList.length" description="暂无任务" />
            </section>
          </div>
        </div>

        <!-- 创建页面 -->
        <div v-else class="create-page">
        <!-- 统一大卡片 -->
        <div class="main-card">
          <!-- ================= 顶部通栏：基础设置 ================= -->
          <section class="basic-section">
            <h2 class="section-title">
              <span class="section-indicator"></span> 基础任务设置
            </h2>
            <div class="basic-grid">
              <div class="form-field">
                <label class="field-label required">任务名称</label>
                <a-input
                  v-model:value="formData.taskName"
                  class="input-minimal"
                  placeholder="例：2024年春季新警结业组卷任务"
                />
              </div>
              <div class="form-field">
                <label class="field-label required">试卷名称</label>
                <a-input
                  v-model:value="formData.paperTitle"
                  class="input-minimal"
                  placeholder="例：治安管理基础知识测试卷"
                />
              </div>
              <div class="form-field form-field-sm">
                <label class="field-label">试卷类型</label>
                <a-select v-model:value="formData.paperType" class="input-minimal input-select">
                  <a-select-option value="formal">正式考核</a-select-option>
                  <a-select-option value="quiz">模拟练习</a-select-option>
                </a-select>
              </div>
              <div class="form-field form-field-sm" :class="{ 'opacity-50': activeMode !== 'assemble' }">
                <label class="field-label">组卷模式</label>
                <a-select v-model:value="formData.assemblyMode" class="input-minimal input-select" :disabled="activeMode !== 'assemble'">
                  <a-select-option value="balanced">均衡抽题</a-select-option>
                  <a-select-option value="practice">练习导向</a-select-option>
                  <a-select-option value="exam">考试导向</a-select-option>
                </a-select>
              </div>
            </div>
          </section>

          <!-- ================= 左右双栏：核心业务区 ================= -->
          <div class="core-grid">
            <!-- 左栏：出卷方式与数据源 -->
            <div class="left-column">
              <!-- 模块：出卷方式选择 -->
              <section class="mode-section">
                <h2 class="section-title">
                  <span class="section-indicator indigo"></span> 核心出卷方式
                </h2>
                <div class="mode-cards">
                  <!-- 方式 1: 知识点组卷 -->
                  <div
                    class="mode-card"
                    :class="{ active: activeMode === 'assemble' }"
                    @click="activeMode = 'assemble'"
                  >
                    <div class="mode-icon" :class="{ active: activeMode === 'assemble' }">
                      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4"/>
                      </svg>
                    </div>
                    <div class="mode-title">题库智能组卷</div>
                    <div class="mode-desc">从现有题库按知识点筛选</div>
                  </div>

                  <!-- 方式 2: 提示词生成 -->
                  <div
                    class="mode-card"
                    :class="{ active: activeMode === 'topic' }"
                    @click="activeMode = 'topic'"
                  >
                    <div class="mode-icon" :class="{ active: activeMode === 'topic' }">
                      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                      </svg>
                    </div>
                    <div class="mode-title">大纲文本生成</div>
                    <div class="mode-desc">依据给定主题现编试题</div>
                  </div>

                  <!-- 方式 3: 文档生成 -->
                  <div
                    class="mode-card"
                    :class="{ active: activeMode === 'document' }"
                    @click="activeMode = 'document'"
                  >
                    <div class="mode-icon" :class="{ active: activeMode === 'document' }">
                      <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                      </svg>
                    </div>
                    <div class="mode-title">上传文档生成</div>
                    <div class="mode-desc">解析 Word/PDF 生成</div>
                  </div>
                </div>
              </section>

              <div class="divider"></div>

              <!-- 模块：数据源与条件 -->
              <section class="source-section">
                <h2 class="section-title">
                  <span class="section-indicator"></span> 内容源与范围限制
                </h2>

                <!-- 面板 A: 题库提取条件 -->
                <div v-show="activeMode === 'assemble'" class="source-panel">
                  <div class="form-field">
                    <label class="field-label">限制知识点</label>
                    <a-select
                      v-model:value="formData.knowledgePointIds"
                      mode="multiple"
                      allow-clear
                      show-search
                      :filter-option="false"
                      :loading="knowledgePointLoading"
                      placeholder="搜索并选择知识点，留空则在全库抽取"
                      class="input-minimal input-select"
                      :options="knowledgePointSelectOptions"
                      @search="handleKnowledgePointSearch"
                      @focus="handleKnowledgePointFocus"
                    />
                  </div>
                  <div class="form-field">
                    <label class="field-label">适用警种</label>
                    <a-select
                      v-model:value="formData.policeTypeId"
                      allow-clear
                      placeholder="不限"
                      class="input-minimal input-select"
                    >
                      <a-select-option v-for="item in policeTypeOptions" :key="item.id" :value="item.id">
                        {{ item.name }}
                      </a-select-option>
                    </a-select>
                  </div>
                  <div class="toggle-box">
                    <div class="toggle-content">
                      <span class="toggle-label-text">自动放宽条件</span>
                      <p class="toggle-desc">题库余量不足时允许自动降级难度匹配</p>
                    </div>
                    <a-switch v-model:checked="formData.allowRelaxation" />
                  </div>
                </div>

                <!-- 面板 B: 大纲/参考文本生成 -->
                <div v-show="activeMode === 'topic'" class="source-panel">
                  <div class="form-field">
                    <label class="field-label">参考资料 / 考核大纲文本</label>
                    <p class="field-tip">AI 将严格基于您在此输入的参考资料内容进行题目创作，防止超纲。</p>
                    <a-textarea
                      v-model:value="formData.sourceText"
                      class="input-minimal textarea-minimal"
                      :rows="6"
                      :maxlength="8000"
                      show-count
                      placeholder="请在此粘贴相关的法律条文、行动指南或教材段落..."
                    />
                  </div>
                  <div class="form-field">
                    <label class="field-label">生成主题</label>
                    <a-input
                      v-model:value="formData.topic"
                      class="input-minimal"
                      :maxlength="200"
                      placeholder="例：电信网络诈骗案件侦办规范"
                    />
                  </div>
                  <div class="form-field">
                    <label class="field-label">整体难度</label>
                    <a-select v-model:value="formData.difficulty" class="input-minimal input-select">
                      <a-select-option :value="1">1级（入门）</a-select-option>
                      <a-select-option :value="2">2级（基础）</a-select-option>
                      <a-select-option :value="3">3级（适中）</a-select-option>
                      <a-select-option :value="4">4级（较难）</a-select-option>
                      <a-select-option :value="5">5级（困难）</a-select-option>
                    </a-select>
                  </div>
                </div>

                <!-- 面板 C: 文档解析生成 -->
                <div v-show="activeMode === 'document'" class="source-panel">
                  <div class="form-field">
                    <label class="field-label">上传源文档</label>
                    <p class="field-tip">
                      方式一：上传制度规章、教材课件等资料，AI 自动分析内容并智能出题。
                      <br/>
                      方式二：<a href="/trainingplatform/docs/公安人工智能培训智能出卷模板.docx" download class="template-link">下载试题模板</a>，填写完整试卷题目后上传，AI 直接解析生成标准试卷。
                    </p>
                    <div class="upload-container">
                      <div class="upload-zone" @click="triggerUpload">
                        <input
                          ref="fileInputRef"
                          type="file"
                          accept=".txt,.doc,.docx,.pdf,.xlsx,.xls,.csv"
                          multiple
                          style="display: none"
                          @change="handleFileChange"
                        />
                        <div class="upload-icon">
                          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                          </svg>
                        </div>
                        <div class="upload-text">
                          <span class="upload-title">点击上传文件，或将文件拖拽到此处</span>
                          <span class="upload-hint">支持多文件上传 PDF、DOCX、XLSX、CSV、TXT 格式，单个文件不超过 50MB</span>
                        </div>
                      </div>
                      <div v-for="(name, index) in documentFileNames" :key="index" class="file-info">
                        <div class="file-info-content">
                          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                          </svg>
                          <span class="file-name">{{ name }}</span>
                        </div>
                        <span class="file-remove" @click="removeFile(index)">×</span>
                      </div>
                    </div>
                  </div>
                  <div class="form-field">
                    <label class="field-label">整体难度</label>
                    <a-select v-model:value="formData.difficulty" class="input-minimal input-select">
                      <a-select-option :value="1">1级（入门）</a-select-option>
                      <a-select-option :value="2">2级（基础）</a-select-option>
                      <a-select-option :value="3">3级（适中）</a-select-option>
                      <a-select-option :value="4">4级（较难）</a-select-option>
                      <a-select-option :value="5">5级（困难）</a-select-option>
                    </a-select>
                  </div>
                </div>
              </section>
            </div>

            <!-- 右栏：题型配置与AI指令 -->
            <div class="right-column">
              <!-- 模块：题型结构配置 -->
              <section class="type-section">
                <div class="type-section-header">
                  <h2 class="section-title no-margin">
                    <span class="section-indicator dark"></span> 题型结构配置
                  </h2>
                  <div class="type-summary">
                    <span>总题数：<em class="summary-num">{{ typeSummary.totalCount }}</em></span>
                    <span>预计分值：<em class="summary-num blue">{{ typeSummary.totalScore }}</em></span>
                  </div>
                </div>

                <!-- 题型表格 -->
                <div class="type-table">
                  <div class="type-table-head">
                    <span class="col-type">题型</span>
                    <span class="col-qty">数量</span>
                    <span class="col-score">分/题</span>
                    <span class="col-diff" :class="{ dim: activeMode === 'document' }">
                      {{ activeMode === 'topic' ? '生成难度' : activeMode === 'document' ? '难度(参考)' : '目标难度' }}
                    </span>
                    <span class="col-subtotal">小计</span>
                  </div>

                  <!-- 单选题 -->
                  <div class="type-row">
                    <div class="col-type">
                      <span class="type-dot blue"></span>
                      <span class="type-name">单选题</span>
                    </div>
                    <div class="col-qty">
                      <a-input-number
                        v-model:value="formData.typeConfigs[0].count"
                        :min="0"
                        :max="50"
                        class="type-input"
                      />
                    </div>
                    <div class="col-score">
                      <a-input-number
                        v-model:value="formData.typeConfigs[0].score"
                        :min="1"
                        :max="20"
                        class="type-input"
                      />
                    </div>
                    <div class="col-diff" :class="{ dim: activeMode === 'document' }">
                      <a-select
                        v-model:value="formData.typeConfigs[0].difficulty"
                        class="type-select"
                        :disabled="activeMode === 'document'"
                      >
                        <a-select-option :value="1">1级</a-select-option>
                        <a-select-option :value="2">2级</a-select-option>
                        <a-select-option :value="3">3级</a-select-option>
                        <a-select-option :value="4">4级</a-select-option>
                        <a-select-option :value="5">5级</a-select-option>
                      </a-select>
                    </div>
                    <div class="col-subtotal">{{ typeSummary.singleScore }} 分</div>
                  </div>

                  <!-- 多选题 -->
                  <div class="type-row">
                    <div class="col-type">
                      <span class="type-dot purple"></span>
                      <span class="type-name">多选题</span>
                    </div>
                    <div class="col-qty">
                      <a-input-number
                        v-model:value="formData.typeConfigs[1].count"
                        :min="0"
                        :max="50"
                        class="type-input"
                      />
                    </div>
                    <div class="col-score">
                      <a-input-number
                        v-model:value="formData.typeConfigs[1].score"
                        :min="1"
                        :max="20"
                        class="type-input"
                      />
                    </div>
                    <div class="col-diff" :class="{ dim: activeMode === 'document' }">
                      <a-select
                        v-model:value="formData.typeConfigs[1].difficulty"
                        class="type-select"
                        :disabled="activeMode === 'document'"
                      >
                        <a-select-option :value="1">1级</a-select-option>
                        <a-select-option :value="2">2级</a-select-option>
                        <a-select-option :value="3">3级</a-select-option>
                        <a-select-option :value="4">4级</a-select-option>
                        <a-select-option :value="5">5级</a-select-option>
                      </a-select>
                    </div>
                    <div class="col-subtotal">{{ typeSummary.multiScore }} 分</div>
                  </div>

                  <!-- 判断题 -->
                  <div class="type-row last">
                    <div class="col-type">
                      <span class="type-dot amber"></span>
                      <span class="type-name">判断题</span>
                    </div>
                    <div class="col-qty">
                      <a-input-number
                        v-model:value="formData.typeConfigs[2].count"
                        :min="0"
                        :max="50"
                        class="type-input"
                      />
                    </div>
                    <div class="col-score">
                      <a-input-number
                        v-model:value="formData.typeConfigs[2].score"
                        :min="1"
                        :max="20"
                        class="type-input"
                      />
                    </div>
                    <div class="col-diff" :class="{ dim: activeMode === 'document' }">
                      <a-select
                        v-model:value="formData.typeConfigs[2].difficulty"
                        class="type-select"
                        :disabled="activeMode === 'document'"
                      >
                        <a-select-option :value="1">1级</a-select-option>
                        <a-select-option :value="2">2级</a-select-option>
                        <a-select-option :value="3">3级</a-select-option>
                        <a-select-option :value="4">4级</a-select-option>
                        <a-select-option :value="5">5级</a-select-option>
                      </a-select>
                    </div>
                    <div class="col-subtotal">{{ typeSummary.judgeScore }} 分</div>
                  </div>
                </div>
              </section>

              <div class="divider"></div>

              <!-- 模块：附加智能指令 -->
              <section class="ai-section">
                <h2 class="section-title">
                  <span class="section-indicator light-indigo"></span> 附加智能指令
                  <a-tag color="indigo" class="ai-tag">AI</a-tag>
                </h2>
                <a-textarea
                  v-model:value="formData.requirements"
                  class="input-minimal textarea-minimal ai-textarea"
                  :rows="4"
                  placeholder="选填。请用自然语言描述试卷侧重点或出题要求。例如：题目风格需贴近现场实战，选项应具有较强的迷惑性，必须包含情景模拟类题目..."
                  :maxlength="500"
                  show-count
                />
              </section>
            </div>
          </div>
        </div>
        </div>
      </div>
    </div>

    <!-- 任务详情抽屉 -->
    <a-drawer
      v-model:open="detailDrawerVisible"
      :title="activeTask?.taskName || '任务详情'"
      placement="right"
      :width="700"
      @close="detailDrawerVisible = false"
    >
      <template v-if="activeTask">
        <ai-task-timeline
          :status="activeTask.status"
          :created-at="activeTask.createdAt"
          :completed-at="activeTask.completedAt"
          :confirmed-at="activeTask.confirmedAt"
        />

        <a-alert
          v-if="activeTask.errorMessage"
          type="error"
          show-icon
          :message="activeTask.errorMessage"
          style="margin-top: 12px"
        />

        <div class="detail-section">
          <div class="detail-section-title">任务请求</div>
          <a-descriptions :column="2" size="small" bordered>
            <a-descriptions-item label="任务类型">
              <a-tag :color="getTaskTypeColor(activeTask.taskType)">{{ getTaskTypeLabel(activeTask.taskType) }}</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="试卷名称">{{ activeTask.requestPayload?.paperTitle }}</a-descriptions-item>
            <a-descriptions-item label="题型配置" :span="2">
              {{ formatTypeConfigs(activeTask.requestPayload?.typeConfigs) }}
            </a-descriptions-item>
          </a-descriptions>
        </div>

        <div v-if="activeTask.parseSummary || activeTask.parsedRequest" class="detail-section">
          <div class="detail-section-title">解析结果</div>
          <a-alert v-if="activeTask.parseSummary" type="info" show-icon :message="activeTask.parseSummary" />
        </div>

        <div class="detail-section">
          <div class="detail-section-title">试卷草稿</div>
          <paper-draft-editor
            v-if="activeTask.paperDraft"
            v-model="activeTask.paperDraft"
            :disabled="!canEditTask"
            :allow-manual-question="true"
            :sort-by-type="true"
            @edit-question="openEditQuestion"
            @create-question="openCreateQuestion"
          />
          <a-empty v-else-if="activeTask.status === 'processing'" description="任务处理中..." />
          <a-empty v-else description="暂无试卷草稿" />
        </div>

        <div class="detail-actions">
          <a-space>
            <a-button @click="loadTaskDetail(activeTask.id, activeTask.taskType)">刷新详情</a-button>
            <a-button
              v-if="activeTask.status === 'completed'"
              :loading="saving"
              @click="handleSaveTask"
            >
              保存修改
            </a-button>
            <a-button
              v-if="activeTask.status === 'completed'"
              type="primary"
              :loading="confirming"
              @click="handleConfirmTask"
            >
              确认入卷库
            </a-button>
          </a-space>
        </div>
      </template>
    </a-drawer>

    <!-- 题目编辑弹窗 -->
    <question-form-modal
      v-model:open="questionModalOpen"
      :title="editingQuestionIndex === -1 ? '新增题目' : '编辑题目'"
      :question="editingQuestion"
      :police-type-options="policeTypeOptions"
      @submit="handleSubmitQuestion"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import {
  confirmAiPaperAssemblyTask,
  createAiPaperAssemblyTask,
  getAiPaperAssemblyTaskDetail,
  getAiPaperAssemblyTasks,
  updateAiPaperAssemblyTaskResult,
  deleteAiPaperAssemblyTask,
  confirmAiPaperGenerationTask,
  createAiPaperGenerationTask,
  getAiPaperGenerationTaskDetail,
  getAiPaperGenerationTasks,
  updateAiPaperGenerationTaskResult,
  deleteAiPaperGenerationTask,
  getAiPaperDocumentGenerationTasks,
  createAiPaperDocumentGenerationTask,
  getAiPaperDocumentGenerationTaskDetail,
  updateAiPaperDocumentGenerationTaskResult,
  confirmAiPaperDocumentGenerationTask,
  deleteAiPaperDocumentGenerationTask,
  parseAiDocumentFile,
} from '@/api/ai'
import { getPoliceTypes } from '@/api/user'
import AiTaskTimeline from './components/AiTaskTimeline.vue'
import PaperDraftEditor from './components/PaperDraftEditor.vue'
import QuestionFormModal from './components/QuestionFormModal.vue'
import { createKnowledgePointRemoteSelect } from './utils/knowledgePointRemoteSelect'
import { formatPaperTypeConfigs } from './utils/paperTypeConfig'
import { sortQuestionsByType } from './utils/questionSort'

const authStore = useAuthStore()

// 状态
const activeMode = ref('assemble')
const activeTab = ref('create')
const creating = ref(false)
const saving = ref(false)
const confirming = ref(false)
const taskLoading = ref(false)
const taskList = ref([])
const activeTask = ref(null)
const taskTypeFilter = ref(null)
const viewMode = ref('create')
const detailDrawerVisible = ref(false)
const questionModalOpen = ref(false)
const editingQuestion = ref(null)
const editingQuestionIndex = ref(-1)
const documentFileNames = ref([])
const documentFiles = ref([])
const fileInputRef = ref(null)
const selectedTaskIds = ref([])
const batchDeleting = ref(false)
const batchConfirming = ref(false)

const policeTypeOptions = ref([])
const {
  knowledgePointLoading,
  knowledgePointSelectOptions,
  handleKnowledgePointSearch,
  handleKnowledgePointFocus,
} = createKnowledgePointRemoteSelect('name')

const statusLabels = { pending: '待处理', processing: '处理中', completed: '已完成', confirmed: '已确认', failed: '创建失败' }
const statusColors = { pending: 'default', processing: 'blue', completed: 'green', confirmed: 'green', failed: 'red' }

// 表单数据
const formData = reactive({
  taskName: '',
  paperTitle: '',
  paperType: 'formal',
  assemblyMode: 'balanced',
  policeTypeId: undefined,
  knowledgePointIds: [],
  allowRelaxation: true,
  sourceText: '',
  topic: '',
  difficulty: 3,
  duration: 60,
  passingScore: 60,
  requirements: '',
  typeConfigs: [
    { type: 'single', count: 5, difficulty: 3, score: 2 },
    { type: 'multi', count: 3, difficulty: 3, score: 3 },
    { type: 'judge', count: 2, difficulty: 2, score: 1 },
  ],
})

// 题型汇总计算
const typeSummary = computed(() => {
  const configs = formData.typeConfigs
  const single = configs[0] || {}
  const multi = configs[1] || {}
  const judge = configs[2] || {}
  const singleCount = Number(single.count) || 0
  const multiCount = Number(multi.count) || 0
  const judgeCount = Number(judge.count) || 0
  return {
    totalCount: singleCount + multiCount + judgeCount,
    totalScore: (singleCount * (Number(single.score) || 0)) + (multiCount * (Number(multi.score) || 0)) + (judgeCount * (Number(judge.score) || 0)),
    singleScore: singleCount * (Number(single.score) || 0),
    multiScore: multiCount * (Number(multi.score) || 0),
    judgeScore: judgeCount * (Number(judge.score) || 0),
  }
})

// 权限
const canCreateAssemblyTaskPermission = computed(() => authStore.hasPermission('CREATE_AI_PAPER_ASSEMBLY_TASK'))
const canCreateGenerationTaskPermission = computed(() => authStore.hasPermission('CREATE_AI_PAPER_GENERATION_TASK'))
const canUpdateTaskPermission = computed(() => {
  if (!activeTask.value) return false
  if (activeTask.value.taskType === 'paper_assembly') return authStore.hasPermission('UPDATE_AI_PAPER_ASSEMBLY_TASK')
  return authStore.hasPermission('UPDATE_AI_PAPER_GENERATION_TASK')
})
const canConfirmTaskPermission = computed(() => {
  if (!activeTask.value) return false
  if (activeTask.value.taskType === 'paper_assembly') return authStore.hasPermission('CONFIRM_AI_PAPER_ASSEMBLY_TASK')
  return authStore.hasPermission('CONFIRM_AI_PAPER_GENERATION_TASK')
})
const canEditTask = computed(() => activeTask.value?.status === 'completed' && canUpdateTaskPermission.value)

const hasSelectedConfirmable = computed(() => {
  return taskList.value.some(t => selectedTaskIds.value.includes(t.id) && t.status === 'completed')
})

// 任务类型相关
function getTaskTypeLabel(taskType) {
  const map = { paper_assembly: '知识点AI组卷', paper_generation: 'AI提示词生成', paper_document_generation: '文档AI生成' }
  return map[taskType] || taskType
}

function getTaskTypeColor(taskType) {
  const map = { paper_assembly: 'blue', paper_generation: 'green', paper_document_generation: 'purple' }
  return map[taskType] || 'default'
}

function formatTypeConfigs(configs = []) {
  const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题' }
  return configs.map(item => {
    const label = typeLabels[item.type] || item.type
    return `${label} ${item.count}题`
  }).join(' / ')
}

// 加载警种选项
async function loadPoliceTypeOptions() {
  try {
    const result = await getPoliceTypes()
    policeTypeOptions.value = result.items || result || []
  } catch {
    policeTypeOptions.value = []
  }
}

// 加载任务列表
async function loadTasks() {
  taskLoading.value = true
  try {
    const [assemblyResult, generationResult, documentResult] = await Promise.all([
      getAiPaperAssemblyTasks({ size: -1 }),
      getAiPaperGenerationTasks({ size: -1 }),
      getAiPaperDocumentGenerationTasks({ size: -1 }),
    ])

    let allTasks = [
      ...(assemblyResult.items || []).map(t => ({ ...t, taskType: 'paper_assembly' })),
      ...(generationResult.items || []).map(t => ({ ...t, taskType: 'paper_generation' })),
      ...(documentResult.items || []).map(t => ({ ...t, taskType: 'paper_document_generation' })),
    ]

    if (taskTypeFilter.value) {
      const filterMap = { assembly: 'paper_assembly', topic: 'paper_generation', document: 'paper_document_generation' }
      allTasks = allTasks.filter(t => t.taskType === filterMap[taskTypeFilter.value])
    }

    allTasks.sort((a, b) => {
      const timeA = a.createdAt ? new Date(a.createdAt).getTime() : 0
      const timeB = b.createdAt ? new Date(b.createdAt).getTime() : 0
      return timeB - timeA
    })

    taskList.value = allTasks
  } catch (error) {
    message.error(error.message || '加载任务失败')
  } finally {
    taskLoading.value = false
  }
}

// 加载任务详情
async function loadTaskDetail(taskId, taskType) {
  try {
    let result
    if (taskType === 'paper_assembly') {
      result = await getAiPaperAssemblyTaskDetail(taskId)
    } else if (taskType === 'topic' || taskType === 'paper_generation') {
      result = await getAiPaperGenerationTaskDetail(taskId)
    } else {
      result = await getAiPaperDocumentGenerationTaskDetail(taskId)
    }
    activeTask.value = {
      ...result,
      taskType: taskType || result.taskType,
      paperDraft: result.paperDraft ? JSON.parse(JSON.stringify(result.paperDraft)) : null,
    }
  } catch (error) {
    message.error(error.message || '加载任务详情失败')
  }
}

// 选择任务
async function selectTask(task) {
  await loadTaskDetail(task.id, task.taskType)
  detailDrawerVisible.value = true
}

// 重置表单
function resetForm() {
  formData.taskName = ''
  formData.paperTitle = ''
  formData.paperType = 'formal'
  formData.assemblyMode = 'balanced'
  formData.policeTypeId = undefined
  formData.knowledgePointIds = []
  formData.allowRelaxation = true
  formData.sourceText = ''
  formData.topic = ''
  formData.difficulty = 3
  formData.duration = 60
  formData.passingScore = 60
  formData.requirements = ''
  formData.typeConfigs = [
    { type: 'single', count: 5, difficulty: 3, score: 2 },
    { type: 'multi', count: 3, difficulty: 3, score: 3 },
    { type: 'judge', count: 2, difficulty: 2, score: 1 },
  ]
  documentFileNames.value = []
  documentFiles.value = []
}

// 创建任务
async function handleCreateTask() {
  if (!formData.taskName.trim() || !formData.paperTitle.trim()) {
    message.warning('请填写任务名称和试卷名称')
    return
  }
  if (typeSummary.value.totalCount <= 0) {
    message.warning('请至少将一种题型的数量设置为大于 0')
    return
  }

  creating.value = true
  try {
    let result

    if (activeMode.value === 'assemble') {
      if (!canCreateAssemblyTaskPermission.value) {
        message.error('需要 CREATE_AI_PAPER_ASSEMBLY_TASK 权限')
        return
      }
      result = await createAiPaperAssemblyTask({
        taskName: formData.taskName,
        paperTitle: formData.paperTitle,
        paperType: formData.paperType,
        assemblyMode: formData.assemblyMode,
        policeTypeId: formData.policeTypeId,
        knowledgePointIds: formData.knowledgePointIds,
        allowRelaxation: formData.allowRelaxation,
        duration: formData.duration,
        passingScore: formData.passingScore,
        typeConfigs: formData.typeConfigs,
        requirements: formData.requirements,
      })
    } else if (activeMode.value === 'topic') {
      if (!canCreateGenerationTaskPermission.value) {
        message.error('需要 CREATE_AI_PAPER_GENERATION_TASK 权限')
        return
      }
      if (!formData.topic.trim()) {
        message.warning('请填写生成主题')
        return
      }
      result = await createAiPaperGenerationTask({
        taskName: formData.taskName,
        paperTitle: formData.paperTitle,
        paperType: formData.paperType,
        topic: formData.topic,
        sourceText: formData.sourceText,
        difficulty: formData.difficulty,
        duration: formData.duration,
        passingScore: formData.passingScore,
        typeConfigs: formData.typeConfigs,
        requirements: formData.requirements,
      })
    } else {
      if (!canCreateGenerationTaskPermission.value) {
        message.error('需要 CREATE_AI_PAPER_GENERATION_TASK 权限')
        return
      }
      if (!formData.sourceText.trim()) {
        message.warning('请上传文档或输入文档内容')
        return
      }
      result = await createAiPaperDocumentGenerationTask({
        taskName: formData.taskName,
        paperTitle: formData.paperTitle,
        paperType: formData.paperType,
        sourceText: formData.sourceText,
        difficulty: formData.difficulty,
        duration: formData.duration,
        passingScore: formData.passingScore,
        typeConfigs: formData.typeConfigs,
        requirements: formData.requirements,
      })
    }

    message.success('任务已创建')
    resetForm()
    viewMode.value = 'list'
    await loadTasks()
    // 直接跳转到刚创建的任务详情
    if (result?.id) {
      await loadTaskDetail(result.id, result.taskType)
      detailDrawerVisible.value = true
    }
  } catch (error) {
    message.error(error.message || '创建任务失败')
  } finally {
    creating.value = false
  }
}

const fileParsing = ref(false)
const SOURCE_TEXT_MAX_LENGTH = 60000

function appendSourceText(chunk) {
  const textChunk = String(chunk || '')
  if (!textChunk) return
  const nextText = formData.sourceText
    ? `${formData.sourceText}\n\n${textChunk}`
    : textChunk
  if (nextText.length <= SOURCE_TEXT_MAX_LENGTH) {
    formData.sourceText = nextText
    return
  }

  const half = Math.floor(SOURCE_TEXT_MAX_LENGTH / 2)
  const omitted = nextText.length - half * 2
  formData.sourceText = `${nextText.slice(0, half)}\n\n[内容过长，已截断省略 ${omitted} 个字符]\n\n${nextText.slice(-half)}`
  message.warning(`解析内容过长，已自动截断到 ${SOURCE_TEXT_MAX_LENGTH} 字符`)
}

// 文件上传
function triggerUpload() {
  fileInputRef.value?.click()
}

async function handleFileChange(e) {
  const files = Array.from(e.target.files || [])
  if (!files.length) return

  fileParsing.value = true
  try {
    for (const file of files) {
      documentFileNames.value.push(file.name)
      documentFiles.value.push(file)

      const ext = file.name.split('.').pop().toLowerCase()
      if (['txt', 'md'].includes(ext)) {
        const reader = new FileReader()
        const text = await new Promise((resolve) => {
          reader.onload = (ev) => resolve(ev.target?.result || '')
          reader.readAsText(file)
        })
        appendSourceText(text)
      } else {
        const parsed = await parseAiDocumentFile(file)
        if (parsed?.text) {
          appendSourceText(parsed.text)
          continue
        }
        message.error(`${file.name} 解析失败`)
      }
    }
  } catch (err) {
    message.error(err.message || '文件解析失败')
  } finally {
    fileParsing.value = false
    e.target.value = ''
  }
}

function removeFile(index) {
  documentFileNames.value.splice(index, 1)
  documentFiles.value.splice(index, 1)
}

// 保存任务
async function handleSaveTask() {
  if (!canUpdateTaskPermission.value || !activeTask.value) return
  saving.value = true
  try {
    let result
    if (activeTask.value.taskType === 'paper_assembly') {
      result = await updateAiPaperAssemblyTaskResult(activeTask.value.id, {
        taskName: activeTask.value.taskName,
        paperDraft: activeTask.value.paperDraft,
      })
    } else {
      result = await updateAiPaperDocumentGenerationTaskResult(activeTask.value.id, {
        taskName: activeTask.value.taskName,
        paperDraft: activeTask.value.paperDraft,
      })
    }
    activeTask.value = {
      ...result,
      taskType: activeTask.value.taskType,
      paperDraft: result.paperDraft ? JSON.parse(JSON.stringify(result.paperDraft)) : null,
    }
    await loadTasks()
    message.success('任务结果已保存')
  } catch (error) {
    message.error(error.message || '保存失败')
  } finally {
    saving.value = false
  }
}

// 确认任务
async function handleConfirmTask() {
  if (!canConfirmTaskPermission.value || !activeTask.value) return
  confirming.value = true
  try {
    if (activeTask.value.status === 'completed') {
      await handleSaveTask()
    }
    let result
    if (activeTask.value.taskType === 'paper_assembly') {
      result = await confirmAiPaperAssemblyTask(activeTask.value.id)
    } else {
      result = await confirmAiPaperDocumentGenerationTask(activeTask.value.id)
    }
    activeTask.value = {
      ...result,
      taskType: activeTask.value.taskType,
      paperDraft: result.paperDraft ? JSON.parse(JSON.stringify(result.paperDraft)) : null,
    }
    await loadTasks()
    message.success(`试卷已入库，试卷 ID：${result.confirmedPaperId}`)
  } catch (error) {
    message.error(error.message || '确认失败')
  } finally {
    confirming.value = false
  }
}

// 选择/取消选择任务
function toggleSelect(taskId, event) {
  const checked = event.target.checked
  if (checked) {
    if (!selectedTaskIds.value.includes(taskId)) {
      selectedTaskIds.value.push(taskId)
    }
  } else {
    selectedTaskIds.value = selectedTaskIds.value.filter(id => id !== taskId)
  }
}

// 批量删除
async function handleBatchDelete() {
  if (!selectedTaskIds.value.length) return
  const shouldDelete = await new Promise(resolve => {
    Modal.confirm({
      title: '确认删除任务',
      content: `确定删除选中的 ${selectedTaskIds.value.length} 个任务吗？此操作不可恢复。`,
      okText: '确定删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => resolve(true),
      onCancel: () => resolve(false),
    })
  })
  if (!shouldDelete) return
  
  batchDeleting.value = true
  let successCount = 0
  let failCount = 0
  
  for (const taskId of selectedTaskIds.value) {
    const task = taskList.value.find(t => t.id === taskId)
    if (!task) continue
    try {
      if (task.taskType === 'paper_assembly') {
        await deleteAiPaperAssemblyTask(taskId)
      } else if (task.taskType === 'paper_generation') {
        await deleteAiPaperGenerationTask(taskId)
      } else {
        await deleteAiPaperDocumentGenerationTask(taskId)
      }
      successCount++
    } catch {
      failCount++
    }
  }
  
  selectedTaskIds.value = []
  await loadTasks()
  
  if (failCount === 0) {
    message.success(`成功删除 ${successCount} 个任务`)
  } else {
    message.warning(`成功删除 ${successCount} 个，${failCount} 个失败`)
  }
  batchDeleting.value = false
}

// 批量确认
async function handleBatchConfirm() {
  const confirmableIds = taskList.value
    .filter(t => selectedTaskIds.value.includes(t.id) && t.status === 'completed')
    .map(t => t.id)
  
  if (!confirmableIds.length) {
    message.warning('没有可确认的任务')
    return
  }
  
  batchConfirming.value = true
  let successCount = 0
  let failCount = 0
  
  for (const taskId of confirmableIds) {
    const task = taskList.value.find(t => t.id === taskId)
    if (!task) continue
    try {
      if (task.taskType === 'paper_assembly') {
        await confirmAiPaperAssemblyTask(taskId)
      } else {
        await confirmAiPaperDocumentGenerationTask(taskId)
      }
      successCount++
    } catch (error) {
      failCount++
    }
  }
  
  selectedTaskIds.value = []
  await loadTasks()
  
  if (failCount === 0) {
    message.success(`成功确认 ${successCount} 个任务`)
  } else {
    message.warning(`成功确认 ${successCount} 个，${failCount} 个失败`)
  }
  batchConfirming.value = false
}

// 单个删除
async function handleDeleteSingleTask(task) {
  const shouldDelete = await new Promise(resolve => {
    Modal.confirm({
      title: '确认删除任务',
      content: `确定删除任务"${task.taskName}"吗？`,
      okText: '确定删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => resolve(true),
      onCancel: () => resolve(false),
    })
  })
  if (!shouldDelete) return
  
  try {
    if (task.taskType === 'paper_assembly') {
      await deleteAiPaperAssemblyTask(task.id)
    } else if (task.taskType === 'paper_generation') {
      await deleteAiPaperGenerationTask(task.id)
    } else {
      await deleteAiPaperDocumentGenerationTask(task.id)
    }
    message.success('已删除')
    if (activeTask.value?.id === task.id) {
      activeTask.value = null
      detailDrawerVisible.value = false
    }
    await loadTasks()
  } catch (error) {
    message.error(error.message || '删除失败')
  }
}

// 单个确认
async function handleConfirmSingleTask(task) {
  try {
    await selectTaskDirect(task)
    await handleConfirmTask()
  } catch (error) {
    message.error(error.message || '确认失败')
  }
}

async function selectTaskDirect(task) {
  await loadTaskDetail(task.id, task.taskType)
}

// 题目编辑
function openEditQuestion(question, index) {
  if (!canUpdateTaskPermission.value) return
  editingQuestion.value = { ...question }
  editingQuestionIndex.value = index
  questionModalOpen.value = true
}

function openCreateQuestion() {
  if (!canUpdateTaskPermission.value) return
  editingQuestion.value = { origin: 'manual', difficulty: 3, score: 2 }
  editingQuestionIndex.value = -1
  questionModalOpen.value = true
}

function handleSubmitQuestion(question) {
  if (!activeTask.value?.paperDraft) return
  const nextQuestions = [...(activeTask.value.paperDraft.questions || [])]
  if (editingQuestionIndex.value > -1) {
    nextQuestions.splice(editingQuestionIndex.value, 1, question)
  } else {
    nextQuestions.push(question)
  }
  activeTask.value.paperDraft.questions = sortQuestionsByType(nextQuestions)
  editingQuestion.value = null
  editingQuestionIndex.value = -1
}

// 监听 Tab 切换
watch(activeTab, (val) => {
  if (val === 'list') {
    listDrawerVisible.value = true
    loadTasks()
  }
})

onMounted(() => {
  loadPoliceTypeOptions()
  loadTasks()
})
</script>

<style scoped>
/* ================= 页面基础布局 ================= */
.ai-paper-page {
  min-height: 100vh;
  background-color: #F8FAFC;
  display: flex;
  flex-direction: column;
}

/* 顶栏 */
.page-header {
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 40px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-title {
  flex: 1;
}

.header-h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: -0.01em;
  margin: 0;
}

.header-desc {
  color: #64748b;
  margin: 6px 0 0;
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 内容区 */
.page-content {
  flex: 1;
  overflow-y: auto;
  padding: 0px 0px !important;
}

.content-container {
  width: 100%;
  margin: 0 auto  !important;;
}

/* 页面标题 */
.page-title-section {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: -0.01em;
  margin: 0;
}

.page-subtitle {
  color: #64748b;
  margin-top: 6px;
  font-size: 14px;
}

/* 主卡片 */
.main-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  padding: 32px 40px;
  width: 100%;
  margin: 0 auto !important;
}

/* 分隔线 */
.divider {
  height: 1px;
  background: #f1f5f9;
  margin: 32px 0;
}

/* ================= 基础设置区 ================= */
.basic-section {
  padding-bottom: 32px;
  border-bottom: 1px solid #f1f5f9;
}

.section-title {
  font-size: 16px;
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title.no-margin {
  margin-bottom: 0;
}

.section-indicator {
  width: 4px;
  height: 16px;
  background: #3b82f6;
  border-radius: 2px;
}

.section-indicator.indigo {
  background: #6366f1;
}

.section-indicator.dark {
  background: #334155;
}

.section-indicator.light-indigo {
  background: #818cf8;
}

.basic-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 32px;
}

.form-field {
  display: flex;
  flex-direction: column;
}

.form-field:nth-child(1) {
  grid-column: span 4;
}

.form-field:nth-child(2) {
  grid-column: span 4;
}

.form-field-sm {
  grid-column: span 2 !important;
}

.field-label {
  font-size: 14px;
  font-weight: 500;
  color: #475569;
  margin-bottom: 8px;
}

.field-label.required::after {
  content: '*';
  color: #ef4444;
  margin-left: 4px;
}

.field-tip {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 8px;
  line-height: 1.5;
}

/* 单行输入框极简样式 */
.input-minimal {
  background: transparent !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 6px !important;
  padding: 10px 12px !important;
  font-size: 14px !important;
  color: #1e293b !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}

.input-minimal:hover {
  border-color: #cbd5e1 !important;
}

.input-minimal:focus {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
  outline: none !important;
}

.input-minimal::placeholder {
  color: #94a3b8 !important;
}

/* 当 input-minimal 用于 select 时，外层不加边框（由内部 ant-select-selector 控制） */
.input-select.input-minimal {
  border: none !important;
  padding: 0 !important;
}

/* 修复多选 select 样式 - 去除外层边框 */
:deep(.ant-select) {
  background: transparent !important;
}

:deep(.ant-select:not(.ant-select-disabled)) {
  background: transparent !important;
}

:deep(.ant-select-selector) {
  background: transparent !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 6px !important;
  padding: 10px 12px !important;
  box-shadow: none !important;
  height: auto !important;
  min-height: 40px !important;
}

:deep(.ant-select:hover:not(.ant-select-disabled) .ant-select-selector) {
  border-color: #cbd5e1 !important;
}

:deep(.ant-select-focused:not(.ant-select-disabled) .ant-select-selector) {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

:deep(.ant-select-arrow) {
  color: #94a3b8 !important;
  right: 12px !important;
}

:deep(.ant-select-selection-search-input) {
  height: auto !important;
  margin: 0 !important;
}

/* 多选 select（限制知识点）特殊处理 */
:deep(.ant-select-multiple .ant-select-selector) {
  padding: 4px 12px !important;
}

:deep(.ant-select-multiple .ant-select-selection-item) {
  background: #eff6ff !important;
  border: 1px solid #bfdbfe !important;
  border-radius: 4px !important;
  color: #3b82f6 !important;
  line-height: 20px !important;
}

:deep(.ant-select-multiple .ant-select-selection-item-remove) {
  color: #3b82f6 !important;
}

:deep(.ant-select-multiple .ant-select-selection-item-remove:hover) {
  color: #2563eb !important;
}

:deep(.ant-select-multiple .ant-select-selection-search) {
  margin-inline-end: 4px !important;
}

:deep(.ant-select-multiple .ant-select-selection-search-input) {
  height: auto !important;
}

.textarea-minimal {
  min-height: 120px !important;
  resize: vertical !important;
  background: transparent !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 6px !important;
  padding: 10px 12px !important;
  line-height: 1.6 !important;
}

.textarea-minimal:hover {
  border-color: #cbd5e1 !important;
}

.textarea-minimal:focus-within {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

:deep(.ant-input-textarea textarea) {
  background: transparent !important;
}

/* ================= 核心业务区 ================= */
.core-grid {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: 48px;
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
}

/* ================= 模式选择卡片 ================= */
.mode-section {
  margin-bottom: 0;
}

.mode-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.mode-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background: #ffffff;
}

.mode-card:hover {
  border-color: #cbd5e1;
  background: #f8fafc;
}

.mode-card.active {
  border-color: #3b82f6;
  background: #eff6ff;
  box-shadow: 0 0 0 1px #3b82f6;
}

.mode-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #f1f5f9;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  transition: all 0.2s;
}

.mode-icon.active {
  background: #dbeafe;
  color: #2563eb;
}

.mode-title {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 4px;
}

.mode-desc {
  font-size: 12px;
  color: #64748b;
}

/* ================= 数据源面板 ================= */
.source-section {
  margin-bottom: 0;
}

.source-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.toggle-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #f1f5f9;
}

.toggle-content {
  flex: 1;
}

.toggle-label-text {
  font-size: 14px;
  font-weight: 500;
  color: #475569;
}

.toggle-desc {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 2px;
  margin-bottom: 0;
}

.template-link {
  color: #3b82f6;
  text-decoration: underline;
  margin-left: 8px;
}

.template-link:hover {
  color: #2563eb;
}

/* 上传区域 */
.upload-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.upload-zone {
  border: 1px dashed #cbd5e1;
  border-radius: 4px;
  padding: 6px 10px;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s;
  background: #f8fafc;
}

.upload-zone:hover {
  border-color: #3b82f6;
  background: #f8fafc;
}

.upload-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #eff6ff;
  color: #3b82f6;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.upload-icon svg {
  width: 12px;
  height: 12px;
}

.upload-text {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.upload-title {
  font-size: 11px;
  font-weight: 500;
  color: #1e293b;
}

.upload-hint {
  font-size: 11px;
  color: #94a3b8;
}

.file-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  padding: 2px 6px;
  background: #eff6ff;
  border-radius: 3px;
  color: #3b82f6;
  font-size: 11px;
  height: 24px;
}

.file-info-content {
  display: flex;
  align-items: center;
  gap: 4px;
  overflow: hidden;
}

.file-info svg {
  width: 12px;
  height: 12px;
}

.file-name {
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-remove {
  cursor: pointer;
  color: #94a3b8;
  font-size: 12px;
  line-height: 1;
}

.file-remove:hover {
  color: #ef4444;
}

/* ================= 题型配置区 ================= */
.type-section {
  margin-bottom: 0;
}

.type-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.type-summary {
  display: flex;
  gap: 24px;
  font-size: 14px;
  color: #64748b;
}

.summary-num {
  font-weight: 600;
  font-style: normal;
  color: #1e293b;
  font-size: 18px;
}

.summary-num.blue {
  color: #3b82f6;
}

/* 题型表格 */
.type-table {
  border: 1px solid #f1f5f9;
  border-radius: 8px;
  overflow: hidden;
}

.type-table-head {
  display: grid;
  grid-template-columns: 120px repeat(3, 1fr) 80px;
  gap: 8px;
  padding: 12px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #f1f5f9;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.type-row {
  display: grid;
  grid-template-columns: 120px repeat(3, 1fr) 80px;
  gap: 8px;
  padding: 16px 16px;
  border-bottom: 1px solid #f1f5f9;
  align-items: center;
  transition: background 0.15s;
}

.type-row:hover {
  background: #fafbfc;
}

.type-row.last {
  border-bottom: none;
}

.col-type {
  display: flex;
  align-items: center;
  gap: 10px;
}

.type-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.type-dot.blue { background: #3b82f6; }
.type-dot.purple { background: #8b5cf6; }
.type-dot.amber { background: #f59e0b; }

.type-name {
  font-weight: 500;
  color: #475569;
  font-size: 14px;
}

.col-qty,
.col-score,
.col-diff {
  display: flex;
  justify-content: center;
}

.col-subtotal {
  text-align: right;
  font-weight: 500;
  color: #1e293b;
  font-size: 14px;
}

.type-input {
  width: 64px !important;
  text-align: center !important;
  border: none !important;
  border-bottom: 1px solid #e2e8f0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  padding: 4px 0 !important;
}

.type-input:focus {
  border-bottom-color: #3b82f6 !important;
  box-shadow: none !important;
}

.type-select {
  width: 100% !important;
  max-width: 100px !important;
  border: none !important;
  border-bottom: 1px solid #e2e8f0 !important;
  border-radius: 0 !important;
  background: transparent !important;
  padding: 4px 0 !important;
}

.type-select:focus {
  border-bottom-color: #3b82f6 !important;
  box-shadow: none !important;
}

.col-diff.dim {
  opacity: 0.4;
  pointer-events: none;
}

/* ================= AI指令区 ================= */
.ai-section {
  flex: 1;
}

.ai-tag {
  margin-left: 8px;
  font-size: 10px;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.ai-textarea {
  min-height: 140px !important;
  position: relative;
}

/* ================= 任务列表 ================= */
.task-list-page {
  width: 100%;
}

.task-filter {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.task-list {
  max-height: calc(100vh - 280px);
  overflow-y: auto;
}

.task-item {
  cursor: pointer;
  border-radius: 8px;
  padding: 12px !important;
  margin-bottom: 8px;
  border: 1px solid #e2e8f0;
  transition: all 0.15s;
  background: #ffffff;
}

.task-item:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.task-item.active {
  background: #eff6ff;
  border-color: #93c5fd;
}

.task-item.selected {
  background: #f0f9ff;
  border-color: #38bdf8;
}

.task-checkbox {
  flex-shrink: 0;
  margin-right: 12px;
}

/* 选中计数提示 */
.selection-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
  border-radius: 6px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #2563eb;
  font-weight: 500;
}

/* ================= 详情区 ================= */
.detail-section {
  margin-top: 24px;
}

.detail-section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12px;
}

.detail-actions {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f1f5f9;
}

/* ================= 响应式 ================= */
@media (max-width: 1200px) {
  .core-grid {
    grid-template-columns: 1fr;
    gap: 32px;
  }

  .basic-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .form-field:nth-child(1),
  .form-field:nth-child(2) {
    grid-column: span 1;
  }

  .form-field-sm {
    grid-column: span 1 !important;
  }
}

@media (max-width: 768px) {
  .page-content {
    padding: 0px 0px !important;
  }

  .main-card {
    padding: 24px 16px;
  }

  .mode-cards {
    grid-template-columns: 1fr;
  }

  .type-table-head,
  .type-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .col-subtotal {
    text-align: left;
  }
}
</style>
