#!/usr/bin/env python3
"""
Simple Demo of ReAct Agent with SQLite MCP Server
A quick demonstration using auto mode (no LLM required)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agent.react_agent import ReActAgent


async def run_simple_demo():
    """Run a simple demonstration of the ReAct agent."""

    # Path to the SQLite MCP server
    server_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "mcp_server",
        "sqlite_server.py"
    )

    print("\n" + "=" * 70)
    print("ReAct Agent - Simple Demo")
    print("=" * 70)
    print("\nThis demo will:")
    print("1. Connect to the SQLite MCP server")
    print("2. Create a 'users' table")
    print("3. Verify the table was created")
    print("\nRunning in AUTO mode (no LLM needed)...\n")
    print("=" * 70 + "\n")

    # Create the ReAct agent
    agent = ReActAgent(
        server_script_path=server_path,
        max_iterations=5,
        verbose=True
    )

    # Define the task
    task = "Create a users table with id, name, email, age, and created_at columns"

    print(f"Task: {task}\n")
    print("Starting agent execution...\n")

    # Run the agent in auto mode
    # The agent will use predefined responses for this demo task
    result = await agent.run(task)

    # Print summary
    print("\n")
    agent.print_summary()

    # Print final result
    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    print(f"Success: {result['success']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Final State: {result['final_state'].value}")
    print("=" * 70 + "\n")

    return result


async def run_interactive_demo():
    """Run an interactive demo where you can specify tasks."""

    server_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "mcp_server",
        "sqlite_server.py"
    )

    print("\n" + "=" * 70)
    print("ReAct Agent - Interactive Demo")
    print("=" * 70)
    print("\nYou can give tasks to the agent!")
    print("\nAvailable operations:")
    print("- Create tables")
    print("- Insert records")
    print("- Read records")
    print("- Update records")
    print("- Delete records")
    print("- List tables")
    print("- Describe table structure")
    print("\n" + "=" * 70 + "\n")

    while True:
        task = input("Enter a task (or 'quit' to exit): ").strip()

        if task.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break

        if not task:
            print("Please enter a task.")
            continue

        print("\n" + "=" * 70)
        print(f"Executing task: {task}")
        print("=" * 70 + "\n")

        agent = ReActAgent(
            server_script_path=server_path,
            max_iterations=10,
            verbose=True
        )

        try:
            # Run in auto mode first
            print("Attempting AUTO mode...")
            result = await agent.run(task)
            agent.print_summary()
        except Exception as e:
            print(f"\n❌ Error: {e}")

        print("\n")


def main():
    """Main function."""
    print("\nWelcome to the ReAct Agent Simple Demo!\n")
    print("Choose a mode:")
    print("1. Simple Demo (auto mode)")
    print("2. Interactive Demo (auto mode with custom tasks)")
    print("0. Exit")

    choice = input("\nSelect (0-2): ").strip()

    if choice == "1":
        asyncio.run(run_simple_demo())
    elif choice == "2":
        asyncio.run(run_interactive_demo())
    elif choice == "0":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
