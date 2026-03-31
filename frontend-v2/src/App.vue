<template>
  <a-config-provider :theme="antThemeConfig" :locale="zhCN">
    <router-view />
  </a-config-provider>
</template>

<script setup lang="ts">
import zhCN from 'ant-design-vue/es/locale/zh_CN'
import { antThemeConfig } from '@/styles/theme'
</script>
