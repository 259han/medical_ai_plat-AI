<template>
  <MainLayout :activeMenu="route.path">
    <template #header-icon>
      <el-icon><TrendCharts /></el-icon>
    </template>
    <template #header-title>
      预测历史
    </template>
    <div class="history-container">
      <div class="header">
        <h1>预测历史</h1>
        <p>查看您的所有预测记录和结果</p>
        <button @click="goHome" class="back-btn">返回主页</button>
      </div>
      <div class="filters">
        <div class="filter-group">
          <label for="typeFilter">预测类型</label>
          <select id="typeFilter" v-model="filters.type" @change="loadHistory">
            <option value="">全部类型</option>
            <option value="medical_qa">医疗问答</option>
            <option value="heart_disease">心脏病预测</option>
            <option value="tumor">肿瘤分类</option>
            <option value="diabetes">糖尿病评估</option>
            <option value="chest_xray">胸部X光检测</option>
          </select>
        </div>
        <div class="filter-group">
          <label for="resultFilter">风险等级</label>
          <select id="resultFilter" v-model="filters.result" @change="loadHistory">
            <option value="">全部等级</option>
            <option value="high">高风险</option>
            <option value="medium">中风险</option>
            <option value="low">低风险</option>
            <option value="info">信息类</option>
          </select>
        </div>
        <div class="filter-group">
          <label for="dateFilter">时间范围</label>
          <select id="dateFilter" v-model="filters.dateRange" @change="loadHistory">
            <option value="">全部时间</option>
            <option value="today">今天</option>
            <option value="yesterday">昨天</option>
            <option value="this_week">本周</option>
            <option value="this_month">本月</option>
          </select>
        </div>


      </div>
      <div class="history-actions" v-if="history.length > 0">
        <button @click="deleteAllRecords" class="delete-all-btn">
          🗑️ 删除所有历史记录
        </button>
      </div>
      <div class="history-content">
        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>加载中...</p>
        </div>
        <div v-else-if="history.length === 0" class="empty-state">
          <div class="empty-icon">📋</div>
          <h3>暂无预测记录</h3>
          <p>开始使用我们的AI预测功能来查看您的历史记录</p>
          <router-link to="/dashboard" class="start-btn">开始预测</router-link>
        </div>
        <div v-else class="history-list">
          <div
            v-for="record in history"
            :key="record.id"
            class="history-item"
            :class="getRiskClass(record.risk_level)"
          >
            <div class="record-header">
              <div class="record-type">
                <span class="type-icon">
                  {{ getTypeIcon(record.model_type) }}
                </span>
                <span class="type-name">{{ record.model_name }}</span>
              </div>
              <div class="record-date">
                {{ record.created_at_local }}
              </div>
            </div>
            <div class="record-content">
              <div class="prediction-summary">
                <div class="summary-text">{{ record.summary }}</div>
                <div class="risk-badge" :class="getRiskClass(record.risk_level)">
                  {{ getRiskText(record.risk_level) }}
                </div>
              </div>
              <div class="prediction-details">
                <div class="confidence">
                  置信度: {{ (record.confidence_score * 100).toFixed(1) }}%
                </div>
                <div class="recommendations">
                  <h4>健康建议</h4>
                  <ul>
                    <li v-for="(rec, index) in record.recommendations.slice(0, 2)" :key="index">
                      {{ rec }}
                    </li>
                  </ul>
                </div>
              </div>
              <div class="record-actions">
                <button @click="viewDetails(record)" class="details-btn">
                  查看详情
                </button>
                <button @click="deleteRecord(record.id)" class="delete-btn">
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="hasMore && !loading" class="load-more">
          <button @click="loadMore" class="load-more-btn">
            加载更多
          </button>
        </div>
      </div>
      <!-- 详情模态框 -->
      <div v-if="showDetails" class="modal-overlay" @click="closeDetails">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>预测详情</h3>
            <button @click="closeDetails" class="close-btn">&times;</button>
          </div>
          <div class="modal-body">
            <div v-if="selectedRecord" class="detail-content">
              <div class="detail-section">
                <h4>基本信息</h4>
                <div class="detail-grid">
                  <div class="detail-item">
                    <span class="detail-label">预测类型</span>
                    <span class="detail-value">{{ selectedRecord.model_name }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">预测时间</span>
                    <span class="detail-value">{{ selectedRecord.created_at_local }}</span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">预测结果</span>
                    <span class="detail-value" :class="getRiskClass(selectedRecord.risk_level)">
                      {{ getRiskText(selectedRecord.risk_level) }}
                    </span>
                  </div>
                  <div class="detail-item">
                    <span class="detail-label">置信度</span>
                    <span class="detail-value">{{ (selectedRecord.confidence_score * 100).toFixed(1) }}%</span>
                  </div>
                </div>
              </div>
              <div class="detail-section">
                <h4>输入数据</h4>
                <div class="input-data-grid">
                  <div
                    v-for="(value, key) in selectedRecord.input_data"
                    :key="key"
                    class="input-data-item"
                  >
                    <span class="input-data-label">{{ getDataLabel(key) }}</span>
                    <span class="input-data-value">{{ formatDataValue(key, value) }}</span>
                  </div>
                </div>
              </div>
              <div class="detail-section">
                <h4>预测摘要</h4>
                <div class="summary-content">
                  <p>{{ selectedRecord.summary }}</p>
                </div>
              </div>
              <div class="detail-section">
                <h4>健康建议</h4>
                <div class="recommendations">
                  <ul>
                    <li v-for="(recommendation, index) in selectedRecord.recommendations" :key="index">
                      {{ recommendation }}
                    </li>
                  </ul>
                </div>
              </div>
              <!-- 添加导出报告功能 -->
              <div class="detail-section">
                <h4>导出报告</h4>
                <div class="export-options">
                  <div class="export-format">
                    <label for="exportFormat">报告格式</label>
                    <select id="exportFormat" v-model="exportFormat">
                      <option v-for="format in reportFormats" :key="format.value" :value="format.value">
                        {{ format.label }}
                      </option>
                    </select>
                  </div>
                  <button @click="exportReport" class="export-btn" :disabled="exporting">
                    {{ exporting ? '导出中...' : '导出报告' }}
                  </button>
                </div>
                <div v-if="exportError" class="export-error">
                  {{ exportError }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { api, exportReport, getReportFormats } from '@/utils/api'
import MainLayout from '@/components/MainLayout.vue'

export default {
  name: 'History',
  components: { MainLayout },
  setup() {
    const router = useRouter()
    const route = useRoute()
    const goHome = () => router.push('/dashboard')
    const loading = ref(false)
    const history = ref([])
    const hasMore = ref(true)
    const page = ref(1)
    const showDetails = ref(false)
    const selectedRecord = ref(null)
    
    // 导出报告相关
    const exportFormat = ref('pdf')
    const reportFormats = ref([
      { value: 'pdf', label: 'PDF文档' },
      { value: 'excel', label: 'Excel表格' },
      { value: 'word', label: 'Word文档' }
    ])
    const exporting = ref(false)
    const exportError = ref('')
    
    // 加载报告格式
    const loadReportFormats = async () => {
      try {
        const response = await getReportFormats()
        reportFormats.value = response.data.formats
      } catch (err) {
        console.error('加载报告格式失败:', err)
      }
    }
    
    // 导出报告
    const handleExportReport = async () => {
      if (!selectedRecord.value || exporting.value) return
      
      console.log('开始导出报告，记录ID:', selectedRecord.value.id);
      console.log('导出格式:', exportFormat.value);
      console.log('选中的记录:', selectedRecord.value);
      
      exporting.value = true
      exportError.value = ''
      
      try {
        console.log('调用exportReport API...');
        const response = await exportReport(
          selectedRecord.value.id,
          exportFormat.value
        )
        
        console.log('API响应:', response);
        
        // 下载文件
        const downloadUrl = response.data.download_url
        const filename = response.data.filename
        const token = localStorage.getItem('token')
        try {
          const res = await fetch(downloadUrl, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          if (!res.ok) throw new Error('下载失败')
          const blob = await res.blob()
          const link = document.createElement('a')
          link.href = window.URL.createObjectURL(blob)
          link.download = filename
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
        } catch (err) {
          console.error('下载失败', err)
          exportError.value = '下载失败，请重试'
          ElMessage({ type: 'error', message: exportError.value, duration: 3000 })
          return
        }
        
        ElMessage({
          type: 'success',
          message: '报告导出成功',
          duration: 3000
        })
      } catch (err) {
        console.error('导出报告失败:', err);
        console.error('错误详情:', err.response?.data);
        exportError.value = err.response?.data?.error || '导出报告失败，请稍后重试'
        
        ElMessage({
          type: 'error',
          message: exportError.value,
          duration: 3000
        })
      } finally {
        exporting.value = false
      }
    }
    
    const filters = reactive({
      type: '',
      result: '',
      dateRange: ''
    })
    const loadHistory = async (reset = true) => {
      if (reset) {
        page.value = 1
        history.value = []
      }
      loading.value = true
      try {
        const params = {
          page: page.value,
          type: filters.type,
          result: filters.result,
          dateRange: filters.dateRange
        }
        const response = await api.get('/user/history', { params })
        const data = response.data
        console.log('后端返回的原始数据:', data.records)
        const transformedRecords = data.records.map(record => ({
          id: record.id,
          model_type: record.model_type,
          model_name: record.model_name,
          summary: record.summary,
          risk_level: record.risk_level,
          confidence_score: record.confidence_score || 0.8,
          input_data: record.input_data,
          prediction_result: record.prediction_result,
          recommendations: record.recommendations,
          created_at: record.created_at,
          created_at_local: record.created_at_local
        }))
        if (reset) {
          history.value = transformedRecords
        } else {
          history.value.push(...transformedRecords)
        }
        hasMore.value = data.current_page < data.pages
      } catch (err) {
        console.error('加载历史记录失败:', err)
      } finally {
        loading.value = false
      }
    }
    const loadMore = () => {
      if (!loading.value && hasMore.value) {
        page.value++
        loadHistory(false)
      }
    }
    const viewDetails = (record) => {
      console.log('查看详情 - 记录数据:', record)
      console.log('风险等级:', record.risk_level)
      console.log('预测结果:', record.prediction_result)
      selectedRecord.value = record
      showDetails.value = true
    }
    const closeDetails = () => {
      showDetails.value = false
      selectedRecord.value = null
    }
    const deleteRecord = async (id) => {
      try {
        await ElMessageBox.confirm(
          '确定要删除这条记录吗？',
          '删除确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await api.delete(`/user/history/${id}`)
        history.value = history.value.filter(record => record.id !== id)
        
        ElMessage({
          type: 'success',
          message: '记录删除成功',
          duration: 2000
        })
      } catch (err) {
        if (err === 'cancel') {
          return
        }
        console.error('删除记录失败:', err)
        ElMessage({
          type: 'error',
          message: '删除失败，请稍后重试',
          duration: 2000
        })
      }
    }
    const deleteAllRecords = async () => {
      try {
        // 使用Element Plus的确认对话框
        await ElMessageBox.confirm(
          '此操作将删除您的所有历史记录！删除后无法恢复，确定要继续吗？',
          '删除确认',
          {
            confirmButtonText: '确定删除',
            cancelButtonText: '取消',
            type: 'warning',
            dangerouslyUseHTMLString: true,
            customClass: 'delete-confirm-dialog'
          }
        )
        
        // 用户确认删除
        const response = await api.delete('/user/history/all')
        const data = response.data
        
        // 清空本地历史记录
        history.value = []
        hasMore.value = false
        
        // 显示成功消息
        ElMessage({
          type: 'success',
          message: data.message,
          duration: 3000
        })
        
        console.log('删除所有历史记录成功:', data)
      } catch (err) {
        if (err === 'cancel') {
          // 用户取消删除
          return
        }
        
        console.error('删除所有历史记录失败:', err)
        ElMessage({
          type: 'error',
          message: '删除失败，请稍后重试',
          duration: 3000
        })
      }
    }

    const getTypeIcon = (type) => {
      const icons = {
        medical_qa: '💬',
        heart_disease: '🏥',
        tumor: '🩺',
        diabetes: '💉',
        chest_xray: '📷'
      }
      return icons[type] || '📊'
    }
    const getTypeName = (type) => {
      const names = {
        medical_qa: '医疗问答',
        heart_disease: '心脏病预测',
        tumor: '肿瘤分类',
        diabetes: '糖尿病评估',
        chest_xray: '胸部X光检测'
      }
      return names[type] || '未知类型'
    }
    const getRiskClass = (riskLevel) => {
      const classes = {
        high: 'high-risk',
        medium: 'medium-risk',
        low: 'low-risk',
        info: 'info-risk'
      }
      return classes[riskLevel] || 'info-risk'
    }
    const getRiskText = (riskLevel) => {
      const texts = {
        high: '高风险',
        medium: '中风险',
        low: '低风险',
        info: '信息类'
      }
      return texts[riskLevel] || '信息类'
    }
    const getDataLabel = (key) => {
      const labels = {
        age: '年龄',
        sex: '性别',
        gender: '性别',
        cp: '胸痛类型',
        trestbps: '静息血压',
        chol: '胆固醇',
        fbs: '空腹血糖',
        restecg: '心电图结果',
        thalach: '最大心率',
        exang: '运动诱发心绞痛',
        oldpeak: 'ST段压低',
        slope: 'ST段斜率',
        ca: '主要血管数量',
        thal: '地中海贫血',
        pregnancies: '怀孕次数',
        glucose: '血糖水平',
        blood_pressure: '血压',
        skin_thickness: '皮肤厚度',
        insulin: '胰岛素',
        bmi: 'BMI',
        diabetes_pedigree: '糖尿病家族史',
        smoking: '吸烟史',
        yellow_fingers: '黄手指',
        anxiety: '焦虑',
        peer_pressure: '同伴压力',
        chronic_disease: '慢性疾病',
        fatigue: '疲劳',
        allergy: '过敏',
        wheezing: '喘息',
        alcohol_consuming: '饮酒',
        coughing: '咳嗽',
        shortness_of_breath: '呼吸短促',
        swallowing_difficulty: '吞咽困难',
        chest_pain: '胸痛',
        lung_cancer: '肺癌家族史'
      }
      return labels[key] || key
    }
    const formatDataValue = (key, value) => {
      if (key === 'sex' || key === 'gender') {
        return value === '1' || value === 'M' ? '男性' : '女性'
      }
      if (key === 'fbs' || key === 'exang' || key === 'smoking' || key === 'yellow_fingers' || 
          key === 'anxiety' || key === 'peer_pressure' || key === 'chronic_disease' || 
          key === 'fatigue' || key === 'allergy' || key === 'wheezing' || key === 'alcohol_consuming' ||
          key === 'coughing' || key === 'shortness_of_breath' || key === 'swallowing_difficulty' ||
          key === 'chest_pain' || key === 'lung_cancer') {
        return value === 'YES' || value === '1' ? '是' : '否'
      }
      if (key === 'trestbps' || key === 'blood_pressure') {
        return `${value} mmHg`
      }
      if (key === 'chol') {
        return `${value} mg/dl`
      }
      if (key === 'glucose') {
        return `${value} mg/dl`
      }
      if (key === 'insulin') {
        return `${value} mu U/ml`
      }
      if (key === 'skin_thickness') {
        return `${value} mm`
      }
      return value
    }
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }
    const getRecommendations = (type) => {
      const recommendations = {
        heart_disease: [
          '定期进行体检，监测血压、血糖和胆固醇水平',
          '保持健康的生活方式，适量运动，均衡饮食',
          '避免吸烟和过量饮酒',
          '如有不适症状，请及时就医'
        ],
        tumor: [
          '定期进行体检和筛查，特别是胸部CT检查',
          '避免吸烟和二手烟暴露',
          '保持健康的生活方式，适量运动',
          '如有持续咳嗽、胸痛等症状，请及时就医',
          '注意室内空气质量，避免有害物质暴露'
        ],
        diabetes: [
          '定期监测血糖水平，特别是空腹血糖和餐后血糖',
          '保持健康的饮食习惯，控制碳水化合物摄入',
          '适量运动，保持健康体重',
          '避免高糖、高脂肪食物',
          '如有家族史，应更加注意预防'
        ]
      }
      return recommendations[type] || ['建议定期体检，保持健康生活方式']
    }
    onMounted(() => {
      loadHistory()
      loadReportFormats()
    })
    return {
      loading,
      history,
      hasMore,
      filters,
      showDetails,
      selectedRecord,
      loadHistory,
      loadMore,
      viewDetails,
      closeDetails,
      deleteRecord,
      deleteAllRecords,
      getTypeIcon,
      getTypeName,
      getRiskClass,
      getRiskText,
      getDataLabel,
      formatDataValue,
      formatDate,
      getRecommendations,
      goHome,
      route,
      // 导出报告相关
      exportFormat,
      reportFormats,
      exporting,
      exportError,
      exportReport: handleExportReport
    }
  }
}
</script>

<style scoped>
.history-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  text-align: center;
  margin-bottom: 30px;
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

.back-btn {
  background: #667eea;
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  transition: transform 0.2s ease;
  border: none;
  cursor: pointer;
  font-size: 16px;
}

.back-btn:hover {
  background: #5a6fd8;
  transform: translateY(-2px);
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 30px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 150px;
}

.filter-group label {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.search-tips {
  color: #666;
  font-size: 12px;
  margin-top: 4px;
  display: block;
}

.filter-group select,
.filter-group input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  transition: border-color 0.2s ease;
}

.filter-group select:focus,
.filter-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
}

  .filter-actions {
    display: flex;
    gap: 10px;
    align-items: flex-end;
  }
  
  .history-actions {
    display: flex;
    justify-content: flex-end;
    margin: 20px 0;
    padding: 15px;
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 8px;
  }
  
  .delete-all-btn {
    background: #dc3545;
    color: white;
    border: none;
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .delete-all-btn:hover {
    background: #c82333;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
  }
  
  .delete-all-btn:active {
    transform: translateY(0);
  }
  
  /* 自定义确认对话框样式 */
  :deep(.delete-confirm-dialog) {
    .el-message-box__header {
      background: #fff3cd;
      border-bottom: 1px solid #ffeaa7;
    }
    
    .el-message-box__title {
      color: #856404;
      font-weight: 600;
    }
    
    .el-message-box__content {
      padding: 20px;
      color: #333;
      font-size: 16px;
      line-height: 1.6;
    }
    
    .el-button--primary {
      background: #dc3545;
      border-color: #dc3545;
    }
    
    .el-button--primary:hover {
      background: #c82333;
      border-color: #c82333;
    }
  }

.clear-btn,
.search-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-weight: 500;
}

.clear-btn {
  background: #f8f9fa;
  color: #666;
  border: 1px solid #ddd;
}

.clear-btn:hover {
  background: #e9ecef;
  color: #333;
}

.search-btn {
  background: #667eea;
  color: white;
}

.search-btn:hover {
  background: #5a6fd8;
  transform: translateY(-1px);
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group label {
  font-weight: 500;
  color: #555;
  font-size: 14px;
}

.filter-group select {
  padding: 10px 12px;
  border: 2px solid #e1e5e9;
  border-radius: 6px;
  font-size: 14px;
  min-width: 150px;
}

.filter-group select:focus {
  outline: none;
  border-color: #667eea;
}

.history-content {
  min-height: 400px;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h3 {
  color: #333;
  font-size: 24px;
  margin-bottom: 10px;
}

.empty-state p {
  color: #666;
  margin-bottom: 30px;
}

.start-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  transition: transform 0.2s ease;
}

.start-btn:hover {
  transform: translateY(-2px);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.history-item {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  border-left: 4px solid #e1e5e9;
}

.history-item.high-risk {
  border-left-color: #ff6b6b;
}

.history-item.medium-risk {
  border-left-color: #e6a23c;
}

.history-item.low-risk {
  border-left-color: #51cf66;
}

.history-item.info-risk {
  border-left-color: #409eff;
}

.record-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e1e5e9;
}

.record-type {
  display: flex;
  align-items: center;
  gap: 10px;
}

.type-icon {
  font-size: 24px;
}

.type-name {
  font-weight: 600;
  color: #333;
}

.record-date {
  color: #666;
  font-size: 14px;
}

.record-content {
  padding: 20px;
}

.prediction-summary {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  gap: 15px;
}

.summary-text {
  flex: 1;
  color: #333;
  font-size: 16px;
  line-height: 1.5;
}

.risk-badge {
  padding: 6px 12px;
  border-radius: 16px;
  font-weight: 600;
  font-size: 12px;
  white-space: nowrap;
}

.risk-badge.high-risk {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fbc4c4;
}

.risk-badge.medium-risk {
  background: #fdf6ec;
  color: #e6a23c;
  border: 1px solid #f5dab1;
}

.risk-badge.low-risk {
  background: #f0f9ff;
  color: #67c23a;
  border: 1px solid #b3d8ff;
}

.risk-badge.info-risk {
  background: #f0f9ff;
  color: #409eff;
  border: 1px solid #b3d8ff;
}

.prediction-details {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 20px;
}

.recommendations {
  flex: 1;
}

.recommendations h4 {
  color: #333;
  margin-bottom: 10px;
  font-size: 14px;
}

.recommendations ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.recommendations li {
  padding: 4px 0;
  color: #666;
  font-size: 13px;
  position: relative;
  padding-left: 15px;
}

.recommendations li::before {
  content: "•";
  color: #667eea;
  font-weight: bold;
  position: absolute;
  left: 0;
}

.prediction-result {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.result-badge {
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
}

.result-badge.high-risk {
  background: #ff6b6b;
  color: white;
}

.result-badge.low-risk {
  background: #51cf66;
  color: white;
}

.confidence {
  color: #666;
  font-size: 14px;
}

.record-details h4 {
  color: #333;
  margin-bottom: 15px;
  font-size: 16px;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.data-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.data-label {
  color: #555;
  font-size: 14px;
}

.data-value {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.record-actions {
  display: flex;
  gap: 12px;
}

.details-btn, .delete-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.details-btn {
  background: #667eea;
  color: white;
}

.details-btn:hover {
  background: #5a6fd8;
}

.delete-btn {
  background: #dc3545;
  color: white;
}

.delete-btn:hover {
  background: #c82333;
}

.load-more {
  text-align: center;
  margin-top: 30px;
}

.load-more-btn {
  background: #f8f9fa;
  color: #333;
  padding: 12px 24px;
  border: 2px solid #e1e5e9;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.load-more-btn:hover {
  background: #e9ecef;
  border-color: #667eea;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 800px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e1e5e9;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  padding: 20px;
}

.detail-section {
  margin-bottom: 30px;
}

.detail-section h4 {
  color: #333;
  margin-bottom: 15px;
  font-size: 18px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.detail-label {
  color: #555;
  font-weight: 500;
}

.detail-value {
  font-weight: 600;
  color: #333;
}

.detail-value.high-risk {
  color: #ff6b6b;
}

.detail-value.low-risk {
  color: #51cf66;
}

.detail-value.medium-risk {
  color: #e6a23c;
}

.detail-value.info-risk {
  color: #409eff;
}

.summary-content {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.summary-content p {
  margin: 0;
  color: #333;
  line-height: 1.6;
  font-size: 15px;
}

.input-data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.input-data-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
}

.input-data-label {
  color: #555;
  font-size: 14px;
}

.input-data-value {
  font-weight: 600;
  color: #333;
  font-size: 14px;
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

/* 导出报告样式 */
.export-options {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-top: 10px;
}

.export-format {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.export-format label {
  font-weight: 500;
  color: #555;
  font-size: 14px;
}

.export-format select {
  padding: 10px 12px;
  border: 2px solid #e1e5e9;
  border-radius: 6px;
  font-size: 14px;
  min-width: 150px;
}

.export-btn {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.export-btn:hover {
  background: #5a6fd8;
  transform: translateY(-2px);
}

.export-btn:disabled {
  background: #a0aec0;
  cursor: not-allowed;
  transform: none;
}

.export-error {
  color: #e53e3e;
  margin-top: 10px;
  font-size: 14px;
}

@media (max-width: 768px) {
  .filters {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-group {
    min-width: auto;
  }
  
  .filter-actions {
    justify-content: center;
    margin-top: 10px;
  }
  
  .record-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .prediction-summary {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .prediction-details {
    flex-direction: column;
    gap: 15px;
  }
  
  .data-grid {
    grid-template-columns: 1fr;
  }
  
  .record-actions {
    flex-direction: column;
  }
  
  .modal-content {
    width: 95%;
    margin: 20px;
  }
  
  .input-data-grid {
    grid-template-columns: 1fr;
  }
}
</style> 