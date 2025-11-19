#!/usr/bin/env python3
"""
ReAct Agent for SQLite MCP Server
Implements a Reasoning + Acting agent that can interact with the SQLite CRUD server.
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class AgentState(Enum):
    """States the agent can be in during execution."""
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    FINISHED = "finished"


@dataclass
class Step:
    """Represents a single step in the ReAct loop."""
    thought: str
    action: Optional[str] = None
    action_input: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None
    state: AgentState = AgentState.THINKING


class ReActAgent:
    """
    ReAct (Reasoning + Acting) Agent that can use SQLite MCP server tools.

    The agent follows this loop:
    1. Thought: Reason about what to do next
    2. Action: Choose a tool and provide input
    3. Observation: Observe the result
    4. Repeat until task is complete
    """

    def __init__(self, server_script_path: str, max_iterations: int = 10, verbose: bool = True):
        """
        Initialize the ReAct agent.

        Args:
            server_script_path: Path to the SQLite MCP server script
            max_iterations: Maximum number of reasoning-acting iterations
            verbose: Whether to print detailed execution steps
        """
        self.server_script_path = server_script_path
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.tools: List[Any] = []
        self.steps: List[Step] = []
        self.session: Optional[ClientSession] = None

    async def initialize_session(self):
        """Initialize connection to the MCP server."""
        server_params = StdioServerParameters(
            command="python",
            args=[self.server_script_path],
            env=None
        )

        # Store the context manager for later use
        self._stdio_context = stdio_client(server_params)
        read, write = await self._stdio_context.__aenter__()

        self._session_context = ClientSession(read, write)
        self.session = await self._session_context.__aenter__()

        # Initialize and get available tools
        await self.session.initialize()
        tools_response = await self.session.list_tools()
        self.tools = tools_response.tools

        if self.verbose:
            print(f"✓ Connected to SQLite MCP server")
            print(f"✓ Available tools: {len(self.tools)}")
            for tool in self.tools:
                print(f"  - {tool.name}")
            print()

    async def cleanup_session(self):
        """Clean up the MCP session."""
        if hasattr(self, '_session_context'):
            await self._session_context.__aexit__(None, None, None)
        if hasattr(self, '_stdio_context'):
            await self._stdio_context.__aexit__(None, None, None)

    def _get_tool_descriptions(self) -> str:
        """Get formatted descriptions of available tools."""
        descriptions = []
        for tool in self.tools:
            descriptions.append(f"- {tool.name}: {tool.description}")
        return "\n".join(descriptions)

    def _parse_thought_action(self, response: str) -> tuple[str, Optional[str], Optional[Dict]]:
        """
        Parse the agent's response to extract thought, action, and action input.

        Expected format:
        Thought: <reasoning>
        Action: <tool_name>
        Action Input: <json_input>
        """
        thought_match = re.search(r'Thought:\s*(.+?)(?=\n(?:Action:|$))', response, re.DOTALL | re.IGNORECASE)
        action_match = re.search(r'Action:\s*(.+?)(?=\n|$)', response, re.IGNORECASE)
        action_input_match = re.search(r'Action Input:\s*({.+?}|\{.+?\})', response, re.DOTALL | re.IGNORECASE)

        thought = thought_match.group(1).strip() if thought_match else ""
        action = action_match.group(1).strip() if action_match else None

        action_input = None
        if action_input_match:
            try:
                action_input = json.loads(action_input_match.group(1))
            except json.JSONDecodeError:
                action_input = None

        return thought, action, action_input

    def _is_task_complete(self, thought: str) -> bool:
        """Check if the agent thinks the task is complete."""
        completion_keywords = [
            "task complete",
            "finished",
            "done",
            "final answer",
            "successfully completed",
            "task is complete"
        ]
        return any(keyword in thought.lower() for keyword in completion_keywords)

    async def _execute_action(self, action: str, action_input: Dict[str, Any]) -> str:
        """Execute an action using the MCP server."""
        try:
            result = await self.session.call_tool(action, arguments=action_input)
            return result.content[0].text
        except Exception as e:
            return f"Error executing action: {str(e)}"

    def _reason(self, task: str, context: str) -> str:
        """
        Simplified reasoning function that generates thoughts and actions.

        In a production system, this would call an LLM (like GPT-4, Claude, etc.)
        For this implementation, it uses a rule-based approach for demonstration.
        """
        # This is a simplified version - in production, you'd call an LLM here
        # For now, we'll create a prompt-based reasoning system

        steps_taken = len(self.steps)

        # Create a summary of previous steps
        history = ""
        for i, step in enumerate(self.steps[-3:]):  # Last 3 steps
            history += f"\nStep {i+1}:\n"
            history += f"  Thought: {step.thought}\n"
            if step.action:
                history += f"  Action: {step.action}\n"
                history += f"  Observation: {step.observation}\n"

        # Build reasoning prompt
        prompt = f"""You are a ReAct agent helping to complete database tasks.

Task: {task}

Available Tools:
{self._get_tool_descriptions()}

Context: {context}

Previous Steps:{history}

Based on the task and previous steps, what should you do next?

Respond in this EXACT format:
Thought: [your reasoning about what to do next]
Action: [tool name to use, or "FINISH" if task is complete]
Action Input: {{"param": "value"}}

Your response:"""

        # For demonstration, return a structured prompt
        # In production, you would send this to an LLM and get the response
        return prompt

    async def run(self, task: str, llm_callback=None) -> Dict[str, Any]:
        """
        Run the ReAct agent to complete a task.

        Args:
            task: The task to complete
            llm_callback: Optional async function that takes a prompt and returns LLM response
                         If not provided, uses manual mode

        Returns:
            Dictionary with execution results and steps taken
        """
        await self.initialize_session()

        if self.verbose:
            print("=" * 70)
            print(f"TASK: {task}")
            print("=" * 70)
            print()

        context = f"Available tools: {', '.join([t.name for t in self.tools])}"

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

                    # Execute action
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
            await self.cleanup_session()

    def _auto_generate_response(self, task: str, iteration: int) -> str:
        """
        Auto-generate demo responses for common database tasks.
        This simulates what an LLM would respond.
        """
        task_lower = task.lower()

        # Demo flow for creating and populating a users table
        if "create" in task_lower and "user" in task_lower:
            if iteration == 0:
                return """Thought: I need to create a users table with appropriate columns for storing user information.
Action: create_table
Action Input: {"table_name": "users", "columns": {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "name": "TEXT NOT NULL", "email": "TEXT UNIQUE NOT NULL", "age": "INTEGER", "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"}}"""
            elif iteration == 1:
                return """Thought: The table has been created successfully. Now I should verify it exists by listing all tables.
Action: list_tables
Action Input: {}"""
            elif iteration == 2:
                return """Thought: The users table exists. Task is complete.
Action: FINISH
Action Input: {}"""

        # Demo flow for inserting data
        if "insert" in task_lower or "add" in task_lower:
            if iteration == 0:
                return """Thought: I need to insert a new user record into the users table.
Action: insert_record
Action Input: {"table_name": "users", "data": {"name": "John Doe", "email": "john@example.com", "age": 30}}"""
            elif iteration == 1:
                return """Thought: Record inserted successfully. Task is complete.
Action: FINISH
Action Input: {}"""

        # Default response
        return """Thought: I'm not sure how to proceed with this task automatically. Manual input needed.
Action: list_tables
Action Input: {}"""

    def print_summary(self):
        """Print a summary of all steps taken."""
        print("\n" + "=" * 70)
        print("EXECUTION SUMMARY")
        print("=" * 70)

        for i, step in enumerate(self.steps):
            print(f"\nStep {i + 1}:")
            print(f"  Thought: {step.thought}")
            if step.action:
                print(f"  Action: {step.action}")
                print(f"  Observation: {step.observation[:100]}..." if len(step.observation or "") > 100 else f"  Observation: {step.observation}")

        print(f"\nTotal steps: {len(self.steps)}")
        print("=" * 70)
