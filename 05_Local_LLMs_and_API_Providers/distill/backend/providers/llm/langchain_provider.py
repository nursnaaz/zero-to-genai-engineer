from __future__ import annotations
"""LangChain wrapper provider for Distill.

Wraps any LangChain-supported backend. The backend is chosen by
config.llm.langchain.backend (e.g. 'ollama', 'openai').
"""

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI

from .base import BaseLLMProvider, LLMMessage, LLMResponse
from core.config import AppConfig


class LangChainProvider(BaseLLMProvider):
    """Uses LangChain to call any supported backend."""

    def __init__(self, config: AppConfig):
        self._config = config
        backend = config.llm.langchain.backend.lower()
        self._model_name = config.llm.model

        if backend == "ollama":
            self._chain = ChatOllama(
                model=self._model_name,
                base_url=config.llm.ollama.base_url,
                temperature=config.llm.temperature,
            )
        elif backend == "openai":
            self._chain = ChatOpenAI(
                model=self._model_name,
                temperature=config.llm.temperature,
                openai_api_key=config.llm.api_key or "",
            )
        else:
            raise ValueError(f"LangChainProvider: unsupported backend '{backend}'")

        self._backend = backend

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> LLMResponse:
        lc_messages = []
        for m in messages:
            if m.role == "system":
                lc_messages.append(SystemMessage(content=m.content))
            elif m.role == "user":
                lc_messages.append(HumanMessage(content=m.content))
            elif m.role == "assistant":
                lc_messages.append(AIMessage(content=m.content))

        resp = await self._chain.ainvoke(lc_messages)
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        return LLMResponse(
            content=content,
            model=self._model_name,
            provider=f"langchain:{self._backend}",
        )

    def get_provider_name(self) -> str:
        return f"langchain:{self._backend}"

    def get_model_name(self) -> str:
        return self._model_name
