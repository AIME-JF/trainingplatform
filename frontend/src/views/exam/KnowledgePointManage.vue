<template>
  <div class="kp-page">
    <main class="main-content">
      <div class="content-wrapper">
        <div class="sub-nav-bar">
          <div class="sub-nav-left">
            <span class="sub-nav-item active">知识点</span>
          </div>
        </div>

        <div class="main-container">
          <knowledge-point-panel />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import KnowledgePointPanel from './components/KnowledgePointPanel.vue'
</script>

<style scoped>
.kp-page {
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
  font-size: 18px;
  font-weight: 600;
  color: #1E293B;
  padding-bottom: 8px;
  border-bottom: 2px solid #2563EB;
}

.main-container {
  background: white;
  border: 1px solid #E2E8F0;
  border-radius: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 500px;
}
</style>
