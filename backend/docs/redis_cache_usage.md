# Redis缓存使用说明

## 概述

医疗AI平台使用Redis作为缓存系统，提供高性能的数据缓存和会话管理功能。

## 缓存配置

### 缓存策略
```python
CACHE_CONFIG = {
    "default_timeout": 300,        # 默认缓存时间：5分钟
    "medical_qa_timeout": 300,     # 医疗问答缓存：5分钟
    "prediction_timeout": 600,     # 预测结果缓存：10分钟
    "user_session_timeout": 3600,  # 用户会话缓存：1小时
    "model_state_timeout": 1800,   # 模型状态缓存：30分钟
}
```

### 连接配置
- **Redis版本**: 6.2.0
- **连接URL**: `redis://localhost:6379`
- **最大连接数**: 50
- **连接超时**: 5秒
- **重试机制**: 支持超时重试

## 缓存功能

### 1. 医疗问答缓存
- **缓存键格式**: `medical_qa:{question_hash}:{user_id}`
- **缓存内容**: 问答结果
- **过期时间**: 5分钟
- **使用场景**: 相同问题的重复查询

### 2. 预测结果缓存
- **缓存键格式**: `prediction:{model_type}:{input_hash}:{user_id}`
- **缓存内容**: AI预测结果
- **过期时间**: 10分钟
- **使用场景**: 相同输入的重复预测

### 3. 胸部X光图像缓存
- **缓存键格式**: `chest_xray:{file_hash}:{cam_method}`
- **缓存内容**: 预测结果和热力图路径
- **过期时间**: 10分钟
- **使用场景**: 相同图片的重复分析

### 4. 用户会话缓存
- **缓存键格式**: `user_session:{user_id}`
- **缓存内容**: 用户会话数据
- **过期时间**: 1小时
- **使用场景**: 用户状态管理

## API接口

### 缓存监控接口

#### 1. 获取缓存统计信息
```http
GET /api/cache/info
Authorization: Bearer {token}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "connected_clients": 5,
        "used_memory_human": "2.5M",
        "total_commands_processed": 1250,
        "keyspace_hits": 890,
        "keyspace_misses": 360,
        "uptime_in_seconds": 86400,
        "db_size": 45
    },
    "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 2. 清除缓存
```http
POST /api/cache/clear
Authorization: Bearer {token}
Content-Type: application/json

{
    "type": "all"  // all, user, medical_qa, prediction
}
```

**响应示例**:
```json
{
    "success": true,
    "message": "清除所有缓存，删除 45 个键",
    "deleted_count": 45,
    "timestamp": "2024-01-01T12:00:00Z"
}
```

#### 3. 获取缓存键列表
```http
GET /api/cache/keys?pattern=medical_qa:*&limit=50
Authorization: Bearer {token}
```

**响应示例**:
```json
{
    "success": true,
    "data": {
        "keys": [
            {
                "key": "medical_qa:abc123:user1",
                "ttl": 180,
                "type": "string"
            }
        ],
        "total": 1,
        "pattern": "medical_qa:*"
    },
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## 使用示例

### 在服务中使用缓存

#### 医疗问答服务
```python
from utils.redis_manager import get_redis_manager

class MedicalQAService:
    def predict(self, question: str, user_id: str = None):
        # 尝试从缓存获取
        redis_mgr = get_redis_manager()
        cached_answer = redis_mgr.get_medical_qa_cache(question, user_id)
        if cached_answer:
            return {'answer': cached_answer, 'cached': True}
        
        # 生成新答案
        answer = self._generate_answer(question)
        
        # 缓存结果
        redis_mgr.cache_medical_qa(question, answer, user_id)
        return {'answer': answer, 'cached': False}
```

#### 胸部X光服务
```python
def predict(self, file, cam_method='gradcam', user_id: str = None):
    # 生成文件哈希
    file_hash = hashlib.md5(file.read()).hexdigest()
    cache_key = f"chest_xray:{file_hash}:{cam_method}"
    
    # 尝试从缓存获取
    cached_result = redis_mgr.get_cache(cache_key)
    if cached_result:
        return cached_result
    
    # 执行预测
    result = self._predict_image(file, cam_method)
    
    # 缓存结果
    redis_mgr.set_cache(cache_key, result, cache_type="prediction")
    return result
```

## 性能优化

### 1. 连接池管理
- 使用连接池减少连接开销
- 自动重连机制
- 健康检查定期执行

### 2. 序列化优化
- 简单数据类型使用JSON序列化
- 复杂对象使用pickle序列化
- 自动选择最优序列化方式

### 3. 键管理
- 长键自动使用MD5哈希
- 键前缀分类管理
- 支持模式匹配删除

### 4. 错误处理
- 优雅降级：缓存失败不影响核心功能
- 详细日志记录
- 异常自动恢复

## 监控指标

### 关键指标
- **缓存命中率**: `keyspace_hits / (keyspace_hits + keyspace_misses)`
- **内存使用**: `used_memory_human`
- **连接数**: `connected_clients`
- **命令处理量**: `total_commands_processed`

### 健康检查
```python
# 检查Redis连接状态
redis_mgr = get_redis_manager()
if redis_mgr.health_check():
    print("Redis连接正常")
else:
    print("Redis连接异常")
```

## 故障排除

### 常见问题

#### 1. 连接失败
```python
# 检查Redis服务状态
redis-cli ping

# 检查连接配置
print(redis_mgr.redis_url)
```

#### 2. 内存不足
```python
# 查看内存使用
redis-cli info memory

# 清除过期键
redis-cli flushdb
```

#### 3. 序列化错误
```python
# 检查数据类型
print(type(data))

# 使用pickle序列化
import pickle
serialized = pickle.dumps(data)
```

## 最佳实践

### 1. 缓存策略
- 合理设置过期时间
- 避免缓存过大的数据
- 定期清理无用缓存

### 2. 键命名
- 使用有意义的键前缀
- 避免键名过长
- 保持键名一致性

### 3. 错误处理
- 始终检查缓存操作结果
- 提供降级方案
- 记录详细错误日志

### 4. 监控告警
- 监控缓存命中率
- 设置内存使用告警
- 监控连接数变化 