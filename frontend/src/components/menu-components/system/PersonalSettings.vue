<template>
  <div class="personal-settings">
    
    <!-- 个人信息卡片 -->
    <el-card class="info-card" v-if="userInfo">
      <template #header>
        <div class="card-header">
          <span>个人信息</span>
          <el-button 
            type="primary" 
            size="small" 
            @click="showPasswordDialog"
            :icon="Key"
          >
            修改密码
          </el-button>
        </div>
      </template>
      
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ userInfo.username || '未知' }}</el-descriptions-item>
        <el-descriptions-item label="用户ID">{{ userInfo.id || '未知' }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ userInfo.role_name || '未知角色' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(userInfo.create_time || '') }}</el-descriptions-item>
        <el-descriptions-item label="最后更新时间">{{ formatDate(userInfo.update_time || '') }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="passwordDialog.visible"
      title="修改密码"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        :model="passwordForm"
        :rules="passwordRules"
        ref="passwordFormRef"
        label-width="100px"
      >
        <el-form-item label="原密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            placeholder="请输入原密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="passwordDialog.visible = false">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleChangePassword"
            :loading="passwordDialog.loading"
          >
            确定修改
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Key } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { userAPI } from '@/services/account/user'

interface UserInfo {
  id: number
  username: string
  role_name: string
  create_time: string
  update_time: string
}

interface PasswordForm {
  oldPassword: string
  newPassword: string
  confirmPassword: string
}

const userStore = useUserStore()
const userInfo = ref<UserInfo | null>(null)
const passwordFormRef = ref<FormInstance>()

const passwordForm = ref<PasswordForm>({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordDialog = ref({
  visible: false,
  loading: false
})

// 密码验证规则
const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value !== passwordForm.value.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules: FormRules = {
  oldPassword: [
    { required: true, message: '请输入原密码', trigger: 'blur' },
    { min: 1, message: '密码不能为空', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 格式化日期
const formatDate = (dateString: string) => {
  try {
    return new Date(dateString).toLocaleString('zh-CN')
  } catch (error) {
    console.error('日期格式化失败:', error)
    return dateString || '未知时间'
  }
}

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    // 优先从用户存储中获取当前用户信息
    if (userStore.user) {
      userInfo.value = {
        id: userStore.user.id,
        username: userStore.user.username,
        role_name: userStore.user.roleName || '未知角色',
        create_time: userStore.user.create_time || new Date().toISOString(),
        update_time: userStore.user.update_time || new Date().toISOString()
      }
    }
    // 尝试从API获取最新用户信息作为后备
    const currentUser = await userAPI.getCurrentUser()
    if (currentUser) {
      userInfo.value = {
        id: currentUser.id,
        username: currentUser.username,
        role_name: currentUser.roleName || '未知角色',
        create_time: currentUser.create_time || new Date().toISOString(),
        update_time: currentUser.update_time || new Date().toISOString()
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    // 如果store中已有数据，则不显示错误提示
    if (!userStore.user) {
      ElMessage.error('获取用户信息失败')
    }
  }
}

// 显示密码修改对话框
const showPasswordDialog = () => {
  passwordDialog.value.visible = true
  resetForm()
}

// 修改密码
const handleChangePassword = async () => {
  if (!passwordFormRef.value) return

  try {
    const valid = await passwordFormRef.value.validate()
    if (!valid) return

    passwordDialog.value.loading = true

    await userAPI.changePassword({
      old_password: passwordForm.value.oldPassword,
      new_password: passwordForm.value.newPassword
    })

    ElMessage.success('密码修改成功')
    passwordDialog.value.visible = false
    resetForm()
  } catch (error: any) {
    console.error('修改密码失败:', error)
    ElMessage.error(error.response?.data?.detail || '修改密码失败')
  } finally {
    passwordDialog.value.loading = false
  }
}

// 重置表单
const resetForm = () => {
  if (passwordFormRef.value) {
    passwordFormRef.value.resetFields()
  }
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.personal-settings {
  padding: 0;
  max-width: 100%;
  margin: 0;
}

.info-card {
  margin-bottom: 0;
  border: none;
  box-shadow: none;
}

.info-card :deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid #ebeef5;
}

.info-card :deep(.el-card__body) {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  margin: 0;
  padding: 0;
  gap: 16px;
}

:deep(.el-descriptions__body) {
  background-color: #fafafa;
  margin: 0;
  padding: 0;
}

:deep(.el-descriptions__table) {
  margin: 0;
}

:deep(.el-descriptions__label) {
  margin: 0;
  padding: 8px;
}

:deep(.el-descriptions__content) {
  margin: 0;
  padding: 8px;
}
</style>

<!-- 定义组件类型 -->
<script lang="ts">
export default {
  name: 'PersonalSettings'
}
</script>