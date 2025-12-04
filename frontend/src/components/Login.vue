<template>
  <div class="login-container">
    <el-card class="login-card" style="width: 400px;">
      <template #header>
        <div class="card-header">
          <span>用户登录</span>
        </div>
      </template>
      
      <el-form ref="loginForm" :model="formData" label-width="80px" size="default">
        <el-form-item label="用户名" prop="username" :rules="[{ required: true, message: '请输入用户名', trigger: 'blur' }]">
          <el-input v-model="formData.username" placeholder="请输入用户名" :prefix-icon="User"/>
        </el-form-item>
        
        <el-form-item label="密码" prop="password" :rules="[{ required: true, message: '请输入密码', trigger: 'blur' }]">
          <el-input v-model="formData.password" type="password" placeholder="请输入密码" :prefix-icon="Lock" show-password/>
        </el-form-item>
        
        <div class="login-button-container">
          <el-button type="primary" style="width: 100%;" :loading="loading" @click="handleLogin">
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </div>
      </el-form>
      
      <el-alert v-if="error" :closable="false" show-icon type="error" :title="error" style="margin-top: 10px;"/>
      
      <div style="text-align: center; margin-top: 15px;">
        <el-button type="text" @click="navigateToRegister" size="small">
          <User /> 注册为管理员
        </el-button>
        <span style="margin: 0 10px;">|</span>
        <el-button type="text" @click="showServerSettings = true" size="small">
          <Setting /> 设置服务器参数
        </el-button>
      </div>
    </el-card>
    
    <!-- 服务器设置对话框 -->
    <el-dialog v-model="showServerSettings" title="服务器设置" width="450px" :before-close="closeServerSettings">
      <el-form ref="serverForm" :model="serverSettings" label-width="100px" size="default">
        <el-form-item label="服务器IP" prop="ip" :rules="[{ required: true, message: '请输入服务器IP', trigger: 'blur' }]">
          <el-input v-model="serverSettings.ip" placeholder="例如: localhost"/>
        </el-form-item>
        
        <el-form-item label="服务器端口" prop="port" :rules="[{ required: true, message: '请输入服务器端口', trigger: 'blur' }]">
          <el-input v-model.number="serverSettings.port" type="number" placeholder="例如: 8000" min="1" max="65535"/>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeServerSettings">取消</el-button>
          <el-button type="primary" @click="saveServerSettings">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { User, Lock, Setting } from '@element-plus/icons-vue';
import { authAPI } from '../services/api';
import { useRouter } from 'vue-router';

const router = useRouter();
const formData = ref({
  username: '',
  password: ''
});
const loading = ref(false);
const error = ref('');
const showServerSettings = ref(false);

// 服务器设置，默认值为localhost:8000
const serverSettings = ref({
  ip: 'localhost',
  port: 8000
});

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

// 从本地存储加载服务器设置
const loadServerSettings = () => {
  try {
    const savedSettings = localStorage.getItem('serverSettings');
    if (savedSettings) {
      const parsed = JSON.parse(savedSettings);
      serverSettings.value.ip = parsed.ip || 'localhost';
      serverSettings.value.port = parsed.port || 8000;
    }
  } catch (err) {
    console.error('加载服务器设置失败:', err);
  }
};

// 保存服务器设置到本地存储
const saveServerSettings = () => {
  try {
    localStorage.setItem('serverSettings', JSON.stringify(serverSettings.value));
    // 保存后关闭对话框
    closeServerSettings();
    // 显示保存成功提示
    ElMessage.success('服务器设置已保存');
  } catch (err) {
    console.error('保存服务器设置失败:', err);
    ElMessage.error('保存服务器设置失败，请重试');
  }
};

// 关闭服务器设置对话框
const closeServerSettings = () => {
  showServerSettings.value = false;
};

const navigateToRegister = () => {
  router.push('/register');
};

const handleLogin = async () => {
  loading.value = true;
  error.value = '';
  
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
    error.value = errorMessage;
    
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

// 组件挂载时加载服务器设置和表单数据
onMounted(() => {
  loadServerSettings();
  restoreFormData();
});
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.card-header {
  display: flex;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
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
</style>