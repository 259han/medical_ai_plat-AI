#!/usr/bin/env python3
"""
Flask医疗AI平台配置文件
"""

import os
from pathlib import Path
from typing import Dict, Any
import torch

# ==================== 基础路径配置 ====================
BASE_DIR = Path(__file__).parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
LOGS_DIR = BASE_DIR / "logs"

# 创建必要的目录
for directory in [LOGS_DIR, BASE_DIR / "uploads", BASE_DIR / "results", BASE_DIR / "backend" / "models" / "chest_xray_models", BASE_DIR / "sessions"]:
    directory.mkdir(exist_ok=True)

# ==================== Flask应用配置 ====================
class Config:
    """基础配置类"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'medical_ai_secret_key_2024')
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'postgresql+psycopg2://postgres:259006@localhost:5432/medical_ai_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis配置
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    # 会话配置 - 使用文件系统避免 Redis 依赖
    SESSION_TYPE = 'filesystem'
    SESSION_FILE_DIR = BASE_DIR / "sessions"  # 会话文件存储目录
    SESSION_KEY_PREFIX = 'medical_ai_'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = 86400  # 24小时
    
    # 服务配置
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # CORS配置
    CORS_ORIGINS = [
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = BASE_DIR / "logs" / 'app.log'
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    # 胸部X光配置
    NUM_CLASSES = 14  # 疾病分类数量
    DISEASE_LABELS = [
        'Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration',
        'Mass', 'Nodule', 'Pneumonia', 'Pneumothorax',
        'Consolidation', 'Edema', 'Emphysema', 'Fibrosis',
        'Pleural_Thickening', 'Hernia'
    ]
    CHECKPOINT_DIR = BASE_DIR / "backend" / "models" / "chest_xray_models"
    RESULT_DIR = BASE_DIR / "results"
    UPLOAD_DIR = BASE_DIR / "uploads"
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    # 生产环境安全配置
    CORS_ORIGINS = [
        "https://your-domain.com",
        "https://www.your-domain.com"
    ]

class TestingConfig(Config):
    """测试环境配置"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# ==================== 模型配置 ====================
MODEL_CONFIGS = {
    "medical_qa": {
        "model_paths": [
            BASE_DIR / "models" / "medical_qa_models" / "qwen_medical_finetuned",
            BASE_DIR / "models" / "medical_qa_models" / "Qwen1.5-0.5B"
        ],
        "online_model": "Qwen/Qwen1.5-0.5B",
        "max_length": 512,
        "temperature": 0.7,
        "top_p": 0.9
    },
    "heart_disease": {
        "model_paths": [
            BASE_DIR / "models" / "heart_disease_models" / "heart_disease_model.pkl"
        ],
        "feature_names": [
            'FastingBloodSugar', 'HbA1c', 'DietQuality', 'SerumCreatinine',
            'MedicalCheckupsFrequency', 'BMI', 'MedicationAdherence',
            'CholesterolHDL', 'CholesterolTriglycerides', 'SystolicBP'
        ]
    },
    "tumor": {
        "model_paths": [
            BASE_DIR / "models" / "tumor_classification_models" / "bert-base-chinese"
        ],
        "online_model": "bert-base-chinese",
        "class_names": ['良性', '恶性', '交界性', '未确定'],
        "max_length": 512
    },
    "diabetes": {
        "model_paths": [
            BASE_DIR / "models" / "diabetes_models" / "diabetes_model.pth"
        ],
        "feature_names": [
            'Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
            'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age'
        ]
    },
    "chest_xray": {
        "model_paths": [
            BASE_DIR / "backend" / "models" / "chest_xray_models" / "best_model.pth"
        ],
        "model_name": "densenet121",
        "num_classes": 14,
        "disease_labels": [
            'Atelectasis', 'Cardiomegaly', 'Effusion', 'Infiltration',
            'Mass', 'Nodule', 'Pneumonia', 'Pneumothorax',
            'Consolidation', 'Edema', 'Emphysema', 'Fibrosis',
            'Pleural_Thickening', 'Hernia'
        ],
        "upload_dir": BASE_DIR / "uploads",
        "result_dir": BASE_DIR / "results",
        "checkpoint_dir": BASE_DIR / "backend" / "models" / "chest_xray_models",
        "allowed_extensions": {'png', 'jpg', 'jpeg'},
        "device": 'cuda' if torch.cuda.is_available() else 'cpu'
    }
}

# ==================== 缓存配置 ====================
CACHE_CONFIG = {
    "default_timeout": 300,  # 5分钟
    "medical_qa_timeout": 300,  # 医疗问答缓存5分钟
    "prediction_timeout": 600,  # 预测结果缓存10分钟
    "user_session_timeout": 3600,  # 用户会话缓存1小时
}

# ==================== 限流配置 ====================
RATE_LIMIT_CONFIG = {
    "default": "100 per minute",
    "auth": "10 per minute",
    "prediction": "50 per minute"
}

# ==================== 配置获取函数 ====================
def get_config():
    """根据环境变量获取配置"""
    env = os.environ.get('FLASK_ENV', 'development')
    
    if env == 'production':
        return ProductionConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return DevelopmentConfig

def get_model_config(model_name: str) -> Dict[str, Any]:
    """获取指定模型的配置"""
    return MODEL_CONFIGS.get(model_name, {})

def get_model_paths(model_name: str) -> list:
    """获取指定模型的所有可能路径"""
    config = get_model_config(model_name)
    return config.get('model_paths', [])

def get_online_model(model_name: str) -> str:
    """获取在线模型名称"""
    config = get_model_config(model_name)
    return config.get('online_model', '')

# ==================== 环境变量加载 ====================
def load_env_config():
    """加载环境变量配置"""
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            # 如果没有安装 python-dotenv，跳过环境变量加载
            pass

load_env_config()