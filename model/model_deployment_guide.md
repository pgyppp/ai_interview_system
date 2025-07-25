# 模型部署指南

本文档旨在为AI面试评估系统的模型部署提供详细指导，涵盖环境准备、模型结构、推理流程、依赖管理和部署建议。

## 1. 模型概述

AI面试评估系统采用了一个多模态融合模型（HireNet），该模型能够整合视觉、音频和文本信息，对面试者的表现进行综合评估。模型通过以下方式进行推理：

*   **视觉特征提取**：使用预训练的ResNet-50模型从视频帧中提取视觉特征。
*   **音频特征提取**：使用预训练的Wav2Vec2模型从面试音频中提取语音特征。
*   **文本特征提取**：使用预训练的BERT模型从面试转录文本中提取语义特征。
*   **多模态融合与预测**：将提取到的视觉、音频和文本特征输入到HireNet模型中，进行融合并输出最终的评估结果。

## 2. 环境准备

### 2.1 硬件要求

*   **CPU**：最低配置，适用于小规模测试或无GPU环境。
*   **GPU (推荐)**：NVIDIA GPU，推荐使用CUDA兼容的GPU以加速模型推理，显著提高处理效率。

### 2.2 软件要求

*   **操作系统**：Linux (推荐), Windows, macOS。
*   **Python**：Python 3.8+ (推荐 3.10)。
*   **CUDA (如果使用GPU)**：与PyTorch版本兼容的CUDA Toolkit。

### 2.3 依赖安装

所有必要的Python库都列在 `ai_interview\model\requirements.txt` 文件中。请确保在部署环境中安装这些依赖。

```bash
pip install -r requirements.txt
```

**注意**：`transformers` 库会下载预训练模型（如BERT和Wav2Vec2）。在无网络环境部署时，需要提前下载这些模型并配置为本地加载。

## 3. 模型文件

*   **主模型**：`best_model.pth` (HireNet模型权重文件)
*   **预训练模型**：
    *   `bert-base-uncased/` (BERT模型文件，包含 `config.json`, `pytorch_model.bin`, `tokenizer_config.json`, `vocab.txt`)
    *   `wav2vec2-base-960h/` (Wav2Vec2模型文件，包含 `config.json`, `preprocessor_config.json`, `pytorch_model.bin`, `tokenizer_config.json`, `vocab.json`)

这些模型文件通常位于 `ai_interview\model\model\` 目录下。

## 4. 模型推理流程

模型推理的核心逻辑封装在 `model/model/model_inference.py` 的 `ModelInference` 类中。以下是其主要步骤：

1.  **初始化 `ModelInference` 类**：
    *   加载 `best_model.pth` (HireNet模型)。
    *   加载 BERT 模型和分词器 (`bert-base-uncased`)。
    *   加载 Wav2Vec2 模型和处理器 (`wav2vec2-base-960h`)。
    *   加载 ResNet-50 作为视觉特征提取器。
    *   配置推理设备 (CPU 或 GPU)。

2.  **特征提取**：
    *   `extract_visual_features(frame_paths)`：接收视频帧图像路径列表，通过ResNet-50提取视觉特征。
    *   `extract_audio_features(audio_path)`：接收音频文件路径，通过Wav2Vec2提取音频特征。
    *   `extract_text_features(text_path)`：接收文本文件路径（转录文本），通过BERT提取文本特征。

3.  **预测**：
    *   `predict(frame_paths, audio_path, text_content_path)`：调用上述特征提取方法获取多模态特征，然后将这些特征输入到HireNet模型中进行预测，返回评估结果。

## 5. 部署建议

### 5.1 作为API服务部署

推荐将模型推理能力封装为RESTful API服务，供前端或其他服务调用。例如，可以使用 FastAPI、Flask 或 Django 等Python Web框架。

*   **示例 (FastAPI)**：
    *   在 `app.py` 或独立的API文件中创建端点，接收视频、音频和文本输入（或文件路径）。
    *   在API内部调用 `ModelInference` 类的 `predict` 方法。
    *   返回预测结果。

### 5.2 Docker化部署

为了确保环境一致性和简化部署流程，强烈建议使用 Docker 进行容器化部署。

1.  **创建 `Dockerfile`**：
    *   基于Python官方镜像。
    *   安装 `requirements.txt` 中的依赖。
    *   将所有模型文件和代码复制到容器中。
    *   设置环境变量（如CUDA相关）。
    *   定义启动命令，运行API服务。

2.  **构建 Docker 镜像**：
    ```bash
docker build -t ai-interview-model .
    ```

3.  **运行 Docker 容器**：
    ```bash
docker run -p 8000:8000 --gpus all ai-interview-model
    ```
    (如果使用GPU，需要安装 NVIDIA Container Toolkit)

### 5.3 性能优化

*   **GPU加速**：确保在支持CUDA的GPU上运行，并正确配置PyTorch以利用GPU。
*   **批量推理**：如果可能，将多个推理请求打包成批次进行处理，以提高GPU利用率。
*   **模型量化/剪枝**：在对性能要求极高的场景下，可以考虑对模型进行量化或剪枝，以减小模型大小和加速推理，但这可能需要重新训练或微调。
*   **ONNX/TensorRT**：将PyTorch模型转换为ONNX格式，并使用TensorRT进行优化，可以进一步提升推理性能。

## 6. 故障排除

*   **CUDA/GPU问题**：检查CUDA版本与PyTorch、驱动的兼容性。确保 `torch.cuda.is_available()` 返回 `True`。
*   **模型加载失败**：检查 `model_path` 是否正确，模型文件是否完整。
*   **依赖缺失**：确保 `requirements.txt` 中的所有库都已正确安装。
*   **内存溢出 (OOM)**：如果处理大文件或批次过大，可能导致内存不足。尝试减小批次大小或优化特征提取过程。