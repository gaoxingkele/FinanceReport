"""
财务分析智能体 - 源自FinRpt FinancialsAnalyzer

分析公司利润表、资产负债表、现金流量表，
从盈利能力、成长性、偿债能力、运营效率、现金流质量五个维度评估
"""
import json
import logging
from typing import Dict, Any, List

from agents.base import BaseAgent
from prompts.templates import (
    FINANCIAL_ANALYST_SYSTEM_ZH,
    FINANCIAL_ANALYST_USER_ZH,
    FINANCIAL_ANALYST_SYSTEM_EN,
    FINANCIAL_ANALYST_USER_EN,
)

logger = logging.getLogger(__name__)


class FinancialAnalyst(BaseAgent):
    """财务分析智能体"""

    def __init__(self, llm, language="zh", max_rounds=3, enable_reflection=True):
        super().__init__(
            llm=llm,
            name="FinancialAnalyst",
            language=language,
            max_rounds=max_rounds,
            enable_reflection=enable_reflection,
        )

    def perceive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取财务相关数据"""
        context = {
            "stock_code": data.get("stock_code", ""),
            "company_name": data.get("company_info", {}).get("company_name", data.get("stock_code", "")),
            "industry": data.get("company_info", {}).get("industry", "未知"),
            "financial_data": data.get("financial_data", {}).get("text_summary", "")[:5000],
            "market_data": data.get("market_data", {}).get("summary", {}),
        }
        return context

    def plan(self, context: Dict[str, Any]) -> List[str]:
        """规划财务分析步骤"""
        steps = [
            "分析盈利能力指标",
            "评估成长能力",
            "检查偿债能力",
            "评估运营效率",
            "分析现金流质量",
            "综合评分",
        ]
        if not context.get("financial_data"):
            steps = ["提示数据不足，基于有限信息分析"]
        return steps

    def execute(self, context: Dict[str, Any], plan: List[str], round_idx: int) -> Dict[str, Any]:
        """执行财务分析"""
        if self.language == "zh":
            system_prompt = FINANCIAL_ANALYST_SYSTEM_ZH
            user_prompt = FINANCIAL_ANALYST_USER_ZH.format(
                company_name=context.get("company_name", ""),
                stock_code=context.get("stock_code", ""),
                industry=context.get("industry", ""),
                financial_data=context.get("financial_data", "数据暂不可用"),
            )
        else:
            system_prompt = FINANCIAL_ANALYST_SYSTEM_EN
            user_prompt = FINANCIAL_ANALYST_USER_EN.format(
                company_name=context.get("company_name", ""),
                stock_code=context.get("stock_code", ""),
                industry=context.get("industry", ""),
                financial_data=context.get("financial_data", "Data not available"),
            )

        # 如果有反思反馈，加入提示
        if "reflection_feedback" in context:
            user_prompt += f"\n\n[上轮反思反馈] {context['reflection_feedback']}\n请针对反馈改进分析。"

        messages = self._build_messages(system_prompt, user_prompt)

        try:
            raw = self.llm.robust_prompt(messages, response_format="json")
            result = self.llm._parse_json(raw)
            result["_raw"] = raw
            return result
        except Exception as e:
            logger.error(f"财务分析失败: {e}")
            return {
                "error": str(e),
                "overall_score": "N/A",
                "summary": "财务分析失败，请检查数据可用性",
            }
