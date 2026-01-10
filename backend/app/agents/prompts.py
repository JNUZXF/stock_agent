# app/agents/prompts.py
# Agent提示词管理 - 集中管理所有提示词

from textwrap import dedent


class StockAgentPrompts:
    """股票分析Agent提示词"""
    
    SYSTEM_PROMPT = dedent(
        """
        # 你的角色
        你是股票分析专家,严谨、专业、准确。你必须输出高质量的股票分析报告。
        
        # 股票代码注意
        - 必须是类似SZ000001,SH600519这样的股票代码
        - SH开头代表上海证券交易所
        - SZ开头代表深圳证券交易所
        
        # 分析要求
        - 基于提供的财务数据进行客观分析
        - 指出关键财务指标和趋势
        - 分析行业地位和竞争力
        - 评估投资风险和机会
        - 给出明确的投资建议
        
        # 输出格式
        - 使用清晰的章节结构
        - 重要数据用表格展示
        - 关键结论用加粗标注
        - 风险提示必须明确
        """
    ).strip()
    
    ANALYSIS_TEMPLATE = dedent(
        """
        请基于以下股票数据进行详细分析:
        
        {stock_data}
        
        请按照以下结构输出分析报告:
        
        ## 1. 公司概况
        ## 2. 财务分析
        ## 3. 股东结构分析
        ## 4. 行业地位分析
        ## 5. 投资建议
        ## 6. 风险提示
        """
    ).strip()


class GeneralPrompts:
    """通用提示词"""
    
    DEFAULT_SYSTEM = "你是一个专业、严谨的AI助手,致力于提供准确、有价值的信息。"
    
    ERROR_HANDLING = dedent(
        """
        抱歉,在处理您的请求时遇到了问题:
        
        {error_message}
        
        请尝试:
        1. 检查输入格式是否正确
        2. 确认股票代码是否有效
        3. 稍后重试
        
        如果问题持续存在,请联系技术支持。
        """
    ).strip()


def get_stock_agent_system_prompt() -> str:
    """获取股票分析Agent的系统提示词
    
    Returns:
        系统提示词
    """
    return StockAgentPrompts.SYSTEM_PROMPT


def format_analysis_prompt(stock_data: str) -> str:
    """格式化分析提示词
    
    Args:
        stock_data: 股票数据
        
    Returns:
        格式化后的提示词
    """
    return StockAgentPrompts.ANALYSIS_TEMPLATE.format(stock_data=stock_data)


def format_error_message(error: str) -> str:
    """格式化错误消息
    
    Args:
        error: 错误信息
        
    Returns:
        格式化后的错误消息
    """
    return GeneralPrompts.ERROR_HANDLING.format(error_message=error)
