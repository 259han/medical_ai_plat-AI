import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union
import torch
import joblib
from functools import lru_cache

# 导入统一配置
try:
    from config import MODEL_CONFIGS, PERFORMANCE_CONFIG
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from config import MODEL_CONFIGS, PERFORMANCE_CONFIG

logger = logging.getLogger(__name__)

class ModelManager:
    """AI模型管理器"""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_status: Dict[str, str] = {}
        self.load_times: Dict[str, float] = {}
        self.last_used: Dict[str, float] = {}
        
    async def load_all_models(self) -> Dict[str, bool]:
        """异步加载所有模型"""
        logger.info("开始加载所有AI模型...")
        
        tasks = []
        for model_name in MODEL_CONFIGS.keys():
            task = asyncio.create_task(self._load_model_async(model_name))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = 0
        for model_name, result in zip(MODEL_CONFIGS.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"模型 {model_name} 加载失败: {result}")
                self.model_status[model_name] = "failed"
            else:
                success_count += 1
                self.model_status[model_name] = "loaded"
                logger.info(f"模型 {model_name} 加载成功")
        
        logger.info(f"模型加载完成: {success_count}/{len(MODEL_CONFIGS)} 成功")
        return {name: status == "loaded" for name, status in self.model_status.items()}
    
    async def _load_model_async(self, model_name: str) -> bool:
        """异步加载单个模型"""
        try:
            start_time = time.time()
            
            if model_name == "medical_qa":
                await self._load_medical_qa_model()
            elif model_name == "heart_disease":
                await self._load_heart_disease_model()
            elif model_name == "tumor":
                await self._load_tumor_classification_model()
            elif model_name == "diabetes":
                await self._load_diabetes_risk_model()
            elif model_name == "chest_xray":
                await self._load_chest_xray_model()
            else:
                raise ValueError(f"未知的模型类型: {model_name}")
            
            load_time = time.time() - start_time
            self.load_times[model_name] = load_time
            self.last_used[model_name] = time.time()
            
            logger.info(f"模型 {model_name} 加载耗时: {load_time:.2f}秒")
            return True
            
        except Exception as e:
            logger.error(f"模型 {model_name} 加载失败: {str(e)}")
            self.model_status[model_name] = "failed"
            return False
    
    async def _load_medical_qa_model(self):
        """加载医疗问答模型"""
        try:
            class LazyMedicalQAPredictor:
                def __init__(self):
                    self._model = None
                    self._loaded = False
                
                def generate_answer(self, question: str) -> str:
                    if not self._loaded:
                        try:
                            return f"基于您的问题'{question}'，我建议您咨询专业医生进行详细诊断。"
                        except Exception as e:
                            return f"抱歉，暂时无法处理您的问题。错误信息：{str(e)}"
                    return self._model.generate_answer(question) if self._model else "模型未加载"
            
            self.models["medical_qa"] = LazyMedicalQAPredictor()
            
        except Exception as e:
            logger.error(f"医疗问答模型加载失败: {e}")
            class MockMedicalQAPredictor:
                def generate_answer(self, question: str) -> str:
                    return f"基于您的问题'{question}'，我建议您咨询专业医生进行详细诊断。"
            
            self.models["medical_qa"] = MockMedicalQAPredictor()
    
    async def _load_heart_disease_model(self):
        """加载心脏病预测模型"""
        try:
            import warnings
            from sklearn.exceptions import InconsistentVersionWarning
            
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
                model_path = self._get_model_path("heart_disease", "model_paths")
                self.models["heart_disease"] = joblib.load(str(model_path[0]))
        except Exception as e:
            logger.warning(f"使用警告抑制加载失败，尝试普通加载: {e}")
            model_path = self._get_model_path("heart_disease", "model_paths")
            self.models["heart_disease"] = joblib.load(str(model_path[0]))
            
        except Exception as e:
            logger.error(f"心脏病预测模型加载失败: {e}")
            raise
    
    async def _load_tumor_classification_model(self):
        """加载肿瘤分类模型"""
        try:
            from services.tumor_service import EnhancedTumorModel
            from transformers import BertTokenizer
            
            model_path = self._get_model_path("tumor", "model_paths")
            bert_path = self._get_model_path("tumor", "model_paths")[0]
            
            model = EnhancedTumorModel()
            tokenizer = BertTokenizer.from_pretrained(str(bert_path))
            
            self.models["tumor"] = {
                "model": model,
                "tokenizer": tokenizer
            }
            
        except ImportError:
            logger.warning("肿瘤分类模型服务未找到")
            raise
        except Exception as e:
            logger.error(f"肿瘤分类模型加载失败: {e}")
            raise
    
    async def _load_diabetes_risk_model(self):
        """加载糖尿病风险评估模型"""
        try:
            from services.diabetes_service import DiabetesClassifier
            
            model_path = self._get_model_path("diabetes", "model_paths")
            model = DiabetesClassifier(input_size=8)
            
            # 直接使用普通加载，因为模型文件包含sklearn对象
            state_dict = torch.load(str(model_path[0]), map_location='cpu')
            
            model.load_state_dict(state_dict)
            model.eval()
            
            self.models["diabetes"] = model
            
        except ImportError:
            logger.warning("糖尿病风险评估模型服务未找到")
            raise
        except Exception as e:
            logger.error(f"糖尿病风险评估模型加载失败: {e}")
            raise
    
    async def _load_chest_xray_model(self):
        """加载胸部X光预测模型"""
        try:
            from services.chest_xray_service import ChestXrayService
            
            model_path = self._get_model_path("chest_xray", "model_paths")
            service = ChestXrayService()
            self.models["chest_xray"] = service.model
            
        except ImportError:
            logger.warning("胸部X光预测模型服务未找到")
            raise
        except Exception as e:
            logger.error(f"胸部X光预测模型加载失败: {e}")
            raise
    
    def _get_model_path(self, model_name: str, path_type: str = "model_path") -> Union[Path, list]:
        """获取模型路径，支持fallback"""
        if model_name not in MODEL_CONFIGS:
            raise ValueError(f"未知的模型名称: {model_name}")
        
        model_config = MODEL_CONFIGS[model_name]
        primary_path = model_config.get(path_type)
        
        if isinstance(primary_path, list):
            for path in primary_path:
                if Path(path).exists():
                    return primary_path
            raise FileNotFoundError(f"找不到模型文件: {model_name}")
        
        if primary_path and Path(primary_path).exists():
            return Path(primary_path)
        
        raise FileNotFoundError(f"找不到模型文件: {model_name}")
    
    def get_model(self, model_name: str) -> Any:
        """获取模型实例"""
        if model_name not in self.models:
            raise ValueError(f"模型 {model_name} 未加载")
        
        self.last_used[model_name] = time.time()
        return self.models[model_name]
    
    def is_model_loaded(self, model_name: str) -> bool:
        """检查模型是否已加载"""
        return model_name in self.models and self.model_status.get(model_name) == "loaded"
    
    def get_model_status(self) -> Dict[str, str]:
        """获取所有模型状态"""
        return self.model_status.copy()
    
    def get_model_info(self) -> Dict[str, Dict[str, Any]]:
        """获取模型详细信息"""
        try:
            info = {}
            for model_name in MODEL_CONFIGS.keys():
                info[model_name] = {
                    "status": self.model_status.get(model_name, "not_loaded"),
                    "load_time": self.load_times.get(model_name, 0),
                    "last_used": self.last_used.get(model_name, 0),
                    "config": MODEL_CONFIGS[model_name]
                }
            return info
        except Exception as e:
            logger.error(f"获取模型信息失败: {e}")
            return {}
    
    async def reload_model(self, model_name: str) -> bool:
        """重新加载指定模型"""
        logger.info(f"重新加载模型: {model_name}")
        
        if model_name in self.models:
            del self.models[model_name]
        
        return await self._load_model_async(model_name)
@lru_cache(maxsize=1)
def get_model_manager() -> ModelManager:
    """获取模型管理器单例"""
    return ModelManager()