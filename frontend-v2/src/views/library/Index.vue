<template>
  <div class="library-page" @click="handlePageClick">
    <!-- Modals -->
    <QuickUploadModal
      v-model:open="uploadVisible"
      :folder-options="folderOptions"
      :default-folder-id="selectedFolderId"
      @success="handleDataRefresh"
    />
    <KnowledgeCardModal
      v-model:open="knowledgeVisible"
      :folder-options="folderOptions"
      :default-folder-id="selectedFolderId"
      :item-id="editingKnowledgeId"
      :initial-title="editingKnowledgeTitle"
      :initial-content="editingKnowledgeContent"
      @success="handleKnowledgeSaved"
    />
    <MoveItemModal
      v-model:open="moveVisible"
      :item-id="moveTarget ? moveTarget.id : null"
      :current-folder-id="moveTarget ? moveTarget.folder_id : null"
      :folder-options="folderOptions"
      @success="handleDataRefresh"
    />

    <!-- Create Folder Modal -->
    <a-modal
      v-model:open="createFolderVisible"
      title="新建文件夹"
      :footer="null"
      :destroy-on-close="true"
      @cancel="resetFolderForm"
    >
      <a-form layout="vertical">
        <a-form-item label="文件夹名称" required>
          <a-input v-model:value="folderForm.name" :maxlength="100" placeholder="请输入文件夹名称" />
        </a-form-item>
        <a-form-item label="父文件夹">
          <a-select v-model:value="folderForm.parentId" allow-clear placeholder="创建到根目录">
            <a-select-option :value="null">根目录</a-select-option>
            <a-select-option v-for="folder in folderOptions" :key="folder.value" :value="folder.value">
              {{ folder.label }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
      <div class="modal-footer">
        <a-button @click="resetFolderForm">取消</a-button>
        <a-button type="primary" :loading="folderSubmitting" @click="handleCreateFolder">创建文件夹</a-button>
      </div>
    </a-modal>

    <!-- Preview Modal -->
    <a-modal
      v-model:open="previewVisible"
      :title="previewItem ? previewItem.title : '资源预览'"
      :width="960"
      :footer="null"
      :destroy-on-close="true"
    >
      <div v-if="previewItem" class="preview-panel">
        <div class="preview-meta">
          <a-tag color="blue">{{ getLibraryTypeLabel(previewItem.content_type) }}</a-tag>
          <a-tag v-if="previewItem.source_kind === 'ai_generated'" color="cyan">AI教学资源</a-tag>
          <a-tag v-if="previewItem.is_public" color="gold">公共资源</a-tag>
          <span>{{ previewItem.owner_name || '-' }}</span>
          <span>{{ formatDateTime(previewItem.updated_at || previewItem.created_at) }}</span>
        </div>

        <video
          v-if="previewItem.content_type === 'video' && previewItem.file_url"
          :src="previewItem.file_url"
          controls
          class="preview-media"
        />
        <audio
          v-else-if="previewItem.content_type === 'audio' && previewItem.file_url"
          :src="previewItem.file_url"
          controls
          class="preview-audio"
        />
        <div v-else-if="previewItem.content_type === 'image' && previewItem.file_url" class="preview-image-stage">
          <img :src="previewItem.file_url" :alt="previewItem.title" class="preview-image" />
        </div>
        <div v-else-if="previewItem.content_type === 'document' && previewItem.file_url" class="preview-document">
          <iframe :src="previewItem.file_url" class="preview-iframe" title="资源文档预览" />
          <a-button type="link" :href="previewItem.file_url" target="_blank">在新窗口打开文档</a-button>
        </div>
        <div v-else-if="previewItem.content_type === 'knowledge'" class="preview-knowledge" v-html="previewItem.knowledge_content_html" />
        <a-empty v-else description="当前资源暂无可预览内容" />
      </div>
    </a-modal>

    <!-- Storage Stats Modal -->
    <a-modal
      v-model:open="storageModalVisible"
      title="系统存储统计"
      :footer="null"
      :width="720"
      :destroy-on-close="true"
    >
      <div class="storage-modal">
        <div class="storage-panel-head">
          <div>
            <p class="storage-panel-label">当前范围总览</p>
            <h3 class="storage-panel-title">资源容量与结构分布</h3>
          </div>
          <span class="storage-panel-time">{{ storageSummary.latestUpdate }}</span>
        </div>
        <div class="storage-grid">
          <div class="storage-metric">
            <span class="storage-metric-label">资源总数</span>
            <strong>{{ storageSummary.totalItems }}</strong>
          </div>
          <div class="storage-metric">
            <span class="storage-metric-label">目录数量</span>
            <strong>{{ storageSummary.totalFolders }}</strong>
          </div>
          <div class="storage-metric">
            <span class="storage-metric-label">AI 资源</span>
            <strong>{{ storageSummary.aiItems }}</strong>
          </div>
          <div class="storage-metric">
            <span class="storage-metric-label">公共资源</span>
            <strong>{{ storageSummary.publicItems }}</strong>
          </div>
          <div class="storage-metric">
            <span class="storage-metric-label">文件型资源</span>
            <strong>{{ storageSummary.fileItems }}</strong>
          </div>
          <div class="storage-metric">
            <span class="storage-metric-label">累计容量</span>
            <strong>{{ storageSummary.totalSize }}</strong>
          </div>
        </div>
        <div v-if="storageSummary.distribution && storageSummary.distribution.length > 0" class="storage-distribution">
          <div
            v-for="entry in storageSummary.distribution"
            :key="entry.key"
            class="distribution-row"
          >
            <div class="distribution-copy">
              <span class="distribution-name">{{ entry.label }}</span>
              <span class="distribution-count">{{ entry.count }} 项</span>
            </div>
            <div class="distribution-bar">
              <span
                class="distribution-fill"
                :style="{ width: entry.percent + '%' }"
              />
            </div>
          </div>
        </div>
      </div>
    </a-modal>

    <!-- 移动端顶部 Header -->
    <header class="mobile-header">
      <div class="mobile-header-left">
        <button class="mobile-menu-btn" @click="mobileSidebarOpen = !mobileSidebarOpen">
          <svg class="w-6 h-6 shrink-0 icon-lg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
        </button>
        <span class="mobile-header-title">知识库</span>
      </div>
      <div class="mobile-avatar">
        {{ avatarText }}
      </div>
    </header>

    <!-- 移动端遮罩 -->
    <div
      v-if="mobileSidebarOpen"
      class="mobile-sidebar-mask"
      @click="mobileSidebarOpen = false"
    />

    <!-- 主页面布局 -->
    <div class="library-layout">
      <!-- 二级侧边栏 -->
      <aside
        class="library-sidebar"
        :class="{ 'mobile-open': mobileSidebarOpen }"
      >
        <div class="sidebar-inner">
          <div class="sidebar-title-block">
            <h2 class="sidebar-title">知识库</h2>
          </div>

          <!-- 搜索框 -->
          <div class="sidebar-search-wrap">
            <svg class="sidebar-search-icon w-4 h-4 shrink-0 icon-sm" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <input
              v-model="searchKeyword"
              type="text"
              class="search-input"
              placeholder="搜索资料/知识点..."
              @keyup.enter="handleSearch"
            />
          </div>

          <div class="sidebar-scroll hide-scrollbar">
            <!-- 分类标签 -->
            <div class="mb-6">
              <div class="sidebar-section-heading">
                <span class="sidebar-section-label">分类标签</span>
              </div>
              <button
                v-for="cat in categories"
                :key="cat.key"
                type="button"
                class="sidebar-item"
                :class="{
                  active: selectedCategory === cat.key,
                  'ai-resource': cat.key === 'ai_generated'
                }"
                @click="handleCategorySelect(cat.key)"
              >
                <template v-if="cat.key === 'ai_generated'">
                  <svg class="w-4 h-4 mr-2 shrink-0 icon-sm" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"/>
                  </svg>
                  AI 教学资源
                </template>
                <template v-else>{{ cat.label }}</template>
              </button>
            </div>

            <!-- 我的文件夹 -->
            <div>
              <div class="sidebar-section-head group">
                <span class="sidebar-section-label">我的文件夹</span>
                <svg
                  v-if="scopeTab === 'private'"
                  class="w-3.5 h-3.5 shrink-0 icon-xs folder-plus-icon"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  @click="openCreateFolder"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                </svg>
              </div>

              <div class="folder-list">
                <button
                  type="button"
                  class="sidebar-folder"
                  :class="{ active: selectedFolderId === null }"
                  @click="selectedFolderId = null"
                >
                  <svg class="w-4 h-4 mr-2 text-blue-600 shrink-0 icon-sm" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"/>
                  </svg>
                  <span class="truncate font-semibold text-gray-800">根目录</span>
                </button>
                <button
                  v-for="folder in folders"
                  :key="folder.id"
                  type="button"
                  class="sidebar-folder pl-8 group"
                  :class="{ active: selectedFolderId === folder.id }"
                  @click="selectedFolderId = folder.id"
                >
                  <svg class="w-4 h-4 mr-2 text-gray-400 group-hover:text-gray-600 shrink-0 icon-sm" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"/>
                  </svg>
                  <span class="truncate flex-1">{{ folder.name }}</span>
                  <span class="folder-count text-[10px] text-gray-400 bg-gray-100 px-1.5 rounded opacity-0 group-hover:opacity-100 transition">{{ folder.item_count || 0 }}</span>
                  <a-button
                    type="text"
                    size="small"
                    danger
                    class="folder-delete-btn opacity-0 group-hover:opacity-100 ml-1"
                    @click.stop="handleDeleteFolder(folder.id)"
                  >删除</a-button>
                </button>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- 右侧主内容区 -->
      <main class="library-main">
        <div class="library-main-scroll">
          <!-- 顶部大标题与业务快捷操作区 -->
          <div class="main-hero">
            <div class="main-hero-head">
              <div class="main-title-block">
                <h1 class="main-title">我的资源</h1>
                <p class="main-subtitle">当前查看 {{ currentFolderName }} 下的 {{ currentCategoryLabel }}</p>
              </div>
              <div class="main-hero-actions">
                <button
                  type="button"
                  class="stat-button"
                  @click.stop="storageModalVisible = true"
                >
                  系统存储统计
                </button>
              </div>
            </div>

            <!-- 业务卡片 -->
            <div class="action-strip hide-scrollbar">
              <!-- 上传资源 -->
              <button type="button" class="action-card group" @click="uploadVisible = true">
                <div class="action-icon action-icon-blue">
                  <svg class="w-5 h-5 shrink-0 icon-md" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                  </svg>
                </div>
                <div class="action-copy">
                  <span class="action-title action-title-blue">上传资源</span>
                  <span class="action-desc">支持文档、视频、图片</span>
                </div>
              </button>

              <!-- 新建知识点 -->
              <button type="button" class="action-card group" @click="openKnowledgeCreate">
                <div class="action-icon action-icon-purple">
                  <svg class="w-5 h-5 shrink-0 icon-md" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                  </svg>
                </div>
                <div class="action-copy">
                  <span class="action-title action-title-purple">新建知识点</span>
                  <span class="action-desc">录入文本或微课内容</span>
                </div>
              </button>

              <!-- 批量导入 -->
              <button type="button" class="action-card group" @click="uploadVisible = true">
                <div class="action-icon action-icon-emerald">
                  <svg class="w-5 h-5 shrink-0 icon-md" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                  </svg>
                </div>
                <div class="action-copy">
                  <span class="action-title action-title-emerald">批量导入</span>
                  <span class="action-desc">使用模板快速上传</span>
                </div>
              </button>

              <!-- 新建文件夹 -->
              <button type="button" class="action-card group" @click="openCreateFolder">
                <div class="action-icon action-icon-orange">
                  <svg class="w-5 h-5 shrink-0 icon-md" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
                  </svg>
                </div>
                <div class="action-copy">
                  <span class="action-title action-title-orange">新建文件夹</span>
                  <span class="action-desc">创建新的资源目录</span>
                </div>
              </button>
            </div>
          </div>

          <!-- 权限 Tabs -->
          <div class="tabs-bar hide-scrollbar">
            <div class="tabs-main">
              <button
                type="button"
                class="fs-tab"
                :class="{ active: scopeTab === 'private' }"
                @click="setScopeTab('private')"
              >
                私人资源
              </button>
              <button
                type="button"
                class="fs-tab"
                :class="{ active: scopeTab === 'public' }"
                @click="setScopeTab('public')"
              >
                公共资源
              </button>
              <span class="results-hint">{{ displayedItems.length }} 项结果</span>
            </div>

            <div class="tabs-tools">
              <a-popover
                v-model:open="typeFilterOpen"
                trigger="click"
                placement="bottomRight"
              >
                <template #content>
                  <div class="type-filter-popover" @click.stop>
                    <div class="type-filter-popover-head">
                      <span class="type-filter-popover-title">文件类型筛选</span>
                      <button
                        type="button"
                        class="type-filter-popover-clear"
                        @click="selectedFileTypes = []"
                      >
                        清空
                      </button>
                    </div>
                    <div class="type-filter-popover-options">
                      <label
                        v-for="option in quickTypeOptions"
                        :key="option.key"
                        class="type-filter-check"
                      >
                        <input
                          v-model="selectedFileTypes"
                          type="checkbox"
                          :value="option.key"
                        >
                        <span>{{ option.label }}</span>
                      </label>
                    </div>
                    <p class="type-filter-popover-hint">勾选后立即筛选展示，无需确认。</p>
                  </div>
                </template>
                <button
                  type="button"
                  class="filter-trigger"
                  :class="{ active: selectedFileTypes.length > 0 || typeFilterOpen }"
                >
                  <svg class="w-4 h-4 shrink-0 icon-sm" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"/>
                  </svg>
                  文件类型
                  <span v-if="selectedFileTypes.length > 0" class="tool-badge">{{ selectedFileTypes.length }}</span>
                </button>
              </a-popover>
              <div class="view-switch">
                <button
                  type="button"
                  class="view-switch-btn"
                  :class="{ 'is-active': viewMode === 'list' }"
                  @click.stop="setViewMode('list')"
                >
                  <svg class="w-4 h-4 shrink-0 icon-sm" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                  </svg>
                </button>
                <button
                  type="button"
                  class="view-switch-btn"
                  :class="{ 'is-active': viewMode === 'grid' }"
                  @click.stop="setViewMode('grid')"
                >
                  <svg class="w-4 h-4 shrink-0 icon-sm" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <a-spin :spinning="loading">
            <!-- List View -->
            <div v-if="viewMode === 'list'" class="list-view">
              <div class="list-header">
                <div class="list-header-name">资源名称</div>
                <div class="list-header-folder">所属目录</div>
                <div class="list-header-type">类型</div>
                <div class="list-header-size">大小</div>
                <div class="list-header-time">更新时间</div>
                <div class="list-header-actions">操作</div>
              </div>

              <div class="list-body">
                <div
                  v-for="item in displayedItems"
                  :key="item.id"
                  class="list-row group"
                  :class="{ 'list-row-highlight': item.source_kind === 'ai_generated' }"
                  @click="openPreview(item)"
                >
                  <div class="list-name-cell">
                    <div class="doc-icon" :class="getDocIconClass(item)">{{ getLibraryTypeIcon(item.content_type) }}</div>
                    <span class="list-title">{{ item.title }}</span>
                    <a-tag
                      v-if="item.status && statusLabels[item.status]"
                      :color="statusColors[item.status] || 'default'"
                      class="ml-2"
                    >{{ statusLabels[item.status] }}</a-tag>
                    <span
                      v-if="item.source_kind === 'ai_generated'"
                      class="ai-chip"
                    >AI Generated</span>
                  </div>
                  <div class="list-meta list-meta-folder">{{ item.folder_name || '根目录' }}</div>
                  <div class="list-meta list-meta-type">{{ getLibraryTypeLabel(item.content_type) }}</div>
                  <div class="list-meta list-meta-size">{{ formatFileSize(item) }}</div>
                  <div class="list-meta list-meta-time">{{ formatRelativeTime(item.updated_at || item.created_at) }}</div>
                  <div class="list-actions">
                    <button
                      v-if="item.content_type === 'knowledge'"
                      class="row-action-btn"
                      @click.stop="openKnowledgeEdit(item)"
                    >编辑</button>
                    <button
                      class="row-action-btn"
                      @click.stop="showActionMenuFromButton($event, item)"
                    >更多</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Grid View -->
            <div v-else class="grid-view">
              <div class="resource-grid">
                <article
                  v-for="item in displayedItems"
                  :key="item.id"
                  class="resource-card"
                  :class="{ 'resource-card-ai': item.source_kind === 'ai_generated' }"
                  @click="openPreview(item)"
                >
                  <div class="resource-card-cover" :class="getCardCoverClass(item)">
                    <img
                      v-if="item.content_type === 'image' && item.file_url"
                      :src="item.file_url"
                      :alt="item.title"
                      class="resource-card-image"
                    >
                    <template v-else>
                      <div class="resource-card-pattern">
                        <span class="resource-card-type-tag">{{ getLibraryTypeLabel(item.content_type) }}</span>
                        <strong class="resource-card-code">{{ getLibraryTypeIcon(item.content_type) }}</strong>
                        <p class="resource-card-pattern-text">{{ getCardPreviewText(item) }}</p>
                      </div>
                    </template>
                  </div>
                  <div class="resource-card-body">
                    <div class="resource-card-head">
                      <div class="resource-card-badges">
                        <span class="mini-badge">{{ item.folder_name || '根目录' }}</span>
                        <a-tag
                          v-if="item.status && statusLabels[item.status]"
                          :color="statusColors[item.status] || 'default'"
                          size="small"
                        >{{ statusLabels[item.status] }}</a-tag>
                        <span v-if="item.source_kind === 'ai_generated'" class="mini-badge mini-badge-ai">AI</span>
                        <span v-if="item.is_public" class="mini-badge mini-badge-public">公开</span>
                      </div>
                      <button
                        type="button"
                        class="card-menu-btn"
                        @click.stop="showActionMenuFromButton($event, item)"
                      >
                        <svg class="w-4 h-4 shrink-0 icon-sm" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6h.01M12 12h.01M12 18h.01"/>
                        </svg>
                      </button>
                    </div>
                    <h3 class="resource-card-title">{{ item.title }}</h3>
                    <p class="resource-card-desc">{{ getCardDescription(item) }}</p>
                    <div class="resource-card-meta">
                      <span>{{ item.owner_name || '未署名' }}</span>
                      <span>{{ formatRelativeTime(item.updated_at || item.created_at) }}</span>
                    </div>
                  </div>
                </article>
              </div>
            </div>

            <a-empty v-if="!loading && displayedItems.length === 0" description="当前筛选下暂无资源" class="py-12" />
          </a-spin>
        </div>
      </main>
    </div>

    <!-- 右键/更多操作菜单 -->
    <div
      v-if="contextMenu.visible && contextMenu.item"
      class="context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
    >
      <button type="button" @click="handleMoveItem(contextMenu.item)">移动到文件夹</button>
      <button type="button" @click="toggleShare(contextMenu.item)">
        {{ contextMenu.item.is_public ? '取消公开' : '共享到公共资源' }}
      </button>
      <button
        v-if="contextMenu.item.content_type === 'knowledge'"
        type="button"
        @click="openKnowledgeEdit(contextMenu.item)"
      >
        编辑知识点
      </button>
      <button type="button" class="danger" @click="handleDeleteItem(contextMenu.item)">删除资源</button>
    </div>
  </div>
</template>

<script>
import { computed, onBeforeMount, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { Modal, message } from 'ant-design-vue'
import {
  createLibraryFolder,
  deleteLibraryFolder,
  deleteLibraryItem,
  getLibraryItemDetail,
  listLibraryFolders,
  listLibraryItems,
  shareLibraryItem,
  unshareLibraryItem,
} from '@/api/library'
import {
  LIBRARY_CATEGORIES,
  buildLibraryTreeData,
  findLibraryFolderName,
  formatLibraryFileMeta,
  getLibraryTypeIcon,
  getLibraryTypeLabel,
  resolveLibraryCategoryFilter,
} from '@/utils/library-browser'
import QuickUploadModal from '@/components/library/QuickUploadModal.vue'
import KnowledgeCardModal from '@/components/library/KnowledgeCardModal.vue'
import MoveItemModal from '@/components/library/MoveItemModal.vue'

export default {
  name: 'LibraryIndex',
  components: {
    QuickUploadModal,
    KnowledgeCardModal,
    MoveItemModal,
  },
  setup() {
    const categories = LIBRARY_CATEGORIES

    const statusLabels = {
      draft: '草稿',
      pending_review: '待审核',
      reviewing: '审核中',
      published: '已发布',
      rejected: '已驳回',
    }

    const statusColors = {
      draft: 'default',
      pending_review: 'processing',
      reviewing: 'processing',
      published: 'success',
      rejected: 'error',
    }

    const loading = ref(false)
    const items = ref([])
    const folders = ref([])
    const scopeTab = ref('private')
    const selectedCategory = ref('all')
    const selectedFileTypes = ref([])
    const selectedFolderId = ref(null)
    const searchKeyword = ref('')
    const mobileSidebarOpen = ref(false)
    const viewMode = ref('list')
    const storageModalVisible = ref(false)
    const typeFilterOpen = ref(false)

    const uploadVisible = ref(false)
    const knowledgeVisible = ref(false)
    const moveVisible = ref(false)
    const previewVisible = ref(false)
    const previewItem = ref(null)
    const moveTarget = ref(null)
    const editingKnowledgeId = ref(null)
    const editingKnowledgeTitle = ref('')
    const editingKnowledgeContent = ref('')
    const createFolderVisible = ref(false)
    const folderSubmitting = ref(false)

    const folderForm = reactive({
      name: '',
      parentId: null,
    })

    const contextMenu = reactive({
      visible: false,
      x: 0,
      y: 0,
      item: null,
    })

    const avatarText = computed(() => {
      return '用户'.slice(0, 1)
    })

    const treeData = computed(() => buildLibraryTreeData(folders.value))
    const selectedFolderKeys = computed(() => selectedFolderId.value ? [selectedFolderId.value] : [])
    const folderOptions = computed(() => flattenFolders(folders.value))
    const currentFolderName = computed(() => {
      if (selectedFolderId.value) {
        return findLibraryFolderName(folders.value, selectedFolderId.value) || '未知文件夹'
      }
      return '根目录'
    })
    const currentCategoryLabel = computed(() => {
      return categories.find((item) => item.key === selectedCategory.value)?.label || '全部类型'
    })
    const quickTypeOptions = computed(() =>
      categories.filter((item) =>
        ['video', 'document', 'image', 'audio', 'knowledge'].includes(item.key),
      )
    )
    const displayedItems = computed(() => {
      let result = [...items.value]

      if (selectedFileTypes.value.length > 0) {
        result = result.filter((item) => selectedFileTypes.value.includes(item.content_type))
      }

      return result.sort((left, right) => getItemTimestamp(right) - getItemTimestamp(left))
    })
    const totalFolderCount = computed(() => countFolders(folders.value))
    const storageSummary = computed(() => {
      const sourceItems = items.value
      const totalItems = sourceItems.length
      const totalSizeBytes = sourceItems.reduce((sum, item) => sum + Number(item.size || 0), 0)
      const latestTimestamp = sourceItems.reduce((latest, item) => Math.max(latest, getItemTimestamp(item)), 0)
      const distribution = categories
        .filter((item) => item.key !== 'all')
        .map((category) => {
          const count = sourceItems.filter((item) => {
            if (category.key === 'ai_generated') {
              return item.source_kind === 'ai_generated'
            }
            return item.content_type === category.key
          }).length
          return {
            key: category.key,
            label: category.label,
            count,
            percent: totalItems > 0 ? Math.max(8, Math.round((count / totalItems) * 100)) : 0,
          }
        })
        .filter((entry) => entry.count > 0)

      return {
        totalItems,
        totalFolders: totalFolderCount.value,
        totalSize: formatBytes(totalSizeBytes),
        totalSizeBytes,
        aiItems: sourceItems.filter((item) => item.source_kind === 'ai_generated').length,
        publicItems: sourceItems.filter((item) => item.is_public).length,
        fileItems: sourceItems.filter((item) => item.source_kind === 'file').length,
        latestUpdate: latestTimestamp ? formatLocalDateTime(latestTimestamp) : '暂无更新记录',
        distribution,
      }
    })

    const CONTEXT_MENU_WIDTH = 208
    const CONTEXT_MENU_ITEM_HEIGHT = 44
    const CONTEXT_MENU_PADDING = 8
    const CONTEXT_MENU_VIEWPORT_GAP = 12

    watch(
      [scopeTab, selectedCategory, selectedFolderId],
      () => {
        fetchItems()
      },
    )

    onBeforeMount(() => {
      fetchFolders()
      fetchItems()
      document.addEventListener('click', handlePageClick)
      window.addEventListener('resize', handlePageClick)
    })

    onBeforeUnmount(() => {
      document.removeEventListener('click', handlePageClick)
      window.removeEventListener('resize', handlePageClick)
    })

    async function fetchFolders() {
      try {
        folders.value = await listLibraryFolders()
      } catch (error) {
        folders.value = []
        console.error('加载文件夹失败', error)
      }
    }

    async function fetchItems() {
      loading.value = true
      try {
        const filters = resolveLibraryCategoryFilter(selectedCategory.value)
        const response = await listLibraryItems({
          page: 1,
          size: -1,
          scope: scopeTab.value,
          category: filters.category,
          folder_id: scopeTab.value === 'private' ? selectedFolderId.value : undefined,
          search: searchKeyword.value || undefined,
          source_kind: filters.source_kind,
        })
        items.value = response.items || []
      } catch (error) {
        items.value = []
        console.error('加载资源失败', error)
      } finally {
        loading.value = false
      }
    }

    function setScopeTab(nextScope) {
      if (scopeTab.value === nextScope) return
      scopeTab.value = nextScope
      if (nextScope !== 'private') {
        selectedFolderId.value = null
      }
      fetchItems()
    }

    function setViewMode(mode) {
      viewMode.value = mode
    }

    function handleCategorySelect(category) {
      selectedCategory.value = category
    }

    function handleSearch() {
      fetchItems()
    }

    function openCreateFolder() {
      folderForm.name = ''
      folderForm.parentId = selectedFolderId.value
      createFolderVisible.value = true
    }

    function resetFolderForm() {
      createFolderVisible.value = false
      folderForm.name = ''
      folderForm.parentId = null
    }

    async function handleCreateFolder() {
      if (!folderForm.name.trim()) {
        message.warning('请输入文件夹名称')
        return
      }
      folderSubmitting.value = true
      try {
        await createLibraryFolder({
          name: folderForm.name.trim(),
          parent_id: folderForm.parentId,
        })
        message.success('文件夹已创建')
        resetFolderForm()
        await fetchFolders()
      } catch (error) {
        message.error('创建文件夹失败')
      } finally {
        folderSubmitting.value = false
      }
    }

    async function handleDeleteFolder(folderId) {
      Modal.confirm({
        title: '删除文件夹',
        content: '仅空文件夹允许删除。确认继续吗？',
        okText: '删除',
        okType: 'danger',
        cancelText: '取消',
        async onOk() {
          try {
            await deleteLibraryFolder(folderId)
            if (selectedFolderId.value === folderId) {
              selectedFolderId.value = null
            }
            message.success('文件夹已删除')
            await fetchFolders()
          } catch (error) {
            message.error('删除文件夹失败')
          }
        },
      })
    }

    async function openPreview(item) {
      try {
        previewItem.value = await getLibraryItemDetail(item.id)
        previewVisible.value = true
      } catch (error) {
        message.error('加载资源详情失败')
      }
    }

    function showContextMenu(event, item) {
      if (scopeTab.value !== 'private') return

      const actionCount = item.content_type === 'knowledge' ? 4 : 3
      const estimatedHeight = actionCount * CONTEXT_MENU_ITEM_HEIGHT + CONTEXT_MENU_PADDING * 2
      const maxX = Math.max(CONTEXT_MENU_VIEWPORT_GAP, window.innerWidth - CONTEXT_MENU_WIDTH - CONTEXT_MENU_VIEWPORT_GAP)
      const maxY = Math.max(CONTEXT_MENU_VIEWPORT_GAP, window.innerHeight - estimatedHeight - CONTEXT_MENU_VIEWPORT_GAP)

      contextMenu.visible = true
      contextMenu.x = Math.min(Math.max(CONTEXT_MENU_VIEWPORT_GAP, event.clientX), maxX)
      contextMenu.y = Math.min(Math.max(CONTEXT_MENU_VIEWPORT_GAP, event.clientY), maxY)
      contextMenu.item = item
    }

    function showActionMenuFromButton(event, item) {
      const rect = event.currentTarget?.getBoundingClientRect?.()
      const preferredX = (rect?.right || rect?.left || 0) - CONTEXT_MENU_WIDTH
      const preferredY = (rect?.bottom || 0) + 8
      showContextMenu({
        clientX: preferredX,
        clientY: preferredY,
      }, item)
    }

    function closeContextMenu() {
      contextMenu.visible = false
      contextMenu.item = null
    }

    function handlePageClick() {
      closeContextMenu()
    }

    function handleMoveItem(item) {
      moveTarget.value = item
      moveVisible.value = true
      closeContextMenu()
    }

    async function toggleShare(item) {
      try {
        if (item.is_public) {
          await unshareLibraryItem(item.id)
          message.success('已取消公开')
        } else {
          await shareLibraryItem(item.id)
          message.success('已共享到公共资源')
        }
        closeContextMenu()
        await fetchItems()
      } catch (error) {
        message.error('操作失败')
      }
    }

    function openKnowledgeCreate() {
      editingKnowledgeId.value = null
      editingKnowledgeTitle.value = ''
      editingKnowledgeContent.value = ''
      knowledgeVisible.value = true
    }

    async function openKnowledgeEdit(item) {
      try {
        const detail = await getLibraryItemDetail(item.id)
        editingKnowledgeId.value = detail.id
        editingKnowledgeTitle.value = detail.title
        editingKnowledgeContent.value = detail.knowledge_content_html || ''
        knowledgeVisible.value = true
        closeContextMenu()
      } catch (error) {
        message.error('加载知识点失败')
      }
    }

    function handleKnowledgeSaved() {
      knowledgeVisible.value = false
      handleDataRefresh()
    }

    function handleDeleteItem(item) {
      closeContextMenu()
      Modal.confirm({
        title: '删除资源',
        content: `确认删除"${item.title}"吗？`,
        okText: '删除',
        okType: 'danger',
        cancelText: '取消',
        async onOk() {
          try {
            await deleteLibraryItem(item.id)
            message.success('资源已删除')
            await fetchItems()
            await fetchFolders()
          } catch (error) {
            message.error('删除资源失败')
          }
        },
      })
    }

    function handleDataRefresh() {
      fetchItems()
      fetchFolders()
    }

    function flattenFolders(nodes, depth = 0) {
      const result = []
      ;(nodes || []).forEach((node) => {
        result.push({
          value: node.id,
          label: `${'　'.repeat(depth)}${node.name}`,
        })
        result.push(...flattenFolders(node.children || [], depth + 1))
      })
      return result
    }

    function formatDateTime(value) {
      if (!value) return '-'
      return String(value).replace('T', ' ').slice(0, 16)
    }

    function formatFileSize(item) {
      if (item.content_type === 'knowledge' || item.source_kind === 'ai_generated') {
        return '-'
      }
      return formatLibraryFileMeta(item)
    }

    function formatRelativeTime(value) {
      if (!value) return '-'
      const date = new Date(value)
      const now = new Date()
      const diffMs = now.getTime() - date.getTime()
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 1) return '刚刚'
      if (diffMins < 60) return `${diffMins}分钟前`
      if (diffHours < 24) return `${diffHours}小时前`
      if (diffDays < 7) return `${diffDays}天前`

      const month = date.getMonth() + 1
      const day = date.getDate()
      return `${month}月${day}日`
    }

    function getDocIconClass(item) {
      if (item.source_kind === 'ai_generated') return 'icon-ai'
      const map = {
        video: 'icon-vid',
        document: 'icon-doc',
        image: 'icon-img',
        audio: 'icon-aud',
        knowledge: 'icon-txt',
      }
      return map[item.content_type] || 'icon-doc'
    }

    function getItemTimestamp(item) {
      const raw = item.updated_at || item.created_at
      return raw ? new Date(raw).getTime() : 0
    }

    function countFolders(nodes) {
      return (nodes || []).reduce((sum, node) => sum + 1 + countFolders(node.children || []), 0)
    }

    function formatBytes(size) {
      if (size >= 1024 * 1024 * 1024) {
        return `${(size / 1024 / 1024 / 1024).toFixed(1)} GB`
      }
      if (size >= 1024 * 1024) {
        return `${(size / 1024 / 1024).toFixed(1)} MB`
      }
      if (size >= 1024) {
        return `${Math.round(size / 1024)} KB`
      }
      return `${size} B`
    }

    function formatLocalDateTime(timestamp) {
      const date = new Date(timestamp)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      return `${year}-${month}-${day} ${hours}:${minutes}`
    }

    function stripHtmlTags(content) {
      return String(content || '')
        .replace(/<[^>]*>/g, ' ')
        .replace(/&nbsp;/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
    }

    function getCardDescription(item) {
      if (item.content_type === 'knowledge') {
        return stripHtmlTags(item.knowledge_content_html).slice(0, 72) || '知识卡片内容预览'
      }
      if (item.source_kind === 'ai_generated') {
        return 'AI 教学资源已完成入库，可直接预览、共享与归档。'
      }
      if (item.file_name) {
        return item.file_name
      }
      return `${getLibraryTypeLabel(item.content_type)} · ${item.folder_name || '根目录'}`
    }

    function getCardPreviewText(item) {
      if (item.content_type === 'knowledge') {
        return stripHtmlTags(item.knowledge_content_html).slice(0, 60) || '知识点内容摘要'
      }
      if (item.content_type === 'document') {
        return '文档、方案、汇报、制度材料等内容预览'
      }
      if (item.content_type === 'video') {
        return '课程视频、讲解录屏与演示资料'
      }
      if (item.content_type === 'audio') {
        return '音频资源、旁白素材与语音资料'
      }
      if (item.content_type === 'image') {
        return '图片素材与视觉资料'
      }
      return '资源预览'
    }

    function getCardCoverClass(item) {
      const map = {
        video: 'cover-video',
        document: 'cover-document',
        image: 'cover-image',
        audio: 'cover-audio',
        knowledge: 'cover-knowledge',
      }
      if (item.source_kind === 'ai_generated') {
        return 'cover-ai'
      }
      return map[item.content_type] || 'cover-document'
    }

    return {
      // state
      statusLabels,
      statusColors,
      categories,
      loading,
      items,
      folders,
      scopeTab,
      selectedCategory,
      selectedFileTypes,
      selectedFolderId,
      searchKeyword,
      mobileSidebarOpen,
      viewMode,
      storageModalVisible,
      typeFilterOpen,
      uploadVisible,
      knowledgeVisible,
      moveVisible,
      previewVisible,
      previewItem,
      moveTarget,
      editingKnowledgeId,
      editingKnowledgeTitle,
      editingKnowledgeContent,
      createFolderVisible,
      folderSubmitting,
      folderForm,
      contextMenu,
      avatarText,
      quickTypeOptions,
      displayedItems,
      storageSummary,

      // computed
      treeData,
      selectedFolderKeys,
      folderOptions,
      currentFolderName,
      currentCategoryLabel,

      // methods
      fetchFolders,
      fetchItems,
      setScopeTab,
      setViewMode,
      handleCategorySelect,
      handleSearch,
      openCreateFolder,
      resetFolderForm,
      handleCreateFolder,
      handleDeleteFolder,
      openPreview,
      showContextMenu,
      showActionMenuFromButton,
      closeContextMenu,
      handlePageClick,
      handleMoveItem,
      toggleShare,
      openKnowledgeCreate,
      openKnowledgeEdit,
      handleKnowledgeSaved,
      handleDeleteItem,
      handleDataRefresh,
      formatDateTime,
      formatFileSize,
      formatRelativeTime,
      getDocIconClass,
      getCardCoverClass,
      getCardDescription,
      getLibraryTypeLabel,
      getLibraryTypeIcon,
    }
  },
}
</script>

<style scoped>
/* Hide scrollbar utility */
.hide-scrollbar::-webkit-scrollbar { display: none; }
.hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

.library-page {
  height: 100vh;
  background: #fff;
  color: #1f2329;
  overflow: hidden;
}

/* Override parent .content-area for library route — fill full viewport without scroll */
:deep(.content-area) {
  padding: 0 !important;
  overflow: hidden !important;
  height: 100vh !important;
}

.library-page svg {
  display: block;
  flex-shrink: 0;
}

.icon-xs { width: 14px; height: 14px; }
.icon-sm { width: 16px; height: 16px; }
.icon-md { width: 20px; height: 20px; }
.icon-lg { width: 24px; height: 24px; }

/* Mobile Header */
.mobile-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 48px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 50;
  /* 确保移动端头部铺满顶部，无视口偏移 */
  left: 0 !important;
  width: 100% !important;
}

.mobile-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mobile-menu-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
}

.mobile-header-title {
  color: #1f2937;
  font-size: 16px;
  font-weight: 700;
}

.mobile-avatar {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: #2563eb;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.mobile-sidebar-mask {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgba(0, 0, 0, 0.3);
}

/* Main Layout */
.library-layout {
  display: flex;
  flex-direction: row;
  height: 100vh;
  overflow: hidden;
}

@media (min-width: 769px) {
  .mobile-header {
    display: none !important;
  }
  .mobile-sidebar-mask {
    display: none !important;
  }
}

/* Mobile: full screen below mobile header */
@media (max-width: 768px) {
  .library-layout {
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }
  .mobile-sidebar-mask {
    display: block;
  }
  .library-sidebar {
    position: fixed;
    left: 0;
    top: 48px;
    bottom: 0;
    z-index: 40;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    width: 280px;
  }
  .library-sidebar.mobile-open {
    transform: translateX(0);
  }
  .library-main {
    width: 100%;
    min-height: unset;
  }
  .mobile-header {
    display: flex !important;
  }
  .main-hero,
  .tabs-bar,
  .grid-view,
  .list-header,
  .list-row {
    padding-left: 16px;
    padding-right: 16px;
  }
  .grid-view {
    padding: 18px 16px 32px;
  }
  .main-hero-head {
    flex-direction: column;
    align-items: flex-start;
  }
  .storage-grid {
    grid-template-columns: 1fr;
  }
  .storage-panel-head {
    flex-direction: column;
    align-items: flex-start;
  }
  .resource-grid {
    grid-template-columns: 1fr;
  }
  .resource-card-cover {
    aspect-ratio: 16 / 9;
  }
  .tabs-tools,
  .list-header-folder,
  .list-header-size,
  .list-meta-folder,
  .list-meta-size {
    display: none;
  }
  .list-header-type,
  .list-meta-type {
    display: none;
  }
  .list-actions {
    opacity: 1;
    width: auto;
    padding-right: 0;
  }
  .list-header-time,
  .list-meta-time {
    width: 92px;
  }
  .list-row {
    align-items: flex-start;
  }
  .tabs-bar {
    padding-right: 16px;
  }
  .tabs-tools {
    display: none;
  }
  .results-hint {
    display: none;
  }
}

@media (min-width: 769px) and (max-width: 1200px) {
  .main-hero,
  .tabs-bar,
  .grid-view,
  .list-header,
  .list-row {
    padding-left: 24px;
    padding-right: 24px;
  }
  .storage-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .grid-view {
    padding-left: 24px;
    padding-right: 24px;
  }
}

/* Secondary Sidebar */
.library-sidebar {
  width: 260px;
  background: #F9FAFB;
  border-right: 1px solid #e5e7eb;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.sidebar-inner {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding-top: 16px;
}

.sidebar-title-block {
  padding: 0 20px;
  margin-bottom: 16px;
}

.sidebar-title {
  margin: 0;
  color: #1f2937;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.sidebar-search-wrap {
  position: relative;
  padding: 0 20px;
  margin-bottom: 16px;
}

.sidebar-search-icon {
  position: absolute;
  left: 28px;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
}

.sidebar-scroll {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 24px;
}

.sidebar-section-heading {
  padding: 8px 20px;
}

.sidebar-section-label {
  color: #9ca3af;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.sidebar-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  cursor: default;
}

.folder-plus-icon {
  color: #9ca3af;
  cursor: pointer;
  transition: color 0.2s ease;
}

.group:hover .folder-plus-icon {
  color: #4b5563;
}

.folder-list {
  display: flex;
  flex-direction: column;
}

.folder-count {
  color: #9ca3af;
  font-size: 10px;
  background: #f3f4f6;
  padding: 0 6px;
  border-radius: 6px;
}

.folder-delete-btn {
  margin-left: 4px;
}

/* Search Input */
.search-input {
  background-color: #F3F4F6;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 8px 12px 8px 32px;
  font-size: 14px;
  color: #1F2329;
  transition: all 0.2s;
  width: 100%;
}
.search-input:focus {
  background-color: #FFFFFF;
  border-color: #3B82F6;
  outline: none;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

/* Sidebar Items */
.sidebar-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin: 2px 12px;
  border-radius: 6px;
  font-size: 14px;
  color: #4B5563;
  cursor: pointer;
  transition: all 0.2s;
  width: calc(100% - 24px);
  text-align: left;
  border: none;
  background: transparent;
}
.sidebar-item:hover { background-color: #F3F4F6; color: #1F2329; }
.sidebar-item.active { background-color: #E2E8F0; color: #1F2329; font-weight: 600; }
.sidebar-item.ai-resource {
  color: #4F46E5;
  font-weight: 600;
  background-color: rgba(99, 102, 241, 0.05);
  border: 1px solid rgba(99, 102, 241, 0.1);
}
.sidebar-item.ai-resource:hover { background-color: rgba(99, 102, 241, 0.1); }

/* Sidebar Folders */
.sidebar-folder {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  margin: 2px 12px;
  border-radius: 6px;
  font-size: 14px;
  color: #4B5563;
  cursor: pointer;
  transition: all 0.2s;
  width: calc(100% - 24px);
  text-align: left;
  border: none;
  background: transparent;
}
.sidebar-folder:hover { background-color: #F3F4F6; color: #1F2329; }
.sidebar-folder.active { background-color: #E2E8F0; color: #1F2329; font-weight: 600; }

/* Main Content */
.library-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  height: 100%;
  overflow: hidden;
  min-width: 0;
}

.library-main-scroll {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.main-hero {
  padding: 32px 32px 16px;
}

.main-hero-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.main-title {
  margin: 0;
  color: #1f2937;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.main-subtitle {
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 12px;
}

.main-hero-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-button {
  padding: 6px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
  color: #4b5563;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.stat-button:hover {
  background: #f9fafb;
  border-color: #d1d5db;
}

/* Storage Modal */
.storage-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.storage-panel-label {
  margin: 0 0 6px;
  color: #3b82f6;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.storage-panel-title {
  margin: 0;
  color: #0f172a;
  font-size: 18px;
  font-weight: 700;
}

.storage-panel-time {
  color: #64748b;
  font-size: 12px;
  white-space: nowrap;
}

.storage-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.storage-metric {
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid rgba(226, 232, 240, 0.85);
}

.storage-metric-label {
  display: block;
  margin-bottom: 8px;
  color: #64748b;
  font-size: 12px;
}

.storage-metric strong {
  display: block;
  color: #0f172a;
  font-size: 22px;
  font-weight: 800;
}

.storage-distribution {
  display: grid;
  gap: 10px;
}

.distribution-row {
  display: grid;
  gap: 8px;
}

.distribution-copy {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #475569;
  font-size: 12px;
}

.distribution-name {
  color: #0f172a;
  font-weight: 600;
}

.distribution-bar {
  height: 8px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.distribution-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #2563eb 0%, #60a5fa 100%);
}

.action-strip {
  display: flex;
  gap: 16px;
  overflow-x: auto;
  padding-bottom: 8px;
}

/* Action Cards */
.action-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background-color: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 180px;
  text-align: left;
}
.action-card:hover {
  border-color: #D1D5DB;
  box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.05);
  transform: translateY(-1px);
}

.action-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.action-icon-blue { background: #eff6ff; color: #2563eb; }
.action-icon-purple { background: #f3e8ff; color: #7c3aed; }
.action-icon-emerald { background: #ecfdf5; color: #059669; }
.action-icon-orange { background: #fff7ed; color: #f97316; }

.action-card:hover .action-icon-blue { background: #2563eb; color: #fff; }
.action-card:hover .action-icon-purple { background: #7c3aed; color: #fff; }
.action-card:hover .action-icon-emerald { background: #059669; color: #fff; }
.action-card:hover .action-icon-orange { background: #f97316; color: #fff; }

.action-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.action-title {
  color: #1f2937;
  font-size: 14px;
  font-weight: 700;
  transition: color 0.2s ease;
}

.action-desc {
  margin-top: 2px;
  color: #9ca3af;
  font-size: 11px;
}

.action-card:hover .action-title-blue { color: #2563eb; }
.action-card:hover .action-title-purple { color: #7c3aed; }
.action-card:hover .action-title-emerald { color: #059669; }
.action-card:hover .action-title-orange { color: #f97316; }

/* Tabs Bar */
.tabs-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 32px;
  border-bottom: 1px solid #e5e7eb;
  overflow-x: auto;
  min-height: 58px;
  background: rgba(255, 255, 255, 0.96);
}

.tabs-main {
  display: flex;
  align-items: center;
  gap: 0;
  min-width: max-content;
}

/* Feishu-style Tabs */
.fs-tab {
  padding: 12px 8px;
  font-size: 14px;
  color: #647B8B;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
  margin-right: 24px;
  background: transparent;
  border-top: none;
  border-left: none;
  border-right: none;
}
.fs-tab:hover { color: #1F2329; }
.fs-tab.active { color: #2563EB; font-weight: 600; border-bottom-color: #2563EB; }

.results-hint {
  margin-left: 8px;
  color: #94a3b8;
  font-size: 12px;
  white-space: nowrap;
}

.tabs-tools {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 4px;
  min-width: max-content;
}

.filter-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid transparent;
  border-radius: 12px;
  background: transparent;
  color: #6b7280;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.2s ease, background-color 0.2s ease, border-color 0.2s ease;
}

.filter-trigger:hover {
  color: #1f2937;
  background: #f8fafc;
}

.filter-trigger.active {
  color: #2563eb;
  background: #eff6ff;
  border-color: #bfdbfe;
}

.tool-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  background: #2563eb;
  color: #fff;
  font-size: 11px;
}

.type-filter-popover {
  width: 240px;
}

.type-filter-popover-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.type-filter-popover-title {
  color: #0f172a;
  font-size: 13px;
  font-weight: 700;
}

.type-filter-popover-clear {
  border: none;
  background: transparent;
  color: #2563eb;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.type-filter-popover-options {
  display: grid;
  gap: 8px;
}

.type-filter-check {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  background: #f8fafc;
  color: #334155;
  font-size: 12px;
  font-weight: 600;
}

.type-filter-check input {
  margin: 0;
  accent-color: #2563eb;
}

.type-filter-popover-hint {
  margin: 12px 0 0;
  color: #94a3b8;
  font-size: 11px;
  line-height: 1.5;
}

.view-switch {
  display: flex;
  gap: 4px;
  margin-left: 8px;
  padding-left: 16px;
  border-left: 1px solid #e5e7eb;
}

.view-switch-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.view-switch-btn:hover {
  background: #f3f4f6;
}

.view-switch-btn.is-active {
  background: #f3f4f6;
  color: #374151;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.06);
}

.storage-modal {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* List View */
.list-header {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  padding: 12px 32px;
  border-bottom: 1px solid #f3f4f6;
  background: rgba(255, 255, 255, 0.95);
  color: #9ca3af;
  font-size: 12px;
  font-weight: 500;
}

.list-header-name {
  flex: 1;
  min-width: 280px;
}

.list-header-folder,
.list-header-time {
  width: 128px;
  text-align: center;
}

.list-header-type,
.list-header-size {
  width: 96px;
  text-align: center;
}

.list-header-actions {
  width: 96px;
  text-align: right;
  padding-right: 8px;
}

.list-body {
  display: flex;
  flex-direction: column;
  padding-bottom: 40px;
}

.grid-view {
  padding: 20px 32px 36px;
}

.resource-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 18px;
}

.resource-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 24px;
  background: #fff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
  cursor: pointer;
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.resource-card:hover {
  transform: translateY(-3px);
  border-color: #bfdbfe;
  box-shadow: 0 18px 36px rgba(37, 99, 235, 0.12);
}

.resource-card-ai {
  border-color: rgba(196, 181, 253, 0.8);
  box-shadow: 0 16px 34px rgba(109, 40, 217, 0.08);
}

.resource-card-cover {
  position: relative;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  padding: 18px;
}

.cover-document {
  background: linear-gradient(145deg, #f8fbff 0%, #eef5ff 100%);
}

.cover-video {
  background: linear-gradient(145deg, #f5f3ff 0%, #ede9fe 100%);
}

.cover-image {
  background: linear-gradient(145deg, #fff7ed 0%, #ffedd5 100%);
}

.cover-audio {
  background: linear-gradient(145deg, #fdf4ff 0%, #fae8ff 100%);
}

.cover-knowledge {
  background: linear-gradient(145deg, #f0fdfa 0%, #ccfbf1 100%);
}

.cover-ai {
  background: linear-gradient(145deg, #eef2ff 0%, #ede9fe 52%, #f5f3ff 100%);
}

.resource-card-image {
  width: 100%;
  height: 100%;
  border-radius: 16px;
  object-fit: cover;
}

.resource-card-pattern {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  width: 100%;
  height: 100%;
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.68);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.86);
}

.resource-card-type-tag {
  display: inline-flex;
  align-self: flex-start;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.84);
  color: #475569;
  font-size: 11px;
  font-weight: 700;
}

.resource-card-code {
  margin-top: auto;
  color: #0f172a;
  font-size: 40px;
  line-height: 1;
  letter-spacing: -0.06em;
}

.resource-card-pattern-text {
  margin: 14px 0 0;
  color: #475569;
  font-size: 12px;
  line-height: 1.7;
}

.resource-card-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 12px;
  padding: 18px;
}

.resource-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.resource-card-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mini-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 9px;
  border-radius: 999px;
  background: #f8fafc;
  color: #64748b;
  font-size: 11px;
  font-weight: 700;
}

.mini-badge-ai {
  background: #ede9fe;
  color: #7c3aed;
}

.mini-badge-public {
  background: #fff7ed;
  color: #ea580c;
}

.card-menu-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f8fafc;
  color: #64748b;
  cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.card-menu-btn:hover {
  background: #eff6ff;
  color: #2563eb;
}

.resource-card-title {
  margin: 0;
  color: #0f172a;
  font-size: 17px;
  font-weight: 700;
  line-height: 1.4;
}

.resource-card-desc {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.7;
  min-height: 44px;
}

.resource-card-meta {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #94a3b8;
  font-size: 12px;
}

/* List Rows */
.list-row {
  display: flex;
  align-items: center;
  padding: 16px 32px;
  border-bottom: 1px solid #f9fafb;
  transition: background-color 0.2s ease;
  cursor: pointer;
}
.list-row:hover { background-color: #F8FAFC; }

.list-row-highlight {
  background: rgba(238, 242, 255, 0.28);
}

.list-name-cell {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  padding-right: 16px;
}

.list-title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #1f2937;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s ease;
}

.group:hover .list-title {
  color: #2563eb;
}

.ai-chip {
  display: none;
  padding: 2px 6px;
  border-radius: 6px;
  background: #e0e7ff;
  color: #4f46e5;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.list-meta {
  color: #6b7280;
  font-size: 12px;
  text-align: center;
}

.list-meta-folder,
.list-meta-time {
  width: 128px;
}

.list-meta-type,
.list-meta-size {
  width: 96px;
}

.list-meta-folder {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.list-meta-size,
.list-meta-time {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
}

.list-actions {
  width: 96px;
  padding-right: 8px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.group:hover .list-actions {
  opacity: 1;
}

.row-action-btn {
  padding: 4px 8px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  color: #4b5563;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  transition: color 0.2s ease, border-color 0.2s ease, background-color 0.2s ease;
}

.row-action-btn:hover {
  color: #111827;
  border-color: #d1d5db;
  background: #f9fafb;
}

.row-action-btn:first-child:hover {
  color: #2563eb;
}

/* Doc Icons */
.doc-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}
.icon-doc { background-color: #2563EB; }
.icon-vid { background-color: #8B5CF6; }
.icon-txt { background-color: #0F766E; }
.icon-img { background-color: #F59E0B; }
.icon-aud { background-color: #7C3AED; }
.icon-ai { background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%); }

/* Context Menu */
.context-menu {
  position: fixed;
  z-index: 1000;
  width: 208px;
  max-width: calc(100vw - 24px);
  padding: 8px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid rgba(226, 232, 240, 0.96);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
}
.context-menu button {
  width: 100%;
  border: 0;
  background: transparent;
  padding: 10px 12px;
  text-align: left;
  border-radius: 10px;
  color: #1F2329;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}
.context-menu button:hover { background: #F3F4F6; }
.context-menu button.danger { color: #EF4444; }

/* Preview Modal */
.preview-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.preview-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  color: #6B7280;
  font-size: 13px;
}
.preview-media,
.preview-iframe {
  width: 100%;
  min-height: 420px;
  border: 0;
  border-radius: 18px;
  background: #09111d;
}
.preview-audio { width: 100%; }
.preview-image-stage {
  display: flex;
  justify-content: center;
  padding: 20px;
  border-radius: 18px;
  background: #F9FAFB;
}
.preview-image {
  max-width: 100%;
  max-height: 60vh;
  object-fit: contain;
}
.preview-document {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.preview-knowledge {
  padding: 18px;
  border-radius: 18px;
  background: #F9FAFB;
  line-height: 1.9;
  color: #1F2329;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

/* Minimal utility fallbacks used by this view */
.mb-6 { margin-bottom: 24px; }
.group { position: relative; }
.pl-8 { padding-left: 32px; }
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.flex-1 { flex: 1; min-width: 0; }
.font-semibold { font-weight: 600; }
.text-gray-800 { color: #1f2937; }
.text-gray-400 { color: #9ca3af; }
.text-blue-600 { color: #2563eb; }
.bg-gray-100 { background: #f3f4f6; }
.px-1\.5 { padding-left: 6px; padding-right: 6px; }
.rounded { border-radius: 6px; }
.opacity-0 { opacity: 0; }
.transition { transition: all 0.2s ease; }
.ml-1 { margin-left: 4px; }
.mr-2 { margin-right: 8px; }

.group:hover .group-hover\:opacity-100 { opacity: 1; }
.group:hover .group-hover\:text-gray-600 { color: #4b5563; }

</style>
