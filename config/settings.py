"""
配置管理模块 - 加载和验证YAML配置
优先级: .env > config.yaml > 默认值
"""
import os
import yaml
from dataclasses import dataclass, field
from typing import Optional

# 自动加载 .env 文件（如果 python-dotenv 可用）
try:
    from dotenv import load_dotenv
    _env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(_env_file):
        load_dotenv(_env_file, override=True)
except ImportError:
    pass


@dataclass
class LLMConfig:
    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str = ""
    base_url: str = ""
    temperature: float = 0.1
    max_tokens: int = 4096
    max_retries: int = 3
    azure_api_version: str = "2024-02-01"
    azure_deployment: str = ""


@dataclass
class AgentConfig:
    max_rounds: int = 3
    language: str = "zh"
    parallel_analysis: bool = True


@dataclass
class CognitiveConfig:
    enable_reflection: bool = True
    enable_planning: bool = True
    enable_memory: bool = True
    memory_max_items: int = 100
    reflection_depth: int = 2


@dataclass
class ReportConfig:
    output_format: str = "pdf"
    output_dir: str = "./output"
    include_charts: bool = True
    chart_style: str = "seaborn-v0_8"
    language: str = "zh"
    font_family: str = "SimSun"


@dataclass
class DedupConfig:
    bert_threshold: float = 0.85
    minhash_threshold: float = 0.3
    max_news_items: int = 50


@dataclass
class Settings:
    llm: LLMConfig = field(default_factory=LLMConfig)
    agents: AgentConfig = field(default_factory=AgentConfig)
    cognitive: CognitiveConfig = field(default_factory=CognitiveConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    dedup: DedupConfig = field(default_factory=DedupConfig)


def _resolve_llm_from_env(llm: LLMConfig) -> LLMConfig:
    """
    用 .env 中的环境变量覆盖 LLM 配置。
    优先级: 环境变量 > yaml
    支持 provider: openai / anthropic / azure /
               grok / gemini / deepseek / kimi /
               glm / doubao / qwen / minimax / perplexity
    """
    provider = os.environ.get("LLM_PROVIDER", llm.provider).lower()
    llm.provider = provider

    # 每个 provider 对应的 env 变量名
    _key_map = {
        "openai":      ("OPENAI_API_KEY",      "OPENAI_MODEL",      ""),
        "anthropic":   ("ANTHROPIC_API_KEY",   "ANTHROPIC_MODEL",   ""),
        "azure":       ("AZURE_API_KEY",        "AZURE_MODEL",       ""),
        "grok":        ("GROK_API_KEY",         "GROK_MODEL",        "https://api.x.ai/v1"),
        "gemini":      ("GEMINI_API_KEY",       "GEMINI_MODEL",      "https://generativelanguage.googleapis.com/v1beta/openai/"),
        "deepseek":    ("DEEPSEEK_API_KEY",     "DEEPSEEK_MODEL",    "https://api.deepseek.com/v1"),
        "kimi":        ("KIMI_API_KEY",         "KIMI_MODEL",        "https://api.moonshot.cn/v1"),
        "glm":         ("GLM_API_KEY",          "GLM_MODEL",         "GLM_BASE_URL"),
        "doubao":      ("DOUBAO_API_KEY",       "DOUBAO_MODEL",      "DOUBAO_BASE_URL"),
        "qwen":        ("QWEN_API_KEY",         "QWEN_MODEL",        "QWEN_BASE_URL"),
        "minimax":     ("MINMAX_API_KEY",       "MINMAX_MODEL",      "MINMAX_BASE_URL"),
        "perplexity":  ("PERPLEXITY_API_KEY",   "PERPLEXITY_MODEL",  "https://api.perplexity.ai"),
    }

    if provider in _key_map:
        key_env, model_env, base_url_default = _key_map[provider]
        api_key = os.environ.get(key_env, llm.api_key)
        model = os.environ.get(model_env, llm.model)
        # base_url: 如果是 env 变量名则读取
        if base_url_default and base_url_default.isupper():
            base_url = os.environ.get(base_url_default, llm.base_url)
        else:
            base_url = llm.base_url or base_url_default

        llm.api_key = api_key
        llm.model = model
        llm.base_url = base_url

    return llm


def load_settings(config_path: Optional[str] = None) -> Settings:
    """加载配置文件，环境变量优先于 yaml"""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

    raw = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    else:
        print(f"[Warning] 配置文件 {config_path} 不存在，使用默认配置")

    settings = Settings()

    # LLM配置 (先从yaml读，再用env覆盖)
    if "llm" in raw:
        llm = raw["llm"]
        settings.llm = LLMConfig(
            provider=llm.get("provider", "openai"),
            model=llm.get("model", "gpt-4o"),
            api_key=llm.get("api_key", ""),
            base_url=llm.get("base_url", ""),
            temperature=llm.get("temperature", 0.1),
            max_tokens=llm.get("max_tokens", 4096),
            max_retries=llm.get("max_retries", 3),
            azure_api_version=llm.get("azure", {}).get("api_version", "2024-02-01"),
            azure_deployment=llm.get("azure", {}).get("deployment_name", ""),
        )
    # 环境变量覆盖
    settings.llm = _resolve_llm_from_env(settings.llm)

    # 智能体配置
    if "agents" in raw:
        a = raw["agents"]
        settings.agents = AgentConfig(
            max_rounds=a.get("max_rounds", 3),
            language=a.get("language", "zh"),
            parallel_analysis=a.get("parallel_analysis", True),
        )

    # 认知层配置
    if "cognitive" in raw:
        c = raw["cognitive"]
        settings.cognitive = CognitiveConfig(
            enable_reflection=c.get("enable_reflection", True),
            enable_planning=c.get("enable_planning", True),
            enable_memory=c.get("enable_memory", True),
            memory_max_items=c.get("memory_max_items", 100),
            reflection_depth=c.get("reflection_depth", 2),
        )

    # 报告配置
    if "report" in raw:
        r = raw["report"]
        settings.report = ReportConfig(
            output_format=r.get("output_format", "pdf"),
            output_dir=r.get("output_dir", "./output"),
            include_charts=r.get("include_charts", True),
            chart_style=r.get("chart_style", "seaborn-v0_8"),
            language=r.get("language", "zh"),
            font_family=r.get("font_family", "SimSun"),
        )

    # 去重配置
    if "dedup" in raw:
        d = raw["dedup"]
        settings.dedup = DedupConfig(
            bert_threshold=d.get("bert_threshold", 0.85),
            minhash_threshold=d.get("minhash_threshold", 0.3),
            max_news_items=d.get("max_news_items", 50),
        )

    return settings
