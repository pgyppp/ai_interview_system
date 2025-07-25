import base64
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from config.prompts import IMAGE_ANALYSIS_PROMPT
from config.model_config import MODEL_CONFIG

class ImageAnalysisAgent:
    def __init__(self, api_key=None):
        model_config = MODEL_CONFIG["ImageAnalysisAgent"]
        self.llm = ChatOpenAI(
            model_name=model_config["model_name"],
            base_url=model_config["base_url"],
            api_key=api_key
        )
        self.prompt_template = IMAGE_ANALYSIS_PROMPT

    def _encode_image(self, image_path: str) -> str:
        """将图片文件编码为Base64字符串"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except FileNotFoundError:
            return ""

    def analyze(self, image_paths: list[str], detail: str = "high") -> str:
        """分析本地图片文件列表"""
        messages_content = []
        image_urls = []

        for image_path in image_paths:
            base64_image = self._encode_image(image_path)
            if not base64_image:
                messages_content.append({"type": "text", "text": f"错误：无法读取或编码图片文件 {image_path}。"})
                continue
            image_urls.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": detail}})
        
        if not image_urls:
            return "错误：没有可用于分析的图片。"

        prompt_text = self.prompt_template.format(input_image="") # Prompt template might need adjustment for multiple images
        messages_content.append({"type": "text", "text": prompt_text})
        messages_content.extend(image_urls)
        
        # 构建包含图片的消息
        message = HumanMessage(
            content=messages_content
        )

        try:
            stream = self.llm.stream([message])
            full_response_content = ""
            for chunk in stream:
                if chunk.content is not None:
                    full_response_content += chunk.content
            return full_response_content
        except Exception as e:
            return f"调用API失败: {e}"