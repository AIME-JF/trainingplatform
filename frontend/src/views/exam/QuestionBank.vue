<template>
  <div class="question-bank-page">
    <!-- 主体内容 -->
    <main class="main-content">
      <div class="content-wrapper">

        <!-- 1. 二级导航与快捷操作入口 -->
        <div class="sub-nav-bar">
          <div class="sub-nav-left">
            <span
              :class="['sub-nav-item', { active: activeNav === 'bank' }]"
              @click="switchNav('bank')"
            >
              题库管理
            </span>
          </div>
        </div>

        <!-- 2. 统一的大边框容器 -->
        <div class="main-container">
          <template v-if="activeNav === 'bank'">

          <!-- 第一层：操作与搜索过滤 -->
          <div class="toolbar-row">
            <template v-if="selectedFolderId">
              <div class="toolbar-left">
                <button class="btn-aux" @click="handleBackToFolders">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
                  返回题库列表
                </button>
                <span class="toolbar-title">{{ selectedFolderName }}（共 {{ questionList.length }} 道题目）</span>
              </div>
              <div class="toolbar-right">
                <!-- 筛选控件 -->
                <a-input-search v-model:value="pickerSearch" placeholder="搜索题干" style="width:180px" allow-clear />
                <a-select v-model:value="pickerType" style="width:120px">
                  <a-select-option value="all">全部题型</a-select-option>
                  <a-select-option value="single">单选题</a-select-option>
                  <a-select-option value="multi">多选题</a-select-option>
                  <a-select-option value="judge">判断题</a-select-option>
                </a-select>
                <div class="divider-v"></div>
                <a-dropdown v-if="!pickMode">
                  <button type="button" class="btn-primary upload-trigger-btn">
                    新增/导入题目
                    <DownOutlined class="upload-trigger-icon" />
                  </button>
                  <template #overlay>
                    <a-menu @click="handleUploadMenuClick">
                      <a-menu-item key="manual">手动录入题目</a-menu-item>
                      <a-menu-item key="document">按模板导入文档</a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
                <button v-if="!pickMode" class="btn-primary" @click="enterPickMode">
                  从题库选题
                </button>
                <template v-else>
                  <span class="pick-hint">已选 {{ pickSelectedKeys.length }} 道</span>
                  <button class="btn-aux" @click="exitPickMode">取消</button>
                  <button class="btn-primary" :disabled="pickSelectedKeys.length === 0" @click="confirmPick">加入试卷</button>
                </template>
              </div>
            </template>
            <template v-else>
              <div class="toolbar-left">
                <a-dropdown>
                  <button type="button" class="btn-primary upload-trigger-btn">
                    新增/导入题目
                    <DownOutlined class="upload-trigger-icon" />
                  </button>
                  <template #overlay>
                    <a-menu @click="handleUploadMenuClick">
                      <a-menu-item key="manual">手动录入题目</a-menu-item>
                      <a-menu-item key="document">按模板导入文档</a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
                <button v-if="canUseAiQuestion" class="btn-primary" @click="goToAiQuestion">
                  AI 生成题库
                </button>
                <div class="search-wrapper">
                  <svg class="search-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
                  <input type="text" class="input-minimal" v-model="searchText" placeholder="请输入关键字搜索..." @input="handleSearch">
                </div>
              </div>
              <div class="toolbar-right">
                <a-select
                  v-model="quickSelectFolderId"
                  placeholder="选择题库操作..."
                  style="width: 180px"
                  allow-clear
                >
                  <a-select-option v-for="folder in folderListForSelect" :key="folder.id" :value="folder.id">
                    {{ folder.name }}
                  </a-select-option>
                </a-select>
                <select class="input-minimal filter-select" v-model="filterCategory">
                  <option value="">题库分类 (全部)</option>
                  <option v-for="category in categoryOptions" :key="category" :value="category">
                    {{ category }}
                  </option>
                </select>
              </div>
            </template>
          </div>

          <!-- 第二层：表格数据 -->
          <div class="table-wrapper">
            <!-- 文件夹列表视图 -->
            <table v-if="!selectedFolderId" class="data-table">
              <thead>
                <tr>
                  <th class="col-check">
                    <input type="checkbox" class="custom-checkbox" :checked="isAllSelected" @change="toggleSelectAll">
                  </th>
                  <th class="col-index">序号</th>
                  <th class="col-name">题库名称</th>
                  <th class="col-publisher">发布人</th>
                  <th class="col-category text-center">题库分类</th>
                  <th class="col-paper text-center">试卷数</th>
                  <th class="col-course text-center">关联课程</th>
                  <th class="col-questions text-center">题目数量</th>
                  <th class="col-status text-center">状态</th>
                  <th class="col-time">添加时间</th>
                  <th class="col-action text-right">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in displayedList" :key="item.id" class="table-row">
                  <td class="col-check">
                    <input type="checkbox" class="custom-checkbox" :checked="selectedIds.includes(item.id)" @change="toggleSelect(item.id)">
                  </td>
                  <td class="col-index">{{ (pagination.current - 1) * pagination.pageSize + index + 1 }}</td>
                  <td class="col-name">
                    <span class="name-text" :class="{ 'is-system': item.isSystem }">{{ item.displayName || item.name }}</span>
                    <span v-if="item.isSystem" class="badge-system">System</span>
                  </td>
                  <td class="col-publisher">{{ item.creatorName || '-' }}</td>
                  <td class="col-category text-center">{{ item.category }}</td>
                  <td class="col-paper text-center">{{ item.paperCount }}</td>
                  <td class="col-course text-center">{{ item.courseName || '未关联' }}</td>
                  <td class="col-questions text-center">
                    <button class="question-count-btn" @click.stop="handleViewQuestions(item)">{{ item.questionCount }} 题</button>
                  </td>
                  <td class="col-status text-center">
                    <span class="status-text">{{ item.statusText }}</span>
                  </td>
                  <td class="col-time">{{ item.createdAt }}</td>
                  <td class="col-action text-right">
                    <div class="action-btns">
                      <button class="btn-link" @click="handleViewQuestions(item)">查看题目</button>
                      <button class="btn-link" @click="openEditFolderModal(item)" :disabled="item.isSystem">编辑</button>
                      <button class="btn-link btn-link-danger" @click="handleDeleteFolder(item)" :disabled="item.isSystem">删除</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="displayedList.length === 0">
                  <td colspan="11" class="empty-row">暂无数据</td>
                </tr>
              </tbody>
            </table>

            <!-- 文件夹内题目列表视图 -->
            <table v-else class="data-table">
              <thead>
                <tr>
                  <th v-if="pickMode" class="col-check">
                    <input type="checkbox" class="custom-checkbox" :checked="isAllPickSelected" @change="togglePickSelectAll">
                  </th>
                  <th class="col-index">序号</th>
                  <th class="col-type text-center">题型</th>
                  <th class="col-content">题干</th>
                  <th class="col-answer">答案</th>
                  <th class="col-difficulty text-center">难度</th>
                  <th class="col-time">添加时间</th>
                  <th class="col-action text-center">操作</th>
                </tr>
              </thead>
              <tbody v-if="questionLoading">
                <tr>
                  <td :colspan="pickMode ? 8 : 7" class="empty-row">加载中...</td>
                </tr>
              </tbody>
              <tbody v-else>
                <tr v-for="(q, index) in displayedQuestionList" :key="q.id" class="table-row">
                  <td v-if="pickMode" class="col-check">
                    <input type="checkbox" class="custom-checkbox" :checked="pickSelectedKeys.includes(q.id)" @change="togglePickSelect(q.id)">
                  </td>
                  <td class="col-index">{{ (questionPagination.current - 1) * questionPagination.pageSize + index + 1 }}</td>
                  <td class="col-type text-center">
                    <span :class="['tag-pill', typeTagColors[q.type]]">{{ typeLabels[q.type] }}</span>
                  </td>
                  <td class="col-content">
                    <span class="name-text">{{ q.content }}</span>
                    <div v-if="q.options && q.options.length > 0" class="options-preview">
                      <span v-for="opt in q.options.slice(0,4)" :key="opt.key" class="option-tag">{{ opt.key }}. {{ opt.text }}</span>
                    </div>
                  </td>
                  <td class="col-answer">
                    <span class="answer-text">{{ formatAnswer(q) }}</span>
                  </td>
                  <td class="col-difficulty text-center">
                    <span class="difficulty-badge">{{ q.difficulty || 1 }}</span>
                  </td>
                  <td class="col-time">{{ q.createdAt || '-' }}</td>
                  <td class="col-action text-center">
                    <div class="action-btns">
                      <button class="btn-link" @click="handleEditQuestion(q)">编辑</button>
                      <button class="btn-link" @click="handleMoveQuestion(q)">移动</button>
                      <button class="btn-link btn-link-danger" @click="handleDeleteQuestion(q)">删除</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="questionList.length === 0">
                  <td :colspan="pickMode ? 8 : 7" class="empty-row">该题库暂无题目</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 第三层：说明与批量操作 -->
          <div class="footer-area">
            <!-- 说明文字 -->
            <div class="notice-area">
              <svg class="notice-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
              <div class="notice-text">
                <p>说明：1.综合题库为默认题库，不支持编辑、删除和导出等操作，请谨慎使用</p>
                <p class="mt-4">2.被用于试卷的题库和关联课后练习的题库不能删除</p>
              </div>
            </div>

            <div class="footer-divider"></div>

            <!-- 批量操作与分页 -->
            <div class="footer-actions">
              <!-- 题库列表视图 -->
              <template v-if="!selectedFolderId">
                <div class="footer-left">
                  <label class="checkbox-label">
                    <input type="checkbox" class="custom-checkbox" :checked="isAllSelected" @change="toggleSelectAll">
                    <span>全选</span>
                  </label>
                  <div class="divider-v"></div>
                  <div class="batch-ops">
                    <span class="batch-label">批量操作:</span>
                    <button class="btn-batch btn-batch-danger" @click="handleBatchDelete">批量删除</button>
                  </div>
                </div>

                <div class="footer-right">
                  <div class="page-size-selector">
                    <span class="page-size-label">每页显示：</span>
                    <select class="page-size-select" :value="pagination.pageSize" @change="handlePageSizeChange(Number($event.target.value))">
                      <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}条</option>
                    </select>
                  </div>
                  <div class="page-info">
                    共 {{ pagination.total }} 条记录
                  </div>
                  <div class="pagination-btns">
                    <button class="page-btn" :disabled="pagination.current <= 1" @click="changePage(pagination.current - 1)">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/></svg>
                    </button>
                    <button v-for="page in visiblePages" :key="page" class="page-btn" :class="{ 'page-btn-active': page === pagination.current }" @click="changePage(page)">{{ page }}</button>
                    <button class="page-btn" :disabled="pagination.current >= totalPages" @click="changePage(pagination.current + 1)">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>
                    </button>
                  </div>
                </div>
              </template>

              <!-- 题目列表视图 -->
              <template v-else>
                <div class="footer-left">
                  <!-- 空白占位 -->
                </div>

                <div class="footer-right">
                  <div class="page-size-selector">
                    <span class="page-size-label">每页显示：</span>
                    <select class="page-size-select" :value="questionPagination.pageSize" @change="handleQuestionPageSizeChange(Number($event.target.value))">
                      <option v-for="size in pageSizeOptions" :key="size" :value="size">{{ size }}条</option>
                    </select>
                  </div>
                  <div class="page-info">
                    共 {{ questionPagination.total }} 道题目
                  </div>
                  <div class="pagination-btns">
                    <button class="page-btn" :disabled="questionPagination.current <= 1" @click="changeQuestionPage(questionPagination.current - 1)">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7"/></svg>
                    </button>
                    <button v-for="page in questionVisiblePages" :key="page" class="page-btn" :class="{ 'page-btn-active': page === questionPagination.current }" @click="changeQuestionPage(page)">{{ page }}</button>
                    <button class="page-btn" :disabled="questionPagination.current >= questionTotalPages" @click="changeQuestionPage(questionPagination.current + 1)">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 5l7 7-7 7"/></svg>
                    </button>
                  </div>
                </div>
              </template>
            </div>
          </div>
          </template>
        </div>
      </div>
    </main>

    <!-- 新建/编辑题库弹窗 -->
    <a-modal
      v-model:open="folderFormModalVisible"
      :title="editingFolderId ? '编辑题库' : '添加题库'"
      @ok="handleFolderSubmit"
      @cancel="resetFolderFormModal"
      width="520px"
    >
      <a-form :model="folderForm" layout="vertical">
        <a-form-item label="题库名称" :rules="[{ required: true, message: '请输入题库名称' }]">
          <a-input v-model:value="folderForm.name" placeholder="请输入题库名称" :maxlength="100" />
        </a-form-item>
        <a-form-item label="题库分类">
          <a-auto-complete
            v-model:value="folderForm.category"
            placeholder="请选择或输入新分类"
            :options="categorySelectOptions"
            allow-clear
          />
        </a-form-item>
        <a-form-item label="关联课程">
          <a-select v-model:value="folderForm.courseId" placeholder="不关联课程时仅自己可见" allow-clear show-search option-filter-prop="label">
            <a-select-option v-for="item in courseOptions" :key="item.id" :value="item.id" :label="item.title">
              {{ item.title }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="editingFolderId" label="移动到">
          <a-tree-select
            v-model:value="folderForm.parentId"
            :tree-data="folderTreeData"
            placeholder="根目录（不移动）"
            allow-clear
            tree-default-expand-all
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 移动单个题目弹窗 -->
    <a-modal
      v-model:open="moveQuestionModalVisible"
      title="移动题目"
      @ok="handleMoveQuestionConfirm"
    >
      <a-form layout="vertical">
        <a-form-item label="选择目标文件夹">
          <a-select v-model:value="moveQuestionTargetFolderId" placeholder="请选择目标文件夹">
            <a-select-option :value="null">根目录（移出文件夹）</a-select-option>
            <a-select-option v-for="folder in allFolderList" :key="folder.id" :value="folder.id">
              {{ folder.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 新增/编辑题目弹窗 -->
    <question-form-modal
      v-model:open="modalOpen"
      :title="editingQuestion ? '编辑题目' : '新增题目'"
      :question="editingQuestion"
      :police-type-options="policeTypeOptions"
      :default-folder-id="selectedFolderId"
      :show-bank-fields="!editingQuestion"
      :bank-name="manualQuestionDraft.bankName"
      :bank-category="manualQuestionDraft.bankCategory"
      :bank-course-id="manualQuestionDraft.bankCourseId"
      :bank-name-options="folderNameSelectOptions"
      :bank-category-options="categorySelectOptions"
      :course-options="courseOptions"
      @submit="handleSubmitQuestion"
    />

    <!-- 选择或新建题库弹窗 -->
    <a-modal
      v-model:open="targetFolderModalVisible"
      :title="targetFolderModalTitle"
      :confirm-loading="targetFolderSubmitting"
      ok-text="继续"
      @ok="handleTargetFolderSubmit"
      @cancel="resetTargetFolderModal"
      width="560px"
    >
      <a-form :model="targetFolderForm" layout="vertical">
        <a-form-item label="题库名称" required>
          <a-auto-complete
            v-model:value="targetFolderForm.name"
            placeholder="选择已有题库，或直接输入新题库名称"
            :options="folderNameSelectOptions"
            allow-clear
          />
        </a-form-item>
        <a-alert
          v-if="matchedTargetFolder"
          type="info"
          show-icon
          :message="`将使用已有题库：${matchedTargetFolder.name}`"
          :description="matchedTargetFolder.courseName ? `关联课程：${matchedTargetFolder.courseName}` : '未关联课程，仅自己可见'"
          style="margin-bottom: 16px"
        />
        <template v-else>
          <a-alert
            type="warning"
            show-icon
            message="未找到同名题库，将自动创建新题库后继续"
            description="可在下方补充题库分类与关联课程；不关联课程时仅自己可见。"
            style="margin-bottom: 16px"
          />
          <a-form-item label="题库分类">
            <a-auto-complete
              v-model:value="targetFolderForm.category"
              placeholder="可输入新的题库分类"
              :options="categorySelectOptions"
              allow-clear
            />
          </a-form-item>
          <a-form-item label="关联课程">
            <a-select
              v-model:value="targetFolderForm.courseId"
              placeholder="不关联课程时仅自己可见"
              allow-clear
              show-search
              option-filter-prop="label"
            >
              <a-select-option v-for="item in courseOptions" :key="item.id" :value="item.id" :label="item.title">
                {{ item.title }}
              </a-select-option>
            </a-select>
          </a-form-item>
        </template>
      </a-form>
    </a-modal>

    <!-- 批量上传题目弹窗 -->
    <a-modal
      v-model:open="batchUploadModalVisible"
      title="批量上传题目"
      width="600px"
      :confirm-loading="batchUploadLoading"
      @ok="handleBatchUpload"
    >
      <div class="batch-upload-content">
        <div class="upload-tip">
          <p>请上传结构化题目文件，目前支持以下格式：</p>
          <ul>
            <li>JSON 文件（.json）</li>
          </ul>
            <p class="mt-4">如需上传 Word、PDF、Excel、TXT 等文档并按模板直接导入题库，请使用“新增/导入题目”中的“按模板导入文档”。</p>
          <p class="mt-4">文件格式示例（JSON）：</p>
          <pre class="code-block">{{ batchUploadExample }}</pre>
        </div>
        <div class="upload-area" @click="triggerFileInput">
          <input
            ref="fileInputRef"
            type="file"
            accept=".xlsx,.xls,.json"
            style="display:none"
            @change="handleFileSelect"
          >
          <div v-if="!selectedFile" class="upload-placeholder">
            <svg class="w-12 h-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
            </svg>
            <p class="mt-2">点击选择文件或拖拽文件到此处</p>
          </div>
          <div v-else class="selected-file">
            <svg class="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span class="ml-2">{{ selectedFile.name }}</span>
            <span class="ml-2 text-gray-500">({{ formatFileSize(selectedFile.size) }})</span>
          </div>
        </div>
        <div v-if="batchPreviewQuestions.length > 0" class="preview-section">
          <h4>预览（共 {{ batchPreviewQuestions.length }} 道题目）</h4>
          <div class="preview-list">
            <div v-for="(q, idx) in batchPreviewQuestions.slice(0, 10)" :key="idx" class="preview-item">
              <span class="preview-type">{{ typeLabels[q.type] || q.type }}</span>
              <span class="preview-content">{{ q.content?.substring(0, 50) }}{{ q.content?.length > 50 ? '...' : '' }}</span>
            </div>
            <div v-if="batchPreviewQuestions.length > 10" class="preview-more">
              还有 {{ batchPreviewQuestions.length - 10 }} 道题目...
            </div>
          </div>
        </div>
      </div>
    </a-modal>

    <!-- 模板文档导入弹窗 -->
    <a-modal
      v-model:open="documentImportModalVisible"
      title="模板导入题库"
      width="1120px"
      class="document-import-modal"
      :confirm-loading="documentImportLoading"
      ok-text="同步导入"
      @ok="handleDocumentImportSubmit"
      @cancel="resetDocumentImportModal"
    >
      <a-form :model="documentImportForm" layout="vertical">
        <div class="document-import-layout">
          <div class="document-import-panel document-info-panel">
            <div class="document-basic-grid">
              <a-form-item label="题库名称" required class="document-field-name">
                <a-auto-complete
                  v-model:value="documentImportForm.bankName"
                  placeholder="选择已有题库，或直接输入新题库名称"
                  :options="folderNameSelectOptions"
                  allow-clear
                />
              </a-form-item>
              <a-form-item label="题库分类">
                <a-auto-complete
                  v-model:value="documentImportForm.bankCategory"
                  placeholder="可输入新分类"
                  :options="categorySelectOptions"
                  allow-clear
                />
              </a-form-item>
              <a-form-item label="关联课程">
                <a-select
                  v-model:value="documentImportForm.bankCourseId"
                  allow-clear
                  show-search
                  option-filter-prop="label"
                  placeholder="不关联课程时仅自己可见"
                >
                  <a-select-option v-for="item in courseOptions" :key="item.id" :value="item.id" :label="item.title">
                    {{ item.title }}
                  </a-select-option>
                </a-select>
              </a-form-item>
            </div>
            <div class="upload-tip document-upload-tip">
              <p>请按模板整理题目后上传，系统会先同步提取文档文本，再按模板规则直接导入题库。</p>
              <p class="mt-4">
                <a :href="documentTemplateUrl" download class="template-link">下载题目模板</a>
                <span class="template-hint">支持 `.txt/.doc/.docx/.pdf/.xls/.xlsx/.csv`，推荐优先使用模板后另存为 Word 或 TXT 上传。</span>
              </p>
            </div>
          </div>

          <div class="document-import-panel document-result-panel">
            <a-form-item
              label="解析结果"
              extra="上传文档后会自动提取文本；如有识别偏差，可直接在这里微调后再提交。"
              class="document-result-field"
            >
              <a-textarea
                v-model:value="documentImportForm.sourceText"
                :rows="20"
                placeholder="请输入或上传文档后自动填充模板文本"
              />
            </a-form-item>
          </div>

          <div class="document-import-panel document-upload-panel">
            <a-form-item label="上传模板文档" class="document-upload-field">
              <input
                ref="documentFileInputRef"
                type="file"
                accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt"
                style="display:none"
                @change="handleDocumentFileSelect"
              >
              <div class="upload-area document-upload-area" @click="triggerDocumentFileInput">
                <div v-if="!documentImportForm.sourceMaterialName" class="upload-placeholder">
                  <svg class="w-12 h-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                  </svg>
                  <p class="mt-2">{{ documentParsing ? '文档解析中...' : '点击选择模板文档并同步解析' }}</p>
                </div>
                <div v-else class="selected-file">
                  <svg class="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                  </svg>
                  <span class="ml-2">{{ documentImportForm.sourceMaterialName }}</span>
                </div>
              </div>
            </a-form-item>
          </div>
        </div>
      </a-form>
    </a-modal>

  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DownOutlined } from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'
import { AI_QUESTION_PAGE_PERMISSIONS, QUESTION_BANK_PAGE_PERMISSIONS } from '@/constants/pagePermissions'
import { parseAiDocumentFile } from '@/api/ai'
import {
  batchCreateQuestions,
  createQuestion,
  createQuestionFolder,
  deleteQuestion,
  deleteQuestionFolder,
  getQuestions,
  getQuestionFolders,
  moveQuestionToFolder,
  updateQuestion,
  updateQuestionFolder,
} from '@/api/question'
import { getCourses } from '@/api/course'
import { getPoliceTypes } from '@/api/user'
import QuestionFormModal from './components/QuestionFormModal.vue'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

// ============ 导航 ============
const activeNav = ref('bank')

// ============ 搜索与筛选 ============
const searchText = ref('')
const filterCategory = ref('')
const filterDifficulty = ref('')

const typeLabels = { single: '单选题', multi: '多选题', judge: '判断题', gap: '填空题' }
const typeTagColors = { single: 'tag-blue', multi: 'tag-purple', judge: 'tag-orange', gap: 'tag-cyan' }
const canUseAiQuestion = computed(() => authStore.hasAnyPermission(AI_QUESTION_PAGE_PERMISSIONS))
const canManageQuestionBank = computed(() => authStore.hasAnyPermission([...QUESTION_BANK_PAGE_PERMISSIONS, ...AI_QUESTION_PAGE_PERMISSIONS]))

// ============ 题库列表数据 ============
const loading = ref(false)
const folderList = ref([])
const folderTreeSource = ref([])
const selectedIds = ref([])

// 文件夹内题目查看模式
const selectedFolderId = ref(null)
const selectedFolderName = ref('')
const questionList = ref([])
const questionLoading = ref(false)
const courseOptions = ref([])

// 题目筛选与选题模式
const pickerSearch = ref('')
const pickerType = ref('all')
const pickMode = ref(false)
const pickSelectedKeys = ref([])

// ============ 分页 ============
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })
const pageSizeOptions = [10, 20, 50]
const questionPagination = reactive({ current: 1, pageSize: 20, total: 0 })

// ============ 文件夹管理弹窗 ============
const folderFormModalVisible = ref(false)
const editingFolderId = ref(null)
const folderForm = reactive({ name: '', category: '', parentId: null, courseId: undefined })
const moveQuestionModalVisible = ref(false)
const moveQuestionTargetFolderId = ref(null)
const currentMovingQuestion = ref(null)
const targetFolderModalVisible = ref(false)
const targetFolderSubmitting = ref(false)
const targetFolderAction = ref('manual')
const targetFolderForm = reactive({ name: '', category: '', courseId: undefined })

// ============ 题目弹窗 ============
const modalOpen = ref(false)
const editingQuestion = ref(null)
const policeTypeOptions = ref([])
const manualQuestionDraft = reactive({
  bankName: '',
  bankCategory: '',
  bankCourseId: undefined,
})

// ============ 批量上传 ============
const batchUploadModalVisible = ref(false)
const batchUploadLoading = ref(false)
const selectedFile = ref(null)
const batchPreviewQuestions = ref([])
const fileInputRef = ref(null)
const quickSelectFolderId = ref(null)
const documentImportModalVisible = ref(false)
const documentImportLoading = ref(false)
const documentParsing = ref(false)
const documentFileInputRef = ref(null)
const documentImportForm = reactive({
  bankName: '',
  bankCategory: '',
  bankCourseId: undefined,
  sourceText: '',
  sourceMaterialName: '',
})
const documentTemplateUrl = '/trainingplatform/templates/question-document-import-template.txt'
const documentTemplatePreview = `题目1
题型：单选题
题干：请输入题干
A：选项A
B：选项B
C：选项C
D：选项D
答案：A
解析：请输入解析
难度：2
分值：2
知识点：知识点1, 知识点2
警种：治安
---
题目2
题型：判断题
题干：请输入题干
答案：正确
解析：请输入解析`
const batchUploadExample = JSON.stringify([
  {
    type: "single",
    content: "题目内容",
    options: [
      { key: "A", text: "选项A" },
      { key: "B", text: "选项B" },
      { key: "C", text: "选项C" },
      { key: "D", text: "选项D" }
    ],
    answer: "A",
    explanation: "解析",
    difficulty: 1
  }
], null, 2)

function appendMultilineValue(current, next) {
  if (!next) return current || ''
  return current ? `${current}\n${next}` : next
}

function normalizeDocumentLabel(label) {
  return String(label || '').trim().replace(/\s+/g, '')
}

function normalizeDocumentQuestionType(value) {
  const text = String(value || '').trim().toLowerCase()
  if (!text) return ''
  if (['single', '单选', '单选题'].includes(text)) return 'single'
  if (['multi', 'multiple', '多选', '多选题'].includes(text)) return 'multi'
  if (['judge', '判断', '判断题'].includes(text)) return 'judge'
  return ''
}

function normalizeDocumentAnswer(type, value) {
  const text = String(value || '').trim()
  if (type === 'judge') {
    if (['正确', '对', 'true', '是', 'a'].includes(text.toLowerCase())) return 'A'
    if (['错误', '错', 'false', '否', 'b'].includes(text.toLowerCase())) return 'B'
    return text || 'A'
  }

  const answers = text
    .split(/[,，、/\s]+/)
    .map(item => item.trim().toUpperCase())
    .filter(Boolean)

  if (type === 'multi') {
    return [...new Set(answers)]
  }
  return answers[0] || text.toUpperCase()
}

function normalizeQuestionOptions(type, options) {
  if (type === 'judge') {
    return [
      { key: 'A', text: '正确' },
      { key: 'B', text: '错误' },
    ]
  }

  return (options || [])
    .map((item, index) => ({
      key: String(item?.key || String.fromCharCode(65 + index)).trim().toUpperCase(),
      text: String(item?.text || '').trim(),
    }))
    .filter(item => item.key && item.text)
}

function resolvePoliceTypeIdByName(name) {
  const normalized = String(name || '').trim()
  if (!normalized) return undefined
  const exactMatch = policeTypeOptions.value.find(item => item.name === normalized)
  if (exactMatch) return exactMatch.id
  const fuzzyMatch = policeTypeOptions.value.find(item => item.name?.includes(normalized) || normalized.includes(item.name))
  return fuzzyMatch?.id
}

function finalizeDocumentQuestion(rawQuestion, index) {
  const type = normalizeDocumentQuestionType(rawQuestion.type)
  if (!type) {
    throw new Error(`第 ${index + 1} 道题缺少有效题型，请按模板填写“题型”`)
  }

  const content = String(rawQuestion.content || '').trim()
  if (!content) {
    throw new Error(`第 ${index + 1} 道题缺少题干`)
  }

  const options = normalizeQuestionOptions(type, rawQuestion.options)
  const answer = normalizeDocumentAnswer(type, rawQuestion.answer)
  const optionKeys = options.map(item => item.key)

  if (type === 'judge') {
    if (!['A', 'B'].includes(String(answer || '').toUpperCase())) {
      throw new Error(`第 ${index + 1} 道判断题答案仅支持“正确/错误”`)
    }
  } else {
    if (options.length < 2) {
      throw new Error(`第 ${index + 1} 道题至少需要 2 个选项`)
    }
    if (type === 'multi') {
      if (!Array.isArray(answer) || answer.length === 0) {
        throw new Error(`第 ${index + 1} 道多选题至少需要一个正确答案`)
      }
      if (answer.some(item => !optionKeys.includes(item))) {
        throw new Error(`第 ${index + 1} 道题存在未匹配选项的答案`)
      }
    } else if (!optionKeys.includes(String(answer || '').toUpperCase())) {
      throw new Error(`第 ${index + 1} 道题答案未匹配到选项`)
    }
  }

  const knowledgePointNames = String(rawQuestion.knowledgePoints || '')
    .split(/[,，、]/)
    .map(item => item.trim())
    .filter(Boolean)

  return {
    type,
    content,
    options,
    answer,
    explanation: String(rawQuestion.explanation || '').trim() || undefined,
    difficulty: Math.min(5, Math.max(1, Number(rawQuestion.difficulty) || 1)),
    score: Math.max(1, Number(rawQuestion.score) || 1),
    knowledge_point_names: knowledgePointNames,
    police_type_id: resolvePoliceTypeIdByName(rawQuestion.policeTypeName),
  }
}

function parseQuestionBlock(block, index) {
  const question = {
    type: '',
    content: '',
    answer: '',
    explanation: '',
    difficulty: 1,
    score: 1,
    knowledgePoints: '',
    policeTypeName: '',
    options: [],
  }
  let currentField = ''

  const pushOption = (key, value) => {
    if (!key) return
    const optionKey = String(key).trim().toUpperCase()
    const existing = question.options.find(item => item.key === optionKey)
    if (existing) {
      existing.text = value
      return
    }
    question.options.push({ key: optionKey, text: value })
  }

  block.split('\n').forEach((rawLine) => {
    const line = rawLine.trim()
    if (!line || /^题目\s*\d*\s*$/u.test(line)) {
      return
    }

    const optionMatch = line.match(/^([A-F])(?:[\.．、:：\)])\s*(.+)$/i)
    if (optionMatch) {
      pushOption(optionMatch[1], optionMatch[2].trim())
      currentField = `option:${String(optionMatch[1]).toUpperCase()}`
      return
    }

    const fieldMatch = line.match(/^([^:：]+)\s*[:：]\s*(.*)$/)
    if (fieldMatch) {
      const label = normalizeDocumentLabel(fieldMatch[1])
      const value = fieldMatch[2].trim()
      if (['题型', '类型'].includes(label)) {
        question.type = value
        currentField = 'type'
        return
      }
      if (['题干', '题目', '题目内容', '内容'].includes(label)) {
        question.content = value
        currentField = 'content'
        return
      }
      if (['答案', '正确答案'].includes(label)) {
        question.answer = value
        currentField = 'answer'
        return
      }
      if (['解析', '说明'].includes(label)) {
        question.explanation = value
        currentField = 'explanation'
        return
      }
      if (label === '难度') {
        question.difficulty = value
        currentField = 'difficulty'
        return
      }
      if (['分值', '分数'].includes(label)) {
        question.score = value
        currentField = 'score'
        return
      }
      if (['知识点', '知识点名称'].includes(label)) {
        question.knowledgePoints = value
        currentField = 'knowledgePoints'
        return
      }
      if (['警种', '适用警种'].includes(label)) {
        question.policeTypeName = value
        currentField = 'policeTypeName'
        return
      }
      if (/^[A-F]$/i.test(label)) {
        pushOption(label, value)
        currentField = `option:${label.toUpperCase()}`
      }
      return
    }

    if (currentField === 'content') {
      question.content = appendMultilineValue(question.content, line)
      return
    }
    if (currentField === 'explanation') {
      question.explanation = appendMultilineValue(question.explanation, line)
      return
    }
    if (currentField.startsWith('option:')) {
      const optionKey = currentField.split(':')[1]
      const existing = question.options.find(item => item.key === optionKey)
      if (existing) {
        existing.text = appendMultilineValue(existing.text, line)
      }
    }
  })

  return finalizeDocumentQuestion(question, index)
}

function parseDocumentQuestions(text) {
  const normalizedText = String(text || '').replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim()
  if (!normalizedText) return []

  const blocks = normalizedText
    .split(/\n\s*(?:---+|===+|———+)\s*\n/g)
    .map(item => item.trim())
    .filter(Boolean)

  if (!blocks.length) return []
  return blocks.map((block, index) => parseQuestionBlock(block, index))
}

// ============ 计算属性 ============

// 过滤后的题库列表
const filteredList = computed(() => {
  let list = [...folderList.value]

  // 关键字搜索
  if (searchText.value) {
    const keyword = searchText.value.toLowerCase()
    list = list.filter(item => item.name.toLowerCase().includes(keyword) || (item.creatorName || '').toLowerCase().includes(keyword))
  }

  if (filterCategory.value) {
    list = list.filter(item => item.category === filterCategory.value || (filterCategory.value === 'default' && item.category === '默认分类'))
  }

  return list
})

const categoryOptions = computed(() => {
  const values = new Set()
  folderList.value.forEach((item) => {
    const next = (item.category || '默认分类').trim()
    if (next) values.add(next)
  })
  return Array.from(values)
})

const categorySelectOptions = computed(() => categoryOptions.value.map((item) => ({ value: item })))

const folderNameSelectOptions = computed(() => (
  folderListForSelect.value.map((item) => ({ value: item.name }))
))

// 分页后的展示列表
const displayedList = computed(() => {
  const start = (pagination.current - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filteredList.value.slice(start, end)
})

// 总页数
const totalPages = computed(() => Math.ceil(filteredList.value.length / pagination.pageSize) || 1)

const visiblePages = computed(() => {
  const pages = [], total = totalPages.value, cur = pagination.current
  let start = Math.max(1, cur - 2), end = Math.min(total, start + 4)
  if (end - start < 4) start = Math.max(1, end - 4)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

// 全选状态
const isAllSelected = computed(() => {
  if (displayedList.value.length === 0) return false
  return displayedList.value.every(item => selectedIds.value.includes(item.id))
})

const allFolderList = computed(() => [...folderList.value])
const folderListForSelect = computed(() => folderList.value.filter(f => !f.isSystem))
const matchedTargetFolder = computed(() => findFolderByExactName(targetFolderForm.name))
const targetFolderModalTitle = computed(() => {
  const titleMap = {
    manual: '选择题库后手动输入',
    batch: '选择题库后批量上传',
    document: '选择题库后按模板导入',
  }
  return titleMap[targetFolderAction.value] || '选择题库'
})

// 文件夹树形数据（用于选择父文件夹）
const folderTreeData = computed(() => {
  const convert = (folders) => {
    return folders
      .filter(f => f.id !== editingFolderId.value)
      .map(f => ({
        value: f.id,
        label: f.name,
        children: f.children ? convert(f.children) : []
      }))
  }
  return convert(folderTreeSource.value)
})

// ============ 方法 ============

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const pad = n => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function formatAnswer(q) {
  if (q.answer === null || q.answer === undefined) return '-'
  // 判断题答案
  if (q.type === 'judge') {
    return q.answer === true || q.answer === 'true' || q.answer === 1 ? '正确' : '错误'
  }
  // 单选/多选题答案
  if (Array.isArray(q.answer)) {
    return q.answer.join('、')
  }
  return String(q.answer)
}

function flattenFolderTree(folders, depth = 0) {
  let result = []
  for (const folder of folders || []) {
    result.push({ folder, depth })
    if (folder.children && folder.children.length > 0) {
      result = result.concat(flattenFolderTree(folder.children, depth + 1))
    }
  }
  return result
}

function buildBankList(folders) {
  const flattened = flattenFolderTree(folders)
  return flattened.map(({ folder, depth }) => {
    const indent = depth > 0 ? `${'　'.repeat(depth)}└ ` : ''
    const creatorName = folder.created_by_name ?? folder.createdByName
    const category = folder.category ?? '默认分类'
    const paperCount = folder.paper_count ?? folder.paperCount ?? 0
    const exerciseCount = folder.exercise_count ?? folder.exerciseCount ?? 0
    const questionCount = folder.question_count ?? folder.questionCount ?? 0
    const status = folder.status ?? folder.statusText ?? '未使用'
    const createdAt = folder.created_at ?? folder.createdAt
    const createdBy = folder.created_by ?? folder.createdBy
    const parentId = folder.parent_id ?? folder.parentId ?? null
    const courseNames = folder.course_names ?? folder.courseNames ?? []
    const courseIds = folder.course_ids ?? folder.courseIds ?? []
    const fallbackCourseName = folder.course_name ?? folder.courseName ?? ''
    const fallbackCourseId = folder.course_id ?? folder.courseId ?? undefined
    const resolvedCourseNames = courseNames.length ? courseNames : (fallbackCourseName ? [fallbackCourseName] : [])
    const resolvedCourseIds = courseIds.length ? courseIds : (fallbackCourseId ? [fallbackCourseId] : [])

    return {
      id: folder.id,
      name: folder.name,
      displayName: `${indent}${folder.name}`,
      parentId,
      isSystem: folder.name === '综合题库' || folder.is_system,
      creatorName: creatorName || '-',
      category,
      paperCount,
      exerciseCount,
      questionCount,
      statusText: status,
      createdAt: formatDate(createdAt),
      createdBy,
      courseId: resolvedCourseIds[0],
      courseIds: resolvedCourseIds,
      courseName: resolvedCourseNames.join('、'),
      courseNames: resolvedCourseNames,
    }
  })
}

async function loadData() {
  loading.value = true
  try {
    const folders = await getQuestionFolders()
    folderTreeSource.value = folders || []
    const bankList = buildBankList(folderTreeSource.value)
    folderList.value = bankList.map(b => ({ ...b, children: [] }))
    pagination.total = bankList.length
  } catch (error) {
    message.error(error.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.current = 1
}

function changePage(page) {
  if (page < 1 || page > totalPages.value) return
  pagination.current = page
}

function changeQuestionPage(page) {
  const total = Math.ceil(questionPagination.total / questionPagination.pageSize) || 1
  if (page < 1 || page > total) return
  questionPagination.current = page
}

function handlePageSizeChange(size) {
  pagination.pageSize = size
  pagination.current = 1
}

function handleQuestionPageSizeChange(size) {
  questionPagination.pageSize = size
  questionPagination.current = 1
}

// 题目列表分页后的展示列表（应用筛选）
const displayedQuestionList = computed(() => {
  let list = questionList.value
  // 搜索题干
  if (pickerSearch.value) {
    const kw = pickerSearch.value.toLowerCase()
    list = list.filter(q => q.content?.toLowerCase().includes(kw))
  }
  // 题型筛选
  if (pickerType.value !== 'all') {
    list = list.filter(q => q.type === pickerType.value)
  }
  questionPagination.total = list.length
  const start = (questionPagination.current - 1) * questionPagination.pageSize
  const end = start + questionPagination.pageSize
  return list.slice(start, end)
})

const isAllPickSelected = computed(() => {
  return questionList.value.length > 0 && questionList.value.every(q => pickSelectedKeys.value.includes(q.id))
})

// 题目总页数
const questionTotalPages = computed(() => Math.ceil(questionPagination.total / questionPagination.pageSize) || 1)

const questionVisiblePages = computed(() => {
  const pages = [], total = questionTotalPages.value, cur = questionPagination.current
  let start = Math.max(1, cur - 2), end = Math.min(total, start + 4)
  if (end - start < 4) start = Math.max(1, end - 4)
  for (let i = start; i <= end; i++) pages.push(i)
  return pages
})

function toggleSelect(id) {
  const idx = selectedIds.value.indexOf(id)
  if (idx > -1) {
    selectedIds.value.splice(idx, 1)
  } else {
    selectedIds.value.push(id)
  }
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedIds.value = selectedIds.value.filter(id => !displayedList.value.some(item => item.id === id))
  } else {
    const pageIds = displayedList.value.map(item => item.id)
    const merged = new Set([...selectedIds.value, ...pageIds])
    selectedIds.value = Array.from(merged)
  }
}

function openCreateFolderModal() {
  editingFolderId.value = null
  folderForm.name = ''
  folderForm.category = ''
  folderForm.parentId = null
  folderForm.courseId = undefined
  folderFormModalVisible.value = true
}

function goToAiQuestion() {
  router.push({ path: '/question/ai' })
}

function handleUploadMenuClick({ key }) {
  if (key === 'manual') {
    openAddQuestionModal()
    return
  }
  if (key === 'document') {
    openDocumentImportModal()
  }
}

function handleCreateClick(key) {
  if (key === 'manual') {
    router.push({ path: '/paper/repository' })
  } else if (key === 'ai') {
    router.push({ path: '/paper/ai-assemble' })
  }
}

function switchNav(target) {
  if (target === activeNav.value) return
  router.push({ path: '/question/repository' })
}

function openEditFolderModal(folder) {
  editingFolderId.value = folder.id
  folderForm.name = folder.name
  folderForm.category = folder.category === '默认分类' ? '' : folder.category
  folderForm.parentId = folder.parentId
  folderForm.courseId = folder.courseId
  folderFormModalVisible.value = true
}

function resetFolderFormModal() {
  editingFolderId.value = null
  folderForm.name = ''
  folderForm.category = ''
  folderForm.parentId = null
  folderForm.courseId = undefined
  folderFormModalVisible.value = false
}

function findFolderById(folderId) {
  return folderList.value.find((item) => String(item.id) === String(folderId)) || null
}

function findFolderByExactName(name) {
  const normalized = String(name || '').trim()
  if (!normalized) return null
  return folderListForSelect.value.find((item) => item.name === normalized) || null
}

function applySelectedFolder(folder) {
  if (!folder) return
  selectedFolderId.value = folder.id
  selectedFolderName.value = folder.name
  quickSelectFolderId.value = folder.id
}

function fillManualQuestionDraft(folder = null) {
  manualQuestionDraft.bankName = folder?.name || ''
  manualQuestionDraft.bankCategory = folder?.category === '默认分类' ? '' : (folder?.category || '')
  manualQuestionDraft.bankCourseId = folder?.courseId
}

function fillDocumentTargetDraft(folder = null) {
  documentImportForm.bankName = folder?.name || ''
  documentImportForm.bankCategory = folder?.category === '默认分类' ? '' : (folder?.category || '')
  documentImportForm.bankCourseId = folder?.courseId
}

function openTargetFolderModal(action) {
  targetFolderAction.value = action
  const currentFolder = findFolderById(selectedFolderId.value || quickSelectFolderId.value)
  targetFolderForm.name = currentFolder?.name || ''
  targetFolderForm.category = currentFolder?.category === '默认分类' ? '' : (currentFolder?.category || '')
  targetFolderForm.courseId = currentFolder?.courseId
  targetFolderModalVisible.value = true
}

function resetTargetFolderModal() {
  targetFolderAction.value = 'manual'
  targetFolderForm.name = ''
  targetFolderForm.category = ''
  targetFolderForm.courseId = undefined
  targetFolderSubmitting.value = false
  targetFolderModalVisible.value = false
}

async function handleTargetFolderSubmit() {
  const folderName = String(targetFolderForm.name || '').trim()
  if (!folderName) {
    message.warning('请输入题库名称')
    return
  }

  targetFolderSubmitting.value = true
  try {
    const currentAction = targetFolderAction.value
    let folder = findFolderByExactName(folderName)
    if (!folder) {
      await createQuestionFolder({
        name: folderName,
        category: targetFolderForm.category || null,
        sort_order: 0,
        course_id: targetFolderForm.courseId ?? null,
      })
      await loadData()
      folder = findFolderByExactName(folderName)
      message.success('题库已创建')
    }

    if (!folder) {
      throw new Error('题库创建成功，但未获取到题库信息，请刷新后重试')
    }

    applySelectedFolder(folder)
    resetTargetFolderModal()

    if (currentAction === 'manual') {
      editingQuestion.value = null
      modalOpen.value = true
      return
    }
    if (currentAction === 'batch') {
      selectedFile.value = null
      batchPreviewQuestions.value = []
      batchUploadModalVisible.value = true
      return
    }
    if (currentAction === 'document') {
      primeDocumentImportForm()
      documentImportModalVisible.value = true
    }
  } catch (error) {
    message.error(error.message || '题库处理失败')
  } finally {
    targetFolderSubmitting.value = false
  }
}

async function resolveOrCreateTargetFolder({ bankName, bankCategory, bankCourseId }) {
  const normalizedBankName = String(bankName || '').trim()
  if (!normalizedBankName) {
    throw new Error('请填写题库名称')
  }

  let folder = findFolderByExactName(normalizedBankName)
  if (!folder) {
    await createQuestionFolder({
      name: normalizedBankName,
      category: bankCategory || null,
      sort_order: 0,
      course_id: bankCourseId ?? null,
    })
    await loadData()
    folder = findFolderByExactName(normalizedBankName)
    message.success('题库已创建')
  }

  if (!folder) {
    throw new Error('题库创建成功，但未获取到题库信息，请刷新后重试')
  }

  applySelectedFolder(folder)
  return folder
}

async function handleFolderSubmit() {
  if (!folderForm.name?.trim()) {
    message.warning('请输入题库名称')
    return
  }
  try {
    const payload = {
      name: folderForm.name,
      category: folderForm.category || null,
      parent_id: folderForm.parentId,
      sort_order: 0,
      course_id: folderForm.courseId ?? null,
    }
    if (editingFolderId.value) {
      await updateQuestionFolder(editingFolderId.value, payload)
      message.success('题库已更新')
    } else {
      await createQuestionFolder(payload)
      message.success('题库已创建')
    }
    resetFolderFormModal()
    await loadData()
  } catch (error) {
    message.error(error.message || '操作失败')
  }
}

function handleDeleteFolder(folder) {
  if (folder.isSystem) {
    message.warning('系统题库不能删除')
    return
  }
  Modal.confirm({
    title: '确认删除题库',
    content: `删除后无法恢复，是否删除题库「${folder.name}」？`,
    okType: 'danger',
    async onOk() {
      try {
        await deleteQuestionFolder(folder.id)
        message.success('题库已删除')
        await loadData()
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

function handleViewQuestions(item) {
  if (item.isSystem) {
    message.info('系统题库暂无题目')
    return
  }
  selectedFolderId.value = item.id
  selectedFolderName.value = item.name
  pickMode.value = false
  pickSelectedKeys.value = []
  pickerSearch.value = ''
  pickerType.value = 'all'
  router.replace({ path: '/question/repository', query: { folderId: item.id } })
  loadQuestionsForFolder(item.id)
}

async function loadQuestionsForFolder(folderId) {
  questionLoading.value = true
  questionList.value = []
  questionPagination.current = 1
  pickerSearch.value = ''
  pickerType.value = 'all'
  try {
    const result = await getQuestions({ folder_id: folderId, recursive: true, size: -1 })
    questionList.value = result.items || result || []
    questionPagination.total = questionList.value.length
  } catch (error) {
    message.error(error.message || '加载题目失败')
  } finally {
    questionLoading.value = false
  }
}

function enterPickMode() {
  pickMode.value = true
  pickSelectedKeys.value = []
}

function exitPickMode() {
  pickMode.value = false
  pickSelectedKeys.value = []
}

function togglePickSelect(id) {
  const idx = pickSelectedKeys.value.indexOf(id)
  if (idx >= 0) {
    pickSelectedKeys.value.splice(idx, 1)
  } else {
    pickSelectedKeys.value.push(id)
  }
}

function togglePickSelectAll() {
  if (isAllPickSelected.value) {
    pickSelectedKeys.value = []
  } else {
    pickSelectedKeys.value = questionList.value.map(q => q.id)
  }
}

function confirmPick() {
  if (!pickSelectedKeys.value.length) return
  const ids = pickSelectedKeys.value.join(',')
  router.push({ path: '/paper/repository', query: { pickQuestions: ids } })
  exitPickMode()
}

function handleBackToFolders() {
  selectedFolderId.value = null
  selectedFolderName.value = ''
  questionList.value = []
  pickMode.value = false
  pickSelectedKeys.value = []
  pickerSearch.value = ''
  pickerType.value = 'all'
  router.replace({ path: '/question/repository' })
}

function handleBatchDelete() {
  if (selectedIds.value.length === 0) {
    message.warning('请先选择要删除的题库')
    return
  }
  Modal.confirm({
    title: '确认批量删除',
    content: `确定要删除选中的 ${selectedIds.value.length} 个题库吗？`,
    okType: 'danger',
    async onOk() {
      try {
        for (const id of selectedIds.value) {
          await deleteQuestionFolder(id)
        }
        message.success('批量删除成功')
        selectedIds.value = []
        await loadData()
      } catch (error) {
        message.error(error.message || '批量删除失败')
      }
    },
  })
}

// 单个题目操作
function handleEditQuestion(q) {
  editingQuestion.value = q
  modalOpen.value = true
}

function handleMoveQuestion(q) {
  currentMovingQuestion.value = q
  moveQuestionTargetFolderId.value = null
  moveQuestionModalVisible.value = true
}

async function handleMoveQuestionConfirm() {
  if (moveQuestionTargetFolderId.value === null && moveQuestionTargetFolderId.value !== 0) {
    message.warning('请选择目标文件夹')
    return
  }
  try {
    await moveQuestionToFolder(currentMovingQuestion.value.id, moveQuestionTargetFolderId.value)
    message.success('题目已移动')
    moveQuestionModalVisible.value = false
    currentMovingQuestion.value = null
    await loadQuestionsForFolder(selectedFolderId.value)
  } catch (error) {
    message.error(error.message || '移动失败')
  }
}

function handleDeleteQuestion(q) {
  Modal.confirm({
    title: '确认删除题目',
    content: `删除后无法恢复，是否删除该题目？`,
    okType: 'danger',
    async onOk() {
      try {
        await deleteQuestion(q.id)
        message.success('题目已删除')
        await loadQuestionsForFolder(selectedFolderId.value)
      } catch (error) {
        message.error(error.message || '删除失败')
      }
    },
  })
}

// 题目相关
async function handleSubmitQuestion(payload) {
  try {
    const { bankName, bankCategory, bankCourseId, ...questionPayload } = payload
    if (editingQuestion.value?.id) {
      await updateQuestion(editingQuestion.value.id, questionPayload)
      message.success('题目已更新')
    } else {
      const targetFolder = await resolveOrCreateTargetFolder({
        bankName,
        bankCategory,
        bankCourseId,
      })
      const resolvedFolderId = targetFolder.id
      const finalPayload = { ...questionPayload, folderId: resolvedFolderId, folder_id: resolvedFolderId }
      await createQuestion(finalPayload)
      message.success('题目已创建')
      fillManualQuestionDraft(targetFolder)
    }
    modalOpen.value = false
    editingQuestion.value = null
    if (selectedFolderId.value) {
      await loadQuestionsForFolder(selectedFolderId.value)
    }
    await loadData()
  } catch (error) {
    message.error(error.message || '保存失败')
  }
}

function openAddQuestionModal() {
  const folder = findFolderById(selectedFolderId.value || quickSelectFolderId.value)
  fillManualQuestionDraft(folder)
  editingQuestion.value = null
  modalOpen.value = true
}

function openBatchUploadModal() {
  const folder = findFolderById(selectedFolderId.value || quickSelectFolderId.value)
  if (folder) {
    applySelectedFolder(folder)
  } else {
    openTargetFolderModal('batch')
    return
  }
  selectedFile.value = null
  batchPreviewQuestions.value = []
  batchUploadModalVisible.value = true
}

function primeDocumentImportForm() {
  const folder = findFolderById(selectedFolderId.value || quickSelectFolderId.value)
  fillDocumentTargetDraft(folder)
  documentImportForm.sourceText = ''
  documentImportForm.sourceMaterialName = ''
}

function resetDocumentImportModal() {
  documentImportModalVisible.value = false
  documentImportLoading.value = false
  documentParsing.value = false
  primeDocumentImportForm()
}

function openDocumentImportModal() {
  primeDocumentImportForm()
  documentImportModalVisible.value = true
}

function triggerFileInput() {
  fileInputRef.value?.click()
}

function triggerDocumentFileInput() {
  documentFileInputRef.value?.click()
}

function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

async function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return

  selectedFile.value = file
  batchPreviewQuestions.value = []

  try {
    const text = await file.text()
    let questions = []

    if (file.name.endsWith('.json')) {
      questions = JSON.parse(text)
      if (!Array.isArray(questions)) {
        questions = [questions]
      }
    } else {
      message.error('仅支持 JSON 格式文件')
      selectedFile.value = null
      return
    }

    // 验证题目格式
    questions = questions.filter(q => q.type && q.content && (q.answer || q.answer === false || q.answer === 0))
    batchPreviewQuestions.value = questions
  } catch (error) {
    message.error('文件解析失败：' + error.message)
    selectedFile.value = null
  }
}

async function handleDocumentFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file) return

  documentParsing.value = true
  try {
    const result = await parseAiDocumentFile(file)
    const text = result?.text || result?.data?.text || ''
    documentImportForm.sourceMaterialName = file.name
    documentImportForm.sourceText = text || ''
    message.success('文档解析完成')
  } catch (error) {
    message.error(error.message || '文档解析失败')
  } finally {
    documentParsing.value = false
    if (event.target) {
      event.target.value = ''
    }
  }
}

async function handleBatchUpload() {
  if (!selectedFile.value || batchPreviewQuestions.value.length === 0) {
    message.warning('请先选择有效的题目文件')
    return
  }

  batchUploadLoading.value = true
  try {
    const questions = batchPreviewQuestions.value.map(q => ({
      type: q.type,
      content: q.content,
      options: q.options || [],
      answer: q.answer,
      explanation: q.explanation || null,
      difficulty: q.difficulty || 1,
      police_type_id: q.police_type_id || null,
      knowledge_point_names: q.knowledge_point_names || [],
      folder_id: selectedFolderId.value,
    }))

    await batchCreateQuestions({ questions })
    message.success(`成功上传 ${questions.length} 道题目`)

    batchUploadModalVisible.value = false
    selectedFile.value = null
    batchPreviewQuestions.value = []

    if (selectedFolderId.value) {
      await loadQuestionsForFolder(selectedFolderId.value)
    }
  } catch (error) {
    message.error(error.message || '批量上传失败')
  } finally {
    batchUploadLoading.value = false
  }
}

async function handleDocumentImportSubmit() {
  if (!documentImportForm.bankName?.trim()) {
    message.warning('请填写题库名称')
    return
  }
  if (!documentImportForm.sourceText?.trim()) {
    message.warning('请先上传文档或填写模板内容')
    return
  }

  documentImportLoading.value = true
  try {
    const targetFolder = await resolveOrCreateTargetFolder({
      bankName: documentImportForm.bankName,
      bankCategory: documentImportForm.bankCategory,
      bankCourseId: documentImportForm.bankCourseId,
    })
    const parsedQuestions = parseDocumentQuestions(documentImportForm.sourceText)
    if (!parsedQuestions.length) {
      throw new Error('未识别到题目，请先下载模板并按模板格式整理后再上传')
    }

    const questions = parsedQuestions.map(item => ({
      ...item,
      folder_id: targetFolder.id,
    }))

    await batchCreateQuestions({ questions })

    message.success(`已同步导入 ${questions.length} 道题目`)
    resetDocumentImportModal()
    await loadData()
    if (selectedFolderId.value || targetFolder.id) {
      await loadQuestionsForFolder(targetFolder.id)
    }
  } catch (error) {
    message.error(error.message || '同步导入失败')
  } finally {
    documentImportLoading.value = false
  }
}

async function loadPoliceTypeOptions() {
  try {
    const result = await getPoliceTypes()
    policeTypeOptions.value = result.items || result || []
  } catch {
    policeTypeOptions.value = []
  }
}

async function loadCourseOptions() {
  try {
    const result = await getCourses({ page: 1, size: -1 })
    courseOptions.value = result.items || []
  } catch {
    courseOptions.value = []
  }
}

function clearQuestionSelection() {
  selectedFolderId.value = null
  selectedFolderName.value = ''
  questionList.value = []
  questionPagination.total = 0
  questionPagination.current = 1
}

async function syncFolderState(folderId) {
  if (!folderId) {
    clearQuestionSelection()
    return
  }

  const folder = folderList.value.find((item) => String(item.id) === String(folderId))
  if (!folder) {
    clearQuestionSelection()
    return
  }

  selectedFolderId.value = folder.id
  selectedFolderName.value = folder.name
  await loadQuestionsForFolder(folder.id)
}

onMounted(async () => {
  if (canManageQuestionBank.value) {
    await loadData()
    await loadPoliceTypeOptions()
    await loadCourseOptions()
  }
  await syncFolderState(route.query.folderId)
})

watch(() => route.path, () => {
  syncFolderState(route.query.folderId)
})

watch(() => route.query.folderId, (newVal) => {
  syncFolderState(newVal)
})

watch([pickerSearch, pickerType], () => {
  questionPagination.current = 1
})

watch(
  () => filteredList.value.length,
  (value) => {
    pagination.total = value
    const maxPage = Math.ceil(value / pagination.pageSize) || 1
    if (pagination.current > maxPage) {
      pagination.current = maxPage
    }
  },
  { immediate: true }
)

onUnmounted(() => {
  const mainLayout = document.querySelector('.main-layout')
  if (mainLayout) {
    mainLayout.classList.remove('question-bank-fullscreen')
  }
})
</script>

<style scoped>
/* ============ 页面布局 ============ */
.question-bank-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #F8FAFC;
  color: #334155;
  margin: 0;
  padding: 0;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
}

.content-wrapper {
  max-width: 100%;
  width: 100%;
}

/* ============ 二级导航 ============ */
.sub-nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.sub-nav-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.sub-nav-item {
  font-size: 14px;
  font-weight: 600;
  color: #94A3B8;
  padding-bottom: 8px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  cursor: pointer;
}

.sub-nav-item:hover {
  color: #64748B;
}

.sub-nav-item.active {
  color: #1E293B;
  border-color: #2563EB;
}

.sub-nav-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-aux {
  font-size: 12px;
  font-weight: 600;
  color: #64748B;
  padding: 6px 12px;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  background-color: #FFFFFF;
  transition: all 0.2s;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-aux:hover {
  border-color: #CBD5E1;
  background-color: #F8FAFC;
  color: #1E293B;
}

/* ============ 主容器 ============ */
.main-container {
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 640px;
}

/* ============ 工具栏 ============ */
.toolbar-row {
  padding: 24px 32px;
  border-bottom: 1px solid #F1F5F9;
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.btn-primary {
  background: #2563EB;
  color: white;
  font-size: 14px;
  font-weight: 700;
  padding: 8px 24px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 6px rgba(37, 99, 235, 0.1);
}

.btn-primary:hover {
  background: #1D4ED8;
  transform: scale(0.98);
}

.upload-trigger-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.upload-trigger-icon {
  font-size: 12px;
}

.search-wrapper {
  position: relative;
  width: 256px;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 10px;
  width: 16px;
  height: 16px;
  color: #94A3B8;
  pointer-events: none;
}

.input-minimal {
  background-color: transparent;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 14px;
  color: #1E293B;
  transition: all 0.2s;
  outline: none;
  height: 36px;
}

.input-minimal:hover {
  border-color: #CBD5E1;
}

.input-minimal:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-wrapper .input-minimal {
  padding-left: 36px;
  width: 100%;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-title {
  font-size: 15px;
  font-weight: 600;
  color: #334155;
}

.toolbar-hint {
  font-size: 12px;
  color: #94A3B8;
  font-style: italic;
}

.pick-hint {
  font-size: 13px;
  color: #2563EB;
  font-weight: 600;
  padding: 0 8px;
}

.filter-select {
  width: 160px;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2220%22%20height%3D%2220%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M5%207l5%205%205-5%22%20stroke%3D%22%2394A3B8%22%20stroke-width%3D%221.5%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  font-size: 12px;
  font-weight: 500;
  color: #64748B;
  cursor: pointer;
}

.filter-select-sm {
  width: 128px;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2220%22%20height%3D%2220%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M5%207l5%205%205-5%22%20stroke%3D%22%2394A3B8%22%20stroke-width%3D%221.5%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  font-size: 12px;
  font-weight: 500;
  color: #64748B;
  cursor: pointer;
}

.divider-v {
  width: 1px;
  height: 16px;
  background: #E2E8F0;
  margin: 0 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  color: #64748B;
  transition: color 0.2s;
}

.checkbox-label:hover {
  color: #1E293B;
}

.custom-checkbox {
  width: 14px;
  height: 14px;
  border-radius: 4px;
  border: 1px solid #CBD5E1;
  accent-color: #2563EB;
  cursor: pointer;
}

/* ============ 表格 ============ */
.table-wrapper {
  flex: 1;
  overflow-x: auto;
}

.data-table {
  width: 100%;
  text-align: left;
  border-collapse: collapse;
  table-layout: fixed;
}

.data-table thead tr {
  background: #F8FAFC;
  border-bottom: 1px solid #F1F5F9;
}

.data-table th {
  padding: 16px;
  font-size: 10px;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  white-space: nowrap;
}

.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

.col-check {
  padding-left: 32px !important;
  padding-right: 16px !important;
  width: 48px;
}

.col-index {
  width: 60px;
  text-align: center;
}

.col-name {
  width: 200px;
}

.col-publisher {
  width: 80px;
}

.col-category {
  width: 100px;
}

.col-paper {
  width: 80px;
}

.col-course {
  width: 140px;
}

.col-questions {
  width: 80px;
}

.col-status {
  width: 80px;
}

.col-time {
  width: 120px;
}

.col-action {
  width: 140px;
  padding-right: 32px !important;
  padding-left: 16px !important;
}

.col-type {
  width: 80px;
}

.col-content {
  min-width: 200px;
}

.col-answer {
  width: 100px;
}

.answer-text {
  font-size: 13px;
  font-weight: 600;
  color: #059669;
}

.ml-2 {
  margin-left: 8px;
}

.col-difficulty {
  width: 60px;
}

.col-kp {
  max-width: 180px;
}

.kp-text {
  font-size: 12px;
  color: #64748B;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.options-preview {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.option-tag {
  font-size: 11px;
  color: #64748B;
  background: #F1F5F9;
  padding: 1px 6px;
  border-radius: 3px;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.difficulty-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #F1F5F9;
  color: #64748B;
  font-size: 11px;
  font-weight: 600;
}

.table-row {
  transition: background-color 0.2s;
  border-bottom: 1px solid #F8FAFC;
}

.table-row:hover {
  background-color: #F8FAFC;
}

.data-table td {
  padding: 20px 16px;
  vertical-align: middle;
}

.name-text {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
  transition: color 0.2s;
}

.name-text:hover {
  color: #2563EB;
}

.name-text.is-system {
  color: #334155;
}

.badge-system {
  margin-left: 8px;
  font-size: 9px;
  font-weight: 700;
  color: #3B82F6;
  background: #EFF6FF;
  padding: 2px 4px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: -0.02em;
}

.question-count {
  font-weight: 700;
  color: #2563EB;
}

.question-count-btn {
  background: none;
  border: none;
  color: #2563EB;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  padding: 0;
  transition: color 0.2s;
}

.question-count-btn:hover {
  color: #1D4ED8;
  text-decoration: underline;
}

.status-text {
  font-size: 12px;
  font-weight: 500;
  color: #94A3B8;
  font-style: italic;
}

.col-time {
  font-size: 12px;
  color: #94A3B8;
  font-family: monospace;
}

.action-btns {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-link {
  background: none;
  border: none;
  color: #2563EB;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 0;
  transition: color 0.2s;
}

.btn-link:hover:not(:disabled) {
  color: #1D4ED8;
  text-decoration: underline;
}

.btn-link:disabled {
  color: #CBD5E1;
  cursor: not-allowed;
}

.btn-link-danger {
  color: #EF4444;
}

.btn-link-danger:hover:not(:disabled) {
  color: #DC2626;
}

.empty-row {
  text-align: center;
  padding: 40px;
  color: #94A3B8;
  font-size: 14px;
}

/* ============ 底部区域 ============ */
.footer-area {
  padding: 20px 32px;
  border-top: 1px solid #F1F5F9;
  background: rgba(248, 250, 252, 0.1);
  flex-shrink: 0;
}

.notice-area {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 11px;
  color: #94A3B8;
  line-height: 1.6;
  max-width: 800px;
}

.notice-icon {
  width: 16px;
  height: 16px;
  color: #CBD5E1;
  flex-shrink: 0;
  margin-top: 2px;
}

.notice-text {
  margin: 0;
}

.notice-text p {
  margin: 0;
}

.notice-text .mt-4 {
  margin-top: 4px;
}

.footer-divider {
  width: 100%;
  height: 1px;
  background: #F1F5F9;
  margin: 16px 0;
}

.footer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.batch-ops {
  display: flex;
  align-items: center;
  gap: 12px;
}

.batch-label {
  font-size: 12px;
  color: #94A3B8;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: -0.02em;
}

.btn-batch {
  font-size: 12px;
  font-weight: 700;
  color: #64748B;
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid transparent;
  background: none;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-batch:hover {
  background: #F1F5F9;
  border-color: #E2E8F0;
}

.btn-batch-danger {
  color: #EF4444;
}

.btn-batch-danger:hover {
  background: #FEF2F2;
  border-color: #FECACA;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.page-info {
  font-size: 11px;
  color: #94A3B8;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.page-sep {
  margin: 0 12px;
  color: #E2E8F0;
}

.pagination-btns {
  display: flex;
  gap: 4px;
}

.page-btn {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  border: 1px solid #E2E8F0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 10px;
  font-weight: 700;
  color: #64748B;
}

.page-btn:hover:not(:disabled) {
  background: #F1F5F9;
}

.page-btn:disabled {
  color: #CBD5E1;
  cursor: not-allowed;
}

.page-btn-active {
  background: #1E293B;
  color: white;
  border-color: #1E293B;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* ============ 分页大小选择 ============ */
.page-size-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-size-label {
  font-size: 11px;
  color: #94A3B8;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.page-size-select {
  font-size: 12px;
  color: #64748B;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  padding: 4px 24px 4px 8px;
  background: white;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20width%3D%2220%22%20height%3D%2220%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cpath%20d%3D%22M5%207l5%205%205-5%22%20stroke%3D%22%2394A3B8%22%20stroke-width%3D%221.5%22%20fill%3D%22none%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 4px center;
  background-size: 16px;
  transition: all 0.2s;
}

.page-size-select:hover {
  border-color: #CBD5E1;
}

.page-size-select:focus {
  outline: none;
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* ============ 答案展开区域 ============ */
.answer-section {
  margin-top: 12px;
  padding: 12px 16px;
  background: #F0F9FF;
  border-radius: 8px;
  border: 1px solid #E0F2FE;
}

.answer-label {
  font-size: 12px;
  font-weight: 700;
  color: #0369A1;
  margin-bottom: 4px;
}

.answer-content {
  font-size: 14px;
  font-weight: 700;
  color: #0C4A6E;
}

.answer-explanation {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #BAE6FD;
}

.answer-explanation .answer-label {
  color: #7C3AED;
}

.answer-explanation div:last-child {
  font-size: 13px;
  color: #4C1D95;
  line-height: 1.6;
}

/* ============ 文件夹管理弹窗 ============ */
.folder-manager {
  padding: 8px 0;
}

.folder-manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.folder-manager-list {
  max-height: 400px;
  overflow-y: auto;
}

.folder-manager-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 8px;
  border-bottom: 1px solid #F1F5F9;
}

.folder-manager-item:hover {
  background: #F8FAFC;
}

.folder-manager-item-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #334155;
}

.folder-manager-item-actions {
  display: flex;
  gap: 8px;
}

/* ============ 滚动条 ============ */
::-webkit-scrollbar {
  width: 5px;
}

::-webkit-scrollbar-thumb {
  background: #E2E8F0;
  border-radius: 10px;
}

/* ============ 批量上传 ============ */
.batch-upload-content {
  padding: 8px 0;
}

.upload-tip {
  font-size: 13px;
  color: #64748B;
  margin-bottom: 16px;
}

.upload-tip ul {
  margin: 8px 0;
  padding-left: 20px;
}

.upload-tip li {
  margin: 4px 0;
}

.document-upload-tip {
  margin-bottom: 0;
}

.document-import-layout {
  display: grid;
  grid-template-columns: minmax(320px, 0.8fr) minmax(560px, 1.45fr);
  grid-template-areas:
    "info result"
    "upload result";
  gap: 18px;
  align-items: stretch;
}

.document-import-panel {
  border: 1px solid #E2E8F0;
  border-radius: 16px;
  background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
  padding: 18px 18px 10px;
}

.document-info-panel {
  grid-area: info;
}

.document-result-panel {
  grid-area: result;
  display: flex;
  flex-direction: column;
}

.document-upload-panel {
  grid-area: upload;
}

.document-info-panel {
  padding-bottom: 18px;
}

.document-basic-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

.document-field-name {
  grid-column: 1 / -1;
}

.document-upload-field,
.document-result-field {
  margin-bottom: 0;
}

.document-upload-area {
  min-height: 196px;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    linear-gradient(135deg, rgba(37, 99, 235, 0.04), rgba(14, 165, 233, 0.02)),
    #FFFFFF;
}

.document-upload-area:hover {
  border-color: #93C5FD;
  background:
    linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(14, 165, 233, 0.04)),
    #F8FAFC;
}

.document-result-field :deep(.ant-form-item-control-input),
.document-result-field :deep(.ant-form-item-control-input-content) {
  min-height: 100%;
}

.document-result-field :deep(.ant-form-item-extra) {
  margin-bottom: 10px;
}

.document-result-field :deep(textarea.ant-input) {
  min-height: 540px;
  resize: vertical;
  border-radius: 12px;
  padding: 14px 16px;
  line-height: 1.65;
}

:deep(.document-import-modal .ant-modal-body) {
  padding-top: 18px;
}

.template-link {
  color: #2563EB;
  font-weight: 600;
  text-decoration: none;
}

.template-link:hover {
  color: #1D4ED8;
  text-decoration: underline;
}

.template-hint {
  margin-left: 10px;
  color: #64748B;
}

.code-block {
  background: #F1F5F9;
  padding: 12px;
  border-radius: 6px;
  font-size: 11px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: monospace;
}

.upload-area {
  border: 2px dashed #E2E8F0;
  border-radius: 8px;
  padding: 32px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: #CBD5E1;
  background: #F8FAFC;
}

.upload-placeholder {
  color: #94A3B8;
}

.upload-placeholder svg {
  width: 10%;
  height: 10%;
}

.upload-placeholder p {
  margin: 8px 0 0;
  font-size: 14px;
}

.selected-file {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #059669;
  font-size: 14px;
  font-weight: 500;
}

.preview-section {
  margin-top: 16px;
  border-top: 1px solid #F1F5F9;
  padding-top: 16px;
}

.preview-section h4 {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  margin: 0 0 12px;
}

.preview-list {
  max-height: 240px;
  overflow-y: auto;
}

.preview-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  border-bottom: 1px solid #F8FAFC;
}

.preview-item:last-child {
  border-bottom: none;
}

.preview-type {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: #EFF6FF;
  color: #2563EB;
}

.preview-content {
  font-size: 13px;
  color: #64748B;
}

.preview-more {
  padding: 8px;
  text-align: center;
  color: #94A3B8;
  font-size: 12px;
}

@media (max-width: 960px) {
  .document-import-layout {
    grid-template-columns: 1fr;
    grid-template-areas:
      "info"
      "upload"
      "result";
  }

  .document-info-panel,
  .document-result-panel,
  .document-upload-panel {
    grid-area: auto;
  }

  .document-basic-grid {
    grid-template-columns: 1fr;
  }

  .document-field-name {
    grid-column: auto;
  }

  .document-result-field :deep(textarea.ant-input) {
    min-height: 320px;
  }
}
</style>
