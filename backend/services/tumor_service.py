#!/usr/bin/env python3
"""
肿瘤分类服务
基于BERT模型进行肿瘤文本分类
"""

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
import numpy as np
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any
import joblib

sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

class TumorLSTMClassifier(torch.nn.Module):
    """肿瘤分类模型"""
    
    def __init__(self, bert_model_name, lstm_hidden_size=256, num_classes=3):
        super().__init__()
        self.bert = AutoModel.from_pretrained(bert_model_name)
        self.lstm = torch.nn.LSTM(
            input_size=self.bert.config.hidden_size,
            hidden_size=lstm_hidden_size,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        self.classifier = torch.nn.Linear(lstm_hidden_size * 2, num_classes)
        
    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        sequence_output = outputs.last_hidden_state
        lstm_out, _ = self.lstm(sequence_output)
        pooled = lstm_out[:, -1, :]
        logits = self.classifier(pooled)
        return logits

class TumorService:
    """肿瘤分类服务"""
    
    def __init__(self):
        """初始化服务"""
        self.model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.class_names = ['良性', '恶性', '交界性']
        
        try:
            self._load_model()
            logger.info("✅ 肿瘤分类模型加载成功")
        except Exception as e:
            logger.error(f"❌ 肿瘤分类模型加载失败: {e}")
    
    def _load_model(self):
        """加载模型（只允许本地）"""
        bert_dir = Path(__file__).parent.parent / "models" / "tumor_classification_models" / "bert-base-chinese"
        if not bert_dir.exists():
            raise FileNotFoundError("未找到本地BERT模型，请将模型文件放在 backend/models/tumor_classification_models/bert-base-chinese 下")
        logger.info(f"加载BERT模型: {bert_dir}")
        self.tokenizer = AutoTokenizer.from_pretrained(str(bert_dir))
        # 分类权重
        saved_model_path = Path(__file__).parent.parent / "models" / "tumor_classification_models" / "tumor_lstm_model_v3.pth"
        if not saved_model_path.exists():
            raise FileNotFoundError("未找到肿瘤分类模型权重，请将权重文件放在 backend/models/tumor_classification_models/tumor_lstm_model_v3.pth 下")
        logger.info(f"加载分类权重: {saved_model_path}")
        self.model = TumorLSTMClassifier(str(bert_dir), lstm_hidden_size=256, num_classes=3)
        
        # 直接使用普通加载，因为模型文件包含numpy对象
        state_dict = torch.load(saved_model_path, map_location=self.device)
        
        self.model.load_state_dict(state_dict, strict=False)
        self.model = self.model.to(self.device)
        self.model.eval()
    
    def predict(self, text: str) -> Dict[str, Any]:
        """预测肿瘤分类"""
        try:
            if not self.model or not self.tokenizer:
                return {
                    'prediction': '模型未加载',
                    'class': 'unknown',
                    'confidence': 0.0,
                    'error': 'Model not loaded'
                }
            
            # 预处理文本
            if not text.strip():
                return {
                    'prediction': '文本不能为空',
                    'class': 'unknown',
                    'confidence': 0.0,
                    'error': 'Empty text'
                }
            
            # 编码输入
            inputs = self.tokenizer(
                text,
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors="pt"
            ).to(self.device)
            model_inputs = {
                'input_ids': inputs['input_ids'],
                'attention_mask': inputs['attention_mask']
            }
            # 明确只传递这两个参数
            with torch.no_grad():
                outputs = self.model(input_ids=model_inputs['input_ids'], attention_mask=model_inputs['attention_mask'])
                probabilities = F.softmax(outputs, dim=1)
                predicted_class = torch.argmax(probabilities, dim=1).item()
                confidence = probabilities[0][predicted_class].item()
            
            # 获取分类结果
            class_name = self.class_names[predicted_class]
            
            # 生成分析报告和健康建议
            analysis = self._generate_analysis(text, class_name, confidence)
            
            return {
                'prediction': class_name,
                'class': class_name,
                'confidence': confidence,
                'probabilities': {
                    name: float(prob) for name, prob in zip(self.class_names, probabilities[0])
                },
                'input_text': text,
                'recommendations': analysis['recommendations']
            }
            
        except Exception as e:
            logger.error(f"肿瘤分类预测失败: {e}")
            return {
                'prediction': f'预测失败: {str(e)}',
                'class': 'unknown',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _generate_analysis(self, text: str, class_name: str, confidence: float) -> Dict[str, Any]:
        """生成分析报告"""
        analysis = {
            'summary': f'根据提供的病理描述，初步判断为{class_name}肿瘤',
            'confidence_level': '高' if confidence > 0.8 else '中' if confidence > 0.6 else '低',
            'key_features': [],
            'recommendations': []
        }
        
        # 基于分类结果生成建议
        if class_name == '恶性':
            analysis['recommendations'].extend([
                '建议立即进行进一步检查确认',
                '需要制定详细的治疗方案',
                '定期复查监测病情变化',
                '考虑多学科会诊'
            ])
        elif class_name == '良性':
            analysis['recommendations'].extend([
                '建议定期随访观察',
                '保持良好的生活习惯',
                '避免过度担心，保持积极心态'
            ])
        elif class_name == '交界性':
            analysis['recommendations'].extend([
                '需要密切随访观察',
                '考虑手术切除',
                '定期进行影像学检查'
            ])
        else:  # 未确定
            analysis['recommendations'].extend([
                '需要进一步检查明确诊断',
                '建议进行病理活检',
                '可能需要多学科会诊'
            ])
        
        # 基于文本内容提取关键特征
        key_terms = {
            '恶性': ['浸润', '转移', '分化差', '异型性', '核分裂'],
            '良性': ['边界清楚', '包膜完整', '分化好', '生长缓慢'],
            '交界性': ['边界不清', '部分浸润', '中度异型性']
        }
        
        for category, terms in key_terms.items():
            for term in terms:
                if term in text:
                    analysis['key_features'].append(f'发现{term}特征')
        
        return analysis
    
    def batch_predict(self, texts: list) -> list:
        """批量预测"""
        results = []
        for text in texts:
            result = self.predict(text)
            results.append(result)
        return results

if __name__ == "__main__":
    # 测试服务
    service = TumorService()
    
    test_texts = [
        "肿瘤边界清楚，包膜完整，细胞分化良好，未见明显异型性",
        "肿瘤呈浸润性生长，细胞异型性明显，核分裂象多见",
        "肿瘤边界部分不清，细胞中度异型性，未见明显转移"
    ]
    
    for text in test_texts:
        result = service.predict(text)
        print(f"文本: {text}")
        print(f"分类: {result['prediction']}")
        print(f"置信度: {result['confidence']:.3f}")
        print(f"分析: {result['analysis']['summary']}")
        print("-" * 50) 