<template>
  <div class="auth-layout">
    <div class="auth-card">
      <div class="auth-header">
        <h1 class="auth-title">智慧教育训练平台</h1>
      </div>
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.auth-layout {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #001234 0%, #003087 50%, #001849 100%);
  padding: 16px;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: var(--police-radius-lg);
  padding: 32px 24px;
  box-shadow: var(--police-shadow-lg);
}

.auth-header {
  text-align: center;
  margin-bottom: 32px;
}

.auth-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--police-primary);
  margin: 0;
}
</style>
