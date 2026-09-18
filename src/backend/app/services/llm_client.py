"""Thin Gemini wrapper. Reads GEMINI_API_KEY from env via python-dotenv."""
from __future__ import annotations

import os
import time
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

load_dotenv()

# ponytail: module-level client reuse; per-request clients would waste sockets
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not set")
        _client = genai.Client(api_key=api_key)
    return _client


def call_gemini(
    prompt: str,
    response_schema: type[BaseModel] | None = None,
    model: str = "gemini-3.6-flash",
) -> dict[str, Any]:
    """Call Gemini and return a plain dict.

    If response_schema is given, requests structured JSON output and
    validates it against that Pydantic model before returning .model_dump().
    Retries up to 2 times on transient errors (non-4xx).
    """
    client = _get_client()
    config: dict[str, Any] = {}
    if response_schema is not None:
        config["response_mime_type"] = "application/json"
        config["response_schema"] = response_schema

    last_exc: Exception | None = None
    for attempt in range(3):  # 1 try + 2 retries
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(**config) if config else None,
            )
            raw = response.text
            if response_schema is not None:
                try:
                    import json
                    return response_schema.model_validate(json.loads(raw)).model_dump()
                except (ValidationError, ValueError) as exc:
                    raise ValueError(
                        f"Gemini response did not match {response_schema.__name__}: {exc}\nRaw: {raw}"
                    ) from exc
            return {"text": raw}
        except Exception as exc:
            # Don't retry on explicit client errors (4xx); retry everything else
            msg = str(exc).lower()
            if any(code in msg for code in ("400", "401", "403", "404")):
                raise
            last_exc = exc
            if attempt < 2:
                time.sleep(1.5 ** attempt)  # ~0s, ~1.5s

    raise RuntimeError(f"Gemini call failed after 3 attempts: {last_exc}") from last_exc
