#!/usr/bin/env python3
"""
历史记录搜索服务
提供历史记录的搜索、过滤和分页功能
"""

import json
import logging
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class HistorySearchService:
    """历史记录搜索服务"""
    
    def __init__(self, db_session, user_id: int, prediction_record_model):
        self.db_session = db_session
        self.user_id = user_id
        self.PredictionRecord = prediction_record_model
    
    def search_records(self, 
                      page: int = 1, 
                      per_page: int = 10,
                      model_type: Optional[str] = None,
                      risk_level: Optional[str] = None,
                      date_range: Optional[str] = None,
                      keyword: Optional[str] = None) -> Dict[str, Any]:
        """
        搜索历史记录
        
        Args:
            page: 页码
            per_page: 每页数量
            model_type: 模型类型过滤
            risk_level: 风险等级过滤
            date_range: 日期范围过滤 (格式: "2024-01-01 to 2024-01-31")
            keyword: 关键词搜索
            
        Returns:
            包含记录列表和分页信息的字典
        """
        try:
            # 基础查询
            query = self.db_session.query(self.PredictionRecord).filter(
                self.PredictionRecord.user_id == self.user_id
            )
            
            # 应用各种过滤条件
            query = self._apply_model_type_filter(query, model_type)
            query = self._apply_risk_level_filter(query, risk_level)
            query = self._apply_date_range_filter(query, date_range)
            query = self._apply_keyword_filter(query, keyword)
            
            # 排序和分页
            query = query.order_by(self.PredictionRecord.created_at.desc())
            
            # 执行分页查询
            pagination = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            # 格式化记录
            formatted_records = []
            for record in pagination.items:
                formatted_record = self._format_record(record)
                formatted_records.append(formatted_record)
            
            return {
                'records': formatted_records,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
            
        except Exception as e:
            logger.error(f"搜索历史记录失败: {e}")
            raise
    
    def _apply_model_type_filter(self, query, model_type: Optional[str]):
        """应用模型类型过滤"""
        if model_type and model_type.strip():
            query = query.filter(self.PredictionRecord.model_type == model_type.strip())
        return query
    
    def _apply_risk_level_filter(self, query, risk_level: Optional[str]):
        """应用风险等级过滤"""
        if not risk_level or not risk_level.strip():
            return query
        
        risk_level = risk_level.strip()
        
        # 直接使用数据库字段进行过滤，提高性能
        query = query.filter(self.PredictionRecord.risk_level == risk_level)
        
        return query
    
    def _apply_date_range_filter(self, query, date_range: Optional[str]):
        """应用日期范围过滤"""
        if not date_range or not date_range.strip():
            return query
        
        try:
            date_range = date_range.strip()
            
            # 处理特殊日期值
            if date_range.lower() == 'today':
                today = datetime.now().date()
                start_date = datetime.combine(today, datetime.min.time())
                end_date = datetime.combine(today, datetime.max.time())
            elif date_range.lower() == 'yesterday':
                yesterday = (datetime.now() - timedelta(days=1)).date()
                start_date = datetime.combine(yesterday, datetime.min.time())
                end_date = datetime.combine(yesterday, datetime.max.time())
            elif date_range.lower() == 'this_week':
                today = datetime.now().date()
                start_date = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
                end_date = datetime.combine(start_date.date() + timedelta(days=7), datetime.min.time())
            elif date_range.lower() == 'this_month':
                today = datetime.now().date()
                start_date = datetime.combine(today.replace(day=1), datetime.min.time())
                if today.month == 12:
                    end_date = datetime.combine(today.replace(year=today.year + 1, month=1, day=1), datetime.min.time())
                else:
                    end_date = datetime.combine(today.replace(month=today.month + 1, day=1), datetime.min.time())
            else:
                # 处理不同的日期范围格式
                if ' to ' in date_range:
                    start_date_str, end_date_str = date_range.split(' to ')
                elif ' - ' in date_range:
                    start_date_str, end_date_str = date_range.split(' - ')
                else:
                    # 单个日期
                    start_date_str = date_range
                    end_date_str = date_range
                
                # 解析日期
                start_date = datetime.strptime(start_date_str.strip(), '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str.strip(), '%Y-%m-%d') + timedelta(days=1)
            
            # 应用日期过滤
            query = query.filter(
                and_(
                    self.PredictionRecord.created_at >= start_date,
                    self.PredictionRecord.created_at < end_date
                )
            )
            
            logger.debug(f"应用日期范围过滤: {start_date} 到 {end_date}")
            
        except ValueError as e:
            logger.warning(f"无效的日期范围格式 '{date_range}': {e}")
        except Exception as e:
            logger.error(f"处理日期范围过滤时出错: {e}")
        
        return query
    
    def _apply_keyword_filter(self, query, keyword: Optional[str]):
        """应用关键词过滤"""
        if not keyword or not keyword.strip():
            return query
        
        keyword = keyword.strip()
        
        query = query.filter(
            or_(
                self.PredictionRecord.prediction_result.ilike(f'%{keyword}%'),
                self.PredictionRecord.input_data.ilike(f'%{keyword}%'),
                self.PredictionRecord.model_type.ilike(f'%{keyword}%'),
                self.PredictionRecord.risk_level.ilike(f'%{keyword}%')
            )
        )
        
        logger.debug(f"应用关键词过滤: '{keyword}'")
        
        return query
    
    def _format_record(self, record) -> Dict[str, Any]:
        """格式化记录数据"""
        try:
            input_data = json.loads(record.input_data)
            prediction_result = json.loads(record.prediction_result)
            
            # 获取模型显示名称
            model_name = self._get_model_display_name(record.model_type)
            
            # 获取预测摘要
            summary = self._get_prediction_summary(record.model_type, prediction_result)
            
            # 使用数据库存储的风险等级，如果没有则计算
            risk_level = record.risk_level
            if not risk_level:
                risk_level = self._get_risk_level(record.model_type, prediction_result)
            
            # 获取健康建议
            recommendations = self._get_recommendations(record.model_type, prediction_result)
            
            formatted_record = {
                'id': record.id,
                'model_type': record.model_type,
                'model_name': model_name,
                'input_data': input_data,
                'prediction_result': prediction_result,
                'confidence_score': record.confidence_score,
                'created_at': record.created_at.isoformat(),
                'created_at_local': (record.created_at + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                'summary': summary,
                'risk_level': risk_level,
                'recommendations': recommendations
            }
            
            return formatted_record
            
        except Exception as e:
            logger.error(f"格式化记录失败: {e}")
            return {
                'id': record.id,
                'model_type': record.model_type,
                'model_name': '未知类型',
                'input_data': {},
                'prediction_result': {},
                'confidence_score': 0.0,
                'created_at': record.created_at.isoformat(),
                'created_at_local': (record.created_at + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S'),
                'summary': '数据格式错误',
                'risk_level': record.risk_level or 'info',
                'recommendations': ['数据格式错误，请联系管理员']
            }
    
    def _get_model_display_name(self, model_type: str) -> str:
        """获取模型显示名称"""
        model_names = {
            'medical_qa': '医疗问答',
            'heart_disease': '心脏病预测',
            'tumor': '肿瘤分类',
            'diabetes': '糖尿病评估',
            'chest_xray': '胸部X光检测'
        }
        return model_names.get(model_type, model_type)
    
    def _get_prediction_summary(self, model_type: str, prediction_result: Dict[str, Any]) -> str:
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
    
    def _get_risk_level(self, model_type: str, prediction_result: Dict[str, Any]) -> str:
        """获取风险等级"""
        if model_type == 'medical_qa':
            return 'info'
        elif model_type == 'heart_disease':
            prediction = prediction_result.get('prediction', '')
            prediction_str = str(prediction).lower()
            
            # 明确的高风险关键词
            high_risk_keywords = ['有心脏病风险', '高风险', '阳性', '1', 'true']
            # 明确的低风险关键词
            low_risk_keywords = ['无心脏病风险', '低风险', '阴性', '0', 'false']
            
            # 优先检查明确的低风险关键词
            if any(keyword in prediction_str for keyword in low_risk_keywords):
                return 'low'
            # 然后检查高风险关键词
            elif any(keyword in prediction_str for keyword in high_risk_keywords):
                return 'high'
            else:
                # 默认低风险
                return 'low'
                
        elif model_type == 'tumor':
            prediction = prediction_result.get('prediction', '')
            prediction_str = str(prediction)
            
            if '恶性' in prediction_str:
                return 'high'
            elif '良性' in prediction_str:
                return 'low'
            elif '交界性' in prediction_str:
                return 'medium'
            else:
                # 默认中等风险
                return 'medium'
                
        elif model_type == 'diabetes':
            complication = prediction_result.get('并发症类型', '')
            
            if complication == '无':
                return 'low'
            else:
                return 'high'
                
        elif model_type == 'chest_xray':
            predictions = prediction_result.get('predictions', {})
            if predictions:
                # 检查是否有阳性预测
                positive_count = sum(1 for data in predictions.values() if data.get('positive', False))
                return 'high' if positive_count > 0 else 'low'
            else:
                return 'info'
        return 'info'
    
    def _get_recommendations(self, model_type: str, prediction_result: Dict[str, Any]) -> List[str]:
        """获取健康建议"""
        base_recommendations = [
            "定期进行体检，监测身体状况",
            "保持健康的生活方式，适量运动",
            "均衡饮食，避免高糖高脂食物",
            "如有不适症状，请及时就医"
        ]
        
        risk_level = self._get_risk_level(model_type, prediction_result)
        
        if model_type == 'medical_qa':
            return ["建议咨询专业医生获取更详细的医疗建议"]
        elif model_type == 'heart_disease' and risk_level == 'high':
            return [
                "建议立即就医进行详细检查",
                "定期监测血压、血糖和胆固醇",
                "避免剧烈运动，保持情绪稳定",
                "戒烟限酒，控制饮食"
            ]
        elif model_type == 'tumor' and risk_level == 'high':
            return [
                "建议立即就医进行进一步检查",
                "定期进行相关筛查",
                "避免吸烟和有害物质暴露",
                "保持积极心态，配合治疗"
            ]
        elif model_type == 'diabetes' and risk_level == 'high':
            return [
                "建议就医进行糖尿病筛查",
                "定期监测血糖水平",
                "控制饮食，减少糖分摄入",
                "适量运动，保持健康体重"
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
        
        return base_recommendations
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """获取搜索统计信息"""
        try:
            # 总记录数
            total_records = self.db_session.query(self.PredictionRecord).filter(
                self.PredictionRecord.user_id == self.user_id
            ).count()
            
            # 按模型类型统计
            model_stats = self.db_session.query(
                self.PredictionRecord.model_type,
                func.count(self.PredictionRecord.id).label('count')
            ).filter(
                self.PredictionRecord.user_id == self.user_id
            ).group_by(self.PredictionRecord.model_type).all()
            
            # 按风险等级统计
            risk_stats = {
                'high': 0,
                'medium': 0,
                'low': 0,
                'info': 0
            }
            
            # 计算各风险等级的记录数
            for model_type, count in model_stats:
                if model_type == 'medical_qa':
                    risk_stats['info'] += count
                else:
                    risk_stats['low'] += count 
            
            return {
                'total_records': total_records,
                'model_stats': {stat.model_type: stat.count for stat in model_stats},
                'risk_stats': risk_stats
            }
            
        except Exception as e:
            logger.error(f"获取搜索统计信息失败: {e}")
            return {
                'total_records': 0,
                'model_stats': {},
                'risk_stats': {'high': 0, 'medium': 0, 'low': 0, 'info': 0}
            } 