"""
多智能体编排器 - 融合FinRpt的FinRpt.py工作流和Cogito的认知调度

工作流 (12步，源自FinRpt，增强Cogito认知):

Phase 0: 认知规划 (Cogito)
  0. Planner → 分析计划

Phase 1: 数据采集
  1. MarketDataAgent → 行情数据
  2. FinancialDataAgent → 财务数据
  3. NewsCrawler → 新闻数据 + 去重

Phase 2: 并行分析 (FinRpt架构 + Cogito反思)
  4. FinancialAnalyst → 财务分析 (含反思)
  5. NewsAnalyst → 新闻分析 (含反思)

Phase 3: 串行深度分析
  6. RiskAssessor → 风险评估 (含反思)
  7. Predictor → 趋势预测 (含反思)

Phase 4: 综合决策
  8. InvestmentAdvisor → 投资建议 (含反思)
  9. CrossAgentCheck → 跨智能体一致性检查 (Cogito)
  10. FinalReview → 终审 (Cogito)

Phase 5: 报告生成
  11. ChartGenerator → 图表
  12. ReportBuilder → PDF/Markdown报告
"""
import json
import logging
import time
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.llm_client import LLMClient
from config.settings import Settings

from data_sources.market_data import MarketDataAgent
from data_sources.financial_data import FinancialDataAgent
from data_sources.news_crawler import NewsCrawler

from agents.financial_analyst import FinancialAnalyst
from agents.news_analyst import NewsAnalyst
from agents.competitive_analyst import CompetitiveAnalyst
from agents.risk_assessor import RiskAssessor
from agents.predictor import Predictor
from agents.advisor import InvestmentAdvisor

from cognitive.planner import CognitivePlanner
from cognitive.reflector import CognitiveReflector
from cognitive.memory import MemoryManager

from report.chart_generator import ChartGenerator
from report.markdown_builder import MarkdownReportBuilder
from report.pdf_builder import PDFReportBuilder

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    多智能体编排器

    统一调度所有智能体，管理数据流和工作流。
    融合FinRpt的顺序/并行执行和Cogito的认知增强。
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = LLMClient(settings.llm)

        # 数据采集智能体
        self.market_agent = MarketDataAgent(language=settings.agents.language)
        self.financial_agent = FinancialDataAgent(language=settings.agents.language)
        self.news_agent = NewsCrawler(
            language=settings.agents.language,
            max_items=settings.dedup.max_news_items,
            dedup_threshold=settings.dedup.bert_threshold,
        )

        # 分析智能体
        self.financial_analyst = FinancialAnalyst(
            llm=self.llm,
            language=settings.agents.language,
            max_rounds=settings.agents.max_rounds,
            enable_reflection=settings.cognitive.enable_reflection,
        )
        self.news_analyst = NewsAnalyst(
            llm=self.llm,
            language=settings.agents.language,
            max_rounds=settings.agents.max_rounds,
            enable_reflection=settings.cognitive.enable_reflection,
        )
        self.risk_assessor = RiskAssessor(
            llm=self.llm,
            language=settings.agents.language,
            max_rounds=settings.agents.max_rounds,
            enable_reflection=settings.cognitive.enable_reflection,
        )
        self.predictor = Predictor(
            llm=self.llm,
            language=settings.agents.language,
            max_rounds=settings.agents.max_rounds,
            enable_reflection=settings.cognitive.enable_reflection,
        )
        self.competitive_analyst = CompetitiveAnalyst(
            llm=self.llm,
            language=settings.agents.language,
            max_rounds=settings.agents.max_rounds,
            enable_reflection=settings.cognitive.enable_reflection,
        )
        self.advisor = InvestmentAdvisor(
            llm=self.llm,
            language=settings.agents.language,
            max_rounds=settings.agents.max_rounds,
            enable_reflection=settings.cognitive.enable_reflection,
        )

        # 认知层 (Cogito)
        self.planner = CognitivePlanner(self.llm, settings.agents.language)
        self.reflector = CognitiveReflector(
            self.llm,
            settings.agents.language,
            depth=settings.cognitive.reflection_depth,
        )
        self.memory = MemoryManager(
            memory_dir=settings.report.output_dir + "/memory",
            max_items=settings.cognitive.memory_max_items,
        )

        # 报告生成
        self.chart_gen = ChartGenerator(
            output_dir=settings.report.output_dir,
            style=settings.report.chart_style,
        )
        self.md_builder = MarkdownReportBuilder(
            output_dir=settings.report.output_dir,
            language=settings.report.language,
        )
        self.pdf_builder = PDFReportBuilder(
            output_dir=settings.report.output_dir,
            language=settings.report.language,
        )

    def run(self, stock_code: str, analysis_goal: str = "全面深度研究") -> Dict[str, Any]:
        """
        执行完整的股票深度研究流程

        Args:
            stock_code: 股票代码
            analysis_goal: 分析目标

        Returns:
            包含所有分析结果和报告路径的字典
        """
        start_time = time.time()
        logger.info(f"{'='*60}")
        logger.info(f"开始深度研究: {stock_code}")
        logger.info(f"{'='*60}")

        # 共享数据字典 (FinRpt通信机制)
        data = {
            "stock_code": stock_code,
            "save": {},
        }

        # ============================================
        # Phase 1: 数据采集
        # ============================================
        logger.info("[Phase 1] 数据采集...")

        # 1.1 行情数据
        logger.info("  采集行情数据...")
        market_data = self.market_agent.fetch(stock_code)
        data["market_data"] = market_data
        data["company_info"] = market_data.get("company_info", {})
        market = market_data.get("market", "unknown")

        # 1.2 财务数据
        logger.info("  采集财务数据...")
        financial_data = self.financial_agent.fetch(stock_code, market=market)
        data["financial_data"] = financial_data

        # 1.3 新闻数据
        logger.info("  采集新闻数据...")
        company_name = data["company_info"].get("company_name", stock_code)
        news_data = self.news_agent.fetch(stock_code, company_name, market=market)
        data["news_data"] = news_data

        logger.info(
            f"  数据采集完成: 行情={len(market_data.get('price_data', []))}条, "
            f"新闻={news_data.get('news_count', 0)}条"
        )

        # ============================================
        # Phase 0: 认知规划 (Cogito)
        # ============================================
        plan = {}
        if self.settings.cognitive.enable_planning:
            logger.info("[Phase 0] 认知规划...")
            available_data = {
                "market": "error" not in market_data,
                "financials": "error" not in financial_data and bool(financial_data.get("text_summary")),
                "news": news_data.get("news_count", 0) > 0,
            }
            plan = self.planner.create_plan(
                stock_code=stock_code,
                company_info=data["company_info"],
                available_data=available_data,
                analysis_goal=analysis_goal,
            )
            data["analysis_plan"] = plan

        # 检索历史记忆
        if self.settings.cognitive.enable_memory:
            history = self.memory.retrieve_relevant(
                stock_code=stock_code,
                industry=data["company_info"].get("industry"),
            )
            if history:
                data["historical_analysis"] = history
                logger.info(f"  找到 {len(history)} 条历史分析记忆")

        # ============================================
        # Phase 2: 并行分析 (FinRpt + Cogito反思)
        # ============================================
        logger.info("[Phase 2] 并行分析...")

        if self.settings.agents.parallel_analysis:
            # 并行执行财务分析、新闻分析、竞争格局分析
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(self.financial_analyst.run, data):    "FinancialAnalyst",
                    executor.submit(self.news_analyst.run, data):         "NewsAnalyst",
                    executor.submit(self.competitive_analyst.run, data):  "CompetitiveAnalyst",
                }
                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        future.result()
                        logger.info(f"  {name} 完成")
                    except Exception as e:
                        logger.error(f"  {name} 失败: {e}")
        else:
            logger.info("  执行财务分析...")
            self.financial_analyst.run(data)
            logger.info("  执行新闻分析...")
            self.news_analyst.run(data)
            logger.info("  执行竞争格局分析...")
            self.competitive_analyst.run(data)

        # 动态调整计划 (Cogito自适应)
        if self.settings.cognitive.enable_planning and plan:
            plan = self.planner.adjust_plan(
                current_plan=plan,
                completed_agents=["FinancialAnalyst", "NewsAnalyst", "CompetitiveAnalyst"],
                intermediate_results=data.get("save", {}),
            )

        # ============================================
        # Phase 3: 串行深度分析
        # ============================================
        logger.info("[Phase 3] 深度分析...")

        logger.info("  执行风险评估...")
        self.risk_assessor.run(data)

        logger.info("  执行趋势预测...")
        self.predictor.run(data)

        # ============================================
        # Phase 4: 综合决策
        # ============================================
        logger.info("[Phase 4] 综合决策...")

        logger.info("  生成投资建议...")
        self.advisor.run(data)

        # 跨智能体一致性检查 (Cogito)
        if self.settings.cognitive.enable_reflection:
            logger.info("  跨智能体一致性检查...")
            consistency = self.reflector.cross_agent_check(data.get("save", {}))
            data["consistency_check"] = consistency

            # 终审
            logger.info("  最终质量审核...")
            final_review = self.reflector.final_review(
                advisor_result=data["save"].get("InvestmentAdvisor", {}),
                all_results=data.get("save", {}),
            )
            data["final_review"] = final_review

        # ============================================
        # Phase 5: 报告生成
        # ============================================
        logger.info("[Phase 5] 报告生成...")

        # 图表
        charts = {}
        if self.settings.report.include_charts:
            logger.info("  生成图表...")
            charts = self.chart_gen.generate_all(
                stock_code=stock_code,
                market_data=market_data,
                financial_data=financial_data,
            )

        # 认知信息
        data["cognitive_info"] = {
            "plan": plan,
            "consistency_check": data.get("consistency_check", {}),
            "final_review": data.get("final_review", {}),
        }

        # 报告文件
        report_paths = {}
        output_format = self.settings.report.output_format

        if output_format in ("markdown", "both"):
            logger.info("  生成Markdown报告...")
            md_path = self.md_builder.build(stock_code, data, charts)
            report_paths["markdown"] = md_path

        if output_format in ("pdf", "both"):
            logger.info("  生成PDF报告...")
            pdf_path = self.pdf_builder.build(stock_code, data, charts)
            if pdf_path:
                report_paths["pdf"] = pdf_path

        # ============================================
        # 保存记忆 (Cogito)
        # ============================================
        if self.settings.cognitive.enable_memory:
            advisor_result = data["save"].get("InvestmentAdvisor", {})
            self.memory.store_analysis_result(
                stock_code=stock_code,
                analysis_type="deep_research",
                result_summary=advisor_result.get("executive_summary", ""),
                key_findings=advisor_result.get("key_points", []),
                metadata={
                    "industry": data["company_info"].get("industry", ""),
                    "rating": advisor_result.get("recommendation", {}).get("action", ""),
                },
            )
            self.memory.save_long_term()

        # ============================================
        # 完成
        # ============================================
        elapsed = time.time() - start_time
        logger.info(f"{'='*60}")
        logger.info(f"深度研究完成: {stock_code}")
        logger.info(f"耗时: {elapsed:.1f}秒")
        logger.info(f"报告: {report_paths}")
        logger.info(f"{'='*60}")

        return {
            "stock_code": stock_code,
            "company_name": company_name,
            "report_paths": report_paths,
            "chart_paths": charts,
            "analysis_results": data.get("save", {}),
            "cognitive_info": data.get("cognitive_info", {}),
            "elapsed_seconds": elapsed,
        }
