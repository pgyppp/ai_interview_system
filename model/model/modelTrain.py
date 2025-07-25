import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision.models.video import r3d_18, R3D_18_Weights
from transformers import BertModel, BertTokenizer, Wav2Vec2Model, Wav2Vec2Processor
import librosa
import numpy as np
import pandas as pd
from torch.nn.utils.rnn import pad_sequence
import os
from tqdm import tqdm
import matplotlib.pyplot as plt
from torchvision import transforms
import decord
from decord import VideoReader, cpu

# --- MODIFICATION START ---
from sklearn.model_selection import train_test_split
# 假设您的模型在一个名为 hireNetClass.py 的文件中
from hireNetClass import HireNet

plt.rcParams['font.sans-serif'] = ['SimHei']  # 'SimHei' 是一个常用的中文字体
plt.rcParams['axes.unicode_minus'] = False

# --- MODIFICATION END ---

# 设置随机种子确保可复现性
torch.manual_seed(42)
np.random.seed(42)


# --------------------
# 1. 数据预处理模块
# --------------------
class InterviewDataset(Dataset):
    # --- MODIFICATION START ---
    # 修改__init__以直接接收DataFrame，而不是文件路径
    def __init__(self, device, data_dir, labels_df, sample_length=64, fps=8):  # 减少采样长度以加快处理
        # --- MODIFICATION END ---
        self.data_dir = data_dir
        self.device = device
        self.labels = labels_df.reset_index(drop=True)  # 重置索引以保证iloc正常工作
        self.sample_length = sample_length
        self.fps = fps
        self.total_frames = sample_length * fps

        # 初始化预处理器
        self.visual_extractor = r3d_18(weights=R3D_18_Weights.DEFAULT)
        self.visual_extractor.fc = nn.Identity()
        self.visual_extractor.to(self.device)  # 将模型移到设备

        self.text_tokenizer = BertTokenizer.from_pretrained('./bert-base-uncased/')
        self.text_model = BertModel.from_pretrained('./bert-base-uncased')
        self.text_model.to(self.device)

        self.audio_processor = Wav2Vec2Processor.from_pretrained("./wav2vec2-base-960h/")
        self.audio_model = Wav2Vec2Model.from_pretrained("./wav2vec2-base-960h")
        self.audio_model.to(self.device)

        self.video_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((112, 112)),
            transforms.Normalize(mean=[0.43216, 0.394666, 0.37645], std=[0.22803, 0.22145, 0.216989]),
        ])

        # 冻结预训练模型(可选)
        for param in self.visual_extractor.parameters():
            param.requires_grad = False
        for param in self.text_model.parameters():
            param.requires_grad = False
        for param in self.audio_model.parameters():
            param.requires_grad = False

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        # 使用 .iloc[idx] 确保我们基于DataFrame的整数位置进行索引
        row = self.labels.iloc[idx]
        candidate_id = str(row['video_id'])  # 确保ID是字符串

        # 加载视频数据并提取特征
        video_path = os.path.join(self.data_dir, 'videos', candidate_id + '.mp4')
        video_features = self.process_video(video_path)

        # 加载音频数据并提取特征
        audio_path = os.path.join(self.data_dir, 'audios', candidate_id + '.wav')
        audio_features = self.process_audio(audio_path)

        # 加载文本数据并提取特征
        transcript_path = os.path.join(self.data_dir, 'transcripts', candidate_id + '.txt')
        text_features = self.process_text(transcript_path)

        # 获取所有标签
        label_names = [
            'proficiency', 'frameworks', 'optimization', 'versioning',
            'involvement', 'impact', 'outcomes', 'logic',
            'communication', 'solving', 'learning'
        ]
        labels = {key: torch.tensor(row[key], dtype=torch.float32) for key in label_names}

        return {
            'video_id': candidate_id,
            'video': video_features,
            'audio': audio_features,
            'text': text_features,
            'labels': labels
        }

    def process_video(self, video_path):
        try:
            vr = VideoReader(video_path, ctx=cpu(0))
            total_frames_in_video = len(vr)
            if total_frames_in_video == 0: raise IndexError("视频为空")

            indices = [int(i * total_frames_in_video / self.total_frames) for i in range(self.total_frames)]
            frames = vr.get_batch(indices).asnumpy()

            processed_frames = [self.video_transform(frame) for frame in frames]
            video_tensor = torch.stack(processed_frames, dim=1)

            with torch.no_grad():
                features = self.visual_extractor(video_tensor.unsqueeze(0).to(self.device))
            return features.squeeze(0).cpu()
        except Exception as e:
            # print(f"处理视频 {video_path} 时出错: {e}。将返回一个零张量。")
            return torch.zeros(512)

    def process_audio(self, audio_path):
        try:
            audio, sr = librosa.load(audio_path, sr=16000, duration=self.sample_length)
            inputs = self.audio_processor(audio, sampling_rate=sr, return_tensors="pt", padding=True)
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            with torch.no_grad():
                outputs = self.audio_model(**inputs)
            return outputs.last_hidden_state.squeeze(0).cpu()
        except Exception as e:
            # print(f"处理音频 {audio_path} 时出错: {e}。将返回一个零张量。")
            return torch.zeros((1, 768))

    def process_text(self, transcript_path):
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                text = f.read()
            inputs = self.text_tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=512)
            inputs = {key: value.to(self.device) for key, value in inputs.items()}
            with torch.no_grad():
                outputs = self.text_model(**inputs)
            return outputs.last_hidden_state[:, 0, :].squeeze(0).cpu()
        except Exception as e:
            # print(f"处理文本 {transcript_path} 时出错: {e}。将返回一个零张量。")
            return torch.zeros(768)


def custom_collate(batch):
    # --- 关键修改：从batch的每个item中提取 video_id ---
    video_ids = [item['video_id'] for item in batch]

    # --- 下面的部分您应该已经有了 ---
    video_features = [item['video'] for item in batch]
    audio_features = [item['audio'] for item in batch]
    text_features = [item['text'] for item in batch]

    labels = {}
    label_keys = batch[0]['labels'].keys()
    for key in label_keys:
        labels[key] = torch.stack([item['labels'][key] for item in batch])

    video_padded = pad_sequence(video_features, batch_first=True, padding_value=0)
    audio_padded = pad_sequence(audio_features, batch_first=True, padding_value=0)
    text_padded = torch.stack(text_features)

    # --- 关键修改：将收集到的 video_ids 放入返回的字典中 ---
    return {
        'video_id': video_ids, # <--- 确保返回的字典里有这一项
        'video': video_padded,
        'audio': audio_padded,
        'text': text_padded,
        'labels': labels
    }


# --------------------
# 2. 模型架构 (假设在 hireNetClass.py 中)
# from hireNetClass import HireNet
# --------------------

# --------------------
# 3. 训练配置
# --------------------
data_dir = '../dataset'
label_file = '../dataset/labels.csv'

# --- MODIFICATION START ---
# --- 数据集划分 (80%训练, 10%验证, 10%测试) ---
# all_labels_df = pd.read_csv(label_file, encoding='utf-8')
# train_val_df, test_df = train_test_split(all_labels_df, test_size=0.1, random_state=42)
# train_df, val_df = train_test_split(train_val_df, test_size=1 / 9, random_state=42)

all_labels_df = pd.read_csv(label_file, encoding='utf-8')

train_df = all_labels_df
val_df = all_labels_df
test_df = all_labels_df

print(f"Total samples: {len(all_labels_df)}")
print(f"Training samples: {len(train_df)}")
print(f"Validation samples: {len(val_df)}")
print(f"Test samples: {len(test_df)}")

# --- 创建数据集和数据加载器 ---
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
batch_size = 8  # 减小batch size防止OOM

train_dataset = InterviewDataset(device, data_dir, train_df)
val_dataset = InterviewDataset(device, data_dir, val_df)
test_dataset = InterviewDataset(device, data_dir, test_df)

train_dataloader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, collate_fn=custom_collate,
                              num_workers=0)
val_dataloader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, collate_fn=custom_collate, num_workers=0)
test_dataloader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, collate_fn=custom_collate,
                             num_workers=0)
# --- MODIFICATION END ---

# --- MODIFICATION START ---
# 初始化模型，并定义所有11个指标的损失函数
model = HireNet().to(device)  # 假设HireNet接受num_labels参数
label_names = [
    'proficiency', 'frameworks', 'optimization', 'versioning',
    'involvement', 'impact', 'outcomes', 'logic',
    'communication', 'solving', 'learning'
]
criterion = {key: nn.MSELoss() for key in label_names}
# --- MODIFICATION END ---

optimizer = optim.AdamW(model.parameters(), lr=5e-5, weight_decay=1e-4)
scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50, eta_min=1e-6)


# --------------------
# 4. 训练与评估函数 (重构后)
# --------------------
# --- MODIFICATION START ---
def train_epoch(model, dataloader, optimizer, criterion, device):
    model.train()

    # 初始化用于累积各个损失的字典
    epoch_losses = {key: 0.0 for key in criterion.keys()}
    total_loss_accumulator = 0.0

    for batch in tqdm(dataloader, desc="Training"):
        video = batch['video'].to(device)
        audio = batch['audio'].to(device)
        text = batch['text'].to(device)
        labels = {k: v.to(device) for k, v in batch['labels'].items()}

        outputs = model(video, audio, text)

        # 计算当前批次的总损失，并分别累积每个子任务的损失
        batch_total_loss = 0
        for key in criterion.keys():
            loss = criterion[key](outputs[key], labels[key])
            epoch_losses[key] += loss.item()  # 累积每个指标的损失值
            batch_total_loss += loss

        optimizer.zero_grad()
        batch_total_loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        total_loss_accumulator += batch_total_loss.item()

    # 计算整个 epoch 的平均损失
    num_batches = len(dataloader)
    avg_losses = {key: value / num_batches for key, value in epoch_losses.items()}
    avg_losses['total_loss'] = total_loss_accumulator / num_batches

    # 返回包含所有损失项的字典
    return avg_losses


def evaluate(model, dataloader, criterion, device):
    model.eval()

    # 初始化用于累积各个损失和结果的字典/列表
    epoch_losses = {key: 0.0 for key in criterion.keys()}
    total_loss_accumulator = 0.0
    all_ids = []
    all_predictions = {key: [] for key in criterion.keys()}
    all_ground_truths = {key: [] for key in criterion.keys()}

    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Evaluating"):
            video = batch['video'].to(device)
            audio = batch['audio'].to(device)
            text = batch['text'].to(device)
            labels = {k: v.to(device) for k, v in batch['labels'].items()}

            outputs = model(video, audio, text)

            # 计算并累积总损失和各个子任务的损失
            batch_total_loss = 0
            for key in criterion.keys():
                loss = criterion[key](outputs[key], labels[key])
                epoch_losses[key] += loss.item()
                batch_total_loss += loss

                # 收集预测和真实值
                all_predictions[key].extend(outputs[key].cpu().numpy())
                all_ground_truths[key].extend(labels[key].cpu().numpy())

            total_loss_accumulator += batch_total_loss.item()
            all_ids.extend(batch['video_id'])

    # 计算平均损失
    num_batches = len(dataloader)
    avg_losses = {key: value / num_batches for key, value in epoch_losses.items()}
    avg_losses['total_loss'] = total_loss_accumulator / num_batches

    # 计算MAE
    mae = {key: np.mean(np.abs(np.array(all_predictions[key]) - np.array(all_ground_truths[key]))) for key in
           criterion.keys()}

    # 整合详细结果
    results_df = pd.DataFrame({'video_id': all_ids})
    for key in criterion.keys():
        results_df[f'pred_{key}'] = all_predictions[key]
        results_df[f'true_{key}'] = all_ground_truths[key]

    # 返回包含所有损失的字典，以及MAE和详细结果
    return avg_losses, mae, results_df
# --- MODIFICATION END ---


# --------------------
# 6. 主训练循环
# --------------------
num_epochs = 30
train_losses = []
val_losses = []
mae_history = {key: [] for key in criterion.keys()}

# --- MODIFICATION START (2/3): 创建新的历史记录字典来存储每个指标的训练损失 ---
train_metric_loss_history = {key: [] for key in criterion.keys()}
val_metric_loss_history = {key: [] for key in criterion.keys()}
# --- MODIFICATION END (2/3) ---

print("Starting training...")
for epoch in range(num_epochs):
    print(f"\nEpoch {epoch + 1}/{num_epochs}")

    # 训练一个epoch，并接收包含所有损失的字典
    train_loss_dict = train_epoch(model, train_dataloader, optimizer, criterion, device)

    # --- MODIFICATION START (2/3): 存储总损失和每个指标的损失 ---
    train_losses.append(train_loss_dict['total_loss'])
    for key in criterion.keys():
        train_metric_loss_history[key].append(train_loss_dict[key])
    # --- MODIFICATION END (2/3) ---

    val_loss_dict, val_mae, _ = evaluate(model, val_dataloader, criterion, device)
    val_losses.append(val_loss_dict['total_loss'])
    for key in criterion.keys():
        val_metric_loss_history[key].append(val_loss_dict[key])

    for key in mae_history:
        mae_history[key].append(val_mae[key])

    scheduler.step()

    print(f"Train Loss: {train_loss_dict['total_loss']:.4f} | Val Loss: {val_loss_dict['total_loss']:.4f}")
    print(
        f"Validation MAE (Comm): {val_mae['communication']:.4f}, (Solving): {val_mae['solving']:.4f}, (Learning): {val_mae['learning']:.4f}")

    if epoch == 0 or val_loss_dict['total_loss'] < min(val_losses[:-1]):
        torch.save(model.state_dict(), 'best_model.pth')
        print("Saved best model")

# --------------------
# 7. 最终模型测试与结果保存
# ... (此部分保持不变)
# --------------------

# --------------------
# 8. 结果可视化
# --------------------
# 绘制总损失曲线
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 图1：总损失曲线
plt.figure(figsize=(12, 6))
plt.plot(train_losses, label='训练总损失 (Train Total Loss)')
plt.plot(val_losses, label='验证总损失 (Validation Total Loss)')
plt.xlabel('轮次 (Epoch)')
plt.ylabel('损失 (Loss)')
plt.title('总训练与验证损失曲线')
plt.legend()
plt.grid(True)
plt.savefig('total_loss_curves.png')
# plt.show()

# 定义一个颜色循环，让图更好看
colors = plt.get_cmap('tab20', len(criterion.keys()))

# 图2：各子任务的训练损失曲线
plt.figure(figsize=(15, 10))
plt.suptitle('各子任务训练损失迭代曲线', fontsize=16)
for i, (key, losses) in enumerate(train_metric_loss_history.items()):
    plt.plot(losses, label=key.capitalize(), color=colors(i))
plt.xlabel('轮次 (Epoch)')
plt.ylabel('损失 (Loss)')
plt.title('所有指标的训练损失 (Training Loss)')
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.grid(True)
plt.tight_layout(rect=[0, 0, 0.85, 0.95])
plt.savefig('individual_training_losses.png')
# plt.show()

# 图3：各子任务的验证损失曲线 (新增)
plt.figure(figsize=(15, 10))
plt.suptitle('各子任务验证损失迭代曲线', fontsize=16)
for i, (key, losses) in enumerate(val_metric_loss_history.items()):
    plt.plot(losses, label=key.capitalize(), color=colors(i))
plt.xlabel('轮次 (Epoch)')
plt.ylabel('损失 (Loss)')
plt.title('所有指标的验证损失 (Validation Loss)')
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.grid(True)
plt.tight_layout(rect=[0, 0, 0.85, 0.95])
plt.savefig('individual_validation_losses.png')
# plt.show()

# 图4：部分指标的验证集MAE曲线
plt.figure(figsize=(12, 6))
# 只可视化部分关键指标以保持清晰
for i, key in enumerate(['communication', 'solving', 'learning']):
    if key in mae_history:
        plt.plot(mae_history[key], label=f'{key} MAE', color=colors(i))
plt.xlabel('轮次 (Epoch)')
plt.ylabel('MAE')
plt.title('部分指标的验证集MAE曲线')
plt.legend()
plt.grid(True)
plt.savefig('validation_mae_curves.png')
# plt.show()


# --------------------
# 9. 注意力可视化示例
# --------------------
def visualize_attention(model, sample):
    model.eval()
    with torch.no_grad():
        video_s = sample['video'].unsqueeze(0).to(device)
        audio_s = sample['audio'].unsqueeze(0).to(device)
        text_s = sample['text'].unsqueeze(0).to(device)
        outputs = model(video_s, audio_s, text_s)

    # --- MODIFICATION START ---
    # 检查注意力权重是否存在
    audio_att = outputs.get('attention', {}).get('audio')
    if audio_att is not None:
        audio_att = audio_att.cpu().squeeze().numpy()
        plt.figure(figsize=(15, 5))
        plt.bar(range(len(audio_att)), audio_att)
        plt.title('Audio Attention Weights on a Test Sample')
        plt.xlabel('Time Step')
        plt.ylabel('Attention Weight')
        plt.savefig('attention_weights.png')
        # plt.show()
    else:
        print("未在模型输出中找到可用的 'audio' 注意力权重进行可视化。")
    # --- MODIFICATION END ---


# # 使用测试集的一个样本可视化注意力
# if len(test_dataset) > 0:
#     sample = test_dataset[0]
#     visualize_attention(model, sample)

print("Training, testing, and visualization completed!")