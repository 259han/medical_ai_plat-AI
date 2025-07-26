<template>
  <MainLayout :activeMenu="route.path">
    <template #header-icon>
      <el-icon><Monitor /></el-icon>
    </template>
    <template #header-title>
      医疗AI平台
    </template>
    <div class="dashboard-content">
      <el-row :gutter="20">
        <el-col :span="24">
          <h3>欢迎使用医疗AI平台</h3>
          <p>选择下方的功能模块开始您的医疗AI诊断之旅</p>
        </el-col>
      </el-row>
      <el-row :gutter="20" class="feature-cards">
        <el-col :xs="24" :sm="12" :md="6" v-for="feature in features" :key="feature.path">
          <el-card 
            class="feature-card" 
            shadow="hover"
            @click="navigateTo(feature.path)"
          >
            <div class="feature-icon">
              <el-icon :size="40" :color="feature.color">
                <component :is="feature.icon" />
              </el-icon>
            </div>
            <h4>{{ feature.title }}</h4>
            <p>{{ feature.description }}</p>
          </el-card>
        </el-col>
      </el-row>
      <el-row :gutter="20" class="stats-section">
        <el-col :span="24">
          <h3>使用统计</h3>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12" :md="6" v-for="stat in stats" :key="stat.label">
              <el-card class="stat-card">
                <div class="stat-content">
                  <div class="stat-icon">
                    <el-icon :size="24" :color="stat.color">
                      <component :is="stat.icon" />
                    </el-icon>
                  </div>
                  <div class="stat-info">
                    <div class="stat-value">{{ stat.value }}</div>
                    <div class="stat-label">{{ stat.label }}</div>
                  </div>
                </div>
              </el-card>
            </el-col>
          </el-row>
        </el-col>
      </el-row>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/utils/api'
import { ElMessage } from 'element-plus'
import MainLayout from '@/components/MainLayout.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const stats = ref([
  { label: '总预测次数', value: 0, icon: 'TrendCharts', color: '#409eff' },
  { label: '医疗问答', value: 0, icon: 'ChatDotRound', color: '#67c23a' },
  { label: '心脏病预测', value: 0, icon: 'Heart', color: '#f56c6c' },
  { label: '肿瘤分类', value: 0, icon: 'Microscope', color: '#e6a23c' },
  { label: '糖尿病评估', value: 0, icon: 'TrendCharts', color: '#909399' },
  { label: '胸部X光预测', value: 0, icon: 'Camera', color: '#00c4b4' }
])

const features = [
  {
    title: '医疗问答',
    description: '基于AI的智能医疗问题解答',
    icon: 'ChatDotRound',
    color: '#67c23a',
    path: '/medical-qa'
  },
  {
    title: '心脏病预测',
    description: '心脏病风险评估与预测',
    icon: 'Heart',
    color: '#f56c6c',
    path: '/heart-disease'
  },
  {
    title: '肿瘤分类',
    description: '肿瘤良恶性智能分类',
    icon: 'Microscope',
    color: '#e6a23c',
    path: '/tumor'
  },
  {
    title: '糖尿病评估',
    description: '糖尿病风险智能评估',
    icon: 'TrendCharts',
    color: '#409eff',
    path: '/diabetes'
  },
  {
    title: '胸部X光预测',
    description: '胸部X光疾病检测与热力图分析',
    icon: 'Camera',
    color: '#00c4b4',
    path: '/chest-xray'
  }
]

const navigateTo = (path) => {
  router.push(path)
}

const fetchStats = async () => {
  try {
    const response = await api.get('/stats/overview')
    const data = response.data
    stats.value[0].value = data.total_predictions || 0
    stats.value[1].value = data.model_stats?.medical_qa || 0
    stats.value[2].value = data.model_stats?.heart_disease || 0
    stats.value[3].value = data.model_stats?.tumor || 0
    stats.value[4].value = data.model_stats?.diabetes || 0
    stats.value[5].value = data.model_stats?.chest_xray || 0
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.dashboard-content h3 {
  margin: 0 0 10px 0;
  color: #303133;
}
.dashboard-content p {
  color: #606266;
  margin: 0 0 30px 0;
}
.feature-cards {
  margin-bottom: 40px;
}
.feature-card {
  cursor: pointer;
  transition: transform 0.3s;
  height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}
.feature-card:hover {
  transform: translateY(-5px);
}
.feature-icon {
  margin-bottom: 15px;
}
.feature-card h4 {
  margin: 0 0 10px 0;
  color: #303133;
}
.feature-card p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}
.stats-section h3 {
  margin: 0 0 20px 0;
}
.stat-card {
  margin-bottom: 20px;
}
.stat-content {
  display: flex;
  align-items: center;
  gap: 15px;
}
.stat-icon {
  flex-shrink: 0;
}
.stat-info {
  flex: 1;
}
.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}
.stat-label {
  color: #606266;
  font-size: 14px;
}
</style>