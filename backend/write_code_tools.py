

"""
复现论文代码
"""

from dotenv import load_dotenv
from datetime import datetime
from textwrap import dedent
from openai import OpenAI
import PyPDF2
import json
import os
import re
        
WRITE_CODING_PLAN_PROMPT = dedent("""
    我想要初步复现这篇论文涉及到的代码，首先请仔细阅读下面的内容，按照要求完成任务

    # 论文内容
    {pdf_content}

    # 要求
    - 你需要首先用一段话介绍论文的内容，然后：
        1. 设计项目的架构，用markdown格式返回;
        2. 分点介绍每个文件的代码的核心功能，用JSON格式返回


    # 你的示例输出
    你必须严格参考如下格式输出回答：
    ```markdown
    这里是项目的架构图，示例：
    - 文件夹1（你需要写具体的名称）
        - 文件1
        - 文件2
        - 文件3
    - 文件夹2
        - 文件4
        - 文件5
        - 文件6
    - 文件夹3
        - 文件7
        - 文件8
        - 文件9
    ```
    # 返回格式
    {{
        "file_core_functions": [
            {{
                "file_name（具体文件相对路径）": "...",
                "core_function": "..."
            }},
            {{
                "file_name（具体文件相对路径）": "...",
                "core_function": "..."
            }},
            ...
        ]
    }}

    请开始：
""").strip()

MODULAR_CODING_PROMPT = dedent("""
    根据需求，撰写项目架构中的某一个文件的代码.

    # 项目架构
    {architecture}

    # 论文内容
    {pdf_content}

    # 你需要撰写的代码
    {code_file_name_temp}
    功能：{code_file_core_function_temp}

    # 要求
    - 你需要根据需求，撰写项目架构中的某一个文件的代码
    - 必须严格参考论文内容、注意与其他文件的关系
    - 你的输出必须仅包含代码，不能包含其他内容，以```python开头，以```结束

    请开始输出代码：
""").strip()

load_dotenv()
doubao_key = os.getenv("DOUBAO_API_KEY")

def get_doubao_pro_yield(question, model:str="doubao-seed-1-6-251015"):
    client = OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=doubao_key
    )

    completion = client.chat.completions.create(
        model=model,
        messages = [
            {"role": "system", "content": "你是豆包，是由字节跳动开发的 AI 人工智能助手"},
            {"role": "user", "content": question},
        ],
        stream=True
    )
    ans = ""
    for chunk in completion:
        if chunk.choices:
            char = chunk.choices[0].delta.content
            ans += char
            yield char

def get_doubao_pro_yield_converse(conversations):
    client = OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=doubao_key
    )

    completion = client.chat.completions.create(
        model="ep-20241115110340-qmxw5",
        messages=conversations,
        stream=True
    )
    ans = ""
    for chunk in completion:
        if chunk.choices:
            char = chunk.choices[0].delta.content
            ans += char
            yield char

# 提取PDF内容函数
def extract_pdf_content(pdf_path):
    with open(pdf_path, "rb") as f:
        pdf_reader = PyPDF2.PdfReader(f)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text

def get_doubao_answer(prompt:str, model:str="doubao-seed-1-6-251015") -> str:
    for char in get_doubao_pro_yield(prompt, model):
        yield char


def extract_json(text):
    """
    从文本中提取JSON，支持多种格式
    """
    # 方法1: 尝试直接匹配
    pattern = r'\{[\s\S]*\}'
    match = re.search(pattern, text)
    
    if match:
        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # 方法2: 使用大括号计数
    start_idx = text.find('{')
    if start_idx == -1:
        return None
    
    brace_count = 0
    for i in range(start_idx, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                json_str = text[start_idx:i + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"解析错误: {e}")
                    return None
    
    return None

def write_codebase(conversation_dir, model="doubao-seed-1-6-flash"):
    # 获取conversation_dir下面的PDF文件的绝对地址
    pdf_paths = [os.path.join(conversation_dir, f) for f in os.listdir(conversation_dir) if f.endswith(".pdf")]
    # 读取PDF文件
    pdf_path = pdf_paths[0]
    pdf_content = extract_pdf_content(pdf_path).replace("\n", " ")[:50000]
    print(pdf_content[:500])
    # ---大模型提出架构和代码指引---
    prompt = WRITE_CODING_PLAN_PROMPT.format(
        pdf_content=pdf_content
    )
    architecture_and_file_core_functions = ""
    for char in get_doubao_answer(prompt, model):
        architecture_and_file_core_functions += char
        yield char
    yield "\n"
    # 提取architecture，解析markdown内容
    architecture = re.findall(r"```markdown(.*)```", architecture_and_file_core_functions, re.DOTALL)[0]
    # 提取file_core_functions，解析JSON内容
    code_files = extract_json(architecture_and_file_core_functions)["file_core_functions"]
    all_codes = []
    for i,item in enumerate(code_files):
        print(f"Processing {i}/{len(code_files)}")
        written_code_temp = {}
        code_file_name_temp = item["file_name"]
        code_file_core_function_temp = item["core_function"]
        # 如果code_file_name_temp是py文件
        if ".py" in code_file_name_temp:
            print(code_file_name_temp)
            print(code_file_core_function_temp)
            written_code_temp["file_name"] = code_file_name_temp
            written_code_temp["core_function"] = code_file_core_function_temp
            prompt = MODULAR_CODING_PROMPT.format(
                architecture=architecture,
                pdf_content=pdf_content,
                code_file_name_temp=code_file_name_temp,
                code_file_core_function_temp=code_file_core_function_temp
            )
            llm_written_code = ""
            for char in get_doubao_answer(prompt, model):
                llm_written_code += char
                yield char
            yield "\n\n"
            written_code_temp["written_code"] = llm_written_code
            all_codes.append(written_code_temp)

