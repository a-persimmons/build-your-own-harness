"""
Multi-provider LLM client.

Supports Anthropic natively and any OpenAI-compatible provider
(OpenRouter, OpenAI, Ollama, etc.) via the openai SDK.

Usage:
    client = get_client("anthropic")
    client = get_client("openrouter")
    client = get_client("openai")
"""

import os
from enum import Enum
from typing import Iterator

import anthropic
from openai import OpenAI
from pydantic import BaseModel


class Provider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OPENAI = "openai"


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class LLMClient:
    """Thin wrapper that normalises streaming across providers."""

    def __init__(self, provider: Provider, model: str):
        self.provider = provider
        self.model = model
        self._anthropic: anthropic.Anthropic | None = None
        self._openai: OpenAI | None = None

        if provider == Provider.ANTHROPIC:
            self._anthropic = anthropic.Anthropic(
                api_key=os.environ["ANTHROPIC_API_KEY"]
            )
        elif provider == Provider.OPENROUTER:
            self._openai = OpenAI(
                api_key=os.environ["OPENROUTER_API_KEY"],
                base_url="https://openrouter.ai/api/v1",
            )
        elif provider == Provider.OPENAI:
            self._openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def stream(
        self,
        messages: list[Message],
        system: str = "",
        max_tokens: int = 1024,
    ) -> Iterator[str]:
        """Yield text chunks as they arrive from the model."""
        if self.provider == Provider.ANTHROPIC:
            yield from self._stream_anthropic(messages, system, max_tokens)
        else:
            yield from self._stream_openai(messages, system, max_tokens)

    def _stream_anthropic(
        self, messages: list[Message], system: str, max_tokens: int
    ) -> Iterator[str]:
        assert self._anthropic is not None
        raw = [{"role": m.role, "content": m.content} for m in messages]
        kwargs: dict = {"model": self.model, "messages": raw, "max_tokens": max_tokens}
        if system:
            kwargs["system"] = system
        with self._anthropic.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text

    def _stream_openai(
        self, messages: list[Message], system: str, max_tokens: int
    ) -> Iterator[str]:
        assert self._openai is not None
        raw: list[dict] = []
        if system:
            raw.append({"role": "system", "content": system})
        raw.extend({"role": m.role, "content": m.content} for m in messages)
        stream = self._openai.chat.completions.create(
            model=self.model,
            messages=raw,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


# Default models per provider
DEFAULT_MODELS: dict[Provider, str] = {
    Provider.ANTHROPIC: "claude-sonnet-4-6",
    Provider.OPENROUTER: "anthropic/claude-sonnet-4-6",
    Provider.OPENAI: "gpt-4o",
}


def get_client(provider: str = "anthropic", model: str | None = None) -> LLMClient:
    p = Provider(provider)
    return LLMClient(provider=p, model=model or DEFAULT_MODELS[p])
