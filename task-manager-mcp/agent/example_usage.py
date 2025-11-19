#!/usr/bin/env python3
"""
Example Usage of ReAct Agent with SQLite MCP Server

This script demonstrates different ways to use the ReAct agent:
1. Auto mode (demo with predefined responses)
2. Manual mode (user provides responses)
3. LLM mode (with OpenAI, Anthropic, or Ollama)
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from agent.react_agent import ReActAgent
from agent.llm_integration import llm_callback_factory, MockLLMProvider


async def demo_auto_mode():
    """Demo: Auto mode with predefined responses."""
    print("\n" + "=" * 70)
    print("DEMO 1: AUTO MODE (Predefined Responses)")
    print("=" * 70 + "\n")

    # Path to the SQLite MCP server
    server_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "mcp_server",
        "sqlite_server.py"
    )

    # Create agent
    agent = ReActAgent(
        server_script_path=server_path,
        max_iterations=5,
        verbose=True
    )

    # Run with auto mode (no LLM needed)
    task = "Create a users table with id, name, email, age, and created_at columns"
    result = await agent.run(task)

    # Print summary
    agent.print_summary()

    return result


async def demo_manual_mode():
    """Demo: Manual mode where user provides responses."""
    print("\n" + "=" * 70)
    print("DEMO 2: MANUAL MODE (User Input)")
    print("=" * 70 + "\n")

    server_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "mcp_server",
        "sqlite_server.py"
    )

    agent = ReActAgent(
        server_script_path=server_path,
        max_iterations=5,
        verbose=True
    )

    # Run without LLM callback - will prompt user for input
    task = "List all tables in the database"
    result = await agent.run(task)

    agent.print_summary()

    return result


async def demo_mock_llm():
    """Demo: Using mock LLM with predefined responses."""
    print("\n" + "=" * 70)
    print("DEMO 3: MOCK LLM MODE")
    print("=" * 70 + "\n")

    server_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "mcp_server",
        "sqlite_server.py"
    )

    # Create mock LLM with predefined responses
    mock_llm = MockLLMProvider()

    # Add predefined responses for a task
    mock_llm.add_response("""Thought: I need to check what tables exist in the database first.
Action: list_tables
Action Input: {}""")

    mock_llm.add_response("""Thought: Now I should create a products table for an e-commerce system.
Action: create_table
Action Input: {"table_name": "products", "columns": {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "name": "TEXT NOT NULL", "price": "REAL NOT NULL", "stock": "INTEGER DEFAULT 0", "description": "TEXT"}}""")

    mock_llm.add_response("""Thought: Table created. Let me add a sample product.
Action: insert_record
Action Input: {"table_name": "products", "data": {"name": "Laptop", "price": 999.99, "stock": 10, "description": "High-performance laptop"}}""")

    mock_llm.add_response("""Thought: Product added. Let me verify by reading the products.
Action: read_records
Action Input: {"table_name": "products"}""")

    mock_llm.add_response("""Thought: Perfect! The table has been created and populated with a sample product. Task complete.
Action: FINISH
Action Input: {}""")

    # Create callback using the mock LLM
    async def mock_callback(prompt: str) -> str:
        return await mock_llm.generate(prompt)

    agent = ReActAgent(
        server_script_path=server_path,
        max_iterations=10,
        verbose=True
    )

    task = "Create a products table and add a sample product"
    result = await agent.run(task, llm_callback=mock_callback)

    agent.print_summary()

    return result


async def demo_with_openai():
    """Demo: Using OpenAI GPT for reasoning (requires API key)."""
    print("\n" + "=" * 70)
    print("DEMO 4: OPENAI GPT MODE")
    print("=" * 70 + "\n")

    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠ OPENAI_API_KEY not found in environment variables")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        return None

    server_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "mcp_server",
        "sqlite_server.py"
    )

    # Create LLM callback
    llm_callback = await llm_callback_factory("openai", model="gpt-4")

    agent = ReActAgent(
        server_script_path=server_path,
        max_iterations=10,
        verbose=True
    )

    task = "Create an employees table, add 3 employees, then show all employees over age 25"
    result = await agent.run(task, llm_callback=llm_callback)

    agent.print_summary()

    return result


async def demo_with_anthropic():
    """Demo: Using Anthropic Claude for reasoning (requires API key)."""
    print("\n" + "=" * 70)
    print("DEMO 5: ANTHROPIC CLAUDE MODE")
    print("=" * 70 + "\n")

    # Check if API key is available
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠ ANTHROPIC_API_KEY not found in environment variables")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        return None

    server_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "mcp_server",
        "sqlite_server.py"
    )

    # Create LLM callback
    llm_callback = await llm_callback_factory("anthropic", model="claude-3-5-sonnet-20241022")

    agent = ReActAgent(
        server_script_path=server_path,
        max_iterations=10,
        verbose=True
    )

    task = "Create a tasks table with id, title, description, status, and due_date. Add 2 sample tasks."
    result = await agent.run(task, llm_callback=llm_callback)

    agent.print_summary()

    return result


async def demo_with_ollama():
    """Demo: Using Ollama local LLM for reasoning."""
    print("\n" + "=" * 70)
    print("DEMO 6: OLLAMA LOCAL LLM MODE")
    print("=" * 70 + "\n")

    print("⚠ Make sure Ollama is running locally (http://localhost:11434)")
    print("Install Ollama from: https://ollama.ai\n")

    server_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "mcp_server",
        "sqlite_server.py"
    )

    try:
        # Create LLM callback
        llm_callback = await llm_callback_factory("ollama", model="llama2")

        agent = ReActAgent(
            server_script_path=server_path,
            max_iterations=10,
            verbose=True
        )

        task = "List all tables in the database"
        result = await agent.run(task, llm_callback=llm_callback)

        agent.print_summary()

        return result
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Ollama is running and you have pulled a model (e.g., 'ollama pull llama2')")
        return None


def print_menu():
    """Print demo selection menu."""
    print("\n" + "=" * 70)
    print("ReAct Agent Demo - Choose a mode:")
    print("=" * 70)
    print("1. Auto Mode (predefined responses - no LLM needed)")
    print("2. Manual Mode (you provide responses)")
    print("3. Mock LLM Mode (simulated LLM with predefined responses)")
    print("4. OpenAI GPT Mode (requires OPENAI_API_KEY)")
    print("5. Anthropic Claude Mode (requires ANTHROPIC_API_KEY)")
    print("6. Ollama Local LLM Mode (requires Ollama running locally)")
    print("0. Exit")
    print("=" * 70)


async def main():
    """Main function to run demos."""
    demos = {
        "1": demo_auto_mode,
        "2": demo_manual_mode,
        "3": demo_mock_llm,
        "4": demo_with_openai,
        "5": demo_with_anthropic,
        "6": demo_with_ollama,
    }

    while True:
        print_menu()
        choice = input("\nSelect a demo (0-6): ").strip()

        if choice == "0":
            print("Goodbye!")
            break

        if choice in demos:
            try:
                await demos[choice]()
                input("\nPress Enter to continue...")
            except KeyboardInterrupt:
                print("\n\nDemo interrupted by user")
            except Exception as e:
                print(f"\n❌ Error running demo: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("Invalid choice. Please select 0-6.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
