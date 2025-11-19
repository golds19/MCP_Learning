# Google Calendar + SQLite Multi-Tool ReAct Agent
## Integration Plan & Architecture

---

## Executive Summary

**Goal:** Extend the ReAct agent to use BOTH SQLite database AND Google Calendar MCP servers simultaneously to handle appointment scheduling commands.

**Use Case:**
```
User: "Schedule appointment with Dr. Smith next Tuesday at 2pm"

Agent Actions:
1. Parse the natural language command
2. CREATE event in Google Calendar
3. SAVE appointment details to SQLite database
4. Return confirmation to user
```

---

## 1. Third-Party Google Calendar MCP Server Selection

### Recommended Option: `nspady/google-calendar-mcp` ⭐

**Repository:** https://github.com/nspady/google-calendar-mcp
**NPM Package:** @cocal/google-calendar-mcp

**Why This One?**
- ✅ **NPX Installation** - Easiest setup, no repository cloning needed
- ✅ **Intelligent Import** 🔥 - Create events from screenshots, PDFs, web links
- ✅ **Search Events** - Find events by text query
- ✅ **Event Colors** - Color-coded event support
- ✅ **Professional Package** - Published to NPM, well-maintained
- ✅ **Natural Language** - Built-in date/time parsing
- ✅ **Language Agnostic** - Node.js server works perfectly with Python agent via MCP

**Note:** While this is a Node.js/TypeScript server and our agent is Python, MCP is designed for multi-language interoperability. The agent communicates via stdio (JSON over stdin/stdout), so the language difference is irrelevant.

**Alternative:** `guinacio/mcp-google-calendar` (Python-based, simpler but fewer features)

### Available Tools from Google Calendar MCP Server

```javascript
Tools = [
    "list-calendars",        # List all available calendars
    "list-events",          # Get events with date filtering
    "search-events",        # Search events by text query (🔥 NEW)
    "create-event",         # Create new calendar events (supports intelligent import)
    "update-event",         # Modify existing events
    "delete-event",         # Remove events
    "get-freebusy",        # Check availability across calendars
    "list-colors"          # Get available event colors (🔥 NEW)
]
```

---

## 2. Multi-MCP Server Architecture

### Current Architecture (Single Server)
```
┌─────────────────┐
│  ReAct Agent    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  MCP Client     │
│  Session        │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│ SQLite MCP      │
│ Server          │
│ (8 tools)       │
└─────────────────┘
```

### New Architecture (Multi-Server)
```
┌─────────────────────────────────────────┐
│         ReAct Agent                     │
│  - Multi-server session manager         │
│  - Tool routing logic                   │
│  - Cross-server coordination            │
└──────────┬──────────────────────────────┘
           │
     ┌─────┴─────┐
     │           │
     ↓           ↓
┌─────────┐ ┌─────────────┐
│ MCP     │ │ MCP         │
│ Session │ │ Session     │
│ #1      │ │ #2          │
└────┬────┘ └─────┬───────┘
     │            │
     ↓            ↓
┌─────────┐ ┌──────────────┐
│ SQLite  │ │ Google Cal   │
│ MCP     │ │ MCP Server   │
│ Server  │ │              │
│(8 tools)│ │(8 tools)     │
└─────────┘ └──────────────┘
```

### Key Components to Modify

#### A. `MultiServerReActAgent` Class
```python
class MultiServerReActAgent(ReActAgent):
    """
    Enhanced ReAct agent that can connect to multiple MCP servers.
    """

    def __init__(self, server_configs: List[ServerConfig], ...):
        self.server_configs = server_configs
        self.sessions = {}  # server_name -> ClientSession
        self.all_tools = {}  # tool_name -> server_name
```

#### B. `ServerConfig` Dataclass
```python
@dataclass
class ServerConfig:
    name: str              # "sqlite" or "google_calendar"
    script_path: str       # Path to MCP server script
    command: str = "python"
    args: Optional[List[str]] = None
    env: Optional[Dict] = None
```

---

## 3. Database Schema for Appointments

### Tables to Create

#### `appointments` Table
```sql
CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Event Details
    title TEXT NOT NULL,
    description TEXT,
    location TEXT,

    -- Timing
    start_datetime TEXT NOT NULL,  -- ISO 8601 format
    end_datetime TEXT NOT NULL,
    timezone TEXT DEFAULT 'UTC',

    -- Calendar Integration
    google_event_id TEXT UNIQUE,   -- Link to Google Calendar event
    calendar_id TEXT,              -- Which Google calendar

    -- Attendees
    attendees TEXT,                -- JSON array of attendee emails

    -- Status
    status TEXT DEFAULT 'confirmed', -- confirmed, cancelled, tentative

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Sync Status
    synced_to_calendar BOOLEAN DEFAULT 0,
    last_sync_at TIMESTAMP
);
```

#### `sync_log` Table (Optional - for debugging)
```sql
CREATE TABLE sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id INTEGER,
    action TEXT,  -- 'create', 'update', 'delete'
    status TEXT,  -- 'success', 'failed'
    error_message TEXT,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(id)
);
```

---

## 4. Tool Coordination Strategy

### Scenario: "Schedule appointment with Dr. Smith next Tuesday at 2pm"

#### Step-by-Step Agent Flow

```
ITERATION 1: Parse & Validate
├─ Thought: "I need to parse this natural language command and
│           extract: title, date/time, attendees"
├─ Action: get-current-date (Google Calendar tool)
└─ Observation: "2025-11-19 10:30:00 PST"

ITERATION 2: Calculate Exact Date/Time
├─ Thought: "Next Tuesday from 2025-11-19 is 2025-11-25.
│           Time is 14:00. Need to create event."
├─ Action: create-event (Google Calendar tool)
├─ Input: {
│   "summary": "Appointment with Dr. Smith",
│   "start": "2025-11-25T14:00:00",
│   "end": "2025-11-25T15:00:00"
│ }
└─ Observation: "Event created successfully. Event ID: abc123xyz"

ITERATION 3: Save to Database
├─ Thought: "Event created in calendar. Now save to database
│           for record keeping."
├─ Action: insert_record (SQLite tool)
├─ Input: {
│   "table_name": "appointments",
│   "data": {
│     "title": "Appointment with Dr. Smith",
│     "start_datetime": "2025-11-25T14:00:00",
│     "end_datetime": "2025-11-25T15:00:00",
│     "google_event_id": "abc123xyz",
│     "synced_to_calendar": 1
│   }
│ }
└─ Observation: "Record inserted successfully. Row ID: 42"

ITERATION 4: Confirm
├─ Thought: "Both calendar and database updated. Task complete."
├─ Action: FINISH
└─ Final Answer: "Appointment with Dr. Smith scheduled for
                  Tuesday, November 25, 2025 at 2:00 PM"
```

### Tool Routing Logic

```python
def _route_tool_to_server(self, tool_name: str) -> str:
    """Determine which server to use for a given tool."""
    return self.all_tools.get(tool_name)

async def _execute_action(self, action: str, action_input: Dict) -> str:
    """Execute action on the correct MCP server."""
    server_name = self._route_tool_to_server(action)

    if not server_name:
        return f"Error: Unknown tool {action}"

    session = self.sessions[server_name]
    result = await session.call_tool(action, arguments=action_input)
    return result.content[0].text
```

---

## 5. Natural Language Date/Time Parsing

### Challenge
Input: "next Tuesday at 2pm"
Output: "2025-11-25T14:00:00"

### Solution Options

#### Option A: Use LLM for Parsing (Recommended)
- Let the LLM reason about dates
- Use `get-current-date` tool to get reference point
- LLM calculates the exact ISO 8601 datetime

#### Option B: Add `dateparser` Library
```python
import dateparser
from datetime import datetime

def parse_natural_date(text: str, reference_date: datetime) -> str:
    """Parse natural language dates."""
    parsed = dateparser.parse(
        text,
        settings={
            'RELATIVE_BASE': reference_date,
            'PREFER_DATES_FROM': 'future'
        }
    )
    return parsed.isoformat()
```

#### Option C: Create a Date Parsing MCP Tool
- Add a new tool to SQLite server: `parse_date`
- Input: natural language date
- Output: ISO 8601 datetime

**Recommendation:** Use **Option A** (LLM reasoning) as it's most flexible and doesn't require additional dependencies.

---

## 6. Google Calendar Authentication Setup (nspady server)

### Setup Steps

#### 1. Google Cloud Console Setup
```
1. Go to: https://console.cloud.google.com/
2. Create new project (or select existing)
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
   - Application type: Desktop app
   - Download credentials JSON file
```

#### 2. Environment Configuration
The nspady server uses environment variables for credentials:

```bash
# Option A: Export the entire credentials JSON
export GOOGLE_OAUTH_CREDENTIALS='{"installed":{"client_id":"your-id.apps.googleusercontent.com","project_id":"your-project","auth_uri":"https://accounts.google.com/o/oauth2/auth",...}}'

# Option B: Store in a file and reference it
export GOOGLE_OAUTH_CREDENTIALS_PATH="/path/to/credentials.json"
```

#### 3. File Structure (Updated for NPX)
```
project/
├── mcp_server/
│   └── sqlite_server.py           # Your SQLite MCP server
│
├── agent/
│   ├── react_agent.py             # Existing agent
│   ├── multi_server_agent.py      # NEW - Multi-server agent
│   ├── server_config.py           # NEW - Server configurations
│   └── demos/
│       └── appointment_demo.py    # NEW - Demo script
│
├── .env                           # Environment variables
└── node_modules/                  # Auto-created by NPX (can ignore)
```

**Note:** No need to clone the nspady repository! NPX handles it automatically.

#### 4. First-Time Authentication Flow
```
1. User runs: python agent/demos/appointment_demo.py
2. MultiServerReActAgent starts both servers:
   - SQLite server (Python subprocess)
   - Google Calendar server (NPX subprocess)
3. On first run, browser opens automatically
4. User logs into Google account
5. User grants calendar permissions
6. Token is saved to system cache
7. Future runs use cached token (no browser needed)
```

#### 5. Production Mode Setup (Optional, but Recommended)
To avoid 7-day token expiration in test mode:

```
1. In Google Cloud Console:
   - Go to "OAuth consent screen"
   - Click "Publish App"
   - Submit for verification (if needed)
2. Once published, tokens won't expire weekly
```

---

## 7. Implementation Roadmap

### Phase 1: Setup Google Calendar MCP Server (Day 1)
```
□ Install Node.js (if not already installed)
□ Set up Google Cloud credentials (OAuth 2.0 Desktop App)
□ Configure environment variables (GOOGLE_OAUTH_CREDENTIALS)
□ Test nspady server via NPX: npx @cocal/google-calendar-mcp
□ Complete OAuth authentication flow
□ Verify all 8 tools work correctly (list-calendars, create-event, etc.)
□ Test intelligent import feature with a screenshot
```

### Phase 2: Create Multi-Server Agent (Day 2)
```
□ Create ServerConfig dataclass
□ Implement MultiServerReActAgent class
□ Add multi-session initialization
□ Implement tool routing logic
□ Add session cleanup for multiple servers
□ Create comprehensive error handling
```

### Phase 3: Database Schema (Day 2)
```
□ Design appointments table
□ Create schema migration script
□ Add sync_log table
□ Create helper functions for CRUD on appointments
□ Test database operations
```

### Phase 4: Integration & Testing (Day 3)
```
□ Test multi-server connection
□ Test tool routing
□ Test cross-server workflows
□ Add logging and monitoring
□ Create demo scripts
```

### Phase 5: Natural Language Enhancement (Day 4)
```
□ Implement date/time parsing strategy
□ Add prompt engineering for appointment scheduling
□ Test various natural language inputs
□ Handle edge cases (timezone, all-day events, etc.)
```

### Phase 6: Advanced Features (Day 5+)
```
□ Sync existing calendar events to DB
□ Update events (both calendar and DB)
□ Delete events (both calendar and DB)
□ Conflict detection
□ Recurring events support
□ Email reminders
```

---

## 8. Code Structure Changes

### New Files to Create

```
agent/
├── multi_server_agent.py          # MultiServerReActAgent class
├── server_config.py               # ServerConfig dataclass
├── tool_router.py                 # Tool routing logic
├── date_parser.py                 # Date parsing utilities (optional)
└── demos/
    ├── appointment_demo.py        # Appointment scheduling demo
    └── multi_tool_demo.py         # Multi-server demo

mcp_server/
└── sqlite_server.py               # Your existing SQLite MCP server
                                   # (No google_calendar folder needed - NPX handles it!)

db_schema/
├── appointments_schema.sql        # SQL schema
└── setup_database.py             # Database initialization script

.env                               # Environment variables for Google OAuth
```

**Note:** No need to create a google_calendar folder! The nspady server is installed and run via NPX automatically.

---

## 9. Example Usage

### Simple Appointment Scheduling

```python
import os
from agent.multi_server_agent import MultiServerReActAgent
from agent.server_config import ServerConfig

# Configure servers
servers = [
    ServerConfig(
        name="sqlite",
        command="python",
        args=["../mcp_server/sqlite_server.py"]
    ),
    ServerConfig(
        name="google_calendar",
        command="npx",  # Using NPX to run the nspady server
        args=["@cocal/google-calendar-mcp"],
        env={
            "GOOGLE_OAUTH_CREDENTIALS": os.getenv("GOOGLE_OAUTH_CREDENTIALS")
        }
    )
]

# Create multi-server agent
agent = MultiServerReActAgent(
    server_configs=servers,
    max_iterations=10,
    verbose=True
)

# Run task
task = "Schedule appointment with Dr. Smith next Tuesday at 2pm"
result = await agent.run(task, llm_callback=llm_callback)
```

### Advanced: Sync All Calendar Events to Database

```python
task = """
1. Get all events from my Google Calendar for the next 30 days
2. For each event, check if it exists in the appointments table
3. If not, create a new record in the database
4. Return summary of how many events were synced
"""

result = await agent.run(task, llm_callback=llm_callback)
```

---

## 10. Challenges & Solutions

### Challenge 1: Tool Name Conflicts
**Problem:** Both servers might have similar tool names
**Solution:** Namespace tools with server name
```python
# Instead of: "create_table"
# Use: "sqlite.create_table" and "google_calendar.create-event"
```

### Challenge 2: Authentication Interruption
**Problem:** OAuth flow interrupts agent execution
**Solution:** Pre-authenticate before starting agent
```python
async def ensure_authenticated():
    """Run authentication check before agent starts."""
    # Test connection to Google Calendar
    # If token.json missing, trigger OAuth flow
    # Wait for completion before proceeding
```

### Challenge 3: Transaction Consistency
**Problem:** Event created in calendar but DB insert fails
**Solution:** Implement rollback mechanism
```python
try:
    # Create calendar event
    event_id = await create_calendar_event(...)

    # Save to database
    await insert_to_db(event_id=event_id)

except Exception as e:
    # Rollback: delete calendar event
    await delete_calendar_event(event_id)
    raise
```

### Challenge 4: Timezone Handling
**Problem:** User in different timezone than calendar default
**Solution:** Always use explicit timezone information
```python
# Get user's timezone first
timezone = await session.call_tool("get-timezone-info")

# Use it in all datetime operations
start_time = f"2025-11-25T14:00:00{timezone}"
```

---

## 11. Testing Strategy

### Unit Tests
```python
# test_multi_server_agent.py
async def test_connect_to_multiple_servers():
    """Test simultaneous connection to both servers."""
    agent = MultiServerReActAgent(server_configs)
    await agent.initialize_sessions()
    assert len(agent.sessions) == 2
    assert "sqlite" in agent.sessions
    assert "google_calendar" in agent.sessions

async def test_tool_routing():
    """Test correct tool routing to servers."""
    agent = MultiServerReActAgent(server_configs)

    assert agent._route_tool_to_server("create_table") == "sqlite"
    assert agent._route_tool_to_server("create-event") == "google_calendar"
```

### Integration Tests
```python
async def test_appointment_creation_flow():
    """Test full appointment creation workflow."""
    task = "Create appointment: Team Meeting on Dec 1 at 3pm"
    result = await agent.run(task)

    # Verify event in Google Calendar
    events = await get_calendar_events(start_date="2025-12-01")
    assert any("Team Meeting" in e.summary for e in events)

    # Verify record in database
    records = await query_db("SELECT * FROM appointments WHERE title LIKE '%Team Meeting%'")
    assert len(records) == 1
    assert records[0]['google_event_id'] is not None
```

---

## 12. Security Considerations

### OAuth Token Security
```python
# Store tokens securely
TOKEN_PATH = os.path.join(os.path.expanduser("~"), ".mcp_tokens", "google_calendar.json")

# Set proper file permissions (Unix)
os.chmod(TOKEN_PATH, 0o600)
```

### Database Security
```python
# Use parameterized queries (already implemented)
# Never store credentials in database
# Encrypt sensitive appointment data if needed
```

### Environment Variables
```bash
# .env file
GOOGLE_CALENDAR_CREDENTIALS_PATH=/path/to/credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=/path/to/token.json
DATABASE_PATH=/path/to/appointments.db
```

---

## 13. Next Steps

### Immediate Actions
1. ✅ Complete this plan document
2. ⏳ Get user approval on approach
3. ⏳ Clone and test Google Calendar MCP server
4. ⏳ Implement MultiServerReActAgent
5. ⏳ Create database schema
6. ⏳ Build demo

### Questions for User
1. Do you already have Google Cloud credentials, or need help setting that up?
2. Should we handle recurring appointments (daily, weekly, monthly)?
3. Do you want email reminders/notifications?
4. Should we support multiple Google calendars or just the primary one?
5. Do you want bi-directional sync (calendar → DB and DB → calendar)?

---

## 14. Estimated Timeline

```
Week 1:
  Day 1-2: Setup Google Calendar MCP server + authentication
  Day 3-4: Implement MultiServerReActAgent
  Day 5:   Create database schema and test

Week 2:
  Day 1-2: Integration testing
  Day 3:   Demo creation and documentation
  Day 4-5: Advanced features and edge cases
```

---

## 15. Success Criteria

The integration is successful when:

- ✅ Agent connects to BOTH SQLite and Google Calendar servers
- ✅ Agent can route tools to correct servers
- ✅ User can schedule appointments via natural language
- ✅ Events are created in Google Calendar
- ✅ Appointment data is saved to SQLite database
- ✅ Both systems stay in sync
- ✅ Proper error handling and rollback
- ✅ OAuth authentication works smoothly
- ✅ Comprehensive demo works end-to-end

---

**END OF PLAN**
