import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import 'ant-design-vue/dist/reset.css'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

import App from './App.vue'
import router from './router/index.js'
import './assets/styles/global.css'
import { useAuthStore } from './stores/auth.js'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
dayjs.locale('zh-cn')
app.use(Antd, { locale: zhCN })

// 启动时从 localStorage 恢复用户状态，确保刷新后 pinia store 有数据
const authStore = useAuthStore()
authStore.restoreFromStorage()

app.mount('#app')
