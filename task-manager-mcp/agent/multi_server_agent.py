#!/usr/bin/env python3
"""
Multi-Server ReAct Agent
Extends ReActAgent to support multiple MCP servers simultaneously.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .react_agent import ReActAgent, AgentState, Step
from .server_config import ServerConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("multi-server-agent")


class MultiServerReActAgent(ReActAgent):
    """
    Enhanced ReAct agent that can connect to multiple MCP servers.

    This agent maintains multiple simultaneous MCP sessions and routes
    tool calls to the appropriate server based on tool names.
    """

    def __init__(
        self,
        server_configs: List[ServerConfig],
        max_iterations: int = 10,
        verbose: bool = True
    ):
        """
        Initialize the multi-server ReAct agent.

        Args:
            server_configs: List of server configurations
            max_iterations: Maximum number of reasoning-acting iterations
            verbose: Whether to print detailed execution steps
        """
        # Don't call parent __init__ since we're overriding session management
        self.server_configs = server_configs
        self.max_iterations = max_iterations
        self.verbose = verbose

        # Multi-server management
        self.sessions: Dict[str, ClientSession] = {}
        self.all_tools: Dict[str, str] = {}  # tool_name -> server_name mapping
        self.server_tools: Dict[str, List[Any]] = {}  # server_name -> list of tools

        # Track execution
        self.steps: List[Step] = []

        # Context managers for cleanup
        self._stdio_contexts = {}
        self._session_contexts = {}

    async def initialize_sessions(self):
        """Initialize connections to all MCP servers."""
        if self.verbose:
            print(f"🔗 Connecting to {len(self.server_configs)} MCP servers...")
            print()

        for config in self.server_configs:
            try:
                if self.verbose:
                    print(f"  ➤ Connecting to '{config.name}' server...")
                    print(f"    Command: {config.command} {' '.join(config.args)}")

                # Create server parameters
                server_params = StdioServerParameters(
                    command=config.command,
                    args=config.args,
                    env=config.env
                )

                # Establish stdio connection
                stdio_context = stdio_client(server_params)
                read, write = await stdio_context.__aenter__()
                self._stdio_contexts[config.name] = stdio_context

                # Create MCP session
                session_context = ClientSession(read, write)
                session = await session_context.__aenter__()
                self._session_contexts[config.name] = session_context
                self.sessions[config.name] = session

                # Initialize and get tools
                await session.initialize()
                tools_response = await session.list_tools()
                self.server_tools[config.name] = tools_response.tools

                # Map tool names to server names
                for tool in tools_response.tools:
                    self.all_tools[tool.name] = config.name

                if self.verbose:
                    print(f"    ✓ Connected! Found {len(tools_response.tools)} tools:")
                    for tool in tools_response.tools:
                        print(f"      • {tool.name}")
                    print()

            except Exception as e:
                logger.error(f"Failed to connect to {config.name} server: {e}")
                if self.verbose:
                    print(f"    ✗ Connection failed: {e}")
                    print()
                raise

        if self.verbose:
            print(f"✓ All servers connected successfully!")
            print(f"✓ Total tools available: {len(self.all_tools)}")
            print()

    async def cleanup_sessions(self):
        """Clean up all MCP sessions."""
        if self.verbose:
            print("\n🔌 Cleaning up server connections...")

        for name, session_context in self._session_contexts.items():
            try:
                await session_context.__aexit__(None, None, None)
                if self.verbose:
                    print(f"  ✓ Closed session: {name}")
            except Exception as e:
                logger.error(f"Error closing session {name}: {e}")

        for name, stdio_context in self._stdio_contexts.items():
            try:
                await stdio_context.__aexit__(None, None, None)
                if self.verbose:
                    print(f"  ✓ Closed connection: {name}")
            except Exception as e:
                logger.error(f"Error closing stdio {name}: {e}")

    def _get_tool_descriptions(self) -> str:
        """Get formatted descriptions of available tools from all servers."""
        descriptions = []
        for server_name, tools in self.server_tools.items():
            descriptions.append(f"\n[{server_name.upper()} SERVER]")
            for tool in tools:
                descriptions.append(f"  - {tool.name}: {tool.description}")
        return "\n".join(descriptions)

    def _route_tool_to_server(self, tool_name: str) -> Optional[str]:
        """
        Determine which server to use for a given tool.

        Args:
            tool_name: Name of the tool to execute

        Returns:
            Server name or None if tool not found
        """
        return self.all_tools.get(tool_name)

    async def _execute_action(self, action: str, action_input: Dict[str, Any]) -> str:
        """
        Execute an action using the appropriate MCP server.

        Args:
            action: Tool name
            action_input: Tool arguments

        Returns:
            Tool execution result as string
        """
        # Route to correct server
        server_name = self._route_tool_to_server(action)

        if not server_name:
            available_tools = ", ".join(self.all_tools.keys())
            return f"Error: Unknown tool '{action}'. Available tools: {available_tools}"

        # Get the session for this server
        session = self.sessions.get(server_name)
        if not session:
            return f"Error: No active session for server '{server_name}'"

        # Execute the tool
        try:
            if self.verbose:
                print(f"    [Executing on {server_name} server]")

            result = await session.call_tool(action, arguments=action_input)
            return result.content[0].text

        except Exception as e:
            error_msg = f"Error executing {action} on {server_name}: {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def run(self, task: str, llm_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Run the multi-server ReAct agent to complete a task.

        Args:
            task: The task to complete
            llm_callback: Optional async function that takes a prompt and returns LLM response

        Returns:
            Dictionary with execution results and steps taken
        """
        # Initialize all server sessions
        await self.initialize_sessions()

        if self.verbose:
            print("=" * 70)
            print(f"TASK: {task}")
            print("=" * 70)
            print()

        context = f"Available servers: {', '.join(self.sessions.keys())}"
        context += f"\nTotal tools: {len(self.all_tools)}"

        try:
            for iteration in range(self.max_iterations):
                if self.verbose:
                    print(f"--- Iteration {iteration + 1} ---")

                # REASONING PHASE
                prompt = self._reason(task, context)

                if llm_callback:
                    # Use LLM to generate response
                    response = await llm_callback(prompt)
                else:
                    # Manual mode - print prompt and get user input
                    if self.verbose:
                        print("\n[PROMPT FOR LLM]:")
                        print(prompt)
                        print("\n[Please provide LLM response in format: Thought/Action/Action Input]")
                        print("Or type 'AUTO' for automatic demo mode\n")

                    response = input("Response: ").strip()

                    # Demo mode with pre-defined actions
                    if response.upper() == "AUTO":
                        response = self._auto_generate_response(task, iteration)

                # Parse response
                thought, action, action_input = self._parse_thought_action(response)

                if self.verbose:
                    print(f"\nThought: {thought}")

                # Check if task is complete
                if action and action.upper() == "FINISH" or self._is_task_complete(thought):
                    step = Step(
                        thought=thought,
                        state=AgentState.FINISHED
                    )
                    self.steps.append(step)

                    if self.verbose:
                        print(f"\n✓ Task completed in {iteration + 1} iterations!")
                    break

                # ACTING PHASE
                if action and action_input:
                    if self.verbose:
                        print(f"Action: {action}")
                        print(f"Action Input: {json.dumps(action_input, indent=2)}")

                    # Execute action on the appropriate server
                    observation = await self._execute_action(action, action_input)

                    if self.verbose:
                        print(f"Observation: {observation}")
                        print()

                    step = Step(
                        thought=thought,
                        action=action,
                        action_input=action_input,
                        observation=observation,
                        state=AgentState.OBSERVING
                    )
                    self.steps.append(step)

                    # Update context with observation
                    context += f"\nLast observation: {observation[:200]}"
                else:
                    if self.verbose:
                        print("⚠ No valid action provided")
                    break

            return {
                "success": True,
                "iterations": len(self.steps),
                "steps": self.steps,
                "final_state": self.steps[-1].state if self.steps else AgentState.THINKING
            }

        finally:
            await self.cleanup_sessions()

    def get_server_stats(self) -> Dict[str, Any]:
        """Get statistics about connected servers and tools."""
        stats = {
            "total_servers": len(self.sessions),
            "total_tools": len(self.all_tools),
            "servers": {}
        }

        for server_name, tools in self.server_tools.items():
            stats["servers"][server_name] = {
                "tool_count": len(tools),
                "tools": [tool.name for tool in tools]
            }

        return stats

    def print_server_info(self):
        """Print information about all connected servers."""
        print("\n" + "=" * 70)
        print("CONNECTED SERVERS")
        print("=" * 70)

        for server_name, tools in self.server_tools.items():
            print(f"\n{server_name.upper()} SERVER:")
            print(f"  Tools: {len(tools)}")
            for tool in tools:
                print(f"    • {tool.name}: {tool.description}")

        print(f"\nTotal: {len(self.sessions)} servers, {len(self.all_tools)} tools")
        print("=" * 70)
