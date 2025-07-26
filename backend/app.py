#!/usr/bin/env python3
"""
医疗AI平台后端主应用
基于Flask + Redis + MySQL架构
"""

from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import redis
import logging
import os
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
import hashlib
import jwt
from functools import wraps
import pymysql
pymysql.install_as_MySQLdb()
from sqlalchemy import text
from config import Config

sys.path.append(str(Path(__file__).parent.parent))

# 导入AI模型服务
try:
    from services.medical_qa_service import MedicalQAService
    from services.heart_disease_service import HeartDiseaseService
    from services.tumor_service import TumorService
    from services.diabetes_service import DiabetesService
    from services.chest_xray_service import ChestXrayService
    from services.report_export_service import ReportExportService
    from utils.redis_manager import get_redis_manager
except ImportError as e:
    print(f"导入AI服务失败: {e}")
    sys.exit(1)

# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 加载配置
from config import get_config
app.config.update(get_config()().__dict__)

# 初始化扩展
CORS(app, supports_credentials=True, origins=Config.CORS_ORIGINS)
db = SQLAlchemy(app)
Session(app)

# 初始化Redis管理器
redis_manager = get_redis_manager()

# 配置日志
logging.basicConfig(
    level=getattr(logging, app.config['LOG_LEVEL']),
    format=app.config['LOG_FORMAT'],
    handlers=[
        logging.FileHandler(app.config['LOG_FILE']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 抑制预期的警告
import warnings
from sklearn.exceptions import InconsistentVersionWarning
warnings.filterwarnings("ignore", message=".*weights_only.*")
warnings.filterwarnings("ignore", message=".*WeightsUnpickler.*")
warnings.filterwarnings("ignore", message=".*torch.load.*weights_only=False.*")
warnings.filterwarnings("ignore", category=FutureWarning, message=".*torch.load.*")
warnings.filterwarnings("ignore", category=InconsistentVersionWarning)

# 数据模型
class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # user, doctor, admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class PredictionRecord(db.Model):
    """预测记录模型"""
    __tablename__ = 'prediction_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)  # medical_qa, heart_disease, tumor, diabetes, chest_xray
    input_data = db.Column(db.Text, nullable=False)  # JSON格式的输入数据
    prediction_result = db.Column(db.Text, nullable=False)  # JSON格式的预测结果
    confidence_score = db.Column(db.Float)
    risk_level = db.Column(db.String(20), nullable=True)  # high, medium, low, info
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('predictions', lazy=True))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 自动计算风险等级
        if self.prediction_result and not self.risk_level:
            try:
                result_data = json.loads(self.prediction_result)
                self.risk_level = get_risk_level(self.model_type, result_data)
            except:
                self.risk_level = 'info'

# 初始化AI服务
try:
    medical_qa_service = MedicalQAService()
    heart_disease_service = HeartDiseaseService()
    tumor_service = TumorService()
    diabetes_service = DiabetesService()
    # 传递Config类实例而不是app.config字典
    from config import Config
    config_instance = Config()
    chest_xray_service = ChestXrayService(config_instance)
    logger.info("✅ AI服务初始化成功")
except Exception as e:
    logger.error(f"❌ AI服务初始化失败: {e}")
    sys.exit(1)

# 认证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': '缺少认证令牌'}), 401
        
        try:
            token = token.split(' ')[1]  # Bearer token
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['user_id']
            user = db.session.get(User, user_id)
            if not user or not user.is_active:
                return jsonify({'error': '用户不存在或已禁用'}), 401
            request.current_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '无效令牌'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


# 健康检查
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        # 检查数据库连接
        db.session.execute(text('SELECT 1'))
        
        # 检查Redis连接
        redis_status = redis_manager.health_check() if redis_manager else False
        
        # 检查AI服务状态
        services_status = {
            'medical_qa': hasattr(medical_qa_service, 'model') and medical_qa_service.model is not None,
            'heart_disease': hasattr(heart_disease_service, 'model') and heart_disease_service.model is not None,
            'tumor': hasattr(tumor_service, 'model') and tumor_service.model is not None,
            'diabetes': hasattr(diabetes_service, 'model') and diabetes_service.model is not None,
            'chest_xray': hasattr(chest_xray_service, 'model') and chest_xray_service.model is not None
        }
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': services_status,
            'database': 'connected',
            'redis': 'connected' if redis_status else 'disconnected'
        })
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# 缓存监控和管理接口
@app.route('/api/cache/info', methods=['GET'])
@login_required
def get_cache_info():
    """获取缓存统计信息"""
    try:
        if not redis_manager:
            return jsonify({'error': 'Redis未配置'}), 503
        
        cache_info = redis_manager.get_cache_info()
        return jsonify({
            'success': True,
            'data': cache_info,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"获取缓存信息失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
@login_required
def clear_cache():
    """清除缓存"""
    try:
        if not redis_manager:
            return jsonify({'error': 'Redis未配置'}), 503
        
        data = request.get_json() or {}
        cache_type = data.get('type', 'all')  # all, user, medical_qa, prediction
        
        if cache_type == 'all':
            # 清除所有缓存
            deleted = redis_manager.clear_cache_by_pattern('*')
            message = f"清除所有缓存，删除 {deleted} 个键"
        elif cache_type == 'user':
            # 清除当前用户缓存
            user_id = request.current_user.id
            deleted = redis_manager.clear_user_cache(str(user_id))
            message = f"清除用户缓存，删除 {deleted} 个键"
        elif cache_type == 'medical_qa':
            # 清除医疗问答缓存
            deleted = redis_manager.clear_cache_by_pattern('medical_qa:*')
            message = f"清除医疗问答缓存，删除 {deleted} 个键"
        elif cache_type == 'prediction':
            # 清除预测结果缓存
            deleted = redis_manager.clear_cache_by_pattern('prediction:*')
            message = f"清除预测结果缓存，删除 {deleted} 个键"
        else:
            return jsonify({'error': '无效的缓存类型'}), 400
        
        return jsonify({
            'success': True,
            'message': message,
            'deleted_count': deleted,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/keys', methods=['GET'])
@login_required
def get_cache_keys():
    """获取缓存键列表"""
    try:
        if not redis_manager:
            return jsonify({'error': 'Redis未配置'}), 503
        
        pattern = request.args.get('pattern', '*')
        limit = min(int(request.args.get('limit', 100)), 1000)  # 限制最大返回数量
        
        # 获取匹配的键
        keys = redis_manager.redis_client.keys(pattern)[:limit]
        
        # 获取键的详细信息
        key_info = []
        for key in keys:
            try:
                ttl = redis_manager.redis_client.ttl(key)
                key_info.append({
                    'key': key.decode('utf-8') if isinstance(key, bytes) else key,
                    'ttl': ttl if ttl > 0 else -1,  # -1表示永不过期
                    'type': redis_manager.redis_client.type(key).decode('utf-8')
                })
            except Exception as e:
                logger.warning(f"获取键信息失败: {key}, 错误: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'keys': key_info,
                'total': len(key_info),
                'pattern': pattern
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"获取缓存键失败: {e}")
        return jsonify({'error': str(e)}), 500

# 用户认证接口
@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'error': '缺少必要字段'}), 400
        
        # 密码长度校验
        if len(password) <= 6:
            return jsonify({'error': '密码长度必须大于6位'}), 400
        
        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'error': '用户名已存在'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': '邮箱已存在'}), 400
        
        # 创建新用户
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = User(username=username, email=email, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()
        
        # 生成JWT令牌
        token = jwt.encode(
            {
                'user_id': user.id,
                'username': user.username,
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        return jsonify({
            'message': '注册成功',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        })
    except Exception as e:
        logger.error(f"注册失败: {e}")
        db.session.rollback()
        return jsonify({'error': '注册失败'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({'error': '缺少用户名或密码'}), 400
        
        # 查找用户
        user = User.query.filter_by(username=username).first()
        if not user or user.password_hash != hashlib.sha256(password.encode()).hexdigest():
            return jsonify({'error': '用户名或密码错误'}), 401
        
        if not user.is_active:
            return jsonify({'error': '账户已被禁用'}), 401
        
        # 生成JWT令牌
        token = jwt.encode(
            {
                'user_id': user.id,
                'username': user.username,
                'exp': datetime.utcnow() + timedelta(hours=24)
            },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        return jsonify({
            'message': '登录成功',
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        })
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return jsonify({'error': '登录失败'}), 500

# AI预测接口
@app.route('/api/medical_qa', methods=['POST'])
@login_required
def medical_qa():
    """医疗问答接口"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': '问题不能为空'}), 400
        
        # 调用医疗问答服务（传递用户ID以支持缓存）
        user_id = str(request.current_user.id)
        result = medical_qa_service.predict(question, user_id)
        
        # 保存预测记录
        record = PredictionRecord(
            user_id=request.current_user.id,
            model_type='medical_qa',
            input_data=json.dumps({'question': question}),
            prediction_result=json.dumps(result),
            confidence_score=result.get('confidence', 0.0)
        )
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': result,
            'message': '医疗问答完成'
        })
    except Exception as e:
        logger.error(f"医疗问答失败: {e}")
        db.session.rollback()
        return jsonify({'error': '预测失败', 'detail': str(e)}), 500

@app.route('/api/heart_disease', methods=['POST'])
@login_required
def heart_disease():
    """心脏病预测接口"""
    try:
        data = request.get_json()
        
        # 调用AI服务
        result = heart_disease_service.predict(data)
        logger.info(f"心脏病AI返回: {result}")
        logger.info(f"心脏病AI返回confidence: {result.get('confidence')}")
        
        # 保存预测记录
        record = PredictionRecord(
            user_id=request.current_user.id,
            model_type='heart_disease',
            input_data=json.dumps(data),
            prediction_result=json.dumps(result),
            confidence_score=result.get('confidence', 0.0)
        )
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': result,
            'message': '心脏病预测完成'
        })
    except Exception as e:
        logger.error(f"心脏病预测失败: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': '预测失败',
            'detail': str(e)
        }), 500

@app.route('/api/tumor', methods=['POST'])
@login_required
def tumor():
    """肿瘤分类接口"""
    try:
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({'error': '文本不能为空'}), 400
        
        # 调用AI服务
        result = tumor_service.predict(text)
        
        # 保存预测记录
        record = PredictionRecord(
            user_id=request.current_user.id,
            model_type='tumor',
            input_data=json.dumps({'text': text}),
            prediction_result=json.dumps(result),
            confidence_score=result.get('confidence', 0.0)
        )
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': result,
            'message': '肿瘤分类完成'
        })
    except Exception as e:
        logger.error(f"肿瘤分类失败: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': '预测失败',
            'detail': str(e)
        }), 500

@app.route('/api/diabetes', methods=['POST'])
@login_required
def diabetes():
    """糖尿病风险评估接口"""
    try:
        data = request.get_json()
        
        # 调用AI服务
        result = diabetes_service.predict(data)
        
        # 保存预测记录
        record = PredictionRecord(
            user_id=request.current_user.id,
            model_type='diabetes',
            input_data=json.dumps(data),
            prediction_result=json.dumps(result),
            confidence_score=result.get('confidence', 0.0)
        )
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': result,
            'message': '糖尿病风险评估完成'
        })
    except Exception as e:
        logger.error(f"糖尿病风险评估失败: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': '预测失败',
            'detail': str(e)
        }), 500

@app.route('/api/chest_xray', methods=['POST'])
@login_required
def chest_xray():
    """胸部X光预测接口"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '未上传文件'}), 400
        file = request.files['file']
        cam_method = request.form.get('cam_method', 'gradcam').lower()
        if cam_method not in ['gradcam', 'gradcam++', 'scorecam']:
            return jsonify({'error': '无效的CAM方法'}), 400
        
        # 调用AI服务（传递用户ID以支持缓存）
        user_id = str(request.current_user.id)
        result = chest_xray_service.predict(file, cam_method, user_id)
        
        # 保存预测记录
        record = PredictionRecord(
            user_id=request.current_user.id,
            model_type='chest_xray',
            input_data=json.dumps({'filename': file.filename, 'cam_method': cam_method}),
            prediction_result=json.dumps(result),
            confidence_score=max([v['probability'] for v in result['predictions'].values()])
        )
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': result,
            'message': '胸部X光预测完成'
        })
    except Exception as e:
        logger.error(f"胸部X光预测失败: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': '预测失败',
            'detail': str(e)
        }), 500

@app.route('/api/chest_xray/image', methods=['GET'])
@login_required
def get_chest_xray_image():
    """获取生成的X光热力图图片"""
    try:
        image_path = request.args.get('path')
        if not image_path:
            return jsonify({'error': '缺少图片路径'}), 400
        
        # 记录调试信息
        logger.info(f"请求图片路径: {image_path}")
        
        # 直接使用文件名
        full_path = chest_xray_service.get_image(image_path)
        
        # 记录调试信息
        logger.info(f"完整图片路径: {full_path}")
        
        if not os.path.exists(full_path):
            logger.error(f"图片文件不存在: {full_path}")
            return jsonify({'error': '图片文件不存在'}), 404
            
        response = send_file(full_path, mimetype='image/png')
        # 添加CORS头部
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    except Exception as e:
        logger.error(f"获取X光图片失败: {e}")
        return jsonify({'error': '图片获取失败', 'detail': str(e)}), 404

# 用户数据接口
@app.route('/api/user/profile', methods=['GET'])
@login_required
def get_profile():
    """获取用户信息"""
    user = request.current_user
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'created_at': user.created_at.isoformat()
    })

@app.route('/api/user/predictions', methods=['GET'])
@login_required
def get_predictions():
    """获取用户预测记录"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        model_type = request.args.get('model_type')
        
        query = PredictionRecord.query.filter_by(user_id=request.current_user.id)
        if model_type:
            query = query.filter_by(model_type=model_type)
        
        records = query.order_by(PredictionRecord.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'records': [{
                'id': record.id,
                'model_type': record.model_type,
                'input_data': json.loads(record.input_data),
                'prediction_result': json.loads(record.prediction_result),
                'confidence_score': record.confidence_score,
                'created_at': record.created_at.isoformat()
            } for record in records.items],
            'total': records.total,
            'pages': records.pages,
            'current_page': page
        })
    except Exception as e:
        logger.error(f"获取预测记录失败: {e}")
        return jsonify({'error': '获取记录失败', 'detail': str(e)}), 500

@app.route('/api/user/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新用户资料"""
    try:
        data = request.get_json()
        user = request.current_user
        
        # 更新用户信息
        if 'username' in data and data['username'] != user.username:
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': '用户名已存在'}), 400
            user.username = data['username']
        
        if 'email' in data and data['email'] != user.email:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': '邮箱已存在'}), 400
            user.email = data['email']
        
        db.session.commit()
        
        return jsonify({
            'message': '资料更新成功',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'created_at': user.created_at.isoformat()
            }
        })
    except Exception as e:
        logger.error(f"更新用户资料失败: {e}")
        db.session.rollback()
        return jsonify({'error': '更新失败', 'detail': str(e)}), 500

@app.route('/api/user/password', methods=['PUT'])
@login_required
def change_password():
    """修改密码"""
    try:
        data = request.get_json()
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        
        if not current_password or not new_password:
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 新密码长度校验
        if len(new_password) <= 6:
            return jsonify({'error': '新密码长度必须大于6位'}), 400
        
        user = request.current_user
        
        # 验证当前密码
        current_hash = hashlib.sha256(current_password.encode()).hexdigest()
        if current_hash != user.password_hash:
            return jsonify({'error': '当前密码错误'}), 400
        
        # 更新密码
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        user.password_hash = new_hash
        db.session.commit()
        
        return jsonify({'message': '密码修改成功'})
    except Exception as e:
        logger.error(f"修改密码失败: {e}")
        db.session.rollback()
        return jsonify({'error': '修改失败', 'detail': str(e)}), 500

@app.route('/api/user/history/<int:record_id>', methods=['DELETE'])
@login_required
def delete_history_record(record_id):
    """删除历史记录"""
    try:
        record = PredictionRecord.query.filter_by(
            id=record_id,
            user_id=request.current_user.id
        ).first()
        
        if not record:
            return jsonify({'error': '记录不存在或无权限删除'}), 404
        
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({'message': '记录删除成功'})
    except Exception as e:
        logger.error(f"删除历史记录失败: {e}")
        db.session.rollback()
        return jsonify({'error': '删除失败', 'detail': str(e)}), 500

@app.route('/api/user/history/all', methods=['DELETE'])
@login_required
def delete_all_history_records():
    """删除用户所有历史记录"""
    try:
        # 获取用户的所有历史记录
        records = PredictionRecord.query.filter_by(
            user_id=request.current_user.id
        ).all()
        
        if not records:
            return jsonify({'message': '没有历史记录需要删除'})
        
        # 删除所有记录
        for record in records:
            db.session.delete(record)
        
        db.session.commit()
        
        deleted_count = len(records)
        logger.info(f"用户 {request.current_user.id} 删除了 {deleted_count} 条历史记录")
        
        return jsonify({
            'message': f'成功删除 {deleted_count} 条历史记录',
            'deleted_count': deleted_count
        })
    except Exception as e:
        logger.error(f"删除所有历史记录失败: {e}")
        db.session.rollback()
        return jsonify({'error': '删除失败', 'detail': str(e)}), 500

# 统计接口
@app.route('/api/stats/overview', methods=['GET'])
@login_required
def get_stats():
    """获取统计信息"""
    try:
        total_predictions = PredictionRecord.query.filter_by(
            user_id=request.current_user.id
        ).count()
        
        model_stats = db.session.query(
            PredictionRecord.model_type,
            db.func.count(PredictionRecord.id).label('count')
        ).filter_by(user_id=request.current_user.id).group_by(
            PredictionRecord.model_type
        ).all()
        
        return jsonify({
            'total_predictions': total_predictions,
            'model_stats': {stat.model_type: stat.count for stat in model_stats}
        })
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({'error': '获取统计失败', 'detail': str(e)}), 500

@app.route('/api/user/stats', methods=['GET'])
@login_required
def get_user_stats():
    """获取用户统计信息"""
    try:
        from services.history_search_service import HistorySearchService
        
        # 创建搜索服务实例
        search_service = HistorySearchService(db.session, request.current_user.id, PredictionRecord)
        
        # 获取搜索统计信息
        stats = search_service.get_search_statistics()
        
        # 添加最近7天的预测数量
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_predictions = PredictionRecord.query.filter(
            PredictionRecord.user_id == request.current_user.id,
            PredictionRecord.created_at >= seven_days_ago
        ).count()
        
        stats['recent_predictions'] = recent_predictions
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"获取用户统计信息失败: {e}")
        return jsonify({'error': '获取统计失败', 'detail': str(e)}), 500

@app.route('/api/test/risk_level', methods=['POST'])
def test_risk_level():
    """测试风险等级判断逻辑"""
    try:
        data = request.get_json()
        model_type = data.get('model_type')
        prediction_result = data.get('prediction_result')
        
        risk_level = get_risk_level(model_type, prediction_result)
        
        return jsonify({
            'model_type': model_type,
            'prediction_result': prediction_result,
            'risk_level': risk_level
        })
    except Exception as e:
        logger.error(f"测试风险等级判断失败: {e}")
        return jsonify({'error': '测试失败', 'detail': str(e)}), 500

@app.route('/api/user/history', methods=['GET'])
@login_required
def get_user_history():
    """获取用户历史记录"""
    try:
        from services.history_search_service import HistorySearchService
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        model_type = request.args.get('type', '')
        risk_level = request.args.get('result', '')
        date_range = request.args.get('dateRange', '')
        keyword = request.args.get('keyword', '')
        
        # 记录搜索参数
        logger.info(f"搜索历史记录 - 用户ID: {request.current_user.id}, 关键词: '{keyword}', 模型类型: '{model_type}', 风险等级: '{risk_level}', 日期范围: '{date_range}'")
        
        # 创建搜索服务实例
        search_service = HistorySearchService(db.session, request.current_user.id, PredictionRecord)
        
        # 执行搜索
        result = search_service.search_records(
            page=page,
            per_page=per_page,
            model_type=model_type,
            risk_level=risk_level,
            date_range=date_range,
            keyword=keyword
        )
        
        logger.info(f"搜索完成 - 找到 {result['total']} 条记录")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取用户历史记录失败: {e}")
        return jsonify({'error': '获取历史记录失败', 'detail': str(e)}), 500

@app.route('/api/user/report/export', methods=['POST'])
@login_required
def export_report():
    """导出报告"""
    try:
        logger.info(f"开始导出报告 - 用户ID: {request.current_user.id}")
        data = request.get_json()
        record_id = data.get('record_id')
        export_format = data.get('format', 'pdf').lower()
        template_name = data.get('template')
        
        logger.info(f"导出参数 - 记录ID: {record_id}, 格式: {export_format}, 模板: {template_name}")
        
        if not record_id:
            return jsonify({'error': '缺少记录ID'}), 400
        
        # 获取记录
        record = PredictionRecord.query.filter_by(
            id=record_id,
            user_id=request.current_user.id
        ).first()
        
        if not record:
            return jsonify({'error': '记录不存在或无权限访问'}), 404
        
        # 创建搜索服务实例
        from services.history_search_service import HistorySearchService
        search_service = HistorySearchService(db.session, request.current_user.id, PredictionRecord)
        
        # 格式化记录
        formatted_record = search_service._format_record(record)
        
        # 创建导出服务实例
        base_dir = Path(__file__).parent.parent
        logger.info(f"项目根目录: {base_dir}")
        export_service = ReportExportService(base_dir)
        
        # 导出报告
        logger.info(f"开始调用导出服务，格式: {export_format}")
        result = export_service.export_report(
            record_data=formatted_record,
            export_format=export_format,
            template_name=template_name
        )
        logger.info(f"导出服务返回结果: {result}")
        
        if not result['success']:
            return jsonify({'error': result['message']}), 500
        
        # 返回文件路径和下载链接
        return jsonify({
            'success': True,
            'message': result['message'],
            'filename': result['filename'],
            'download_url': f"/api/user/report/download?filename={result['filename']}",
            'format': result['format']
        })
    except Exception as e:
        logger.error(f"导出报告失败: {e}")
        return jsonify({'error': '导出报告失败', 'detail': str(e)}), 500

@app.route('/api/user/report/download', methods=['GET'])
@login_required
def download_report():
    """下载报告"""
    try:
        logger.info(f"开始下载报告 - 用户ID: {request.current_user.id}")
        filename = request.args.get('filename')
        logger.info(f"请求下载文件: {filename}")
        
        if not filename:
            return jsonify({'error': '缺少文件名'}), 400
        
        # 构建文件路径
        base_dir = Path(__file__).parent.parent
        filepath = base_dir / "exports" / filename
        logger.info(f"文件路径: {filepath}")
        
        if not filepath.exists():
            logger.error(f"文件不存在: {filepath}")
            return jsonify({'error': '文件不存在'}), 404
        
        # 获取文件类型
        file_ext = filepath.suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        mime_type = mime_types.get(file_ext, 'application/octet-stream')
        
        # 发送文件
        return send_file(
            filepath,
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"下载报告失败: {e}")
        return jsonify({'error': '下载报告失败', 'detail': str(e)}), 500

@app.route('/api/user/report/formats', methods=['GET'])
@login_required
def get_report_formats():
    """获取支持的报告格式"""
    return jsonify({
        'formats': [
            {'value': 'pdf', 'label': 'PDF文档'},
            {'value': 'excel', 'label': 'Excel表格'},
            {'value': 'word', 'label': 'Word文档'}
        ]
    })

def get_model_display_name(model_type):
    """获取模型显示名称"""
    model_names = {
        'medical_qa': '医疗问答',
        'heart_disease': '心脏病预测',
        'tumor': '肿瘤分类',
        'diabetes': '糖尿病评估',
        'chest_xray': '胸部X光检测'
    }
    return model_names.get(model_type, model_type)

def get_prediction_summary(model_type, prediction_result):
    """获取预测结果摘要"""
    if model_type == 'medical_qa':
        answer = prediction_result.get('answer', '')
        return answer[:100] + '...' if len(answer) > 100 else answer
    elif model_type == 'heart_disease':
        prediction = prediction_result.get('prediction', '')
        return f"心脏病风险: {prediction}"
    elif model_type == 'tumor':
        prediction = prediction_result.get('prediction', '')
        return f"肿瘤分类: {prediction}"
    elif model_type == 'diabetes':
        prediction = prediction_result.get('prediction', '')
        return f"糖尿病风险: {prediction}"
    elif model_type == 'chest_xray':
        predictions = prediction_result.get('predictions', {})
        if predictions:
            # 获取阳性预测的疾病
            positive_diseases = []
            for disease, data in predictions.items():
                if data.get('positive', False):
                    positive_diseases.append(disease)
            
            if positive_diseases:
                return f"检测到疾病: {', '.join(positive_diseases[:3])}"
            else:
                return "未检测到明显疾病"
        else:
            return "预测完成"
    return "预测完成"

def get_risk_level(model_type, prediction_result):
    """获取风险等级"""
    logger.debug(f"判断风险等级 - 模型类型: {model_type}, 预测结果: {prediction_result}")
    
    if model_type == 'medical_qa':
        return 'info'
    elif model_type == 'heart_disease':
        confidence = prediction_result.get('confidence', 0.0)
        try:
            confidence = float(confidence)
        except:
            confidence = 0.0
        if confidence > 0.7:
            logger.debug(f"心脏病预测 - 概率: {confidence:.2f}, 风险等级: high")
            return 'high'
        elif confidence > 0.4:
            logger.debug(f"心脏病预测 - 概率: {confidence:.2f}, 风险等级: medium")
            return 'medium'
        else:
            logger.debug(f"心脏病预测 - 概率: {confidence:.2f}, 风险等级: low")
            return 'low'
            
    elif model_type == 'tumor':
        prediction = prediction_result.get('prediction', '')
        prediction_str = str(prediction)
        
        if '恶性' in prediction_str:
            logger.debug(f"肿瘤预测 - 预测值: {prediction}, 风险等级: high")
            return 'high'
        elif '良性' in prediction_str:
            logger.debug(f"肿瘤预测 - 预测值: {prediction}, 风险等级: low")
            return 'low'
        elif '交界性' in prediction_str:
            logger.debug(f"肿瘤预测 - 预测值: {prediction}, 风险等级: medium")
            return 'medium'
        else:
            # 默认中等风险
            logger.debug(f"肿瘤预测 - 预测值: {prediction}, 风险等级: medium (默认)")
            return 'medium'
            
    elif model_type == 'diabetes':
        # 糖尿病服务返回的是并发症类型和发病概率
        complication = prediction_result.get('并发症类型', '')
        probability_str = prediction_result.get('发病概率', '0%')
        
        # 解析发病概率
        try:
            probability = float(probability_str.replace('%', '')) / 100
        except:
            probability = 0.0
        
        if complication == '无':
            # 无并发症，根据发病概率判断风险
            if probability > 0.5:
                logger.debug(f"糖尿病预测 - 并发症类型: {complication}, 发病概率: {probability:.1%}, 风险等级: medium")
                return 'medium'
            elif probability > 0.2:
                logger.debug(f"糖尿病预测 - 并发症类型: {complication}, 发病概率: {probability:.1%}, 风险等级: low")
                return 'low'
            else:
                logger.debug(f"糖尿病预测 - 并发症类型: {complication}, 发病概率: {probability:.1%}, 风险等级: low")
                return 'low'
        else:
            # 有并发症，根据发病概率判断风险
            if probability > 0.7:
                logger.debug(f"糖尿病预测 - 并发症类型: {complication}, 发病概率: {probability:.1%}, 风险等级: high")
                return 'high'
            elif probability > 0.4:
                logger.debug(f"糖尿病预测 - 并发症类型: {complication}, 发病概率: {probability:.1%}, 风险等级: medium")
                return 'medium'
            else:
                logger.debug(f"糖尿病预测 - 并发症类型: {complication}, 发病概率: {probability:.1%}, 风险等级: low")
                return 'low'
            
    elif model_type == 'chest_xray':
        predictions = prediction_result.get('predictions', {})
        if predictions:
            # 检查是否有阳性预测
            positive_count = sum(1 for data in predictions.values() if data.get('positive', False))
            if positive_count > 0:
                logger.debug(f"胸部X光检测 - 检测到 {positive_count} 种疾病, 风险等级: high")
                return 'high'
            else:
                logger.debug(f"胸部X光检测 - 未检测到疾病, 风险等级: low")
                return 'low'
        else:
            logger.debug(f"胸部X光检测 - 无预测结果, 风险等级: info")
            return 'info'
    return 'info'

def get_recommendations(model_type, prediction_result):
    """获取健康建议"""
    base_recommendations = [
        "定期进行体检，监测身体状况",
        "保持健康的生活方式，适量运动",
        "均衡饮食，避免高糖高脂食物",
        "如有不适症状，请及时就医"
    ]
    
    if model_type == 'medical_qa':
        return ["建议咨询专业医生获取更详细的医疗建议"]
    elif model_type == 'heart_disease':
        risk_level = get_risk_level(model_type, prediction_result)
        if risk_level == 'high':
            return [
                "建议立即就医进行详细检查",
                "定期监测血压、血糖和胆固醇",
                "避免剧烈运动，保持情绪稳定",
                "戒烟限酒，控制饮食"
            ]
        else:
            return base_recommendations
    elif model_type == 'tumor':
        risk_level = get_risk_level(model_type, prediction_result)
        if risk_level == 'high':
            return [
                "建议立即就医进行进一步检查",
                "定期进行相关筛查",
                "避免吸烟和有害物质暴露",
                "保持积极心态，配合治疗"
            ]
        else:
            return base_recommendations
    elif model_type == 'diabetes':
        risk_level = get_risk_level(model_type, prediction_result)
        complication = prediction_result.get('并发症类型', '')
        probability_str = prediction_result.get('发病概率', '0%')
        
        if risk_level == 'high':
            return [
                "建议立即就医进行详细检查",
                "定期监测血糖和并发症相关指标",
                "严格控制饮食，减少糖分和碳水化合物摄入",
                "适量运动，保持健康体重",
                "定期进行并发症筛查"
            ]
        elif risk_level == 'medium':
            return [
                "建议就医进行糖尿病筛查",
                "定期监测血糖水平",
                "控制饮食，减少糖分摄入",
                "适量运动，保持健康体重",
                "注意并发症早期症状"
            ]
        else:
            if complication == '无':
                return [
                    "继续保持当前健康管理方案",
                    "定期进行血糖监测",
                    "保持健康的生活方式",
                    "如有不适症状，请及时就医"
                ]
            else:
                return [
                    "建议咨询专业医生",
                    "定期监测相关指标",
                    "保持健康的生活方式",
                    "注意并发症早期症状"
                ]
    elif model_type == 'chest_xray':
        predictions = prediction_result.get('predictions', {})
        if predictions:
            # 检查是否有阳性预测
            positive_count = sum(1 for data in predictions.values() if data.get('positive', False))
            if positive_count > 0:
                return [
                    "建议就医进行进一步检查",
                    "定期进行胸部X光检查",
                    "避免吸烟和二手烟暴露",
                    "注意呼吸系统健康"
                ]
            else:
                return base_recommendations
        else:
            return base_recommendations
    
    return base_recommendations

if __name__ == '__main__':
    # 创建数据库表
    with app.app_context():
        db.create_all()
    # 启动应用，仅监听本地，使用HTTP
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )