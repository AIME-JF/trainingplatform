<template>
  <div class="dark-page-shell">
    <div class="dark-page-header" :class="{ 'has-filters': $slots.filters }">
      <div class="dark-header-main">
        <div class="dark-header-leading">
          <h1 class="dark-header-title">{{ title }}</h1>
          <p v-if="subtitle" class="dark-header-subtitle">{{ subtitle }}</p>
        </div>

        <div class="dark-header-search">
          <a-input
            :value="modelValue"
            class="dark-search-input"
            size="large"
            :placeholder="searchPlaceholder"
            allow-clear
            @update:value="emit('update:modelValue', $event)"
            @pressEnter="emit('search', modelValue || '')"
          >
            <template #prefix>
              <SearchOutlined class="dark-search-prefix" />
            </template>
            <template #suffix>
              <button
                type="button"
                class="dark-search-btn"
                aria-label="搜索"
                @click="emit('search', modelValue || '')"
              >
                <SearchOutlined />
              </button>
            </template>
          </a-input>
        </div>

        <div v-if="$slots.actions" class="dark-header-actions">
          <slot name="actions" />
        </div>
      </div>

      <div v-if="$slots.filters" class="dark-filter-row">
        <slot name="filters" />
      </div>

      <div v-if="$slots.extra" class="dark-extra-row">
        <slot name="extra" />
      </div>
    </div>

    <div class="dark-page-body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { SearchOutlined } from '@ant-design/icons-vue'

interface Props {
  title: string
  subtitle?: string
  searchPlaceholder?: string
  modelValue?: string
}

withDefaults(defineProps<Props>(), {
  subtitle: '',
  searchPlaceholder: '搜索…',
  modelValue: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  search: [value: string]
}>()
</script>

<style scoped>
/* ── shell ── */
.dark-page-shell {
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

/* ── header ── */
.dark-page-header {
  position: sticky;
  top: 0;
  z-index: 12;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 20px 24px 18px;
  background: var(--v2-bg-header);
  backdrop-filter: blur(16px);
}

/* ── main row ── */
.dark-header-main {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  grid-template-areas: 'leading search actions';
  align-items: center;
  gap: 18px;
}

.dark-header-leading {
  grid-area: leading;
}

.dark-header-title {
  margin: 0;
  font-family: SimHei, 'Microsoft YaHei', sans-serif;
  font-size: 22px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.94);
  white-space: nowrap;
}

.dark-header-subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.48);
}

/* ── search ── */
.dark-header-search {
  grid-area: search;
  width: min(100%, 520px);
  min-width: 0;
}

.dark-header-search :deep(.dark-search-input.ant-input-affix-wrapper) {
  height: 48px;
  padding: 6px 8px 6px 18px;
  border: none !important;
  border-radius: 22px;
  background: transparent !important;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.16);
}

.dark-header-search :deep(.dark-search-input.ant-input-affix-wrapper:hover),
.dark-header-search :deep(.dark-search-input.ant-input-affix-wrapper-focused) {
  background: transparent !important;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.24);
}

.dark-header-search :deep(.dark-search-input > input.ant-input) {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.96);
  background: transparent !important;
}

.dark-header-search :deep(.dark-search-input > input.ant-input::placeholder) {
  color: rgba(255, 255, 255, 0.50);
}

.dark-header-search :deep(.dark-search-input .ant-input-prefix),
.dark-header-search :deep(.dark-search-input .ant-input-suffix),
.dark-header-search :deep(.dark-search-input .ant-input-clear-icon) {
  background: transparent !important;
  color: rgba(255, 255, 255, 0.7);
}

.dark-search-prefix {
  color: rgba(255, 255, 255, 0.68);
  font-size: 17px;
}

.dark-search-btn {
  border: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  border-radius: 999px;
  background: transparent;
  color: #fff;
  font-size: 15px;
  cursor: pointer;
  transition: transform 0.2s, color 0.2s;
}

.dark-search-btn:hover {
  transform: translateY(-1px);
  color: rgba(255, 255, 255, 0.82);
}

/* ── actions ── */
.dark-header-actions {
  grid-area: actions;
  display: flex;
  align-items: center;
  gap: 10px;
}

/* ── filter chips row ── */
.dark-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

/* expose chip style as global class so pages can use it */
.dark-filter-row :deep(.dark-chip) {
  min-height: 36px;
  padding: 0 16px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.72);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, border-color 0.2s, transform 0.2s;
}

.dark-filter-row :deep(.dark-chip:hover) {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.09);
  transform: translateY(-1px);
}

.dark-filter-row :deep(.dark-chip.active) {
  border-color: transparent;
  background: #fff;
  color: #050505;
  box-shadow: 0 10px 22px rgba(255, 255, 255, 0.10);
}

/* ── extra row ── */
.dark-extra-row {
  /* reserve for collapsible advanced filters */
}

/* ── body ── */
.dark-page-body {
  flex: 1;
  padding: 20px 24px 24px;
}

/* ── mobile ── */
@media (max-width: 768px) {
  .dark-page-header {
    padding: 16px 16px 14px;
    gap: 12px;
  }

  .dark-header-main {
    grid-template-columns: minmax(0, 1fr) auto;
    grid-template-areas:
      'leading actions'
      'search search';
    gap: 12px;
  }

  .dark-header-title {
    font-size: 19px;
  }

  .dark-header-search {
    width: 100%;
  }

  .dark-header-actions {
    align-self: start;
  }

  .dark-filter-row {
    gap: 8px;
  }

  .dark-filter-row :deep(.dark-chip) {
    min-height: 32px;
    padding: 0 13px;
    font-size: 13px;
  }

  .dark-page-body {
    padding: 16px 16px 20px;
  }
}
</style>
