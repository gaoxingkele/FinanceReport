"""
记忆管理模块 - 源自Cogito的Memory Module

核心能力:
1. 短期记忆: 当前分析session的中间结果
2. 长期记忆: 历史分析的经验和模式
3. 记忆检索: 基于相关性检索历史记忆
4. 记忆更新: 分析完成后更新记忆库
"""
import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    记忆管理器

    Cogito论文核心思想:
    - Agent具备记忆能力，可以从历史分析中学习
    - 短期记忆存储当前分析上下文
    - 长期记忆存储分析经验和行业模式
    """

    def __init__(
        self,
        memory_dir: str = "./memory",
        max_items: int = 100,
    ):
        self.memory_dir = memory_dir
        self.max_items = max_items
        self._short_term: List[Dict[str, Any]] = []
        self._long_term: List[Dict[str, Any]] = []
        self._load_long_term()

    def _load_long_term(self):
        """加载长期记忆"""
        memory_file = os.path.join(self.memory_dir, "long_term_memory.json")
        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r", encoding="utf-8") as f:
                    self._long_term = json.load(f)
                logger.info(f"[Memory] 加载了 {len(self._long_term)} 条长期记忆")
            except Exception as e:
                logger.warning(f"[Memory] 长期记忆加载失败: {e}")
                self._long_term = []

    def save_long_term(self):
        """持久化长期记忆"""
        os.makedirs(self.memory_dir, exist_ok=True)
        memory_file = os.path.join(self.memory_dir, "long_term_memory.json")

        # 限制条目数
        if len(self._long_term) > self.max_items:
            self._long_term = self._long_term[-self.max_items:]

        try:
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(self._long_term, f, ensure_ascii=False, indent=2)
            logger.info(f"[Memory] 保存了 {len(self._long_term)} 条长期记忆")
        except Exception as e:
            logger.warning(f"[Memory] 长期记忆保存失败: {e}")

    # ---- 短期记忆 (当前session) ----

    def store_short_term(self, key: str, value: Any):
        """存储短期记忆"""
        self._short_term.append({
            "key": key,
            "value": value,
            "timestamp": datetime.now().isoformat(),
        })

    def get_short_term(self, key: Optional[str] = None) -> Any:
        """检索短期记忆"""
        if key is None:
            return self._short_term
        for item in reversed(self._short_term):
            if item["key"] == key:
                return item["value"]
        return None

    def get_analysis_context(self) -> Dict[str, Any]:
        """获取当前分析上下文 (所有短期记忆)"""
        context = {}
        for item in self._short_term:
            context[item["key"]] = item["value"]
        return context

    # ---- 长期记忆 (跨session) ----

    def store_analysis_result(
        self,
        stock_code: str,
        analysis_type: str,
        result_summary: str,
        key_findings: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """存储分析结果到长期记忆"""
        memory_item = {
            "stock_code": stock_code,
            "analysis_type": analysis_type,
            "result_summary": result_summary,
            "key_findings": key_findings,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self._long_term.append(memory_item)

    def retrieve_relevant(
        self,
        stock_code: Optional[str] = None,
        industry: Optional[str] = None,
        analysis_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        检索相关历史记忆

        基于股票代码、行业、分析类型进行检索
        """
        candidates = self._long_term

        if stock_code:
            # 优先匹配相同股票
            same_stock = [m for m in candidates if m.get("stock_code") == stock_code]
            if same_stock:
                candidates = same_stock

        if analysis_type:
            type_match = [
                m for m in candidates if m.get("analysis_type") == analysis_type
            ]
            if type_match:
                candidates = type_match

        if industry:
            industry_match = [
                m for m in candidates
                if m.get("metadata", {}).get("industry") == industry
            ]
            if industry_match:
                candidates = industry_match

        # 按时间降序，取最近的
        candidates.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return candidates[:limit]

    def get_stock_history(self, stock_code: str) -> List[Dict[str, Any]]:
        """获取某只股票的历史分析记录"""
        return [
            m for m in self._long_term if m.get("stock_code") == stock_code
        ]

    # ---- 清理 ----

    def clear_short_term(self):
        """清空短期记忆"""
        self._short_term = []

    def clear_all(self):
        """清空所有记忆"""
        self._short_term = []
        self._long_term = []
