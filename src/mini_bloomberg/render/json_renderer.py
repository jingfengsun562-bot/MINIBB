"""
JSON renderer for LLM consumption.
Strips None values and trims verbose fields to keep token count low.
"""

import json
from typing import Any


_TRIM_FIELDS = {"long_description", "business_address", "mailing_address"}
_DESC_MAX_LEN = 200


def to_json(result: dict, indent: int | None = None) -> str:
    """Serialize a function result dict to JSON, stripping Nones and trimming."""
    return json.dumps(_clean(result), indent=indent, default=str)


def _clean(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if v is None:
                continue
            if k in _TRIM_FIELDS and isinstance(v, str) and len(v) > _DESC_MAX_LEN:
                out[k] = v[:_DESC_MAX_LEN] + "…"
            else:
                out[k] = _clean(v)
        return out
    if isinstance(obj, list):
        return [_clean(item) for item in obj]
    return obj
