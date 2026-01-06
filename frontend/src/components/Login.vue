<template>
  <div class="login-background-optimized">
    <div class="login-slogan">
      <h2>规范管理提效能，精准保障强战力</h2>
    </div>
    <div class="login-container">
      <el-card class="login-card" style="width: 400px;">
      <template #header>
        <div class="card-header">
          <span>用户登录</span>
        </div>
      </template>
      
      <el-form ref="loginForm" :model="formData" size="default">
        <el-form-item prop="username" :rules="[{ required: true, message: '请输入用户名', trigger: 'blur' }]" style="width: 100%; max-width: 320px; margin: 0 auto 20px auto;">
          <el-input v-model="formData.username" placeholder="请输入用户名" :prefix-icon="User" style="width: 100%;"/>
        </el-form-item>
        
        <el-form-item prop="password" :rules="[{ required: true, message: '请输入密码', trigger: 'blur' }]" style="width: 100%; max-width: 320px; margin: 0 auto;">
          <el-input v-model="formData.password" type="password" placeholder="请输入密码" :prefix-icon="Lock" show-password style="width: 100%;"/>
        </el-form-item>
        
        <div class="login-button-container">
          <el-button type="primary" style="width: 100%;" :loading="loading" @click="handleLogin">
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </div>
      </el-form>
      
      <!-- 隐藏注册入口，使用 Ctrl+Shift+A 快捷键打开注册页面 -->
    </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { User, Lock } from '@element-plus/icons-vue';
import { authAPI } from '../services/api';
import { useRouter } from 'vue-router';
import { PerformanceMonitor } from '../utils/performanceMonitor';

const router = useRouter();
const formData = ref({
  username: '',
  password: ''
});
const loading = ref(false);
const performanceMonitor = new PerformanceMonitor();

// 保存表单数据到本地存储（仅在开发环境下）
const saveFormData = () => {
  if (process.env.NODE_ENV === 'development') {
    try {
      localStorage.setItem('loginFormData', JSON.stringify({
        username: formData.value.username
        // 注意：出于安全考虑，不保存密码
      }));
    } catch (err) {
      console.warn('保存表单数据失败:', err);
    }
  }
};

// 从本地存储恢复表单数据
const restoreFormData = () => {
  if (process.env.NODE_ENV === 'development') {
    try {
      const savedData = localStorage.getItem('loginFormData');
      if (savedData) {
        const parsed = JSON.parse(savedData);
        if (parsed.username) {
          formData.value.username = parsed.username;
        }
      }
    } catch (err) {
      console.warn('恢复表单数据失败:', err);
    }
  }
};



const navigateToRegister = () => {
  router.push('/register');
};

// Ctrl+Shift+A 快捷键监听
const handleKeyPress = (event) => {
  // 检测 Ctrl+Shift+A 组合键
  if (event.ctrlKey && event.shiftKey && event.key === 'A') {
    event.preventDefault(); // 阻止默认行为
    navigateToRegister();
  }
};

const handleLogin = async () => {
  loading.value = true;
  
  // 登录前保存表单数据
  saveFormData();
  
  try {
    await authAPI.login(formData.value);
    // 登录成功后清除保存的表单数据
    if (process.env.NODE_ENV === 'development') {
      localStorage.removeItem('loginFormData');
    }
    
    ElMessage.success('登录成功');
    
    // 登录成功后启动Redis状态检查
    if (window.startRedisStatusCheck) {
      window.startRedisStatusCheck();
    }
    
    router.push('/');
  } catch (err) {
    // 确保捕获错误时不清空表单数据
    const errorMessage = err.response?.data?.detail || '登录失败，请检查用户名和密码';
    
    // 使用消息组件防护，避免null值
    ElMessage.error(errorMessage || '登录失败，请重试');
    
    // 保留表单数据，不进行任何清空操作
    console.log('登录失败，保留表单数据:', {
      username: formData.value.username,
      hasPassword: !!formData.value.password
    });
    
    // 确保表单数据不被意外修改
    if (!formData.value.username || !formData.value.password) {
      console.warn('检测到表单数据可能被清空，尝试恢复...');
      restoreFormData();
    }
  } finally {
    loading.value = false;
  }
};

// 组件挂载时恢复表单数据和性能监控
onMounted(() => {
  restoreFormData();
  
  // 添加键盘事件监听
  window.addEventListener('keydown', handleKeyPress);
  
  // 开始性能监控
  performanceMonitor.recordCoreWebVitals();
  
  // 监控背景图片加载
  const backgroundElement = document.querySelector('.login-background-optimized');
  if (backgroundElement) {
    const computedStyle = window.getComputedStyle(backgroundElement);
    const backgroundImage = computedStyle.backgroundImage;
    
    // 提取图片URL并监控加载
    const imageUrl = backgroundImage.replace(/url\(["']?(.*?)["']?\)/, '$1');
    if (imageUrl && imageUrl !== 'none') {
      const loadStart = performanceMonitor.startImageLoad(imageUrl);
      
      const img = new Image();
      img.onload = () => {
        performanceMonitor.endImageLoad(imageUrl, loadStart);
        performanceMonitor.calculateTotalLoadTime();
        
        // 开发环境下生成性能报告
        if (process.env.NODE_ENV === 'development') {
          setTimeout(() => {
            performanceMonitor.generateReport();
          }, 1000);
        }
      };
      img.src = imageUrl;
    }
  }
});

// 组件卸载时移除键盘事件监听
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyPress);
});
</script>

<style>
/* 全局样式重置，确保全屏显示 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

#app {
  width: 100%;
  height: 100%;
}
</style>

<style scoped>
/* 导入优化后的背景图片配置 */
@import url('../assets/background/background-config.css');

.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  min-height: 100vh;
  position: relative;
  z-index: 1;
  margin: 0;
  padding: 0 20px;
}

.login-slogan {
  position: absolute;
  top: 7%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
  z-index: 2;
  width: 100%;
}

.login-slogan h2 {
  font-size: 40px;
  font-weight: 600;
  letter-spacing: 1px;
  margin: 0;
  line-height: 1.4;
}

.login-background-optimized {
  width: 100vw;
  height: 100vh;
  min-height: 100vh;
  position: relative;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.login-card {
  position: relative;
  z-index: 2;
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(5px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
  background-color: rgba(64, 158, 255, 0.3);
  color: white;
  padding: 12px 0;
  margin: -20px -20px -20px -20px;
}

/* 确保登录按钮居中的样式 */
.el-form {
  width: 100%;
}

/* 登录按钮容器样式 */
.login-button-container {
  margin-top: 20px;
  width: 100%;
}

/* 确保登录按钮居中 */
.login-button-container .el-button {
  width: 100%;
  max-width: 320px;
  display: block;
  margin: 0 auto;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .login-card {
    width: 90% !important;
    margin: 0 auto;
  }
  
  .el-form-item {
    max-width: 100% !important;
  }
}

/* 加载动画 */
.login-background-optimized {
  animation: fadeIn 0.8s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
</style>