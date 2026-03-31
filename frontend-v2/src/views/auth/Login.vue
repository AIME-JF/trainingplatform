<template>
  <a-form
    :model="form"
    layout="vertical"
    @finish="handleLogin"
  >
    <a-form-item label="用户名" name="username" :rules="[{ required: true, message: '请输入用户名' }]">
      <a-input v-model:value="form.username" placeholder="请输入用户名" size="large" />
    </a-form-item>

    <a-form-item label="密码" name="password" :rules="[{ required: true, message: '请输入密码' }]">
      <a-input-password v-model:value="form.password" placeholder="请输入密码" size="large" />
    </a-form-item>

    <a-form-item>
      <a-button type="primary" html-type="submit" block size="large" :loading="loading">
        登录
      </a-button>
    </a-form-item>

    <div class="quick-login">
      <span class="quick-label">快速体验：</span>
      <a-button size="small" @click="quickLogin('instructor', 'teach2025')">教官登录</a-button>
      <a-button size="small" @click="quickLogin('student', 'learn2025')">学员登录</a-button>
    </div>
  </a-form>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const form = reactive({
  username: '',
  password: '',
})

async function handleLogin() {
  loading.value = true
  try {
    await authStore.loginWithCredentials(form.username, form.password)
    message.success('登录成功')
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : '登录失败')
  } finally {
    loading.value = false
  }
}

function quickLogin(username: string, password: string) {
  form.username = username
  form.password = password
  handleLogin()
}
</script>

<style scoped>
.quick-login {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  margin-top: 16px;
}

.quick-label {
  font-size: 13px;
  color: var(--police-text-muted);
}
</style>
