<template>
  <MainLayout :activeMenu="route.path">
    <template #header-icon>
      <el-icon><Microscope /></el-icon>
    </template>
    <template #header-title>
      肿瘤预测
    </template>
    <div class="tumor-container">
      <div class="header">
        <h1>肿瘤预测</h1>
        <p>输入病理或医学描述文本，AI将为您预测肿瘤类型</p>
      </div>
      <div class="content">
        <div class="form-section">
          <h2>病理/医学描述输入</h2>
          <form @submit.prevent="handleSubmit" class="prediction-form">
            <div class="form-group">
              <label for="text">病理/医学描述</label>
              <textarea id="text" v-model="form.text" required placeholder="请输入病理或医学描述文本" rows="8"></textarea>
            </div>
            <button type="submit" :disabled="loading" class="submit-btn">
              {{ loading ? '预测中...' : '开始预测' }}
            </button>
          </form>
        </div>
        <div v-if="result" class="result-section">
          <h2>预测结果</h2>
          <div class="result-card" :class="resultClass">
            <div class="result-icon">
              <span v-if="result.prediction === '恶性'" class="high-risk">⚠️</span>
              <span v-else class="low-risk">✅</span>
            </div>
            <div class="result-content">
              <h3>{{ result.prediction }}</h3>
              <p v-if="result.prediction === '恶性'">检测到恶性肿瘤风险，建议及时就医检查</p>
              <p v-else-if="result.prediction === '良性'">当前数据显示为良性肿瘤风险较低</p>
              <p v-else-if="result.prediction === '交界性'">交界性肿瘤，建议密切随访</p>
              <div class="confidence">
                置信度: {{ (result.confidence * 100).toFixed(1) }}%
              </div>
            </div>
          </div>
          <div class="recommendations">
            <h4>健康建议</h4>
            <ul>
              <li v-for="(rec, idx) in result.recommendations || []" :key="idx">{{ rec }}</li>
            </ul>
          </div>
        </div>
      </div>
      <div v-if="error" class="error-message">
        {{ error }}
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/utils/api'
import { ElMessage } from 'element-plus'
import MainLayout from '@/components/MainLayout.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref('')
const result = ref(null)
const form = reactive({ text: '' })
const resultClass = computed(() => {
  if (!result.value) return ''
  return result.value.prediction === '恶性' ? 'high-risk' : 'low-risk'
})
const handleSubmit = async () => {
  if (!form.text) {
    ElMessage.error('请输入文本内容')
    return
  }
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const response = await api.post('/tumor', { text: form.text })
    
    // 处理新的响应格式
    if (response.data.success) {
      result.value = response.data.data
    } else {
      error.value = response.data.error || '预测失败'
      ElMessage.error(error.value)
    }
  } catch (err) {
    error.value = err.response?.data?.message || '预测失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.tumor-container {
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
.content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
}
.form-section, .result-section {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}
.form-section h2, .result-section h2 {
  color: #333;
  margin-bottom: 25px;
  font-size: 24px;
}
.prediction-form {
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
textarea {
  padding: 12px 16px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s ease;
  resize: vertical;
}
textarea:focus {
  outline: none;
  border-color: #667eea;
}
.submit-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px;
  border: none;
  border-radius: 8px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s ease;
  margin-top: 20px;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
}
.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.result-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 25px;
  border-radius: 12px;
  margin-bottom: 25px;
}
.result-card.high-risk {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
  color: white;
}
.result-card.low-risk {
  background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
  color: white;
}
.result-icon {
  font-size: 48px;
}
.result-content h3 {
  font-size: 24px;
  margin-bottom: 8px;
}
.result-content p {
  margin-bottom: 12px;
  opacity: 0.9;
}
.confidence {
  font-weight: 600;
  font-size: 16px;
}
.recommendations h4 {
  color: #333;
  margin-bottom: 15px;
  font-size: 18px;
}
.recommendations ul {
  list-style: none;
  padding: 0;
}
.recommendations li {
  padding: 8px 0;
  color: #555;
  position: relative;
  padding-left: 20px;
}
.recommendations li::before {
  content: "•";
  color: #667eea;
  font-weight: bold;
  position: absolute;
  left: 0;
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
  .form-group {
    width: 100%;
  }
}
</style> 