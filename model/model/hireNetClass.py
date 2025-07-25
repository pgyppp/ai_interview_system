import torch
import torch.nn as nn


# ----------------------------------------------------------------------------------
# 新的注意力模块：用于二维特征向量
# ----------------------------------------------------------------------------------
class FeatureAttention(nn.Module):
    """特征自注意力模块"""

    def __init__(self, input_dim, n_heads=8, dropout=0.1):
        super().__init__()
        # PyTorch内置的多头自注意力层
        # 注意：input_dim必须能被n_heads整除
        self.attention = nn.MultiheadAttention(embed_dim=input_dim, num_heads=n_heads, dropout=dropout,
                                               batch_first=True)
        self.norm = nn.LayerNorm(input_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # x 的形状是 (batch_size, feature_dim)

        # 自注意力层期望的输入是 (batch, sequence_length, feature_dim)
        # 我们的特征向量不是一个序列，所以我们给它增加一个虚拟的序列长度维度，值为1
        x_seq = x.unsqueeze(1)  # 形状变为 (batch, 1, feature_dim)

        # Q, K, V 都来自同一个输入 x_seq
        attn_output, _ = self.attention(x_seq, x_seq, x_seq)

        # 将注意力的输出通过残差连接和层归一化（标准的Transformer做法）
        x = x + self.dropout(attn_output.squeeze(1))  # 移除虚拟的序列维度
        x = self.norm(x)

        return x


# ----------------------------------------------------------------------------------
#                                     修改后的 HireNet 模型
# ----------------------------------------------------------------------------------
class HireNet(nn.Module):
    """完整的HireNet模型架构 (集成了新的特征注意力模块)"""

    def __init__(self, visual_feat_dim=512, audio_feat_dim=768, text_feat_dim=768):
        super().__init__()

        # --- 视觉处理分支 (已修改) ---
        # 使用新的特征注意力模块替换旧的分层注意力
        self.visual_attention = FeatureAttention(input_dim=visual_feat_dim)
        self.visual_adapter = nn.Sequential(
            nn.Linear(visual_feat_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3))

        # --- 音频处理分支 (保持不变) ---
        # 移除或注释掉这一行，因为它在 __init__ 中访问了未定义的 'audio' 变量
        # print(f"HireNet: Input audio shape: {audio.shape}") # Debug print
        self.audio_lstm = nn.LSTM(
            input_size=audio_feat_dim,
            hidden_size=256,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        self.audio_attention = nn.Sequential(
            nn.Linear(512, 128),
            nn.Tanh(),
            nn.Linear(128, 1)
        )
        self.audio_adapter = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.3))

        # --- 文本处理分支 (保持不变) ---
        self.text_adapter = nn.Sequential(
            nn.Linear(text_feat_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.3))

        # --- 多模态融合 (保持不变) ---
        self.fusion_layer = nn.Sequential(
            nn.Linear(256 * 3, 512),
            nn.ReLU(),
            nn.Dropout(0.5))

        # --- 输出层 (保持不变) ---
        # 注意：这里为您补全了所有11个指标的输出层定义
        self.proficiency = nn.Sequential(nn.Linear(512, 1), nn.Sigmoid())
        self.frameworks = nn.Sequential(nn.Linear(512, 1), nn.Sigmoid())
        self.optimization = nn.Sequential(nn.Linear(512, 1), nn.Sigmoid())
        self.versioning = nn.Sequential(nn.Linear(512, 1), nn.Sigmoid())
        self.involvement = nn.Sequential(nn.Linear(512, 1), nn.Sigmoid())
        self.impact = nn.Sequential(nn.Linear(512, 1), nn.Sigmoid())
        self.outcomes = nn.Sequential(nn.Linear(512, 1), nn.Sigmoid())
        self.logic = nn.Sequential(nn.Linear(512, 1), nn.Sigmoid())
        self.communication = nn.Sequential(nn.Linear(512, 1), nn.Sigmoid())
        self.solving = nn.Sequential(nn.Linear(512, 1), nn.Sigmoid())
        self.learning = nn.Sequential(nn.Linear(512, 1), nn.Sigmoid())

        # --- 可学习的融合权重 (保持不变) ---
        self.fusion_weights = nn.Parameter(torch.tensor([0.4, 0.3, 0.3]))

    def forward(self, video, audio, text):
        # --- 视觉分支处理 (已修改) ---
        # 1. 将(batch, feat_dim)的视频特征送入新的注意力模块
        visual_context = self.visual_attention(video)
        # 2. 将经过注意力加权的特征送入适配器
        visual_feat = self.visual_adapter(visual_context)

        # --- 音频分支处理 (保持不变) ---
        audio_out, _ = self.audio_lstm(audio)
        print(f"HireNet: audio_out shape: {audio_out.shape}")  # Debug print
        audio_weights = torch.softmax(self.audio_attention(audio_out), dim=1)
        print(f"HireNet: audio_weights shape: {audio_weights.shape}")  # Debug print
        audio_context = torch.sum(audio_out * audio_weights, dim=1)
        print(f"HireNet: audio_context shape: {audio_context.shape}")  # Debug print
        audio_feat = self.audio_adapter(audio_context)

        # --- 文本分支处理 (保持不变) ---
        text_feat = self.text_adapter(text)

        # --- 加权特征融合 (保持不变) ---
        # fused_feat = self.fusion_weights[0] * visual_feat + \
        #              self.fusion_weights[1] * audio_feat + \
        #              self.fusion_weights[2] * text_feat

        fused_feat = torch.cat([visual_feat, audio_feat, text_feat], dim=1)

        # --- 通过融合层 (保持不变) ---
        fused_feat = self.fusion_layer(fused_feat)

        # --- 多任务输出 (保持不变) ---
        proficiency = self.proficiency(fused_feat).squeeze(-1)
        frameworks = self.frameworks(fused_feat).squeeze(-1)
        optimization = self.optimization(fused_feat).squeeze(-1)
        versioning = self.versioning(fused_feat).squeeze(-1)
        involvement = self.involvement(fused_feat).squeeze(-1)
        impact = self.impact(fused_feat).squeeze(-1)
        outcomes = self.outcomes(fused_feat).squeeze(-1)
        logic = self.logic(fused_feat).squeeze(-1)
        communication = self.communication(fused_feat).squeeze(-1)
        solving = self.solving(fused_feat).squeeze(-1)
        learning = self.learning(fused_feat).squeeze(-1)

        # --- 返回值 (保持结构不变) ---
        # 新的注意力机制不产生独立的frame/segment权重，设为None
        return {
            'proficiency': proficiency,
            'frameworks': frameworks,
            'optimization': optimization,
            'versioning': versioning,
            'involvement': involvement,
            'impact': impact,
            'outcomes': outcomes,
            'logic': logic,
            'communication': communication,
            'solving': solving,
            'learning': learning,
            'attention': {
                'frame': None,  # 不再有帧级注意力
                'segment': None,  # 不再有片段级注意力
                'audio': audio_weights
            }
        }