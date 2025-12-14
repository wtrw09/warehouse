<template>
  <div id="app">
    <BackgroundPreloader v-if="showPreloader" />
    <router-view v-show="!showPreloader" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import BackgroundPreloader from './components/BackgroundPreloader.vue';

const router = useRouter();
const showPreloader = ref(true);

// 监听背景预加载完成事件
const handleBackgroundPreloaded = () => {
  console.log('🎉 背景预加载完成，显示主页面');
  showPreloader.value = false;
};

onMounted(() => {
  // 监听预加载完成事件
  window.addEventListener('backgroundPreloaded', handleBackgroundPreloaded);
  
  // 如果是登录页，立即显示（避免双重预加载）
  if (window.location.pathname === '/login' || window.location.pathname === '/') {
    console.log('🔍 检测到登录页，跳过预加载器');
    showPreloader.value = false;
  }
});
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
