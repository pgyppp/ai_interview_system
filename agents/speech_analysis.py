from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from config.prompts import SPEECH_EXPRESSION_PROMPT
from config.model_config import MODEL_CONFIG

class SpeechAnalysisAgent:
    def __init__(self, api_key=None):
        model_config = MODEL_CONFIG["SpeechAnalysisAgent"]
        self.llm = ChatOpenAI(
            model_name=model_config["model_name"],
            base_url=model_config["base_url"],
            api_key=api_key
        )
        self.prompt = PromptTemplate.from_template(SPEECH_EXPRESSION_PROMPT)

    def analyze(self, transcribed_text: str) -> str:
        prompt_value = self.prompt.invoke({"transcribed_text": transcribed_text})
        stream = self.llm.stream(prompt_value.to_string())
        full_response_content = ""
        for chunk in stream:
            if chunk.content is not None:
                full_response_content += chunk.content
        return full_response_content