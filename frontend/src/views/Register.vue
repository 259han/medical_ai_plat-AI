<template>
  <MainLayout :activeMenu="''">
    <template #header-icon>
      <el-icon><UserFilled /></el-icon>
    </template>
    <template #header-title>
      注册
    </template>
    <div class="register-container">
      <div class="register-card">
        <h2>用户注册</h2>
        <form @submit.prevent="handleRegister" class="register-form">
          <div class="form-group">
            <label for="username">用户名</label>
            <input type="text" id="username" v-model="form.username" required placeholder="请输入用户名" />
          </div>
          <div class="form-group">
            <label for="email">邮箱</label>
            <input type="email" id="email" v-model="form.email" required placeholder="请输入邮箱" />
          </div>
          <div class="form-group">
            <label for="password">密码</label>
            <input type="password" id="password" v-model="form.password" required placeholder="请输入密码" />
          </div>
          <div class="form-group">
            <label for="confirmPassword">确认密码</label>
            <input type="password" id="confirmPassword" v-model="form.confirmPassword" required placeholder="请再次输入密码" />
          </div>
          <button type="submit" :disabled="loading" class="register-btn">
            {{ loading ? '注册中...' : '注册' }}
          </button>
        </form>
        <div class="login-link">
          已有账号？ <router-link to="/login">立即登录</router-link>
        </div>
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import MainLayout from '@/components/MainLayout.vue'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const error = ref('')
const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})
const handleRegister = async () => {
  if (form.password !== form.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await authStore.register({
      username: form.username,
      email: form.email,
      password: form.password
    })
    router.push('/dashboard')
  } catch (err) {
    error.value = err.message || '注册失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-card {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

h2 {
  text-align: center;
  color: #333;
  margin-bottom: 30px;
  font-size: 28px;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

label {
  font-weight: 500;
  color: #555;
  font-size: 14px;
}

input {
  padding: 12px 16px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s ease;
}

input:focus {
  outline: none;
  border-color: #667eea;
}

.register-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 14px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.register-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.register-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.login-link {
  text-align: center;
  margin-top: 20px;
  color: #666;
  font-size: 14px;
}

.login-link a {
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
}

.login-link a:hover {
  text-decoration: underline;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 12px;
  border-radius: 6px;
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
}
</style> 