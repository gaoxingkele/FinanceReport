"""
财务数据采集模块 - 源自FinRpt的financial statements获取逻辑

数据源: akshare (主) → tushare (备用) → yfinance (降级)

逆向推理补充:
  Apple报告包含: 多年营收趋势、利润率趋势、现金流分析等图表。
  这些图表需要结构化的数值序列(key_metrics)，而非纯文字摘要。
  新增 _extract_key_metrics() 方法，从原始报表中提取可供图表渲染的数据。
"""
import os
import logging
from typing import Dict, Any, Optional, List

import pandas as pd

from utils.remote_call import timed_api_call

logger = logging.getLogger(__name__)


class FinancialDataAgent:
    """财务数据采集智能体"""

    def __init__(self, language: str = "zh"):
        self.language = language

    def fetch(self, stock_code: str, market: str = "A") -> Dict[str, Any]:
        if market == "A":
            return self._fetch_a_share_financials(stock_code)
        else:
            return self._fetch_yfinance_financials(stock_code)

    def _fetch_a_share_financials(self, stock_code: str) -> Dict[str, Any]:
        result = self._fetch_akshare_financials(stock_code)
        if result and "error" not in result and len(result) > 2:
            return result

        logger.info("akshare财务数据获取失败，尝试tushare备用: %s", stock_code)
        result = self._fetch_tushare_financials(stock_code)
        if result and "error" not in result and len(result) > 2:
            return result

        logger.info("tushare财务数据获取失败，降级到yfinance: %s", stock_code)
        return self._fetch_yfinance_financials(stock_code)

    def _fetch_akshare_financials(self, stock_code: str) -> Dict[str, Any]:
        """通过 akshare 获取A股财务数据"""
        try:
            import akshare as ak

            code = stock_code.replace(".SH", "").replace(".SZ", "").replace(".BJ", "")
            result = {}

            # 利润表
            for fn, fn_name, kwargs in [
                (ak.stock_financial_report_sina, "ak.stock_financial_report_sina(利润表)", {"stock": code, "symbol": "利润表"}),
                (ak.stock_profit_sheet_by_report_em, "ak.stock_profit_sheet_by_report_em", {"symbol": code}),
            ]:
                try:
                    df = timed_api_call(fn, call_name=fn_name, log=logger, **kwargs)
                    if df is not None and not df.empty:
                        result["income_statement"] = df.head(8).to_dict("records")
                        break
                except Exception as e:
                    logger.warning("利润表获取失败(%s): %s", fn_name, e)

            # 资产负债表
            for fn, fn_name, kwargs in [
                (ak.stock_financial_report_sina, "ak.stock_financial_report_sina(资产负债表)", {"stock": code, "symbol": "资产负债表"}),
                (ak.stock_balance_sheet_by_report_em, "ak.stock_balance_sheet_by_report_em", {"symbol": code}),
            ]:
                try:
                    df = timed_api_call(fn, call_name=fn_name, log=logger, **kwargs)
                    if df is not None and not df.empty:
                        result["balance_sheet"] = df.head(8).to_dict("records")
                        break
                except Exception as e:
                    logger.warning("资产负债表获取失败(%s): %s", fn_name, e)

            # 现金流量表
            for fn, fn_name, kwargs in [
                (ak.stock_financial_report_sina, "ak.stock_financial_report_sina(现金流量表)", {"stock": code, "symbol": "现金流量表"}),
                (ak.stock_cash_flow_sheet_by_report_em, "ak.stock_cash_flow_sheet_by_report_em", {"symbol": code}),
            ]:
                try:
                    df = timed_api_call(fn, call_name=fn_name, log=logger, **kwargs)
                    if df is not None and not df.empty:
                        result["cash_flow"] = df.head(8).to_dict("records")
                        break
                except Exception as e:
                    logger.warning("现金流量表获取失败(%s): %s", fn_name, e)

            # 关键指标
            try:
                df = timed_api_call(
                    ak.stock_financial_analysis_indicator,
                    call_name="ak.stock_financial_analysis_indicator",
                    log=logger,
                    symbol=code,
                )
                if df is not None and not df.empty:
                    result["key_indicators"] = df.head(8).to_dict("records")
            except Exception as e:
                logger.warning("关键财务指标获取失败: %s", e)

            if not result:
                return {"stock_code": stock_code, "error": "akshare财务数据全部获取失败"}

            result.update({"stock_code": stock_code, "market": "A", "data_source": "akshare"})
            result["text_summary"] = self._format_to_text(result)
            result["key_metrics"] = self._extract_key_metrics(result)
            return result

        except ImportError:
            return {"stock_code": stock_code, "error": "akshare未安装"}
        except Exception as e:
            logger.error("akshare财务数据获取失败: %s", e)
            return {"stock_code": stock_code, "error": str(e)}

    def _fetch_tushare_financials(self, stock_code: str) -> Dict[str, Any]:
        """通过 tushare 获取A股财务数据 (备用)"""
        token = os.environ.get("TUSHARE_TOKEN", "")
        if not token:
            return {"stock_code": stock_code, "error": "TUSHARE_TOKEN未配置"}

        try:
            import tushare as ts
            ts.set_token(token)
            pro = ts.pro_api()

            code = stock_code.replace(".SH", "").replace(".SZ", "").replace(".BJ", "")
            ts_code = f"{code}.SH" if code.startswith("6") else \
                      f"{code}.SZ" if code.startswith(("0", "3")) else \
                      f"{code}.BJ" if code.startswith(("4", "8", "9")) else f"{code}.SH"

            result = {}

            for attr, call_name, kw in [
                ("income_statement", "tushare.pro.income", {"ts_code": ts_code, "limit": 8}),
                ("balance_sheet",    "tushare.pro.balancesheet", {"ts_code": ts_code, "limit": 8}),
                ("cash_flow",        "tushare.pro.cashflow", {"ts_code": ts_code, "limit": 8}),
                ("key_indicators",   "tushare.pro.fina_indicator", {"ts_code": ts_code, "limit": 8}),
            ]:
                fn_map = {
                    "tushare.pro.income": pro.income,
                    "tushare.pro.balancesheet": pro.balancesheet,
                    "tushare.pro.cashflow": pro.cashflow,
                    "tushare.pro.fina_indicator": pro.fina_indicator,
                }
                try:
                    df = timed_api_call(fn_map[call_name], call_name=call_name, log=logger, **kw)
                    if df is not None and not df.empty:
                        result[attr] = df.to_dict("records")
                except Exception as e:
                    logger.warning("%s 获取失败: %s", call_name, e)

            if not result:
                return {"stock_code": stock_code, "error": "tushare财务数据全部获取失败"}

            result.update({"stock_code": stock_code, "market": "A", "data_source": "tushare"})
            result["text_summary"] = self._format_to_text(result)
            result["key_metrics"] = self._extract_key_metrics(result)
            return result

        except ImportError:
            return {"stock_code": stock_code, "error": "tushare未安装"}
        except Exception as e:
            logger.error("tushare财务数据获取失败: %s", e)
            return {"stock_code": stock_code, "error": str(e)}

    def _fetch_yfinance_financials(self, stock_code: str) -> Dict[str, Any]:
        """通过yfinance获取财务数据"""
        try:
            import yfinance as yf

            ticker = yf.Ticker(stock_code)
            result = {}

            for attr, call_name, prop in [
                ("income_statement",  f"yfinance.financials({stock_code})",          "financials"),
                ("balance_sheet",     f"yfinance.balance_sheet({stock_code})",        "balance_sheet"),
                ("cash_flow",         f"yfinance.cashflow({stock_code})",             "cashflow"),
                ("quarterly_income",  f"yfinance.quarterly_financials({stock_code})", "quarterly_financials"),
            ]:
                try:
                    df = timed_api_call(
                        lambda p=prop: getattr(ticker, p),
                        call_name=call_name,
                        log=logger,
                    )
                    if df is not None and not df.empty:
                        result[attr] = df.to_dict()
                except Exception as e:
                    logger.warning("%s 获取失败: %s", call_name, e)

            result.update({"stock_code": stock_code, "market": "non-A", "data_source": "yfinance"})
            result["text_summary"] = self._format_to_text(result)
            result["key_metrics"] = self._extract_key_metrics(result)
            return result

        except Exception as e:
            logger.error("yfinance财务数据获取失败: %s", e)
            return {"stock_code": stock_code, "error": str(e)}

    # ─────────────────────────────────────────────────────────────────────────
    # key_metrics 提取 — 供图表渲染使用
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _get_val(row: dict, *candidates) -> Optional[float]:
        """从 dict 中依次尝试多个 key，返回第一个有效 float"""
        for key in candidates:
            if key in row:
                val = row[key]
                if val is not None:
                    try:
                        f = float(val)
                        if f == f:  # NaN check
                            return f
                    except (TypeError, ValueError):
                        pass
        return None

    def _extract_key_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        从原始财务报表中提取结构化数值序列，供图表渲染。

        Returns dict:
            periods:          [str]  — 报告期标签（YYYY-MM）
            revenue:          [float] — 营业总收入（元）
            net_profit:       [float] — 归母净利润（元）
            gross_margin:     [float] — 毛利率（%）
            operating_margin: [float] — 营业利润率（%）
            net_margin:       [float] — 净利率（%）
            operating_cf:     [float] — 经营活动现金流净额（元）
            roe:              [float] — ROE加权（%）
        """
        metrics: Dict[str, List] = {
            "periods":          [],
            "revenue":          [],
            "net_profit":       [],
            "gross_margin":     [],
            "operating_margin": [],
            "net_margin":       [],
            "operating_cf":     [],
            "roe":              [],
            "total_assets":     [],
            "total_liab":       [],
            "equity":           [],
        }

        income       = data.get("income_statement", [])
        cash_flow    = data.get("cash_flow", [])
        balance_sheet = data.get("balance_sheet", [])
        key_ind      = data.get("key_indicators", [])

        if not isinstance(income, list) or not income:
            return metrics

        # ── 利润表解析 ─────────────────────────────────────────────────────────
        for row in income[:8]:
            if not isinstance(row, dict):
                continue

            date = str(
                self._get_str(row, "报告日期", "报告日", "REPORT_DATE", "end_date", "ann_date") or ""
            )[:7]
            if not date or date == "None":
                continue

            rev = self._get_val(row,
                "营业总收入", "营业收入", "TOTAL_OPERATE_INCOME", "total_revenue", "revenue")
            cost = self._get_val(row,
                "营业总成本", "营业成本", "OPERATE_COST", "TOTAL_OPERATE_COST",
                "total_cogs", "oper_cost")
            op_profit = self._get_val(row,
                "营业利润", "OPERATE_PROFIT", "operate_profit")
            net_p = self._get_val(row,
                "归属于母公司股东的净利润", "净利润", "PARENT_NETPROFIT", "NETPROFIT",
                "n_income_attr_p", "n_income")

            if rev is None or rev <= 0:
                continue

            metrics["periods"].append(date)
            metrics["revenue"].append(rev)
            metrics["net_profit"].append(net_p)

            gm = ((rev - cost) / rev * 100) if cost is not None else None
            metrics["gross_margin"].append(round(gm, 2) if gm is not None else None)
            metrics["operating_margin"].append(
                round(op_profit / rev * 100, 2) if op_profit is not None else None)
            metrics["net_margin"].append(
                round(net_p / rev * 100, 2) if net_p is not None else None)

        # ── 现金流量表 ─────────────────────────────────────────────────────────
        if isinstance(cash_flow, list):
            cf_vals = []
            for row in cash_flow[:8]:
                if not isinstance(row, dict):
                    continue
                cf = self._get_val(row,
                    "经营活动产生的现金流量净额", "经营活动现金流量净额",
                    "NETCASH_OPERATE", "n_cashflow_act", "net_operate_cash_flow")
                if cf is not None:
                    cf_vals.append(cf)
            metrics["operating_cf"] = cf_vals[:len(metrics["periods"])]

        # ── 资产负债表 ─────────────────────────────────────────────────────────
        if isinstance(balance_sheet, list):
            ta_vals, tl_vals, eq_vals = [], [], []
            for row in balance_sheet[:8]:
                if not isinstance(row, dict):
                    continue
                ta = self._get_val(row, "资产总计", "TOTAL_ASSETS", "total_assets",
                                   "balance_total_assets")
                tl = self._get_val(row, "负债合计", "TOTAL_LIABILITIES", "total_liab",
                                   "balance_total_liab")
                eq = self._get_val(row, "所有者权益合计", "TOTAL_EQUITY", "total_equity",
                                   "equity_total")
                ta_vals.append(ta)
                tl_vals.append(tl)
                eq_vals.append(eq)
            n = len(metrics["periods"])
            metrics["total_assets"] = list(reversed(ta_vals[:n]))
            metrics["total_liab"]   = list(reversed(tl_vals[:n]))
            metrics["equity"]       = list(reversed(eq_vals[:n]))

        # ── 关键财务指标 (ROE / 毛利率 补充) ─────────────────────────────────
        if isinstance(key_ind, list) and key_ind:
            roe_vals = []
            for i, row in enumerate(key_ind[:8]):
                if not isinstance(row, dict):
                    continue
                roe = self._get_val(row,
                    "净资产收益率加权(%)", "ROE（加权）(%)", "净资产收益率(加权)",
                    "roe_waa", "roe")
                gm_ki = self._get_val(row,
                    "销售毛利率(%)", "毛利率(%)", "grossprofit_margin")
                roe_vals.append(roe)

                # 若利润表中毛利率为 None，用 key_indicators 补充
                if i < len(metrics["gross_margin"]) and metrics["gross_margin"][i] is None:
                    if gm_ki is not None:
                        metrics["gross_margin"][i] = round(gm_ki, 2)

            metrics["roe"] = roe_vals[:len(metrics["periods"])]
        else:
            # key_indicators 无数据时，从净利润/净资产推算 ROE（年化）
            n = len(metrics["periods"])
            roe_vals = []
            for i in range(n):
                np_i = metrics["net_profit"][i] if i < len(metrics["net_profit"]) else None
                eq_i = metrics["equity"][i] if i < len(metrics["equity"]) else None
                if np_i is not None and eq_i and eq_i != 0:
                    roe_vals.append(round(np_i / eq_i * 100, 2))
                else:
                    roe_vals.append(None)
            metrics["roe"] = roe_vals

        # ── 时间顺序（最新优先 → 由旧到新）─────────────────────────────────
        n = len(metrics["periods"])
        for k in metrics:
            lst = metrics[k]
            if lst:
                # 补齐长度
                while len(lst) < n:
                    lst.append(None)
                metrics[k] = list(reversed(lst[:n]))

        return metrics

    @staticmethod
    def _get_str(row: dict, *candidates) -> Optional[str]:
        for key in candidates:
            if key in row and row[key] is not None:
                return str(row[key])
        return None

    # 展示给 LLM 的关键财务列 (label, [候选列名列表])
    _INCOME_GROUPS: List = [
        ("报告期",        ["报告日", "报告日期", "REPORT_DATE", "end_date"]),
        ("营收(亿)",      ["营业总收入", "营业收入", "TOTAL_OPERATE_INCOME", "total_revenue"]),
        ("净利润(亿)",    ["净利润", "NETPROFIT", "n_income"]),
        ("归母净利润(亿)", ["归属于母公司股东的净利润", "PARENT_NETPROFIT", "n_income_attr_p"]),
        ("营业总成本(亿)", ["营业总成本", "营业成本", "TOTAL_OPERATE_COST", "OPERATE_COST"]),
        ("营业利润(亿)",  ["营业利润", "OPERATE_PROFIT", "operate_profit"]),
    ]
    _BS_GROUPS: List = [
        ("报告期",       ["报告日", "报告日期", "REPORT_DATE", "end_date"]),
        ("总资产(亿)",   ["资产总计", "TOTAL_ASSETS", "total_assets"]),
        ("流动资产(亿)", ["流动资产合计", "CURRENT_ASSETS_TOTAL", "total_cur_assets"]),
        ("总负债(亿)",   ["负债合计", "TOTAL_LIABILITIES", "total_liab"]),
        ("流动负债(亿)", ["流动负债合计", "CURRENT_LIABILITIES_TOTAL", "total_cur_liab"]),
        ("股东权益(亿)", ["所有者权益合计", "TOTAL_EQUITY", "total_equity"]),
        ("货币资金(亿)", ["货币资金", "MONETARYFUNDS", "money_cap"]),
    ]
    _CF_GROUPS: List = [
        ("报告期",          ["报告日", "报告日期", "REPORT_DATE", "end_date"]),
        ("经营现金流(亿)",  ["经营活动产生的现金流量净额", "经营活动现金流量净额",
                             "NETCASH_OPERATE", "n_cashflow_act"]),
        ("投资现金流(亿)",  ["投资活动产生的现金流量净额", "NETCASH_INVEST", "n_cashflow_inv_act"]),
        ("筹资现金流(亿)",  ["筹资活动产生的现金流量净额", "NETCASH_FINANCE", "n_cash_flows_fnc_act"]),
    ]

    @staticmethod
    def _select_cols(rows: List[dict], groups: List) -> List[dict]:
        """从原始records中按字段组选出关键列，转换为可读标签和亿元单位"""
        out = []
        for row in rows:
            rec = {}
            for label, candidates in groups:
                for src in candidates:
                    if src in row and row[src] is not None:
                        val = row[src]
                        if label == "报告期":
                            s = str(val).strip()
                            # Normalize YYYYMMDD → YYYY-MM, YYYY-MM-DD → YYYY-MM
                            if len(s) == 8 and s.isdigit():
                                s = f"{s[:4]}-{s[4:6]}"
                            else:
                                s = s[:7]
                            rec[label] = s
                        else:
                            try:
                                fval = float(val)
                                rec[label] = f"{fval/1e8:.2f}" if fval == fval else "—"
                            except (TypeError, ValueError):
                                rec[label] = str(val)
                        break  # 找到第一个匹配的候选列即停止
            if rec:
                out.append(rec)
        return out

    def _format_to_text(self, data: Dict[str, Any]) -> str:
        lines = []
        if "income_statement" in data and isinstance(data["income_statement"], list):
            lines.append("## 利润表 (最近8个报告期，单位: 亿元)")
            rows = self._select_cols(data["income_statement"][:8], self._INCOME_GROUPS)
            lines.append(pd.DataFrame(rows).to_string(index=False) if rows else "数据格式异常")
        if "balance_sheet" in data:
            lines.append("\n## 资产负债表 (最近8个报告期，单位: 亿元)")
            bs = data["balance_sheet"]
            if isinstance(bs, list):
                rows = self._select_cols(bs[:8], self._BS_GROUPS)
                lines.append(pd.DataFrame(rows).to_string(index=False) if rows else "数据格式异常")
            else:
                lines.append(pd.DataFrame(bs).to_string(max_rows=20, max_cols=8))
        if "cash_flow" in data:
            lines.append("\n## 现金流量表 (最近8个报告期，单位: 亿元)")
            cf = data["cash_flow"]
            if isinstance(cf, list):
                rows = self._select_cols(cf[:8], self._CF_GROUPS)
                lines.append(pd.DataFrame(rows).to_string(index=False) if rows else "数据格式异常")
            else:
                lines.append(pd.DataFrame(cf).to_string(max_rows=20, max_cols=8))
        if "key_indicators" in data and data["key_indicators"]:
            lines.append("\n## 关键财务指标")
            ki = data["key_indicators"]
            if isinstance(ki, list) and ki:
                lines.append(pd.DataFrame(ki).to_string(max_rows=8, max_cols=15))
        return "\n".join(lines) if lines else "财务数据暂不可用"
