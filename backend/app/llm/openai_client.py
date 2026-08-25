"""OpenRouter chat client with a deterministic offline stub."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings


@dataclass
class LLMResponse:
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    finish_reason: str
    raw: dict[str, Any]


class LLMClient:
    """Thin OpenAI-SDK wrapper pointed at OpenRouter."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None
        if self.settings.has_llm_key:
            # Lazy import so tests / offline installs don't require openai at import time.
            from openai import OpenAI  # type: ignore

            self._client = OpenAI(
                base_url=self.settings.openrouter_base_url,
                api_key=self.settings.openrouter_api_key,
                default_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Vartalaap Dummy Chatbot",
                },
            )

    # ------------------------------------------------------------------
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, min=0.5, max=4.0),
        reraise=True,
    )
    def chat(
        self,
        *,
        system: str,
        user: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[dict[str, Any]] = None,
    ) -> LLMResponse:
        model = model or self.settings.llm_model
        temperature = temperature if temperature is not None else self.settings.llm_temperature
        max_tokens = max_tokens or self.settings.llm_max_tokens

        if not self._client:
            return _stub_response(system=system, user=user, model=model)

        try:
            resp = self._client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                response_format=response_format or None,
            )
        except Exception:  # noqa: BLE001 — fall back rather than crash the demo
            if model != self.settings.llm_fallback_model:
                resp = self._client.chat.completions.create(
                    model=self.settings.llm_fallback_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    response_format=response_format or None,
                )
            else:
                raise

        choice = resp.choices[0]
        usage = resp.usage
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
            total_tokens=getattr(usage, "total_tokens", 0) or 0,
            finish_reason=choice.finish_reason or "stop",
            raw=resp.model_dump() if hasattr(resp, "model_dump") else {},
        )


# ----------------------------------------------------------------------
def _stub_response(*, system: str, user: str, model: str) -> LLMResponse:
    """Deterministic fake used when no OpenRouter key is configured.

    Keeps every downstream stage runnable so observability plumbing can be
    exercised end-to-end without network access.
    """
    digest = hashlib.sha1((system + "\n---\n" + user).encode("utf-8")).hexdigest()[:8]
    answer = (
        "[offline-stub] "
        + user.strip().split("\n")[0][:180]
        + f" (hash={digest})"
    )
    payload = {
        "id": f"stub-{digest}",
        "model": model,
        "choices": [
            {"message": {"role": "assistant", "content": answer}, "finish_reason": "stop"}
        ],
        "usage": {
            "prompt_tokens": len(system) + len(user),
            "completion_tokens": len(answer),
            "total_tokens": len(system) + len(user) + len(answer),
        },
    }
    return LLMResponse(
        content=answer,
        model=model,
        prompt_tokens=payload["usage"]["prompt_tokens"],
        completion_tokens=payload["usage"]["completion_tokens"],
        total_tokens=payload["usage"]["total_tokens"],
        finish_reason="stop",
        raw=payload,
    )


# Handy for schema fields expecting a string blob
def token_info(resp: LLMResponse) -> str:
    return json.dumps(
        {
            "model": resp.model,
            "prompt_tokens": resp.prompt_tokens,
            "completion_tokens": resp.completion_tokens,
            "total_tokens": resp.total_tokens,
        }
    )
