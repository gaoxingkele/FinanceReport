"""
行情数据采集模块 - 源自FinRpt的Dataer + 扩展

支持:
- akshare: A股 (主)
- tushare: A股 (备用)
- yfinance: 美股/港股/降级
- 自动检测市场并选择合适的数据源
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import pandas as pd

from utils.remote_call import timed_api_call

logger = logging.getLogger(__name__)


class MarketDataAgent:
    """行情数据采集智能体"""

    def __init__(self, language: str = "zh"):
        self.language = language

    def fetch(self, stock_code: str, period_days: int = 180) -> Dict[str, Any]:
        market = self._detect_market(stock_code)
        logger.info("检测到市场: %s, 股票: %s", market, stock_code)

        if market == "A":
            return self._fetch_a_share(stock_code, period_days)
        elif market == "US":
            return self._fetch_us_stock(stock_code, period_days)
        elif market == "HK":
            return self._fetch_hk_stock(stock_code, period_days)
        else:
            return self._fetch_generic(stock_code, period_days)

    def _detect_market(self, stock_code: str) -> str:
        code = stock_code.strip().upper()
        if code.endswith(".HK"):
            return "HK"
        if code.isdigit() and len(code) == 6:
            return "A"
        if code.endswith((".SH", ".SZ", ".BJ")):
            return "A"
        return "US"

    def _fetch_a_share(self, stock_code: str, period_days: int) -> Dict[str, Any]:
        """获取A股数据，优先 akshare，失败后转 tushare"""
        result = self._fetch_akshare(stock_code, period_days)
        if "error" not in result and result.get("price_data"):
            return result

        logger.info("akshare获取失败，尝试tushare备用: %s", stock_code)
        result = self._fetch_tushare(stock_code, period_days)
        if "error" not in result and result.get("price_data"):
            return result

        logger.info("tushare获取失败，降级到yfinance: %s", stock_code)
        return self._fetch_generic(stock_code, period_days)

    def _fetch_akshare(self, stock_code: str, period_days: int) -> Dict[str, Any]:
        """通过 akshare 获取A股数据"""
        try:
            import akshare as ak

            code = stock_code.replace(".SH", "").replace(".SZ", "").replace(".BJ", "")
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y%m%d")

            try:
                df = timed_api_call(
                    ak.stock_zh_a_hist,
                    call_name="ak.stock_zh_a_hist",
                    log=logger,
                    symbol=code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq",
                )
            except Exception as e:
                logger.error("akshare A股行情获取失败: %s", e)
                return {"stock_code": stock_code, "error": str(e)}

            if df is None or df.empty:
                return {"stock_code": stock_code, "error": "akshare返回空数据"}

            col_map = {
                "日期": "date", "开盘": "open", "收盘": "close",
                "最高": "high", "最低": "low", "成交量": "volume",
                "成交额": "amount", "涨跌幅": "pct_change",
            }
            df = df.rename(columns=col_map)

            company_info = self._get_akshare_company_info(code)

            try:
                idx_df = timed_api_call(
                    ak.stock_zh_index_daily,
                    call_name="ak.stock_zh_index_daily(sh000300)",
                    log=logger,
                    symbol="sh000300",
                )
                idx_df = idx_df.tail(period_days) if idx_df is not None else pd.DataFrame()
            except Exception:
                idx_df = pd.DataFrame()

            return {
                "stock_code": stock_code,
                "market": "A",
                "price_data": df.to_dict("records") if len(df) <= 500 else df.tail(120).to_dict("records"),
                "price_df": df,
                "company_info": company_info,
                "benchmark_data": idx_df.to_dict("records") if not idx_df.empty else [],
                "latest_price": df.iloc[-1].to_dict() if not df.empty else {},
                "summary": self._compute_summary(df),
                "data_source": "akshare",
            }

        except ImportError:
            return {"stock_code": stock_code, "error": "akshare未安装"}
        except Exception as e:
            logger.error("akshare A股数据获取失败: %s", e)
            return {"stock_code": stock_code, "error": str(e)}

    def _get_akshare_company_info(self, code: str) -> Dict[str, Any]:
        """从 akshare 获取公司信息，规范化字段名"""
        try:
            import akshare as ak
            info_df = timed_api_call(
                ak.stock_individual_info_em,
                call_name="ak.stock_individual_info_em",
                log=logger,
                symbol=code,
            )
            raw = {row["item"]: row["value"] for _, row in info_df.iterrows()}
            return {
                "company_name": raw.get("股票简称", raw.get("股票名称", code)),
                "stock_code": raw.get("股票代码", code),
                "industry": raw.get("行业", ""),
                "market_cap": raw.get("总市值", ""),
                "float_cap": raw.get("流通市值", ""),
                "pe_ratio": raw.get("市盈率(动)", raw.get("市盈率", "")),
                "pb_ratio": raw.get("市净率", ""),
                "listing_date": raw.get("上市时间", ""),
            }
        except Exception as e:
            logger.warning("akshare公司信息获取失败: %s", e)
            return {"company_name": code, "stock_code": code}

    def _fetch_tushare(self, stock_code: str, period_days: int) -> Dict[str, Any]:
        """通过 tushare 获取A股数据 (备用)"""
        token = os.environ.get("TUSHARE_TOKEN", "")
        if not token:
            return {"stock_code": stock_code, "error": "TUSHARE_TOKEN未配置"}

        try:
            import tushare as ts
            ts.set_token(token)
            pro = ts.pro_api()

            code = stock_code.replace(".SH", "").replace(".SZ", "").replace(".BJ", "")
            if code.startswith("6"):
                ts_code = f"{code}.SH"
            elif code.startswith(("0", "3")):
                ts_code = f"{code}.SZ"
            elif code.startswith(("4", "8", "9")):
                ts_code = f"{code}.BJ"
            else:
                ts_code = f"{code}.SH"

            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y%m%d")

            try:
                df = timed_api_call(
                    pro.daily,
                    call_name="tushare.pro.daily",
                    log=logger,
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                )
            except Exception as e:
                logger.error("tushare日线数据获取失败: %s", e)
                return {"stock_code": stock_code, "error": str(e)}

            if df is None or df.empty:
                return {"stock_code": stock_code, "error": "tushare返回空数据"}

            df = df.sort_values("trade_date")
            df = df.rename(columns={
                "trade_date": "date", "vol": "volume", "pct_chg": "pct_change",
            })

            company_info = {"company_name": code, "stock_code": code}
            try:
                basic = timed_api_call(
                    pro.stock_basic,
                    call_name="tushare.pro.stock_basic",
                    log=logger,
                    ts_code=ts_code,
                    fields="name,industry,list_date",
                )
                if basic is not None and not basic.empty:
                    row = basic.iloc[0]
                    company_info = {
                        "company_name": row.get("name", code),
                        "stock_code": ts_code,
                        "industry": row.get("industry", ""),
                        "listing_date": row.get("list_date", ""),
                    }
            except Exception as e:
                logger.warning("tushare公司基本信息获取失败: %s", e)

            return {
                "stock_code": stock_code,
                "market": "A",
                "price_data": df.to_dict("records") if len(df) <= 500 else df.tail(120).to_dict("records"),
                "price_df": df,
                "company_info": company_info,
                "benchmark_data": [],
                "latest_price": df.iloc[-1].to_dict() if not df.empty else {},
                "summary": self._compute_summary(df),
                "data_source": "tushare",
            }

        except ImportError:
            return {"stock_code": stock_code, "error": "tushare未安装"}
        except Exception as e:
            logger.error("tushare A股数据获取失败: %s", e)
            return {"stock_code": stock_code, "error": str(e)}

    def _fetch_us_stock(self, stock_code: str, period_days: int) -> Dict[str, Any]:
        return self._fetch_yfinance(stock_code, period_days, market="US")

    def _fetch_hk_stock(self, stock_code: str, period_days: int) -> Dict[str, Any]:
        return self._fetch_yfinance(stock_code, period_days, market="HK")

    def _fetch_yfinance(self, stock_code: str, period_days: int, market: str = "US") -> Dict[str, Any]:
        """通过yfinance获取数据"""
        try:
            import yfinance as yf

            ticker = yf.Ticker(stock_code)
            try:
                df = timed_api_call(
                    ticker.history,
                    call_name=f"yfinance.history({stock_code})",
                    log=logger,
                    period=f"{period_days}d",
                )
            except Exception as e:
                logger.error("yfinance history获取失败: %s", e)
                return {"stock_code": stock_code, "market": market, "error": str(e)}

            if df.empty:
                return {"stock_code": stock_code, "market": market, "error": "无数据"}

            df = df.reset_index()
            df.columns = [c.lower().replace(" ", "_") for c in df.columns]

            info = {"company_name": stock_code}
            try:
                raw_info = timed_api_call(
                    lambda: ticker.info,
                    call_name=f"yfinance.info({stock_code})",
                    log=logger,
                )
                info = {
                    "company_name": raw_info.get("longName", stock_code),
                    "industry": raw_info.get("industry", ""),
                    "sector": raw_info.get("sector", ""),
                    "market_cap": raw_info.get("marketCap", 0),
                    "pe_ratio": raw_info.get("trailingPE", 0),
                    "pb_ratio": raw_info.get("priceToBook", 0),
                    "dividend_yield": raw_info.get("dividendYield", 0),
                    "52w_high": raw_info.get("fiftyTwoWeekHigh", 0),
                    "52w_low": raw_info.get("fiftyTwoWeekLow", 0),
                }
            except Exception as e:
                logger.warning("yfinance info获取失败: %s", e)

            return {
                "stock_code": stock_code,
                "market": market,
                "price_data": df.to_dict("records") if len(df) <= 500 else df.tail(120).to_dict("records"),
                "price_df": df,
                "company_info": info,
                "benchmark_data": [],
                "latest_price": df.iloc[-1].to_dict() if not df.empty else {},
                "summary": self._compute_summary(df),
                "data_source": "yfinance",
            }

        except Exception as e:
            logger.error("yfinance数据获取失败: %s", e)
            return {"stock_code": stock_code, "market": market, "error": str(e)}

    def _fetch_generic(self, stock_code: str, period_days: int) -> Dict[str, Any]:
        return self._fetch_yfinance(stock_code, period_days, market="unknown")

    @staticmethod
    def _compute_summary(df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {}
        close_col = "close" if "close" in df.columns else "Close"
        vol_col = "volume" if "volume" in df.columns else "Volume"
        try:
            close = df[close_col].astype(float)
            return {
                "latest_close": float(close.iloc[-1]),
                "period_high": float(close.max()),
                "period_low": float(close.min()),
                "period_return": float((close.iloc[-1] / close.iloc[0] - 1) * 100),
                "avg_volume": float(df[vol_col].mean()) if vol_col in df.columns else 0,
                "volatility": float(close.pct_change().std() * (252 ** 0.5) * 100),
                "ma5": float(close.rolling(5).mean().iloc[-1]) if len(close) >= 5 else None,
                "ma20": float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else None,
                "ma60": float(close.rolling(60).mean().iloc[-1]) if len(close) >= 60 else None,
                "data_points": len(df),
            }
        except Exception:
            return {"data_points": len(df)}
