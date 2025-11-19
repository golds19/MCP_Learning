#!/usr/bin/env python3
"""
Server Configuration for Multi-Server ReAct Agent
Defines configuration for MCP servers.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class ServerConfig:
    """
    Configuration for an MCP server.

    Attributes:
        name: Unique identifier for the server (e.g., "sqlite", "google_calendar")
        command: Command to execute (e.g., "python", "npx", "node")
        args: Command arguments (e.g., ["server.py"] or ["@cocal/google-calendar-mcp"])
        env: Environment variables to pass to the server process
        description: Optional description of the server
    """
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    description: str = ""

    def __post_init__(self):
        """Validate configuration."""
        if not self.name:
            raise ValueError("Server name cannot be empty")
        if not self.command:
            raise ValueError("Server command cannot be empty")
        if not self.args:
            raise ValueError("Server args cannot be empty")


# Predefined server configurations
def create_sqlite_config(script_path: str) -> ServerConfig:
    """
    Create configuration for SQLite MCP server.

    Args:
        script_path: Path to sqlite_server.py

    Returns:
        ServerConfig for SQLite server
    """
    return ServerConfig(
        name="sqlite",
        command="python",
        args=[script_path],
        description="SQLite database CRUD operations"
    )


def create_google_calendar_config(credentials: Optional[str] = None) -> ServerConfig:
    """
    Create configuration for Google Calendar MCP server (nspady).

    Args:
        credentials: Google OAuth credentials JSON string or path

    Returns:
        ServerConfig for Google Calendar server
    """
    import os

    env = {}
    if credentials:
        # Check if it's a file path or JSON string
        if credentials.endswith('.json') and os.path.exists(credentials):
            env["GOOGLE_OAUTH_CREDENTIALS_PATH"] = credentials
        else:
            env["GOOGLE_OAUTH_CREDENTIALS"] = credentials
    else:
        # Try to get from environment
        if os.getenv("GOOGLE_OAUTH_CREDENTIALS"):
            env["GOOGLE_OAUTH_CREDENTIALS"] = os.getenv("GOOGLE_OAUTH_CREDENTIALS")
        elif os.getenv("GOOGLE_OAUTH_CREDENTIALS_PATH"):
            env["GOOGLE_OAUTH_CREDENTIALS_PATH"] = os.getenv("GOOGLE_OAUTH_CREDENTIALS_PATH")

    return ServerConfig(
        name="google_calendar",
        command="npx",
        args=["@cocal/google-calendar-mcp"],
        env=env if env else None,
        description="Google Calendar event management"
    )


# Example configurations
EXAMPLE_CONFIGS = {
    "sqlite": ServerConfig(
        name="sqlite",
        command="python",
        args=["../mcp_server/sqlite_server.py"],
        description="SQLite database operations"
    ),
    "google_calendar": ServerConfig(
        name="google_calendar",
        command="npx",
        args=["@cocal/google-calendar-mcp"],
        description="Google Calendar management"
    )
}
