# ReAct Agent for SQLite MCP Server

A **Reasoning + Acting (ReAct)** agent that can interact with SQLite databases through the Model Context Protocol (MCP).

## Overview

This implementation combines:
- **ReAct Pattern**: An agent that reasons about tasks and acts using available tools
- **MCP Integration**: Connects to the SQLite CRUD MCP server
- **LLM Support**: Works with OpenAI, Ollama, or mock LLM providers
- **Flexible Execution**: Supports auto, manual, and LLM-driven modes

## Architecture

### Core Components

#### 1. `react_agent.py` - The ReAct Agent
The main agent implementation that follows the ReAct loop:

```
1. THOUGHT → Reason about what to do next
2. ACTION → Choose a tool and provide input
3. OBSERVATION → See the result
4. Repeat until task complete
```

**Key Classes:**
- `ReActAgent`: Main agent class
- `Step`: Represents a single reasoning-acting step
- `AgentState`: Enum for agent states (THINKING, ACTING, OBSERVING, FINISHED)

#### 2. `llm_integration.py` - LLM Providers
Interfaces to different LLM providers for the reasoning component:

- `OpenAIProvider`: OpenAI GPT models
- `OllamaProvider`: Local Ollama models
- `MockLLMProvider`: Testing with predefined responses

#### 3. Demo Scripts
- `simple_demo.py`: Quick demonstration (no LLM needed)
- `example_usage.py`: Comprehensive examples with all modes

## How It Works

### The ReAct Loop

```
Task: "Create a users table"

┌─────────────────────────────────────────┐
│ 1. THOUGHT PHASE                        │
│    Agent: "I need to create a table     │
│            with appropriate columns"    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 2. ACTION PHASE                         │
│    Action: create_table                 │
│    Input: {                             │
│      "table_name": "users",             │
│      "columns": {...}                   │
│    }                                    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ 3. OBSERVATION PHASE                    │
│    Result: "Table 'users' created       │
│             successfully"               │
└─────────────────────────────────────────┘
                    ↓
         (repeat or finish)
```

### MCP Connection Flow

```
ReAct Agent
    ↓
MCP Client (stdio)
    ↓
SQLite MCP Server
    ↓
SQLite Database
```

The agent:
1. Connects to the MCP server via stdin/stdout
2. Lists available tools (create_table, insert_record, etc.)
3. Calls tools based on reasoning
4. Processes observations to decide next steps

## Usage Examples

### 1. Simple Auto Mode (No LLM Required)

```python
from agent.react_agent import ReActAgent

server_path = "../mcp_server/sqlite_server.py"
agent = ReActAgent(server_path, verbose=True)

task = "Create a users table with id, name, and email"
result = await agent.run(task)
```

### 2. With Mock LLM (Predefined Responses)

```python
from agent.llm_integration import MockLLMProvider

mock_llm = MockLLMProvider()
mock_llm.add_response("""
Thought: I need to list tables first
Action: list_tables
Action Input: {}
""")

async def callback(prompt):
    return await mock_llm.generate(prompt)

result = await agent.run(task, llm_callback=callback)
```

### 3. With OpenAI GPT

```python
from agent.llm_integration import llm_callback_factory

# Set OPENAI_API_KEY environment variable first
llm_callback = await llm_callback_factory("openai", model="gpt-4")
result = await agent.run(task, llm_callback=llm_callback)
```

### 4. With Ollama (Local)

```python
from agent.llm_integration import llm_callback_factory

# Make sure Ollama is running
llm_callback = await llm_callback_factory("ollama", model="llama2")
result = await agent.run(task, llm_callback=llm_callback)
```

## Running the Demos

### Quick Start

```bash
cd agent
python simple_demo.py
```

Choose mode 1 for a simple demonstration.

### Full Examples

```bash
python example_usage.py
```

This provides 6 different demo modes:
1. Auto mode (predefined responses)
2. Manual mode (you provide responses)
3. Mock LLM mode
4. OpenAI mode
5. Anthropic mode (if enabled)
6. Ollama mode

## Implementation Details

### Agent Initialization

```python
agent = ReActAgent(
    server_script_path="path/to/sqlite_server.py",
    max_iterations=10,    # Maximum reasoning loops
    verbose=True          # Print execution details
)
```

### Session Management

The agent manages MCP sessions automatically:

1. `initialize_session()`: Connects to MCP server
2. `cleanup_session()`: Properly closes connections
3. Context managers ensure cleanup even on errors

### Response Parsing

The agent expects LLM responses in this format:

```
Thought: <reasoning about what to do>
Action: <tool_name>
Action Input: {"param": "value"}
```

Example:
```
Thought: I need to create a users table with standard fields
Action: create_table
Action Input: {"table_name": "users", "columns": {"id": "INTEGER PRIMARY KEY", "name": "TEXT"}}
```

### Auto-Generation for Demos

For demo purposes, the agent can auto-generate responses for common tasks:

- Creating tables
- Inserting records
- Reading data
- Listing tables

This is implemented in `_auto_generate_response()`.

## Available MCP Tools

The agent can use these SQLite tools:

1. **create_table** - Create new tables
2. **insert_record** - Insert data
3. **read_records** - Read with filtering
4. **update_record** - Update records
5. **delete_record** - Delete records
6. **execute_query** - Custom SELECT queries
7. **list_tables** - List all tables
8. **describe_table** - Get table schema

## Error Handling

The agent includes robust error handling:

- MCP connection errors
- Tool execution errors
- LLM response parsing errors
- Session cleanup on failure

## Extending the Agent

### Adding New LLM Providers

```python
from agent.llm_integration import LLMProvider

class CustomProvider(LLMProvider):
    async def generate(self, prompt: str, **kwargs) -> str:
        # Your implementation
        return response
```

### Custom Reasoning Logic

Override `_reason()` method:

```python
class CustomReActAgent(ReActAgent):
    def _reason(self, task: str, context: str) -> str:
        # Custom reasoning logic
        return prompt
```

### Task-Specific Agents

Create specialized agents for specific tasks:

```python
class DataAnalysisAgent(ReActAgent):
    async def analyze_data(self, table_name: str):
        task = f"Analyze data in {table_name} table"
        return await self.run(task)
```

## Limitations and Considerations

1. **Auto Mode**: Only works for predefined task patterns
2. **Security**: Only SELECT queries allowed in execute_query
3. **Max Iterations**: Prevents infinite loops (default: 10)
4. **LLM Costs**: OpenAI mode incurs API costs
5. **Local Resources**: Ollama requires local model installation

## Requirements

- Python 3.8+
- MCP library (`pip install mcp`)
- Optional: OpenAI (`pip install openai`)
- Optional: Anthropic (`pip install anthropic`)
- Optional: Ollama (local installation)

## Project Structure

```
agent/
├── __init__.py           # Package initialization
├── react_agent.py        # Main ReAct agent
├── llm_integration.py    # LLM provider interfaces
├── simple_demo.py        # Quick demo script
├── example_usage.py      # Comprehensive examples
└── README.md            # This file
```

## Future Enhancements

Potential improvements:
- Memory/conversation history
- Multi-tool parallel execution
- Plan generation before execution
- Error recovery strategies
- Streaming LLM responses
- Agent benchmarking suite

## License

MIT License

## Contributing

Contributions welcome! Areas of interest:
- Additional LLM providers
- Better reasoning strategies
- More sophisticated demo tasks
- Performance optimizations
