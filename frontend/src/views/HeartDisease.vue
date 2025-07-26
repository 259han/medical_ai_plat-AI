<template>
  <MainLayout :activeMenu="route.path">
    <template #header-icon>
      <el-icon><Heart /></el-icon>
    </template>
    <template #header-title>
      心脏病预测
    </template>
    <div class="heart-disease-container">
      <div class="header">
        <h1>心脏病预测</h1>
        <p>输入您的健康数据，AI将为您预测心脏病风险</p>
      </div>
      <div class="content">
        <div class="form-section">
          <h2>健康数据输入</h2>
          <form @submit.prevent="handleSubmit" class="prediction-form">
            <div class="form-row">
              <div class="form-group">
                <label for="FastingBloodSugar">空腹血糖 (mg/dL)</label>
                <input type="number" id="FastingBloodSugar" v-model.number="form.FastingBloodSugar" required min="0" step="0.1" placeholder="请输入空腹血糖" />
              </div>
              <div class="form-group">
                <label for="HbA1c">糖化血红蛋白 HbA1c (%)</label>
                <input type="number" id="HbA1c" v-model.number="form.HbA1c" required min="1.0" max="10.0" step="0.1" placeholder="1.0-10.0" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="DietQuality">饮食质量评分 (1-10)</label>
                <input type="number" id="DietQuality" v-model.number="form.DietQuality" required min="1" max="10" step="0.1" placeholder="1-10" />
              </div>
              <div class="form-group">
                <label for="SerumCreatinine">血清肌酐 (mg/dL)</label>
                <input type="number" id="SerumCreatinine" v-model.number="form.SerumCreatinine" required min="0" step="0.01" placeholder="请输入血清肌酐" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="MedicalCheckupsFrequency">每年体检次数</label>
                <input type="number" id="MedicalCheckupsFrequency" v-model.number="form.MedicalCheckupsFrequency" required min="0" placeholder="请输入体检次数" />
              </div>
              <div class="form-group">
                <label for="BMI">身体质量指数 (BMI)</label>
                <input type="number" id="BMI" v-model.number="form.BMI" required min="10" max="60" step="0.1" placeholder="10-60" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="MedicationAdherence">服药依从性 (0-10)</label>
                <input type="number" id="MedicationAdherence" v-model.number="form.MedicationAdherence" required min="0" max="10" step="0.1" placeholder="0-10" />
              </div>
              <div class="form-group">
                <label for="CholesterolHDL">高密度脂蛋白胆固醇 (mg/dL)</label>
                <input type="number" id="CholesterolHDL" v-model.number="form.CholesterolHDL" required min="0" max ="100" step="0.1" placeholder="0-100" />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label for="CholesterolTriglycerides">甘油三酯 (mg/dL)</label>
                <input type="number" id="CholesterolTriglycerides" v-model.number="form.CholesterolTriglycerides" required min="0" step="0.1" placeholder="请输入甘油三酯" />
              </div>
              <div class="form-group">
                <label for="SystolicBP">收缩压 (mmHg)</label>
                <input type="number" id="SystolicBP" v-model.number="form.SystolicBP" required min="70" max="250" placeholder="70-250" />
              </div>
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
              <span v-if="result.risk_level === 'high'" class="high-risk">⚠️</span>
              <span v-else-if="result.risk_level === 'medium'" class="medium-risk">⚠️</span>
              <span v-else class="low-risk">✅</span>
            </div>
            <div class="result-content">
              <h3>
                {{ result.risk_level === 'high' ? '高风险' : result.risk_level === 'medium' ? '中风险' : '低风险' }}
              </h3>
              <p>
                <template v-if="result.risk_level === 'high'">
                  检测到心脏病高风险（置信度{{ (result.confidence * 100).toFixed(1) }}%），请及时就医检查
                </template>
                <template v-else-if="result.risk_level === 'medium'">
                  检测到心脏病中风险（置信度{{ (result.confidence * 100).toFixed(1) }}%），建议加强监测和管理
                </template>
                <template v-else>
                  当前数据显示心脏病风险较低
                </template>
              </p>
              <div class="confidence">
                置信度: {{ (result.confidence * 100).toFixed(1) }}%
              </div>
            </div>
          </div>
          <div class="recommendations">
            <h4>健康建议</h4>
            <ul>
              <li v-for="(rec, index) in result.recommendations" :key="index">{{ rec }}</li>
            </ul>
          </div>
        </div>
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
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
const form = reactive({
  FastingBloodSugar: '',
  HbA1c: '',
  DietQuality: '',
  SerumCreatinine: '',
  MedicalCheckupsFrequency: '',
  BMI: '',
  MedicationAdherence: '',
  CholesterolHDL: '',
  CholesterolTriglycerides: '',
  SystolicBP: ''
})

const resultClass = computed(() => {
  if (!result.value) return ''
  if (result.value.risk_level === 'high') return 'high-risk'
  if (result.value.risk_level === 'medium') return 'medium-risk'
  return 'low-risk'
})

const handleSubmit = async () => {
  loading.value = true
  error.value = ''
  result.value = null
  
  try {
    // 验证表单数据
    const validationErrors = validateForm()
    if (validationErrors.length > 0) {
      error.value = validationErrors.join(', ')
      return
    }
    
    const response = await api.post('/heart_disease', form)
    
    // 处理新的响应格式
    if (response.data.success) {
      result.value = response.data.data
    } else {
      error.value = response.data.error || '预测失败'
      ElMessage.error(error.value)
    }
  } catch (err) {
    error.value = err.response?.data?.error || err.response?.data?.detail || '预测失败，请重试'
  } finally {
    loading.value = false
  }
}

const validateForm = () => {
  const errors = []
  
  if (form.FastingBloodSugar === '' || form.FastingBloodSugar < 0) {
    errors.push('空腹血糖不能为空且不能为负数')
  }
  
  if (form.HbA1c === '' || form.HbA1c < 1.0 || form.HbA1c > 10.0) {
    errors.push('糖化血红蛋白必须在1.0-10.0%之间')
  }
  
  if (form.DietQuality === '' || form.DietQuality < 1 || form.DietQuality > 10) {
    errors.push('饮食质量评分必须在1-10之间')
  }
  
  if (form.SerumCreatinine === '' || form.SerumCreatinine < 0 || form.SerumCreatinine > 5) {
    errors.push('血清肌酐必须在0-5之间')
  }
  
  if (form.MedicalCheckupsFrequency === '' || form.MedicalCheckupsFrequency < 0) {
    errors.push('体检次数不能为空且不能为负数')
  }
  
  if (form.BMI === '' || form.BMI < 10 || form.BMI > 60) {
    errors.push('BMI必须在10-60之间')
  }
  
  if (form.MedicationAdherence === '' || form.MedicationAdherence < 0 || form.MedicationAdherence > 10) {
    errors.push('服药依从性必须在0-10之间')
  }
  
  if (form.CholesterolHDL === '' || form.CholesterolHDL < 0 || form.CholesterolHDL > 100) {
    errors.push('HDL胆固醇不能为空且需在0-100之间')
  }
  
  if (form.CholesterolTriglycerides === '' || form.CholesterolTriglycerides < 0 || form.CholesterolTriglycerides > 1000) {
    errors.push('甘油三酯不能为空且需在0-1000之间')
  }
  
  if (form.SystolicBP === '' || form.SystolicBP < 70 || form.SystolicBP > 250) {
    errors.push('收缩压必须在70-250mmHg之间')
  }
  
  return errors
}
</script>

<style scoped>
.heart-disease-container {
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
  background: linear-gradient(135deg, #ff6b6b 0%, #ff8787 100%);
  color: white;
}
.result-card.medium-risk {
  background: linear-gradient(135deg, #ffd93d 0%, #ffc107 100%);
  color: #333;
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
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style> 