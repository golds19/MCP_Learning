#!/usr/bin/env python3
"""
LLM Integration for ReAct Agent
Provides interfaces to different LLM providers (OpenAI, Anthropic, Ollama, etc.)
"""

import os
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-5-nano"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that follows the ReAct (Reasoning + Acting) format. Always respond with Thought, Action, and Action Input."},
                {"role": "user", "content": prompt}
            ],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 500)
        )
        return response.choices[0].message.content


# class AnthropicProvider(LLMProvider):
#     """Anthropic Claude provider."""

#     def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
#         """
#         Initialize Anthropic provider.

#         Args:
#             api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
#             model: Model to use (default: claude-3-5-sonnet)
#         """
#         self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
#         self.model = model

#         if not self.api_key:
#             raise ValueError("Anthropic API key not provided")

#         try:
#             from anthropic import AsyncAnthropic
#             self.client = AsyncAnthropic(api_key=self.api_key)
#         except ImportError:
#             raise ImportError("anthropic package not installed. Install with: pip install anthropic")

#     async def generate(self, prompt: str, **kwargs) -> str:
#         """Generate response using Anthropic API."""
#         response = await self.client.messages.create(
#             model=self.model,
#             max_tokens=kwargs.get("max_tokens", 1024),
#             messages=[
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=kwargs.get("temperature", 0.7),
#         )
#         return response.content[0].text


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama provider.

        Args:
            model: Model to use (default: llama2)
            base_url: Ollama server URL
        """
        self.model = model
        self.base_url = base_url

        try:
            import httpx
            self.client = httpx.AsyncClient()
        except ImportError:
            raise ImportError("httpx package not installed. Install with: pip install httpx")

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using Ollama API."""
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": kwargs.get("temperature", 0.7),
            }
        )
        response.raise_for_status()
        return response.json()["response"]


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing (returns predefined responses)."""

    def __init__(self):
        """Initialize mock provider."""
        self.call_count = 0
        self.responses = []

    def add_response(self, response: str):
        """Add a predefined response."""
        self.responses.append(response)

    async def generate(self, prompt: str, **kwargs) -> str:
        """Return next predefined response."""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        else:
            # Default response if no more predefined ones
            return """Thought: I have completed all predefined actions.
Action: FINISH
Action Input: {}"""


def create_llm_provider(provider_type: str, **kwargs) -> LLMProvider:
    """
    Factory function to create LLM providers.

    Args:
        provider_type: Type of provider ("openai", "anthropic", "ollama", "mock")
        **kwargs: Provider-specific arguments

    Returns:
        LLMProvider instance
    """
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        "mock": MockLLMProvider,
    }

    if provider_type.lower() not in providers:
        raise ValueError(f"Unknown provider type: {provider_type}. Available: {list(providers.keys())}")

    return providers[provider_type.lower()](**kwargs)


# Convenience function for agent integration
async def llm_callback_factory(provider_type: str, **provider_kwargs):
    """
    Create an LLM callback function for use with ReActAgent.

    Args:
        provider_type: Type of LLM provider
        **provider_kwargs: Provider-specific arguments

    Returns:
        Async callback function
    """
    provider = create_llm_provider(provider_type, **provider_kwargs)

    async def callback(prompt: str) -> str:
        return await provider.generate(prompt)

    return callback
