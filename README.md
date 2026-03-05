# Stock Deep Research

多智能体股票深度研究框架，融合两篇学术论文的架构设计：

- **Cogito** — 认知智能体框架（感知→规划→执行→反思循环）
- **FinRpt** — 自动化股票研究报告生成

支持 A 股、美股、港股，输出含图表的专业 PDF/Markdown 研究报告。

---

## 架构

```
python main.py --stock 600519
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│                       Orchestrator                          │
│                    统一调度 5 个阶段                          │
└────────────┬──────────────────────────────────┬────────────┘
             │                                  │
    ┌────────▼────────┐               ┌─────────▼────────┐
    │  Cognitive 认知层 │               │   Data 数据采集层  │
    │  ┌────────────┐  │               │  ┌─────────────┐ │
    │  │  Planner   │  │  Phase 0/4    │  │ MarketData  │ │
    │  │  Reflector │  │◄─────────────►│  │ FinancialData│ │
    │  │  Memory    │  │               │  │ NewsCrawler │ │
    │  └────────────┘  │               │  └─────────────┘ │
    └─────────────────┘               └──────────────────┘
             │
    ┌────────▼──────────────────────────────────────────────┐
    │              Analysis Agents  (Phase 2–4)             │
    │                                                       │
    │  Phase 2 并行:  FinancialAnalyst  NewsAnalyst         │
    │                 CompetitiveAnalyst                    │
    │                                                       │
    │  Phase 3 串行:  RiskAssessor → Predictor             │
    │                                                       │
    │  Phase 4 综合:  InvestmentAdvisor + 跨智能体一致性检查  │
    └────────────────────────────┬──────────────────────────┘
                                 │
    ┌────────────────────────────▼──────────────────────────┐
    │               Report Generation  (Phase 5)            │
    │         ChartGenerator → MarkdownBuilder → PDFBuilder │
    └───────────────────────────────────────────────────────┘
```

### 5 个执行阶段

| 阶段 | 名称 | 内容 |
|------|------|------|
| Phase 1 | 数据采集 | 行情、财务、新闻三路并行拉取（akshare→tushare→yfinance 三级降级） |
| Phase 0 | 认知规划 | Planner 根据数据生成个性化分析焦点，写入 Memory |
| Phase 2 | 并行分析 | FinancialAnalyst、NewsAnalyst、CompetitiveAnalyst 并发执行 |
| Phase 3 | 串行分析 | RiskAssessor 评估风险后 Predictor 生成价格预测 |
| Phase 4 | 综合决策 | InvestmentAdvisor 汇总，Reflector 做跨智能体一致性检查 |
| Phase 5 | 报告生成 | 生成 6 张图表，输出 PDF / Markdown 报告 |

### 认知循环（每个智能体内部）

```
perceive(输入上下文)
  → plan(分解子任务)
    → execute(调用 LLM)
      → reflect(检查输出质量)
        → act(决定继续/完成)
```

最多迭代 `max_rounds`（默认 3）次，直到质量达标或轮次用尽。

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

```bash
cp config/config_example.yaml config/config.yaml
```

编辑 `config/config.yaml`，或直接用 `.env` 文件（优先级更高）：

```dotenv
# .env
LLM_PROVIDER=openai
LLM_API_KEY=sk-xxxx
LLM_MODEL=gpt-4o

# 可选：代理
LLM_PROXY=http://127.0.0.1:7890

# 可选：Tushare（A股备用数据源）
TUSHARE_TOKEN=xxxx
```

### 3. 运行

```bash
# A股（默认中文报告）
python main.py --stock 600519

# 美股（英文报告）
python main.py --stock AAPL --language en

# 港股，指定分析目标
python main.py --stock 00700.HK --goal "分析腾讯云计算业务前景"

# 同时输出 PDF 和 Markdown
python main.py --stock 301500 --output both

# 调试模式
python main.py --stock 600519 --log-level DEBUG
```

### 完整参数

```
--stock,   -s   股票代码（必填）。A股: 600519；美股: AAPL；港股: 00700.HK
--language,-l   报告语言: zh（默认）/ en
--output,  -o   输出格式: pdf（默认）/ markdown / both
--output-dir    输出目录（默认: ./output）
--goal,    -g   分析目标（默认: "全面深度研究"）
--config,  -c   配置文件路径（默认: config/config.yaml）
--no-reflection 禁用认知反思（加速但降低质量）
--no-planning   禁用认知规划
--log-level     日志级别: DEBUG / INFO（默认）/ WARNING / ERROR
```

---

## 支持的 LLM

在 `config.yaml` 的 `llm.provider` 或 `.env` 的 `LLM_PROVIDER` 中配置：

| Provider | provider 值 | 对应 env |
|----------|------------|----------|
| OpenAI | `openai` | `OPENAI_API_KEY` |
| Anthropic Claude | `anthropic` | `ANTHROPIC_API_KEY` |
| Azure OpenAI | `azure` | `AZURE_OPENAI_API_KEY` |
| xAI Grok | `grok` | `GROK_API_KEY` |
| Google Gemini | `gemini` | `GEMINI_API_KEY` |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` |
| Kimi (月之暗面) | `kimi` | `KIMI_API_KEY` |
| GLM (智谱) | `glm` | `GLM_API_KEY` |
| 豆包 (ByteDance) | `doubao` | `DOUBAO_API_KEY` |
| 通义千问 | `qwen` | `QWEN_API_KEY` |
| MiniMax | `minimax` | `MINIMAX_API_KEY` |
| Perplexity | `perplexity` | `PERPLEXITY_API_KEY` |

---

## 数据源

| 数据类型 | 主数据源 | 备用 1 | 备用 2 |
|----------|---------|--------|--------|
| A股行情 | akshare | tushare | yfinance |
| A股财务 | akshare (新浪财报) | tushare | yfinance |
| A股新闻 | 东方财富 (akshare) | 财新快讯 | — |
| 美股/港股 | yfinance | — | — |

Tushare 需要 token（免费注册获取），填入 `.env` 的 `TUSHARE_TOKEN`。

---

## 项目结构

```
stock_deep_research/
├── main.py                      # 入口，CLI 参数解析
├── requirements.txt
├── config/
│   ├── config_example.yaml      # 配置模板（复制为 config.yaml 使用）
│   └── settings.py              # 配置加载（.env 优先于 yaml）
├── agents/
│   ├── base.py                  # BaseAgent：认知循环实现
│   ├── orchestrator.py          # 5 阶段流水线编排
│   ├── financial_analyst.py     # 财务分析
│   ├── news_analyst.py          # 新闻情感分析
│   ├── competitive_analyst.py   # 竞争格局分析
│   ├── risk_assessor.py         # 风险评估
│   ├── predictor.py             # 价格趋势预测
│   └── advisor.py               # 投资建议综合
├── cognitive/
│   ├── planner.py               # 认知规划（生成分析焦点）
│   ├── reflector.py             # 跨智能体一致性检查
│   └── memory.py                # 持久化记忆管理
├── data_sources/
│   ├── market_data.py           # 行情 + 公司基本信息
│   ├── financial_data.py        # 财务三表（三级降级）
│   └── news_crawler.py          # 新闻采集与去重
├── report/
│   ├── chart_generator.py       # matplotlib 图表（价格/量/技术/财务）
│   ├── pdf_builder.py           # reportlab PDF 生成
│   └── markdown_builder.py      # Markdown 生成
├── utils/
│   ├── llm_client.py            # 统一 LLM 客户端，含 json_repair 兜底
│   ├── data_processing.py       # 数据清洗工具
│   ├── dedup.py                 # MinHash + BERT 新闻去重
│   └── remote_call.py           # HTTP 请求统一超时补丁
└── prompts/
    └── templates.py             # 所有智能体提示词模板
```

---

## 输出示例

运行后在 `./output/` 生成：

```
output/
├── 600519_research_report_20260304_111727.pdf   # 主报告
├── 600519_price.png       # 价格趋势 + MA 均线
├── 600519_volume.png      # 成交量
├── 600519_technical.png   # 技术指标（MACD / RSI / 布林带）
├── 600519_revenue.png     # 营收与利润趋势
├── 600519_margin.png      # 毛利率 / 净利率
└── 600519_cashflow.png    # 经营现金流
```

---

## 参考论文

- Cogito: *A Cognitive Agentive Framework for Stock Market Analysis*
- FinRpt: *Automated Multi-Modal Equity Research Report Generation*
