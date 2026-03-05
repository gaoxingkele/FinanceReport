"""
趋势预测智能体 - 源自FinRpt Predictor

综合技术面和基本面分析，预测股票未来走势
"""
import json
import logging
from typing import Dict, Any, List

from agents.base import BaseAgent
from prompts.templates import PREDICTOR_SYSTEM_ZH, PREDICTOR_USER_ZH

logger = logging.getLogger(__name__)


class Predictor(BaseAgent):
    """趋势预测智能体"""

    def __init__(self, llm, language="zh", max_rounds=2, enable_reflection=True):
        super().__init__(
            llm=llm,
            name="Predictor",
            language=language,
            max_rounds=max_rounds,
            enable_reflection=enable_reflection,
        )

    def perceive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """汇总所有分析数据"""
        save = data.get("save", {})
        market = data.get("market_data", {})

        # 提取价格摘要
        price_summary = market.get("summary", {})
        price_data_str = json.dumps(price_summary, ensure_ascii=False, default=str)

        # 最近价格数据 (取最近20条)
        recent_prices = market.get("price_data", [])[-20:]
        if recent_prices:
            price_data_str += "\n\n最近行情:\n"
            for p in recent_prices[-10:]:
                price_data_str += f"  {p.get('date', '')}: 收盘={p.get('close', '')} 成交量={p.get('volume', '')}\n"

        return {
            "stock_code": data.get("stock_code", ""),
            "company_name": data.get("company_info", {}).get(
                "company_name", data.get("stock_code", "")
            ),
            "price_data": price_data_str[:2000],
            "financial_summary": json.dumps(
                save.get("FinancialAnalyst", {}), ensure_ascii=False, default=str
            )[:2000],
            "news_summary": json.dumps(
                save.get("NewsAnalyst", {}), ensure_ascii=False, default=str
            )[:1500],
            "risk_summary": json.dumps(
                save.get("RiskAssessor", {}), ensure_ascii=False, default=str
            )[:1500],
        }

    def execute(self, context: Dict[str, Any], plan: List[str], round_idx: int) -> Dict[str, Any]:
        """执行趋势预测"""
        system_prompt = PREDICTOR_SYSTEM_ZH
        user_prompt = PREDICTOR_USER_ZH.format(
            company_name=context.get("company_name", ""),
            stock_code=context.get("stock_code", ""),
            price_data=context.get("price_data", ""),
            financial_summary=context.get("financial_summary", ""),
            news_summary=context.get("news_summary", ""),
            risk_summary=context.get("risk_summary", ""),
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
            logger.error(f"趋势预测失败: {e}")
            return {"error": str(e), "rating": "N/A"}
