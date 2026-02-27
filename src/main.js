import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

import App from './App.vue'
import router from './router/index.js'
import './assets/styles/global.css'
import { useAuthStore } from './stores/auth.js'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(Antd)

// 启动时从 localStorage 恢复用户状态，确保刷新后 pinia store 有数据
const authStore = useAuthStore()
authStore.restoreFromStorage()

app.mount('#app')
