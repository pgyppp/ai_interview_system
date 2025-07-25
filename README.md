# AI 面试评估系统

这是一个基于多模态大语言模型技术的 AI 面试评估系统。它通过分析面试视频中的图像、语音和文本内容，为候选人提供多维度、深层次的面试表现评估和富有洞察力的反馈。系统集成了先进的视频处理技术、多个专门的 AI 智能体评估模块、直观的雷达图数据可视化以及一键式 PDF 报告生成功能，所有服务均通过一个高效的 FastAPI 后端提供。

## ✨ 项目亮点与优势

- **🤖 多模态综合评估**：系统不仅分析候选人说了什么（文本内容），还分析他们如何说（语音语调）以及他们的非语言表达（面部表情、肢体语言），提供了一个比传统面试更全面的评估视角。
- **🧠 核心 AI 智能体**：项目采用了多个专门设计的 AI 智能体，每个智能体负责一个特定的评估维度（如图像、语音、文本），还有一个综合评估智能体来整合所有信息，形成最终的、连贯的评估报告。这种模块化设计使得系统易于扩展和维护。
- **🚀 先进的技术栈**：后端采用 `FastAPI`，以其高性能和易用性著称。前端则采用原生 `HTML/CSS/JS` 配合 `Tailwind CSS`，实现了现代化、响应式的用户界面，无需复杂的前端框架即可快速迭代。
- **📄 自动化报告生成**：能够一键生成包含雷达图、详细评分、AI 评价和对话历史的专业 PDF 报告，极大地提高了招聘流程的效率。
- **💡 优秀的架构设计**：项目遵循关注点分离（SoC）原则，将路由、AI 智能体、数据库操作和工具函数清晰地分离开来，使得代码库结构清晰、易于理解和扩展。

## 🛠️ 技术栈

- **后端**: FastAPI, Uvicorn
- **前端**: HTML, CSS, JavaScript, Tailwind CSS
- **AI / LLM**: OpenAI (通过 StepFun API) langchain
- **数据可视化**: ECharts (用于雷达图)
- **数据库**: SQLite
- **视频/音频处理**: FFmpeg, MoviePy
- **PDF 生成**: FPDF

## 🏛️ 系统架构

```mermaid
graph TD
    A[用户界面 (UI)] -->|HTTP 请求| B(FastAPI 后端)

    subgraph FastAPI 后端
        B --> C{API 路由}
        C -->|用户管理| D[用户路由]
        C -->|面试流程| E[面试路由]
        C -->|报告生成| F[报告路由]
    end

    subgraph 核心服务
        E --> G[视频处理]
        G --> H[抽帧 & 音频提取]
        H --> I{多模态分析}
        I --> J[图像分析Agent]
        I --> K[语音分析Agent]
        I --> L[文本分析Agent]
        J & K & L --> M[综合评估Agent]
        F --> N[PDF报告生成]
        M --> N
    end

    D & E & F --> O[数据库 (SQLite)]

    A -- 显示 --> O
    A -- 显示 --> N
```

## 📂 项目结构

```
ai_interview/
├── .env                   # 环境变量配置
├── agents/                  # AI 智能体模块
│   ├── image_analysis.py    # 图像分析
│   ├── integrated_evaluator.py # 综合评估
│   ├── question_agent.py    # 问题生成
│   ├── speech_analysis.py   # 语音分析
│   └── text_analysis.py     # 文本分析
├── app.py                   # FastAPI 应用主入口
├── config/                  # 配置模块
│   ├── db_config.py         # 数据库配置
│   ├── mail_config.py       # 邮件配置
│   ├── model_config.py      # 模型配置
│   ├── prompts.py           # 提示词模板
│   ├── question\            # 问题配置
│   │   ├── python开发面试问题.txt
│   │   ├── 数据分析师问题.txt
│   │   └── 通用面试问题.txt
│   └── voice_config.py      # 语音配置
├── database/                # 数据库模块
│   ├── crud.py              # 数据库操作
│   ├── database.py          # 数据库连接
│   └── models.py            # ORM 模型
├── output/                  # 视频处理输出
├── output_chart/            # 雷达图输出
├── output_reports/          # PDF 报告输出
├── question_audio/          # 问题音频输出
├── requirements.txt         # Python 依赖
├── run.py                   # 应用启动脚本
├── routes/                  # API 路由
│   ├── interview_routes.py  # 面试相关路由
│   ├── report_routes.py     # 报告相关路由
│   └── user_routes.py       # 用户相关路由
├── ui/                      # 前端界面
│   ├── *.html               # 各页面 HTML
│   └── js/*.js              # 各页面逻辑
└── utils/                   # 工具函数
    ├── Video_processing.py  # 视频处理
    ├── audio_utils.py       # 音频工具
    ├── radar_chart_generator.py # 雷达图生成
    ├── text2Audio.py        # 文本转语音
    └── to_pdf.py            # PDF 生成
    ├── audio_processing.py  # 音频处理
```

## 🚀 快速开始

### 1. 环境准备

- Python 3.8+
- FFmpeg (需要安装并将其添加到系统环境变量中)

### 2. 克隆项目

```bash
git clone <项目仓库地址>
cd ai_interview
```

### 3. 创建并激活虚拟环境

```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置环境变量

在项目根目录下创建 `.env` 文件，并填入你的 API Keys：

```env
STEPFUN_API_KEY="你的 StepFun API Key"
XF_APPID="你的讯飞开放平台 AppID"
XF_SECRET_KEY="你的讯飞开放平台 Secret Key"
```

### 6. 运行应用

```bash
python run.py
```

应用启动后，后端服务将在 `http://<你的本地IP>:8000` 上运行。你可以直接在浏览器中打开这个地址`http://<你的本地IP>:8000/ui`访问前端界面。



## 📝 功能详解

### 1. 用户注册与登录

- **文件**: `ui/index.html`, `ui/register.html`, `ui/js/login.js`, `routes/user_routes.py`
- **逻辑**: 用户通过注册页面创建账户，信息存储在 SQLite 数据库中。登录时，前端将用户信息发送到后端进行验证。为了简化流程，当前实现中，登录成功后用户信息会存储在 `localStorage` 中，以便后续 API 调用时使用。

### 2. 仪表盘

- **文件**: `ui/dashboard.html`, `ui/js/dashboard.js`
- **逻辑**: 登录后进入仪表盘页面，展示用户的面试历史统计数据，如总面试次数、平均分等。目前前端为静态展示，需要与后端 API 对接以实现动态数据加载。

### 3. 开始面试

- **文件**: `ui/interview.html`, `ui/js/interview.js`, `routes/interview_routes.py`, `agents/question_agent.py`
- **逻辑**:
    1. 用户选择面试的岗位类型。
    2. 前端请求后端生成面试问题。`question_agent` 会根据岗位类型从预设题库或通过 LLM 动态生成问题，并将其转换为音频。
    3. 前端播放问题音频，并使用 `MediaRecorder` API 录制用户的回答视频。
    4. 用户回答完毕后，视频被上传到后端。
    5. 后端 `interview_routes` 接收视频，调用 `Video_processing` 工具进行抽帧和音频提取。
    6. 提取出的多模态数据（图像、音频转写的文本）被传递给相应的 AI 分析智能体。

### 4. 多模态分析

- **文件**: `agents/*_analysis.py`, `agents/integrated_evaluator.py`
- **逻辑**:
    1. **ImageAnalysisAgent**: 分析视频关键帧，评估表情、姿态等非语言信号。
    2. **SpeechAnalysisAgent**: 分析语音转写的文本，评估语速、流畅度和情感。
    3. **TextContentAgent**: 分析回答的文本内容，评估其专业性、逻辑性和相关性。
    4. **IntegratedEvaluator**: 接收以上所有分析结果，进行综合评估，生成一个包含各项评分和文字评价的 JSON 对象。

### 5. 查看报告

- **文件**: `ui/reports.html`, `ui/js/reports.js`, `routes/report_routes.py`, `utils/radar_chart_generator.py`, `utils/to_pdf.py`
- **逻辑**:
    1. 面试分析完成后，结果保存在 `sessionStorage` 中，并跳转到报告页面。
    2. `js/reports.js` 从 `sessionStorage` 读取数据，并动态渲染到页面上，包括总分、各项得分和 AI 的详细评价。
    3. 用户点击“下载报告”时，前端会请求后端 `/generate_report/` 接口。
    4. 后端调用 `radar_chart_generator` 生成 ECharts 雷达图，并调用 `to_pdf` 将所有评估数据和图表整合到一个 PDF 文件中。
    5. 后端返回 PDF 文件的路径，前端触发下载。

## 💡 优秀的设计实践

- **配置与代码分离**: `prompts.py` 和 `model_config.py` 将易变的提示词和模型配置与核心业务逻辑分离，便于调整和优化 AI 表现。
- **缓存机制**: 在 `interview_routes.py` 中使用 `functools.lru_cache` 缓存 AI 智能体实例，避免了在每次请求时都重新创建模型对象，显著提高了性能和响应速度。
- **模块化工具**: `utils/` 目录下的工具函数（如视频处理、PDF生成）都是独立的、可重用的模块，降低了代码耦合度。
- **异步处理**: FastAPI 的异步特性使得处理耗时的 I/O 操作（如文件上传、AI 模型调用）时不会阻塞整个应用，提升了系统的并发处理能力。

## 许可证

本项目采用 MIT 许可证。