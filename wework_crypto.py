"""Load WXBizJsonMsgCrypt directly from official weworkapi_python source tree."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


def _load_from_local_repo():
    """Load from ./weworkapi_python/callback_json_python3."""
    base = Path(__file__).resolve().parent
    callback_dir = base / "weworkapi_python" / "callback_json_python3"
    if not callback_dir.exists():
        raise ImportError(
            "Missing official source: weworkapi_python/callback_json_python3. "
            "Please clone https://github.com/sbzhu/weworkapi_python to ./weworkapi_python."
        )
    callback_path = str(callback_dir)
    if callback_path not in sys.path:
        sys.path.insert(0, callback_path)
    mod = importlib.import_module("WXBizJsonMsgCrypt")
    return mod.WXBizJsonMsgCrypt


def get_wxbiz_class():
    return _load_from_local_repo()

__all__ = ["get_wxbiz_class"]
