import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from typing import List, Dict, Optional
from config.prompts import INTEGRATED_EVALUATION_PROMPT, RADAR_CHART_PROMPT
from config.model_config import MODEL_CONFIG
from model.model.model_inference import ModelInference

class IntegratedEvaluator:
    def __init__(self, api_key=None, model_path=None):
        model_config = MODEL_CONFIG["IntegratedEvaluator"]
        self.llm = ChatOpenAI(
            model_name=model_config["model_name"],
            base_url=model_config["base_url"],
            api_key=api_key
        )
        # 这里很关键：你的 INTEGRATED_EVALUATION_PROMPT 需要有 {model_predictions} 的占位符
        self.prompt = PromptTemplate.from_template(INTEGRATED_EVALUATION_PROMPT)
        self.radar_prompt = PromptTemplate.from_template(RADAR_CHART_PROMPT)
        self.chat_history: List[Dict[str, str]] = []

        # 初始化面试辅助决策模型
        if model_path:
            self.decision_model = ModelInference(model_path)
        else:
            self.decision_model = None

    def _get_llm_response(self, prompt_input) -> str:
        """一个私有辅助方法，用于处理 LLM 的流式响应和更新聊天历史"""
        stream = self.llm.stream(prompt_input)
        full_response_content = ""
        for chunk in stream:
            if chunk.content is not None:
                full_response_content += chunk.content
        return full_response_content

    def start_conversation(self, image_result: str, speech_result: str, text_result: str,
                           model_predictions: Dict[str, float]) -> str:
        """
        使用初始分析结果和辅助模型预测结果开始对话。
        """
        model_predictions_str = json.dumps(model_predictions, indent=2, ensure_ascii=False) # 将预测结果转换为字符串，方便注入到提示词中


        initial_prompt = self.prompt.invoke({
            "image_result": image_result,
            "speech_result": speech_result,
            "text_result": text_result,
            "model_predictions": model_predictions_str # 将辅助模型预测结果添加到提示词中
        })

        full_response_content = self._get_llm_response(initial_prompt.to_string())
        self.chat_history.append({"role": "assistant", "content": full_response_content})
        return full_response_content

    def chat_with_ai(self, user_message: str, conversation_history: List[Dict[str, str]]) -> str:
        """
        与AI智能体进行对话，基于当前的对话历史。
        """
        messages = []
        for msg in conversation_history:
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                messages.append(AIMessage(content=msg['content']))
        
        messages.append(HumanMessage(content=user_message))

        full_response_content = self._get_llm_response(messages)
        return full_response_content

    def continue_conversation(self, user_message: str, conversation_history: List[Dict[str, str]],
                              image_result: str, speech_result: str, text_result: str,
                              model_predictions: Dict[str, float]) -> str:
        """
        继续与LLM的对话，并根据需要注入辅助模型预测结果。
        """
        model_predictions_str = json.dumps(model_predictions, indent=2, ensure_ascii=False)

        messages = []
        for msg in conversation_history:
            if msg['role'] == 'user':
                messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                messages.append(AIMessage(content=msg['content']))

        combined_message_content = (
            f"图像分析: {image_result}\n"
            f"语音分析: {speech_result}\n"
            f"文本分析: {text_result}\n"
            f"辅助模型预测结果：{model_predictions_str}\n"
            f"用户：{user_message}"
        )
        messages.append(HumanMessage(content=combined_message_content))

        full_response_content = self._get_llm_response(messages)
        self.chat_history.append({"role": "assistant", "content": full_response_content})
        return full_response_content

    def generate_full_report_data(self, job_type: str, image_result: str, speech_result: str, text_result: str, conversation_history: List[Dict[str, str]], model_predictions: Dict[str, float]) -> Dict:
        """
        根据所有输入数据生成完整的报告数据，返回一个可以直接用于前端渲染的字典。
        """
        model_predictions_str = json.dumps(model_predictions, indent=2, ensure_ascii=False)
        # 注意：这里假设传入的 conversation_history 是列表，但我们只用它来注入上下文，不直接返回。
        # 如果你需要在最终报告里展示对话历史，需要额外处理。
        conversation_history_str = "\n".join(conversation_history)

        # 确保 prompt 模板中包含所有需要的变量
        prompt_input = self.prompt.invoke({
            "job_type": job_type,
            "image_result": image_result,
            "speech_result": speech_result,
            "text_result": text_result,
            "conversation_history": conversation_history_str,
            "model_predictions": model_predictions_str
        })

        response_content = self._get_llm_response(prompt_input.to_string())
        print(f"LLM 原始响应内容: {response_content}")

        try:
            # 移除 markdown 代码块标记
            cleaned_content = response_content.strip()
            if cleaned_content.startswith("```json") and cleaned_content.endswith("```"):
                cleaned_content = cleaned_content[len("```json"): -len("```")].strip()

            report_data = json.loads(cleaned_content)
            print(f"解析后的报告数据: {report_data}")

            # --- 关键修改：验证新的数据结构 ---
            # 验证并修正 overall_score
            if "overall_score" not in report_data or not isinstance(report_data["overall_score"], (int, float)):
                print("警告：LLM 响应中缺少 'overall_score' 字段或其值不是数字，设置为 0。")
                report_data["overall_score"] = 0
            else:
                report_data["overall_score"] = int(report_data["overall_score"]) # 确保是整数

            # 验证并修正 score_details
            if "score_details" not in report_data or not isinstance(report_data["score_details"], dict):
                print("警告：LLM 响应中缺少 'score_details' 字段或其格式不正确，设置为 {}。")
                report_data["score_details"] = {}
            else:
                for dimension, score in report_data["score_details"].items():
                    if not isinstance(score, (int, float)) or score < 0 or score > 100:
                        print(f"警告：评分明细 '{dimension}' 的分数无效 ({score})，已修正为0-100之间。")
                        report_data["score_details"][dimension] = max(0, min(100, int(score)))

            # 验证并修正 ai_analysis
            if "ai_analysis" not in report_data or not isinstance(report_data["ai_analysis"], dict):
                print("警告：LLM 响应中缺少 'ai_analysis' 字段或其格式不正确，设置为 {}。")
                report_data["ai_analysis"] = {}
            else:
                # 确保 ai_analysis 包含前端期望的键，并提供默认值
                for key in ["综合评价", "优势", "待改进"]:
                    if key not in report_data["ai_analysis"]:
                        report_data["ai_analysis"][key] = "暂无相关信息。"

            # --- 将 conversation_history 转换为前端期望的格式并添加到返回数据中 ---
            # 前端期望的格式是 [{ speaker: 'AI', text: '...' }, { speaker: 'User', text: '...' }]
            formatted_conversation_history = []
            for msg in conversation_history:
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    formatted_conversation_history.append({"speaker": msg['role'].capitalize(), "text": msg['content']})
                elif isinstance(msg, str):
                    # 尝试从字符串解析，例如 "User: xxx" 或 "AI: yyy"
                    if msg.startswith("User:"):
                        formatted_conversation_history.append({"speaker": "User", "text": msg.replace("User:", "").strip()})
                    elif msg.startswith("AI:"):
                        formatted_conversation_history.append({"speaker": "AI", "text": msg.replace("AI:", "").strip()})
                    else:
                        formatted_conversation_history.append({"speaker": "Unknown", "text": msg.strip()})
            report_data["conversation_analysis"] = formatted_conversation_history

            # 添加 job_type 和 model_predictions 到返回数据中
            report_data["job_type"] = job_type
            report_data["model_predictions"] = model_predictions

            return report_data

        except json.JSONDecodeError as e:
            print(f"解析报告数据时出错: {e}")
            print(f"LLM 响应内容: {response_content}")
            # 返回一个带有错误信息的默认结构，防止前端崩溃
            return {
                "overall_score": 0,
                "score_details": {},
                "ai_analysis": {
                    "综合评价": "评估失败：无法解析AI返回的数据。",
                    "优势": "",
                    "待改进": ""
                },
                "conversation_analysis": [],
                "job_type": job_type,
                "model_predictions": model_predictions
            }
        except ValueError as e:
            print(f"报告数据结构验证失败: {e}")
            print(f"LLM 响应内容: {response_content}")
            return {
                "overall_score": 0,
                "score_details": {},
                "ai_analysis": {
                    "综合评价": f"评估失败：数据结构错误 - {str(e)}",
                    "优势": "",
                    "待改进": ""
                },
                "conversation_analysis": [],
                "job_type": job_type,
                "model_predictions": model_predictions
            }

    def evaluate(self, image_result: str, speech_result: str, text_result: str,
                 model_predictions: Dict[str, float]) -> str:
        """
        单一评估模式，现在可以接收辅助模型输入。
        与 start_conversation 逻辑相同，主要用于兼容旧接口。
        """
        return self.start_conversation(image_result, speech_result, text_result,
                                       model_predictions)


    def generate_radar_chart_data(self, image_result: str, speech_result: str, text_result: str,
                                  model_predictions: Optional[Dict[str, float]] = None,
                                  frame_paths: List[str] = None, audio_path: str = None, text_content_path: str = None) -> Dict[str, float]:
        """
        根据分析结果和可选的辅助模型预测结果生成雷达图数据。
        优先使用传入的 model_predictions；如果未提供，则根据文件路径运行辅助决策模型。
        """
        model_predictions_str = "无辅助模型预测结果。" # 默认值

        if model_predictions:
            print("使用传入的辅助模型预测结果生成雷达图数据...")
            model_predictions_str = json.dumps(model_predictions, indent=2, ensure_ascii=False)
        elif self.decision_model and frame_paths and audio_path and text_content_path:
            print("未传入辅助模型预测结果，正在使用辅助决策模型进行雷达图数据预测...")
            predictions = self.decision_model.predict(frame_paths, audio_path, text_content_path)
            model_predictions_str = json.dumps(predictions, indent=2, ensure_ascii=False)
        else:
            if self.decision_model:
                 print("未提供完整的辅助模型输入路径 (frame_paths, audio_path, text_content_path) 且未传入 model_predictions，跳过辅助模型预测雷达图数据。")
            else:
                 print("辅助决策模型未初始化，跳过辅助模型预测雷达图数据。")

        radar_prompt = self.radar_prompt
        prompt_input = radar_prompt.invoke({
            "image_result": image_result,
            "speech_result": speech_result,
            "text_result": text_result,
            "model_predictions": model_predictions_str # 将辅助模型预测结果添加到雷达图提示词中
        })
        response = self.llm.invoke(prompt_input.to_string())
        try:
            # 去除 markdown 代码块标记
            content = response.content.strip()
            if content.startswith("```json") and content.endswith("```"):
                content = content[len("```json"): -len("```")].strip()
            radar_data = json.loads(content)
            expected_keys = ["肢体语言", "表情管理", "语速", "流畅度", "专业知识", "逻辑性"]
            for key in expected_keys:
                if key not in radar_data or not isinstance(radar_data[key], (int, float)):
                    print(f"警告：雷达数据中缺少或无效的键 '{key}'。设置为 0。")
                    radar_data[key] = 0.0
                else:
                    radar_data[key] = float(radar_data[key])
            return radar_data
        except json.JSONDecodeError as e:
            print(f"解码雷达图数据时出错: {e}")
            print(f"LLM 响应内容: {response.content}")
            return {"肢体语言": 0.0, "表情管理": 0.0, "语速": 0.0, "流畅度": 0.0, "专业知识": 0.0, "逻辑性": 0.0}