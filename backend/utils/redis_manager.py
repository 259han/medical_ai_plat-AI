#!/usr/bin/env python3
"""
Redis缓存管理器
提供统一的缓存操作接口，支持医疗AI平台的缓存需求
"""

import redis
import json
import logging
import pickle
import hashlib
from typing import Any, Optional, Dict, Union
from datetime import timedelta
import os

logger = logging.getLogger(__name__)

class RedisManager:
    """Redis缓存管理器"""
    
    def __init__(self, redis_url: str = None, max_connections: int = 50):
        """
        初始化Redis管理器
        
        Args:
            redis_url: Redis连接URL，默认为环境变量或本地连接b
            max_connections: 最大连接数
        """
        self.redis_url = redis_url or os.environ.get('REDIS_URL', 'redis://localhost:6379')
        self.max_connections = max_connections
        self.redis_client = None
        self._connect()
        
        # 缓存配置
        self.cache_config = {
            "default_timeout": 300,  # 5分钟
            "medical_qa_timeout": 300,  # 医疗问答缓存5分钟
            "prediction_timeout": 600,  # 预测结果缓存10分钟
            "user_session_timeout": 3600,  # 用户会话缓存1小时
            "model_state_timeout": 1800,  # 模型状态缓存30分钟
        }
    
    def _connect(self):
        """建立Redis连接"""
        try:
            # 创建连接池
            self.redis_client = redis.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=False,  # 保持二进制模式以支持pickle
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # 测试连接
            self.redis_client.ping()
            logger.info(f"✅ Redis连接成功: {self.redis_url}")
            
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis连接失败: {e}")
            self.redis_client = None
        except Exception as e:
            logger.error(f"❌ Redis初始化错误: {e}")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, *args) -> str:
        """
        生成缓存键
        
        Args:
            prefix: 键前缀
            *args: 键组成部分
            
        Returns:
            生成的缓存键
        """
        # 将所有参数转换为字符串并连接
        key_parts = [str(arg) for arg in args]
        key_string = f"{prefix}:{':'.join(key_parts)}"
        
        # 如果键太长，使用MD5哈希
        if len(key_string) > 250:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:{key_hash}"
        
        return key_string
    
    def _serialize_data(self, data: Any) -> bytes:
        """
        序列化数据
        
        Args:
            data: 要序列化的数据
            
        Returns:
            序列化后的字节数据
        """
        try:
            # 尝试JSON序列化
            if isinstance(data, (dict, list, str, int, float, bool)) or data is None:
                return json.dumps(data, ensure_ascii=False).encode('utf-8')
            else:
                # 使用pickle序列化复杂对象
                return pickle.dumps(data)
        except Exception as e:
            logger.warning(f"序列化失败，使用pickle: {e}")
            return pickle.dumps(data)
    
    def _deserialize_data(self, data: bytes) -> Any:
        """
        反序列化数据
        
        Args:
            data: 序列化的字节数据
            
        Returns:
            反序列化后的数据
        """
        if data is None:
            return None
            
        try:
            # 尝试JSON反序列化
            json_str = data.decode('utf-8')
            return json.loads(json_str)
        except (UnicodeDecodeError, json.JSONDecodeError):
            try:
                # 使用pickle反序列化
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"反序列化失败: {e}")
                return None
    
    def get_cache(self, key: str) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的数据，如果不存在返回None
        """
        if not self.redis_client:
            return None
            
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                logger.debug(f"缓存命中: {key}")
                return self._deserialize_data(cached_data)
            else:
                logger.debug(f"缓存未命中: {key}")
                return None
        except Exception as e:
            logger.warning(f"获取缓存失败: {key}, 错误: {e}")
            return None
    
    def set_cache(self, key: str, data: Any, timeout: int = None, cache_type: str = "default") -> bool:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            data: 要缓存的数据
            timeout: 过期时间（秒），None使用默认配置
            cache_type: 缓存类型，用于确定默认过期时间
            
        Returns:
            是否设置成功
        """
        if not self.redis_client:
            return False
            
        try:
            # 确定过期时间
            if timeout is None:
                timeout = self.cache_config.get(f"{cache_type}_timeout", self.cache_config["default_timeout"])
            
            # 序列化数据
            serialized_data = self._serialize_data(data)
            
            # 设置缓存
            result = self.redis_client.setex(key, timeout, serialized_data)
            
            if result:
                logger.debug(f"缓存设置成功: {key}, 过期时间: {timeout}秒")
            else:
                logger.warning(f"缓存设置失败: {key}")
                
            return result
            
        except Exception as e:
            logger.error(f"设置缓存失败: {key}, 错误: {e}")
            return False
    
    def delete_cache(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        if not self.redis_client:
            return False
            
        try:
            result = self.redis_client.delete(key)
            if result:
                logger.debug(f"缓存删除成功: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"删除缓存失败: {key}, 错误: {e}")
            return False
    
    def clear_cache_by_pattern(self, pattern: str) -> int:
        """
        按模式清除缓存
        
        Args:
            pattern: 键模式，支持通配符
            
        Returns:
            删除的键数量
        """
        if not self.redis_client:
            return 0
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"清除缓存模式 {pattern}: 删除 {deleted} 个键")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"清除缓存模式失败: {pattern}, 错误: {e}")
            return 0
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        if not self.redis_client:
            return {"error": "Redis未连接"}
            
        try:
            info = self.redis_client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                "db_size": self.redis_client.dbsize()
            }
        except Exception as e:
            logger.error(f"获取缓存信息失败: {e}")
            return {"error": str(e)}
    
    # 特定业务缓存方法
    
    def cache_medical_qa(self, question: str, answer: str, user_id: str = None) -> bool:
        """
        缓存医疗问答结果
        
        Args:
            question: 问题
            answer: 答案
            user_id: 用户ID（可选）
            
        Returns:
            是否缓存成功
        """
        key = self._generate_key("medical_qa", question, user_id or "anonymous")
        return self.set_cache(key, answer, cache_type="medical_qa")
    
    def get_medical_qa_cache(self, question: str, user_id: str = None) -> Optional[str]:
        """
        获取医疗问答缓存
        
        Args:
            question: 问题
            user_id: 用户ID（可选）
            
        Returns:
            缓存的答案
        """
        key = self._generate_key("medical_qa", question, user_id or "anonymous")
        return self.get_cache(key)
    
    def cache_prediction_result(self, model_type: str, input_data: str, result: Dict, user_id: str = None) -> bool:
        """
        缓存预测结果
        
        Args:
            model_type: 模型类型
            input_data: 输入数据
            result: 预测结果
            user_id: 用户ID（可选）
            
        Returns:
            是否缓存成功
        """
        key = self._generate_key("prediction", model_type, input_data, user_id or "anonymous")
        return self.set_cache(key, result, cache_type="prediction")
    
    def get_prediction_cache(self, model_type: str, input_data: str, user_id: str = None) -> Optional[Dict]:
        """
        获取预测结果缓存
        
        Args:
            model_type: 模型类型
            input_data: 输入数据
            user_id: 用户ID（可选）
            
        Returns:
            缓存的预测结果
        """
        key = self._generate_key("prediction", model_type, input_data, user_id or "anonymous")
        return self.get_cache(key)
    
    def cache_user_session(self, user_id: str, session_data: Dict) -> bool:
        """
        缓存用户会话数据
        
        Args:
            user_id: 用户ID
            session_data: 会话数据
            
        Returns:
            是否缓存成功
        """
        key = self._generate_key("user_session", user_id)
        return self.set_cache(key, session_data, cache_type="user_session")
    
    def get_user_session_cache(self, user_id: str) -> Optional[Dict]:
        """
        获取用户会话缓存
        
        Args:
            user_id: 用户ID
            
        Returns:
            缓存的会话数据
        """
        key = self._generate_key("user_session", user_id)
        return self.get_cache(key)
    
    def clear_user_cache(self, user_id: str) -> int:
        """
        清除用户相关缓存
        
        Args:
            user_id: 用户ID
            
        Returns:
            删除的键数量
        """
        pattern = f"*:{user_id}"
        return self.clear_cache_by_pattern(pattern)
    
    def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            Redis是否健康
        """
        if not self.redis_client:
            return False
            
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis健康检查失败: {e}")
            return False
    
    def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis连接已关闭")
            except Exception as e:
                logger.error(f"关闭Redis连接失败: {e}")

# 全局Redis管理器实例
redis_manager = RedisManager()

def get_redis_manager() -> RedisManager:
    """获取Redis管理器实例"""
    return redis_manager 