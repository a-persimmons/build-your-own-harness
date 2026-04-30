"""
Context management: token counting and window strategies.

Two strategies (Strategy pattern):
- SlidingWindow: drop oldest messages when over the token limit
- Summarizer:    compress oldest messages into a summary block via LLM call

Both implement ContextStrategy so AgentLoop can swap them without knowing the
difference (Open/Closed Principle).

Token counting uses tiktoken with cl100k_base (the GPT-4/Claude approximation).
Anthropic's usage field is authoritative at inference time — tiktoken gives a
fast pre-flight estimate so we can truncate before the API call.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import tiktoken

from harness_l01.providers import LLMClient, Message


# ---------------------------------------------------------------------------
# Token counting (pure functions — no IO)
# ---------------------------------------------------------------------------

_ENCODING = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_ENCODING.encode(text))


def count_message_tokens(messages: list[Message]) -> int:
    # 4 tokens overhead per message (role + separators) is the standard approximation
    return sum(4 + count_tokens(m.content) for m in messages)


@dataclass
class TokenUsage:
    messages: int
    system: int
    total: int

    @property
    def remaining(self) -> int:
        return max(0, 200_000 - self.total)  # Claude's max context


def measure_usage(messages: list[Message], system: str = "") -> TokenUsage:
    msg_tokens = count_message_tokens(messages)
    sys_tokens = count_tokens(system) if system else 0
    return TokenUsage(messages=msg_tokens, system=sys_tokens, total=msg_tokens + sys_tokens)


# ---------------------------------------------------------------------------
# Strategy interface (Strategy pattern)
# ---------------------------------------------------------------------------


class ContextStrategy(ABC):
    """Decides how to trim history when approaching the token limit."""

    @abstractmethod
    def apply(self, messages: list[Message], system: str, limit: int) -> list[Message]:
        """Return a (possibly trimmed) copy of messages that fits within limit tokens."""
        ...


# ---------------------------------------------------------------------------
# Strategy 1: Sliding Window
# ---------------------------------------------------------------------------


class SlidingWindow(ContextStrategy):
    """Drop oldest messages until the history fits within the token limit.

    Always preserves the most recent user message so the model has context
    for the current turn. Pairs of (user, assistant) are dropped together
    to avoid orphaned roles.
    """

    def apply(self, messages: list[Message], system: str, limit: int) -> list[Message]:
        if count_message_tokens(messages) + count_tokens(system) <= limit:
            return list(messages)

        result = list(messages)
        while len(result) > 1:
            usage = count_message_tokens(result) + count_tokens(system)
            if usage <= limit:
                break
            # Drop the oldest message; if it leaves an orphaned assistant turn, drop that too
            result.pop(0)
            if result and result[0].role == "assistant":
                result.pop(0)

        return result


# ---------------------------------------------------------------------------
# Strategy 2: Summarizer
# ---------------------------------------------------------------------------

_SUMMARIZE_SYSTEM = (
    "You are a conversation summarizer. "
    "Summarize the provided conversation history concisely, preserving key facts, "
    "decisions, and context. Output only the summary — no preamble."
)


class Summarizer(ContextStrategy):
    """Compress the oldest half of history into a summary block via an LLM call.

    The summary is injected as a synthetic user message at the start of the
    trimmed history so the model always has long-term context.
    """

    def __init__(self, client: LLMClient, summary_budget: int = 300) -> None:
        self._client = client
        self._summary_budget = summary_budget

    def apply(self, messages: list[Message], system: str, limit: int) -> list[Message]:
        if count_message_tokens(messages) + count_tokens(system) <= limit:
            return list(messages)

        midpoint = len(messages) // 2
        to_summarize = messages[:midpoint]
        to_keep = messages[midpoint:]

        conversation_text = "\n".join(
            f"{m.role.upper()}: {m.content}" for m in to_summarize
        )
        summary = "".join(
            self._client.stream(
                [Message(role="user", content=f"Summarize this conversation:\n\n{conversation_text}")],
                system=_SUMMARIZE_SYSTEM,
                max_tokens=self._summary_budget,
            )
        )

        summary_message = Message(
            role="user",
            content=f"[Earlier conversation summary]\n{summary}",
        )
        return [summary_message] + list(to_keep)


# ---------------------------------------------------------------------------
# Context manager — wraps a strategy with usage tracking
# ---------------------------------------------------------------------------


@dataclass
class ContextManager:
    """Applies a strategy and records token usage per turn."""

    strategy: ContextStrategy
    token_limit: int = 8_000
    usage_log: list[TokenUsage] = field(default_factory=list)

    def trim(self, messages: list[Message], system: str = "") -> list[Message]:
        trimmed = self.strategy.apply(messages, system, self.token_limit)
        usage = measure_usage(trimmed, system)
        self.usage_log.append(usage)
        return trimmed

    @property
    def last_usage(self) -> TokenUsage | None:
        return self.usage_log[-1] if self.usage_log else None
