# Learning Model Context Protocol (MCP)

## What is MCP?

Model Context Protocol (MCP) is an open protocol developed by Anthropic that standardizes how AI applications connect to external data sources and tools. Think of it as a universal adapter that allows AI assistants like Claude to securely interact with various services, databases, and APIs.

## Why Learn MCP?

- **Extensibility**: Add custom tools and data sources to AI applications
- **Standardization**: One protocol works across different AI systems
- **Security**: Built-in security model for safe AI-tool interactions
- **Flexibility**: Connect to databases, APIs, file systems, and more

## Core Concepts

### 1. MCP Servers

Programs that expose resources (data) and tools (actions) to AI applications. Examples:

- File system access
- Database connections
- API integrations
- Custom business logic

### 2. MCP Clients

AI applications that connect to MCP servers to access resources and tools. Examples:

- Claude Desktop
- Custom AI applications
- Automation tools

### 3. Resources

Data that can be read by the AI:

- Files and documents
- Database records
- API responses
- Live data feeds

### 4. Tools

Actions the AI can perform:

- Running queries
- Modifying data
- Calling external APIs
- Executing commands