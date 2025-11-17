import asyncio
from typing import Optional
import sys
import os
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_openai import ChatOpenAI
from langchain_core.messages import ToolMessage
from dotenv import load_dotenv

# load environement variables
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

class MCPClient:
    def __init__(self):
        # Intializes session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.openai = ChatOpenAI(model="gpt-5-nano")

    # methods will go here
    async def connect_to_server(self, server_script_path: str):
        """
        Connect to an MCP server

        Args:
            server_script_path: Path to the server script
        """
        is_server = server_script_path.endswith('.py')
        if not is_server:
            raise ValueError("Server script must be a .py file")

        print(f"[DEBUG] Connecting to server: {server_script_path}")

        command = "python"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            print("[DEBUG] Transport established")

            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )
            print("[DEBUG] Session created")

            await self.session.initialize()
            print("[DEBUG] Session initialized")

            # List available tools
            response = await self.session.list_tools()
            tools = response.tools
            print(f"\nConnected to server with tools: {[tool.name for tool in tools]}")
        except Exception as e:
            print(f"[ERROR] Failed to connect to server: {e}")
            import traceback
            traceback.print_exc()
            raise

    # query processing logic
    async def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available tools"""

        if not self.session:
            raise RuntimeError("Not connected to MCP server. Call connect_to_server() first.")

        # Get MCP tools
        try:
            response = await self.session.list_tools()
            print(f"[DEBUG] Got {len(response.tools)} tools from MCP server")
        except Exception as e:
            print(f"[ERROR] Failed to get tools: {e}")
            raise

        # Convert to OpenAI format
        tools = []
        for tool in response.tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })

        # Use OpenAI model with tools
        messages = [{"role": "user", "content": query}]
        final_text = []

        max_iterations = 10
        for iteration in range(max_iterations):
            # Call OpenAI with tools
            llm_with_tools = self.openai.bind_tools(tools)
            response = llm_with_tools.invoke(messages)

            print(f"[DEBUG] Iteration {iteration + 1}: Got response with {len(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else 0} tool calls")

            # Check for tool calls
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Add the assistant message with tool calls
                messages.append(response)

                for tool_call in response.tool_calls:
                    # LangChain format: tool_call is a dict with 'name', 'args', 'id'
                    tool_name = tool_call.get("name") if isinstance(tool_call, dict) else tool_call.name
                    tool_args = tool_call.get("args") if isinstance(tool_call, dict) else tool_call.args
                    tool_id = tool_call.get("id") if isinstance(tool_call, dict) else getattr(tool_call, "id", None)

                    print(f"[DEBUG] Calling tool: {tool_name} with args: {tool_args}")
                    final_text.append(f"[Calling {tool_name} with args {tool_args}]")

                    # Execute via MCP
                    result = await self.session.call_tool(tool_name, tool_args)
                    print(f"[DEBUG] Tool result: {str(result.content)[:100]}...")

                    # Create a tool message using LangChain format
                    tool_message = ToolMessage(
                        content=str(result.content),
                        tool_call_id=tool_id
                    )
                    messages.append(tool_message)
            else:
                # No more tool calls
                if response.content:
                    final_text.append(response.content)
                break

        return "\n".join(final_text)
    
    # add interactive chat interface
    async def chat_loop(self):
        """
        Run an interactive chat loop
        """
        print(f"\nMCP Client Started!")
        print(F"Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input(f"\nQuery: ").strip()
                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print(f"\n {response}")

            except Exception as e:
                print(f"\nError: {str(e)}")
            
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())




