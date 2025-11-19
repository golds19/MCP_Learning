#!/usr/bin/env python3
"""
SQLite CRUD MCP Server
A Model Context Protocol server that provides CRUD operations for SQLite databases.
"""

import sqlite3
import json
import logging
from typing import Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sqlite-mcp-server")

# MCP imports
try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.server.stdio
except ImportError:
    logger.error("MCP library not found. Please install it with: pip install mcp")
    raise

# Initialize MCP server
app = Server("sqlite-crud-server")

# Database path - can be configured
DB_PATH = "mcp_database.db"


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Create and return a database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def execute_query(query: str, params: tuple = (), db_path: str = DB_PATH, fetch: bool = False) -> Any:
    """
    Execute a SQL query and return results if needed.

    Args:
        query: SQL query to execute
        params: Query parameters
        db_path: Path to database file
        fetch: Whether to fetch and return results

    Returns:
        Query results if fetch=True, otherwise None
    """
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)

        if fetch:
            # Fetch all results and convert to list of dicts
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        else:
            conn.commit()
            return {"affected_rows": cursor.rowcount, "lastrowid": cursor.lastrowid}

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise Exception(f"Database error: {str(e)}")
    finally:
        if conn:
            conn.close()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for SQLite CRUD operations."""
    return [
        Tool(
            name="create_table",
            description="Create a new table in the SQLite database",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to create"
                    },
                    "columns": {
                        "type": "object",
                        "description": "Column definitions as key-value pairs (column_name: type)",
                        "additionalProperties": {"type": "string"}
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Path to database file (optional, defaults to mcp_database.db)"
                    }
                },
                "required": ["table_name", "columns"]
            }
        ),
        Tool(
            name="insert_record",
            description="Insert a new record into a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table"
                    },
                    "data": {
                        "type": "object",
                        "description": "Data to insert as key-value pairs",
                        "additionalProperties": True
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Path to database file (optional)"
                    }
                },
                "required": ["table_name", "data"]
            }
        ),
        Tool(
            name="read_records",
            description="Read records from a table with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table"
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Columns to select (optional, defaults to all)"
                    },
                    "where": {
                        "type": "string",
                        "description": "WHERE clause without the WHERE keyword (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to return (optional)"
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Path to database file (optional)"
                    }
                },
                "required": ["table_name"]
            }
        ),
        Tool(
            name="update_record",
            description="Update records in a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table"
                    },
                    "data": {
                        "type": "object",
                        "description": "Data to update as key-value pairs",
                        "additionalProperties": True
                    },
                    "where": {
                        "type": "string",
                        "description": "WHERE clause without the WHERE keyword"
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Path to database file (optional)"
                    }
                },
                "required": ["table_name", "data", "where"]
            }
        ),
        Tool(
            name="delete_record",
            description="Delete records from a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table"
                    },
                    "where": {
                        "type": "string",
                        "description": "WHERE clause without the WHERE keyword"
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Path to database file (optional)"
                    }
                },
                "required": ["table_name", "where"]
            }
        ),
        Tool(
            name="execute_query",
            description="Execute a custom SQL query (SELECT queries only for safety)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query to execute (SELECT only)"
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Path to database file (optional)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_tables",
            description="List all tables in the database",
            inputSchema={
                "type": "object",
                "properties": {
                    "db_path": {
                        "type": "string",
                        "description": "Path to database file (optional)"
                    }
                }
            }
        ),
        Tool(
            name="describe_table",
            description="Get the schema/structure of a table",
            inputSchema={
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Name of the table to describe"
                    },
                    "db_path": {
                        "type": "string",
                        "description": "Path to database file (optional)"
                    }
                },
                "required": ["table_name"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls for SQLite CRUD operations."""

    try:
        db_path = arguments.get("db_path", DB_PATH)

        if name == "create_table":
            table_name = arguments["table_name"]
            columns = arguments["columns"]

            # Build CREATE TABLE query
            column_defs = []
            for col_name, col_type in columns.items():
                column_defs.append(f"{col_name} {col_type}")

            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"
            execute_query(query, db_path=db_path)

            return [TextContent(
                type="text",
                text=f"Table '{table_name}' created successfully with columns: {', '.join(columns.keys())}"
            )]

        elif name == "insert_record":
            table_name = arguments["table_name"]
            data = arguments["data"]

            # Build INSERT query
            columns = list(data.keys())
            placeholders = ["?" for _ in columns]
            values = tuple(data.values())

            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            result = execute_query(query, values, db_path=db_path)

            return [TextContent(
                type="text",
                text=f"Record inserted successfully. Row ID: {result['lastrowid']}"
            )]

        elif name == "read_records":
            table_name = arguments["table_name"]
            columns = arguments.get("columns", ["*"])
            where_clause = arguments.get("where")
            limit = arguments.get("limit")

            # Build SELECT query
            cols_str = ", ".join(columns) if columns != ["*"] else "*"
            query = f"SELECT {cols_str} FROM {table_name}"

            if where_clause:
                query += f" WHERE {where_clause}"
            if limit:
                query += f" LIMIT {limit}"

            results = execute_query(query, db_path=db_path, fetch=True)

            return [TextContent(
                type="text",
                text=f"Found {len(results)} record(s):\n{json.dumps(results, indent=2)}"
            )]

        elif name == "update_record":
            table_name = arguments["table_name"]
            data = arguments["data"]
            where_clause = arguments["where"]

            # Build UPDATE query
            set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
            values = tuple(data.values())

            query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            result = execute_query(query, values, db_path=db_path)

            return [TextContent(
                type="text",
                text=f"Updated {result['affected_rows']} record(s) successfully"
            )]

        elif name == "delete_record":
            table_name = arguments["table_name"]
            where_clause = arguments["where"]

            # Build DELETE query
            query = f"DELETE FROM {table_name} WHERE {where_clause}"
            result = execute_query(query, db_path=db_path)

            return [TextContent(
                type="text",
                text=f"Deleted {result['affected_rows']} record(s) successfully"
            )]

        elif name == "execute_query":
            query = arguments["query"].strip()

            # Security check - only allow SELECT queries
            if not query.upper().startswith("SELECT"):
                return [TextContent(
                    type="text",
                    text="Error: Only SELECT queries are allowed for security reasons. Use specific CRUD tools for modifications."
                )]

            results = execute_query(query, db_path=db_path, fetch=True)

            return [TextContent(
                type="text",
                text=f"Query executed successfully:\n{json.dumps(results, indent=2)}"
            )]

        elif name == "list_tables":
            query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            results = execute_query(query, db_path=db_path, fetch=True)
            tables = [row['name'] for row in results]

            return [TextContent(
                type="text",
                text=f"Tables in database:\n{json.dumps(tables, indent=2)}"
            )]

        elif name == "describe_table":
            table_name = arguments["table_name"]
            query = f"PRAGMA table_info({table_name})"
            results = execute_query(query, db_path=db_path, fetch=True)

            if not results:
                return [TextContent(
                    type="text",
                    text=f"Table '{table_name}' not found"
                )]

            # Format the schema information
            schema = []
            for col in results:
                schema.append({
                    "name": col["name"],
                    "type": col["type"],
                    "not_null": bool(col["notnull"]),
                    "default": col["dflt_value"],
                    "primary_key": bool(col["pk"])
                })

            return [TextContent(
                type="text",
                text=f"Schema for table '{table_name}':\n{json.dumps(schema, indent=2)}"
            )]

        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        logger.error(f"Error in {name}: {str(e)}")
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    logger.info("Starting SQLite CRUD MCP Server...")

    # Run the server using stdin/stdout
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
