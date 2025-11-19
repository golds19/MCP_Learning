# Reading Order Guide
## How to Understand the Multi-Server ReAct Agent Implementation

This guide will walk you through the codebase in the optimal order to understand how everything works together. Follow this path to learn the implementation step-by-step.

---

## 🎯 Learning Objectives

By following this guide, you'll understand:
1. How ReAct agents work (Reasoning + Acting)
2. How MCP (Model Context Protocol) enables multi-tool systems
3. How to connect to multiple MCP servers simultaneously
4. How to route tools to the correct servers
5. How to coordinate actions across different systems
6. How to build a complete appointment scheduling system

---

## 📚 Reading Order

### Phase 1: Understand the Foundation (30 minutes)

#### 1. Start Here: `RESULT.md`
**Why:** High-level overview of what was built
**Focus on:**
- Overview section - what the system does
- Architecture diagram - how components connect
- Available tools - what the agent can do

**Key Concepts:**
- Multi-server architecture
- Tool routing
- Cross-server coordination

---

#### 2. Read: `db_schema/appointments_schema.sql`
**Why:** Understand the data model
**Focus on:**
- `appointments` table structure (lines 6-29)
- `sync_log` table for audit trail (lines 38-49)
- Indexes for performance (lines 52-61)

**Key Concepts:**
- Database schema design
- Linking calendar events with database records via `google_event_id`
- Sync status tracking

**Exercise:** Visualize how an appointment looks in the database:
```
id: 1
title: "Appointment with Dr. Smith"
start_datetime: "2025-11-25T14:00:00"
google_event_id: "abc123xyz"
synced_to_calendar: 1
```

---

### Phase 2: Understand Single-Server Agent (45 minutes)

#### 3. Read: `agent/react_agent.py` (skip for now, read key parts)
**Why:** Understand the base ReAct pattern
**Focus on:**
- `Step` dataclass (lines ~15-25) - represents one reasoning cycle
- `AgentState` enum (lines ~10-15) - agent states
- `ReActAgent.__init__` (lines ~40-60) - initialization
- `ReActAgent.run()` (lines ~180-260) - main execution loop

**Key Concepts:**
- **ReAct Loop:** Think → Act → Observe → Repeat
- **LLM Integration:** How the agent uses AI to reason
- **Tool Execution:** How actions are performed

**The Core Loop:**
```python
for iteration in range(max_iterations):
    # 1. THINK: Generate reasoning
    prompt = self._reason(task, context)
    response = await llm_callback(prompt)

    # 2. Parse response
    thought, action, action_input = self._parse_thought_action(response)

    # 3. ACT: Execute action
    observation = await self._execute_action(action, action_input)

    # 4. Store step
    steps.append(Step(thought, action, observation))

    # 5. Check if done
    if finished:
        break
```

**Exercise:** Trace a simple execution:
1. Agent thinks: "I need to list tables"
2. Agent acts: `list_tables`
3. Agent observes: "Found 2 tables: appointments, sync_log"
4. Agent thinks: "Task complete"

---

### Phase 3: Understand Multi-Server Extension (1 hour)

#### 4. Read: `agent/server_config.py`
**Why:** Learn how to configure multiple servers
**Read in order:**

**a) `ServerConfig` dataclass (lines ~10-35)**
```python
@dataclass
class ServerConfig:
    name: str        # Identifier: "sqlite" or "google_calendar"
    command: str     # Executable: "python" or "npx"
    args: List[str]  # Arguments: ["server.py"] or ["@cocal/..."]
    env: Dict        # Environment variables (for OAuth)
```

**b) Helper functions (lines ~38-85)**
- `create_sqlite_config()` - Quick SQLite setup
- `create_google_calendar_config()` - Quick Google Calendar setup

**Key Concepts:**
- Configuration abstraction
- Different servers use different runtimes (Python vs Node.js)
- Environment variables for credentials

**Exercise:** Write your own server config:
```python
ServerConfig(
    name="my_server",
    command="python",
    args=["path/to/server.py"],
    env={"API_KEY": "secret"}
)
```

---

#### 5. Read: `agent/multi_server_agent.py` ⭐ **MOST IMPORTANT**
**Why:** This is the core of the multi-server system
**Read in this order:**

**a) Class structure (lines ~20-50)**
```python
class MultiServerReActAgent(ReActAgent):
    def __init__(self, server_configs: List[ServerConfig], ...):
        self.server_configs = server_configs
        self.sessions = {}        # server_name -> ClientSession
        self.all_tools = {}       # tool_name -> server_name
        self.server_tools = {}    # server_name -> list of tools
```

**Understanding:**
- Extends single-server `ReActAgent`
- Manages multiple `ClientSession` objects
- Maps tools to servers

**b) Session initialization (lines ~52-120)**
```python
async def initialize_sessions(self):
    for config in self.server_configs:
        # 1. Create server parameters
        server_params = StdioServerParameters(...)

        # 2. Establish stdio connection
        read, write = await stdio_client(server_params).__aenter__()

        # 3. Create MCP session
        session = await ClientSession(read, write).__aenter__()
        self.sessions[config.name] = session

        # 4. Get tools from this server
        tools = await session.list_tools()

        # 5. Map tool names to server
        for tool in tools:
            self.all_tools[tool.name] = config.name
```

**Key Concepts:**
- **Stdio communication:** MCP uses stdin/stdout
- **Session management:** One session per server
- **Tool discovery:** Ask each server what tools it has
- **Tool mapping:** Build a lookup table

**Exercise:** Trace initialization with 2 servers:
```
Server 1 (sqlite):
  - Connect via Python subprocess
  - Get tools: [create_table, insert_record, ...]
  - Map: create_table -> "sqlite"

Server 2 (google_calendar):
  - Connect via NPX subprocess
  - Get tools: [create-event, list-calendars, ...]
  - Map: create-event -> "google_calendar"

Result:
  sessions = {
    "sqlite": ClientSession(...),
    "google_calendar": ClientSession(...)
  }
  all_tools = {
    "create_table": "sqlite",
    "create-event": "google_calendar",
    ...
  }
```

**c) Tool routing (lines ~140-160)**
```python
def _route_tool_to_server(self, tool_name: str) -> str:
    """Find which server has this tool."""
    return self.all_tools.get(tool_name)

async def _execute_action(self, action: str, action_input: Dict) -> str:
    # 1. Route to correct server
    server_name = self._route_tool_to_server(action)

    # 2. Get that server's session
    session = self.sessions[server_name]

    # 3. Execute on that server
    result = await session.call_tool(action, arguments=action_input)
    return result.content[0].text
```

**Key Concepts:**
- **Tool routing:** Use the mapping to find the right server
- **Session selection:** Get the correct MCP session
- **Execution:** Call the tool on that server

**Exercise:** Trace a tool call:
```
Action: "create-event"
Input: {"summary": "Meeting"}

1. Route: all_tools["create-event"] = "google_calendar"
2. Session: sessions["google_calendar"]
3. Execute: session.call_tool("create-event", {...})
4. Result: "Event created, ID: abc123"
```

**d) Main execution loop (lines ~165-250)**
- Almost identical to single-server agent
- Main difference: `_execute_action` now routes to servers

**Key Insight:** The multi-server agent extends the base agent with:
1. Multiple session management
2. Tool routing logic
3. That's it! The ReAct loop stays the same.

---

### Phase 4: Understand Complete Workflow (45 minutes)

#### 6. Read: `agent/demos/appointment_demo.py`
**Why:** See how everything works together
**Read in order:**

**a) Setup (lines ~1-50)**
- Imports and configuration
- Server setup

**b) `demo_basic_scheduling()` (lines ~52-180)**
**Focus on:**

1. **Server configuration (lines ~70-95)**
```python
servers = [
    ServerConfig("sqlite", "python", ["sqlite_server.py"]),
    create_google_calendar_config()
]
```

2. **Agent creation (lines ~97-105)**
```python
agent = MultiServerReActAgent(
    server_configs=servers,
    max_iterations=10,
    verbose=True
)
```

3. **MockLLM responses (lines ~107-155)**
- See predefined agent responses
- Understand the workflow sequence

4. **Agent execution (lines ~160-175)**
```python
result = await agent.run(task, llm_callback=mock_callback)
```

**Key Workflow:**
```
Step 1: describe_table (SQLite)
  → Check appointments table exists

Step 2: list-calendars (Google Calendar)
  → Get available calendars

Step 3: create-event (Google Calendar)
  → Create appointment in calendar
  → Get event ID: "abc123"

Step 4: insert_record (SQLite)
  → Save to database with event ID
  → Link both systems

Step 5: read_records (SQLite)
  → Verify appointment saved

Step 6: FINISH
  → Task complete
```

**Exercise:** Modify the demo to:
1. Change the appointment time
2. Add a different type of appointment
3. Query appointments differently

---

### Phase 5: Understand LLM Integration (30 minutes)

#### 7. Read: `agent/llm_integration.py`
**Why:** Understand how AI reasoning works
**Read in order:**

**a) `LLMProvider` base class (lines ~10-20)**
- Abstract interface for all LLM providers

**b) `MockLLMProvider` (lines ~120-145)**
**Most important for understanding:**
```python
class MockLLMProvider(LLMProvider):
    def __init__(self):
        self.responses = []
        self.call_count = 0

    def add_response(self, response: str):
        """Add predefined response."""
        self.responses.append(response)

    async def generate(self, prompt: str) -> str:
        """Return next predefined response."""
        response = self.responses[self.call_count]
        self.call_count += 1
        return response
```

**Key Insight:** MockLLM simulates AI reasoning with pre-written responses. Replace with real LLM for actual AI.

**c) Real LLM providers (lines ~30-110)**
- `OpenAIProvider` - GPT-4 integration
- `OllamaProvider` - Local LLM integration

**Exercise:** Compare MockLLM vs Real LLM:
```python
# Mock: Predefined
mock = MockLLMProvider()
mock.add_response("Thought: I should do X\nAction: Y")

# Real: AI-generated
openai = OpenAIProvider(api_key="...")
response = await openai.generate(prompt)  # AI decides
```

---

### Phase 6: Understand the Streamlit App (30 minutes)

#### 8. Read: `streamlit_app.py`
**Why:** See how to build a UI for the agent
**Focus on:**

**a) Configuration UI (lines ~30-80)**
- Server selection checkboxes
- LLM provider dropdown
- Settings sliders

**b) `run_agent()` function (lines ~120-180)**
- Server setup
- Agent creation
- Task execution
- Same pattern as demo, but in UI

**c) Execution and display (lines ~240-300)**
- Execute button handler
- Result display
- Step-by-step visualization

**Key Concepts:**
- Streamlit for rapid UI development
- Async execution in Streamlit
- Real-time agent output display

---

## 🧠 Key Concepts Summary

### 1. ReAct Pattern
```
THINK (Reasoning) → ACT (Tool Use) → OBSERVE (Results) → Repeat
```

### 2. MCP (Model Context Protocol)
- Standard protocol for AI-tool communication
- Servers expose tools via MCP
- Clients (agents) use tools via MCP
- Language agnostic (Python ↔ Node.js works)

### 3. Multi-Server Architecture
```
Agent → Routes to Server 1 (SQLite) → Tool A
      → Routes to Server 2 (Calendar) → Tool B
```

### 4. Tool Routing
```
tool_name → lookup in mapping → server_name → execute on session
```

### 5. Cross-Server Coordination
```
1. Create in Calendar → get ID
2. Save to Database → use ID from step 1
3. Both systems linked
```

---

## 🔧 How to Replicate This in Your Projects

### Step 1: Start with Single Server
1. Build a single MCP server (e.g., SQLite)
2. Create a basic ReAct agent
3. Get the agent working with one server

### Step 2: Add Multi-Server Support
1. Create `ServerConfig` for configuration
2. Extend agent to manage multiple sessions
3. Implement tool routing logic
4. Test with 2+ servers

### Step 3: Add Real LLM
1. Integrate OpenAI or Ollama
2. Design prompts for your use case
3. Test reasoning quality

### Step 4: Build UI
1. Start with command-line demo
2. Add Streamlit UI
3. Add error handling and logging

---

## 📝 Practice Exercises

### Exercise 1: Add a New Tool
Add a "search appointments by date" tool to SQLite server.

**Steps:**
1. Add tool definition in `sqlite_server.py`
2. Test that multi-server agent picks it up
3. Use it in a demo

### Exercise 2: Add a Third Server
Add a third MCP server (e.g., email notifications).

**Steps:**
1. Create the MCP server
2. Add ServerConfig
3. Add to agent configuration
4. Test tool routing with 3 servers

### Exercise 3: Custom Workflow
Create a workflow that:
1. Checks calendar for conflicts
2. If no conflict, create appointment
3. If conflict, suggest alternative times

**Hint:** This requires chaining multiple tools.

---

## 🐛 Common Debugging Points

### Issue 1: Tool Not Found
**Check:**
- Tool name spelling
- Server initialized correctly
- Tool mapping built

### Issue 2: Wrong Server
**Check:**
- Tool routing logic
- Server name in mapping
- Case sensitivity

### Issue 3: Session Error
**Check:**
- Server process running
- Stdio connection established
- Session initialized

---

## 📚 Advanced Topics (Beyond This Implementation)

Once you understand the basics, explore:

1. **Error Recovery:** Rollback on failure
2. **Parallel Tool Execution:** Execute multiple tools simultaneously
3. **Dynamic Tool Discovery:** Add servers at runtime
4. **Conversation Memory:** Multi-turn conversations
5. **Tool Chaining:** Automatic dependency resolution
6. **Observability:** Logging, tracing, monitoring

---

## ✅ Checklist: You Understand It When...

- [ ] Can explain ReAct pattern to someone
- [ ] Can trace a tool call from agent to server
- [ ] Can add a new tool to existing server
- [ ] Can add a new server to the agent
- [ ] Can modify the workflow in demo
- [ ] Can debug routing issues
- [ ] Can add new LLM provider
- [ ] Can build a simple UI for your agent

---

## 🎓 Learning Path Complete!

You've now learned:
1. ✅ ReAct agent architecture
2. ✅ MCP protocol basics
3. ✅ Multi-server coordination
4. ✅ Tool routing implementation
5. ✅ Real-world application (appointment scheduling)

**Next Steps:**
- Build your own multi-server agent
- Add more tools and servers
- Integrate with real LLMs
- Build production-ready features

---

## 📖 Quick Reference Card

```
File Reading Order:
1. RESULT.md              (Overview)
2. appointments_schema.sql (Data model)
3. react_agent.py         (Base agent)
4. server_config.py       (Configuration)
5. multi_server_agent.py  (Multi-server ⭐)
6. appointment_demo.py    (Complete example)
7. llm_integration.py     (AI reasoning)
8. streamlit_app.py       (UI)

Key Classes:
- ReActAgent              (Base agent)
- MultiServerReActAgent   (Multi-server extension)
- ServerConfig            (Server configuration)
- LLMProvider             (AI interface)

Key Concepts:
- ReAct loop (Think → Act → Observe)
- Tool routing (tool_name → server_name)
- MCP protocol (stdio communication)
- Cross-server coordination
```

---

Good luck building your own multi-server agents! 🚀
