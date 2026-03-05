"""
LLM统一接口 - 支持多种Provider
融合FinRpt的robust_prompt和Cogito的认知提示机制

支持: openai / anthropic / azure / grok / gemini / deepseek /
      kimi / glm / doubao / qwen / minimax / perplexity
"""
import json
import os
import time
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# 需要走代理的 provider（境外服务）
_PROXY_REQUIRED_PROVIDERS = {"openai", "anthropic", "azure", "grok", "gemini", "perplexity"}

# Provider默认配置 (base_url, 从env读取的api_key变量名, 从env读取的model变量名)
_PROVIDER_DEFAULTS = {
    "grok": {
        "base_url": "https://api.x.ai/v1",
        "api_key_env": "GROK_API_KEY",
        "model_env": "GROK_MODEL",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key_env": "GEMINI_API_KEY",
        "model_env": "GEMINI_MODEL",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model_env": "DEEPSEEK_MODEL",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "api_key_env": "KIMI_API_KEY",
        "model_env": "KIMI_MODEL",
    },
    "glm": {
        "base_url_env": "GLM_BASE_URL",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
        "api_key_env": "GLM_API_KEY",
        "model_env": "GLM_MODEL",
    },
    "doubao": {
        "base_url_env": "DOUBAO_BASE_URL",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        "api_key_env": "DOUBAO_API_KEY",
        "model_env": "DOUBAO_MODEL",
    },
    "qwen": {
        "base_url_env": "QWEN_BASE_URL",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        "api_key_env": "QWEN_API_KEY",
        "model_env": "QWEN_MODEL",
    },
    "minimax": {
        "base_url_env": "MINMAX_BASE_URL",
        "base_url": "https://api.minimax.chat/v1/text/chatcompletion_v2",
        "api_key_env": "MINMAX_API_KEY",
        "model_env": "MINMAX_MODEL",
    },
    "perplexity": {
        "base_url": "https://api.perplexity.ai",
        "api_key_env": "PERPLEXITY_API_KEY",
        "model_env": "PERPLEXITY_MODEL",
    },
}


class LLMClient:
    """统一的LLM调用客户端"""

    def __init__(self, config):
        self.config = config
        self.provider = config.provider
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.max_retries = config.max_retries
        self._client = None
        self._init_client()

    def _init_client(self):
        """初始化对应的LLM客户端"""
        provider = self.provider

        if provider == "anthropic":
            from anthropic import Anthropic
            self._client = Anthropic(api_key=self.config.api_key)
            return

        if provider == "azure":
            from openai import AzureOpenAI
            self._client = AzureOpenAI(
                api_key=self.config.api_key,
                api_version=self.config.azure_api_version,
                azure_endpoint=self.config.base_url,
            )
            return

        # OpenAI 及所有兼容 OpenAI 接口的 provider
        from openai import OpenAI

        api_key = self.config.api_key
        base_url = self.config.base_url

        # 从 Provider 默认配置补充 base_url / api_key
        if provider in _PROVIDER_DEFAULTS:
            defaults = _PROVIDER_DEFAULTS[provider]
            if not base_url:
                base_url = os.environ.get(
                    defaults.get("base_url_env", ""),
                    defaults.get("base_url", ""),
                )
            if not api_key:
                api_key = os.environ.get(defaults.get("api_key_env", ""), "")
            if not self.model:
                self.model = os.environ.get(defaults.get("model_env", ""), "")
        elif provider != "openai":
            logger.warning(f"未知 provider '{provider}'，尝试作为 OpenAI 兼容接口处理")

        kwargs: Dict[str, Any] = {"api_key": api_key or "placeholder"}
        if base_url:
            # GLM/Doubao/Qwen 的 base_url 包含完整路径，需要截断到根路径
            # OpenAI SDK 只需要到 /v1 这一级
            if base_url.endswith("/chat/completions"):
                base_url = base_url.rsplit("/chat/completions", 1)[0]
            kwargs["base_url"] = base_url

        # 只有境外服务才走代理，国产大模型直连
        if provider in _PROXY_REQUIRED_PROVIDERS:
            proxy = os.environ.get("LLM_PROXY", "")
            if proxy:
                import httpx
                kwargs["http_client"] = httpx.Client(proxies=proxy)
                logger.info(f"[LLMClient] 使用代理: {proxy}")

        self._client = OpenAI(**kwargs)
        logger.info(f"[LLMClient] Provider={provider}, Model={self.model}, BaseURL={base_url or 'default'}")

    def prompt(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[str] = None,
    ) -> str:
        """
        发送消息并获取回复

        Args:
            messages: 消息列表 [{"role": "system"|"user"|"assistant", "content": "..."}]
            temperature: 覆盖默认温度
            max_tokens: 覆盖默认max_tokens
            response_format: "json" 则要求JSON输出
        Returns:
            回复文本
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        if self.provider == "anthropic":
            return self._prompt_anthropic(messages, temp, tokens, response_format)
        else:
            return self._prompt_openai(messages, temp, tokens, response_format)

    # 确认支持 json_object response_format 的 provider
    _JSON_FORMAT_PROVIDERS = {"openai", "azure", "deepseek", "doubao"}

    def _prompt_openai(self, messages, temperature, max_tokens, response_format):
        """OpenAI / Azure / 兼容接口 调用"""
        kwargs = {
            "model": self.config.azure_deployment or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format == "json" and self.provider in self._JSON_FORMAT_PROVIDERS:
            kwargs["response_format"] = {"type": "json_object"}

        resp = self._client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content
        if not content:
            finish = resp.choices[0].finish_reason
            logger.warning(f"[LLMClient] {self.provider} 返回空内容, finish_reason={finish}")
            raise ValueError(f"LLM返回空内容 (finish_reason={finish})")
        return content

    def _prompt_anthropic(self, messages, temperature, max_tokens, response_format):
        """Anthropic Claude 调用"""
        system_msg = ""
        chat_messages = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                chat_messages.append(m)

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": chat_messages,
        }
        if system_msg:
            kwargs["system"] = system_msg

        resp = self._client.messages.create(**kwargs)
        return resp.content[0].text

    def simple_prompt(self, user_message: str, system_message: str = "") -> str:
        """简单的单轮对话"""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_message})
        return self.prompt(messages)

    def json_prompt(self, user_message: str, system_message: str = "") -> Dict[str, Any]:
        """
        获取JSON格式回复，带重试解析逻辑 (源自FinRpt)
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_message})

        for attempt in range(self.max_retries):
            try:
                raw = self.prompt(messages, response_format="json")
                return self._parse_json(raw)
            except Exception as e:
                logger.warning(f"JSON解析失败 (尝试 {attempt+1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    return {"error": str(e), "raw": raw if 'raw' in dir() else ""}
                time.sleep(1)

    def robust_prompt(
        self,
        messages: List[Dict[str, str]],
        retries: Optional[int] = None,
        response_format: Optional[str] = None,
    ) -> str:
        """
        带重试的健壮调用 (源自FinRpt的robust_prompt)
        """
        max_r = retries or self.max_retries
        last_error = None
        for attempt in range(max_r):
            try:
                return self.prompt(messages, response_format=response_format)
            except Exception as e:
                last_error = e
                logger.warning(f"LLM调用失败 (尝试 {attempt+1}/{max_r}): {e}")
                time.sleep(2 ** attempt)  # 指数退避
        raise RuntimeError(f"LLM调用在{max_r}次重试后仍然失败: {last_error}")

    @staticmethod
    def _clean_json_text(text: str) -> str:
        """清理LLM输出中常见的JSON格式问题"""
        import re
        # 替换中文/智能引号为ASCII引号
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        # 移除尾随逗号 (trailing comma): ,} 或 ,]
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        # 修复字符串值内的未转义控制字符（换行/制表符）
        text = LLMClient._escape_control_chars_in_strings(text)
        return text

    @staticmethod
    def _escape_control_chars_in_strings(text: str) -> str:
        """将JSON字符串值内的未转义换行/制表符转换为合法的转义序列"""
        result = []
        in_string = False
        escape_next = False
        for ch in text:
            if escape_next:
                result.append(ch)
                escape_next = False
            elif ch == '\\' and in_string:
                result.append(ch)
                escape_next = True
            elif ch == '"':
                result.append(ch)
                in_string = not in_string
            elif in_string and ch in '\n\r\t':
                result.append('\\n' if ch == '\n' else '\\r' if ch == '\r' else '\\t')
            else:
                result.append(ch)
        return ''.join(result)

    @staticmethod
    def _parse_json(text: str) -> Dict[str, Any]:
        """健壮的JSON解析，处理markdown代码块等"""
        import re
        text = text.strip()
        # 移除markdown代码块标记
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # 清理常见JSON问题（智能引号、尾随逗号）
        cleaned = LLMClient._clean_json_text(text)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as first_err:
            # 尝试找到第一个 { 和最后一个 }
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(cleaned[start:end])
                except json.JSONDecodeError:
                    pass
            # 尝试找数组
            start = cleaned.find("[")
            end = cleaned.rfind("]") + 1
            if start != -1 and end > start:
                try:
                    return {"items": json.loads(cleaned[start:end])}
                except json.JSONDecodeError:
                    pass
            # 使用 json_repair 库修复更复杂的JSON格式问题（如非转义引号）
            try:
                from json_repair import repair_json
                repaired = repair_json(cleaned, return_objects=True)
                if isinstance(repaired, dict) and repaired:
                    logger.debug(f"[LLMClient] json_repair修复成功")
                    return repaired
            except Exception:
                pass
            # 记录无法解析的原始内容（便于诊断）
            logger.debug(f"[LLMClient] JSON解析失败，原始内容(前200字): {cleaned[:200]!r}")
            raise first_err
