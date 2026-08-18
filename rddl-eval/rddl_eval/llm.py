"""Client for a local LM Studio server (OpenAI-compatible, no auth).

No retries on purpose: a flaky connection should stop the run loudly rather
than quietly turn into a failed generation in the statistics.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import requests

DEFAULT_ENDPOINT = "http://localhost:1234/v1/chat/completions"
DEFAULT_MODEL = "google/gemma-4-12b-qat"
#: A 12B model over a 32k-token context is slow; this has to be generous.
DEFAULT_TIMEOUT = 900


def default_endpoint() -> str:
    return os.environ.get("LMSTUDIO_URL", DEFAULT_ENDPOINT)


class LLMError(RuntimeError):
    pass


@dataclass
class LMStudioClient:
    endpoint: str = ""
    model: str = DEFAULT_MODEL
    timeout: int = DEFAULT_TIMEOUT
    temperature: float = 0.7
    max_tokens: int = -1

    def __post_init__(self) -> None:
        self.endpoint = self.endpoint or default_endpoint()

    def complete(self, messages: list[dict], temperature: float | None = None) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature if temperature is None else temperature,
            "stream": False,
        }
        if self.max_tokens > 0:
            payload["max_tokens"] = self.max_tokens

        try:
            response = requests.post(self.endpoint, json=payload, timeout=self.timeout)
        except requests.exceptions.ConnectionError as exc:
            raise LLMError(
                f"LM Studio is not reachable at {self.endpoint} -- check that the "
                f"server is started and shows Status: Running, and that the address "
                f"matches --endpoint / $LMSTUDIO_URL. ({exc.__class__.__name__})"
            ) from exc
        except requests.exceptions.ReadTimeout as exc:
            raise LLMError(
                f"LM Studio did not answer within {self.timeout}s at {self.endpoint}. "
                f"Raise the timeout or use a smaller context."
            ) from exc

        if response.status_code != 200:
            raise LLMError(
                f"LM Studio returned HTTP {response.status_code} at {self.endpoint}: "
                f"{response.text[:500]}"
            )

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError) as exc:
            raise LLMError(
                f"Could not read a completion out of the LM Studio response: "
                f"{response.text[:500]}"
            ) from exc
