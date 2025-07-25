from datetime import datetime
from datetime import datetime
import functools
import json
import logging
import os
import random
import shutil
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agents.image_analysis import ImageAnalysisAgent
from agents.integrated_evaluator import IntegratedEvaluator
from agents.integrated_evaluator import IntegratedEvaluator
from agents.question_agent import InterviewQuestionAgent
from agents.speech_analysis import SpeechAnalysisAgent
from agents.text_analysis import TextContentAgent
from utils.Video_processing import InterviewProcessor
from utils.radar_chart_generator import generate_interactive_single_radar_chart
from utils.to_pdf import PDFGenerator # 导入functools，用于缓存代理实例

# --- 配置与初始化 ---
UPLOAD_DIR = "./user_uploads"  # 视频保存目录
# 确保视频上传目录存在，如果不存在则创建
os.makedirs(UPLOAD_DIR, exist_ok=True)

load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH")

# 从环境变量加载API Key，用于大模型服务（如StepFun、讯飞等）
STEPFUN_API_KEY = os.getenv("STEPFUN_API_KEY")
XF_APPID = os.getenv("XF_APPID")
XF_SECRET_KEY = os.getenv("XF_SECRET_KEY")


router = APIRouter()

# --- AI代理实例初始化 (优化改进) ---
# 使用 @functools.lru_cache() 装饰器来缓存代理实例
# 这样，每个代理只会在首次被调用时初始化一次，后续调用将直接返回缓存的实例，
# 大大提高性能，避免重复加载大型模型。

@functools.lru_cache()
def get_image_analysis_agent():
    """获取并缓存图像分析代理实例"""
    return ImageAnalysisAgent(api_key=STEPFUN_API_KEY)

@functools.lru_cache()
def get_speech_analysis_agent():
    """获取并缓存语音分析代理实例"""
    return SpeechAnalysisAgent(api_key=STEPFUN_API_KEY)

@functools.lru_cache()
def get_text_content_agent(job_type: str = 'python_engineer'):
    """
    获取并缓存文本内容分析代理实例。
    TextContentAgent 可能会根据 job_type 动态加载不同的提示词，
    因此 job_type 作为参数保留，但 lru_cache 仍能处理不同参数的缓存。
    """
    return TextContentAgent(api_key=STEPFUN_API_KEY, job_type=job_type)

@functools.lru_cache()
def get_integrated_evaluator():
    """获取并缓存综合评估代理实例，它包含了面试辅助决策模型（HireNet）"""
    return IntegratedEvaluator(api_key=STEPFUN_API_KEY, model_path=MODEL_PATH)

# --- Pydantic 模型定义 (用于请求体数据验证) ---

class InterviewRequest(BaseModel):
    """定义处理面试视频请求的Pydantic模型"""
    video_path: str # 待处理视频的路径
    frame_interval: int = 8 # 视频帧抽取间隔（秒）
    job_type: str = 'python_engineer' # 面试岗位类型，用于定制文本分析提示词
    job_description: Optional[str] = None # 岗位描述，可选，可用于更精细的文本分析

class InitialConversationRequest(BaseModel):
    image_result: str
    speech_result: str
    text_result: str
    conversation_history: List[Dict[str, str]]
    model_predictions: Dict[str, float]

class GenerateQuestionsRequest(BaseModel):
    interview_type: str
    job_type: str

class ContinueConversationRequest(BaseModel):
    user_message: str
    conversation_history: List[Dict[str, str]]
    image_result: str
    speech_result: str
    text_result: str
    model_predictions: Dict[str, float]

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []

class GenerateQuestionsResponse(BaseModel):
    questions: List[str]
    audio_paths: List[str]

# --- API 路由定义 ---

@router.post("/generate_questions/")
@router.post("/generate_questions", response_model=GenerateQuestionsResponse)
async def generate_questions_endpoint(request: GenerateQuestionsRequest):
    try:
        # 根据 interview_type 和 job_type 初始化 InterviewQuestionAgent
        # 注意：目前 InterviewQuestionAgent 主要根据 job_type 选择问题文件
        # interview_type 可以在未来用于更复杂的逻辑，例如选择不同类型的面试问题集
        logging.info(f"Received job_type from frontend: {request.job_type}")
        question_agent = InterviewQuestionAgent(api_key=STEPFUN_API_KEY, job_type=request.job_type)
        # 假设 generate_questions 方法不需要 interview_type，或者其内部已处理
        # 如果需要，这里可能需要调整 generate_questions 的调用参数
        questions, audio_paths = question_agent.generate_questions() # 假设默认生成问题，不再需要 num_questions 和 use_llm 参数
        logging.info(f"生成的问题: {questions}")
        logging.info(f"生成的音频路径: {audio_paths}")

        # 将本地文件路径转换为可访问的URL路径
        base_audio_url = "/audio/questions/"
        # 假设question_audio_paths中的路径是绝对路径，我们需要将其转换为相对路径
        # 例如：e:/比赛/挑战杯-ai面试/ai_interview/question_audio/question_0_hash.wav
        # 转换为：/audio/questions/question_0_hash.wav
        # 提取文件名部分
        relative_audio_paths = [base_audio_url + os.path.basename(p) for p in audio_paths]

        return JSONResponse(content={"questions": questions, "audio_paths": relative_audio_paths})
    except Exception as e:
        logging.error(f"生成问题失败: {e}", exc_info=True) # 添加 exc_info=True 打印详细堆栈信息
        raise HTTPException(status_code=500, detail=f"生成问题失败: {e}")

@router.post("/process_interview/")
async def process_interview_endpoint(request: InterviewRequest):
    """
    处理上传的面试视频：进行视频抽帧、音频提取、语音转写，
    并调用各个AI代理进行初步的图像、语音和文本分析。
    最后返回各项分析结果及处理后的文件路径。
    """
    try:
        # 获取缓存的AI代理实例
        image_agent = get_image_analysis_agent()
        speech_agent = get_speech_analysis_agent()
        # 根据请求中的 job_type 获取文本分析代理
        text_agent = get_text_content_agent(request.job_type)
        # 获取综合评估代理实例，用于辅助模型预测
        evaluator = get_integrated_evaluator()

        # --- 1. 视频处理 ---
        print("--- [步骤 1/3] 开始处理面试视频 ---")
        processor = InterviewProcessor(
            video_path=request.video_path,
            appid=XF_APPID, # 讯飞开放平台 AppID
            secret_key=XF_SECRET_KEY, # 讯飞开放平台 Secret Key
            frame_interval=request.frame_interval # 抽帧间隔
        )
        processor.run_pipeline() # 执行视频处理管线（抽帧、提取音频、语音转写）

        # --- 2. 加载处理后的数据 ---
        print("\n--- [步骤 2/3] 加载处理后的数据用于分析 ---")
        # 读取语音转写文本内容
        try:
            with open(processor.text_output_path, 'r', encoding='utf-8') as f:
                transcript = f.read()
            print(f"成功加载语音转写文本，共 {len(transcript)} 字。")
        except FileNotFoundError:
            print(f"错误：找不到转写文件 {processor.text_output_path}")
            transcript = "" # 如果文件不存在，则文本为空

        # 获取抽取的帧图像文件路径，并随机选择最多5张用于分析
        frame_files = os.listdir(processor.frames_output_dir)
        if not frame_files:
            print(f"错误：在 {processor.frames_output_dir} 中找不到任何帧图像。")
            selected_frame_paths = []
        else:
            num_images_to_select = min(5, len(frame_files)) # 最多选择5张
            selected_frames = random.sample(frame_files, num_images_to_select) # 随机采样
            selected_frame_paths = [os.path.join(processor.frames_output_dir, f) for f in selected_frames]
            print(f"随机选择 {num_images_to_select} 张帧图像进行分析：{selected_frame_paths}")

        # --- 3. 运行AI智能体进行多维度评估 ---
        print("\n--- [步骤 3/3] 开始进行多维度AI评估 ---")

        # a. 图像分析（表情、姿势、眼神交流）
        if selected_frame_paths:
            image_result = image_agent.analyze(selected_frame_paths)
            print("\n[图像分析结果]:\n", image_result)
        else:
            image_result = "无法进行图像分析，因为没有找到帧图像。"
            print("\n[图像分析结果]:\n", image_result)

        # b. 语音分析（语速、流畅度、情绪）
        speech_result = speech_agent.analyze(transcript)
        print("\n[语音分析结果]:\n", speech_result)

        # c. 文本内容分析（专业能力、逻辑性、切题性）
        job_description_py = request.job_description if request.job_description else ""
        # 这里的 'question' 是一个示例问题。在实际多轮面试中，这个问题可能来自LLM或预设。
        # 目前用于驱动 TextContentAgent 的分析。
        question = "请根据你的项目经验，谈谈你对Python Web开发、数据库使用以及性能优化方面的理解。"
        # TextContentAgent 会根据其 job_type 内部选择合适的提示词进行分析
        text_result = text_agent.analyze(question, transcript, job_description_py)
        print(f"\n[文本内容评估结果]:\n{text_result}")

        # d. 获取辅助模型的预测结果
        # 只有当所有必要的输入都存在时才进行预测
        if selected_frame_paths and processor.audio_output_path and processor.text_output_path:
            model_predictions = evaluator.decision_model.predict(
                frame_paths=selected_frame_paths,
                audio_path=processor.audio_output_path,
                text_content_path=processor.text_output_path
            )
            print(f"\n[辅助模型预测结果]:\n{model_predictions}")
        else:
            model_predictions = {}
            print("\n[辅助模型预测结果]: 缺少必要输入，跳过预测。")

        # 将所有初步分析结果、处理后的文件路径和辅助模型预测结果返回给客户端。
        # 客户端随后会使用这些数据来调用 /start_conversation/ 以启动综合评估和多轮对话。
        return JSONResponse(content={
            "image_result": image_result,
            "speech_result": speech_result,
            "text_result": text_result,
            "transcript": transcript, # 原始语音转写文本（内容）
            "selected_frame_paths": selected_frame_paths, # 供辅助模型使用的帧图像路径列表
            "audio_output_path": processor.audio_output_path, # 供辅助模型使用的音频文件路径
            "text_output_path": processor.text_output_path, # 供辅助模型使用的转写文本文件路径
            "model_predictions": model_predictions # 添加辅助模型的预测结果
        })
    except Exception as e:
        # 打印完整的错误栈，有助于调试
        import traceback
        traceback.print_exc()
        # 抛出HTTP异常，返回500状态码和错误信息
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload_video/")
async def upload_video_endpoint(file: UploadFile = File(...)):
    """
    接收客户端上传的视频文件，并将其保存到指定目录。
    返回保存后的文件路径。
    """
    try:
        # 生成一个唯一的文件名，防止文件覆盖冲突
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{timestamp}_{file.filename}"
        file_location = os.path.join(UPLOAD_DIR, unique_filename)

        # 将上传的文件内容写入到本地文件
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer) # 使用 shutil.copyfileobj 进行高效文件拷贝
        return JSONResponse(content={
            "message": f"文件 '{file.filename}' 上传成功",
            "file_path": file_location # 返回保存的文件路径
        })
    except Exception as e:
        import traceback
        print(f"文件上传失败: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.post("/start_conversation/")
async def start_conversation_endpoint(
    request: InitialConversationRequest,
    evaluator: IntegratedEvaluator = Depends(get_integrated_evaluator)
):
    """
    启动AI面试官与用户的对话。
    """
    try:
        initial_response = evaluator.start_conversation(
            image_result=request.image_result,
            speech_result=request.speech_result,
            text_result=request.text_result,
            model_predictions=request.model_predictions
        )
        return JSONResponse(content={
            "initial_response": initial_response,
            "conversation_history": request.conversation_history + [{"role": "assistant", "content": initial_response}] # 返回包含初始对话的完整对话历史
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/continue_conversation/")
async def continue_conversation_endpoint(
    request: ContinueConversationRequest,
    evaluator: IntegratedEvaluator = Depends(get_integrated_evaluator)
):
    """
    继续AI面试官与用户的对话。
    """
    try:
        current_response = evaluator.continue_conversation(
            user_message=request.user_message,
            conversation_history=request.conversation_history,
            image_result=request.image_result,
            speech_result=request.speech_result,
            text_result=request.text_result,
            model_predictions=request.model_predictions
        )
        return JSONResponse(content={
            "current_response": current_response,
            "updated_conversation_history": request.conversation_history + [{"role": "user", "content": request.user_message}, {"role": "assistant", "content": current_response}]
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat_with_ai/")
async def chat_with_ai_endpoint(
    request: ChatRequest,
    evaluator: IntegratedEvaluator = Depends(get_integrated_evaluator)
):
    """
    与AI智能体进行对话。
    """
    try:
        # 调用 IntegratedEvaluator 的 chat_with_ai 方法
        ai_reply = evaluator.chat_with_ai(
            user_message=request.message,
            conversation_history=request.conversation_history
        )
        return JSONResponse(content={
            "reply": ai_reply,
            "conversation_history": request.conversation_history + [{"role": "user", "content": request.message}, {"role": "assistant", "content": ai_reply}]
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# --- Pydantic 模型定义 (用于请求体数据验证) ---
class GenerateReportRequest(BaseModel):
    """
    定义生成报告请求的Pydantic模型。
    确保所有字段都是客户端应该发送的，并且类型匹配。
    """
    job_type: str # 新增字段，表示面试类型
    image_result: str
    speech_result: str
    text_result: str
    # conversation_history: 完整的聊天历史，例如 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    # 注意：JS中的 conversationHistory 当前是字符串数组，需要调整为对象数组或在后端处理
    # 为了匹配前端当前发送的简单字符串数组，我们先将其改为 List[str]，
    # 但更推荐前端发送 List[Dict[str, str]]
    conversation_history: List[str] # 更改为 List[str] 以匹配你当前JS的 `conversationHistory.push(``[用户]:\n${input}``);`

    model_predictions: Dict[str, float] # 辅助多模态模型生成的量化预测结果

    # 如果雷达图生成依赖于重新运行辅助模型，则还需要以下路径。
    # 这些路径应该是从 /process_interview/ 返回的。
    processed_frame_paths: List[str] # 抽取的帧图像文件路径列表
    processed_audio_path: str # 抽取出的音频文件路径
    processed_text_content_path: str # 语音转写文本文件路径

# --- API 路由定义 ---
@router.post("/analyze_for_report/")
async def analyze_for_report(request: GenerateReportRequest):
    """
    [API 1] 仅进行数据分析和评估，不生成文件。
    用于前端页面首次加载，获取数据以动态渲染HTML。
    """
    try:
        evaluator = get_integrated_evaluator()

        # 调用新的方法生成所有报告数据
        report_data = evaluator.generate_full_report_data(
            job_type=request.job_type,
            image_result=request.image_result,
            speech_result=request.speech_result,
            text_result=request.text_result,
            conversation_history=request.conversation_history,
            model_predictions=request.model_predictions
        )

        # print("[数据]:\n", report_data)

        if not report_data:
            raise HTTPException(status_code=500, detail="分析失败：未能从LLM获取有效数据。")

        # 返回所有分析数据，不生成文件
        return JSONResponse(content=report_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

