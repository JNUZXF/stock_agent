# app/agents/tools/stock_tool.py
# 股票分析工具

from typing import Dict, Any
import pysnowball as ball
import logging

from app.agents.tools.base_tool import BaseTool
from app.core.config import settings

logger = logging.getLogger(__name__)


class StockAnalysisTool(BaseTool):
    """股票分析工具
    
    获取股票的详细信息,包括财务数据、股东信息、行业对比等
    """
    
    def __init__(self):
        super().__init__()
        # 设置雪球token
        if settings.XQ_A_TOKEN:
            ball.set_token(f"xq_a_token={settings.XQ_A_TOKEN}")
    
    def get_definition(self) -> Dict[str, Any]:
        """获取工具定义"""
        return {
            "type": "function",
            "name": "get_stock_info",
            "description": "获取股票详细信息,包括现金流、利润表、主营业务、股东信息、主要指标、机构持仓和行业对比",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "股票代码,格式如: SH600519(贵州茅台), SZ000001(平安银行)",
                    },
                },
                "required": ["symbol"],
            },
        }
    
    async def execute(self, symbol: str, **kwargs) -> str:
        """执行股票信息获取
        
        Args:
            symbol: 股票代码
            
        Returns:
            格式化的股票信息字符串
            
        Raises:
            ValueError: 当股票代码无效时
        """
        if not symbol:
            raise ValueError("股票代码不能为空")
        
        try:
            # 获取各类数据
            cash_flow = ball.cash_flow(symbol)["data"]["list"]
            income = ball.income(symbol=symbol, is_annals=1, count=1)["data"]["list"]
            business = ball.business(symbol=symbol, count=1)["data"]["list"]
            top_holders = ball.top_holders(symbol=symbol, circula=0)["data"]["items"]
            main_indicator = ball.main_indicator(symbol)["data"]
            org_holding_change = ball.org_holding_change(symbol)["data"]["items"]
            industry_compare = ball.industry_compare(symbol)["data"]
            
            # 格式化输出
            info_template = f"""
股票代码: {symbol}

现金流数据:
{cash_flow}
---

利润表数据:
{income}
---

主营业务构成:
{business}
---

十大股东:
{top_holders}
---

主要指标:
{main_indicator}
---

机构持仓变化:
{org_holding_change}
---

行业对比:
{industry_compare}
"""
            
            return info_template.strip()
            
        except Exception as e:
            logger.error(f"获取股票信息失败 symbol={symbol}: {e}", exc_info=True)
            raise ValueError(f"获取股票信息失败: {str(e)}")
