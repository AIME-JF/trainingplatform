<template>
  <a-card v-if="recommendedAction" :bordered="false" style="margin-bottom:16px" class="next-step-card">
    <div class="next-step-kicker">推荐下一步</div>
    <div class="next-step-title">{{ recommendedAction.title }}</div>
    <div class="next-step-desc">{{ recommendedAction.description }}</div>
    <permissions-tooltip
      v-if="recommendedAction.tooltip"
      :allowed="recommendedAction.allowed"
      :tips="recommendedAction.tooltip"
      block
      v-slot="{ disabled }"
    >
      <a-button
        block
        :type="recommendedAction.type"
        :danger="recommendedAction.danger"
        :ghost="recommendedAction.ghost"
        :disabled="disabled"
        @click="recommendedAction.onClick"
      >
        {{ recommendedAction.buttonText }}
      </a-button>
    </permissions-tooltip>
    <a-button
      v-else
      block
      :type="recommendedAction.type"
      :danger="recommendedAction.danger"
      :ghost="recommendedAction.ghost"
      @click="recommendedAction.onClick"
    >
      {{ recommendedAction.buttonText }}
    </a-button>
    <div v-if="recommendedAction.secondaryActions?.length" class="next-step-secondary-actions">
      <template v-for="action in recommendedAction.secondaryActions" :key="action.key || action.buttonText">
        <permissions-tooltip
          v-if="action.tooltip"
          :allowed="action.allowed"
          :tips="action.tooltip"
          block
          v-slot="{ disabled }"
        >
          <a-button
            block
            :type="action.type"
            :danger="action.danger"
            :ghost="action.ghost"
            :disabled="disabled"
            @click="action.onClick"
          >
            {{ action.buttonText }}
          </a-button>
        </permissions-tooltip>
        <a-button
          v-else
          block
          :type="action.type"
          :danger="action.danger"
          :ghost="action.ghost"
          @click="action.onClick"
        >
          {{ action.buttonText }}
        </a-button>
      </template>
    </div>
  </a-card>
</template>

<script setup>
import PermissionsTooltip from '@/components/common/PermissionsTooltip.vue'

defineProps({
  recommendedAction: { type: Object, default: null },
})
</script>

<style scoped>
.next-step-card { background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%); border: 1px solid #dbeafe; }
.next-step-kicker { font-size: 12px; font-weight: 700; color: #2563eb; letter-spacing: 0.08em; text-transform: uppercase; }
.next-step-title { margin-top: 8px; font-size: 20px; font-weight: 700; color: #0f172a; }
.next-step-desc { margin: 10px 0 16px; color: #475569; line-height: 1.7; font-size: 13px; }
.next-step-secondary-actions { display: flex; flex-direction: column; gap: 10px; margin-top: 12px; }
</style>
