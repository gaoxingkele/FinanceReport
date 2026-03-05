"""
Markdown报告生成器

将所有分析结果组织为结构化的Markdown报告
"""
import json
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MarkdownReportBuilder:
    """Markdown格式报告生成器"""

    def __init__(self, output_dir: str = "./output", language: str = "zh"):
        self.output_dir = output_dir
        self.language = language
        os.makedirs(output_dir, exist_ok=True)

    def build(
        self,
        stock_code: str,
        data: Dict[str, Any],
        charts: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        生成Markdown报告

        Returns:
            报告文件路径
        """
        company_info = data.get("company_info", {})
        save = data.get("save", {})
        company_name = company_info.get("company_name", stock_code)

        sections = []

        # 标题
        sections.append(f"# {company_name}({stock_code}) 深度研究报告")
        sections.append(f"\n> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        sections.append("> 免责声明: 本报告由AI生成，仅供研究参考，不构成投资建议。\n")

        # 目录
        sections.append("## 目录\n")
        sections.append("1. [执行摘要](#执行摘要)")
        sections.append("2. [公司概况](#公司概况)")
        sections.append("3. [财务分析](#财务分析)")
        sections.append("4. [竞争格局](#竞争格局)")
        sections.append("5. [新闻分析](#新闻分析)")
        sections.append("6. [风险评估](#风险评估)")
        sections.append("7. [趋势预测](#趋势预测)")
        sections.append("8. [投资建议](#投资建议)")
        sections.append("9. [附录: 图表](#附录图表)\n")

        # 执行摘要
        advisor = save.get("InvestmentAdvisor", {})
        sections.append("## 执行摘要\n")
        sections.append(advisor.get("executive_summary", "暂无摘要"))
        rec = advisor.get("recommendation", {})
        if rec:
            sections.append(f"\n**投资评级**: {rec.get('action', 'N/A')}")
            sections.append(f"**信心水平**: {rec.get('confidence', 'N/A')}")
            sections.append(f"**投资周期**: {rec.get('time_horizon', 'N/A')}")

        # 公司概况
        sections.append("\n## 公司概况\n")
        for k, v in company_info.items():
            if k not in ("_raw",) and v:
                sections.append(f"- **{k}**: {v}")

        # 市场行情摘要
        summary = data.get("market_data", {}).get("summary", {})
        if summary:
            sections.append("\n### 市场行情\n")
            sections.append(f"- 最新收盘价: {summary.get('latest_close', 'N/A')}")
            sections.append(f"- 区间涨幅: {summary.get('period_return', 'N/A'):.2f}%"
                          if isinstance(summary.get('period_return'), (int, float)) else "")
            sections.append(f"- 年化波动率: {summary.get('volatility', 'N/A'):.2f}%"
                          if isinstance(summary.get('volatility'), (int, float)) else "")

        # 财务分析
        sections.append("\n## 财务分析\n")
        fin = save.get("FinancialAnalyst", {})
        self._add_financial_section(sections, fin)

        # 竞争格局
        sections.append("\n## 竞争格局\n")
        comp = save.get("CompetitiveAnalyst", {})
        self._add_competitive_section(sections, comp)

        # 新闻分析
        sections.append("\n## 新闻分析\n")
        news = save.get("NewsAnalyst", {})
        self._add_news_section(sections, news)

        # 风险评估
        sections.append("\n## 风险评估\n")
        risk = save.get("RiskAssessor", {})
        self._add_risk_section(sections, risk)

        # 趋势预测
        sections.append("\n## 趋势预测\n")
        pred = save.get("Predictor", {})
        self._add_prediction_section(sections, pred)

        # 投资建议
        sections.append("\n## 投资建议\n")
        self._add_advisor_section(sections, advisor)

        # 图表
        if charts:
            sections.append("\n## 附录: 图表\n")
            for name, path in charts.items():
                rel_path = os.path.relpath(path, self.output_dir)
                sections.append(f"### {name}\n")
                sections.append(f"![{name}]({rel_path})\n")

        # 认知层信息
        cognitive_info = data.get("cognitive_info", {})
        if cognitive_info:
            sections.append("\n## 附录: 分析过程\n")
            plan = cognitive_info.get("plan", {})
            if plan:
                sections.append("### 分析计划")
                sections.append(f"- 分析重点: {', '.join(plan.get('analysis_focus', []))}")
                sections.append(f"- 复杂度: {plan.get('estimated_complexity', 'N/A')}")

            review = cognitive_info.get("final_review", {})
            if review:
                sections.append("\n### 质量审核")
                sections.append(f"- 质量评分: {review.get('quality_score', 'N/A')}/10")
                sections.append(f"- 审核通过: {'是' if review.get('approved') else '否'}")

        # 数据来源声明
        sections.append("\n---\n")
        sections.append("## 数据来源声明\n")
        sections.append("| 数据类型 | 数据源 |")
        sections.append("|----------|--------|")
        fin_src = data.get("financial_data", {}).get("data_source", "akshare/tushare/yfinance")
        sections.append(f"| 行情数据 | akshare / yfinance |")
        sections.append(f"| 财务数据 | {fin_src} |")
        sections.append(f"| 新闻资讯 | 新浪财经 / 东方财富 / Yahoo Finance |")
        sections.append(f"| AI分析 | Claude / Gemini / GPT |")
        sections.append(f"\n> **免责声明**: 本报告由AI多智能体系统自动生成，仅供学术研究参考，不构成任何投资建议。投资有风险，入市需谨慎。\n")

        # 写入文件
        content = "\n".join(sections)
        filepath = os.path.join(
            self.output_dir,
            f"{stock_code}_research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
        )

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"[Report] Markdown报告已生成: {filepath}")
        return filepath

    def _add_financial_section(self, sections: List[str], fin: Dict[str, Any]):
        """添加财务分析章节"""
        if not fin or "error" in fin:
            sections.append("财务数据暂不可用。\n")
            return

        # 盈利能力
        prof = fin.get("profitability", {})
        if prof:
            sections.append("### 盈利能力\n")
            sections.append(prof.get("summary", ""))
            sections.append(f"\n趋势: {prof.get('trend', 'N/A')}")

        # 成长能力
        growth = fin.get("growth", {})
        if growth:
            sections.append("\n### 成长能力\n")
            sections.append(growth.get("summary", ""))

        # 偿债能力
        solv = fin.get("solvency", {})
        if solv:
            sections.append("\n### 偿债能力\n")
            sections.append(solv.get("summary", ""))
            sections.append(f"\n风险等级: {solv.get('risk_level', 'N/A')}")

        # 综合评分
        sections.append(f"\n**财务综合评分**: {fin.get('overall_score', 'N/A')}/10\n")

        # 关键风险和亮点
        risks = fin.get("key_risks", [])
        if risks:
            sections.append("**关键风险**:")
            for r in risks:
                sections.append(f"- {r}")

        highlights = fin.get("key_highlights", [])
        if highlights:
            sections.append("\n**关键亮点**:")
            for h in highlights:
                sections.append(f"- {h}")

    def _add_competitive_section(self, sections: List[str], comp: Dict[str, Any]):
        """添加竞争格局章节"""
        if not comp or "error" in comp:
            sections.append("竞争分析暂不可用。\n")
            return

        # 行业概览
        ind = comp.get("industry_overview", {})
        if ind:
            sections.append("### 行业概览\n")
            sections.append(ind.get("description", ""))
            sections.append(f"\n- 市场规模: {ind.get('market_size', 'N/A')}")
            sections.append(f"- 增长率: {ind.get('growth_rate', 'N/A')}")
            sections.append(f"- 竞争强度: {ind.get('competition_intensity', 'N/A')}")

        # 市场地位
        pos = comp.get("market_position", {})
        if pos:
            sections.append("\n### 市场地位\n")
            sections.append(f"- 市场份额: {pos.get('market_share', 'N/A')}")
            sections.append(f"- 市场排名: {pos.get('market_rank', 'N/A')}")
            sections.append(f"- 定价权: {pos.get('pricing_power', 'N/A')}")

        # 竞争护城河
        moat = comp.get("competitive_moat", {})
        if moat:
            sections.append("\n### 竞争护城河\n")
            sections.append(f"**护城河强度**: {moat.get('moat_strength', 'N/A')}")
            for src in moat.get("moat_sources", []):
                sections.append(f"- {src}")

        # SWOT
        swot = comp.get("swot", {})
        if swot:
            sections.append("\n### SWOT分析\n")
            sections.append("| 维度 | 内容 |")
            sections.append("|------|------|")
            for dim, label in [("strengths", "优势"), ("weaknesses", "劣势"),
                               ("opportunities", "机会"), ("threats", "威胁")]:
                items = swot.get(dim, [])
                if items:
                    sections.append(f"| **{label}** | {' / '.join(items[:3])} |")

        # 竞争评分
        score = comp.get("competitive_score")
        if score is not None:
            sections.append(f"\n**竞争力综合评分**: {score}/10")

        outlook = comp.get("outlook", "")
        if outlook:
            sections.append(f"\n**展望**: {outlook}\n")

    def _add_news_section(self, sections: List[str], news: Dict[str, Any]):
        """添加新闻分析章节"""
        if not news or "error" in news:
            sections.append("暂无相关新闻分析。\n")
            return

        sections.append(f"**整体情绪**: {news.get('overall_sentiment', 'N/A')}")
        sections.append(f"**情绪评分**: {news.get('sentiment_score', 'N/A')}\n")

        key_news = news.get("key_news", [])
        if key_news:
            sections.append("### 关键新闻\n")
            for item in key_news:
                impact = item.get("impact", "")
                emoji = "🟢" if impact == "利好" else "🔴" if impact == "利空" else "⚪"
                sections.append(f"- {emoji} **{item.get('title', '')}**")
                sections.append(f"  - 影响: {impact} ({item.get('impact_level', '')})")
                sections.append(f"  - 持续性: {item.get('impact_duration', '')}")

    def _add_risk_section(self, sections: List[str], risk: Dict[str, Any]):
        """添加风险评估章节"""
        if not risk or "error" in risk:
            sections.append("风险评估暂不可用。\n")
            return

        sections.append(f"**整体风险等级**: {risk.get('overall_risk_level', 'N/A')}")
        sections.append(f"**风险评分**: {risk.get('risk_score', 'N/A')}/10\n")

        factors = risk.get("risk_factors", [])
        if factors:
            sections.append("### 风险因素\n")
            sections.append("| 类别 | 描述 | 严重性 | 概率 |")
            sections.append("|------|------|--------|------|")
            for f in factors:
                sections.append(
                    f"| {f.get('category', '')} | {f.get('description', '')} "
                    f"| {f.get('severity', '')} | {f.get('probability', '')} |"
                )

    def _add_prediction_section(self, sections: List[str], pred: Dict[str, Any]):
        """添加趋势预测章节"""
        if not pred or "error" in pred:
            sections.append("趋势预测暂不可用。\n")
            return

        sections.append(f"**投资评级**: {pred.get('rating', 'N/A')}")
        sections.append(f"**相对大盘**: {pred.get('vs_benchmark', 'N/A')}\n")

        short = pred.get("short_term", {})
        if short:
            sections.append("### 短期展望\n")
            sections.append(f"- 周期: {short.get('period', '')}")
            sections.append(f"- 趋势: {short.get('trend', '')}")
            sections.append(f"- 信心: {short.get('confidence', '')}")

        medium = pred.get("medium_term", {})
        if medium:
            sections.append("\n### 中期展望\n")
            sections.append(f"- 周期: {medium.get('period', '')}")
            sections.append(f"- 趋势: {medium.get('trend', '')}")
            sections.append(f"- 信心: {medium.get('confidence', '')}")

    def _add_advisor_section(self, sections: List[str], advisor: Dict[str, Any]):
        """添加投资建议章节"""
        if not advisor or "error" in advisor:
            sections.append("投资建议暂不可用。\n")
            return

        thesis = advisor.get("investment_thesis", {})
        if thesis:
            sections.append("### 情景分析\n")
            sections.append(f"**乐观情景**: {thesis.get('bull_case', '')}")
            sections.append(f"\n**基准情景**: {thesis.get('base_case', '')}")
            sections.append(f"\n**悲观情景**: {thesis.get('bear_case', '')}")

        key_points = advisor.get("key_points", [])
        if key_points:
            sections.append("\n### 核心观点\n")
            for i, p in enumerate(key_points, 1):
                sections.append(f"{i}. {p}")

        risk_mgmt = advisor.get("risk_management", {})
        if risk_mgmt:
            sections.append("\n### 风险管理建议\n")
            sections.append(f"- **止损**: {risk_mgmt.get('stop_loss', 'N/A')}")
            sections.append(f"- **仓位**: {risk_mgmt.get('position_sizing', 'N/A')}")
            sections.append(f"- **对冲**: {risk_mgmt.get('hedging', 'N/A')}")

        monitors = advisor.get("monitoring_indicators", [])
        if monitors:
            sections.append("\n### 持续关注指标\n")
            for m in monitors:
                sections.append(f"- {m}")
