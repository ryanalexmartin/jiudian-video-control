"""Internationalization: simple JSON-based translation system."""
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_strings: dict[str, str] = {}
_current_lang: str = "zh_tw"
_i18n_dir = Path(__file__).parent
_listeners: list = []


def set_language(lang: str) -> None:
    """Switch language. Supported: 'zh_tw', 'en'."""
    global _strings, _current_lang
    path = _i18n_dir / f"{lang}.json"
    if not path.exists():
        logger.warning("Language file not found: %s", path)
        return
    _strings = json.loads(path.read_text(encoding="utf-8"))
    _current_lang = lang
    logger.info("Language set to: %s", lang)
    for cb in _listeners:
        try:
            cb()
        except Exception:
            logger.exception("Error in language change listener")


def get_language() -> str:
    """Return current language code."""
    return _current_lang


def t(key: str, **kwargs) -> str:
    """Translate a key, with optional {name} substitutions."""
    text = _strings.get(key, key)
    if kwargs:
        for k, v in kwargs.items():
            text = text.replace(f"{{{k}}}", str(v))
    return text


def on_language_change(callback) -> None:
    """Register a callback for language changes."""
    _listeners.append(callback)


# Load default language on import
set_language("zh_tw")
