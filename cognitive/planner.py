"""
认知规划器 - 源自Cogito的Planning Module

根据股票信息和可用数据，动态规划分析路径。
核心能力:
1. 评估数据可用性，决定分析重点
2. 根据行业特性调整分析权重
3. 动态调整智能体执行顺序和参数
"""
import json
import logging
from typing import Dict, Any, List, Optional

from utils.llm_client import LLMClient
from prompts.templates import PLANNER_SYSTEM_ZH, PLANNER_USER_ZH

logger = logging.getLogger(__name__)


class CognitivePlanner:
    """
    认知规划器

    Cogito论文核心思想:
    - Agent在执行前先进行"思考"(thinking)
    - 基于当前状态和目标，制定最优行动计划
    - 动态调整策略以应对数据缺失等异常情况
    """

    def __init__(self, llm: LLMClient, language: str = "zh"):
        self.llm = llm
        self.language = language

    def create_plan(
        self,
        stock_code: str,
        company_info: Dict[str, Any],
        available_data: Dict[str, bool],
        analysis_goal: str = "全面深度研究",
    ) -> Dict[str, Any]:
        """
        创建分析计划

        Args:
            stock_code: 股票代码
            company_info: 公司基本信息
            available_data: 各数据源可用性 {"market": True, "financials": True, ...}
            analysis_goal: 分析目标

        Returns:
            分析计划字典
        """
        company_name = company_info.get("company_name", stock_code)
        industry = company_info.get("industry", "未知")
        data_str = ", ".join(
            f"{k}: {'可用' if v else '不可用'}" for k, v in available_data.items()
        )

        prompt = PLANNER_USER_ZH.format(
            company_name=company_name,
            stock_code=stock_code,
            industry=industry,
            available_data=data_str,
            analysis_goal=analysis_goal,
        )

        try:
            result = self.llm.json_prompt(prompt, PLANNER_SYSTEM_ZH)
            plan = self._validate_plan(result, available_data)
            logger.info(f"[Planner] 分析计划: {json.dumps(plan, ensure_ascii=False)[:500]}")
            return plan
        except Exception as e:
            logger.warning(f"[Planner] 规划失败，使用默认计划: {e}")
            return self._default_plan(available_data)

    def _validate_plan(
        self, plan: Dict[str, Any], available_data: Dict[str, bool]
    ) -> Dict[str, Any]:
        """验证并修正计划"""
        # 确保必要字段存在
        if "agent_sequence" not in plan:
            plan["agent_sequence"] = self._default_sequence(available_data)
        if "analysis_focus" not in plan:
            plan["analysis_focus"] = ["综合分析"]

        # 如果数据不可用，调整计划
        if not available_data.get("financials", False):
            plan.setdefault("special_attention", []).append(
                "财务数据不可用，分析将主要依赖新闻和行情数据"
            )

        return plan

    def _default_plan(self, available_data: Dict[str, bool]) -> Dict[str, Any]:
        """默认分析计划"""
        return {
            "analysis_focus": ["盈利能力", "成长性", "风险评估", "趋势判断"],
            "data_requirements": list(available_data.keys()),
            "agent_sequence": self._default_sequence(available_data),
            "special_attention": [],
            "estimated_complexity": "中",
        }

    @staticmethod
    def _default_sequence(available_data: Dict[str, bool]) -> List[str]:
        """默认智能体执行顺序"""
        sequence = []
        if available_data.get("financials", False):
            sequence.append("FinancialAnalyst")
        if available_data.get("news", False):
            sequence.append("NewsAnalyst")
        sequence.extend(["RiskAssessor", "Predictor", "InvestmentAdvisor"])
        return sequence

    def adjust_plan(
        self,
        current_plan: Dict[str, Any],
        completed_agents: List[str],
        intermediate_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        动态调整计划 (Cogito的自适应规划)

        在分析过程中根据中间结果调整后续步骤
        """
        # 检查是否需要额外分析
        adjustments = []

        # 如果财务分析发现重大风险，加强风险评估
        fin_result = intermediate_results.get("FinancialAnalyst", {})
        risk_level = fin_result.get("solvency", {}).get("risk_level", "")
        if risk_level == "高":
            adjustments.append("增加风险评估深度")
            current_plan.setdefault("special_attention", []).append(
                "财务风险较高，需要深入评估偿债能力"
            )

        # 如果新闻面有重大事件，加强趋势预测
        news_result = intermediate_results.get("NewsAnalyst", {})
        sentiment = news_result.get("overall_sentiment", "")
        if sentiment in ("积极", "消极"):
            adjustments.append(f"新闻情绪{sentiment}，重点关注短期趋势")

        if adjustments:
            current_plan["dynamic_adjustments"] = adjustments
            logger.info(f"[Planner] 动态调整: {adjustments}")

        return current_plan
