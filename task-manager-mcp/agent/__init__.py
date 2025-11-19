"""
ReAct Agent for MCP Servers

A Reasoning + Acting agent that can interact with multiple MCP servers
including SQLite databases and Google Calendar through the Model Context Protocol (MCP).
"""

from .react_agent import ReActAgent, AgentState, Step
from .multi_server_agent import MultiServerReActAgent
from .server_config import ServerConfig, create_sqlite_config, create_google_calendar_config
from .llm_integration import (
    LLMProvider,
    OpenAIProvider,
    OllamaProvider,
    MockLLMProvider,
    create_llm_provider,
    llm_callback_factory
)

__version__ = "2.0.0"
__all__ = [
    # Core agent classes
    "ReActAgent",
    "MultiServerReActAgent",
    "AgentState",
    "Step",
    # Server configuration
    "ServerConfig",
    "create_sqlite_config",
    "create_google_calendar_config",
    # LLM providers
    "LLMProvider",
    "OpenAIProvider",
    "OllamaProvider",
    "MockLLMProvider",
    "create_llm_provider",
    "llm_callback_factory"
]
