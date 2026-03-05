"""
风险评估智能体 - 源自FinRpt RiskAssessor

综合财务分析和新闻分析结果，评估投资风险
"""
import json
import logging
from typing import Dict, Any, List

from agents.base import BaseAgent
from prompts.templates import RISK_ASSESSOR_SYSTEM_ZH, RISK_ASSESSOR_USER_ZH

logger = logging.getLogger(__name__)


class RiskAssessor(BaseAgent):
    """风险评估智能体"""

    def __init__(self, llm, language="zh", max_rounds=2, enable_reflection=True):
        super().__init__(
            llm=llm,
            name="RiskAssessor",
            language=language,
            max_rounds=max_rounds,
            enable_reflection=enable_reflection,
        )

    def perceive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """汇总上游分析结果"""
        save = data.get("save", {})
        return {
            "stock_code": data.get("stock_code", ""),
            "company_name": data.get("company_info", {}).get(
                "company_name", data.get("stock_code", "")
            ),
            "financial_summary": json.dumps(
                save.get("FinancialAnalyst", {}), ensure_ascii=False, default=str
            )[:3000],
            "news_summary": json.dumps(
                save.get("NewsAnalyst", {}), ensure_ascii=False, default=str
            )[:2000],
            "market_data": json.dumps(
                data.get("market_data", {}).get("summary", {}),
                ensure_ascii=False, default=str,
            )[:1000],
        }

    def execute(self, context: Dict[str, Any], plan: List[str], round_idx: int) -> Dict[str, Any]:
        """执行风险评估"""
        system_prompt = RISK_ASSESSOR_SYSTEM_ZH
        user_prompt = RISK_ASSESSOR_USER_ZH.format(
            company_name=context.get("company_name", ""),
            stock_code=context.get("stock_code", ""),
            financial_summary=context.get("financial_summary", ""),
            news_summary=context.get("news_summary", ""),
            market_data=context.get("market_data", ""),
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
            logger.error(f"风险评估失败: {e}")
            return {"error": str(e), "overall_risk_level": "未知"}
