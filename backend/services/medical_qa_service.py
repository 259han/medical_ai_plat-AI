#!/usr/bin/env python3
"""
医疗问答服务
基于Qwen模型进行医疗问题回答
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
import os
import sys
from pathlib import Path
import json
import numpy as np
from typing import Dict, Any

sys.path.append(str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

class MedicalQAService:
    """医疗问答服务"""
    
    def __init__(self):
        """初始化服务"""
        self.model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        try:
            self._load_model()
            logger.info("✅ 医疗问答模型加载成功")
        except Exception as e:
            logger.error(f"❌ 医疗问答模型加载失败: {e}")
    
    def _load_model(self):
        """加载模型（只允许本地）"""
        model_dir1 = Path(__file__).parent.parent / "models" / "medical_qa_models" / "qwen_medical_finetuned"
        model_dir2 = Path(__file__).parent.parent / "models" / "medical_qa_models" / "Qwen1.5-0.5B"
        if model_dir1.exists():
            model_path = str(model_dir1)
        elif model_dir2.exists():
            model_path = str(model_dir2)
        else:
            raise FileNotFoundError("未找到本地医疗问答模型，请将模型文件放在 backend/models/medical_qa_models/qwen_medical_finetuned 或 Qwen1.5-0.5B 下")
        logger.info(f"加载模型: {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True,
            padding_side='left'
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True
        )
        if not torch.cuda.is_available():
            self.model = self.model.to(self.device)
        self.model.eval()
    
    def predict(self, question: str, user_id: str = None) -> Dict[str, Any]:
        """预测医疗问题答案"""
        try:
            # 尝试从缓存获取结果
            from utils.redis_manager import get_redis_manager
            redis_mgr = get_redis_manager()
            cached_answer = redis_mgr.get_medical_qa_cache(question, user_id)
            if cached_answer:
                logger.info(f"✅ 医疗问答缓存命中: {question[:50]}...")
                return {
                    'answer': cached_answer,
                    'confidence': 0.9,
                    'cached': True
                }
            
            if not self.model or not self.tokenizer:
                return {
                    'answer': '模型未加载，请检查模型文件',
                    'confidence': 0.0,
                    'error': 'Model not loaded'
                }
            
            # 构建提示词
            prompt = f"""请回答以下医疗问题，请用专业但易懂的语言回答：

问题：{question}

回答："""
            
            # 编码输入
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)
            
            # 生成回答
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=512,
                    temperature=0.7,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # 解码输出
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 提取回答部分
            answer = generated_text[len(prompt):].strip()
            
            # 计算置信度（基于生成文本的长度和质量）
            confidence = min(0.9, len(answer) / 100.0 + 0.1)
            
            # 缓存结果
            try:
                redis_mgr.cache_medical_qa(question, answer, user_id)
                logger.info(f"✅ 医疗问答结果已缓存: {question[:50]}...")
            except Exception as e:
                logger.warning(f"缓存医疗问答结果失败: {e}")
            
            return {
                'answer': answer,
                'confidence': confidence,
                'question': question,
                'cached': False,
                'model_info': {
                    'model_name': 'Qwen Medical QA',
                    'device': str(self.device)
                }
            }
            
        except Exception as e:
            logger.error(f"医疗问答预测失败: {e}")
            return {
                'answer': f'抱歉，处理您的问题时出现错误：{str(e)}',
                'confidence': 0.0,
                'error': str(e)
            }
    
    def batch_predict(self, questions: list) -> list:
        """批量预测"""
        results = []
        for question in questions:
            result = self.predict(question)
            results.append(result)
        return results

if __name__ == "__main__":
    # 测试服务
    service = MedicalQAService()
    
    test_questions = [
        "什么是高血压？",
        "糖尿病的早期症状有哪些？",
        "如何预防心脏病？"
    ]
    
    for question in test_questions:
        result = service.predict(question)
        print(f"问题: {question}")
        print(f"回答: {result['answer']}")
        print(f"置信度: {result['confidence']}")
        print("-" * 50)
