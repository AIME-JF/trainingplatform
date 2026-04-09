<template>
  <div class="assistant-nav">
    <section
      v-for="group in groups"
      :key="group.key"
      class="assistant-nav-group"
    >
      <div class="assistant-nav-group-head">
        <span class="assistant-nav-group-label">{{ group.title }}</span>
        <p class="assistant-nav-group-desc">{{ group.description }}</p>
      </div>

      <div class="assistant-nav-grid">
        <button
          v-for="item in group.items"
          :key="item.key"
          type="button"
          class="assistant-nav-card"
          :class="{ active: item.key === activeKey }"
          @click="$emit('select', item.key)"
        >
          <span class="assistant-nav-icon">
            <component :is="item.icon" />
          </span>
          <span class="assistant-nav-copy">
            <strong>{{ item.title }}</strong>
            <span>{{ item.description }}</span>
          </span>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { AssistantPanelKey, AssistantWorkbenchGroup } from './assistantWorkbench'

defineProps<{
  activeKey: AssistantPanelKey
  groups: AssistantWorkbenchGroup[]
}>()

defineEmits<{
  select: [key: AssistantPanelKey]
}>()
</script>

<style scoped>
.assistant-nav {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.assistant-nav-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.assistant-nav-group-head {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.assistant-nav-group-label {
  color: #11224d;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.assistant-nav-group-desc {
  color: #7f8aa8;
  font-size: 12px;
  line-height: 1.6;
  margin: 0;
}

.assistant-nav-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.assistant-nav-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  width: 100%;
  padding: 16px;
  border: 1px solid rgba(225, 231, 244, 0.96);
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 249, 255, 0.94) 100%);
  text-align: left;
  cursor: pointer;
  transition: transform 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease;
}

.assistant-nav-card:hover {
  transform: translateY(-2px);
  border-color: rgba(75, 110, 245, 0.22);
  box-shadow: 0 16px 28px rgba(48, 71, 122, 0.08);
}

.assistant-nav-card.active {
  border-color: rgba(75, 110, 245, 0.26);
  background: linear-gradient(180deg, rgba(240, 244, 255, 0.98) 0%, rgba(250, 252, 255, 0.96) 100%);
  box-shadow:
    inset 0 0 0 1px rgba(75, 110, 245, 0.12),
    0 18px 32px rgba(75, 110, 245, 0.08);
}

.assistant-nav-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(75, 110, 245, 0.16) 0%, rgba(75, 110, 245, 0.08) 100%);
  color: var(--v2-primary);
  font-size: 22px;
  flex-shrink: 0;
}

.assistant-nav-card.active .assistant-nav-icon {
  background: linear-gradient(135deg, #274fd6 0%, #4b6ef5 100%);
  color: #fff;
  box-shadow: 0 14px 24px rgba(75, 110, 245, 0.24);
}

.assistant-nav-copy {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}

.assistant-nav-copy strong {
  color: #132450;
  font-size: 15px;
  line-height: 1.35;
}

.assistant-nav-copy span {
  color: #6e7a99;
  font-size: 13px;
  line-height: 1.65;
}

@media (max-width: 768px) {
  .assistant-nav-group {
    gap: 10px;
  }

  .assistant-nav-grid {
    display: grid;
    grid-auto-flow: column;
    grid-auto-columns: minmax(240px, 1fr);
    overflow-x: auto;
    gap: 12px;
    padding-bottom: 4px;
    scrollbar-width: none;
  }

  .assistant-nav-grid::-webkit-scrollbar {
    display: none;
  }
}
</style>
