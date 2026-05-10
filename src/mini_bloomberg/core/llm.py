"""
Singleton Anthropic client — one instance for the lifetime of the process.
Import _get_client() from here instead of instantiating anthropic.Anthropic() directly.
"""

import anthropic
from mini_bloomberg.config import get_settings

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key)
    return _client
