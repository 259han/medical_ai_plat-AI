<template>
  <MainLayout :activeMenu="route.path">
    <template #header-icon>
      <el-icon><TrendCharts /></el-icon>
    </template>
    <template #header-title>
      糖尿病预测
    </template>
    <div class="diabetes-container">
      <div class="header">
        <h1>糖尿病预测</h1>
        <p>输入您的健康数据，AI将为您预测糖尿病并发症风险</p>
      </div>
      <div class="content">
        <div class="form-section">
          <h2>健康数据输入</h2>
          <form @submit.prevent="handleSubmit" class="prediction-form">
            <div class="form-row">
              <div class="form-group">
                <label>性别</label>
                <select v-model="form.性别" required>
                  <option value="男">男</option>
                  <option value="女">女</option>
                </select>
              </div>
              <div class="form-group">
                <label>年龄</label>
                <input type="number" v-model.number="form.年龄" min="1" max="120" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>身高(cm)</label>
                <input type="number" v-model.number="form['身高(cm)']" min="100" max="250" step="0.1" required />
              </div>
              <div class="form-group">
                <label>体重(kg)</label>
                <input type="number" v-model.number="form['体重(kg)']" min="20" max="200" step="0.1" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>空腹血糖值(mmol/L)</label>
                <input type="number" v-model.number="form['空腹血糖值(mmol/L)']" min="2" max="1000" step="0.1" required />
              </div>
              <div class="form-group">
                <label>餐后2小时血糖值(mmol/L)</label>
                <input type="number" v-model.number="form['餐后2小时血糖值(mmol/L)']" min="2" max="1000" step="0.1" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>糖化血红蛋白(%)</label>
                <input type="number" v-model.number="form['糖化血红蛋白(%)']" min="3" max="200" step="0.1" required />
              </div>
              <div class="form-group">
                <label>总胆固醇(mmol/L)</label>
                <input type="number" v-model.number="form['总胆固醇(mmol/L)']" min="1" max="100" step="0.1" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>甘油三酯(mmol/L)</label>
                <input type="number" v-model.number="form['甘油三酯(mmol/L)']" min="0.1" max="150" step="0.01" required />
              </div>
              <div class="form-group">
                <label>高密度脂蛋白(mmol/L)</label>
                <input type="number" v-model.number="form['高密度脂蛋白(mmol/L)']" min="0.1" max="50" step="0.01" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>低密度脂蛋白(mmol/L)</label>
                <input type="number" v-model.number="form['低密度脂蛋白(mmol/L)']" min="0.1" max="80" step="0.01" required />
              </div>
              <div class="form-group">
                <label>尿微量白蛋白(mg/L)</label>
                <input type="number" v-model.number="form['尿微量白蛋白(mg/L)']" min="0" max="5000" step="0.1" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>收缩压(mmHg)</label>
                <input type="number" v-model.number="form['收缩压(mmHg)']" min="70" max="250" required />
              </div>
              <div class="form-group">
                <label>舒张压(mmHg)</label>
                <input type="number" v-model.number="form['舒张压(mmHg)']" min="40" max="250" required />
              </div>
            </div>
            <button type="submit" :disabled="loading" class="submit-btn">
              {{ loading ? '预测中...' : '开始预测' }}
            </button>
          </form>
        </div>
        <div v-if="result" class="result-section">
          <h2>预测结果</h2>
          <div class="result-card" :class="resultRiskClass">
            <div class="result-icon">
              <span v-if="computedRiskLevel === 'high'" class="high-risk">⚠️</span>
              <span v-else-if="computedRiskLevel === 'medium'" class="medium-risk">⚠️</span>
              <span v-else class="low-risk">✅</span>
            </div>
            <div class="result-content">
              <h3>
                {{ computedRiskLevel === 'high' ? '高风险' : computedRiskLevel === 'medium' ? '中风险' : '低风险' }}
                <template v-if="computedRiskLevel !== 'low' && result['并发症类型'] !== '无'">
                  ：{{ result['并发症类型'] }}
                </template>
              </h3>
              <p>
                <template v-if="computedRiskLevel === 'high'">
                  检测到并发症高风险，请及时就医检查
                </template>
                <template v-else-if="computedRiskLevel === 'medium'">
                  检测到并发症中风险，建议加强监测和管理
                </template>
                <template v-else>
                  当前数据显示并发症风险较低
                </template>
              </p>
              <div class="days-to-onset" v-if="computedRiskLevel !== 'low' && result['预计发病天数'] && result['预计发病天数'] !== '不适用'">
                预计发病天数: {{ result['预计发病天数'] }}
              </div>
            </div>
          </div>
          <div class="recommendations">
            <h4>健康建议</h4>
            <div>{{ result['医疗建议'] }}</div>
          </div>
          <div class="risk-factors">
            <h4>风险因素分析</h4>
            <div class="factor-grid">
              <div class="factor-item">
                <span class="factor-label">血糖水平</span>
                <span class="factor-value" :class="getGlucoseClass()">
                  {{ form['空腹血糖值(mmol/L)'] }} mmol/L
                </span>
              </div>
              <div class="factor-item">
                <span class="factor-label">BMI指数</span>
                <span class="factor-value" :class="getBMIClass()">
                  {{ form['体重(kg)'] }} kg / {{ form['身高(cm)'] }} cm
                </span>
              </div>
              <div class="factor-item">
                <span class="factor-label">血压</span>
                <span class="factor-value" :class="getBPClass()">
                  {{ form['收缩压(mmHg)'] }} / {{ form['舒张压(mmHg)'] }} mmHg
                </span>
              </div>
            </div>
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
const form = reactive({
  性别: '',
  年龄: '',
  '身高(cm)': '',
  '体重(kg)': '',
  '空腹血糖值(mmol/L)': '',
  '餐后2小时血糖值(mmol/L)': '',
  '糖化血红蛋白(%)': '',
  '总胆固醇(mmol/L)': '',
  '甘油三酯(mmol/L)': '',
  '高密度脂蛋白(mmol/L)': '',
  '低密度脂蛋白(mmol/L)': '',
  '尿微量白蛋白(mg/L)': '',
  '收缩压(mmHg)': '',
  '舒张压(mmHg)': ''
})
const resultRiskClass = computed(() => {
  if (!result.value) return ''
  
  const complication = result.value['并发症类型']
  const probabilityStr = result.value['发病概率'] || '0%'
  
  // 解析发病概率
  let probability = 0.0
  try {
    probability = parseFloat(probabilityStr.replace('%', '')) / 100
  } catch {
    probability = 0.0
  }
  
  // 根据并发症类型和发病概率判断风险等级
  if (complication === '无') {
    if (probability > 0.5) return 'medium-risk'
    return 'low-risk'
  } else {
    if (probability > 0.7) return 'high-risk'
    if (probability > 0.4) return 'medium-risk'
    return 'low-risk'
  }
})
const computedRiskLevel = computed(() => {
  if (!result.value) return ''
  // 先判断发病概率
  let probability = 0.0
  const probabilityStr = result.value['发病概率'] || '0%'
  try {
    probability = parseFloat(probabilityStr.replace('%', '')) / 100
  } catch {
    probability = 0.0
  }
  if (probability <= 0.001) {
    return 'low'
  }
  // 否则用后端risk_level
  return result.value.risk_level
})
const getGlucoseClass = () => {
  if (form['空腹血糖值(mmol/L)'] >= 126) return 'high'
  if (form['空腹血糖值(mmol/L)'] >= 100) return 'medium'
  return 'low'
}
const getBMIClass = () => {
  const weight = form['体重(kg)']
  const heightCm = form['身高(cm)']
  if (!weight || !heightCm) return ''
  const heightM = heightCm / 100
  const bmi = weight / (heightM * heightM)
  if (bmi >= 28) return 'high'      // 肥胖
  if (bmi >= 24) return 'medium'    // 超重
  if (bmi >= 18.5) return 'low'     // 正常
  return 'low'                      // 偏瘦
}
const getBPClass = () => {
  if (form['收缩压(mmHg)'] >= 140) return 'high'
  if (form['收缩压(mmHg)'] >= 120) return 'medium'
  return 'low'
}
const getRiskLevel = () => {
  if (!result.value) return ''
  const complication = result.value['并发症类型']
  const probabilityStr = result.value['发病概率'] || '0%'
  let probability = 0.0
  try {
    probability = parseFloat(probabilityStr.replace('%', '')) / 100
  } catch {
    probability = 0.0
  }
  if (complication === '无') {
    if (probability > 0.5) return '中风险'
    return '低风险'
  } else {
    if (probability > 0.7) return '高风险'
    if (probability > 0.4) return '中风险'
    return '低风险'
  }
}
const handleSubmit = async () => {
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const response = await api.post('/diabetes', form)
    
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
.diabetes-container {
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
.recommendations h4, .risk-factors h4 {
  color: #333;
  margin-bottom: 15px;
  font-size: 18px;
}
.recommendations ul {
  list-style: none;
  padding: 0;
  margin-bottom: 25px;
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
.factor-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}
.factor-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #e1e5e9;
}
.factor-label {
  font-weight: 500;
  color: #555;
}
.factor-value {
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
}
.factor-value.high {
  background: #ff6b6b;
  color: white;
}
.factor-value.medium {
  background: #ffd93d;
  color: #333;
}
.factor-value.low {
  background: #51cf66;
  color: white;
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