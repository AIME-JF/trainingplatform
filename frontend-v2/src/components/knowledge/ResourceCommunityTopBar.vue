<template>
  <div class="community-topbar" :class="{ 'has-filter': showFilter }">
    <div class="community-topbar-main">
      <div class="community-topbar-leading">
        <div class="community-channel-switch" role="tablist" aria-label="资源社区频道">
          <button
            type="button"
            class="channel-tab"
            :class="{ active: activeTab === 'recommended' }"
            @click="emit('tabChange', 'recommended')"
          >
            推荐
          </button>
          <button
            type="button"
            class="channel-tab"
            :class="{ active: activeTab === 'featured' }"
            @click="emit('tabChange', 'featured')"
          >
            精选
          </button>
        </div>
      </div>

      <div v-if="showSearch" class="community-search">
        <a-input
          :value="keyword"
          class="community-search-input"
          size="large"
          :placeholder="placeholder"
          allow-clear
          @update:value="handleKeywordChange"
          @pressEnter="emitSearch"
        >
          <template #prefix>
            <SearchOutlined class="community-search-icon" />
          </template>
          <template #suffix>
            <button
              type="button"
              class="community-search-trigger"
              :aria-label="searching ? '搜索中' : '执行搜索'"
              :disabled="searching"
              @click="emitSearch"
            >
              <SearchOutlined class="community-search-trigger-icon" />
            </button>
          </template>
        </a-input>
      </div>

      <div v-if="$slots.actions" class="community-topbar-actions">
        <slot name="actions" />
      </div>
    </div>

    <div v-if="showFilter" class="community-filter-row" role="tablist" aria-label="资源类型筛选">
      <button
        v-for="item in typeOptions"
        :key="item.value || 'all'"
        type="button"
        class="filter-chip"
        :class="{ active: contentType === item.value }"
        @click="emit('update:contentType', item.value)"
      >
        {{ item.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { SearchOutlined } from '@ant-design/icons-vue'

interface Props {
  activeTab: 'recommended' | 'featured'
  keyword?: string
  contentType?: string
  placeholder?: string
  showSearch?: boolean
  showFilter?: boolean
  searching?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  keyword: '',
  contentType: '',
  placeholder: '搜索标题、简介、作者或标签',
  showSearch: true,
  showFilter: false,
  searching: false,
})

const emit = defineEmits<{
  'update:keyword': [value: string]
  'update:contentType': [value: string]
  search: [value: string]
  tabChange: [tab: 'recommended' | 'featured']
}>()

const typeOptions = [
  { value: '', label: '全部' },
  { value: 'video', label: '视频' },
  { value: 'document', label: '文档' },
  { value: 'image', label: '图片' },
]

function handleKeywordChange(value: string) {
  emit('update:keyword', value)
}

function emitSearch() {
  emit('search', props.keyword || '')
}
</script>

<style scoped>
.community-topbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.community-topbar-main {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  grid-template-areas: 'leading search actions';
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.community-topbar-leading {
  grid-area: leading;
  display: flex;
  align-items: center;
}

.community-search {
  grid-area: search;
  width: min(100%, 520px);
  min-width: 0;
}

.community-topbar-actions {
  grid-area: actions;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex: 0 0 auto;
}

.community-search :deep(.community-search-input.ant-input-affix-wrapper) {
  height: 54px;
  padding: 7px 8px 7px 18px;
  border: none !important;
  border-radius: 22px;
  background: transparent !important;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(8px);
}

.community-search :deep(.community-search-input.ant-input-affix-wrapper:hover),
.community-search :deep(.community-search-input.ant-input-affix-wrapper-focused) {
  background: transparent !important;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.22);
}

.community-search :deep(.community-search-input.ant-input-affix-wrapper > input.ant-input) {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.96);
  background: transparent !important;
}

.community-search :deep(.community-search-input.ant-input-affix-wrapper > input.ant-input::placeholder) {
  color: rgba(255, 255, 255, 0.58);
}

.community-search :deep(.community-search-input.ant-input-affix-wrapper .ant-input-prefix),
.community-search :deep(.community-search-input.ant-input-affix-wrapper .ant-input-suffix),
.community-search :deep(.community-search-input.ant-input-affix-wrapper .ant-input-clear-icon) {
  background: transparent !important;
  color: rgba(255, 255, 255, 0.7);
}

.community-search-icon {
  color: rgba(255, 255, 255, 0.74);
  font-size: 18px;
}

.community-search-trigger {
  border: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  min-width: 38px;
  height: 38px;
  padding: 0;
  border-radius: 999px;
  background: transparent;
  color: #fff;
  cursor: pointer;
  box-shadow: none;
  transition:
    transform 0.2s ease,
    color 0.2s ease,
    opacity 0.2s ease;
}

.community-search-trigger:hover:not(:disabled) {
  transform: translateY(-1px);
  color: rgba(255, 255, 255, 0.82);
}

.community-search-trigger:disabled {
  cursor: not-allowed;
  opacity: 0.68;
}

.community-search-trigger-icon {
  font-size: 16px;
}

.community-channel-switch {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border-radius: 22px;
  background: rgba(14, 20, 31, 0.34);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.12),
    0 16px 30px rgba(4, 10, 18, 0.18);
  backdrop-filter: blur(12px);
}

.channel-tab {
  border: none;
  background: transparent;
  min-width: 78px;
  padding: 8px 16px;
  border-radius: 16px;
  color: rgba(255, 255, 255, 0.72);
  font-family: SimHei, 'Microsoft YaHei', sans-serif;
  font-size: 20px;
  font-weight: 700;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.channel-tab:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.16);
}

.channel-tab.active {
  background: rgba(255, 255, 255, 0.94);
  color: #111827;
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(255, 255, 255, 0.16);
}

.community-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-chip {
  min-height: 38px;
  padding: 0 16px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.72);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    border-color 0.2s ease,
    transform 0.2s ease;
}

.filter-chip:hover {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.09);
  transform: translateY(-1px);
}

.filter-chip.active {
  border-color: transparent;
  background: #fff;
  color: #050505;
  box-shadow: 0 12px 24px rgba(255, 255, 255, 0.12);
}

@media (max-width: 1024px) {
  .community-search {
    width: min(100%, 460px);
  }
}

@media (max-width: 768px) {
  .community-topbar-main {
    grid-template-columns: minmax(0, 1fr) auto;
    grid-template-areas:
      'leading actions'
      'search search';
    align-items: start;
    gap: 12px;
  }

  .community-search {
    width: 100%;
    margin-left: 0;
  }

  .community-topbar-actions {
    justify-self: end;
    align-self: start;
  }

  .community-channel-switch {
    align-self: flex-start;
    width: max-content;
  }

  .channel-tab {
    min-width: 72px;
    padding: 8px 14px;
    font-size: 18px;
  }

  .community-filter-row {
    gap: 8px;
  }

  .filter-chip {
    min-height: 34px;
    padding: 0 14px;
    font-size: 13px;
  }
}
</style>
