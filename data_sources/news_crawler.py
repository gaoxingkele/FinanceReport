"""
新闻数据采集模块 - 源自FinRpt的新闻采集 + 去重逻辑

支持:
- 东方财富股吧 (A股)
- 新浪财经快讯 (A股)
- 通用新闻搜索 (yfinance)
"""
import logging
import hashlib
import time
from typing import Dict, Any, List

import requests

from utils.remote_call import timed_api_call

logger = logging.getLogger(__name__)


class NewsCrawler:
    """新闻采集智能体"""

    def __init__(self, language: str = "zh", max_items: int = 50, dedup_threshold: float = 0.85):
        self.language = language
        self.max_items = max_items
        self.dedup_threshold = dedup_threshold
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def fetch(self, stock_code: str, company_name: str = "", market: str = "A") -> Dict[str, Any]:
        all_news = []

        if market == "A":
            em_news = self._fetch_eastmoney(stock_code)
            all_news.extend(em_news)
            sina_news = self._fetch_sina(stock_code, company_name)
            all_news.extend(sina_news)
        else:
            search_news = self._fetch_generic(stock_code, company_name)
            all_news.extend(search_news)

        deduped = self._dedup_news(all_news)[:self.max_items]
        text = self._format_news_text(deduped)

        return {
            "stock_code": stock_code,
            "news_items": deduped,
            "news_count": len(deduped),
            "news_text": text,
            "sources": list(set(n.get("source", "") for n in deduped)),
        }

    def _fetch_eastmoney(self, stock_code: str) -> List[Dict[str, Any]]:
        """东方财富个股新闻"""
        news_list = []
        code = stock_code.replace(".SH", "").replace(".SZ", "").replace(".BJ", "")

        # 优先尝试 HTTP API
        url = (
            f"https://search-api-web.eastmoney.com/search/jsonp"
            f"?cb=jQuery&param=%7B%22uid%22%3A%22%22%2C%22keyword%22%3A%22{code}%22"
            f"%2C%22type%22%3A%5B%22cmsArticleWebOld%22%5D%2C%22client%22%3A%22web%22"
            f"%2C%22clientType%22%3A%22web%22%2C%22clientVersion%22%3A%22curr%22"
            f"%2C%22param%22%3A%7B%22cmsArticleWebOld%22%3A%7B%22searchScope%22%3A%22default%22"
            f"%2C%22sort%22%3A%22default%22%2C%22pageIndex%22%3A1%2C%22pageSize%22%3A20"
            f"%2C%22preTag%22%3A%22%22%2C%22postTag%22%3A%22%22%7D%7D%7D"
        )
        try:
            import json as _json
            logger.info("[REMOTE→] requests.get  url=eastmoney-search  code=%s", code)
            start = time.time()
            resp = requests.get(url, headers=self.headers, timeout=10)
            elapsed = time.time() - start
            logger.info("[REMOTE✓] requests.get  status=%s  耗时=%.1fs", resp.status_code, elapsed)

            if resp.status_code == 200:
                text = resp.text
                json_str = text[text.index("(") + 1: text.rindex(")")]
                data = _json.loads(json_str)
                articles = data.get("result", {}).get("cmsArticleWebOld", {}).get("list", [])
                for art in articles[:20]:
                    news_list.append({
                        "title": art.get("title", "").replace("<em>", "").replace("</em>", ""),
                        "content": art.get("content", "")[:500],
                        "date": art.get("date", ""),
                        "source": "东方财富",
                        "url": art.get("url", ""),
                    })
        except Exception as e:
            logger.warning("[REMOTE✗] 东方财富HTTP新闻获取失败: %s", e)

        # 备用: akshare stock_news_em
        if not news_list:
            try:
                import akshare as ak
                df = timed_api_call(
                    ak.stock_news_em,
                    call_name="ak.stock_news_em",
                    log=logger,
                    symbol=code,
                )
                if df is not None and not df.empty:
                    for _, row in df.head(30).iterrows():
                        news_list.append({
                            "title": str(row.get("新闻标题", "")),
                            "content": str(row.get("新闻内容", ""))[:500],
                            "date": str(row.get("发布时间", "")),
                            "source": "东方财富",
                            "url": str(row.get("新闻链接", "")),
                        })
            except Exception as e:
                logger.warning("akshare东方财富新闻获取失败: %s", e)

        return news_list

    def _fetch_sina(self, stock_code: str, company_name: str) -> List[Dict[str, Any]]:
        """新浪财经个股新闻（ak.stock_news_em 第二次调用，来源标记为新浪）
        使用 ak.news_cctv 或 ak.stock_info_global_sina 等补充宏观新闻。
        实际上 akshare 对个股新闻的新浪接口与东方财富接口是同一函数，
        这里改为抓取财经新闻大盘快讯并按关键词过滤。
        """
        news_list = []
        try:
            import akshare as ak

            # 财经新闻大盘快讯（财联社/财经大盘）
            df = timed_api_call(
                ak.stock_news_main_cx,
                call_name="ak.stock_news_main_cx",
                log=logger,
            )
            if df is not None and not df.empty and company_name:
                keyword = company_name[:4]
                # 列名可能为 title/content 或中文
                title_col = next((c for c in df.columns if "标题" in c or "title" in c.lower()), None)
                content_col = next((c for c in df.columns if "内容" in c or "content" in c.lower()), None)
                date_col = next((c for c in df.columns if "时间" in c or "date" in c.lower()), None)
                if title_col:
                    mask = df[title_col].astype(str).str.contains(keyword, na=False)
                    if content_col:
                        mask |= df[content_col].astype(str).str.contains(keyword, na=False)
                    df = df[mask].head(20)
                    for _, row in df.iterrows():
                        news_list.append({
                            "title": str(row.get(title_col, "")),
                            "content": str(row.get(content_col, ""))[:500] if content_col else "",
                            "date": str(row.get(date_col, "")) if date_col else "",
                            "source": "财联社",
                        })
        except Exception as e:
            logger.warning("财联社快讯获取失败: %s", e)

        return news_list

    def _fetch_generic(self, stock_code: str, company_name: str) -> List[Dict[str, Any]]:
        """通用新闻搜索 (yfinance, 非A股)"""
        try:
            import yfinance as yf
            from datetime import datetime

            ticker = yf.Ticker(stock_code)
            news = timed_api_call(
                lambda: ticker.news or [],
                call_name=f"yfinance.news({stock_code})",
                log=logger,
            )
            return [
                {
                    "title": item.get("title", ""),
                    "content": item.get("title", ""),
                    "date": datetime.fromtimestamp(item.get("providerPublishTime", 0)).strftime("%Y-%m-%d %H:%M"),
                    "source": item.get("publisher", ""),
                    "url": item.get("link", ""),
                }
                for item in news[:20]
            ]
        except Exception as e:
            logger.warning("通用新闻获取失败: %s", e)
            return []

    def _dedup_news(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not news_list:
            return []
        seen_hashes = set()
        phase1 = []
        for news in news_list:
            title = news.get("title", "").strip()
            if not title or len(title) < 5:
                continue
            h = hashlib.md5(title.encode()).hexdigest()
            if h not in seen_hashes:
                seen_hashes.add(h)
                phase1.append(news)

        phase2 = []
        for news in phase1:
            title = news.get("title", "")
            if not any(self._jaccard(title, e.get("title", "")) > self.dedup_threshold for e in phase2):
                phase2.append(news)
        return phase2

    @staticmethod
    def _jaccard(s1: str, s2: str) -> float:
        set1, set2 = set(s1), set(s2)
        if not set1 and not set2:
            return 1.0
        union = len(set1 | set2)
        return len(set1 & set2) / union if union > 0 else 0.0

    @staticmethod
    def _format_news_text(news_list: List[Dict[str, Any]]) -> str:
        lines = []
        for i, news in enumerate(news_list, 1):
            lines.append(f"[{i}] [{news.get('date', '')}] [{news.get('source', '')}] {news.get('title', '')}")
            content = news.get("content", "")
            if content and content != news.get("title", ""):
                lines.append(f"    {content[:200]}")
            lines.append("")
        return "\n".join(lines)
