<template>
  <MainLayout :activeMenu="route.path">
    <template #header-icon>
      <el-icon><Camera /></el-icon>
    </template>
    <template #header-title>
      胸部X光预测
    </template>
    <div class="xray-container">
      <el-card class="xray-card">
        <template #header>
          <div class="card-header">
            <span>胸部X光疾病预测</span>
            <el-tag type="success" size="small">AI诊断</el-tag>
          </div>
        </template>
        <div class="xray-form">
          <el-form>
            <el-form-item label="上传X光图片">
              <el-upload
                :auto-upload="false"
                :limit="1"
                :on-change="handleFileChange"
                :on-remove="handleFileRemove"
                accept=".png,.jpg,.jpeg"
                drag
              >
                <el-icon class="el-icon--upload"><Upload /></el-icon>
                <div class="el-upload__text">
                  拖放图片或 <em>点击上传</em><br />
                  支持 PNG、JPG、JPEG 格式
                </div>
              </el-upload>
            </el-form-item>
            <el-form-item label="选择CAM方法">
              <el-select v-model="camMethod" placeholder="选择热力图生成方法">
                <el-option label="GradCAM" value="gradcam" />
                <el-option label="GradCAM++" value="gradcam++" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="loading"
                :disabled="!file || !camMethod"
                @click="submitXray"
              >
                <el-icon><Search /></el-icon>
                开始预测
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-card>
      <div v-if="result" class="result-section">
        <el-card class="result-card">
          <template #header>
            <div class="card-header">
              <span>预测结果</span>
              <el-tag type="info" size="small">
                CAM方法: {{ result.cam_method.toUpperCase() }}
              </el-tag>
            </div>
          </template>
          <div class="result-content">
            <el-row :gutter="20">
              <el-col :xs="24" :md="12">
                <h4>预测结果</h4>
                <el-table :data="predictionData" style="width: 100%">
                  <el-table-column prop="disease" label="疾病" />
                  <el-table-column prop="positive" label="状态">
                    <template #default="scope">
                      <el-tag :type="scope.row.positive ? 'danger' : 'success'">
                        {{ scope.row.positive ? '阳性' : '阴性' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="probability" label="概率">
                    <template #default="scope">
                      {{ (scope.row.probability * 100).toFixed(1) }}%
                    </template>
                  </el-table-column>
                </el-table>
              </el-col>
              <el-col :xs="24" :md="12">
                <h4>纯热力图</h4>
                <el-image
                  v-if="heatmapUrl"
                  :src="heatmapUrl"
                  fit="contain"
                  style="width: 100%; max-height: 400px"
                  :preview-src-list="[heatmapUrl]"
                  @error="handleImageError"
                />
                <p v-else-if="imageLoading">加载纯热力图中...</p>
                <p v-else>暂无纯热力图</p>
                <h4>热力图叠加原图</h4>
                <el-image
                  v-if="superimposedUrl"
                  :src="superimposedUrl"
                  fit="contain"
                  style="width: 100%; max-height: 400px"
                  :preview-src-list="[superimposedUrl]"
                  @error="handleImageError"
                />
                <p v-else-if="imageLoading">加载热力图叠加原图中...</p>
                <p v-else>暂无热力图叠加原图</p>
              </el-col>
            </el-row>
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
import { ref, computed, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/utils/api'
import { ElMessage } from 'element-plus'
import { Camera, Upload, Search } from '@element-plus/icons-vue'
import MainLayout from '@/components/MainLayout.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const file = ref(null)
const camMethod = ref('gradcam')
const result = ref(null)
const error = ref('')
const loading = ref(false)
const heatmapUrl = ref('')
const superimposedUrl = ref('')
const imageLoading = ref(false)

const diseaseNameMap = {
  "Atelectasis": "肺不张",
  "Cardiomegaly": "心脏肥大",
  "Effusion": "胸腔积液",
  "Infiltration": "渗出",
  "Mass": "肿块",
  "Nodule": "结节",
  "Pneumonia": "肺炎",
  "Pneumothorax": "气胸",
  "Consolidation": "实变",
  "Edema": "肺水肿",
  "Emphysema": "肺气肿",
  "Fibrosis": "肺纤维化",
  "Pleural_Thickening": "胸膜增厚",
  "Hernia": "疝气"
}

const predictionData = computed(() => {
  if (!result.value || !result.value.predictions) return []
  
  // 定义正确的疾病标签顺序（与后端一致）
  const diseaseOrder = [
    'Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration',
    'Mass', 'Nodule', 'Pneumonia', 'Pneumothorax',
    'Consolidation', 'Edema', 'Emphysema', 'Fibrosis',
    'Pleural_Thickening', 'Hernia'
  ]
  
  // 按照定义的顺序处理数据
  return diseaseOrder.map(disease => {
    const data = result.value.predictions[disease]
    if (data) {
      return {
        disease: `${disease}${diseaseNameMap[disease] ? '（' + diseaseNameMap[disease] + '）' : ''}`,
        positive: data.positive,
        probability: data.probability
      }
    }
    return null
  }).filter(item => item !== null)
})

const handleFileChange = (uploadFile) => {
  file.value = uploadFile.raw
}
const handleFileRemove = () => {
  file.value = null
  result.value = null
  error.value = ''
  if (heatmapUrl.value && heatmapUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(heatmapUrl.value)
  }
  if (superimposedUrl.value && superimposedUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(superimposedUrl.value)
  }
  heatmapUrl.value = ''
  superimposedUrl.value = ''
}
onUnmounted(() => {
  if (heatmapUrl.value && heatmapUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(heatmapUrl.value)
  }
  if (superimposedUrl.value && superimposedUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(superimposedUrl.value)
  }
})
const submitXray = async () => {
  if (!file.value) {
    ElMessage.warning('请上传X光图片')
    return
  }
  if (!camMethod.value) {
    ElMessage.warning('请选择CAM方法')
    return
  }
  loading.value = true
  error.value = ''
  result.value = null
  heatmapUrl.value = ''
  superimposedUrl.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file.value)
    formData.append('cam_method', camMethod.value)
    const response = await api.post('/chest_xray', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    // 处理新的响应格式
    if (response.data.success) {
      result.value = response.data.data
      console.log('后端返回的原始数据:', result.value)
      console.log('预测结果顺序:', Object.keys(result.value.predictions || {}))
      if (result.value.error) {
        error.value = result.value.error
      } else {
        try {
          if (heatmapUrl.value && heatmapUrl.value.startsWith('blob:')) {
            URL.revokeObjectURL(heatmapUrl.value)
          }
          if (superimposedUrl.value && superimposedUrl.value.startsWith('blob:')) {
            URL.revokeObjectURL(superimposedUrl.value)
          }
          heatmapUrl.value = await loadImage(result.value.heatmap_path)
          superimposedUrl.value = await loadImage(result.value.superimposed_path)
          ElMessage.success('预测完成')
        } catch (imgError) {
          ElMessage.warning('预测完成，但图片加载失败')
        }
      }
    } else {
      error.value = response.data.error || '预测失败'
      ElMessage.error(error.value)
    }
  } catch (err) {
    error.value = err.response?.data?.error || '预测失败，请稍后重试'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}
const handleImageError = (error) => {
  ElMessage.error('图片加载失败，请稍后重试')
}
const loadImage = async (imagePath) => {
  try {
    imageLoading.value = true
    const response = await api.get(`/chest_xray/image?path=${encodeURIComponent(imagePath)}`, {
      responseType: 'blob'
    })
    const blob = new Blob([response.data], { type: 'image/png' })
    return URL.createObjectURL(blob)
  } catch (error) {
    throw error
  } finally {
    imageLoading.value = false
  }
}
</script>

<style scoped>
.xray-container {
  max-width: 1000px;
  margin: 0 auto;
}
.xray-card {
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.xray-form {
  margin-top: 20px;
}
.result-section {
  margin-top: 20px;
}
.result-card {
  margin-bottom: 20px;
}
.result-content {
  line-height: 1.6;
}
.result-content h4 {
  margin: 0 0 10px 0;
  color: #303133;
}
.el-table {
  margin-bottom: 20px;
}
.el-image {
  border-radius: 8px;
  margin-bottom: 20px;
}
.error-section {
  margin-top: 20px;
}
</style>