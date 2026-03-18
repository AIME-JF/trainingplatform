<template>
  <a-card title="签到率统计" :bordered="false">
    <div class="checkin-summary" style="display: flex; justify-content: space-around; align-items: center">
      <div style="text-align: center">
        <a-progress type="circle" :percent="startCheckinRate" :size="100" />
        <div style="margin-top: 8px; font-weight: 500">开班签到率</div>
      </div>
      <div style="text-align: center">
        <a-progress type="circle" :percent="totalCourseRate" :size="100" :stroke-color="{ '0%': '#003087', '100%': '#52c41a' }" />
        <div style="margin-top: 8px; font-weight: 500">课程总签到率</div>
      </div>
    </div>
  </a-card>
</template>

<script setup>
defineProps({
  startCheckinRate: { type: Number, default: 0 },
  totalCourseRate: { type: Number, default: 0 },
})
</script>

<style scoped>
.checkin-summary { display: flex; align-items: center; gap: 20px; justify-content: space-around; }
</style>
