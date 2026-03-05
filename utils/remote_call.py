"""
远程调用统一封装 - 超时控制 + 日志记录

功能:
1. 全局 requests 默认超时（覆盖 akshare/tushare 内部调用）
2. timed_api_call() 包装器：记录调用参数、耗时、结果大小
3. 线程级超时强制（兼容 Windows）
"""
import time
import logging
import concurrent.futures
from typing import Callable, Any, Optional

import requests

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------
# 全局 requests 默认超时（单位: 秒）
# 覆盖 akshare / tushare 等库内部的 requests 调用
# ----------------------------------------------------------------
_DATA_CONNECT_TIMEOUT = 10   # TCP 连接超时
_DATA_READ_TIMEOUT = 30      # 数据读取超时
_DATA_TIMEOUT = (_DATA_CONNECT_TIMEOUT, _DATA_READ_TIMEOUT)

_original_request = requests.Session.request


def _patched_request(self, method, url, **kwargs):
    """为所有 requests 调用注入默认超时"""
    kwargs.setdefault("timeout", _DATA_TIMEOUT)
    return _original_request(self, method, url, **kwargs)


requests.Session.request = _patched_request
logger.debug("[remote_call] requests 全局超时已设置: connect=%ss, read=%ss",
             _DATA_CONNECT_TIMEOUT, _DATA_READ_TIMEOUT)

# ----------------------------------------------------------------
# timed_api_call — 带日志 + 线程级超时的远程调用包装器
# ----------------------------------------------------------------
_CALL_TIMEOUT = 45  # 单次外层超时（秒），留出重试余量


def timed_api_call(
    fn: Callable,
    *args,
    call_name: str = "",
    timeout: int = _CALL_TIMEOUT,
    retries: int = 3,
    retry_interval: float = 10.0,
    log: Optional[logging.Logger] = None,
    **kwargs,
) -> Any:
    """
    带超时控制、重试和日志记录的远程 API 调用包装器。

    Args:
        fn:             要调用的函数
        *args:          位置参数
        call_name:      日志中显示的调用名称（默认取 fn.__name__）
        timeout:        单次调用的线程级超时秒数（默认 45s）
        retries:        超时/失败后的最大重试次数（默认 3）
        retry_interval: 每次重试前的等待秒数（默认 10s）
        log:            logger 实例（默认模块级 logger）
        **kwargs:       关键字参数
    Returns:
        fn 的返回值
    Raises:
        最后一次尝试仍失败时抛出对应异常
    """
    _log = log or logger
    name = call_name or getattr(fn, "__name__", str(fn))
    kw_str = _fmt_kwargs(kwargs)
    last_exc: Exception = RuntimeError("未执行")

    for attempt in range(1, retries + 1):
        _log.info("[REMOTE→] %s  %s  (第%d/%d次)", name, kw_str, attempt, retries)
        start = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fn, *args, **kwargs)
            try:
                result = future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                elapsed = time.time() - start
                _log.warning(
                    "[REMOTE✗] %s  超时 %.1fs (限制%ss)  第%d/%d次",
                    name, elapsed, timeout, attempt, retries,
                )
                last_exc = TimeoutError(f"[{name}] 超时 ({timeout}s)")
            except Exception as exc:
                elapsed = time.time() - start
                _log.warning(
                    "[REMOTE✗] %s  错误: %s  耗时%.1fs  第%d/%d次",
                    name, exc, elapsed, attempt, retries,
                )
                last_exc = exc
            else:
                elapsed = time.time() - start
                _log.info("[REMOTE✓] %s  耗时%.1fs  %s", name, elapsed, _fmt_result(result))
                return result

        if attempt < retries:
            _log.info("[REMOTE↺] %s  %.0fs后重试…", name, retry_interval)
            time.sleep(retry_interval)

    _log.error("[REMOTE✗] %s  已重试%d次，全部失败: %s", name, retries, last_exc)
    raise last_exc


# ----------------------------------------------------------------
# 内部工具
# ----------------------------------------------------------------

def _fmt_kwargs(kwargs: dict) -> str:
    """格式化 kwargs 用于日志，截断过长字符串"""
    parts = []
    for k, v in kwargs.items():
        if isinstance(v, str) and len(v) > 40:
            parts.append(f"{k}='{v[:30]}…'")
        else:
            parts.append(f"{k}={v!r}")
    return "  ".join(parts) if parts else ""


def _fmt_result(result) -> str:
    """格式化返回值大小用于日志"""
    try:
        import pandas as pd
        if isinstance(result, pd.DataFrame):
            return f"rows={len(result)}"
    except ImportError:
        pass
    if isinstance(result, (list, tuple)):
        return f"len={len(result)}"
    if isinstance(result, dict):
        return f"keys={len(result)}"
    return ""
