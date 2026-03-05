"""
竞争格局分析智能体

逆向推理补充: Apple 苹果报告中包含完整竞争格局章节（§6 竞争格局与市场领导地位），
但当前系统缺少此分析维度。本 Agent 补充：
  - 行业概览与增长阶段
  - 市场地位与份额估计
  - 护城河分析（Porter五力 + 护城河类型）
  - 主要竞争对手差异化对比
  - SWOT矩阵
  - 竞争格局展望
"""
import json
import logging
from typing import Dict, Any, List

from agents.base import BaseAgent
from prompts.templates import COMPETITIVE_ANALYST_SYSTEM_ZH, COMPETITIVE_ANALYST_USER_ZH

logger = logging.getLogger(__name__)


class CompetitiveAnalyst(BaseAgent):
    """竞争格局分析智能体"""

    def __init__(self, llm, language: str = "zh", max_rounds: int = 2,
                 enable_reflection: bool = True):
        super().__init__(
            llm=llm,
            name="CompetitiveAnalyst",
            language=language,
            max_rounds=max_rounds,
            enable_reflection=enable_reflection,
        )

    def perceive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取竞争分析所需上下文"""
        company_info = data.get("company_info", {})
        financial_data = data.get("financial_data", {})
        market_data = data.get("market_data", {})

        # 精简公司信息（剔除_raw等冗余字段）
        co_info = {k: v for k, v in company_info.items() if k != "_raw" and v}

        # 财务摘要（截取核心段落）
        fin_summary = financial_data.get("text_summary", "暂无财务数据")
        if len(fin_summary) > 1500:
            fin_summary = fin_summary[:1500] + "..."

        # 市场摘要
        market_summary = market_data.get("summary", {})
        mkt_str = json.dumps(market_summary, ensure_ascii=False, default=str)

        return {
            "stock_code": data.get("stock_code", ""),
            "company_name": company_info.get("company_name", data.get("stock_code", "")),
            "industry": company_info.get("industry", "未知"),
            "company_info": json.dumps(co_info, ensure_ascii=False, default=str)[:800],
            "financial_summary": fin_summary,
            "market_summary": mkt_str[:600],
        }

    def plan(self, context: Dict[str, Any]) -> List[str]:
        return [
            "分析行业概览与增长阶段",
            "评估竞争地位与市场份额",
            "构建护城河模型",
            "识别主要竞争对手",
            "SWOT矩阵分析",
            "竞争格局展望",
        ]

    def execute(self, context: Dict[str, Any], plan: List[str],
                round_idx: int) -> Dict[str, Any]:
        """执行竞争格局分析"""
        user_prompt = COMPETITIVE_ANALYST_USER_ZH.format(
            company_name=context["company_name"],
            stock_code=context["stock_code"],
            industry=context["industry"],
            company_info=context["company_info"],
            financial_summary=context["financial_summary"],
            market_summary=context["market_summary"],
        )

        if "reflection_feedback" in context:
            user_prompt += f"\n\n[上轮反思反馈] {context['reflection_feedback']}\n请针对反馈改进分析。"

        messages = self._build_messages(COMPETITIVE_ANALYST_SYSTEM_ZH, user_prompt)

        try:
            raw = self.llm.robust_prompt(messages, response_format="json")
            result = self.llm._parse_json(raw)
            result["_raw"] = raw
            return result
        except Exception as e:
            logger.error(f"竞争格局分析失败: {e}")
            return {
                "error": str(e),
                "competitive_score": "N/A",
                "outlook": "竞争分析暂不可用",
            }
