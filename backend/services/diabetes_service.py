#!/usr/bin/env python3
"""
糖尿病风险评估服务
基于机器学习模型进行糖尿病风险预测
"""

import torch
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import os

# 字段映射：后端英文字段 -> learn1中文字段
FIELD_MAP = {
    'Sex': '性别',
    'Age': '年龄',
    'Height': '身高(cm)',
    'Weight': '体重(kg)',
    'FastingGlucose': '空腹血糖值(mmol/L)',
    'PostprandialGlucose': '餐后2小时血糖值(mmol/L)',
    'HbA1c': '糖化血红蛋白(%)',
    'TotalCholesterol': '总胆固醇(mmol/L)',
    'Triglycerides': '甘油三酯(mmol/L)',
    'HDL': '高密度脂蛋白(mmol/L)',
    'LDL': '低密度脂蛋白(mmol/L)',
    'UrineAlbumin': '尿微量白蛋白(mg/L)',
    'SystolicBP': '收缩压(mmHg)',
    'DiastolicBP': '舒张压(mmHg)'
}

# 并发症类型映射
COMPLICATION_TYPES = {
    0: "无",
    1: "糖尿病肾病",
    2: "糖尿病视网膜病变",
    3: "糖尿病足",
    4: "糖尿病神经病变",
    5: "糖尿病心血管疾病",
    6: "糖尿病酮症酸中毒"
}

# 医疗建议映射
MEDICAL_ADVICE = {
    "无": "继续保持当前健康管理方案",
    "糖尿病肾病": "建议进行肾功能检查，控制蛋白质摄入",
    "糖尿病视网膜病变": "建议进行眼科检查，控制血糖水平",
    "糖尿病足": "建议进行足部检查，注意足部护理",
    "糖尿病神经病变": "建议进行神经功能检查，控制血糖水平",
    "糖尿病心血管疾病": "建议进行心血管检查，控制血压和血脂",
    "糖尿病酮症酸中毒": "立即就医，监测血糖和酮体水平"
}

logger = logging.getLogger(__name__)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

class OptimizedLSTMModel(torch.nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, num_classes):
        super(OptimizedLSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.lstm = torch.nn.LSTM(input_size, hidden_size, num_layers,
                                  batch_first=True, bidirectional=True, dropout=0.4)
        self.attention = torch.nn.Sequential(
            torch.nn.Linear(hidden_size * 2, hidden_size),
            torch.nn.Tanh(),
            torch.nn.Linear(hidden_size, 1)
        )
        self.fc_complication = torch.nn.Sequential(
            torch.nn.Linear(hidden_size * 2, hidden_size),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.5),
            torch.nn.Linear(hidden_size, num_classes)
        )
        self.fc_days = torch.nn.Sequential(
            torch.nn.Linear(hidden_size * 2, hidden_size),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.5),
            torch.nn.Linear(hidden_size, 1)
        )
        self.fc_prob = torch.nn.Sequential(
            torch.nn.Linear(hidden_size * 2, hidden_size),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.5),
            torch.nn.Linear(hidden_size, 1),
            torch.nn.Sigmoid()
        )
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        attention_weights = torch.softmax(self.attention(lstm_out), dim=1)
        weighted_features = (lstm_out * attention_weights).sum(dim=1)
        complication_pred = self.fc_complication(weighted_features)
        days_pred = self.fc_days(weighted_features)
        prob_pred = self.fc_prob(weighted_features)
        return complication_pred, days_pred, prob_pred

class DiabetesPredictor:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = Path(__file__).parent.parent / "models" / "diabetes_models" / "diabetes_model.pth"
        
        checkpoint = torch.load(model_path, map_location=device, weights_only=False)
        self.model = OptimizedLSTMModel(
            input_size=checkpoint['input_size'],
            hidden_size=checkpoint['hidden_size'],
            num_layers=checkpoint['num_layers'],
            num_classes=checkpoint['num_classes']
        ).to(device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        self.checkpoint = checkpoint
        self.sequence_length = 20
        self.min_days = 7
        self.max_days = 365
    def predict(self, input_data):
        features = self._preprocess_input(input_data)
        input_tensor = torch.FloatTensor(features).unsqueeze(0).to(device)
        with torch.no_grad():
            complication_pred, days_pred, prob_pred = self.model(input_tensor)
            _, complication_idx = torch.max(complication_pred, 1)
            complication = COMPLICATION_TYPES[complication_idx.item()]
            prob = min(max(0.0, prob_pred.item()), 1.0)
            if complication == "无":
                days_display = "不适用"
            else:
                normalized_days = torch.sigmoid(days_pred).item()
                days = self.min_days + (self.max_days - self.min_days) * normalized_days
                days = max(self.min_days, min(self.max_days, round(days)))
                days_display = f"{days}天后"
            return {
                '并发症类型': complication,
                '预计发病天数': days_display,
                '发病概率': f"{prob:.1%}",
                '医疗建议': self._get_medical_advice(complication, prob)
            }
    def _preprocess_input(self, input_data):
        input_df = pd.DataFrame([input_data])
        input_df['性别'] = self.checkpoint['gender_encoder'].transform(input_df['性别'])
        features = self.checkpoint['scaler'].transform(input_df)
        features = np.tile(features, (self.sequence_length, 1))
        return features
    def _get_medical_advice(self, complication, probability):
        base_advice = MEDICAL_ADVICE.get(complication, "请咨询专业医生")
        if complication == "无":
            if probability > 0.3:
                return f"{base_advice}，但未来发病风险较高(概率{probability:.1%})，建议加强监测"
            return base_advice
        else:
            if probability > 0.7:
                urgency = "高"
            elif probability > 0.4:
                urgency = "中"
            else:
                urgency = "低"
            return f"[{urgency}风险] {base_advice} (概率{probability:.1%})"

class DiabetesService:
    """集成LSTM模型的糖尿病预测服务"""
    def __init__(self):
        try:
            self.predictor = DiabetesPredictor()
            logger.info("✅ 糖尿病LSTM模型加载成功")
        except Exception as e:
            logger.error(f"❌ 糖尿病LSTM模型加载失败: {e}")
            self.predictor = None
    def predict(self, data: dict) -> dict:
        if not self.predictor:
            return {'error': '模型未加载'}
        # 字段映射：兼容前端英文字段和learn1中文字段
        mapped = {}
        for k, v in FIELD_MAP.items():
            if k in data:
                mapped[v] = data[k]
        # 允许直接传中文字段
        for v in FIELD_MAP.values():
            if v in data:
                mapped[v] = data[v]
        # 检查必需字段
        required = list(FIELD_MAP.values())
        for f in required:
            if f not in mapped:
                return {'error': f'缺少必要字段: {f}'}
        try:
            result = self.predictor.predict(mapped)
            complication = result.get('并发症类型', '')
            if complication == '无':
                risk_level = 'low'
            else:
                risk_level = 'high'
            result['risk_level'] = risk_level
            result['医疗建议'] = MEDICAL_ADVICE.get(complication, "请咨询专业医生")
            return result
        except Exception as e:
            logger.error(f"推理失败: {e}")
            return {'error': str(e)} 