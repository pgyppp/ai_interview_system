from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.messages import HumanMessage, AIMessage
from config.prompts import (
    TEXT_CONTENT_PROMPT,
    TEXT_CONTENT_PROMPT_DATA_ANALYST,
    TEXT_CONTENT_PROMPT_PYTHON_ENGINEER
)
from config.model_config import MODEL_CONFIG

class TextContentAgent:
    def __init__(self, api_key=None, job_type='general'):
        model_config = MODEL_CONFIG["TextContentAgent"]
        self.llm = ChatOpenAI(
            model_name=model_config["model_name"],
            base_url=model_config["base_url"],
            api_key=api_key
        )
        self.chat_history = []

        # 根据岗位类型选择不同的提示词模板
        if job_type == 'data_analyst':
            prompt_template = TEXT_CONTENT_PROMPT_DATA_ANALYST
        elif job_type == 'python_engineer':
            prompt_template = TEXT_CONTENT_PROMPT_PYTHON_ENGINEER
        else:
            prompt_template = TEXT_CONTENT_PROMPT

        # 创建包含对话历史的提示词
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_template),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 创建 Agent
        agent = create_tool_calling_agent(self.llm, tools=[], prompt=self.prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=[])

    def analyze(self, question: str, answer_text: str, job_description: str) -> str:
        # 构建输入
        input_text = f"岗位职责: {job_description}\n面试问题: {question}\n候选人回答: {answer_text}"
        input_data = {
            "input": input_text,
            "chat_history": self.chat_history
        }

        # 调用 Agent
        stream = self.agent_executor.stream(input_data)
        full_response_content = ""
        for chunk in stream:
            if "output" in chunk and chunk["output"] is not None:
                full_response_content += chunk["output"]

        # 更新对话历史
        self.chat_history.append(HumanMessage(content=input_text))
        self.chat_history.append(AIMessage(content=full_response_content))

        return full_response_content