#!/usr/bin/env python3
"""
Test client for SQLite CRUD MCP Server
Demonstrates how to use the MCP server with CRUD operations.
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_crud_operations():
    """Test all CRUD operations of the SQLite MCP server."""

    # Define server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["sqlite_server.py"],
        env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            print("=" * 60)
            print("SQLite CRUD MCP Server - Test Client")
            print("=" * 60)

            # List available tools
            tools = await session.list_tools()
            print(f"\n✓ Available tools: {len(tools.tools)}")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            print("\n" + "=" * 60)
            print("TEST 1: Create a table")
            print("=" * 60)
            result = await session.call_tool(
                "create_table",
                arguments={
                    "table_name": "users",
                    "columns": {
                        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                        "name": "TEXT NOT NULL",
                        "email": "TEXT UNIQUE NOT NULL",
                        "age": "INTEGER",
                        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    }
                }
            )
            print(f"Result: {result.content[0].text}")

            print("\n" + "=" * 60)
            print("TEST 2: Insert records")
            print("=" * 60)

            # Insert multiple users
            users_data = [
                {"name": "Alice Johnson", "email": "alice@example.com", "age": 28},
                {"name": "Bob Smith", "email": "bob@example.com", "age": 34},
                {"name": "Charlie Brown", "email": "charlie@example.com", "age": 25},
            ]

            for user in users_data:
                result = await session.call_tool(
                    "insert_record",
                    arguments={
                        "table_name": "users",
                        "data": user
                    }
                )
                print(f"Result: {result.content[0].text}")

            print("\n" + "=" * 60)
            print("TEST 3: Read all records")
            print("=" * 60)
            result = await session.call_tool(
                "read_records",
                arguments={
                    "table_name": "users"
                }
            )
            print(f"Result: {result.content[0].text}")

            print("\n" + "=" * 60)
            print("TEST 4: Read with filtering")
            print("=" * 60)
            result = await session.call_tool(
                "read_records",
                arguments={
                    "table_name": "users",
                    "where": "age > 25",
                    "columns": ["name", "email", "age"]
                }
            )
            print(f"Result: {result.content[0].text}")

            print("\n" + "=" * 60)
            print("TEST 5: Update a record")
            print("=" * 60)
            result = await session.call_tool(
                "update_record",
                arguments={
                    "table_name": "users",
                    "data": {"age": 29},
                    "where": "name = 'Alice Johnson'"
                }
            )
            print(f"Result: {result.content[0].text}")

            # Verify the update
            result = await session.call_tool(
                "read_records",
                arguments={
                    "table_name": "users",
                    "where": "name = 'Alice Johnson'"
                }
            )
            print(f"Verification: {result.content[0].text}")

            print("\n" + "=" * 60)
            print("TEST 6: Execute custom query")
            print("=" * 60)
            result = await session.call_tool(
                "execute_query",
                arguments={
                    "query": "SELECT name, email FROM users WHERE age >= 30 ORDER BY age DESC"
                }
            )
            print(f"Result: {result.content[0].text}")

            print("\n" + "=" * 60)
            print("TEST 7: Describe table structure")
            print("=" * 60)
            result = await session.call_tool(
                "describe_table",
                arguments={
                    "table_name": "users"
                }
            )
            print(f"Result: {result.content[0].text}")

            print("\n" + "=" * 60)
            print("TEST 8: List all tables")
            print("=" * 60)
            result = await session.call_tool(
                "list_tables",
                arguments={}
            )
            print(f"Result: {result.content[0].text}")

            print("\n" + "=" * 60)
            print("TEST 9: Delete a record")
            print("=" * 60)
            result = await session.call_tool(
                "delete_record",
                arguments={
                    "table_name": "users",
                    "where": "name = 'Charlie Brown'"
                }
            )
            print(f"Result: {result.content[0].text}")

            # Verify deletion
            result = await session.call_tool(
                "read_records",
                arguments={
                    "table_name": "users"
                }
            )
            print(f"Verification: {result.content[0].text}")

            print("\n" + "=" * 60)
            print("All tests completed successfully!")
            print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_crud_operations())
