"""
数据处理工具 - 源自FinRpt的data_processing.py

包含:
- DataFrame到文本转换
- 数据清洗和标准化
- 数值提取
"""
import re
import json
import logging
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def df_to_text(df: pd.DataFrame, max_rows: int = 20, max_cols: int = 10) -> str:
    """将DataFrame转为文本描述"""
    if df is None or df.empty:
        return "无数据"
    return df.head(max_rows).to_string(max_cols=max_cols)


def extract_numbers(text: str) -> List[float]:
    """从文本中提取数值"""
    pattern = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
    matches = re.findall(pattern, text)
    return [float(m) for m in matches]


def safe_json_parse(text: str) -> Optional[Dict[str, Any]]:
    """安全的JSON解析"""
    if not text:
        return None

    text = text.strip()
    # 移除markdown代码块
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试找JSON对象
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return None


def truncate_text(text: str, max_length: int = 2000) -> str:
    """截断文本到指定长度"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"... (truncated, total {len(text)} chars)"


def format_number(num: Union[int, float], precision: int = 2) -> str:
    """格式化数字显示"""
    if num is None or (isinstance(num, float) and np.isnan(num)):
        return "N/A"
    if abs(num) >= 1e12:
        return f"{num/1e12:.{precision}f}万亿"
    if abs(num) >= 1e8:
        return f"{num/1e8:.{precision}f}亿"
    if abs(num) >= 1e4:
        return f"{num/1e4:.{precision}f}万"
    return f"{num:.{precision}f}"


def clean_html(text: str) -> str:
    """清除HTML标签"""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()
