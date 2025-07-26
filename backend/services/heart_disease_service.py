#!/usr/bin/env python3
"""
心脏病预测服务
仿照 medical_system 方式：只加载一个包含scaler和模型的pkl文件
"""

import joblib
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HeartDiseaseService:
    """心脏病预测服务（仿照 medical_system）"""
    def __init__(self):
        self.model = None
        self.feature_names = None
        try:
            self._load_model()
            logger.info("✅ 心脏病预测模型加载成功")
        except Exception as e:
            logger.error(f"❌ 心脏病预测模型加载失败: {e}")

    def _load_model(self):
        model_path = Path(__file__).parent.parent / "models" / "heart_disease_models" / "heart_disease_model.pkl"
        if not model_path.exists():
            raise FileNotFoundError("未找到心脏病预测模型，请将模型文件放在 backend/models/heart_disease_models/heart_disease_model.pkl 下")
        logger.info(f"加载模型: {model_path}")
        
        try:
            import warnings
            from sklearn.exceptions import InconsistentVersionWarning
            
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
                self.model = joblib.load(model_path)
        except Exception as e:
            logger.warning(f"使用警告抑制加载失败，尝试普通加载: {e}")
            self.model = joblib.load(model_path)
        # 自动获取特征顺序
        if hasattr(self.model, 'feature_names_in_'):
            self.feature_names = list(self.model.feature_names_in_)
        else:
            # 兼容性处理
            self.feature_names = [
                'FastingBloodSugar', 'HbA1c', 'DietQuality', 'SerumCreatinine',
                'MedicalCheckupsFrequency', 'BMI', 'MedicationAdherence',
                'CholesterolHDL', 'CholesterolTriglycerides', 'SystolicBP'
            ]

    def predict(self, data: Dict[str, float]) -> Dict[str, Any]:
        try:
            if not self.model:
                return {
                    'prediction': '模型未加载',
                    'risk_level': 'unknown',
                    'confidence': 0.0,
                    'error': 'Model not loaded'
                }
            # 校验输入
            missing_features = [f for f in self.feature_names if f not in data]
            if missing_features:
                return {
                    'prediction': f'缺少必要特征: {", ".join(missing_features)}',
                    'risk_level': 'unknown',
                    'confidence': 0.0,
                    'error': f'Missing features: {missing_features}'
                }
            validation_errors = self._validate_data(data)
            if validation_errors:
                return {
                    'prediction': f'数据验证失败: {", ".join(validation_errors)}',
                    'risk_level': 'unknown',
                    'confidence': 0.0,
                    'error': f'Validation errors: {validation_errors}'
                }
            # 构造输入
            input_data = np.array([[data[feat] for feat in self.feature_names]])
            pred = self.model.predict(input_data)[0]
            proba = self.model.predict_proba(input_data)[0][1]
            confidence = float(max(self.model.predict_proba(input_data)[0]))
            # 风险等级
            if pred == 1:
                if confidence > 0.4:
                    risk_level = "high"
                elif confidence > 0.2:
                    risk_level = "medium"
                else:
                    risk_level = "medium"
            else:
                if confidence > 0.8:
                    risk_level = "low"
                else:
                    risk_level = "low"
            recommendations = self._generate_recommendations(data, risk_level)
            return {
                'prediction': '有心脏病风险' if pred == 1 else '无心脏病风险',
                'risk_level': risk_level,
                'confidence': confidence,
                'probability': {
                    'no_risk': float(self.model.predict_proba(input_data)[0][0]),
                    'has_risk': float(self.model.predict_proba(input_data)[0][1])
                },
                'recommendations': recommendations,
                'input_features': data
            }
        except Exception as e:
            logger.error(f"心脏病预测失败: {e}")
            return {
                'prediction': f'预测失败: {str(e)}',
                'risk_level': 'unknown',
                'confidence': 0.0,
                'error': str(e)
            }

    def _validate_data(self, data: Dict[str, float]) -> list:
        errors = []
        if not (0 <= data.get('MedicationAdherence', 0) <= 10):
            errors.append("服药依从性必须在0到10之间")
        if not (1.0 <= data.get('DietQuality', 0) <= 10.0):
            errors.append("饮食质量评分必须在1.0到10.0之间")
        if not (1.0 <= data.get('HbA1c', 0) <= 10.0):
            errors.append("糖化血红蛋白应在1.0-10.0%之间")
        if data.get('FastingBloodSugar', 0) < 0:
            errors.append("空腹血糖不能为负数")
        if data.get('SerumCreatinine', 0) < 0:
            errors.append("血清肌酐不能为负数")
        if data.get('MedicalCheckupsFrequency', 0) < 0:
            errors.append("体检次数不能为负数")
        if data.get('BMI', 0) < 10 or data.get('BMI', 0) > 60:
            errors.append("BMI应在10-60之间")
        if data.get('CholesterolHDL', 0) < 0:
            errors.append("HDL胆固醇不能为负数")
        if data.get('CholesterolTriglycerides', 0) < 0:
            errors.append("甘油三酯不能为负数")
        if data.get('SystolicBP', 0) < 70 or data.get('SystolicBP', 0) > 250:
            errors.append("收缩压应在70-250mmHg之间")
        return errors

    def _generate_recommendations(self, data: Dict[str, float], risk_level: str) -> list:
        recommendations = []
        if risk_level in ["高风险", "中高风险"]:
            recommendations.append("建议立即就医，进行详细的心脏检查")
            recommendations.append("定期监测血压、血糖和血脂水平")
        if data.get('BMI', 0) > 30:
            recommendations.append("建议控制体重，BMI过高会增加心脏病风险")
        if data.get('SystolicBP', 0) > 140:
            recommendations.append("血压偏高，建议低盐饮食，规律运动")
        if data.get('FastingBloodSugar', 0) > 126:
            recommendations.append("空腹血糖偏高，建议控制碳水化合物摄入")
        if data.get('CholesterolHDL', 0) < 40:
            recommendations.append("HDL胆固醇偏低，建议增加有氧运动")
        return recommendations
