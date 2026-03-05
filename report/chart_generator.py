"""
图表生成模块 - 源自FinRpt的charting.py

生成股票分析所需的各类图表:
1. 股价走势图 (与基准对比)
2. PE/EPS趋势图
3. 营收增长图
4. 技术指标图
"""
import logging
import os
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class ChartGenerator:
    """图表生成器"""

    def __init__(self, output_dir: str = "./output", style: str = "seaborn-v0_8"):
        self.output_dir = output_dir
        self.style = style
        os.makedirs(output_dir, exist_ok=True)

    def generate_all(
        self,
        stock_code: str,
        market_data: Dict[str, Any],
        financial_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """
        生成所有图表

        Returns:
            {"chart_name": "file_path", ...}
        """
        charts = {}

        key_metrics = (financial_data or {}).get("key_metrics", {})

        # ── 市场类图表 ─────────────────────────────────────────────────────────
        price_chart = self._generate_price_chart(stock_code, market_data)
        if price_chart:
            charts["price_trend"] = price_chart

        volume_chart = self._generate_volume_chart(stock_code, market_data)
        if volume_chart:
            charts["volume"] = volume_chart

        tech_chart = self._generate_technical_chart(stock_code, market_data)
        if tech_chart:
            charts["technical"] = tech_chart

        # ── 财务类图表（需 key_metrics）─────────────────────────────────────
        if key_metrics and key_metrics.get("periods"):
            rev_chart = self._generate_revenue_chart(stock_code, key_metrics)
            if rev_chart:
                charts["revenue"] = rev_chart

            margin_chart = self._generate_margin_chart(stock_code, key_metrics)
            if margin_chart:
                charts["margin"] = margin_chart

            cf_chart = self._generate_cashflow_chart(stock_code, key_metrics)
            if cf_chart:
                charts["cashflow"] = cf_chart

        logger.info(f"[ChartGen] 生成了 {len(charts)} 张图表")
        return charts

    def _generate_price_chart(
        self, stock_code: str, market_data: Dict[str, Any]
    ) -> Optional[str]:
        """生成股价走势图"""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates

            # 尝试设置中文字体
            try:
                plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
                plt.rcParams["axes.unicode_minus"] = False
            except Exception:
                pass

            price_data = market_data.get("price_data", [])
            if not price_data:
                return None

            df = pd.DataFrame(price_data)

            # 统一列名
            date_col = "date" if "date" in df.columns else "Date"
            close_col = "close" if "close" in df.columns else "Close"

            if date_col not in df.columns or close_col not in df.columns:
                return None

            df[date_col] = pd.to_datetime(df[date_col])

            fig, ax = plt.subplots(figsize=(12, 6))

            ax.plot(df[date_col], df[close_col], linewidth=1.5, color="#1f77b4", label=stock_code)

            # 添加均线
            if len(df) >= 5:
                ax.plot(
                    df[date_col],
                    df[close_col].rolling(5).mean(),
                    linewidth=0.8, color="#ff7f0e", alpha=0.7, label="MA5",
                )
            if len(df) >= 20:
                ax.plot(
                    df[date_col],
                    df[close_col].rolling(20).mean(),
                    linewidth=0.8, color="#2ca02c", alpha=0.7, label="MA20",
                )
            if len(df) >= 60:
                ax.plot(
                    df[date_col],
                    df[close_col].rolling(60).mean(),
                    linewidth=0.8, color="#d62728", alpha=0.7, label="MA60",
                )

            ax.set_title(f"{stock_code} Price Trend", fontsize=14)
            ax.set_xlabel("Date")
            ax.set_ylabel("Price")
            ax.legend(loc="best")
            ax.grid(True, alpha=0.3)

            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
            plt.xticks(rotation=45)
            plt.tight_layout()

            filepath = os.path.join(self.output_dir, f"{stock_code}_price.png")
            plt.savefig(filepath, dpi=150, bbox_inches="tight")
            plt.close()
            return filepath

        except Exception as e:
            logger.error(f"股价图生成失败: {e}")
            return None

    def _generate_volume_chart(
        self, stock_code: str, market_data: Dict[str, Any]
    ) -> Optional[str]:
        """生成成交量图"""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            try:
                plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
                plt.rcParams["axes.unicode_minus"] = False
            except Exception:
                pass

            price_data = market_data.get("price_data", [])
            if not price_data:
                return None

            df = pd.DataFrame(price_data)
            date_col = "date" if "date" in df.columns else "Date"
            close_col = "close" if "close" in df.columns else "Close"
            vol_col = "volume" if "volume" in df.columns else "Volume"

            if vol_col not in df.columns:
                return None

            df[date_col] = pd.to_datetime(df[date_col])

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[2, 1], sharex=True)

            ax1.plot(df[date_col], df[close_col], linewidth=1.2, color="#1f77b4")
            ax1.set_ylabel("Price")
            ax1.set_title(f"{stock_code} Price & Volume", fontsize=14)
            ax1.grid(True, alpha=0.3)

            # 涨跌着色
            if "pct_change" in df.columns:
                colors = ["#d62728" if x >= 0 else "#2ca02c" for x in df["pct_change"]]
            else:
                colors = "#1f77b4"

            ax2.bar(df[date_col], df[vol_col], color=colors, alpha=0.6, width=0.8)
            ax2.set_ylabel("Volume")
            ax2.grid(True, alpha=0.3)

            plt.xticks(rotation=45)
            plt.tight_layout()

            filepath = os.path.join(self.output_dir, f"{stock_code}_volume.png")
            plt.savefig(filepath, dpi=150, bbox_inches="tight")
            plt.close()
            return filepath

        except Exception as e:
            logger.error(f"成交量图生成失败: {e}")
            return None

    def _generate_technical_chart(
        self, stock_code: str, market_data: Dict[str, Any]
    ) -> Optional[str]:
        """生成技术指标图 (RSI + MACD)"""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            price_data = market_data.get("price_data", [])
            if not price_data or len(price_data) < 26:
                return None

            df = pd.DataFrame(price_data)
            close_col = "close" if "close" in df.columns else "Close"
            date_col = "date" if "date" in df.columns else "Date"

            if close_col not in df.columns:
                return None

            df[date_col] = pd.to_datetime(df[date_col])
            close = df[close_col].astype(float)

            # 计算RSI
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss.replace(0, np.nan)
            rsi = 100 - (100 / (1 + rs))

            # 计算MACD
            ema12 = close.ewm(span=12).mean()
            ema26 = close.ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            histogram = macd - signal

            fig, (ax1, ax2, ax3) = plt.subplots(
                3, 1, figsize=(12, 10), height_ratios=[2, 1, 1], sharex=True
            )

            # 价格
            ax1.plot(df[date_col], close, linewidth=1.2)
            ax1.set_title(f"{stock_code} Technical Indicators", fontsize=14)
            ax1.set_ylabel("Price")
            ax1.grid(True, alpha=0.3)

            # RSI
            ax2.plot(df[date_col], rsi, linewidth=1, color="purple")
            ax2.axhline(70, color="red", linestyle="--", alpha=0.5)
            ax2.axhline(30, color="green", linestyle="--", alpha=0.5)
            ax2.fill_between(df[date_col], 30, 70, alpha=0.1, color="gray")
            ax2.set_ylabel("RSI")
            ax2.set_ylim(0, 100)
            ax2.grid(True, alpha=0.3)

            # MACD
            ax3.plot(df[date_col], macd, linewidth=1, label="MACD", color="blue")
            ax3.plot(df[date_col], signal, linewidth=1, label="Signal", color="orange")
            colors_hist = ["red" if v >= 0 else "green" for v in histogram]
            ax3.bar(df[date_col], histogram, color=colors_hist, alpha=0.5, width=0.8)
            ax3.set_ylabel("MACD")
            ax3.legend(loc="best", fontsize=8)
            ax3.grid(True, alpha=0.3)

            plt.xticks(rotation=45)
            plt.tight_layout()

            filepath = os.path.join(self.output_dir, f"{stock_code}_technical.png")
            plt.savefig(filepath, dpi=150, bbox_inches="tight")
            plt.close()
            return filepath

        except Exception as e:
            logger.error(f"技术指标图生成失败: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # 财务类图表 (逆向推理补充 — Apple报告 Chart1/Chart2/Chart7 等)
    # ─────────────────────────────────────────────────────────────────────────

    def _generate_revenue_chart(
        self, stock_code: str, key_metrics: Dict[str, Any]
    ) -> Optional[str]:
        """
        营收 & 净利润趋势组合图 (双轴 bar + line)
        对应 Apple报告 Chart1: 核心财务指标趋势
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.ticker as mticker

            try:
                plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
                plt.rcParams["axes.unicode_minus"] = False
            except Exception:
                pass

            periods  = key_metrics.get("periods", [])
            revenue  = key_metrics.get("revenue", [])
            net_p    = key_metrics.get("net_profit", [])

            if not periods or not any(v is not None for v in revenue):
                return None

            n = len(periods)
            rev_vals = [v / 1e8 if v is not None else 0 for v in revenue]   # 亿元
            np_vals  = [v / 1e8 if v is not None else 0 for v in net_p]     # 亿元

            x = np.arange(n)
            width = 0.38

            fig, ax1 = plt.subplots(figsize=(10, 5))
            ax2 = ax1.twinx()

            bars1 = ax1.bar(x - width / 2, rev_vals, width, label="营业收入(亿)", color="#2980B9", alpha=0.85)
            bars2 = ax1.bar(x + width / 2, np_vals,  width, label="净利润(亿)",  color="#27AE60", alpha=0.85)

            ax1.set_xlabel("报告期")
            ax1.set_ylabel("金额（亿元）")
            ax1.set_xticks(x)
            ax1.set_xticklabels([p[:7] for p in periods], rotation=30, ha="right", fontsize=8)
            ax1.legend(loc="upper left", fontsize=8)
            ax1.grid(axis="y", alpha=0.3)

            # 净利润率折线（右轴）
            margins_raw = key_metrics.get("net_margin", [])
            if any(v is not None for v in margins_raw):
                nm_vals = [v if v is not None else np.nan for v in margins_raw]
                ax2.plot(x, nm_vals, "o-", color="#E67E22", linewidth=1.5,
                         markersize=5, label="净利率(%)")
                ax2.set_ylabel("净利率（%）")
                ax2.legend(loc="upper right", fontsize=8)
                ax2.set_ylim(0, max(v for v in nm_vals if not np.isnan(v)) * 1.5 + 1)

            ax1.set_title(f"{stock_code} 营收 & 净利润趋势", fontsize=13)
            plt.tight_layout()

            filepath = os.path.join(self.output_dir, f"{stock_code}_revenue.png")
            plt.savefig(filepath, dpi=150, bbox_inches="tight")
            plt.close()
            return filepath

        except Exception as e:
            logger.error(f"营收图生成失败: {e}")
            return None

    def _generate_margin_chart(
        self, stock_code: str, key_metrics: Dict[str, Any]
    ) -> Optional[str]:
        """
        利润率趋势多线图
        对应 Apple报告 Chart2: 三年利润率趋势图（毛利率 / 营业利润率 / 净利率）
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            try:
                plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
                plt.rcParams["axes.unicode_minus"] = False
            except Exception:
                pass

            periods = key_metrics.get("periods", [])
            gross   = key_metrics.get("gross_margin", [])
            op      = key_metrics.get("operating_margin", [])
            net     = key_metrics.get("net_margin", [])

            if not periods:
                return None

            has_data = any(
                any(v is not None for v in lst)
                for lst in [gross, op, net]
            )
            if not has_data:
                return None

            def safe(lst):
                return [v if v is not None else np.nan for v in lst]

            fig, ax = plt.subplots(figsize=(10, 5))
            x_labels = [p[:7] for p in periods]

            if any(v is not None for v in gross):
                ax.plot(x_labels, safe(gross), "o-", color="#2980B9",
                        linewidth=2, markersize=6, label="毛利率%")
            if any(v is not None for v in op):
                ax.plot(x_labels, safe(op), "s-", color="#27AE60",
                        linewidth=2, markersize=6, label="营业利润率%")
            if any(v is not None for v in net):
                ax.plot(x_labels, safe(net), "^-", color="#E67E22",
                        linewidth=2, markersize=6, label="净利率%")

            ax.set_title(f"{stock_code} 利润率趋势", fontsize=13)
            ax.set_xlabel("报告期")
            ax.set_ylabel("利润率（%）")
            ax.legend(loc="best", fontsize=9)
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=30, ha="right", fontsize=8)
            plt.tight_layout()

            filepath = os.path.join(self.output_dir, f"{stock_code}_margin.png")
            plt.savefig(filepath, dpi=150, bbox_inches="tight")
            plt.close()
            return filepath

        except Exception as e:
            logger.error(f"利润率图生成失败: {e}")
            return None

    def _generate_cashflow_chart(
        self, stock_code: str, key_metrics: Dict[str, Any]
    ) -> Optional[str]:
        """
        现金流对比图 (营收 / 净利润 / 经营现金流 三柱并排)
        对应 Apple报告 Chart7: 关键财务指标对比
        """
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            try:
                plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
                plt.rcParams["axes.unicode_minus"] = False
            except Exception:
                pass

            periods = key_metrics.get("periods", [])
            revenue = key_metrics.get("revenue", [])
            net_p   = key_metrics.get("net_profit", [])
            op_cf   = key_metrics.get("operating_cf", [])

            if not periods:
                return None

            has_cf = any(v is not None for v in op_cf)
            has_np = any(v is not None for v in net_p)
            if not (has_cf or has_np):
                return None

            n = len(periods)
            scaler = 1e8  # 亿元

            def safe_scale(lst):
                return [v / scaler if v is not None else 0 for v in lst[:n]]

            rev_s  = safe_scale(revenue)
            np_s   = safe_scale(net_p)
            cf_s   = safe_scale(op_cf) if has_cf else [0] * n

            x = np.arange(n)
            w = 0.26

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(x - w, rev_s, w, label="营业收入", color="#2980B9", alpha=0.85)
            ax.bar(x,      np_s, w, label="净利润",   color="#27AE60", alpha=0.85)
            if has_cf:
                ax.bar(x + w, cf_s, w, label="经营现金流", color="#8E44AD", alpha=0.85)

            ax.set_title(f"{stock_code} 收入 / 利润 / 现金流对比（亿元）", fontsize=13)
            ax.set_xlabel("报告期")
            ax.set_ylabel("金额（亿元）")
            ax.set_xticks(x)
            ax.set_xticklabels([p[:7] for p in periods], rotation=30, ha="right", fontsize=8)
            ax.legend(loc="best", fontsize=9)
            ax.grid(axis="y", alpha=0.3)
            plt.tight_layout()

            filepath = os.path.join(self.output_dir, f"{stock_code}_cashflow.png")
            plt.savefig(filepath, dpi=150, bbox_inches="tight")
            plt.close()
            return filepath

        except Exception as e:
            logger.error(f"现金流图生成失败: {e}")
            return None
