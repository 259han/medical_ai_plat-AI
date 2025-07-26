<template>
  <MainLayout :activeMenu="route.path">
    <template #header-icon>
      <el-icon><ChatDotRound /></el-icon>
    </template>
    <template #header-title>
      医疗问答
    </template>
    <div class="qa-container">
      <el-card class="qa-card">
        <template #header>
          <div class="card-header">
            <span>AI医疗问答</span>
            <el-tag type="success" size="small">智能诊断</el-tag>
          </div>
        </template>
        <div class="qa-form">
          <el-form>
            <el-form-item>
              <el-input
                v-model="question"
                type="textarea"
                :rows="4"
                placeholder="请输入您的医疗问题，例如：什么是高血压？如何预防心脏病？"
                maxlength="1000"
                show-word-limit
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                :disabled="!question.trim()"
                @click="askQuestion"
              >
                <el-icon><ChatDotRound /></el-icon>
                提问
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-card>
      <div v-if="result" class="result-section">
        <el-card class="result-card">
          <template #header>
            <div class="card-header">
              <span>AI回答</span>
              <div class="confidence-info">
                <el-tag :type="getConfidenceType(result.confidence)" size="small">
                  置信度: {{ (result.confidence * 100).toFixed(1) }}%
                </el-tag>
              </div>
            </div>
          </template>
          <div class="answer-content">
            <div class="question-display">
              <strong>问题：</strong>
              <p>{{ result.question }}</p>
            </div>
            <div class="answer-display">
              <strong>回答：</strong>
              <div class="answer-text" v-html="formatAnswer(result.answer)"></div>
            </div>
            <div class="recommendations">
              <h4>健康建议</h4>
              <ul>
                <li>建议咨询专业医生获取更详细的医疗建议</li>
                <li>定期进行体检，监测身体状况</li>
                <li>保持健康的生活方式，适量运动</li>
                <li>如有不适症状，请及时就医</li>
              </ul>
            </div>
            <div v-if="result.model_info" class="model-info">
              <el-divider />
              <p><small>模型信息：{{ result.model_info.model_name }} | 设备：{{ result.model_info.device }}</small></p>
            </div>
          </div>
        </el-card>
      </div>
      <div v-if="error" class="error-section">
        <el-alert :title="error" type="error" show-icon :closable="false" />
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/utils/api'
import { ElMessage } from 'element-plus'
import MainLayout from '@/components/MainLayout.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const question = ref('')
const result = ref(null)
const error = ref('')
const loading = ref(false)

const askQuestion = async () => {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  loading.value = true
  error.value = ''
  result.value = null
  try {
    const response = await api.post('/medical_qa', {
      question: question.value.trim()
    })
    
    // 处理新的响应格式
    if (response.data.success) {
      result.value = response.data.data
      if (result.value.error) {
        error.value = result.value.error
      } else {
        ElMessage.success('AI回答生成成功')
      }
    } else {
      error.value = response.data.error || '请求失败'
      ElMessage.error(error.value)
    }
  } catch (err) {
    error.value = err.response?.data?.error || '请求失败，请稍后重试'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}
const getConfidenceType = (confidence) => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'warning'
  return 'danger'
}
const escapeHtml = (unsafe) => {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
const formatAnswer = (answer) => {
  // 先转义，再换行
  return escapeHtml(answer).replace(/\n/g, '<br>');
}
</script>

<style scoped>
.qa-container {
  max-width: 800px;
  margin: 0 auto;
}
.qa-card {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.qa-form {
  margin-top: 20px;
}
.result-section {
  margin-top: 20px;
}
.result-card {
  margin-bottom: 20px;
}
.confidence-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
.answer-content {
  line-height: 1.6;
}
.question-display {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}
.question-display strong {
  color: #409eff;
}
.question-display p {
  margin: 10px 0 0 0;
  color: #303133;
}
.answer-display {
  margin-bottom: 20px;
}
.answer-display strong {
  color: #67c23a;
  display: block;
  margin-bottom: 10px;
}
.answer-text {
  padding: 15px;
  background: #f0f9ff;
  border-radius: 8px;
  border-left: 4px solid #67c23a;
  color: #303133;
}

.recommendations {
  margin-top: 20px;
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
  color: #409eff;
  font-weight: bold;
  position: absolute;
  left: 0;
}
.model-info {
  margin-top: 20px;
}
.model-info p {
  margin: 0;
  color: #909399;
  text-align: center;
}
.error-section {
  margin-top: 20px;
}
</style> 