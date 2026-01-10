# app/agents/tools/arxiv_tool.py
# arXiv论文搜索工具

from typing import Dict, Any
import arxiv
import logging

from app.agents.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class ArxivPaperTool(BaseTool):
    """arXiv论文搜索工具
    
    搜索arXiv上的学术论文
    """
    
    def get_definition(self) -> Dict[str, Any]:
        """获取工具定义"""
        return {
            "type": "function",
            "name": "search_arxiv_papers",
            "description": "搜索arXiv上的学术论文,返回最新的相关论文信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词(必须是英文)",
                    },
                    "num_papers": {
                        "type": "integer",
                        "description": "返回的论文数量",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        }
    
    async def execute(self, query: str, num_papers: int = 5, **kwargs) -> str:
        """执行论文搜索
        
        Args:
            query: 搜索关键词(英文)
            num_papers: 返回论文数量
            
        Returns:
            格式化的论文信息字符串
            
        Raises:
            ValueError: 当参数无效时
        """
        if not query:
            raise ValueError("搜索关键词不能为空")
        
        if num_papers <= 0:
            raise ValueError("论文数量必须为正整数")
        
        # 限制最大数量
        num_papers = min(num_papers, 20)
        
        try:
            search = arxiv.Search(
                query=query,
                max_results=num_papers,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )
            
            client = arxiv.Client()
            papers = []
            
            for result in client.results(search):
                # 提取作者名称
                author_names = [
                    author.name if hasattr(author, "name") else str(author)
                    for author in result.authors
                ]
                
                # 格式化提交日期
                submitted_at = (
                    result.published.strftime("%Y-%m-%d")
                    if result.published
                    else "未知"
                )
                
                # 构建论文信息
                paper_info = [
                    f"标题: {result.title.strip()}",
                    f"作者: {', '.join(author_names)}" if author_names else "作者: 未知",
                    f"摘要: {result.summary.strip()}",
                    f"提交日期: {submitted_at}",
                    f"链接: {result.entry_id}",
                    "-" * 80,
                ]
                
                papers.append("\n".join(paper_info))
            
            if not papers:
                return f"未找到与'{query}'相关的论文"
            
            return "\n\n".join(papers)
            
        except Exception as e:
            logger.error(f"搜索arXiv论文失败 query={query}: {e}", exc_info=True)
            raise ValueError(f"搜索论文失败: {str(e)}")
