#!/usr/bin/env python3
"""
Flask API 服务，用于胸部 X 光图片的疾病预测和病灶定位热力图生成
支持 GradCAM、GradCAM++ 和 ScoreCAM
"""

import sys
import os
import uuid
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from PIL import Image
import cv2
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from pathlib import Path
import torchvision.transforms as transforms

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CAM 基类
class CAMBase:
    def __init__(self, model, target_layers, use_cuda=False):
        self.model = model.eval()
        self.target_layers = target_layers
        self.use_cuda = use_cuda
        self.device = torch.device("cuda" if use_cuda and torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.gradients = []
        self.activations = []
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations.append(output)
        def backward_hook(module, grad_in, grad_out):
            self.gradients.append(grad_out[0])
        for layer in self.target_layers:
            layer.register_forward_hook(forward_hook)
            layer.register_backward_hook(backward_hook)

    def __call__(self, input_tensor, targets=None):
        raise NotImplementedError

    def _get_activations_gradients(self, input_tensor):
        self.gradients = []
        self.activations = []
        output = self.model(input_tensor)
        return output

# GradCAM 类 - 改进版本
class GradCAM(CAMBase):
    def __call__(self, input_tensor, targets=None):
        input_tensor = input_tensor.to(self.device)
        output = self._get_activations_gradients(input_tensor)
        if targets is not None:
            self.model.zero_grad()
            target_score = output[0, targets].sum()
            target_score.backward()
        
        activations = self.activations[0].detach()
        gradients = self.gradients[0].detach()
        
        # 使用ReLU确保梯度为正值
        gradients = F.relu(gradients)
        
        # 计算权重
        weights = torch.mean(gradients, dim=(2, 3))
        
        # 创建CAM
        cam = torch.zeros(activations.shape[2:], device=self.device)
        for i, w in enumerate(weights[0]):
            cam += w * activations[0, i]
        
        # 后处理：确保数值稳定性
        cam = F.relu(cam)
        cam_min = cam.min()
        cam_max = cam.max()
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min + 1e-8)
        
        return cam.cpu().numpy()[None, :]

# GradCAM++ 类 - 改进版本
class GradCAMPlusPlus(CAMBase):
    def __call__(self, input_tensor, targets=None):
        input_tensor = input_tensor.to(self.device)
        output = self._get_activations_gradients(input_tensor)
        if targets is not None:
            self.model.zero_grad()
            target_score = output[0, targets].sum()
            target_score.backward()
        
        activations = self.activations[0].detach()
        gradients = self.gradients[0].detach()
        
        # 计算alpha权重（GradCAM++的核心）
        alpha_num = gradients ** 2
        alpha_denom = 2 * gradients ** 2 + torch.sum(activations * gradients ** 3, dim=(2, 3), keepdim=True)
        alpha = alpha_num / (alpha_denom + 1e-8)
        
        # 计算权重
        weights = torch.sum(alpha * F.relu(gradients), dim=(2, 3))
        
        # 创建CAM
        cam = torch.zeros(activations.shape[2:], device=self.device)
        for i, w in enumerate(weights[0]):
            cam += w * activations[0, i]
        
        # 后处理：确保数值稳定性
        cam = F.relu(cam)
        cam_min = cam.min()
        cam_max = cam.max()
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min + 1e-8)
        
        return cam.cpu().numpy()[None, :]

# ScoreCAM 类 - 改进版本
class ScoreCAM(CAMBase):
    def __call__(self, input_tensor, targets=None):
        input_tensor = input_tensor.to(self.device)
        batch_size, _, height, width = input_tensor.size()
        
        # 获取激活图
        with torch.no_grad():
            output = self._get_activations_gradients(input_tensor)
            activations = self.activations[0].detach()
        
        # 使用ReLU确保激活图为正值，并标准化
        activations = F.relu(activations)
        
        # 计算每个通道的重要性分数（基于激活强度）
        channel_importance = torch.mean(activations.view(activations.size(1), -1), dim=1)
        
        # 选择前k个最重要的通道以提高效率
        k = min(64, activations.size(1))  # 最多选择64个通道
        _, top_k_indices = torch.topk(channel_importance, k)
        
        # 创建CAM
        cam = torch.zeros((height, width), device=self.device)
        
        with torch.no_grad():
            for i in top_k_indices:
                # 获取单个通道的激活图
                activation = activations[:, i:i+1, :, :]
                
                # 上采样到输入尺寸
                upsampled = F.interpolate(
                    activation,
                    size=(height, width),
                    mode='bilinear',
                    align_corners=False
                )
                
                # 改进的归一化：使用softmax-like归一化
                upsampled_flat = upsampled.view(upsampled.size(0), -1)
                upsampled_norm = F.softmax(upsampled_flat, dim=1).view_as(upsampled)
                
                # 创建掩码输入 - 使用更合理的掩码方式
                masked_input = input_tensor * upsampled_norm
                
                # 前向传播
                output = self.model(masked_input)
                if targets is not None:
                    score = output[0, targets]
                else:
                    score = output[0].max()
                
                # 累加到CAM，使用通道重要性作为权重
                cam += score * upsampled_norm[0, 0] * channel_importance[i]
        
        # 后处理：确保数值稳定性
        cam = F.relu(cam)
        cam_min = cam.min()
        cam_max = cam.max()
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min + 1e-8)
        
        return cam.cpu().numpy()[None, :]

# 模型类
class DenseNet121(nn.Module):
    def __init__(self, num_classes=14, pretrained=False):
        super(DenseNet121, self).__init__()
        if pretrained:
            self.densenet = models.densenet121(pretrained=pretrained)
        else:
            self.densenet = models.densenet121(pretrained=False)
        num_ftrs = self.densenet.classifier.in_features
        self.densenet.classifier = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_ftrs, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )

    def forward(self, x):
        return self.densenet(x)

# 预测类
class Predictor:
    def __init__(self, model, config):
        self.config = config
        self.model = model
        self.device = torch.device(self.config.DEVICE)
        self.model.to(self.device)
        self.model.eval()
        self.optimal_thresholds = self._load_optimal_thresholds()

    def _load_optimal_thresholds(self):
        threshold_path = os.path.join(self.config.CHECKPOINT_DIR, 'optimal_thresholds.pth')
        if os.path.exists(threshold_path):
            thresholds = torch.load(threshold_path, map_location='cpu')
            
            if isinstance(thresholds, list) or isinstance(thresholds, np.ndarray):
                logger.info(f"✅ 成功加载阈值: {thresholds}")
                return thresholds
            elif isinstance(thresholds, dict) and 'Optimal_Threshold' in thresholds:
                logger.info(f"✅ 成功加载阈值: {thresholds['Optimal_Threshold']}")
                return thresholds['Optimal_Threshold']
            else:
                logger.warning(f"Invalid format in {threshold_path}, using default threshold 0.5")
                return [0.5] * self.config.NUM_CLASSES
        else:
            logger.warning(f"{threshold_path} not found, using default threshold 0.5")
            return [0.5] * self.config.NUM_CLASSES

    def predict_single_image(self, image_path, transform):
        image = Image.open(image_path).convert('RGB')
        image = transform(image).unsqueeze(0)
        image = image.to(self.device)
        with torch.no_grad():
            output = self.model(image)
            probabilities = torch.sigmoid(output)
            predictions = torch.zeros_like(probabilities)
            for i, threshold in enumerate(self.optimal_thresholds):
                predictions[:, i] = (probabilities[:, i] > threshold).float()
        return predictions.cpu().numpy()[0], probabilities.cpu().numpy()[0]

# 主服务类
class ChestXrayService:
    def __init__(self, config=None):
        if config is None:
            from config import Config
            self.config = Config()
        else:
            self.config = config
            
        self.UPLOAD_FOLDER = str(self.config.UPLOAD_DIR)
        os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(str(self.config.RESULT_DIR), exist_ok=True)
        self.ALLOWED_EXTENSIONS = self.config.ALLOWED_EXTENSIONS
        try:
            self.model = DenseNet121(num_classes=self.config.NUM_CLASSES, pretrained=True)
            checkpoint_path = os.path.join(str(self.config.CHECKPOINT_DIR), 'best_model.pth')
            if not os.path.exists(checkpoint_path):
                raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}")
            
            checkpoint = torch.load(checkpoint_path, map_location=self.config.DEVICE)
            
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.to(self.config.DEVICE)
            self.model.eval()
            logger.info("✅ Model loaded successfully")
            logger.info(f"📋 模型配置: num_classes={self.config.NUM_CLASSES}, pretrained=True")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            raise RuntimeError("Model initialization failed")
        self.predictor = Predictor(self.model, self.config)
        self.target_layer = self.model.densenet.features.denseblock4

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def get_transforms(self, is_training=False):
        return transforms.Compose([
            transforms.Resize((512, 512)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def generate_heatmap(self, image_tensor, class_idx, cam_method):
        cam_classes = {
            'gradcam': GradCAM,
            'gradcam++': GradCAMPlusPlus,
            'scorecam': ScoreCAM
        }
        if cam_method not in cam_classes:
            raise ValueError(f"Unsupported CAM method: {cam_method}")
        cam = cam_classes[cam_method](self.model, [self.target_layer], use_cuda=(self.config.DEVICE == 'cuda'))
        heatmap = cam(image_tensor, targets=class_idx)
        return heatmap[0]

    def predict(self, file, cam_method='gradcam', user_id: str = None):
        if file.filename == '' or not self.allowed_file(file.filename):
            raise ValueError('Invalid file format. Only PNG, JPG, JPEG allowed')
        
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        file_path = os.path.join(self.UPLOAD_FOLDER, filename)
        file.save(file_path)
        logger.info(f"📁 临时文件已保存: {file_path}")
        
        try:
            from utils.redis_manager import get_redis_manager
            redis_mgr = get_redis_manager()
            
            # 生成缓存键（基于文件内容和参数）
            import hashlib
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            cache_key = f"chest_xray:{file_hash}:{cam_method}"
            
            cached_result = redis_mgr.get_cache(cache_key)
            if cached_result:
                logger.info(f"✅ 胸部X光预测缓存命中: {filename}")
                # 清理临时文件
                os.remove(file_path)
                return cached_result
        except Exception as e:
            logger.warning(f"缓存检查失败: {e}")
        
        # 读取原始图片并保存尺寸信息
        original_image = Image.open(file_path).convert('RGB')
        original_size = original_image.size  # (width, height)
        original_np = np.array(original_image)
        
        # 记录调试信息
        logger.info(f"处理图片: {filename}")
        logger.info(f"原始尺寸: {original_size}")
        logger.info(f"原始数组形状: {original_np.shape}")
        
        # 应用变换得到模型输入
        transform = self.get_transforms(is_training=False)
        image_tensor = transform(original_image).unsqueeze(0).to(self.config.DEVICE)
        
        logger.info(f"模型输入张量形状: {image_tensor.shape}")
        
        # 进行预测
        with torch.no_grad():
            output = self.model(image_tensor)
            probabilities = torch.sigmoid(output)
            predictions = torch.zeros_like(probabilities)
            for i, threshold in enumerate(self.predictor.optimal_thresholds):
                predictions[:, i] = (probabilities[:, i] > threshold).float()
        
        pred_labels = predictions.cpu().numpy()[0]
        pred_probs = probabilities.cpu().numpy()[0]
        
        # 详细记录预测结果
        logger.info("=" * 60)
        logger.info("🔍 详细预测结果分析")
        logger.info("=" * 60)
        logger.info(f"模型输出原始值范围: [{output.min().item():.4f}, {output.max().item():.4f}]")
        logger.info(f"Sigmoid后概率值范围: [{pred_probs.min():.4f}, {pred_probs.max():.4f}]")
        logger.info(f"使用的阈值: {self.predictor.optimal_thresholds}")
        logger.info("")
        
        # 记录每个疾病的预测结果
        logger.info("📊 各疾病预测详情:")
        for i, (disease, prob, pred, threshold) in enumerate(zip(
            self.config.DISEASE_LABELS, pred_probs, pred_labels, self.predictor.optimal_thresholds
        )):
            status = "✅ 阳性" if pred == 1 else "❌ 阴性"
            logger.info(f"  {i:2d}. {disease:20s}: 概率={prob:.4f}, 阈值={threshold:.4f}, 预测={status}")
        
        # 选择概率最高的类别生成热力图
        class_idx = np.argmax(pred_probs)
        max_prob = pred_probs[class_idx]
        max_disease = self.config.DISEASE_LABELS[class_idx]
        logger.info("")
        logger.info(f"🎯 选择用于热力图的类别: {class_idx} ({max_disease}), 概率: {max_prob:.4f}")
        
        # 记录阳性预测的疾病
        positive_diseases = [self.config.DISEASE_LABELS[i] for i, pred in enumerate(pred_labels) if pred == 1]
        logger.info(f"🔍 最终阳性预测疾病: {positive_diseases}")
        logger.info("=" * 60)
        
        # 生成热力图
        logger.info(f"开始生成热力图，方法: {cam_method}")
        heatmap = self.generate_heatmap(image_tensor, class_idx, cam_method)
        logger.info(f"热力图形状: {heatmap.shape}, 值范围: [{heatmap.min():.4f}, {heatmap.max():.4f}]")
        
        # 改进的热力图resize方法
        # 使用双线性插值而不是最近邻插值，保持热力图的平滑性
        heatmap_resized = cv2.resize(heatmap, (original_size[0], original_size[1]), 
                                   interpolation=cv2.INTER_LINEAR)
        
        logger.info(f"调整后热力图形状: {heatmap_resized.shape}")
        
        # 确保热力图值在合理范围内
        heatmap_resized = np.clip(heatmap_resized, 0, 1)
        logger.info(f"裁剪后热力图值范围: [{heatmap_resized.min():.4f}, {heatmap_resized.max():.4f}]")
        
        # 转换为8位图像用于可视化
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        
        # 确保原始图片是BGR格式用于叠加
        if len(original_np.shape) == 3 and original_np.shape[2] == 3:
            # 如果是RGB格式，转换为BGR
            original_bgr = cv2.cvtColor(original_np, cv2.COLOR_RGB2BGR)
        else:
            original_bgr = original_np
        
        # 叠加热力图到原图
        superimposed_img = heatmap_colored * 0.3 + original_bgr * 0.7
        superimposed_img = np.clip(superimposed_img, 0, 255).astype(np.uint8)
        
        # 保存结果
        heatmap_filename = f'heatmap_{cam_method}_{filename}'
        superimposed_filename = f'superimposed_{cam_method}_{filename}'
        heatmap_path = os.path.join(self.config.RESULT_DIR, heatmap_filename)
        superimposed_path = os.path.join(self.config.RESULT_DIR, superimposed_filename)
        
        # 保存热力图（转换为RGB格式）
        heatmap_rgb = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
        Image.fromarray(heatmap_rgb).save(heatmap_path)
        
        # 保存叠加图（转换为RGB格式）
        superimposed_rgb = cv2.cvtColor(superimposed_img, cv2.COLOR_BGR2RGB)
        Image.fromarray(superimposed_rgb).save(superimposed_path)
        
        logger.info(f"保存热力图: {heatmap_path}")
        logger.info(f"保存叠加图: {superimposed_path}")
        
        # 清理临时文件
        os.remove(file_path)
        logger.info(f"🗑️ 临时文件已清理: {file_path}")
        
        # 返回结果
        predictions = {}
        for i in range(self.config.NUM_CLASSES):
            predictions[self.config.DISEASE_LABELS[i]] = {
                'positive': bool(pred_labels[i]),
                'probability': float(pred_probs[i])
            }
        
        results = {
            'predictions': predictions,
            'heatmap_path': heatmap_filename,
            'superimposed_path': superimposed_filename,
            'cam_method': cam_method,
            'original_size': original_size,
            'model_input_size': (512, 512)  # 与chestxrays保持一致
        }
        
        # 添加改进的CAM方法说明
        logger.info("🎯 使用的改进CAM方法:")
        if cam_method == 'gradcam':
            logger.info("  - GradCAM: 使用ReLU确保梯度为正值，改进数值稳定性")
        elif cam_method == 'gradcam++':
            logger.info("  - GradCAM++: 使用alpha权重计算，改进定位精度")
        elif cam_method == 'scorecam':
            logger.info("  - ScoreCAM: 选择前64个重要通道，使用softmax归一化，提高效率")
        
        # 缓存结果
        try:
            if 'redis_mgr' in locals():
                redis_mgr.set_cache(cache_key, results, cache_type="prediction")
                logger.info(f"✅ 胸部X光预测结果已缓存: {filename}")
        except Exception as e:
            logger.warning(f"缓存胸部X光预测结果失败: {e}")
        
        return results

    def get_image(self, image_path):
        filename = os.path.basename(image_path)
        full_path = os.path.join(str(self.config.RESULT_DIR), filename)
        
        logger.info(f"服务获取图片 - 输入路径: {image_path}, 文件名: {filename}, 完整路径: {full_path}")
        
        if not os.path.exists(full_path):
            logger.error(f"图片文件不存在: {full_path}")
            raise FileNotFoundError(f'Image not found: {filename}')
        
        return full_path

# Flask 应用
app = Flask(__name__)
service = ChestXrayService()

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        cam_method = request.form.get('cam_method', 'gradcam')
        if cam_method not in ['gradcam', 'gradcam++', 'scorecam']:
            return jsonify({'error': 'Invalid CAM method'}), 400
        results = service.predict(file, cam_method)
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in predict: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_image/<path:image_path>', methods=['GET'])
def get_image(image_path):
    try:
        full_path = service.get_image(image_path)
        return send_file(full_path, mimetype='image/png')
    except Exception as e:
        logger.error(f"Error in get_image: {e}")
        return jsonify({'error': str(e)}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)