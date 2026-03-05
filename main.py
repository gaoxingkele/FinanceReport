#!/usr/bin/env python3
"""
Stock Deep Research - 多智能体股票深度研究框架
主入口

融合论文:
  1. Cogito: A Cognitive Agentive Framework for Stock Market Analysis (认知智能体)
  2. FinRpt: Automated Equity Research Report Generation (金融报告生成)

用法:
  python main.py --stock 600519 --language zh
  python main.py --stock AAPL --language en --output both
  python main.py --stock 00700.HK --goal "分析腾讯云计算业务前景"
"""
import argparse
import logging
import os
import sys

# 将项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 最先导入，让全局 requests 超时补丁生效
import utils.remote_call  # noqa: F401

from config.settings import load_settings
from agents.orchestrator import Orchestrator


def setup_logging(level: str = "INFO"):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Stock Deep Research - 多智能体股票深度研究框架"
    )
    parser.add_argument(
        "--stock", "-s",
        type=str,
        required=True,
        help="股票代码 (例: 600519, AAPL, 00700.HK)",
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="配置文件路径 (默认: config/config.yaml)",
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default=None,
        choices=["zh", "en"],
        help="报告语言 (zh=中文, en=English)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        choices=["pdf", "markdown", "both"],
        help="输出格式",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="输出目录",
    )
    parser.add_argument(
        "--goal", "-g",
        type=str,
        default="全面深度研究",
        help="分析目标",
    )
    parser.add_argument(
        "--no-reflection",
        action="store_true",
        help="禁用认知反思（加速但降低质量）",
    )
    parser.add_argument(
        "--no-planning",
        action="store_true",
        help="禁用认知规划",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别",
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.log_level)

    # 加载配置
    settings = load_settings(args.config)

    # 命令行参数覆盖配置文件
    if args.language:
        settings.agents.language = args.language
        settings.report.language = args.language
    if args.output:
        settings.report.output_format = args.output
    if args.output_dir:
        settings.report.output_dir = args.output_dir
    if args.no_reflection:
        settings.cognitive.enable_reflection = False
    if args.no_planning:
        settings.cognitive.enable_planning = False

    # 确保输出目录存在
    os.makedirs(settings.report.output_dir, exist_ok=True)

    # 创建编排器并执行
    orchestrator = Orchestrator(settings)
    result = orchestrator.run(
        stock_code=args.stock,
        analysis_goal=args.goal,
    )

    # 打印结果摘要
    print("\n" + "=" * 60)
    print(f"  深度研究完成: {result['company_name']} ({result['stock_code']})")
    print(f"  耗时: {result['elapsed_seconds']:.1f} 秒")
    print(f"  报告文件:")
    for fmt, path in result.get("report_paths", {}).items():
        print(f"    [{fmt}] {path}")
    print(f"  图表文件:")
    for name, path in result.get("chart_paths", {}).items():
        print(f"    [{name}] {path}")
    print("=" * 60)

    return result


if __name__ == "__main__":
    main()
