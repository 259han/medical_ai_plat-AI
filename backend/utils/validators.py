from typing import Dict, Any, List, Tuple
from fastapi import HTTPException
import numpy as np

def validate_heart_disease_data(data: Dict[str, Any]) -> List[float]:
    """验证心脏病预测数据"""
    required_features = [
        "FastingBloodSugar", "HbA1c", "DietQuality", "SerumCreatinine",
        "MedicalCheckupsFrequency", "BMI", "MedicationAdherence",
        "CholesterolHDL", "CholesterolTriglycerides", "SystolicBP"
    ]
    
    # 检查必需特征
    for feature in required_features:
        if feature not in data:
            raise HTTPException(status_code=400, detail=f"缺少必需特征: {feature}")
    
    # 验证数值范围
    validations = {
        "MedicationAdherence": (0, 10),
        "DietQuality": (1.0, 10.0),
        "HbA1c": (1.0, 10.0),
        "BMI": (10, 70),
        "SystolicBP": (50, 300)
    }
    
    for feature, (min_val, max_val) in validations.items():
        value = data[feature]
        if not isinstance(value, (int, float)) or value < min_val or value > max_val:
            raise HTTPException(
                status_code=400, 
                detail=f"{feature} 必须在 {min_val}-{max_val} 范围内"
            )
    
    return [data[feature] for feature in required_features]

def validate_diabetes_data(data: Dict[str, Any]) -> List[float]:
    """验证糖尿病风险评估数据"""
    required_features = [
        "gender", "age", "hypertension", "heart_disease",
        "smoking_history", "bmi", "HbA1c_level", "blood_glucose_level"
    ]
    
    # 检查必需特征
    for feature in required_features:
        if feature not in data:
            raise HTTPException(status_code=400, detail=f"缺少必需特征: {feature}")
    
    # 验证数值范围
    validations = {
        "gender": (0, 1),
        "age": (10, 120),
        "hypertension": (0, 1),
        "heart_disease": (0, 1),
        "smoking_history": (0, 5),
        "bmi": (10, 70),
        "HbA1c_level": (3.0, 20.0),
        "blood_glucose_level": (50, 300)
    }
    
    for feature, (min_val, max_val) in validations.items():
        value = data[feature]
        if not isinstance(value, (int, float)) or value < min_val or value > max_val:
            raise HTTPException(
                status_code=400, 
                detail=f"{feature} 必须在 {min_val}-{max_val} 范围内"
            )
    
    return [data[feature] for feature in required_features]

def validate_text_input(text: str, max_length: int = 1000) -> str:
    """验证文本输入"""
    if not text or not isinstance(text, str):
        raise HTTPException(status_code=400, detail="文本输入不能为空")
    
    if len(text) > max_length:
        raise HTTPException(status_code=400, detail=f"文本长度不能超过 {max_length} 字符")
    
    return text.strip()

def validate_probability(prob: float) -> float:
    """验证概率值"""
    if not isinstance(prob, (int, float)) or prob < 0 or prob > 1:
        raise HTTPException(status_code=400, detail="概率值必须在 0-1 之间")
    return float(prob)

def validate_model_name(model_name: str) -> str:
    """验证模型名称"""
    valid_models = ["medical_qa", "heart_disease", "tumor_classification", "diabetes_risk"]
    if model_name not in valid_models:
        raise HTTPException(
            status_code=400, 
            detail=f"无效的模型名称。有效选项: {', '.join(valid_models)}"
        )
    return model_name 