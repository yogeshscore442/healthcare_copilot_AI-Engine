"""
cache.py — SHA-256 file-hash disk cache for LLM extraction results.
Keeps demo stable by avoiding redundant LLM calls for the same file.
Never raises externally.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_CACHE_DIR = Path.home() / ".health_copilot_cache"
_TTL_SECONDS = 86400  # 24 hours


def _disabled() -> bool:
    return os.getenv("DISABLE_CACHE", "false").lower() == "true"


def _cache_path(key: str) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{key}.json"


def get_file_hash(file_path: str) -> str:
    """Return hex SHA-256 of file contents."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def get_cached(file_path: str) -> Optional[dict]:
    """
    Return cached extraction result for *file_path*, or None on miss/expiry.
    Never raises.
    """
    if _disabled():
        return None
    try:
        key = get_file_hash(file_path)
        path = _cache_path(key)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - payload.get("_cached_at", 0) > _TTL_SECONDS:
            path.unlink(missing_ok=True)
            logger.debug("Cache expired for %s", key)
            return None
        logger.info("Cache HIT for %s", key[:12])
        return payload["data"]
    except Exception:
        logger.debug("Cache read failed — treating as miss", exc_info=True)
        return None


def set_cached(file_path: str, data: dict) -> None:
    """
    Store *data* in cache keyed by SHA-256 of *file_path*.
    Never raises.
    """
    if _disabled():
        return
    try:
        key = get_file_hash(file_path)
        path = _cache_path(key)
        payload = {"_cached_at": time.time(), "data": data}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Cache SET for %s", key[:12])
    except Exception:
        logger.debug("Cache write failed", exc_info=True)


def clear_cache() -> int:
    """Delete all cache entries. Returns count deleted."""
    count = 0
    try:
        for f in _CACHE_DIR.glob("*.json"):
            f.unlink()
            count += 1
    except Exception:
        pass
    return count
