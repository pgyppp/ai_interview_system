import random
import logging
import os
import hashlib
from typing import List
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSequence
from config.prompts import QUESTION_AGENT_PROMPT
from config.model_config import MODEL_CONFIG
from utils.text2Audio import run_tts

# 配置日志
# 设置日志级别为 INFO，并定义日志输出格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class InterviewQuestionAgent:
    """
    面试问题生成代理类。
    根据不同的岗位类型，智能体可以自主决定从预设文件加载问题或通过大型语言模型(LLM)动态生成问题。
    """
    def __init__(self, api_key: str = None, job_type: str = 'general'):
        """
        初始化面试问题生成代理。

        Args:
            api_key (str, optional): OpenAI API 密钥。如果模型需要认证，则必须提供。默认为 None。
            job_type (str): 面试的岗位类型，例如 'python_engineer', 'data_analyst', 'general'。
                            这将决定加载哪个问题文件或指导LLM生成问题。默认为 'general'。
        """
        # 从 MODEL_CONFIG 中获取面试问题代理的模型配置
        model_config = MODEL_CONFIG["InterviewQuestionAgent"]
        # 初始化 LangChain 的 ChatOpenAI 模型
        self.llm = ChatOpenAI(
            model_name=model_config["model_name"],  # 指定使用的模型名称
            base_url=model_config["base_url"],      # 指定模型的基础URL，可用于代理或自定义API
            api_key=api_key                          # 传入API密钥进行认证
        )
        self.job_type = job_type  # 设置当前面试的岗位类型
        logging.info(f"InterviewQuestionAgent initialized with job_type: {self.job_type}")
        # 定义不同岗位类型对应的问题文件路径
        self.question_files = {
            'python_engineer': 'config/question/python开发面试问题.txt',
            'data_analyst': 'config/question/数据分析师问题.txt',
            'general': 'config/question/通用面试问题.txt'
        }
        # 初始化智能体
        self._initialize_agent()

    def _initialize_agent(self):
        """初始化能够自主调用工具的智能体"""
        
        # 创建工具函数 - 使用函数而不是方法
        @tool("load_questions")
        def load_questions_tool(job_type: str = "general", num_questions: int = 10) -> List[str]:
            """
            从指定岗位类型的文件中随机加载面试问题。

            Args:
                job_type (str): 面试的岗位类型，默认为 'general'
                num_questions (int): 需要随机获取的问题数量，默认为10

            Returns:
                list[str]: 从文件中随机读取的问题列表
            """
            return self._load_questions_from_file_internal(job_type, num_questions)
        
        # 将工具添加到工具列表
        self.tools = [load_questions_tool]
        
        # 检查 QUESTION_AGENT_PROMPT 是否为字符串，如果是则转换为 ChatPromptTemplate
        if isinstance(QUESTION_AGENT_PROMPT, str):
            # 创建一个包含系统消息和用户消息的 ChatPromptTemplate
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", QUESTION_AGENT_PROMPT),
                ("human", "岗位类型: {job_type}\n需要问题数量: {num_questions}\n可用的问题文件类型: {question_files_available}"),
                ("placeholder", "{agent_scratchpad}")
            ])
        else:
            # 如果已经是 ChatPromptTemplate 对象，直接使用
            prompt_template = QUESTION_AGENT_PROMPT
        
        # 创建工具调用智能体
        agent = create_tool_calling_agent(
            self.llm,
            self.tools,
            prompt_template,
        )
        # 创建智能体执行器
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False
        )

    def _load_questions_from_file_internal(self, job_type: str = "general", num_questions: int = 10) -> List[str]:
        """
        内部方法：从指定岗位类型的文件中随机加载面试问题。

        Args:
            job_type (str): 面试的岗位类型，默认为 'general'
            num_questions (int): 需要随机获取的问题数量，默认为10

        Returns:
            list[str]: 从文件中随机读取的问题列表
        """
        # 修正相对路径问题，确保从项目根目录开始查找
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, self.question_files.get(job_type, self.question_files['general']))
        logging.info(f"Attempting to load questions for job_type: {job_type} from filepath: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                # 读取文件所有行，去除首尾空白符，并过滤空行
                all_questions = [line.strip() for line in f if line.strip()]
            
            if not all_questions:
                logging.warning(f"文件 {filepath} 为空或未找到。")
                return []
                
            # 随机选择指定数量的问题
            selected_questions = random.sample(all_questions, min(num_questions, len(all_questions)))
            logging.info(f"从文件 {filepath} 中随机选择了 {len(selected_questions)} 个问题。")
            return selected_questions
        except FileNotFoundError:
            # 如果文件未找到，记录警告并返回空列表
            logging.warning(f"文件 {filepath} 未找到。")
            return []
        except Exception as e:
            # 捕获其他可能的读取错误
            logging.error(f"读取文件 {filepath} 时发生错误: {e}")
            return []

    def _generate_questions_with_agent(self, num_questions: int) -> list[str]:
        """
        使用智能体自主调用工具生成面试问题。

        Args:
            num_questions (int): 需要生成的问题数量。

        Returns:
            list[str]: 生成的面试问题列表。
        """
        try:
            # 构建智能体输入
            agent_input = {
                "job_type": self.job_type,
                "num_questions": num_questions,
                "question_files_available": list(self.question_files.keys())
            }
            
            # 执行智能体
            response = self.agent_executor.invoke(agent_input)
            
            # 解析智能体的响应内容
            # 智能体返回的response可能是一个字典，其键为'output'
            if isinstance(response, dict) and 'output' in response:
                # 如果输出是列表，直接使用
                if isinstance(response['output'], list):
                    generated_questions = response['output']
                else:
                    # 如果输出是字符串，按行分割
                    generated_questions = [line.strip() for line in str(response['output']).strip().split('\n') if line.strip()]
            else:
                # 如果响应是列表，直接使用
                if isinstance(response, list):
                    generated_questions = response
                else:
                    # 如果响应是字符串，按行分割
                    generated_questions = [line.strip() for line in str(response).strip().split('\n') if line.strip()]
            
            # 过滤掉可能包含引导语或错误编号的行
            filtered_questions = []
            import re
            for q in generated_questions:
                # 移除开头的数字编号（如 "1. "）或 "以下是针对..." 这样的引导语
                cleaned_q = re.sub(r'^\d+\.\s*', '', q).strip() # 移除 "1. " 这种格式
                if not cleaned_q.startswith("以下是针对") and cleaned_q: # 过滤掉 "以下是针对..." 这种引导语
                    filtered_questions.append(cleaned_q)
            
            generated_questions = filtered_questions

            logging.info(f"智能体生成了 {len(generated_questions)} 个问题。")
            return generated_questions
        except Exception as e:
            # 捕获智能体执行过程中可能发生的错误，并打印详细堆栈信息
            logging.error(f"智能体生成问题失败: {e}", exc_info=True) # exc_info=True 会打印堆栈信息
            return []

    def generate_questions(self, time_limit_per_question: float = 1.25) -> tuple[list[str], list[str]]:
        """
        生成面试问题。

        Args:
            time_limit_per_question (float): 每道题预估的回答时间（分钟）。用于估算总面试时间。默认为1.25分钟。

        Returns:
            tuple[list[str], list[str]]: 包含"自我介绍"在内的面试问题列表和对应的音频文件路径列表。
        """
        # 默认生成4个问题，如果需要更多或更少，可以在前端控制或通过其他参数传递
        num_questions = 4
        # 默认使用智能体生成问题，如果需要从文件中加载，可以在前端控制或通过其他参数传递
        use_agent = True
        
        # 所有面试默认包含自我介绍
        questions = ["请做个自我介绍"]
        question_audio_paths = [] # 新增列表用于存储语音文件路径

        if use_agent:
            # 如果选择使用智能体生成问题
            generated = self._generate_questions_with_agent(num_questions)
            # 将智能体生成的问题添加到列表中，确保不超过指定的数量
            questions.extend(generated[:num_questions])
            if not generated:
                logging.warning("智能体未能生成问题，将尝试从文件中加载通用问题作为备用。")
                # 智能体生成失败时，尝试回退到通用文件问题
                file_questions = self._load_questions_from_file_internal(self.job_type, num_questions)
                # 如果特定岗位的问题文件为空或未找到，则尝试回退到通用问题
                if not file_questions:
                    logging.warning(f"在岗位 '{self.job_type}' 的问题文件中未找到问题，将尝试加载通用问题。")
                    file_questions = self._load_questions_from_file_internal("general", num_questions)
                questions.extend(file_questions[:num_questions])
        else:
            # 如果不使用智能体，则从文件中加载问题
            # 先从题库中随机获取10个左右的问题
            file_questions = self._load_questions_from_file_internal(self.job_type, 10)
            
            # 如果特定岗位的问题文件为空或未找到，则尝试回退到通用问题
            if not file_questions:
                logging.warning(f"在岗位 '{self.job_type}' 的问题文件中未找到问题，将尝试加载通用问题。")
                file_questions = self._load_questions_from_file_internal("general", 10)

            # 如果即使通用问题文件也为空，则记录错误
            if not file_questions:
                logging.error("没有可用的问题文件，无法选择面试问题。")
            else:
                # 从随机获取的问题中再选择指定数量的问题
                selected = random.sample(file_questions, min(num_questions, len(file_questions)))
                questions.extend(selected)

        # 将生成的问题转换为语音并保存
        # 修正相对路径问题，确保从项目根目录开始查找
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        audio_dir = os.path.join(base_dir, "question_audio")
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)

        for i, question_text in enumerate(questions):
            # 使用问题内容的哈希值作为文件名，确保唯一性
            file_hash = hashlib.md5(question_text.encode('utf-8')).hexdigest()
            audio_filename = f"question_{i}_{file_hash}.wav"
            audio_filepath = os.path.join(audio_dir, audio_filename)
            
            # 异步调用 run_tts，避免阻塞主线程
            # 注意：run_tts 内部已经使用了线程，这里不需要额外开线程
            run_tts(question_text, audio_filepath)
            question_audio_paths.append(audio_filepath)
            logging.info(f"问题 '{question_text}' 的语音文件已保存到: {audio_filepath}")

        # 计算总的面试预估时间
        total_time = len(questions) * time_limit_per_question
        logging.info(f"总问题数: {len(questions)}，预估总时长: {total_time:.2f} 分钟。")

        # 返回问题列表和语音文件路径列表
        return questions, question_audio_paths