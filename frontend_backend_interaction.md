# 前后端交互文档

## 1. 项目概述

本项目是一个AI面试评估系统，旨在通过分析面试者的视频、音频和文本数据，提供多维度的AI评估报告。后端基于FastAPI框架构建，提供RESTful API接口供前端调用。前端负责用户界面展示、数据采集和结果呈现。

## 2. 整体架构

前端通过HTTP请求与后端API进行通信，后端处理业务逻辑、调用AI模型进行分析、存储数据并生成报告。静态文件（如前端UI、生成的报告、图表等）由后端提供服务。

## 3. API接口详情

以下将详细列出后端提供的API接口，包括其功能、请求方式、URL、请求参数和响应数据。

### 3.1 核心API接口

#### 用户管理接口 (`/users`)

*   **用户注册**
    *   **URL**: `/register`
    *   **方法**: `POST`
    *   **功能**: 注册新用户。
    *   **请求体**: `UserCreate` (包含 `username`, `password`, `email`)
    *   **响应**: `User` (创建成功的用户信息)
    *   **错误**: `400 Bad Request` (用户名或邮箱已存在)

*   **用户登录**
    *   **URL**: `/login`
    *   **方法**: `POST`
    *   **功能**: 用户登录并获取认证Token。
    *   **请求体**: `UserLogin` (包含 `username`, `password`)
    *   **响应**: `Token` (包含 `access_token`, `token_type`)
    *   **错误**: `401 Unauthorized` (用户名或密码错误)

*   **获取当前用户信息**
    *   **URL**: `/users/me`
    *   **方法**: `GET`
    *   **功能**: 获取当前认证用户的信息。
    *   **请求头**: `Authorization: Bearer <token>`
    *   **响应**: `User` (当前用户信息)
    *   **错误**: `401 Unauthorized` (未认证)

*   **上传用户头像**
    *   **URL**: `/upload_avatar`
    *   **方法**: `POST`
    *   **功能**: 上传用户头像。
    *   **请求体**: `UploadFile` (文件)
    *   **请求头**: `Authorization: Bearer <token>`
    *   **响应**: `JSONResponse` (包含 `message`, `avatar_url`)
    *   **错误**: `400 Bad Request` (文件类型不支持), `401 Unauthorized` (未认证)

*   **获取用户头像**
    *   **URL**: `/avatars/{filename}`
    *   **方法**: `GET`
    *   **功能**: 获取用户头像文件。
    *   **路径参数**: `filename` (str)
    *   **响应**: `FileResponse` (头像文件)
    *   **错误**: `404 Not Found` (文件不存在)

#### 面试流程接口 (`/`)

*   **生成面试问题**
    *   **URL**: `/generate_questions/`
    *   **方法**: `POST`
    *   **功能**: 根据面试类型和岗位类型生成面试问题及对应音频。
    *   **请求体**: `GenerateQuestionsRequest` (包含 `interview_type`, `job_type`)
    *   **响应**: `GenerateQuestionsResponse` (包含 `questions` (问题列表) 和 `audio_paths` (音频文件URL列表))
    *   **错误**: `500 Internal Server Error` (生成问题失败)

*   **处理面试视频**
    *   **URL**: `/process_interview/`
    *   **方法**: `POST`
    *   **功能**: 处理用户上传的面试视频，进行视频抽帧、音频提取、语音转写，并调用AI代理进行初步的图像、语音和文本分析。
    *   **请求体**: `InterviewRequest` (包含 `video_path`, `frame_interval`, `job_type`, `job_description`)
    *   **请求头**: `Authorization: Bearer <token>`
    *   **响应**: `JSONResponse` (包含 `message`, `video_filename`, `audio_filename`, `transcript_filename`, `frames_dir`)
    *   **错误**: `500 Internal Server Error` (处理失败), `401 Unauthorized` (未认证)

*   **开始对话**
    *   **URL**: `/start_conversation/`
    *   **方法**: `POST`
    *   **功能**: 开始与AI进行对话，用于模拟面试。
    *   **请求体**: `ConversationRequest` (包含 `user_id`, `job_type`, `conversation_history`)
    *   **请求头**: `Authorization: Bearer <token>`
    *   **响应**: `JSONResponse` (包含 `response` (AI的回复), `conversation_history` (更新后的对话历史))
    *   **错误**: `500 Internal Server Error` (对话失败), `401 Unauthorized` (未认证)

#### 报告生成接口 (`/generate_report/`)

*   **生成报告**
    *   **URL**: `/generate_report/`
    *   **方法**: `POST`
    *   **功能**: 根据已有的分析结果，生成PDF报告文件和雷达图，并返回下载链接。
    *   **请求体**: `GenerateReportRequest` (包含 `user_id`, `job_type`, `video_filename`, `audio_filename`, `transcript_filename`, `frames_dir`, `conversation_history`)
    *   **请求头**: `Authorization: Bearer <token>`
    *   **响应**: `JSONResponse` (包含 `pdf_report_url` (PDF报告文件URL) 和 `radar_chart_url` (雷达图HTML文件URL))
    *   **错误**: `500 Internal Server Error` (报告生成失败), `401 Unauthorized` (未认证)

### 3.2 静态文件服务

后端通过FastAPI的`StaticFiles`提供静态文件服务，主要用于前端UI、生成的报告和图表的访问。

*   `/ui`: 前端用户界面文件，对应后端 `ui` 目录。
*   `/output_reports`: 生成的PDF报告文件，对应后端 `output_reports` 目录。
*   `/output_chart`: 生成的雷达图HTML和PNG文件，对应后端 `output_chart` 目录。
*   `/audio/questions`: 面试问题音频文件，对应后端 `question_audio` 目录。

## 4. 数据模型

以下是后端主要的数据模型定义，用于请求体和响应数据。

### `User`

表示用户信息。

```python
class User(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    created_at: datetime
    avatar_url: Optional[str] = None
```

### `UserCreate`

用于用户注册的请求体。

```python
class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
```

### `UserLogin`

用于用户登录的请求体。

```python
class UserLogin(BaseModel):
    username: str
    password: str
```

### `Token`

表示认证Token。

```python
class Token(BaseModel):
    access_token: str
    token_type: str
```

### `InterviewRequest`

用于 `/process_interview/` 接口的请求体。

```python
class InterviewRequest(BaseModel):
    video_path: str  # 待处理视频的路径
    frame_interval: int = 8  # 视频帧抽取间隔（秒）
    job_type: str = 'python_engineer'  # 面试岗位类型，用于定制文本分析提示词
    job_description: Optional[str] = None  # 岗位描述，可选，可用于更精细的文本分析
```

### `ConversationRequest`

用于 `/start_conversation/` 接口的请求体。

```python
class ConversationRequest(BaseModel):
    user_id: int
    job_type: str
    conversation_history: List[Dict[str, str]]
```

### `GenerateQuestionsRequest`

用于 `/generate_questions/` 接口的请求体。

```python
class GenerateQuestionsRequest(BaseModel):
    interview_type: str
    job_type: str
```

### `GenerateQuestionsResponse`

用于 `/generate_questions/` 接口的响应体。

```python
class GenerateQuestionsResponse(BaseModel):
    questions: List[str]
    audio_paths: List[str]
```

### `GenerateReportRequest`

用于 `/generate_report/` 接口的请求体。

```python
class GenerateReportRequest(BaseModel):
    user_id: int
    job_type: str
    video_filename: str
    audio_filename: str
    transcript_filename: str
    frames_dir: str
    conversation_history: List[Dict[str, str]]
```

## 5. 交互流程示例

以下是一个典型的用户与AI面试评估系统交互的流程：

1.  **用户注册/登录**：
    *   前端调用 `/users/` (POST) 接口创建新用户或通过其他方式识别用户。

2.  **生成面试问题**：
    *   用户选择面试类型和岗位类型。
    *   前端调用 `/generate_questions/` (POST) 接口，后端根据配置生成面试问题列表和对应的音频文件URL。
    *   前端接收问题和音频URL，播放音频并展示问题。

3.  **用户录制面试视频**：
    *   用户根据问题进行回答，前端录制用户的面试视频。

4.  **处理面试视频并进行初步AI分析**：
    *   用户完成录制后，前端将视频文件上传到后端（具体上传方式可能通过其他接口或直接文件上传）。
    *   前端调用 `/process_interview/` (POST) 接口，传入视频路径、抽帧间隔、岗位类型等信息。
    *   后端处理视频（抽帧、音频提取、语音转写），并调用图像分析、语音分析、文本内容分析等AI代理进行初步评估。
    *   后端返回各项分析结果（`image_result`, `speech_result`, `text_result`, `model_predictions`）以及处理后的文件路径（`processed_video_path`, `audio_path`, `transcript_path`, `frames_dir`）。

5.  **生成并展示评估报告**：
    *   前端接收到 `/process_interview/` 返回的分析结果后，调用 `/generate_report/` (POST) 接口，传入所有分析结果和处理后的文件路径。
    *   后端根据这些结果生成详细的PDF报告和交互式雷达图。
    *   后端返回PDF报告的URL (`pdf_file_path`) 和雷达图HTML的URL (`radar_chart_path`)。
    *   前端接收到URL后，可以在页面上嵌入雷达图（通过iframe加载HTML），并提供PDF报告的下载链接。

6.  **查看历史评估结果**：
    *   用户可以调用 `/users/{user_id}/evaluations/` (GET) 或 `/users/{user_id}/evaluations/latest/` (GET) 接口来查看其历史面试评估结果。