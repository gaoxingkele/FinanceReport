"""
新闻分析智能体 - 源自FinRpt NewsAnalyzer

分析公司相关新闻，提取关键事件，评估对股价的影响
"""
import json
import logging
from typing import Dict, Any, List

from agents.base import BaseAgent
from prompts.templates import (
    NEWS_ANALYST_SYSTEM_ZH,
    NEWS_ANALYST_USER_ZH,
    NEWS_ANALYST_SYSTEM_EN,
    NEWS_ANALYST_USER_EN,
)

logger = logging.getLogger(__name__)


class NewsAnalyst(BaseAgent):
    """新闻分析智能体"""

    def __init__(self, llm, language="zh", max_rounds=2, enable_reflection=True):
        super().__init__(
            llm=llm,
            name="NewsAnalyst",
            language=language,
            max_rounds=max_rounds,
            enable_reflection=enable_reflection,
        )

    def perceive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取新闻数据"""
        news_data = data.get("news_data", {})
        return {
            "stock_code": data.get("stock_code", ""),
            "company_name": data.get("company_info", {}).get(
                "company_name", data.get("stock_code", "")
            ),
            "news_text": news_data.get("news_text", ""),
            "news_count": news_data.get("news_count", 0),
        }

    def plan(self, context: Dict[str, Any]) -> List[str]:
        """规划新闻分析步骤"""
        if context.get("news_count", 0) == 0:
            return ["无新闻可分析"]
        return [
            "筛选关键新闻",
            "分类并评估影响",
            "综合情绪判断",
        ]

    def execute(self, context: Dict[str, Any], plan: List[str], round_idx: int) -> Dict[str, Any]:
        """执行新闻分析"""
        if context.get("news_count", 0) == 0:
            return {
                "key_news": [],
                "overall_sentiment": "中性",
                "sentiment_score": 0,
                "summary": "暂无相关新闻",
            }

        if self.language == "zh":
            system_prompt = NEWS_ANALYST_SYSTEM_ZH
            user_prompt = NEWS_ANALYST_USER_ZH.format(
                company_name=context.get("company_name", ""),
                stock_code=context.get("stock_code", ""),
                news_data=context.get("news_text", ""),
            )
        else:
            system_prompt = NEWS_ANALYST_SYSTEM_EN
            user_prompt = NEWS_ANALYST_USER_EN.format(
                company_name=context.get("company_name", ""),
                stock_code=context.get("stock_code", ""),
                news_data=context.get("news_text", ""),
            )

        if "reflection_feedback" in context:
            user_prompt += f"\n\n[上轮反思反馈] {context['reflection_feedback']}"

        messages = self._build_messages(system_prompt, user_prompt)

        try:
            raw = self.llm.robust_prompt(messages, response_format="json")
            result = self.llm._parse_json(raw)
            result["_raw"] = raw
            return result
        except Exception as e:
            logger.error(f"新闻分析失败: {e}")
            return {
                "error": str(e),
                "overall_sentiment": "中性",
                "sentiment_score": 0,
            }
