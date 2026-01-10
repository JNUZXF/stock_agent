
import os
import json
import random
import openai
import arxiv

import pysnowball as ball
from openai import OpenAI
from textwrap import dedent
from datetime import datetime
from dotenv import load_dotenv

from write_code_tools import *

from typing import Generator, Dict, Any, Optional, List

INFO_TEMPLATE = dedent(
    """
    cash_flow:
    {cash_flow}
    ---

    income:
    {income}
    ----

    business:
    {business}
    ----

    top_holders:
    {top_holders}
    ---

    main_indicator:
    {main_indicator}
    ---

    org_holding_change:
    {org_holding_change}
    ---

    industry_compare:
    {industry_compare}
    """
).strip()


STOCK_AGENT_PROMPT = dedent(
    """
    # 你的角色
    你是股票分析专家，严谨、专业、准确。你必须输出高质量的股票分析报告。

    # 股票代码注意
    - 必须是类似SZ000001,SH600519这样的股票代码


    """
).strip()

load_dotenv()
xq_a_token = os.getenv("xq_a_token")
ball.set_token(f"xq_a_token={xq_a_token}")

model = "doubao-seed-1-6-251015"
DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY")

client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=DOUBAO_API_KEY,
)

def get_doubao_answer(
    query: str,
    system_prompt: str = None,
    stream: bool = True,
    thinking: bool = "disabled",
):
    messages = []
    if system_prompt is None:
        system_prompt = "你必须严格遵守我的要求。"

    system_message = {"role": "system", "content": system_prompt}
    user_message = {"role": "user", "content": query}
    messages.append(system_message)
    messages.append(user_message)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=stream,
        extra_body={"thinking": {"type": thinking}}
    )
    responses = []
    answer = ""
    for chunk in response:
        responses.append(chunk)
        if chunk.choices[0].delta.content:
            char = chunk.choices[0].delta.content
            answer += char
            print(char, end="", flush=True)
    return answer

def get_stock_info(symbol: str):
    cash_flow = ball.cash_flow(symbol)["data"]["list"]
    income = ball.income(symbol=symbol,is_annals=1,count=1)["data"]["list"]
    # 主营业务构成
    business = ball.business(symbol=symbol,count=1)["data"]["list"]
    # 十大股东
    top_holders = ball.top_holders(symbol=symbol,circula=0)["data"]["items"]
    # 主要指标
    main_indicator = ball.main_indicator(symbol)["data"]
    # 机构持仓
    org_holding_change = ball.org_holding_change(symbol)["data"]["items"]
    # 行业对比
    industry_compare = ball.industry_compare(symbol)["data"]
    info = INFO_TEMPLATE.format(
        cash_flow=cash_flow,
        income=income,
        business=business,
        top_holders=top_holders,
        main_indicator=main_indicator,
        org_holding_change=org_holding_change,
        industry_compare=industry_compare
    )

    return info

def generate_conversation_id() -> str:
    """
    生成基于时间戳和随机数的会话ID
    格式: yyyymmdd-hhmmss+随机字符串（5位随机数字）
    
    Returns:
        str: 格式化的会话ID，例如 "20240115-14305212345"
    """
    now = datetime.now()
    # 格式化时间部分: yyyymmdd-hhmmss
    time_part = now.strftime("%Y%m%d-%H%M%S")
    # 生成5位随机数字
    random_part = random.randint(10000, 99999)
    # 组合成完整ID
    conversation_id = f"{time_part}{random_part}"
    return conversation_id


# -------------------- 工具定义 --------------------

class ArxivPaperTool:
    """arXiv 论文搜索工具"""
    
    @staticmethod
    def execute(**kwargs) -> str:
        """
        获取 arxiv 最新的 n 篇与关键词相关的论文。
        
        Args:
            query: 搜索关键词（必须是英文）
            num_papers: 最大搜索结果数
            
        Returns:
            格式化的论文信息字符串
            
        Raises:
            ValueError: 当 query 为空或 num_papers 无效时
        """
        query = kwargs["query"]
        num_papers = kwargs["num_papers"]

        if not query:
            raise ValueError("query 不能为空")
        if num_papers <= 0:
            raise ValueError("num_papers 必须为正整数")

        search = arxiv.Search(
            query=query,
            max_results=num_papers,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        client = arxiv.Client()
        papers = []

        for result in client.results(search):
            author_names = [
                author.name if hasattr(author, "name") else str(author) 
                for author in result.authors
            ]
            submitted_at = (
                result.published.strftime("%Y-%m-%d") 
                if result.published else "未知"
            )

            paper_info = [
                f"标题: {result.title.strip()}",
                f"作者: {', '.join(author_names)}" if author_names else "作者: 未知",
                f"摘要: {result.summary.strip()}",
                f"提交日期: {submitted_at}",
                f"链接: {result.entry_id}",
                "-" * 80,
            ]

            papers.append("\n".join(paper_info))

        return "\n\n".join(papers)

class modular_coding:
    @staticmethod
    def execute(**kwargs) -> str:
        """
        根据需求，撰写项目架构中的某一个文件的代码
        """
        conversation_dir = kwargs["conversation_dir"]
        model = kwargs["model"]
        # 获取conversation_dir下面的PDF文件的绝对地址
        all_codes = ""
        for char in write_codebase(conversation_dir, model):
            all_codes += char
            yield char
        # 将answer写入文件
        folder_path = os.path.join(conversation_dir, "code")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        now = datetime.now()
        # 格式化时间部分: yyyymmdd-hhmmss
        time_part = now.strftime("%Y%m%d-%H%M%S")
        file_path = os.path.join(folder_path, f"code-{time_part}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(all_codes, indent=4))

class StockAnalysisTool:
    """
    股票分析
    """
    
    @staticmethod
    def execute(symbol: str) -> str:
        """
        获取股票信息。
        
        Args:
            symbol: 股票代码
            
        Returns:
            格式化的股票信息字符串
            
        Raises:
            ValueError: 当 symbol 为空或无效时
        """

        stock_info = get_stock_info(symbol)
        return stock_info




class StockAnalysisAgent:
    """股票分析智能体
    
    支持根据用户问题自主判断是否需要调用工具，并返回流式响应。
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://ark.cn-beijing.volces.com/api/v3",
        model: str = "doubao-seed-1-6-251015",
        conversation_id: Optional[str] = None,

    ):
        """
        初始化智能体
        
        Args:
            api_key: Doubao API 密钥，若为 None 则从环境变量读取
            base_url: API 服务地址
            model: 使用的模型名称
            conversation_id: 会话ID，若为 None 则自动生成
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("DOUBAO_API_KEY")
        self.base_url = base_url
        self.model = model
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        
        # 生成或使用提供的会话ID
        self.conversation_id = conversation_id or generate_conversation_id()
        
        # 创建会话文件夹
        self.files_dir = "files"
        self.conversation_dir = os.path.join(self.files_dir, self.conversation_id)
        os.makedirs(self.conversation_dir, exist_ok=True)
        
        # 对话记录存储
        self.conversations: List[Dict[str, str]] = [
            {"role": "system", "content": STOCK_AGENT_PROMPT}
        ]
        
        # 定义可用工具
        self.tools = self._define_tools()
        
        # 工具名称到执行函数的映射
        self.tool_executors = {
            "get_stock_info": StockAnalysisTool.execute,
        }

    def _define_tools(self) -> List[Dict[str, Any]]:
        """定义可用的工具列表"""
        return [
            {
                "type": "function",
                "name": "get_stock_info",
                "description": "获取股票信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {
                            "type": "string",
                            "description": "股票代码，例如: SH600519",
                        },
                    },
                    "required": ["symbol"],
                },
            }
        ]

    def _execute_tool(self, tool_name: str, tool_arguments: Dict[str, Any]) -> str:
        """
        执行指定的工具
        
        Args:
            tool_name: 工具名称
            tool_arguments: 工具参数
            
        Returns:
            工具执行结果
            
        Raises:
            ValueError: 当工具不存在时
        """
        if tool_name not in self.tool_executors:
            raise ValueError(f"未知的工具: {tool_name}")
        
        executor = self.tool_executors[tool_name]
        return executor(**tool_arguments)

    def _save_conversation_json(self) -> None:
        """
        保存对话记录为JSON格式
        使用原子写入确保数据完整性
        """
        json_path = os.path.join(self.conversation_dir, "conversation.json")
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            
            # 使用临时文件进行原子写入
            temp_file = f"{json_path}.tmp"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(self.conversations, f, ensure_ascii=False, indent=2)
            
            # 原子性重命名
            if os.path.exists(json_path):
                os.replace(temp_file, json_path)
            else:
                os.rename(temp_file, json_path)
        except Exception as e:
            # 清理临时文件
            temp_file = f"{json_path}.tmp"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            print(f"保存JSON对话记录失败: {e}")

    def _save_conversation_markdown(self) -> None:
        """
        保存对话记录为Markdown格式
        """
        md_path = os.path.join(self.conversation_dir, "conversation.md")
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write("# 对话记录\n\n")
                f.write(f"会话ID: {self.conversation_id}\n\n")
                f.write("---\n\n")
                
                for msg in self.conversations:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    
                    if role == "user":
                        f.write(f"## 用户\n\n{content}\n\n")
                    elif role == "assistant":
                        f.write(f"## 助手\n\n{content}\n\n")
                    elif role == "system":
                        f.write(f"## 系统\n\n{content}\n\n")
                    
                    f.write("---\n\n")
        except Exception as e:
            print(f"保存Markdown对话记录失败: {e}")

    def chat(self, user_question: str) -> Generator[str, None, None]:
        """
        与智能体进行聊天，流式返回最终回答
        
        Args:
            user_question: 用户提出的问题
            
        Yields:
            流式输出的智能体回答
        """
        # 第一轮请求：触发工具调用（如果需要）
        self.conversations.append({
            "type": "message",
            "role": "user",
            "content": user_question,
        })

        response = self.client.responses.create(
            model=self.model,
            input=self.conversations,
            stream=True,
            tools=self.tools,
            extra_body={"thinking": {"type": "disabled"}}
        )
        response_type = None
        tool_call = None

        assistant_response = ""
        for i, event in enumerate(response):
            if i == 2:
                if type(event) == openai.types.responses.response_output_item_added_event.ResponseOutputItemAddedEvent:
                    if event.item.type == "function_call":
                        response_type = "function_call"
                        tool_call = True
                    else:
                        response_type = "stream"
            if hasattr(event, "delta") and response_type and response_type == "stream":
                assistant_response += event.delta
                yield event.delta

        while tool_call:
            call_id = event.response.output[0].call_id
            tool_name = event.response.output[0].name
            arguments = event.response.output[0].arguments
            print(arguments)
            call_arguments = json.loads(arguments)
            tool_output = self._execute_tool(tool_name, call_arguments)
            self.conversations.append({
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(tool_output, ensure_ascii=False),
            })
            response = self.client.responses.create(
                model=self.model,
                previous_response_id=event.response.id,
                input=self.conversations,
                stream=True,
                tools=self.tools,
                extra_body={"thinking": {"type": "disabled"}},
            )
            self.latest_response = response

            assistant_response = ""
            for i, event in enumerate(response):
                if i == 2:
                    if type(event) == openai.types.responses.response_output_item_added_event.ResponseOutputItemAddedEvent:
                        if event.item.type == "function_call":
                            response_type = "function_call"
                            tool_call = True
                        else:
                            response_type = "stream"
                            tool_call = False
                if hasattr(event, "delta") and response_type and response_type == "stream":
                    assistant_response += event.delta
                    yield event.delta

        # 添加助手回复到对话记录
        if assistant_response:
            self.conversations.append({
                "role": "assistant",
                "content": assistant_response,
            })
        
        # 保存对话记录
        self._save_conversation_json()
        self._save_conversation_markdown()

    def run_interactive(self):
        """启动命令行交互式对话"""
        print("=" * 80)
        print("欢迎使用股票分析智能体")
        print(f"会话ID: {self.conversation_id}")
        print(f"对话记录将保存到: {self.conversation_dir}")
        print("输入 'quit' 或 'exit' 退出程序")
        print("=" * 80)
        
        while True:
            try:
                user_input = input("\n您的问题: ").strip()
                
                if user_input.lower() in ("quit", "exit"):
                    print("感谢使用，再见!")
                    break
                
                if not user_input:
                    print("请输入有效的问题")
                    continue
                
                print("\n智能体回答: ", end="", flush=True)
                
                for text in self.chat(user_input):
                    print(text, end="", flush=True)
                
                print()  # 换行
                
            except KeyboardInterrupt:
                print("\n\n程序已中断")
                break
            except Exception as e:
                print(f"\n发生错误: {e}")

if __name__ == "__main__":
    """
    分析一下SZ:002384这只股票，给出详细的股票分析报告。
    分析一下SH600745这只股票，给出详细的股票分析报告。
    """
    agent = StockAnalysisAgent()
    agent.run_interactive()
