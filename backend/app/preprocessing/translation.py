"""Language detection + best-effort translation.

Detection uses `langdetect`. Translation delegates to the LLM (matches doc §4:
"Preprocessing: Glossary, language translation, spelling correction (OpenAI)").
When the LLM stub is active it becomes a pass-through, which is fine for the
demo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..llm import LLMClient, LLMResponse, token_info


@dataclass
class LanguageResult:
    original_language: str
    translated_text: str
    translation_needed: bool
    token_info_json: Optional[str] = None
    model: Optional[str] = None


_SYSTEM_TEMPLATE = (
    "You are a translation utility. Detect the language of the user text and, "
    "if it is not English, return an accurate English translation. "
    "Respond ONLY with the translated text — no preface, no explanation."
)


def detect_language(text: str) -> str:
    text = (text or "").strip()
    if not text:
        return "unknown"
    try:
        from langdetect import DetectorFactory, detect  # type: ignore

        DetectorFactory.seed = 0
        return detect(text)
    except Exception:  # noqa: BLE001
        return "en"


class Translator:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self.llm = llm or LLMClient()

    def to_english(self, text: str) -> LanguageResult:
        original = detect_language(text)
        if original == "en" or not text.strip():
            return LanguageResult(
                original_language=original,
                translated_text=text,
                translation_needed=False,
            )
        resp: LLMResponse = self.llm.chat(
            system=_SYSTEM_TEMPLATE,
            user=text,
            temperature=0.0,
            max_tokens=400,
        )
        return LanguageResult(
            original_language=original,
            translated_text=resp.content.strip() or text,
            translation_needed=True,
            token_info_json=token_info(resp),
            model=resp.model,
        )
