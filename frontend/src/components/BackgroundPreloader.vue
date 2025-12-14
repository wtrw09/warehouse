<template>
  <!-- 图片预加载组件，在登录页之前加载背景图片 -->
  <div v-if="showPreloader" class="background-preloader">
    <div class="loading-spinner">
      <div class="spinner"></div>
      <p>正在加载背景...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const showPreloader = ref(true);
const imagesLoaded = ref(false);

// 预加载图片列表 - 使用 Vite 的静态资源导入方式
const backgroundImages = [
  new URL('../assets/background/login-background-small.jpg', import.meta.url).href,
  new URL('../assets/background/login-background-medium.jpg', import.meta.url).href,
  new URL('../assets/background/login-background-original.jpg', import.meta.url).href,
  new URL('../assets/background/login-background-small.webp', import.meta.url).href,
  new URL('../assets/background/login-background-medium.webp', import.meta.url).href,
  new URL('../assets/background/login-background-original.webp', import.meta.url).href
];

// 预加载图片
const preloadImages = () => {
  const promises = backgroundImages.map(src => {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = resolve;
      img.onerror = reject;
      img.src = src;
    });
  });

  Promise.all(promises)
    .then(() => {
      imagesLoaded.value = true;
      console.log('✅ 所有背景图片预加载完成');
      
      // 延迟隐藏预加载器，确保图片完全加载
      setTimeout(() => {
        showPreloader.value = false;
        // 触发自定义事件，通知登录页可以显示
        window.dispatchEvent(new CustomEvent('backgroundPreloaded'));
      }, 500);
    })
    .catch(error => {
      console.warn('⚠️ 部分图片预加载失败:', error);
      console.error('失败的图片路径:', backgroundImages);
      // 即使部分图片加载失败，也继续显示页面
      imagesLoaded.value = true;
      showPreloader.value = false;
      window.dispatchEvent(new CustomEvent('backgroundPreloaded'));
    });
};

// 组件挂载时开始预加载
onMounted(() => {
  console.log('🚀 开始预加载背景图片...');
  preloadImages();
  
  // 设置超时保护，防止无限等待
  setTimeout(() => {
    if (!imagesLoaded.value) {
      console.warn('⏰ 预加载超时，强制显示页面');
      showPreloader.value = false;
      window.dispatchEvent(new CustomEvent('backgroundPreloaded'));
    }
  }, 10000); // 10秒超时
});

// 组件卸载时清理
onUnmounted(() => {
  showPreloader.value = false;
});
</script>

<style scoped>
.background-preloader {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  transition: opacity 0.5s ease-out;
}

.loading-spinner {
  text-align: center;
  color: white;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top: 3px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

p {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

/* 淡出动画 */
.background-preloader.fade-out {
  opacity: 0;
  pointer-events: none;
}
</style>