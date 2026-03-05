"""
自我反思模块 - 源自Cogito的Reflection Module

核心能力:
1. 对每个智能体的输出进行质量评估
2. 发现分析中的逻辑矛盾和遗漏
3. 跨智能体一致性检查
4. 生成改进建议
"""
import json
import logging
from typing import Dict, Any, List, Tuple

from utils.llm_client import LLMClient
from prompts.templates import REFLECTOR_SYSTEM_ZH, REFLECTOR_USER_ZH

logger = logging.getLogger(__name__)


class CognitiveReflector:
    """
    认知反思器

    Cogito论文核心思想:
    - 每个Agent执行后进行自我反思
    - 评估输出质量，发现不一致之处
    - 提供改进建议，驱动迭代优化
    """

    def __init__(self, llm: LLMClient, language: str = "zh", depth: int = 2):
        self.llm = llm
        self.language = language
        self.depth = depth  # 反思深度（最大迭代次数）

    def reflect_on_agent(
        self,
        agent_name: str,
        task_description: str,
        result: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        对单个智能体的输出进行反思

        Returns:
            (is_acceptable, feedback, reflection_details)
        """
        # 清理结果中的内部字段
        clean_result = {k: v for k, v in result.items() if not k.startswith("_")}
        result_str = json.dumps(clean_result, ensure_ascii=False, default=str)[:3000]

        prompt = REFLECTOR_USER_ZH.format(
            agent_name=agent_name,
            task_description=task_description,
            result=result_str,
        )

        try:
            resp = self.llm.json_prompt(prompt, REFLECTOR_SYSTEM_ZH)

            is_acceptable = resp.get("is_acceptable", True)
            quality_score = resp.get("quality_score", 7)
            feedback_parts = []

            if resp.get("weaknesses"):
                feedback_parts.extend(resp["weaknesses"])
            if resp.get("suggestions"):
                feedback_parts.extend(resp["suggestions"])

            feedback = "; ".join(feedback_parts) if feedback_parts else ""

            logger.info(
                f"[Reflector] {agent_name}: score={quality_score}, "
                f"acceptable={is_acceptable}"
            )

            return is_acceptable, feedback, resp

        except Exception as e:
            logger.warning(f"[Reflector] 反思失败: {e}")
            return True, "", {"error": str(e)}

    def cross_agent_check(
        self, all_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        跨智能体一致性检查

        检查不同智能体的分析结论是否存在矛盾
        """
        # 提取各智能体核心结论
        summaries = {}
        for agent_name, result in all_results.items():
            if isinstance(result, dict):
                summaries[agent_name] = json.dumps(
                    result, ensure_ascii=False, default=str
                )[:800]

        if len(summaries) < 2:
            return {"consistent": True, "issues": []}

        prompt = f"""请检查以下各分析智能体的结论是否存在矛盾或不一致:

{json.dumps(summaries, ensure_ascii=False, indent=2)}

请以JSON格式输出:
{{
    "consistent": true/false,
    "inconsistencies": [
        {{
            "agents": ["智能体A", "智能体B"],
            "issue": "矛盾描述",
            "severity": "高/中/低"
        }}
    ],
    "resolution_suggestions": ["建议1", "..."]
}}"""

        try:
            result = self.llm.json_prompt(prompt, REFLECTOR_SYSTEM_ZH)
            if not result.get("consistent", True):
                logger.warning(
                    f"[Reflector] 发现跨智能体不一致: "
                    f"{result.get('inconsistencies', [])}"
                )
            return result
        except Exception as e:
            logger.warning(f"[Reflector] 跨智能体检查失败: {e}")
            return {"consistent": True, "issues": [], "error": str(e)}

    def final_review(
        self,
        advisor_result: Dict[str, Any],
        all_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        最终审核 - 对投资建议进行终审

        确保最终建议与各分析结论一致，逻辑完整
        """
        prompt = f"""作为研究质量审核专家，请对以下投资建议进行终审:

## 最终投资建议
{json.dumps(advisor_result, ensure_ascii=False, default=str)[:3000]}

## 各分析智能体结论摘要
{json.dumps({k: str(v)[:500] for k, v in all_results.items()}, ensure_ascii=False)}

请评估:
1. 投资建议是否与分析结论一致？
2. 逻辑推导是否严密？
3. 风险提示是否充分？
4. 建议是否清晰可操作？

请以JSON格式输出:
{{
    "approved": true/false,
    "quality_score": "1-10",
    "issues": ["问题1", "..."],
    "improvements": ["改进建议1", "..."]
}}"""

        try:
            return self.llm.json_prompt(prompt, REFLECTOR_SYSTEM_ZH)
        except Exception as e:
            logger.warning(f"[Reflector] 终审失败: {e}")
            return {"approved": True, "quality_score": 7, "error": str(e)}
