"""
基础智能体类 - 融合FinRpt的BaseModel和Cogito的认知Agent架构

FinRpt: 每个Agent有 run(data) 方法，通过共享data字典通信
Cogito: 每个Agent具备 perceive → decide → act → reflect 认知循环
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from utils.llm_client import LLMClient

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    基础智能体 — 所有分析智能体的父类

    认知循环 (Cogito):
        1. perceive()  - 感知输入数据
        2. plan()      - 规划分析步骤
        3. execute()   - 执行核心分析
        4. reflect()   - 反思结果质量
        5. act()       - 输出最终结果

    通信机制 (FinRpt):
        - 通过共享的 data 字典进行智能体间通信
        - 每个智能体从 data 读取上游结果，写入自己的分析
    """

    def __init__(
        self,
        llm: LLMClient,
        name: str = "BaseAgent",
        language: str = "zh",
        max_rounds: int = 3,
        enable_reflection: bool = True,
    ):
        self.llm = llm
        self.name = name
        self.language = language
        self.max_rounds = max_rounds
        self.enable_reflection = enable_reflection
        self._memory: List[Dict[str, Any]] = []

    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        智能体主入口 (兼容FinRpt接口)
        实现Cogito认知循环: perceive → plan → execute → reflect → act
        """
        logger.info(f"[{self.name}] 开始执行...")

        # Step 1: 感知 - 从共享data中提取所需信息
        context = self.perceive(data)

        # Step 2: 规划 - 确定分析步骤
        plan = self.plan(context)

        # Step 3: 执行 - 核心分析逻辑，支持多轮迭代
        result = None
        for round_idx in range(self.max_rounds):
            result = self.execute(context, plan, round_idx)

            # Step 4: 反思 - 检查结果质量
            if self.enable_reflection:
                quality_ok, feedback = self.reflect(result, context)
                if quality_ok:
                    logger.info(f"[{self.name}] 第{round_idx+1}轮: 反思通过")
                    break
                else:
                    logger.info(f"[{self.name}] 第{round_idx+1}轮: 需要改进 - {feedback}")
                    context["reflection_feedback"] = feedback
            else:
                break

        # Step 5: 行动 - 将结果写入共享data
        output = self.act(result, data)

        # 记录到记忆
        self._memory.append({
            "input_keys": list(context.keys()),
            "output_summary": str(output)[:200],
            "rounds": round_idx + 1 if result else 0,
        })

        logger.info(f"[{self.name}] 执行完成")
        return output

    @abstractmethod
    def perceive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从共享data中提取本智能体需要的上下文"""
        pass

    def plan(self, context: Dict[str, Any]) -> List[str]:
        """
        规划分析步骤 (Cogito规划能力)
        子类可覆盖以实现特定规划逻辑
        """
        return ["analyze"]

    @abstractmethod
    def execute(
        self, context: Dict[str, Any], plan: List[str], round_idx: int
    ) -> Dict[str, Any]:
        """执行核心分析逻辑"""
        pass

    def reflect(
        self, result: Dict[str, Any], context: Dict[str, Any]
    ) -> tuple:
        """
        反思结果质量 (Cogito反思能力)

        Returns:
            (quality_ok: bool, feedback: str)
        """
        if not result:
            return False, "结果为空"

        # 默认反思: 检查结果是否有实质内容
        prompt = f"""请评估以下分析结果的质量:
分析结果: {json.dumps(result, ensure_ascii=False, default=str)[:2000]}

请判断:
1. 结果是否包含有实质性的分析内容？
2. 结果逻辑是否自洽？
3. 是否有明显遗漏？

请用JSON回复: {{"quality_ok": true/false, "feedback": "..."}}"""

        try:
            resp = self.llm.json_prompt(prompt)
            return resp.get("quality_ok", True), resp.get("feedback", "")
        except Exception:
            return True, ""  # 反思失败时默认通过

    def act(self, result: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将结果写入共享data字典 (FinRpt通信机制)
        子类可覆盖以定制输出格式
        """
        if "save" not in data:
            data["save"] = {}
        data["save"][self.name] = result
        return result

    def get_memory(self) -> List[Dict[str, Any]]:
        """获取智能体记忆"""
        return self._memory

    def _build_messages(
        self, system_prompt: str, user_prompt: str
    ) -> List[Dict[str, str]]:
        """构建消息列表的便捷方法"""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
