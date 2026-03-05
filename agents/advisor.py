"""
投资建议智能体 - 源自FinRpt Advisor

综合所有分析结果，通过三条并行分析流(财务/信息/策略)，
生成最终的投资建议
"""
import json
import logging
from typing import Dict, Any, List

from agents.base import BaseAgent
from prompts.templates import ADVISOR_SYSTEM_ZH, ADVISOR_USER_ZH

logger = logging.getLogger(__name__)


class InvestmentAdvisor(BaseAgent):
    """投资建议智能体"""

    def __init__(self, llm, language="zh", max_rounds=2, enable_reflection=True):
        super().__init__(
            llm=llm,
            name="InvestmentAdvisor",
            language=language,
            max_rounds=max_rounds,
            enable_reflection=enable_reflection,
        )

    def perceive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """汇总所有分析结果（含竞争格局）"""
        save = data.get("save", {})
        company_info = data.get("company_info", {})

        return {
            "stock_code": data.get("stock_code", ""),
            "company_name": company_info.get("company_name", data.get("stock_code", "")),
            "company_info": json.dumps(company_info, ensure_ascii=False, default=str)[:1500],
            "financial_analysis": json.dumps(
                save.get("FinancialAnalyst", {}), ensure_ascii=False, default=str
            )[:3000],
            "competitive_analysis": json.dumps(
                save.get("CompetitiveAnalyst", {}), ensure_ascii=False, default=str
            )[:2000],
            "news_analysis": json.dumps(
                save.get("NewsAnalyst", {}), ensure_ascii=False, default=str
            )[:2000],
            "risk_assessment": json.dumps(
                save.get("RiskAssessor", {}), ensure_ascii=False, default=str
            )[:2000],
            "prediction": json.dumps(
                save.get("Predictor", {}), ensure_ascii=False, default=str
            )[:2000],
        }

    def plan(self, context: Dict[str, Any]) -> List[str]:
        """三条并行分析流 (FinRpt Advisor架构)"""
        return [
            "财务维度综合评估",
            "信息维度综合评估",
            "策略维度综合评估",
            "生成统一投资建议",
        ]

    def execute(self, context: Dict[str, Any], plan: List[str], round_idx: int) -> Dict[str, Any]:
        """生成投资建议"""
        system_prompt = ADVISOR_SYSTEM_ZH
        user_prompt = ADVISOR_USER_ZH.format(
            company_name=context.get("company_name", ""),
            stock_code=context.get("stock_code", ""),
            company_info=context.get("company_info", ""),
            financial_analysis=context.get("financial_analysis", ""),
            competitive_analysis=context.get("competitive_analysis", "暂无"),
            news_analysis=context.get("news_analysis", ""),
            risk_assessment=context.get("risk_assessment", ""),
            prediction=context.get("prediction", ""),
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
            logger.error(f"投资建议生成失败: {e}")
            return {"error": str(e), "recommendation": {"action": "N/A"}}
