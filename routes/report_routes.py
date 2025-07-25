from datetime import datetime
import functools
import json
import os
import random  # 尽管没有直接使用，如果其他部分需要可保留
import shutil  # 尽管没有直接使用，如果其他部分需要可保留
from typing import Dict, List, Optional
from dotenv import load_dotenv  # 确保你已经安装了 python-dotenv
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 导入你的业务逻辑模块
from agents.integrated_evaluator import IntegratedEvaluator
from utils.radar_chart_generator import generate_interactive_single_radar_chart
from utils.to_pdf import PDFGenerator

# 加载环境变量
load_dotenv()

# 从环境变量获取模型路径和API Key
MODEL_PATH = os.getenv("MODEL_PATH")
STEPFUN_API_KEY = os.getenv("STEPFUN_API_KEY")  # 确保这个变量在 .env 文件中定义

# --- AI代理实例初始化 (使用 functools.lru_cache 进行缓存) ---
# 这是一个高效的做法，确保 IntegratedEvaluator 只被初始化一次
@functools.lru_cache()
def get_integrated_evaluator_for_report():
    """
    获取并缓存综合评估代理实例，专用于报告生成，确保模型路径和 API Key 被传递。
    如果你的 get_integrated_evaluator 在其他共享模块中已经定义并缓存，
    这里应该直接导入并使用该共享实例，而不是重新定义一个。
    """
    if not STEPFUN_API_KEY:
        raise ValueError("STEPFUN_API_KEY 环境变量未设置。请检查你的 .env 文件。")
    if not MODEL_PATH:
        raise ValueError("MODEL_PATH 环境变量未设置。请检查你的 .env 文件。")
    return IntegratedEvaluator(api_key=STEPFUN_API_KEY, model_path=MODEL_PATH)

router = APIRouter()

# --- Pydantic 模型定义 (用于请求体数据验证) ---
class GenerateReportRequest(BaseModel):
    """
    定义生成报告请求的Pydantic模型。
    确保所有字段都是客户端应该发送的，并且类型匹配。
    """
    job_type: str  # 新增字段，表示面试类型
    image_result: str
    speech_result: str
    text_result: str
    conversation_history: List[Dict[str, str]]  # 更改为 List[Dict[str, str]] 以匹配前端发送的对象数组
    model_predictions: Dict[str, float]  # 辅助多模态模型生成的量化预测结果
    processed_frame_paths: List[str]  # 抽取的帧图像文件路径列表
    processed_audio_path: str  # 抽取出的音频文件路径
    processed_text_content_path: str  # 语音转写文本文件路径

# --- API 路由定义 ---
@router.post("/generate_report/")
async def generate_report_pdf_endpoint(request: GenerateReportRequest):
    """
    [API 2] 根据已有的分析结果，生成PDF报告文件并返回下载链接。
    专供“下载报告”按钮触发。
    """
    try:
        # 解构请求数据
        job_type = request.job_type
        image_result = request.image_result
        speech_result = request.speech_result
        text_result = request.text_result
        conversation_history = request.conversation_history
        model_predictions = request.model_predictions

        # 获取缓存的综合评估代理实例
        evaluator = get_integrated_evaluator_for_report()

        # --- 1. 生成雷达图数据 ---
        print("\n--- [步骤 1/2] 生成雷达图数据 ---")
        radar_chart_data = evaluator.generate_radar_chart_data(
            image_result=image_result,
            speech_result=speech_result,
            text_result=text_result,
            model_predictions=model_predictions,
            frame_paths=request.processed_frame_paths,
            audio_path=request.processed_audio_path,
            text_content_path=request.processed_text_content_path
        )
        print("\n[雷达图数据]:\n", radar_chart_data)

        # 生成雷达图图片 (PNG格式)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        radar_chart_png_path, radar_chart_html_path = generate_interactive_single_radar_chart(
            radar_chart_data,
            output_dir="output_chart",
            tag=timestamp,
            save_png=True  # PDF报告需要PNG图像
        )
        print(f"雷达图已生成：{radar_chart_png_path}")

        # --- 2. 生成PDF报告 ---
        print("\n--- [步骤 2/2] 生成PDF报告 ---")

        def format_conversation_history(history: List[Dict[str, str]]) -> str:
            lines = []
            for entry in history:
                speaker = entry.get("speaker", "未知")
                text = entry.get("text", "")
                lines.append(f"{speaker}：{text}")
            return "\n".join(lines)

        def generate_report_content(job_type, img_res, sp_res, txt_res, conv_hist_list, radar_data, model_preds) -> str:
            def format_model_predictions(predictions: Dict[str, float]) -> str:
                labels = {
                    "visual_score": "视觉表现",
                    "audio_score": "音频表现",
                    "text_score": "文本内容",
                    "overall_score": "综合得分"
                }
                lines = []
                for key, value in predictions.items():
                    label = labels.get(key, key)
                    lines.append(f"{label}：{value:.2%}")
                return "\n".join(lines)

            formatted_conv_hist = format_conversation_history(conv_hist_list)
            formatted_model_preds = format_model_predictions(model_preds)

            report_lines = [
                "AI 面试评估报告",
                "",
                f"面试类型：{job_type}",
                "",
                "=" * 40,
                "一、各项分析结果",
                "-" * 30,
                f"图像分析结果：\n{img_res}",
                "",
                f"语音分析结果：\n{sp_res}",
                "",
                f"文本内容评估结果：\n{txt_res}",
                "",
                "=" * 40,
                "二、辅助多模态模型量化分数",
                "-" * 30,
                formatted_model_preds,
                "",
                "=" * 40,
                "三、能力雷达图数据",
                "-" * 30,
                "雷达图已嵌入报告中，以下是其原始数据：",
                "",  # 空行
            ]

            # 添加雷达图数据（非 JSON 格式）
            for category, score in radar_data.items():
                report_lines.append(f"{category}：{score}")

            report_lines.extend([
                "",
                "=" * 40,
                "四、综合评估对话历史",
                "-" * 30,
                formatted_conv_hist,
                ""
            ])

            return "\n".join(report_lines)

        report_content = generate_report_content(
            job_type, image_result, speech_result, text_result,
            conversation_history, radar_chart_data, model_predictions
        )

        pdf_generator_instance = PDFGenerator()
        output_reports_dir = "output_reports"
        os.makedirs(output_reports_dir, exist_ok=True)

        pdf_file_path = pdf_generator_instance.generate(
            text=report_content,
            title="AI面试评估报告",
            output_dir=output_reports_dir,
            image_path=radar_chart_png_path
        )
        print(f"\nPDF报告已生成：{pdf_file_path}")

        # 返回PDF和雷达图的路径
        return JSONResponse(content={
            "pdf_file_path": f"/output_reports/{os.path.basename(pdf_file_path)}",
            "radar_chart_path": f"/output_chart/{os.path.basename(radar_chart_html_path)}"
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")