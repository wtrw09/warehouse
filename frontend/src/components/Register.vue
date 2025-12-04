<template>
  <div class="register-container">
    <el-card class="register-card" style="width: 400px;">
      <template #header>
        <div class="card-header">
          <span>管理员注册</span>
        </div>
      </template>
      
      <el-form ref="registerForm" :model="formData" label-width="100px" size="default">
        <el-form-item label="用户名" prop="username" :rules="[{ required: true, message: '请输入用户名', trigger: 'blur' }]" label-position="right">
          <el-input v-model="formData.username" placeholder="请输入用户名" :prefix-icon="User"/>
        </el-form-item>
        
        <el-form-item label="密码" prop="password" :rules="[
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码长度至少为6位', trigger: 'blur' }
        ]">
          <el-input v-model="formData.password" type="password" placeholder="请输入密码" :prefix-icon="Lock" show-password/>
        </el-form-item>
        
        <el-form-item label="邀请码" prop="invitation_code" :rules="[{ required: true, message: '请输入邀请码', trigger: 'blur' }]">
          <el-input v-model="formData.invitation_code" type="text" placeholder="请输入管理员邀请码" :prefix-icon="Key"/>
        </el-form-item>
        
        <div class="register-button-container">
          <el-button type="primary" style="width: 100%;" :loading="loading" @click="handleRegister">
            {{ loading ? '注册中...' : '注册' }}
          </el-button>
        </div>
      </el-form>
      
      <el-alert v-if="error" :closable="true" show-icon type="error" :title="error" style="margin-top: 10px; z-index: 1000;"/>
      
      <div style="text-align: center; margin-top: 15px;">
        <el-button type="text" @click="navigateToLogin" size="small">
          <ArrowLeft /> 返回登录
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { User, Lock, Key, ArrowLeft } from '@element-plus/icons-vue';
import { authAPI } from '../services/api';
import { useRouter } from 'vue-router';

const router = useRouter();
const formData = ref({
  username: '',
  password: '',
  invitation_code: ''
});
const loading = ref(false);
const error = ref('');

const handleRegister = async () => {
  loading.value = true;
  error.value = '';
  
  try {
    await authAPI.register(formData.value);
    
    // 注册成功后显示提示并返回登录页面
    ElMessage.success('注册成功，请登录');
    setTimeout(() => {
      router.push('/login');
    }, 1500);
  } catch (err) {
    console.error('注册错误:', err);
    // 显示更详细的错误信息
    if (err.response?.data?.detail) {
      error.value = err.response.data.detail;
    } else if (err.response?.data?.errors) {
      // 如果有多个错误，合并显示
      error.value = err.response.data.errors.map(e => e.msg).join('; ');
    } else {
      error.value = JSON.stringify(err.response?.data) || '注册失败，请检查信息是否正确';
    }
  } finally {
    loading.value = false;
  }
};

const navigateToLogin = () => {
  router.push('/login');
};
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f5f5;
}

.register-card {
  overflow: visible !important;
}

.card-header {
  display: flex;
  justify-content: center;
  font-size: 18px;
  font-weight: bold;
}

/* 确保表单和按钮样式 */
.el-form {
  width: 100%;
}

/* 注册按钮容器样式 */
.register-button-container {
  margin-top: 20px;
  width: 100%;
}

/* 确保注册按钮居中 */
.register-button-container .el-button {
  width: 100%;
  max-width: 300px;
  display: block;
  margin: 0 auto;
}
</style>