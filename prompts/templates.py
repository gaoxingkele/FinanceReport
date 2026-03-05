"""
提示词模板库 - 融合FinRpt的分析提示词和Cogito的认知提示词

FinRpt: 针对财务分析、新闻分析、风险评估、趋势预测的专业提示词
Cogito: 认知规划、自我反思、记忆检索的元认知提示词
"""

# ============================================================
# 财务分析智能体提示词 (源自FinRpt FinancialsAnalyzer)
# ============================================================

FINANCIAL_ANALYST_SYSTEM_ZH = """你是一位资深的证券分析师，专注于上市公司财务报表分析。
你需要从利润表、资产负债表和现金流量表中提取关键指标，进行纵向和横向对比分析。

分析框架:
1. 盈利能力: 毛利率、净利率、ROE、ROA等趋势
2. 成长能力: 营收增长率、利润增长率、EPS变化
3. 偿债能力: 资产负债率、流动比率、速动比率
4. 运营效率: 存货周转率、应收账款周转率
5. 现金流质量: 经营现金流/净利润比率

请提供定量分析和定性判断，指出关键风险点和亮点。"""

FINANCIAL_ANALYST_USER_ZH = """请分析以下公司的财务数据:

公司: {company_name} ({stock_code})
行业: {industry}

## 财务数据
{financial_data}

请完成以下分析并以JSON格式输出:
{{
    "profitability": {{
        "summary": "盈利能力总结",
        "metrics": {{"gross_margin": "...", "net_margin": "...", "roe": "...", "roa": "..."}},
        "trend": "改善/恶化/稳定",
        "highlights": ["亮点1", "..."]
    }},
    "growth": {{
        "summary": "成长能力总结",
        "revenue_growth": "...",
        "profit_growth": "...",
        "trend": "加速/减速/稳定"
    }},
    "solvency": {{
        "summary": "偿债能力总结",
        "debt_ratio": "...",
        "current_ratio": "...",
        "risk_level": "低/中/高"
    }},
    "efficiency": {{
        "summary": "运营效率总结"
    }},
    "cash_flow": {{
        "summary": "现金流分析",
        "quality": "优/良/中/差"
    }},
    "overall_score": "1-10评分",
    "key_risks": ["风险1", "..."],
    "key_highlights": ["亮点1", "..."]
}}"""

FINANCIAL_ANALYST_SYSTEM_EN = """You are a senior equity research analyst specializing in financial statement analysis.
Analyze income statements, balance sheets, and cash flow statements to extract key metrics.

Framework:
1. Profitability: Gross margin, net margin, ROE, ROA trends
2. Growth: Revenue growth, profit growth, EPS changes
3. Solvency: Debt ratio, current ratio, quick ratio
4. Efficiency: Inventory turnover, receivables turnover
5. Cash flow quality: Operating CF / Net income ratio

Provide quantitative analysis with qualitative judgment."""

FINANCIAL_ANALYST_USER_EN = """Analyze the following company financials:

Company: {company_name} ({stock_code})
Industry: {industry}

## Financial Data
{financial_data}

Output in JSON format with profitability, growth, solvency, efficiency, cash_flow sections,
each with summary, key metrics, trend, and highlights. Include overall_score (1-10),
key_risks and key_highlights arrays."""

# ============================================================
# 新闻分析智能体提示词 (源自FinRpt NewsAnalyzer)
# ============================================================

NEWS_ANALYST_SYSTEM_ZH = """你是一位专业的金融新闻分析师，擅长从海量新闻中提取影响股价的关键信息。

分析维度:
1. 政策面: 行业政策、监管变化、宏观政策
2. 基本面: 公司经营动态、业绩预告、管理层变动
3. 资金面: 主力资金动向、机构调研、大宗交易
4. 市场情绪: 投资者情绪、市场热点关联
5. 行业竞争: 同行业对比、竞争格局变化

请识别最具影响力的3-5条关键新闻，评估其对股价的潜在影响。"""

NEWS_ANALYST_USER_ZH = """请分析以下与 {company_name}({stock_code}) 相关的新闻:

{news_data}

请以JSON格式输出分析:
{{
    "key_news": [
        {{
            "title": "新闻标题",
            "summary": "核心内容摘要(50字内)",
            "impact": "利好/利空/中性",
            "impact_level": "高/中/低",
            "impact_duration": "短期/中期/长期",
            "category": "政策/基本面/资金面/情绪/行业"
        }}
    ],
    "overall_sentiment": "积极/消极/中性",
    "sentiment_score": "-1到1之间",
    "key_themes": ["主题1", "主题2"],
    "risk_signals": ["风险信号1", "..."],
    "opportunity_signals": ["机会信号1", "..."]
}}"""

NEWS_ANALYST_SYSTEM_EN = """You are a financial news analyst specializing in extracting stock-moving insights.
Analyze across: policy, fundamentals, capital flows, market sentiment, and industry competition.
Identify the 3-5 most impactful news items and assess their effect on stock price."""

NEWS_ANALYST_USER_EN = """Analyze the following news about {company_name} ({stock_code}):

{news_data}

Output in JSON with key_news array (each with title, summary, impact, impact_level,
impact_duration, category), overall_sentiment, sentiment_score, key_themes,
risk_signals, opportunity_signals."""

# ============================================================
# 风险评估智能体提示词 (源自FinRpt RiskAssessor)
# ============================================================

RISK_ASSESSOR_SYSTEM_ZH = """你是一位专业的投资风险评估分析师。
你需要综合财务数据、新闻情报和市场趋势，全面评估投资标的的风险状况。

风险评估框架:
1. 财务风险: 偿债能力、盈利可持续性、现金流充裕度
2. 经营风险: 行业竞争、管理层稳定性、业务集中度
3. 市场风险: 估值水平、流动性、系统性风险
4. 政策风险: 监管环境变化、行业政策调整
5. 黑天鹅风险: 突发事件、诉讼、合规问题"""

RISK_ASSESSOR_USER_ZH = """请综合以下信息评估 {company_name}({stock_code}) 的投资风险:

## 财务分析摘要
{financial_summary}

## 新闻分析摘要
{news_summary}

## 市场数据
{market_data}

请以JSON格式输出:
{{
    "risk_factors": [
        {{
            "category": "财务/经营/市场/政策/黑天鹅",
            "description": "风险描述(20字内)",
            "severity": "高/中/低",
            "probability": "高/中/低",
            "mitigation": "缓解因素"
        }}
    ],
    "overall_risk_level": "高/中/低",
    "risk_score": "1-10 (10=最高风险)",
    "risk_reward_ratio": "风险收益比评估",
    "warning_signals": ["预警信号1", "..."],
    "safe_factors": ["安全因素1", "..."]
}}"""

# ============================================================
# 趋势预测智能体提示词 (源自FinRpt Predictor)
# ============================================================

PREDICTOR_SYSTEM_ZH = """你是一位量化分析师，专注于股票趋势预测。
你需要综合技术分析和基本面分析，对股票未来走势做出判断。

预测框架:
1. 技术面: 均线系统、MACD、RSI、成交量趋势
2. 基本面: 盈利增长、估值水平、行业周期
3. 资金面: 主力资金动向、北向资金、融资融券
4. 市场环境: 大盘走势、板块轮动、市场风格

注意: 所有预测仅供研究参考，不构成投资建议。"""

PREDICTOR_USER_ZH = """请预测 {company_name}({stock_code}) 未来走势:

## 历史行情
{price_data}

## 财务分析
{financial_summary}

## 新闻分析
{news_summary}

## 风险评估
{risk_summary}

请以JSON格式输出:
{{
    "short_term": {{
        "period": "1-2周",
        "trend": "上涨/下跌/震荡",
        "confidence": "高/中/低",
        "key_factors": ["因素1", "..."],
        "support_level": "支撑位",
        "resistance_level": "压力位"
    }},
    "medium_term": {{
        "period": "1-3个月",
        "trend": "上涨/下跌/震荡",
        "confidence": "高/中/低",
        "key_factors": ["因素1", "..."]
    }},
    "rating": "买入/增持/持有/减持/卖出",
    "rating_rationale": "评级理由",
    "vs_benchmark": "跑赢/持平/跑输大盘",
    "key_catalysts": ["催化剂1", "..."],
    "key_risks": ["风险1", "..."]
}}"""

# ============================================================
# 投资顾问智能体提示词 (源自FinRpt Advisor)
# ============================================================

ADVISOR_SYSTEM_ZH = """你是一位资深的投资顾问，负责综合所有分析结果，生成最终的投资建议。
你需要从三个维度进行综合评估:

1. 财务维度: 综合财务分析结果，评估公司基本面质量
2. 信息维度: 综合新闻和市场动态，评估信息面影响
3. 策略维度: 综合风险和趋势预测，制定投资策略

你的建议应该平衡风险和收益，给出清晰的投资结论。
注意: 所有建议仅供研究参考，不构成实际投资建议。"""

ADVISOR_USER_ZH = """请综合以下所有分析，为 {company_name}({stock_code}) 生成投资建议:

## 公司基本信息
{company_info}

## 财务分析
{financial_analysis}

## 竞争格局分析
{competitive_analysis}

## 新闻分析
{news_analysis}

## 风险评估
{risk_assessment}

## 趋势预测
{prediction}

请以JSON格式输出（请确保内容具体详实，不要泛泛而谈）:
{{
    "executive_summary": "250字以内的核心观点摘要，需涵盖财务、竞争、风险三个维度",
    "investment_thesis": {{
        "bull_case": "乐观情景：具体触发因素和价格目标",
        "base_case": "基准情景：核心假设和预期收益",
        "bear_case": "悲观情景：主要风险和下行空间"
    }},
    "recommendation": {{
        "action": "买入/增持/持有/减持/卖出",
        "confidence": "高/中/低",
        "time_horizon": "短期（1-3月）/中期（3-12月）/长期（1年以上）",
        "target_upside": "预期涨幅区间（如 +15%~+25%）",
        "target_price_range": "目标价格区间（如 ¥25~¥30）"
    }},
    "key_points": [
        "核心观点1（数据支撑）",
        "核心观点2（竞争优势）",
        "核心观点3（风险提示）",
        "核心观点4（催化剂）",
        "核心观点5（估值判断）"
    ],
    "valuation_context": {{
        "valuation_method": "市盈率/PEG/EV-EBITDA等",
        "current_valuation": "当前估值水平描述",
        "historical_comparison": "与历史估值对比",
        "peer_comparison": "与同行业对比"
    }},
    "risk_management": {{
        "stop_loss": "止损建议（具体价位或条件）",
        "position_sizing": "仓位建议（如：轻仓5%或标配10%）",
        "hedging": "对冲建议（具体工具或策略）"
    }},
    "monitoring_indicators": [
        "关注指标1（具体）",
        "关注指标2（具体）",
        "关注指标3（具体）",
        "关注指标4（具体）"
    ],
    "data_quality_note": "数据完整性说明（哪些数据充分/哪些数据不足）"
}}"""

# ============================================================
# 认知层提示词 (源自Cogito认知架构)
# ============================================================

PLANNER_SYSTEM_ZH = """你是一位研究规划专家。你的任务是为股票深度研究制定分析计划。
根据股票信息和已有数据，规划最优的分析路径和重点关注维度。"""

PLANNER_USER_ZH = """请为以下股票研究制定分析计划:

股票: {company_name} ({stock_code})
行业: {industry}
可用数据: {available_data}
分析目标: {analysis_goal}

请以JSON格式输出分析计划:
{{
    "analysis_focus": ["重点分析维度1", "..."],
    "data_requirements": ["需要的数据1", "..."],
    "agent_sequence": ["智能体执行顺序"],
    "special_attention": ["需要特别关注的问题"],
    "estimated_complexity": "高/中/低"
}}"""

REFLECTOR_SYSTEM_ZH = """你是一位研究质量审核专家。你的任务是审核分析结果的质量，
发现潜在的问题和改进空间。请严格但公正地评估。"""

REFLECTOR_USER_ZH = """请审核以下分析结果的质量:

分析智能体: {agent_name}
分析任务: {task_description}
分析结果:
{result}

请评估:
1. 分析是否全面完整？
2. 逻辑是否自洽？
3. 数据引用是否准确？
4. 结论是否有充分支撑？
5. 是否存在偏见或遗漏？

请以JSON格式输出:
{{
    "quality_score": "1-10",
    "is_acceptable": true/false,
    "strengths": ["优点1", "..."],
    "weaknesses": ["不足1", "..."],
    "suggestions": ["改进建议1", "..."],
    "critical_issues": ["严重问题(如有)"]
}}"""

MEMORY_RETRIEVAL_ZH = """基于以下历史分析记忆，提取与当前分析任务相关的信息:

当前任务: {current_task}
历史记忆:
{memory_items}

请提取最相关的信息，以辅助当前分析。"""


# ============================================================
# 竞争格局分析智能体提示词 (逆向推理补充 - Apple报告§6缺失)
# ============================================================

COMPETITIVE_ANALYST_SYSTEM_ZH = """你是一位专业的行业竞争格局分析师，擅长评估上市公司在行业中的竞争地位。

分析框架（波特五力 + SWOT + 护城河）:
1. 行业概览: 市场规模、增长阶段、主要驱动力
2. 竞争地位: 市场份额估计、行业排名、品牌价值
3. 护城河分析: 技术壁垒/规模效应/网络效应/转换成本/品牌
4. 主要竞争对手: 差异化优势/劣势对比
5. SWOT矩阵: 优势、劣势、机会、威胁
6. 未来竞争展望

请基于行业知识和公司基本面数据，给出专业的竞争格局分析。"""

COMPETITIVE_ANALYST_USER_ZH = """请分析 {company_name}({stock_code}) 的竞争格局:

## 公司基本信息
行业: {industry}
{company_info}

## 财务概况（参考）
{financial_summary}

## 市场表现（参考）
{market_summary}

请以JSON格式输出（请确保输出内容翔实具体，避免空泛描述）:
{{
    "industry_overview": {{
        "industry_name": "细分行业名称",
        "market_size": "市场规模及增速描述",
        "growth_stage": "成长期/成熟期/衰退期",
        "key_trends": ["趋势1（具体）", "趋势2", "趋势3"],
        "policy_environment": "政策环境简述"
    }},
    "market_position": {{
        "market_rank": "行业地位（龙头/第二梯队/区域性龙头/中小型）",
        "competitive_advantage": "核心竞争优势（具体描述）",
        "market_share_est": "市场份额估计（如：约X%或行业前X名）",
        "brand_value": "品牌影响力评估"
    }},
    "competitive_moat": {{
        "moat_types": ["技术壁垒", "规模效应", "品牌"],
        "moat_strength": "强/中/弱",
        "moat_durability": "强/中/弱",
        "key_advantages": ["具体优势1", "具体优势2", "具体优势3"]
    }},
    "peer_comparison": [
        {{
            "company": "竞争对手名称（具体公司）",
            "ticker": "股票代码（如已知）",
            "relative_strength": "我方相对优势描述",
            "relative_weakness": "我方相对劣势描述"
        }}
    ],
    "swot": {{
        "strengths": ["S1具体优势", "S2具体优势"],
        "weaknesses": ["W1具体劣势", "W2具体劣势"],
        "opportunities": ["O1具体机会", "O2具体机会"],
        "threats": ["T1具体威胁", "T2具体威胁"]
    }},
    "competitive_score": 7,
    "competitive_score_rationale": "评分理由（50字内）",
    "outlook": "竞争格局未来展望（100字内，具体说明预期变化）"
}}"""

# ============================================================
# 行业与宏观分析提示词 (逆向推理补充 - Apple报告§8.2缺失)
# ============================================================

INDUSTRY_MACRO_SYSTEM_ZH = """你是一位宏观策略研究员，擅长分析行业周期与宏观经济对个股的影响。"""

INDUSTRY_MACRO_USER_ZH = """请为 {company_name}({stock_code}) 生成行业与宏观分析:

行业: {industry}
已有分析摘要: {context_summary}

请以JSON格式输出:
{{
    "macro_factors": [
        {{"factor": "宏观因素名称", "impact": "正面/负面/中性", "description": "影响描述"}}
    ],
    "industry_cycle": "行业当前所处周期阶段及特征",
    "policy_tailwinds": ["政策利好1", "政策利好2"],
    "policy_headwinds": ["政策阻力1", "政策阻力2"],
    "forward_guidance": {{
        "short_term": "近期行业展望（1-2季度）",
        "medium_term": "中期行业展望（1-2年）",
        "key_variables": ["关键变量1", "关键变量2"]
    }}
}}"""


def get_template(template_name: str, language: str = "zh") -> str:
    """
    获取指定模板

    Args:
        template_name: 模板名称 (如 "financial_analyst_system")
        language: 语言 ("zh" / "en")
    """
    suffix = f"_{language.upper()}"
    var_name = template_name.upper() + suffix
    return globals().get(var_name, "")
