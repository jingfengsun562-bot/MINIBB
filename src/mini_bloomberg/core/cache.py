"""
Disk-backed cache decorator using diskcache.
Every data-layer function should be wrapped with @cached(ttl=86400).
"""

import functools
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import diskcache

_CACHE_DIR = Path(__file__).parent.parent.parent.parent / ".cache" / "mini_bloomberg"
_cache = diskcache.Cache(str(_CACHE_DIR))


def _make_key(fn: Callable, args: tuple, kwargs: dict) -> str:
    key_data = {
        "fn": f"{fn.__module__}.{fn.__qualname__}",
        "args": args,
        "kwargs": kwargs,
    }
    raw = json.dumps(key_data, default=str, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def cached(ttl: int = 86400):
    """Decorator that caches the return value to disk for `ttl` seconds."""
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            key = _make_key(fn, args, kwargs)
            result = _cache.get(key)
            if result is not None:
                return result
            result = fn(*args, **kwargs)
            _cache.set(key, result, expire=ttl)
            return result
        return wrapper
    return decorator


def clear_cache() -> None:
    _cache.clear()
