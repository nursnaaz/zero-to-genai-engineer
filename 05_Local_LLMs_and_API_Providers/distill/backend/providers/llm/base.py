from __future__ import annotations
"""Base abstractions for all LLM providers.

Services only import from this module — never from specific provider implementations.
This is the boundary that makes provider-swapping a one-line config change.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMMessage:
    """A single message in a conversation."""
    role: str   # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    """The complete response from an LLM call."""
    content: str
    model: str
    provider: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class BaseLLMProvider(ABC):
    """All LLM providers implement this interface.

    The services layer only knows about this class — never about specific providers.
    Adding a new provider: create one file + add one elif in factory.py.
    """

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> LLMResponse:
        """Send a list of messages, return a complete (non-streaming) response."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider identifier (e.g. 'ollama', 'anthropic')."""

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier currently in use."""
