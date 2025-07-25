import torch
import torch.nn as nn
from transformers import BertModel, BertTokenizer, Wav2Vec2Model, Wav2Vec2Processor
import torchvision.models as models
from torchvision import transforms
import torchaudio
from PIL import Image
import numpy as np
import os

# 导入 HireNet 模型定义
from model.model.hireNetClass import HireNet

class ModelInference:
    def __init__(self, model_path, device='cpu'):
        # 根据用户输入选择设备
        self.device = torch.device(device if torch.cuda.is_available() and device == 'cuda' else 'cpu')
        print(f"使用设备: {self.device}")

        self.model = self._load_model(model_path)
        # self.bert_tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        # self.bert_model = BertModel.from_pretrained("bert-base-uncased").to(self.device)
        # self.wav2vec2_processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
        # self.wav2vec2_model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base-960h").to(self.device)
        self.bert_tokenizer = BertTokenizer.from_pretrained("bert-base-uncased", local_files_only=True)
        self.bert_model = BertModel.from_pretrained("bert-base-uncased", local_files_only=True).to(self.device)
        self.wav2vec2_processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h", local_files_only=True)
        self.wav2vec2_model = Wav2Vec2Model.from_pretrained("facebook/wav2vec2-base-960h", local_files_only=True).to(self.device)
        self.visual_feature_extractor = self._load_visual_feature_extractor().to(self.device)
        self.visual_projection = nn.Linear(2048, 512).to(self.device) # 添加一个投影层

    def _load_model(self, model_path):
        # 加载 HireNet 模型
        model = HireNet(visual_feat_dim=512, audio_feat_dim=768, text_feat_dim=768)
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model.eval() # 设置为评估模式
        return model

    def _load_visual_feature_extractor(self):
        # 使用 ResNet-50 作为视觉特征提取器
        # 注意：这里会看到关于 'pretrained' 和 'weights' 的 UserWarning，因为 torchvision 的 API 更新了。
        # 在实际部署中，可以更新为 weights=ResNet50_Weights.IMAGENET1K_V1 或 .DEFAULT
        resnet = models.resnet50(pretrained=True) 
        # 去掉最后的全连接层，保留特征提取部分
        resnet = nn.Sequential(*list(resnet.children())[:-1])
        return resnet

    def extract_visual_features(self, frame_paths):
        # 图像预处理：resize, 转换为 tensor, 标准化
        transform = transforms.Compose([
            transforms.Resize((224, 224)),  # resize 图像
            transforms.ToTensor(),  # 转换为 Tensor
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # 标准化
        ])
        
        features = []
        for path in frame_paths:
            img = Image.open(path).convert('RGB')
            img_tensor = transform(img).unsqueeze(0).to(self.device)
            with torch.no_grad(): # 确保特征提取过程不计算梯度
                feat = self.visual_feature_extractor(img_tensor)
            # 应用投影层并移除空间维度 (squeeze(2).squeeze(2))
            feat = self.visual_projection(feat.squeeze(2).squeeze(2)) 
            features.append(feat.detach().cpu().numpy())
        
        # 将所有帧的特征平均，并确保最终张量的形状是 (1, feature_dim)
        # np.array(features) 将列表转换为一个 NumPy 数组 (num_frames, 1, feature_dim)
        # .mean(dim=0) 对帧维度进行平均，结果为 (1, feature_dim)
        # 核心修改：移除 .unsqueeze(0)，确保形状为 (1, feature_dim)
        return torch.tensor(np.array(features)).mean(dim=0).to(self.device) 

    def extract_audio_features(self, audio_path, sample_rate=16000):
        # 读取音频并重采样
        waveform, sr = torchaudio.load(audio_path, normalize=True)
        if sr != sample_rate:
            waveform = torchaudio.transforms.Resample(orig_freq=sr, new_freq=sample_rate)(waveform)
        
        # 确保音频是单通道，并转换为 numpy 数组
        audio_array = waveform.mean(dim=0).cpu().numpy()
        
        # 使用 Wav2Vec2 处理音频数据，确保返回批次大小为 1 的张量
        inputs = self.wav2vec2_processor(audio_array, sampling_rate=sample_rate, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()} # 将输入移动到指定设备
        print(f"Wav2Vec2 input_values 形状: {inputs['input_values'].shape}")
        with torch.no_grad():
            outputs = self.wav2vec2_model(**inputs).last_hidden_state
        # outputs 形状为 (batch_size, sequence_length, feature_dim)
        return outputs.to(self.device)

    def extract_text_features(self, text_path): # 更改参数为文本文件路径
        with open(text_path, 'r', encoding='utf-8') as f:
            text_content = f.read()

        # 使用 BERT 提取文本特征
        inputs = self.bert_tokenizer(text_content, return_tensors="pt", truncation=True, padding=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.bert_model(**inputs).last_hidden_state
        # outputs.mean(dim=1) 会将序列维度平均掉，结果形状为 (batch_size, feature_dim)，批次大小在这里是 1。
        return outputs.mean(dim=1).to(self.device)

    def predict(self, frame_paths, audio_path, text_content_path): # 更改参数为文本文件路径
        # 提取视觉、音频和文本特征
        visual_feat = self.extract_visual_features(frame_paths)
        audio_feat = self.extract_audio_features(audio_path)
        text_feat = self.extract_text_features(text_content_path) # 传递文件路径

        print(f"拼接前特征形状:")
        print(f"  视觉特征 (visual_feat): {visual_feat.shape}")
        print(f"  音频特征 (audio_feat): {audio_feat.shape}") # 预期为 (1, 序列长度, 特征维度)
        print(f"  文本特征 (text_feat): {text_feat.shape}")

        # 模型推理
        with torch.no_grad():
            predictions = self.model(visual_feat, audio_feat, text_feat)
        
        # 格式化输出，去除 'attention' 等不需要的键
        # 确保在调用 .item() 之前，张量只包含一个元素
        return {k: v.item() if isinstance(v, torch.Tensor) and v.numel() == 1 else v 
                for k, v in predictions.items() if k != 'attention'}

# 示例用法
if __name__ == "__main__":
    # 假设模型路径和一些示例数据
    model_path = r'e:\比赛\挑战杯-ai面试\ai_interview\ai-review\model\best_model.pth'
    # 假设有帧图像路径列表、音频文件路径和文本内容
    sample_frame_paths = [
        r"E:\比赛\挑战杯-ai面试\ai_interview\output\task_2\frames\frame_6s.jpg", 
        r"E:\比赛\挑战杯-ai面试\ai_interview\output\task_2\frames\frame_12s.jpg"
    ]
    sample_audio_path = r"E:\比赛\挑战杯-ai面试\ai_interview\output\task_2\audio.wav"
    sample_text_content_path = r"E:\比赛\挑战杯-ai面试\ai_interview\output\task_2\transcript.txt" # 现在传递的是文件路径

    # 初始化时可以指定 device 为 'cpu' 或 'cuda'（如果 GPU 可用）
    inference_engine = ModelInference(model_path, device='cpu')  # 或者使用 'cpu'
    results = inference_engine.predict(sample_frame_paths, sample_audio_path, sample_text_content_path)
    print("\n推理结果:")
    for key, value in results.items():
        print(f"  {key}: {value:.4f}")