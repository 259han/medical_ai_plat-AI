import time
import logging
import json
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

try:
    from config import SECURITY_CONFIG, ERROR_CONFIG, BACKEND_CONFIG
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from config import SECURITY_CONFIG, ERROR_CONFIG, BACKEND_CONFIG

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # 记录请求信息
        logger.info(f"请求开始: {request.method} {request.url.path}")
        
        # 处理请求
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                f"请求完成: {request.method} {request.url.path} - "
                f"状态码: {response.status_code} - 耗时: {process_time:.3f}秒"
            )
            
            # 添加响应头
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"请求异常: {request.method} {request.url.path} - "
                f"错误: {str(e)} - 耗时: {process_time:.3f}秒"
            )
            raise

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            # 记录详细的错误信息
            logger.error(
                f"未处理的异常 - 路径: {request.url.path} - 方法: {request.method} - "
                f"客户端: {request.client.host if request.client else 'unknown'} - "
                f"错误: {str(e)}", 
                exc_info=True
            )
            
            # 返回标准错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "error": "内部服务器错误",
                    "message": "服务器处理请求时发生错误",
                    "details": str(e) if ERROR_CONFIG["enable_detailed_errors"] else "请稍后重试",
                    "timestamp": time.time(),
                    "path": request.url.path,
                    "method": request.method
                }
            )

class CORSMiddleware(BaseHTTPMiddleware):
    """CORS中间件"""
    
    def __init__(self, app: ASGIApp, allow_origins: list = None):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 设置CORS头
        origin = request.headers.get("origin")
        if origin in self.allow_origins or "*" in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
        
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
        return response

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(self, app: ASGIApp, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host
        current_time = time.time()
        
        # 清理过期的请求记录
        self._cleanup_old_requests(current_time)
        
        # 检查速率限制
        if client_ip in self.requests:
            if len(self.requests[client_ip]) >= self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "请求过于频繁",
                        "message": f"请等待 {self.window_seconds} 秒后重试",
                        "retry_after": self.window_seconds
                    }
                )
        
        # 记录请求
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)
        
        return await call_next(request)
    
    def _cleanup_old_requests(self, current_time: float):
        """清理过期的请求记录"""
        cutoff_time = current_time - self.window_seconds
        for client_ip in list(self.requests.keys()):
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if req_time > cutoff_time
            ]
            if not self.requests[client_ip]:
                del self.requests[client_ip]

class ModelStatusMiddleware(BaseHTTPMiddleware):
    """模型状态检查中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 检查是否是模型相关的API
        if request.url.path.startswith("/api/"):
            from .model_manager import get_model_manager
            model_manager = get_model_manager()
            
            # 根据路径判断需要的模型
            required_model = self._get_required_model(request.url.path)
            if required_model and not model_manager.is_model_loaded(required_model):
                return JSONResponse(
                    status_code=503,
                    content={
                        "error": "服务不可用",
                        "message": f"模型 {required_model} 未加载或加载失败",
                        "model_status": model_manager.get_model_status()
                    }
                )
        
        return await call_next(request)
    
    def _get_required_model(self, path: str) -> str:
        """根据API路径获取需要的模型"""
        if "/medical_qa/" in path:
            return "medical_qa"
        elif "/heart_disease/" in path:
            return "heart_disease"
        elif "/tumor/" in path:
            return "tumor_classification"
        elif "/diabetes/" in path:
            return "diabetes_risk"
        return None

class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """请求验证中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 验证请求大小
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > SECURITY_CONFIG["max_request_size"]:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "请求过大",
                    "message": f"请求大小不能超过 {SECURITY_CONFIG['max_request_size'] // (1024*1024)}MB"
                }
            )
        
        return await call_next(request) 