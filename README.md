# Stock Deep Research - 多智能体股票深度研究框架

基于 Cogito (认知智能体) 和 FinRpt (金融报告生成) 两篇论文的多智能体架构，
用于生成专业级多模态股票深度研究报告。

## 架构概览

```
┌─────────────────────────────────────────────────────┐
│                  Orchestrator (编排器)                │
│         统一调度所有智能体，管理工作流                    │
├─────────────────────────────────────────────────────┤
│  Cognitive Layer (认知层 - 源自Cogito)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐        │
│  │ Planner  │ │ Reflector│ │MemoryManager │        │
│  │ 任务规划  │ │ 自我反思  │ │  记忆管理     │        │
│  └──────────┘ └──────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────┤
│  Data Agents (数据采集层)                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐        │
│  │ Market   │ │  News    │ │  Financial   │        │
│  │ DataAgent│ │ Crawler  │ │  DataAgent   │        │
│  └──────────┘ └──────────┘ └──────────────┘        │
├─────────────────────────────────────────────────────┤
│  Analysis Agents (分析层 - 融合FinRpt+Cogito)        │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐        │
│  │Financial │ │  News    │ │    Risk      │        │
│  │ Analyst  │ │ Analyst  │ │  Assessor    │        │
│  └──────────┘ └──────────┘ └──────────────┘        │
│  ┌──────────┐ ┌──────────────────────────┐          │
│  │Predictor │ │  Investment Advisor      │          │
│  └──────────┘ └──────────────────────────┘          │
├─────────────────────────────────────────────────────┤
│  Report Generation (报告生成层)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐        │
│  │  Chart   │ │   PDF    │ │  Markdown    │        │
│  │Generator │ │ Builder  │ │  Builder     │        │
│  └──────────┘ └──────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────┘
```

## 快速开始

```bash
pip install -r requirements.txt
cp config/config_example.yaml config/config.yaml
# 编辑 config.yaml 填入API密钥
python main.py --stock 600519 --language zh
```

## 项目结构

```
stock_deep_research/
├── main.py                 # 主入口
├── requirements.txt        # 依赖
├── config/
│   ├── config_example.yaml # 配置模板
│   └── settings.py         # 配置加载
├── agents/
│   ├── base.py             # 基础智能体类
│   ├── financial_analyst.py# 财务分析智能体
│   ├── news_analyst.py     # 新闻分析智能体
│   ├── risk_assessor.py    # 风险评估智能体
│   ├── predictor.py        # 趋势预测智能体
│   ├── advisor.py          # 投资建议智能体
│   └── orchestrator.py     # 多智能体编排器
├── cognitive/
│   ├── planner.py          # 认知规划器
│   ├── reflector.py        # 自我反思模块
│   └── memory.py           # 记忆管理
├── data_sources/
│   ├── market_data.py      # 行情数据采集
│   ├── news_crawler.py     # 新闻采集
│   └── financial_data.py   # 财务数据采集
├── report/
│   ├── chart_generator.py  # 图表生成
│   ├── pdf_builder.py      # PDF报告生成
│   └── markdown_builder.py # Markdown报告生成
├── utils/
│   ├── llm_client.py       # LLM统一接口
│   ├── data_processing.py  # 数据处理工具
│   └── dedup.py            # 去重工具
└── prompts/
    └── templates.py        # 所有提示词模板
```
