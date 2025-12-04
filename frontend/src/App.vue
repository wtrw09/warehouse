<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import router from './router'
</script>

<style>
/* 全局样式 - 为Element Plus组件提供适当的基础样式 */
body {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 确保路由视图能正确填充容器 */
#app {
  width: 100%;
  height: 100vh;
}
</style>
