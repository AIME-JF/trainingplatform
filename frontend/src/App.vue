<template>
  <a-config-provider :locale="zhCN">
    <router-view />
  </a-config-provider>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth.js'
import zhCN from "ant-design-vue/es/locale/zh_CN";

const authStore = useAuthStore()
onMounted(() => {
  authStore.restoreFromStorage()
})
</script>
