"""
PDF报告生成器 — 融合 Apple 苹果综合研究报告 + Cogito 评估框架

参照 Apple Inc. FY2023 综合研究报告结构，包含以下章节:
  0. 封面 (关键指标卡片 + 评级徽章)
  1. 执行摘要
  2. 公司概况 + 市场行情
  3. 财务分析 (盈利/成长/偿债/现金流)
     ├─ 营收 & 净利润趋势图 (Chart-Revenue)
     └─ 利润率趋势图 (Chart-Margin)
  4. 竞争格局分析 (新增 — Apple报告§6)
  5. 新闻 & 舆情分析
  6. 现金流分析 (Chart-Cashflow)
  7. 风险评估
  8. 趋势预测
  9. 投资建议 (情景分析 + 风险管理)
 10. 股价走势图 + 成交量图 + 技术指标图
 11. 分析过程 (AI思维链)
 12. 数据来源声明

颜色与排版参照 Apple 报告的专业金融风格:
  主色: 深蓝 #1A3A5C   副色: 蓝 #2980B9
  绿:   #27AE60          橙:   #E67E22
  红:   #C0392B          紫:   #8E44AD
  青:   #1ABC9C          灰:   #7F8C8D
"""
import json
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# ── 颜色调色板 ───────────────────────────────────────────────────────────────
C_NAV   = "#1A3A5C"   # 深蓝 主色
C_BLUE  = "#2980B9"   # 蓝 副色
C_TEAL  = "#1ABC9C"   # 青绿 强调
C_GREEN = "#27AE60"   # 绿 利好
C_ORA   = "#E67E22"   # 橙 中性/警告
C_RED   = "#C0392B"   # 红 利空/风险
C_PURP  = "#8E44AD"   # 紫 风险
C_GRAY  = "#7F8C8D"   # 灰 辅助
C_LB    = "#EAF2F8"   # 浅蓝 背景
C_LG    = "#F4F6F7"   # 浅灰 交替行
C_W     = "#FFFFFF"


class PDFReportBuilder:
    """PDF格式报告生成器 — 美观图文并茂 (Apple报告风格)"""

    def __init__(self, output_dir: str = "./output", language: str = "zh"):
        self.output_dir = output_dir
        self.language = language
        os.makedirs(output_dir, exist_ok=True)

    def build(
        self,
        stock_code: str,
        data: Dict[str, Any],
        charts: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """生成 PDF 报告，返回文件路径"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import mm
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table,
                TableStyle, Image, PageBreak,
            )
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            # ── 字体 ─────────────────────────────────────────────────────────
            fn = self._register_font(pdfmetrics, TTFont)

            # ── 数据提取 ─────────────────────────────────────────────────────
            company_info = data.get("company_info", {})
            save         = data.get("save", {})
            market_data  = data.get("market_data", {})
            fin_data     = data.get("financial_data", {})
            cog_info     = data.get("cognitive_info", {})

            company_name = company_info.get("company_name", stock_code)
            advisor  = save.get("InvestmentAdvisor", {})
            fin      = save.get("FinancialAnalyst", {})
            comp     = save.get("CompetitiveAnalyst", {})
            news     = save.get("NewsAnalyst", {})
            risk     = save.get("RiskAssessor", {})
            pred     = save.get("Predictor", {})

            rec           = (advisor or {}).get("recommendation", {})
            rating_action = rec.get("action", "")
            rating_color  = self._rating_color(rating_action)
            summary       = market_data.get("summary", {})
            key_metrics   = fin_data.get("key_metrics", {})
            charts        = charts or {}

            # ── 输出路径 ─────────────────────────────────────────────────────
            filepath = os.path.join(
                self.output_dir,
                f"{stock_code}_research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            )

            # ── 文档 ─────────────────────────────────────────────────────────
            PAGE_W, PAGE_H = A4
            MARGIN = 18 * mm
            W = PAGE_W - 2 * MARGIN

            doc = SimpleDocTemplate(
                filepath, pagesize=A4,
                rightMargin=MARGIN, leftMargin=MARGIN,
                topMargin=22 * mm, bottomMargin=18 * mm,
                title=f"{company_name} 深度研究报告",
                author="Stock Deep Research AI",
            )

            # ── 样式工厂 ─────────────────────────────────────────────────────
            def S(name, **kw):
                return ParagraphStyle(name, fontName=fn, **kw)

            st_body    = S("Body",   fontSize=11, leading=18,
                           textColor=colors.HexColor("#2C3E50"), spaceAfter=5)
            st_small   = S("Small",  fontSize=10, leading=15,
                           textColor=colors.HexColor("#4A4A4A"), spaceAfter=3)
            st_sub     = S("Sub",    fontSize=12, leading=16,
                           textColor=colors.HexColor(C_NAV), spaceBefore=8, spaceAfter=4)
            st_wht     = S("SecWht", fontSize=13, leading=17, textColor=colors.white)
            st_wht_sm  = S("SecWhtSm", fontSize=11, leading=15, textColor=colors.white)
            st_cap     = S("Cap",    fontSize=10, leading=14,
                           textColor=colors.HexColor("#4A4A4A"),
                           alignment=TA_CENTER, spaceAfter=4)
            st_hdr     = S("TblHdr", fontSize=10, leading=13, textColor=colors.white,
                           alignment=TA_CENTER)
            st_cell    = S("Cell",   fontSize=10, leading=14,
                           textColor=colors.HexColor("#2C3E50"))
            st_cellc   = S("CellC",  fontSize=10, leading=14,
                           textColor=colors.HexColor("#2C3E50"), alignment=TA_CENTER)
            st_green   = S("Grn",    fontSize=11, leading=15,
                           textColor=colors.HexColor(C_GREEN), spaceAfter=3)
            st_red     = S("Red",    fontSize=11, leading=15,
                           textColor=colors.HexColor(C_RED), spaceAfter=3)

            # Cover-specific styles
            st_cname   = S("CName",  fontSize=28, leading=34, textColor=colors.white,
                           alignment=TA_CENTER, spaceAfter=4)
            st_ccode   = S("CCode",  fontSize=14, leading=18,
                           textColor=colors.HexColor(C_TEAL),
                           alignment=TA_CENTER, spaceAfter=0)
            st_cdate   = S("CDate",  fontSize=10,
                           textColor=colors.HexColor("#555555"), alignment=TA_CENTER)
            st_cdisc   = S("CDisc",  fontSize=9,
                           textColor=colors.HexColor("#555555"), alignment=TA_CENTER)

            # ── 便捷构建函数 ──────────────────────────────────────────────────

            def sec(title, bg=C_NAV, fg=colors.white, sz=13):
                """章节色条标题"""
                p_st = ParagraphStyle("_sec", fontName=fn, fontSize=sz, leading=sz + 4,
                                      textColor=fg)
                t = Table([[Paragraph(title, p_st)]], colWidths=[W])
                t.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(bg)),
                    ("TOPPADDING",    (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ]))
                return [Spacer(1, 8), t, Spacer(1, 6)]

            def card(label, value, bg, w=None):
                """关键指标卡片"""
                t = Table([[label], [value]], colWidths=[w or W / 3])
                t.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(bg)),
                    ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.HexColor("#DDDDDD")),
                    ("TEXTCOLOR",     (0, 1), (-1, 1),  colors.white),
                    ("FONTNAME",      (0, 0), (-1, -1), fn),
                    ("FONTSIZE",      (0, 0), (-1, 0),  9),
                    ("FONTSIZE",      (0, 1), (-1, 1),  15),
                    ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING",    (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]))
                return t

            def chart_img(path, caption, max_h=None):
                """嵌入图表"""
                if not path or not os.path.exists(path):
                    return []
                h = max_h or W * 0.52
                try:
                    img = Image(path, width=W, height=h)
                    return [img, Paragraph(caption, st_cap), Spacer(1, 5)]
                except Exception:
                    return []

            def styled_table(rows, col_w, hdr_bg=C_NAV,
                             alt_bg=C_LG, show_grid=True):
                """带表头色+交替行的标准表格"""
                style_cmds = [
                    ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor(hdr_bg)),
                    ("FONTNAME",      (0, 0), (-1, -1), fn),
                    ("FONTSIZE",      (0, 0), (-1, -1), 10),
                    ("TOPPADDING",    (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                    ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ]
                if show_grid:
                    style_cmds.append(
                        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")))
                for i in range(1, len(rows), 2):
                    style_cmds.append(
                        ("BACKGROUND", (0, i), (-1, i), colors.HexColor(alt_bg)))
                t = Table(rows, colWidths=col_w)
                t.setStyle(TableStyle(style_cmds))
                return t

            def badge(text, bg, w_frac=0.45):
                """彩色徽章"""
                t = Table([[text]], colWidths=[W * w_frac])
                t.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(bg)),
                    ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
                    ("FONTNAME",      (0, 0), (-1, -1), fn),
                    ("FONTSIZE",      (0, 0), (-1, -1), 11),
                    ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING",    (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                wrap = Table([[t]], colWidths=[W])
                wrap.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
                return wrap

            def _s(v) -> str:
                """安全转字符串，防止 dict/list 传入 Paragraph 报错"""
                if v is None:
                    return ""
                if isinstance(v, str):
                    return v
                if isinstance(v, (list, dict)):
                    return json.dumps(v, ensure_ascii=False)
                return str(v)

            # ══════════════════════════════════════════════════════════════════
            # 封面
            # ══════════════════════════════════════════════════════════════════
            els: list = []

            top_bar = Table([[""]], colWidths=[W], rowHeights=[5])
            top_bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(C_TEAL))]))
            els.append(top_bar)
            els.append(Spacer(1, 28))

            els.append(Paragraph(f"<b>{company_name}</b>", st_cname))
            els.append(Paragraph(f"股票代码：{stock_code}", st_ccode))
            els.append(Spacer(1, 18))

            tbl_title = Table([["深 度 研 究 报 告"]], colWidths=[W])
            tbl_title.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(C_NAV)),
                ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
                ("FONTNAME",      (0, 0), (-1, -1), fn),
                ("FONTSIZE",      (0, 0), (-1, -1), 18),
                ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING",    (0, 0), (-1, -1), 14),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ]))
            els.append(tbl_title)
            els.append(Spacer(1, 26))

            # 封面三格指标卡片
            latest    = summary.get("latest_close", "N/A")
            p_ret     = summary.get("period_return", None)
            vol       = summary.get("volatility", None)
            ret_str   = f"{p_ret:.2f}%" if isinstance(p_ret, (int, float)) else "N/A"
            vol_str   = f"{vol:.2f}%"   if isinstance(vol, (int, float)) else "N/A"
            ret_color = C_GREEN if isinstance(p_ret, (int, float)) and p_ret > 0 else C_RED

            cov_cards = Table([[
                card("最新收盘价", f"CNY {latest}", C_NAV),
                card("区间涨幅",   ret_str,      ret_color),
                card("年化波动率", vol_str,      C_ORA),
            ]], colWidths=[W / 3] * 3)
            cov_cards.setStyle(TableStyle([
                ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING",  (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ]))
            els.append(cov_cards)
            els.append(Spacer(1, 22))

            if rating_action:
                els.append(badge(f"投资评级：{rating_action}", rating_color))
                els.append(Spacer(1, 22))

            # 数据源标注（Apple报告有引用说明）
            data_source = fin_data.get("data_source", "akshare/tushare")
            els.append(Paragraph(
                f"报告生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}　"
                f"数据来源：{data_source}", st_cdate))
            els.append(Spacer(1, 6))
            els.append(Paragraph(
                "【免责声明】本报告由人工智能系统自动生成，仅供研究参考，"
                "不构成任何投资建议。投资者应自行判断，风险自担。",
                st_cdisc))
            els.append(Spacer(1, 18))

            bot_bar = Table([[""]], colWidths=[W], rowHeights=[5])
            bot_bar.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(C_TEAL))]))
            els.append(bot_bar)
            els.append(PageBreak())

            # ══════════════════════════════════════════════════════════════════
            # § 1  执行摘要
            # ══════════════════════════════════════════════════════════════════
            els += sec("一、执行摘要", C_NAV)

            conf = rec.get("confidence", "N/A")
            hrz  = rec.get("time_horizon", "N/A")
            tgt  = rec.get("target_upside", "")
            summary_cards = Table([[
                card("评级",     rating_action or "N/A", rating_color),
                card("信心水平", conf,                    C_BLUE),
                card("投资周期", hrz,                     C_NAV),
            ]], colWidths=[W / 3] * 3)
            summary_cards.setStyle(TableStyle([
                ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING",  (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ]))
            els.append(summary_cards)
            if tgt:
                els.append(Spacer(1, 4))
                els.append(Paragraph(f"<b>目标收益区间：</b>{tgt}", st_small))
            els.append(Spacer(1, 8))

            exec_sum = (advisor or {}).get("executive_summary", "")
            if exec_sum:
                els.append(Paragraph(_s(exec_sum), st_body))

            # 核心观点列表
            key_pts = (advisor or {}).get("key_points", [])
            if key_pts:
                els.append(Spacer(1, 6))
                els.append(Paragraph("<b>核心观点</b>", st_sub))
                for i, pt in enumerate(key_pts, 1):
                    els.append(Paragraph(f"{i}. {_s(pt)}", st_body))

            # ══════════════════════════════════════════════════════════════════
            # § 2  公司概况
            # ══════════════════════════════════════════════════════════════════
            els += sec("二、公司概况", C_BLUE)

            label_map = {
                "company_name": "公司名称", "stock_code": "股票代码",
                "industry": "所属行业",     "listing_date": "上市日期",
                "area": "注册地区",         "market": "上市市场",
            }
            co_rows = []
            for k, v in company_info.items():
                if k == "_raw" or not v:
                    continue
                lbl = label_map.get(k, k)
                co_rows.append([Paragraph(f"<b>{lbl}</b>", st_cell),
                                 Paragraph(str(v), st_cell)])
            if co_rows:
                els.append(styled_table(co_rows, [W * 0.28, W * 0.72],
                                        hdr_bg=C_LB, alt_bg=C_LG, show_grid=True))
                els.append(Spacer(1, 6))

            # 市场行情摘要
            if summary:
                els.append(Paragraph("<b>市场行情摘要</b>", st_sub))
                mkt_rows = []
                mkt_map = {
                    "latest_close":  "最新收盘价",
                    "period_return": "区间涨幅(%)",
                    "volatility":    "年化波动率(%)",
                }
                for k, lbl in mkt_map.items():
                    v = summary.get(k)
                    if v is not None:
                        val_str = f"{v:.2f}" if isinstance(v, float) else str(v)
                        mkt_rows.append([Paragraph(f"<b>{lbl}</b>", st_cell),
                                         Paragraph(val_str, st_cell)])
                if mkt_rows:
                    els.append(styled_table(mkt_rows, [W * 0.35, W * 0.65],
                                            hdr_bg=C_LB, show_grid=False))
                els.append(Spacer(1, 6))

            # ══════════════════════════════════════════════════════════════════
            # § 3  财务分析
            # ══════════════════════════════════════════════════════════════════
            els += sec("三、财务分析", C_NAV)

            if not fin or "error" in fin:
                els.append(Paragraph("财务数据暂不可用。", st_body))
            else:
                # 三大能力摘要表
                ability_rows = []
                for lbl, key in [
                    ("盈利能力", "profitability"),
                    ("成长能力", "growth"),
                    ("偿债能力", "solvency"),
                    ("运营效率", "efficiency"),
                    ("现金流质量", "cash_flow"),
                ]:
                    blk = fin.get(key, {})
                    if not blk:
                        continue
                    trend = blk.get("trend", blk.get("risk_level", blk.get("quality", "")))
                    ability_rows.append([
                        Paragraph(f"<b>{lbl}</b>", st_sub),
                        Paragraph(_s(blk.get("summary", "")), st_body),
                        Paragraph(_s(trend), st_small),
                    ])

                if ability_rows:
                    ab_style = [
                        ("FONTNAME",      (0, 0), (-1, -1), fn),
                        ("TOPPADDING",    (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
                    ]
                    for i in range(0, len(ability_rows), 2):
                        ab_style.append(("BACKGROUND", (0, i), (-1, i),
                                         colors.HexColor(C_LB)))
                    ab_t = Table(ability_rows, colWidths=[W * 0.14, W * 0.66, W * 0.20])
                    ab_t.setStyle(TableStyle(ab_style))
                    els.append(ab_t)
                    els.append(Spacer(1, 8))

                # 综合评分徽章
                score = fin.get("overall_score", "N/A")
                if isinstance(score, (int, float)):
                    sc_c = C_GREEN if score >= 7 else (C_ORA if score >= 5 else C_RED)
                else:
                    sc_c = C_GRAY
                sc_t = Table([[f"财务综合评分：{score} / 10"]], colWidths=[W / 3])
                sc_t.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(sc_c)),
                    ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
                    ("FONTNAME",      (0, 0), (-1, -1), fn),
                    ("FONTSIZE",      (0, 0), (-1, -1), 11),
                    ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING",    (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                els.append(sc_t)
                els.append(Spacer(1, 8))

                # 亮点 & 风险双列
                hl = fin.get("key_highlights", [])
                rk = fin.get("key_risks", [])
                if hl or rk:
                    max_n = max(len(hl), len(rk))
                    hl_rows = [[Paragraph("<b>▲ 关键亮点</b>", st_sub)]]
                    rk_rows = [[Paragraph("<b>▼ 关键风险</b>", st_sub)]]
                    for i in range(max_n):
                        hl_rows.append([Paragraph(f"• {_s(hl[i])}" if i < len(hl) else "", st_green)])
                        rk_rows.append([Paragraph(f"• {_s(rk[i])}" if i < len(rk) else "", st_red)])

                    hl_t = Table(hl_rows, colWidths=[W * 0.47])
                    hl_t.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D5F5E3")),
                        ("FONTNAME",   (0, 0), (-1, -1), fn),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
                        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#AADDAA")),
                    ]))
                    rk_t = Table(rk_rows, colWidths=[W * 0.47])
                    rk_t.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FADBD8")),
                        ("FONTNAME",   (0, 0), (-1, -1), fn),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
                        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#DDAAAA")),
                    ]))
                    two = Table([[hl_t, rk_t]], colWidths=[W * 0.50, W * 0.50])
                    two.setStyle(TableStyle([
                        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING",  (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ]))
                    els.append(two)
                    els.append(Spacer(1, 8))

            # 财务图表：营收 + 利润率
            if charts.get("revenue") and os.path.exists(charts["revenue"]):
                els += sec("营收 & 净利润趋势", C_BLUE, sz=12)
                els += chart_img(charts["revenue"],
                                 "图：营业收入（蓝柱）& 净利润（绿柱）& 净利率（橙线）趋势",
                                 W * 0.55)

            if charts.get("margin") and os.path.exists(charts["margin"]):
                els += sec("利润率结构趋势", C_BLUE, sz=12)
                els += chart_img(charts["margin"],
                                 "图：毛利率（蓝线）/ 营业利润率（绿线）/ 净利率（橙线）趋势",
                                 W * 0.52)

            # ══════════════════════════════════════════════════════════════════
            # § 4  竞争格局分析 (新增 — Apple报告§6)
            # ══════════════════════════════════════════════════════════════════
            els += sec("四、竞争格局分析", C_NAV)

            if not comp or "error" in comp:
                els.append(Paragraph("竞争格局分析暂不可用。", st_body))
            else:
                # 行业概览
                ind_ov = comp.get("industry_overview", {})
                if ind_ov:
                    els.append(Paragraph("<b>行业概览</b>", st_sub))
                    rows_ind = []
                    for lbl, key in [
                        ("细分行业", "industry_name"),
                        ("市场规模", "market_size"),
                        ("增长阶段", "growth_stage"),
                        ("政策环境", "policy_environment"),
                    ]:
                        v = ind_ov.get(key)
                        if v:
                            rows_ind.append([Paragraph(f"<b>{lbl}</b>", st_cell),
                                             Paragraph(str(v), st_cell)])
                    if rows_ind:
                        els.append(styled_table(rows_ind, [W * 0.22, W * 0.78],
                                                hdr_bg=C_LB, show_grid=False))
                    trends = ind_ov.get("key_trends", [])
                    if trends:
                        els.append(Spacer(1, 4))
                        els.append(Paragraph("<b>关键趋势：</b>", st_body))
                        for tr in trends:
                            els.append(Paragraph(f"• {tr}", st_body))
                    els.append(Spacer(1, 6))

                # 竞争地位 + 护城河 双列
                mkt_pos = comp.get("market_position", {})
                moat    = comp.get("competitive_moat", {})
                if mkt_pos or moat:
                    def info_card(title, items, bg):
                        inner_rows = [[Paragraph(f"<b>{title}</b>", st_wht_sm)]]
                        for lbl, val in items:
                            if val:
                                inner_rows.append([Paragraph(f"{_s(lbl)}：{_s(val)}", st_cell)])
                        t = Table(inner_rows, colWidths=[W * 0.46])
                        t.setStyle(TableStyle([
                            ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor(bg)),
                            ("BACKGROUND",    (0, 1), (-1, -1), colors.HexColor(C_LG)),
                            ("FONTNAME",      (0, 0), (-1, -1), fn),
                            ("TOPPADDING",    (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
                        ]))
                        return t

                    pos_items = [
                        ("行业地位",  mkt_pos.get("market_rank", "")),
                        ("市场份额",  mkt_pos.get("market_share_est", "")),
                        ("品牌价值",  mkt_pos.get("brand_value", "")),
                        ("核心优势",  mkt_pos.get("competitive_advantage", "")),
                    ]
                    moat_items = [
                        ("护城河类型",  "、".join(_s(x) for x in moat.get("moat_types", []))),
                        ("护城河强度",  _s(moat.get("moat_strength", ""))),
                        ("持久性",      _s(moat.get("moat_durability", ""))),
                    ]
                    for adv in moat.get("key_advantages", [])[:3]:
                        moat_items.append(("", f"• {_s(adv)}"))

                    left_t  = info_card("市场竞争地位", pos_items, C_BLUE)
                    right_t = info_card("护城河分析",   moat_items, C_NAV)

                    two_col = Table([[left_t, right_t]], colWidths=[W * 0.50, W * 0.50])
                    two_col.setStyle(TableStyle([
                        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING",  (0, 0), (-1, -1), 2),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ]))
                    els.append(two_col)
                    els.append(Spacer(1, 8))

                # 竞争对手对比表
                peers = comp.get("peer_comparison", [])
                if peers:
                    els.append(Paragraph("<b>主要竞争对手对比</b>", st_sub))
                    peer_hdr = [
                        Paragraph("竞争对手", st_hdr),
                        Paragraph("我方相对优势", st_hdr),
                        Paragraph("我方相对劣势", st_hdr),
                    ]
                    peer_rows = [peer_hdr]
                    for p in peers[:5]:
                        name = p.get("company", p.get("ticker", ""))
                        peer_rows.append([
                            Paragraph(_s(name), st_cellc),
                            Paragraph(_s(p.get("relative_strength", "")), st_cell),
                            Paragraph(_s(p.get("relative_weakness", "")), st_cell),
                        ])
                    els.append(styled_table(peer_rows, [W * 0.20, W * 0.40, W * 0.40],
                                            hdr_bg=C_BLUE))
                    els.append(Spacer(1, 8))

                # SWOT 矩阵 (2×2)
                swot = comp.get("swot", {})
                if swot:
                    els.append(Paragraph("<b>SWOT 矩阵</b>", st_sub))

                    def swot_cell(title, items, bg, text_color):
                        inner = [[Paragraph(f"<b>{title}</b>", st_wht)]]
                        for it in items[:4]:
                            inner.append([Paragraph(f"• {_s(it)}", st_cell)])
                        t = Table(inner, colWidths=[W * 0.46])
                        t.setStyle(TableStyle([
                            ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor(bg)),
                            ("BACKGROUND",    (0, 1), (-1, -1), colors.HexColor(C_LG)),
                            ("FONTNAME",      (0, 0), (-1, -1), fn),
                            ("TOPPADDING",    (0, 0), (-1, -1), 5),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
                        ]))
                        return t

                    sw_t = Table([
                        [swot_cell("S 优势 Strengths",      swot.get("strengths", []),    C_GREEN, C_GREEN),
                         swot_cell("W 劣势 Weaknesses",     swot.get("weaknesses", []),   C_ORA,  C_ORA)],
                        [swot_cell("O 机会 Opportunities",  swot.get("opportunities", []),C_BLUE, C_BLUE),
                         swot_cell("T 威胁 Threats",        swot.get("threats", []),      C_RED,  C_RED)],
                    ], colWidths=[W * 0.50, W * 0.50])
                    sw_t.setStyle(TableStyle([
                        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING",  (0, 0), (-1, -1), 2),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                        ("TOPPADDING",   (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
                    ]))
                    els.append(sw_t)
                    els.append(Spacer(1, 6))

                # 竞争评分 + 展望
                c_score = comp.get("competitive_score", "N/A")
                c_ratio = comp.get("competitive_score_rationale", "")
                c_out   = comp.get("outlook", "")
                if c_score != "N/A":
                    sc_c2 = C_GREEN if isinstance(c_score, (int, float)) and c_score >= 7 \
                            else (C_ORA if isinstance(c_score, (int, float)) and c_score >= 5 else C_RED)
                    els.append(badge(f"竞争力综合评分：{c_score} / 10  ({c_ratio})", sc_c2, 0.7))
                    els.append(Spacer(1, 5))
                if c_out:
                    els.append(Paragraph(f"<b>竞争格局展望：</b>{c_out}", st_body))
                els.append(Spacer(1, 6))

            # ══════════════════════════════════════════════════════════════════
            # § 5  新闻 & 舆情分析
            # ══════════════════════════════════════════════════════════════════
            els += sec("五、新闻与舆情分析", C_NAV)

            if not news or "error" in news:
                els.append(Paragraph("暂无相关新闻分析。", st_body))
            else:
                sentiment = news.get("overall_sentiment", "N/A")
                nscore    = news.get("sentiment_score", None)
                s_color = (C_GREEN if any(k in str(sentiment) for k in ["积极", "正面", "positive"])
                           else (C_RED if any(k in str(sentiment) for k in ["消极", "负面", "negative"])
                                 else C_ORA))
                ns_str = f"{nscore:.2f}" if isinstance(nscore, (int, float)) else str(nscore)

                sent_t = Table([[f"整体情绪：{sentiment}", f"情绪评分：{ns_str}"]],
                               colWidths=[W * 0.55, W * 0.45])
                sent_t.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(s_color)),
                    ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
                    ("FONTNAME",      (0, 0), (-1, -1), fn),
                    ("FONTSIZE",      (0, 0), (-1, -1), 10),
                    ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING",    (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                els.append(sent_t)
                els.append(Spacer(1, 8))

                key_news = news.get("key_news", [])
                if key_news:
                    ns_hdr = [Paragraph("标题", st_hdr), Paragraph("影响", st_hdr),
                              Paragraph("程度", st_hdr), Paragraph("持续性", st_hdr)]
                    ns_rows = [ns_hdr]
                    for item in key_news[:8]:
                        impact = item.get("impact", "")
                        ic = (C_GREEN if impact == "利好"
                              else (C_RED if impact == "利空" else C_ORA))
                        imp_st = ParagraphStyle("_imp", fontName=fn, fontSize=10,
                                               textColor=colors.white,
                                               backColor=colors.HexColor(ic),
                                               alignment=TA_CENTER)
                        ns_rows.append([
                            Paragraph(_s(item.get("title", "")), st_cell),
                            Paragraph(_s(impact), imp_st),
                            Paragraph(_s(item.get("impact_level", "")), st_cellc),
                            Paragraph(_s(item.get("impact_duration", "")), st_cellc),
                        ])
                    ns_t = styled_table(ns_rows, [W * 0.52, W * 0.14, W * 0.14, W * 0.20],
                                        hdr_bg=C_NAV)
                    els.append(ns_t)
                    els.append(Spacer(1, 6))

                # 主题与信号
                themes = news.get("key_themes", [])
                opps   = news.get("opportunity_signals", [])
                risks_n = news.get("risk_signals", [])
                if themes:
                    els.append(Paragraph(f"<b>关键主题：</b>{'  ·  '.join(_s(x) for x in themes)}", st_small))
                if opps:
                    els.append(Paragraph(
                        f"<b>机会信号：</b>{'  ·  '.join(_s(x) for x in opps[:3])}", st_green))
                if risks_n:
                    els.append(Paragraph(
                        f"<b>风险信号：</b>{'  ·  '.join(_s(x) for x in risks_n[:3])}", st_red))
                els.append(Spacer(1, 6))

            # ══════════════════════════════════════════════════════════════════
            # § 6  现金流分析 (Apple报告§5.1)
            # ══════════════════════════════════════════════════════════════════
            els += sec("六、现金流分析", C_BLUE, sz=12)
            if charts.get("cashflow") and os.path.exists(charts["cashflow"]):
                els += chart_img(charts["cashflow"],
                                 "图：营业收入 / 净利润 / 经营现金流 对比（亿元）",
                                 W * 0.52)
            # 现金流数值表（有 key_metrics 时显示）
            cf_periods = key_metrics.get("periods", [])
            cf_data    = key_metrics.get("operating_cf", [])
            rev_data   = key_metrics.get("revenue", [])
            np_data    = key_metrics.get("net_profit", [])
            if cf_periods and (cf_data or rev_data):
                cf_hdr  = [Paragraph(h, st_hdr) for h in ["报告期", "营收(亿)", "净利润(亿)", "经营现金流(亿)"]]
                cf_rows = [cf_hdr]
                for i, period in enumerate(cf_periods):
                    def _fmt(lst, i):
                        v = lst[i] if i < len(lst) else None
                        return f"{v/1e8:.2f}" if v is not None else "—"
                    cf_rows.append([
                        Paragraph(period, st_cellc),
                        Paragraph(_fmt(rev_data, i), st_cellc),
                        Paragraph(_fmt(np_data,  i), st_cellc),
                        Paragraph(_fmt(cf_data,  i), st_cellc),
                    ])
                cf_t = styled_table(cf_rows, [W*0.22, W*0.26, W*0.26, W*0.26], hdr_bg=C_BLUE)
                els.append(cf_t)
                els.append(Spacer(1, 6))
            else:
                # 直接从 financial_data cash_flow 表格提取展示
                raw_cf = fin_data.get("cash_flow", [])
                if isinstance(raw_cf, list) and raw_cf:
                    cf_hdr2 = [Paragraph(h, st_hdr) for h in ["报告期", "经营活动现金流净额(亿)"]]
                    cf_rows2 = [cf_hdr2]
                    for row in raw_cf[:6]:
                        if not isinstance(row, dict):
                            continue
                        d = row.get("报告日", row.get("报告日期", ""))
                        cf = None
                        for k in ("经营活动产生的现金流量净额", "经营活动现金流量净额"):
                            if k in row and row[k] is not None:
                                try: cf = float(row[k])
                                except: pass
                                break
                        cf_rows2.append([
                            Paragraph(_s(str(d)[:7]), st_cellc),
                            Paragraph(f"{cf/1e8:.2f}" if cf is not None else "—", st_cellc),
                        ])
                    if len(cf_rows2) > 1:
                        els.append(styled_table(cf_rows2, [W*0.40, W*0.60], hdr_bg=C_BLUE))
                        els.append(Spacer(1, 6))
                else:
                    els.append(Paragraph("现金流数据暂不可用。", st_body))

            # ══════════════════════════════════════════════════════════════════
            # § 7  风险评估
            # ══════════════════════════════════════════════════════════════════
            els += sec("七、风险评估", C_PURP)

            if not risk or "error" in risk:
                els.append(Paragraph("风险评估暂不可用。", st_body))
            else:
                level  = risk.get("overall_risk_level", "N/A")
                rscore = risk.get("risk_score", None)
                r_color = (C_RED if "高" in str(level)
                           else (C_ORA if "中" in str(level) else C_GREEN))
                rs_str = f"{rscore}/10" if rscore is not None else "N/A"

                ri_t = Table([[f"整体风险等级：{level}", f"风险评分：{rs_str}"]],
                             colWidths=[W * 0.60, W * 0.40])
                ri_t.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(r_color)),
                    ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
                    ("FONTNAME",      (0, 0), (-1, -1), fn),
                    ("FONTSIZE",      (0, 0), (-1, -1), 11),
                    ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING",    (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]))
                els.append(ri_t)
                els.append(Spacer(1, 8))

                factors = risk.get("risk_factors", [])
                if factors:
                    rf_hdr = [Paragraph("类别", st_hdr), Paragraph("描述", st_hdr),
                              Paragraph("严重性", st_hdr), Paragraph("概率", st_hdr)]
                    rf_rows = [rf_hdr]
                    for f in factors:
                        sev = f.get("severity", "")
                        sv_c = C_RED if "高" in str(sev) else (C_ORA if "中" in str(sev) else C_GREEN)
                        sev_st = ParagraphStyle("_sev", fontName=fn, fontSize=10,
                                                textColor=colors.HexColor(sv_c),
                                                alignment=TA_CENTER)
                        rf_rows.append([
                            Paragraph(_s(f.get("category", "")),    st_cellc),
                            Paragraph(_s(f.get("description", "")), st_cell),
                            Paragraph(f"<b>{_s(sev)}</b>",          sev_st),
                            Paragraph(_s(f.get("probability", "")), st_cellc),
                        ])
                    rf_t = styled_table(rf_rows,
                                        [W * 0.14, W * 0.50, W * 0.18, W * 0.18],
                                        hdr_bg=C_PURP, alt_bg="#F9EBEA")
                    els.append(rf_t)

                # 预警信号 + 安全因素
                warns = risk.get("warning_signals", [])
                safes = risk.get("safe_factors", [])
                if warns or safes:
                    els.append(Spacer(1, 6))
                    if warns:
                        els.append(Paragraph(
                            f"<b>预警信号：</b>{'  ·  '.join(_s(x) for x in warns[:3])}", st_red))
                    if safes:
                        els.append(Paragraph(
                            f"<b>安全因素：</b>{'  ·  '.join(_s(x) for x in safes[:3])}", st_green))
                els.append(Spacer(1, 8))

            # ══════════════════════════════════════════════════════════════════
            # § 8  趋势预测
            # ══════════════════════════════════════════════════════════════════
            els += sec("八、趋势预测", C_BLUE)

            if not pred or "error" in pred:
                els.append(Paragraph("趋势预测暂不可用。", st_body))
            else:
                p_rating  = pred.get("rating", "N/A")
                vs_bench  = pred.get("vs_benchmark", "N/A")
                ph_t = Table([[f"技术评级：{p_rating}", f"相对大盘：{vs_bench}"]],
                             colWidths=[W * 0.5, W * 0.5])
                ph_t.setStyle(TableStyle([
                    ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(C_BLUE)),
                    ("TEXTCOLOR",     (0, 0), (-1, -1), colors.white),
                    ("FONTNAME",      (0, 0), (-1, -1), fn),
                    ("FONTSIZE",      (0, 0), (-1, -1), 10),
                    ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING",    (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                els.append(ph_t)
                els.append(Spacer(1, 8))

                outlook_cards = []
                for lbl, ok in [("短期展望（1-2周）", "short_term"),
                                 ("中期展望（1-3月）", "medium_term")]:
                    blk = pred.get(ok, {})
                    if not blk:
                        continue
                    trend = blk.get("trend", "N/A")
                    tr_c  = (C_GREEN if "上涨" in str(trend)
                             else (C_RED if "下跌" in str(trend) else C_ORA))
                    c_rows = [
                        [Paragraph(f"<b>{lbl}</b>", st_wht)],
                        [Paragraph(f"周期：{_s(blk.get('period', ''))}", st_cell)],
                        [Paragraph(f"趋势：{_s(trend)}", st_cell)],
                        [Paragraph(f"信心：{_s(blk.get('confidence', ''))}", st_cell)],
                    ]
                    for fac in blk.get("key_factors", [])[:2]:
                        c_rows.append([Paragraph(f"• {_s(fac)}", st_small)])
                    ct = Table(c_rows, colWidths=[W * 0.46])
                    ct.setStyle(TableStyle([
                        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor(tr_c)),
                        ("BACKGROUND",    (0, 1), (-1, -1), colors.HexColor(C_LG)),
                        ("FONTNAME",      (0, 0), (-1, -1), fn),
                        ("TOPPADDING",    (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
                    ]))
                    outlook_cards.append(ct)

                if len(outlook_cards) == 2:
                    oc = Table([outlook_cards], colWidths=[W * 0.50, W * 0.50])
                    oc.setStyle(TableStyle([
                        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING",  (0, 0), (-1, -1), 2),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ]))
                    els.append(oc)
                elif outlook_cards:
                    els.append(outlook_cards[0])

                catalysts = pred.get("key_catalysts", [])
                if catalysts:
                    els.append(Spacer(1, 6))
                    els.append(Paragraph(
                        f"<b>关键催化剂：</b>{'  ·  '.join(_s(x) for x in catalysts[:3])}", st_green))
                els.append(Spacer(1, 8))

            # ══════════════════════════════════════════════════════════════════
            # § 9  投资建议
            # ══════════════════════════════════════════════════════════════════
            els += sec("九、投资建议", C_GREEN)

            if not advisor or "error" in advisor:
                els.append(Paragraph("投资建议暂不可用。", st_body))
            else:
                # 情景字段中文映射
                _FIELD_ZH = {
                    "trigger_factors": "触发因素", "key_catalysts": "关键催化",
                    "price_target": "价格目标", "expected_return": "预期收益",
                    "core_assumptions": "核心假设", "assumptions": "核心假设",
                    "main_risks": "主要风险", "downside_potential": "下行空间",
                    "upside_potential": "上行空间", "description": "描述",
                }

                def _scenario_rows(raw):
                    """将字符串或嵌套dict转成 [[Paragraph], ...] 行列表"""
                    rows = []
                    if isinstance(raw, str):
                        rows.append([Paragraph(raw, st_small)])
                    elif isinstance(raw, dict):
                        for k, v in raw.items():
                            label = _FIELD_ZH.get(k, k)
                            if isinstance(v, list):
                                rows.append([Paragraph(f"<b>{label}:</b>", st_small)])
                                for item in v[:4]:
                                    rows.append([Paragraph(f"• {_s(item)}", st_small)])
                            else:
                                rows.append([Paragraph(f"{label}: {_s(v)}", st_small)])
                    if not rows:
                        rows.append([Paragraph("—", st_small)])
                    return rows

                thesis = advisor.get("investment_thesis", {})
                if thesis:
                    sc_cards = []
                    for lbl, key, bg in [
                        ("乐观情景", "bull_case", C_GREEN),
                        ("基准情景", "base_case", C_BLUE),
                        ("悲观情景", "bear_case", C_RED),
                    ]:
                        raw  = thesis.get(key, "")
                        body = _scenario_rows(raw)
                        sct_rows = [[Paragraph(f"<b>{lbl}</b>", st_wht)]] + body
                        sct = Table(sct_rows, colWidths=[W * 0.30])
                        sct_style = [
                            ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor(bg)),
                            ("BACKGROUND",    (0, 1), (-1, -1), colors.HexColor(C_LG)),
                            ("FONTNAME",      (0, 0), (-1, -1), fn),
                            ("TOPPADDING",    (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                            ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
                        ]
                        sct.setStyle(TableStyle(sct_style))
                        sc_cards.append(sct)

                    sc_w = Table([sc_cards], colWidths=[W * 0.32] * 3)
                    sc_w.setStyle(TableStyle([
                        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING",  (0, 0), (-1, -1), 2),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ]))
                    els.append(sc_w)
                    els.append(Spacer(1, 8))

                # 估值背景（新增 — Apple报告有估值对比）
                val_ctx = advisor.get("valuation_context", {})
                if val_ctx:
                    els.append(Paragraph("<b>估值分析</b>", st_sub))
                    val_rows = []
                    for lbl, k in [
                        ("估值方法", "valuation_method"),
                        ("当前估值", "current_valuation"),
                        ("历史对比", "historical_comparison"),
                        ("同行对比", "peer_comparison"),
                    ]:
                        v = val_ctx.get(k)
                        if v:
                            val_rows.append([Paragraph(f"<b>{lbl}</b>", st_cell),
                                             Paragraph(str(v), st_cell)])
                    if val_rows:
                        els.append(styled_table(val_rows, [W * 0.22, W * 0.78],
                                                hdr_bg="#EAFAF1", show_grid=False))
                    els.append(Spacer(1, 6))

                # 风险管理表
                rm = advisor.get("risk_management", {})
                if rm:
                    rm_rows = []
                    for lbl, k in [("止损", "stop_loss"),
                                   ("仓位管理", "position_sizing"),
                                   ("对冲建议", "hedging")]:
                        v = rm.get(k)
                        if v:
                            rm_rows.append([Paragraph(lbl, st_hdr),
                                            Paragraph(_s(v), st_cell)])
                    if rm_rows:
                        rm_t = Table(rm_rows, colWidths=[W * 0.18, W * 0.82])
                        rm_t.setStyle(TableStyle([
                            ("BACKGROUND",    (0, 0), (0, -1), colors.HexColor(C_BLUE)),
                            ("BACKGROUND",    (1, 0), (1, -1), colors.HexColor(C_LG)),
                            ("FONTNAME",      (0, 0), (-1, -1), fn),
                            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#AAAAAA")),
                            ("TOPPADDING",    (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                        ]))
                        els.append(rm_t)
                        els.append(Spacer(1, 8))

                # 持续关注指标
                monitors = advisor.get("monitoring_indicators", [])
                if monitors:
                    mon_rows  = [[Paragraph("持续关注指标", st_hdr)]]
                    mon_style = [
                        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor(C_BLUE)),
                        ("FONTNAME",      (0, 0), (-1, -1), fn),
                        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
                        ("TOPPADDING",    (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
                    ]
                    for i, m in enumerate(monitors, 1):
                        mon_rows.append([Paragraph(f"• {_s(m)}", st_cell)])
                        if i % 2 == 0:
                            mon_style.append(("BACKGROUND", (0, i), (-1, i),
                                             colors.HexColor(C_LG)))
                    mon_t = Table(mon_rows, colWidths=[W])
                    mon_t.setStyle(TableStyle(mon_style))
                    els.append(mon_t)
                    els.append(Spacer(1, 8))

                # 数据质量说明
                dq = advisor.get("data_quality_note", "")
                if dq:
                    els.append(Paragraph(f"<b>数据质量：</b>{dq}", st_small))

            # ══════════════════════════════════════════════════════════════════
            # § 10  市场图表
            # ══════════════════════════════════════════════════════════════════
            if any(charts.get(k) and os.path.exists(charts[k])
                   for k in ["price_trend", "volume", "technical"]):
                els += sec("十、市场行情图表", C_NAV)

            if charts.get("price_trend") and os.path.exists(charts["price_trend"]):
                els += sec("股价走势", C_BLUE, sz=12)
                els += chart_img(charts["price_trend"],
                                 "图：股价走势与移动均线（MA5 / MA20 / MA60）",
                                 W * 0.50)

            if charts.get("volume") and os.path.exists(charts["volume"]):
                els += sec("成交量分析", C_BLUE, sz=12)
                els += chart_img(charts["volume"],
                                 "图：股价与成交量（红涨绿跌）", W * 0.55)

            if charts.get("technical") and os.path.exists(charts["technical"]):
                els += sec("技术指标 (RSI & MACD)", C_BLUE, sz=12)
                els += chart_img(charts["technical"],
                                 "图：RSI 超买超卖 & MACD 趋势指标", W * 0.68)

            # ══════════════════════════════════════════════════════════════════
            # § 11  AI 分析过程
            # ══════════════════════════════════════════════════════════════════
            if cog_info:
                els += sec("十一、AI 分析过程（思维链）", C_GRAY)
                plan   = cog_info.get("plan", {})
                review = cog_info.get("final_review", {})
                if plan:
                    focus = ", ".join(_s(x) for x in plan.get("analysis_focus", []))
                    els.append(Paragraph(f"<b>分析重点：</b>{focus}", st_body))
                    els.append(Paragraph(
                        f"<b>复杂度：</b>{_s(plan.get('estimated_complexity', 'N/A'))}", st_small))
                if review:
                    q_score  = review.get("quality_score", "N/A")
                    approved = "是" if review.get("approved") else "否"
                    els.append(Paragraph(
                        f"<b>质量评分：</b>{q_score}/10　　<b>审核通过：</b>{approved}", st_body))
                els.append(Spacer(1, 6))

            # ══════════════════════════════════════════════════════════════════
            # § 12  数据来源声明 (Apple报告有16条引用)
            # ══════════════════════════════════════════════════════════════════
            els += sec("十二、数据来源与免责声明", C_GRAY)

            ds = fin_data.get("data_source", "未知")
            src_items = [
                f"股票行情数据：AKShare / Tushare（数据源：{ds}）",
                "财务报表数据：AKShare（新浪财经 / 东方财富）或 Tushare Pro",
                "新闻资讯数据：东方财富（stock_news_em）/ 财联社（stock_news_main_cx）",
                "大模型分析：Gemini 2.5 Flash（Google Generative AI）",
                "图表生成：Matplotlib / ReportLab（本地计算）",
            ]
            for i, src in enumerate(src_items, 1):
                els.append(Paragraph(f"[{i}]  {src}", st_small))
            els.append(Spacer(1, 6))
            els.append(Paragraph(
                "本报告全部内容均由人工智能系统自动生成，不代表任何机构的官方观点。"
                "所有分析结论和预测仅供研究参考，不构成投资建议，不作为买卖决策依据。"
                "投资有风险，入市须谨慎。",
                st_small))
            els.append(Spacer(1, 8))

            # ── 生成 PDF ──────────────────────────────────────────────────────
            doc.build(els)
            logger.info(f"[Report] PDF 报告已生成: {filepath}")
            return filepath

        except ImportError as e:
            logger.error(f"reportlab 未安装: {e}")
            return None
        except Exception as e:
            import traceback
            logger.error(f"PDF 生成失败: {e}\n{traceback.format_exc()}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _register_font(pdfmetrics, TTFont) -> str:
        candidates = [
            ("C:/Windows/Fonts/simhei.ttf",  "SimHei"),
            ("C:/Windows/Fonts/simsun.ttc",  "SimSun"),
            ("C:/Windows/Fonts/msyh.ttc",    "MicrosoftYaHei"),
            ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", "NotoSansCJK"),
            ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "NotoSansCJK"),
        ]
        for path, name in candidates:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(name, path))
                    logger.info(f"[PDF] 中文字体已注册: {name}")
                    return name
                except Exception:
                    continue
        logger.warning("[PDF] 未找到中文字体，使用 Helvetica")
        return "Helvetica"

    @staticmethod
    def _rating_color(action: str) -> str:
        a = (action or "").lower()
        if any(k in a for k in ["增持", "买入", "strong buy", "buy", "outperform"]):
            return C_GREEN
        if any(k in a for k in ["减持", "卖出", "sell", "underperform"]):
            return C_RED
        return C_ORA
