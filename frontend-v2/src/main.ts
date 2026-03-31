import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue'
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

import './styles/variables.css'
import './styles/global.css'
import './styles/resource-theme.css'
import './styles/mobile.css'
import 'ant-design-vue/dist/reset.css'

dayjs.locale('zh-cn')

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(Antd)

// 挂载前恢复登录状态
const authStore = useAuthStore()
authStore.restoreFromStorage().finally(() => {
  app.mount('#app')
})
