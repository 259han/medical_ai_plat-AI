<template>
  <MainLayout :activeMenu="route.path">
    <template #header-icon>
      <el-icon><UserFilled /></el-icon>
    </template>
    <template #header-title>
      个人资料
    </template>
    <div class="profile-container">
      <div class="header">
        <h1>个人资料</h1>
        <p>管理您的个人信息和账户设置</p>
        <button @click="goHome" class="back-btn">返回主页</button>
      </div>
      <div class="content">
        <div class="profile-section">
          <h2>基本信息</h2>
          <form @submit.prevent="handleUpdateProfile" class="profile-form">
            <div class="form-row">
              <div class="form-group">
                <label for="username">用户名</label>
                <input type="text" id="username" v-model="form.username" required placeholder="请输入用户名" />
              </div>
              <div class="form-group">
                <label for="email">邮箱</label>
                <input type="email" id="email" v-model="form.email" required placeholder="请输入邮箱" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="fullName">姓名</label>
                <input type="text" id="fullName" v-model="form.fullName" placeholder="请输入姓名" />
              </div>
              <div class="form-group">
                <label for="phone">手机号</label>
                <input type="tel" id="phone" v-model="form.phone" placeholder="请输入手机号" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="age">年龄</label>
                <input type="number" id="age" v-model.number="form.age" min="1" max="120" placeholder="请输入年龄" />
              </div>
              <div class="form-group">
                <label for="gender">性别</label>
                <select id="gender" v-model="form.gender">
                  <option value="">请选择性别</option>
                  <option value="male">男性</option>
                  <option value="female">女性</option>
                  <option value="other">其他</option>
                </select>
              </div>
            </div>
            <div class="form-group">
              <label for="address">地址</label>
              <input type="text" id="address" v-model="form.address" placeholder="请输入地址" />
            </div>
            <button type="submit" :disabled="loading" class="update-btn">
              {{ loading ? '更新中...' : '更新资料' }}
            </button>
          </form>
        </div>
        <div class="password-section">
          <h2>修改密码</h2>
          <form @submit.prevent="handleChangePassword" class="password-form">
            <div class="form-group">
              <label for="currentPassword">当前密码</label>
              <input type="password" id="currentPassword" v-model="passwordForm.currentPassword" required placeholder="请输入当前密码" />
            </div>
            <div class="form-group">
              <label for="newPassword">新密码</label>
              <input type="password" id="newPassword" v-model="passwordForm.newPassword" required placeholder="请输入新密码" />
            </div>
            <div class="form-group">
              <label for="confirmPassword">确认新密码</label>
              <input type="password" id="confirmPassword" v-model="passwordForm.confirmPassword" required placeholder="请再次输入新密码" />
            </div>
            <button type="submit" :disabled="passwordLoading" class="password-btn">
              {{ passwordLoading ? '修改中...' : '修改密码' }}
            </button>
          </form>
        </div>
        <div class="stats-section">
          <h2>使用统计</h2>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon">📊</div>
              <div class="stat-content">
                <h3>总预测次数</h3>
                <p class="stat-number">{{ stats.totalPredictions }}</p>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">🏥</div>
              <div class="stat-content">
                <h3>心脏病预测</h3>
                <p class="stat-number">{{ stats.heartDiseasePredictions }}</p>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">🩺</div>
              <div class="stat-content">
                <h3>肿瘤预测</h3>
                <p class="stat-number">{{ stats.tumorPredictions }}</p>
              </div>
            </div>
            <div class="stat-card">
              <div class="stat-icon">💉</div>
              <div class="stat-content">
                <h3>糖尿病预测</h3>
                <p class="stat-number">{{ stats.diabetesPredictions }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="success" class="success-message">
        {{ success }}
      </div>
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/utils/api'
import MainLayout from '@/components/MainLayout.vue'

const router = useRouter()
const route = useRoute()
const goHome = () => router.push('/dashboard')
const authStore = useAuthStore()
const loading = ref(false)
const passwordLoading = ref(false)
const error = ref('')
const success = ref('')
const stats = ref({
  totalPredictions: 0,
  heartDiseasePredictions: 0,
  tumorPredictions: 0,
  diabetesPredictions: 0
})
const form = reactive({
  username: '',
  email: '',
  fullName: '',
  phone: '',
  age: '',
  gender: '',
  address: ''
})
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})
const loadProfile = async () => {
  try {
    const response = await api.get('/user/profile')
    const profile = response.data
    form.username = profile.username || ''
    form.email = profile.email || ''
    form.fullName = profile.fullName || ''
    form.phone = profile.phone || ''
    form.age = profile.age || ''
    form.gender = profile.gender || ''
    form.address = profile.address || ''
  } catch (err) {
    error.value = '加载个人资料失败'
  }
}
const loadStats = async () => {
  try {
    const response = await api.get('/user/stats')
    const data = response.data
    stats.value = {
      totalPredictions: data.total_predictions || 0,
      heartDiseasePredictions: data.model_stats?.heart_disease || 0,
      tumorPredictions: data.model_stats?.tumor || 0,
      diabetesPredictions: data.model_stats?.diabetes || 0
    }
  } catch (err) {
    console.error('加载统计数据失败:', err)
  }
}
const handleUpdateProfile = async () => {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    await api.put('/user/profile', form)
    success.value = '个人资料更新成功'
  } catch (err) {
    error.value = err.response?.data?.message || '更新失败，请重试'
  } finally {
    loading.value = false
  }
}
const handleChangePassword = async () => {
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    error.value = '两次输入的新密码不一致'
    return
  }
  passwordLoading.value = true
  error.value = ''
  success.value = ''
  try {
    await api.put('/user/password', {
      currentPassword: passwordForm.currentPassword,
      newPassword: passwordForm.newPassword
    })
    success.value = '密码修改成功'
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (err) {
    error.value = err.response?.data?.message || '密码修改失败，请重试'
  } finally {
    passwordLoading.value = false
  }
}
onMounted(() => {
  loadProfile()
  loadStats()
})
</script>

<style scoped>
.profile-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 40px;
}

.header h1 {
  color: #333;
  font-size: 32px;
  margin-bottom: 10px;
}

.header p {
  color: #666;
  font-size: 16px;
}

.header .back-btn {
  background: #667eea;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s ease;
  margin-top: 20px;
}

.header .back-btn:hover {
  background: #5a67d8;
}

.header .back-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.profile-section, .password-section, .stats-section {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.stats-section {
  grid-column: 1 / -1;
}

.profile-section h2, .password-section h2, .stats-section h2 {
  color: #333;
  margin-bottom: 25px;
  font-size: 24px;
}

.profile-form, .password-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
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

input, select {
  padding: 12px 16px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s ease;
}

input:focus, select:focus {
  outline: none;
  border-color: #667eea;
}

.update-btn, .password-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 14px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease;
  margin-top: 10px;
}

.update-btn:hover:not(:disabled), .password-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}

.update-btn:disabled, .password-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 25px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  border-left: 4px solid #667eea;
}

.stat-icon {
  font-size: 32px;
}

.stat-content h3 {
  color: #333;
  font-size: 16px;
  margin-bottom: 8px;
}

.stat-number {
  color: #667eea;
  font-size: 28px;
  font-weight: 700;
  margin: 0;
}

.success-message {
  background: #d4edda;
  color: #155724;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 15px;
  border-radius: 8px;
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
}

@media (max-width: 768px) {
  .content {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style> 