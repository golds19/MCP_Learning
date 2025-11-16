# from mcp.server.fastmcp import FastMCP
# from dotenv import load_dotenv

# load_dotenv()

# # Create mcp server
# mcp = FastMCP(
#     name="Calculator",
# )

# # Add a simple calculator tool
# @mcp.tool()
# def add(a:int, b:int) -> int:
#     """Add two numbers together"""
#     return a + b

# # Run the server
# if __name__ == "__main__":
#     transport = "stdio"  # Changed to stdio
#     if transport == "stdio":
#         print(f"Running server with stdio transport", flush=True)  # Added flush=True
#         mcp.run(transport="stdio")
#     elif transport == "sse":
#         print(f"Running server with SSE transport")
#         mcp.run(transport="sse")
#     else:
#         raise ValueError(f"Unknown transport: {transport}")

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# Create mcp server
mcp = FastMCP(
    name="Calculator",
    host="0.0.0.0",
    port=8050
)

# Add a simple calculator tool
@mcp.tool()
def add(a:int, b:int) -> int:
    """Add two numbers together"""
    return a + b

# Run the server
if __name__ == "__main__":
    transport = "sse"
    if transport == "stdio":
        print(f"Running server with stdio transport")
        mcp.run(transport="stdio")
    elif transport == "sse":
        print(f"Running server with SSE transport")
        mcp.run(transport="sse")
    else:
        raise ValueError(f"Unknown transport: {transport}")