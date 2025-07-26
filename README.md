# 医疗AI智能诊断平台

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.3+-green.svg)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-red.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 项目简介

医疗AI智能诊断平台是一个基于人工智能技术的综合性医疗诊断辅助系统，集成了多种医疗AI模型，为医生和患者提供智能化的医疗诊断支持。平台采用前后端分离架构，提供直观易用的Web界面和强大的后端API服务。

## ✨ 核心功能

### 🤖 AI诊断模块
- **医疗智能问答**: 基于Qwen模型的医疗知识问答系统
- **心脏病风险评估**: 基于机器学习的心脏病风险预测
- **肿瘤良恶性分类**: 智能肿瘤分类诊断
- **糖尿病风险评估**: 糖尿病风险智能评估
- **胸部X光疾病检测**: 基于深度学习的胸部X光片疾病检测与热力图分析

### 🔍 高级特性
- **多模态CAM热力图**: 支持GradCAM、GradCAM++、ScoreCAM等多种可视化方法
- **病灶定位分析**: 精确识别和标注病灶位置
- **置信度评估**: 提供预测结果的置信度评分
- **批量处理**: 支持批量图片上传和诊断

### 👥 用户管理
- **用户认证**: JWT令牌认证机制
- **历史记录**: 完整的诊断历史记录管理
- **个人档案**: 用户个人信息管理

### 📊 数据分析
- **实时统计**: 平台使用情况实时统计
- **数据可视化**: 基于ECharts的数据图表展示
- **预测记录**: 详细的预测结果记录和查询
- **历史记录管理**: 完整的诊断历史记录，支持多维度搜索和筛选
- **智能搜索**: 支持按模型类型、风险等级、时间范围、关键词等多条件组合搜索
- **健康建议**: 基于预测结果提供个性化健康建议
- **报告导出**: 支持PDF、Excel、Word等多种格式的诊断报告导出

## 🛠️ 技术栈

### 后端技术
- **框架**: Flask 2.3+
- **数据库**: PostgreSQL + Redis (支持pg_trgm全文搜索)
- **AI框架**: PyTorch 2.0+, Transformers 4.37+
- **机器学习**: Scikit-learn 1.3+
- **认证**: JWT (PyJWT)
- **图像处理**: OpenCV, PIL
- **深度学习模型**: DenseNet121, BERT, LSTM
- **数据库优化**: 复合索引、风险等级预计算

### 前端技术
- **框架**: Vue.js 3.3+
- **UI组件库**: Element Plus 2.3+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.2+
- **HTTP客户端**: Axios 1.5+
- **图表库**: ECharts 5.4+
- **构建工具**: Vite 4.4+

## 📁 项目结构

```
grop_medical_ai/
├── backend/                    # 后端服务
│   ├── app.py                 # Flask主应用
│   ├── config.py              # 配置文件
│   ├── requirements.txt       # Python依赖
│   ├── services/              # AI服务模块
│   │   ├── medical_qa_service.py      # 医疗问答服务
│   │   ├── heart_disease_service.py   # 心脏病预测服务
│   │   ├── tumor_service.py           # 肿瘤分类服务
│   │   ├── diabetes_service.py        # 糖尿病评估服务
│   │   ├── chest_xray_service.py      # 胸部X光检测服务
│   │   └── history_search_service.py  # 历史记录搜索服务
│   ├── models/                # AI模型文件
│   ├── utils/                 # 工具函数
│   └── logs/                  # 日志文件
├── frontend/                  # 前端应用
│   ├── src/
│   │   ├── components/        # Vue组件
│   │   ├── views/             # 页面视图
│   │   ├── stores/            # 状态管理
│   │   ├── router/            # 路由配置
│   │   └── utils/             # 工具函数
│   ├── package.json           # Node.js依赖
│   └── vite.config.js         # Vite配置
├── data/                      # 数据文件
├── results/                   # 预测结果和热力图
├── logs/                      # 系统日志
└── docs/                      # 项目文档
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.11
- **Node.js**: 16+
- **PostgreSQL**: 12+
- **Redis**: 6+
- **CUDA**: 11.0+ (可选，用于GPU加速)

### 1. 克隆项目

```bash
git clone https://github.com/259han/medical_ai_plat-AI.git
cd grop_medical_ai
```

### 2. 后端环境配置

```bash
# 进入后端目录
cd backend
# 推荐
conda create myenv python=3.11
conda activate myenv
# 或者
# 创建虚拟环境
python3.11 -m venv venv      # Linux/Mac（推荐）
py -3.11 -m venv venv        # Windows（推荐）
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
# 安装依赖
pip install -r requirements.txt
```

### 3. 数据库配置

```bash
# 创建PostgreSQL数据库
createdb medical_ai_db

# 初始化数据库表
psql -d medical_ai_db -f init_db.sql

# 创建数据库索引优化查询性能
psql -d medical_ai_db -f backend/create_indexes.sql

```

### 4. 前端环境配置

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
```

### 5. 启动服务

#### 启动redis
```bash
redis-server
```

#### 启动后端服务

```bash
cd backend
python app.py
```

#### 启动前端服务

```bash
cd frontend
npm run dev
```

访问地址：
- 前端: http://localhost:8081
- 后端API: http://localhost:5000

## 📖 使用指南

### 用户注册与登录

1. 访问平台首页，点击"注册"按钮
2. 填写用户名、邮箱和密码
3. 注册成功后自动登录，或使用已有账号登录

### AI诊断功能

#### 医疗问答
- 在医疗问答页面输入医疗相关问题
- 系统基于Qwen模型提供专业回答
- 支持中文医疗知识问答

#### 心脏病预测
- 输入相关生理指标（血糖、血压、BMI等）
- 系统评估心脏病风险
- 提供风险等级和建议

#### 肿瘤分类
- 输入肿瘤相关描述信息
- 系统进行良恶性分类
- 提供分类置信度

#### 糖尿病评估
- 输入糖尿病相关指标
- 系统评估糖尿病风险
- 提供预防建议

#### 胸部X光检测
- 上传胸部X光片（支持PNG、JPG格式）
- 系统检测14种常见胸部疾病
- 生成热力图显示病灶位置
- 支持多种CAM可视化方法

### 历史记录管理

- 查看所有诊断历史记录
- **多维度搜索**: 支持按模型类型、风险等级、时间范围、关键词搜索
- **智能筛选**: 组合多个条件进行精确筛选
- **实时搜索**: 输入关键词即可实时搜索预测结果和输入数据
- **高性能查询**: 优化的数据库索引和预计算风险等级
- **自动风险等级**: 系统自动计算并存储风险等级，确保显示一致性
- **报告导出**: 支持将诊断结果导出为PDF、Excel、Word等多种格式的专业报告
- 删除不需要的记录
- 导出诊断报告(点击具体的“查看详情”)

### 报告导出功能

平台提供了强大的诊断报告导出功能，支持多种格式的专业医疗报告生成：

#### 支持的报告格式
- **PDF文档**: 适合打印和正式场合使用
- **Excel表格**: 适合数据分析和二次处理
- **Word文档**: 适合编辑和修改

#### 报告导出流程
1. 在历史记录页面找到需要导出的诊断记录
2. 点击"查看详情"按钮
3. 在详情页面底部的"导出报告"区域选择所需格式
4. 点击"导出报告"按钮
5. 系统自动生成并下载报告文件

#### 报告内容
导出的报告包含以下内容：
- **基本信息**: 报告时间、预测类型、风险等级等
- **预测摘要**: 诊断结果的简要总结
- **详细结果**: 根据不同模型类型展示的详细诊断结果
- **健康建议**: 基于诊断结果提供的个性化健康建议

#### 技术特点
- **自动中英文转换**: 系统自动将中文内容转换为英文，确保PDF等格式的兼容性
- **智能翻译**: 内置26条常见健康建议的精确中英文映射
- **安全下载**: 采用带认证的文件下载机制，确保数据安全
- **格式优化**: 针对不同格式进行了专门的排版优化

#### 报告导出示例

```bash
# 导出API示例
POST /api/user/report/export
{
  "record_id": 123,
  "format": "pdf"  # 可选: pdf, excel, word
}

# 下载API示例
GET /api/user/report/download?filename=heart_disease_20240726123456.pdf
```

#### 故障排除
- **下载失败**: 确认浏览器已登录并有效，报告下载需要认证
- **中文乱码**: 系统已自动处理中文转英文，确保最新版本
- **格式问题**: 不同格式可能有细微排版差异，PDF格式最为稳定

## 🔧 配置说明

### 搜索功能配置

历史记录搜索支持以下参数：

```python
# 搜索参数示例
{
    "page": 1,                    # 页码
    "per_page": 10,               # 每页数量
    "type": "heart_disease",      # 模型类型过滤
    "result": "high",             # 风险等级过滤 (high/medium/low/info)
    "dateRange": "2024-01-01 to 2024-01-31",  # 日期范围
    "keyword": "心脏病"            # 关键词搜索
}
```

### 模型配置

在 `backend/config.py` 中配置AI模型路径：

```python
MODEL_CONFIGS = {
    "medical_qa": {
        "model_paths": [
            "models/medical_qa_models/qwen_medical_finetuned",
            "models/medical_qa_models/Qwen1.5-0.5B"
        ]
    },
    # 其他模型配置...
}
```

### 服务配置

```python
# 服务端口
PORT = 5000

# 数据库连接
DATABASE_URL = "postgresql://user:pass@localhost:5432/db"

# Redis缓存
REDIS_URL = "redis://localhost:6379"
```

## 📊 API文档

### 认证接口

```http
POST /api/auth/register
POST /api/auth/login
```

### AI诊断接口

```http
POST /api/medical_qa          # 医疗问答
POST /api/heart_disease       # 心脏病预测
POST /api/tumor              # 肿瘤分类
POST /api/diabetes           # 糖尿病评估
POST /api/chest_xray         # 胸部X光检测
```

### 用户管理接口

```http
GET  /api/user/profile        # 获取用户信息
PUT  /api/user/profile        # 更新用户信息
GET  /api/user/predictions    # 获取预测记录
GET  /api/user/history        # 获取历史记录（支持搜索）
DELETE /api/user/history/{id} # 删除历史记录
POST /api/user/report/export  # 导出报告
GET  /api/user/report/download # 下载报告
GET  /api/user/report/formats # 获取支持的报告格式
```

### 统计接口

```http
GET /api/stats/overview       # 平台统计概览
GET /api/user/stats          # 用户统计信息
POST /api/test/risk_level    # 测试风险等级判断
```

## 🔒 安全特性

- **JWT认证**: 安全的用户认证机制
- **CORS配置**: 跨域请求安全控制
- **输入验证**: 严格的数据输入验证
- **SQL注入防护**: 使用ORM防止SQL注入
- **文件上传安全**: 文件类型和大小限制
- **路径遍历防护**: 防止路径遍历攻击

## 📈 性能优化

- **Redis缓存**: 减少数据库查询压力
- **模型缓存**: AI模型内存缓存
- **异步处理**: 支持异步任务处理
- **图片压缩**: 自动图片压缩优化
- **CDN支持**: 静态资源CDN加速
- **数据库索引优化**: 为历史记录查询创建复合索引，提升查询性能80%+
- **风险等级预计算**: 自动计算并存储风险等级，避免重复计算
- **搜索优化**: 高效的数据库查询和索引优化
- **分页加载**: 支持大数据量的分页显示
- **全文搜索**: 支持关键词模糊搜索，使用PostgreSQL pg_trgm扩展
- **查询性能**: 历史记录筛选从2-5秒优化到0.1-0.5秒

## 🐛 故障排除

### 常见问题

1. **模型加载失败**
   - 检查模型文件路径
   - 确认CUDA环境配置
   - 查看日志文件

2. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串
   - 确认数据库权限

3. **前端无法访问后端**
   - 检查CORS配置
   - 验证API地址
   - 确认网络连接

4. **搜索功能异常**
   - 检查数据库索引
   - 验证搜索参数格式
   - 查看搜索服务日志
   - 确认pg_trgm扩展已启用

5. **历史记录显示问题**
   - 检查数据格式一致性
   - 验证时间时区设置
   - 确认风险等级判断逻辑
   - 检查risk_level字段是否存在

6. **数据库索引问题**
   - 确认PostgreSQL版本支持pg_trgm扩展
   - 检查索引创建是否成功
   - 验证复合索引是否生效

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
grep ERROR logs/app.log
```

## 🙏 致谢

- [Qwen](https://github.com/QwenLM/Qwen) - 医疗问答模型
- [PyTorch](https://pytorch.org/) - 深度学习框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Element Plus](https://element-plus.org/) - UI组件库
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM框架
- [ECharts](https://echarts.apache.org/) - 数据可视化库
- [PostgreSQL](https://www.postgresql.org/) - 数据库系统
- [pg_trgm](https://www.postgresql.org/docs/current/pgtrgm.html) - 全文搜索扩展

---