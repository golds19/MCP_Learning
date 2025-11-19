# Quick Start Guide: Multi-Tool ReAct Agent
## SQLite + Google Calendar Integration

This is a simplified guide to get you started quickly.

---

## What You're Building

An AI agent that can:
```
Input:  "Schedule appointment with Dr. Smith next Tuesday at 2pm"

Output:
  ✓ Event created in Google Calendar
  ✓ Appointment saved in SQLite database
  ✓ Confirmation message
```

---

## Prerequisites

1. **Python 3.8+** installed
2. **Google Cloud account** (free tier works)
3. **MCP library** (`pip install mcp`)
4. **LLM access** (OpenAI API key or Ollama running locally)

---

## Setup Steps (30 minutes)

### Step 1: Google Cloud Setup (10 min)

1. Go to https://console.cloud.google.com/
2. Create a new project (e.g., "Calendar Agent")
3. Enable Google Calendar API:
   - Search for "Google Calendar API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "Credentials" → "Create Credentials" → "OAuth client ID"
   - Choose "Desktop app"
   - Download JSON file
   - Save as `credentials.json`

### Step 2: Install Google Calendar MCP Server (10 min)

```bash
cd mcp_server
mkdir google_calendar
cd google_calendar

# Clone the MCP server
git clone https://github.com/guinacio/mcp-google-calendar.git .

# Install dependencies
pip install -e .

# Copy your credentials
cp /path/to/downloaded/credentials.json ./credentials.json
```

### Step 3: Test Google Calendar Server (5 min)

```bash
# Run the server directly to authenticate
python server.py

# This will:
# 1. Open your browser
# 2. Ask you to log in to Google
# 3. Grant calendar permissions
# 4. Save token.json automatically
```

### Step 4: Setup Database Schema (5 min)

```bash
cd ../../
python db_schema/setup_database.py

# This creates the appointments table in your SQLite database
```

---

## File Structure

After setup, your project should look like:

```
task-manager-mcp/
├── mcp_server/
│   ├── sqlite_server.py              # Already exists
│   └── google_calendar/
│       ├── server.py                 # Cloned
│       ├── credentials.json          # You created
│       └── token.json                # Auto-generated
│
├── agent/
│   ├── react_agent.py                # Already exists
│   ├── multi_server_agent.py         # We'll create
│   └── demos/
│       └── appointment_demo.py       # We'll create
│
├── db_schema/
│   ├── appointments_schema.sql       # We'll create
│   └── setup_database.py             # We'll create
│
├── INTEGRATION_PLAN.md               # Full plan
└── QUICK_START_GUIDE.md             # This file
```

---

## Running Your First Multi-Tool Task

```bash
cd agent
python demos/appointment_demo.py
```

Example interaction:
```
> Schedule a dentist appointment next Monday at 10am

Agent thinking...
✓ Getting current date from Google Calendar
✓ Creating event in Google Calendar
✓ Saving appointment to database
✓ Done!

Appointment scheduled:
- Title: Dentist Appointment
- Date: November 24, 2025
- Time: 10:00 AM
- Google Event ID: abc123xyz
- Database Record ID: 1
```

---

## Architecture Overview

```
┌────────────────────────────────────────┐
│   User Input (Natural Language)       │
│  "Schedule appointment next Tuesday"  │
└─────────────────┬──────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│      Multi-Server ReAct Agent          │
│  ┌─────────────────────────────────┐   │
│  │ 1. THINK: Parse the request     │   │
│  │ 2. ACT: Use appropriate tools   │   │
│  │ 3. OBSERVE: Check results       │   │
│  │ 4. REPEAT: Until task complete  │   │
│  └─────────────────────────────────┘   │
└──────────┬──────────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ↓             ↓
┌─────────┐  ┌──────────────┐
│ SQLite  │  │ Google Cal   │
│ MCP     │  │ MCP Server   │
│ Server  │  │              │
└────┬────┘  └──────┬───────┘
     │              │
     ↓              ↓
┌─────────┐  ┌──────────────┐
│ SQLite  │  │ Google       │
│ Database│  │ Calendar API │
└─────────┘  └──────────────┘
```

---

## How It Works

### Example: "Schedule appointment with Dr. Smith next Tuesday at 2pm"

**Iteration 1: Get Current Date**
```
Thought: Need to know what date "next Tuesday" is
Action: get-current-date (Google Calendar)
Observation: "2025-11-19 10:30:00 PST"
```

**Iteration 2: Create Calendar Event**
```
Thought: Next Tuesday is 2025-11-25. Create event at 14:00
Action: create-event (Google Calendar)
Input: {
  "summary": "Appointment with Dr. Smith",
  "start": "2025-11-25T14:00:00-08:00",
  "end": "2025-11-25T15:00:00-08:00"
}
Observation: "Event created. ID: abc123xyz"
```

**Iteration 3: Save to Database**
```
Thought: Event created. Now save to database for records
Action: insert_record (SQLite)
Input: {
  "table_name": "appointments",
  "data": {
    "title": "Appointment with Dr. Smith",
    "start_datetime": "2025-11-25T14:00:00",
    "google_event_id": "abc123xyz",
    "synced_to_calendar": true
  }
}
Observation: "Record inserted. Row ID: 1"
```

**Iteration 4: Finish**
```
Thought: Both systems updated. Task complete!
Action: FINISH
```

---

## Key Concepts

### 1. Multi-Server Sessions
The agent maintains **two simultaneous MCP connections**:
- One to SQLite server
- One to Google Calendar server

### 2. Tool Routing
The agent knows which tools belong to which server:
```python
sqlite_tools = [
    "create_table", "insert_record", "read_records",
    "update_record", "delete_record", "list_tables",
    "describe_table", "execute_query"
]

google_calendar_tools = [
    "list-calendars", "get-events", "create-event",
    "update-event", "delete-event", "check-availability",
    "get-timezone-info", "get-current-date"
]
```

### 3. Cross-Tool Coordination
The agent can use output from one tool as input to another:
```python
# Step 1: Get event ID from Google Calendar
event_id = create_event(...)

# Step 2: Use event ID in database
insert_record(google_event_id=event_id)
```

---

## Common Tasks

### Schedule an Appointment
```python
task = "Schedule dentist appointment next Friday at 3pm"
result = await agent.run(task)
```

### List All Appointments
```python
task = "Show me all appointments in the database for next week"
result = await agent.run(task)
```

### Update an Appointment
```python
task = "Change my dentist appointment from 3pm to 4pm"
result = await agent.run(task)
```

### Delete an Appointment
```python
task = "Cancel my dentist appointment and remove it from both calendar and database"
result = await agent.run(task)
```

### Sync Calendar to Database
```python
task = "Get all events from my calendar for the next 30 days and save them to the database"
result = await agent.run(task)
```

---

## Troubleshooting

### "OAuth error" or "credentials.json not found"
- Make sure you downloaded credentials from Google Cloud
- Place it in `mcp_server/google_calendar/credentials.json`

### "Token expired"
- Delete `token.json`
- Run the server again to re-authenticate

### "Cannot connect to SQLite server"
- Check that `sqlite_server.py` path is correct
- Try running it standalone: `python mcp_server/sqlite_server.py`

### "Tool not found"
- The agent might not have initialized both servers
- Check logs to see which servers connected successfully

### "Date parsing error"
- Be specific with dates: "next Monday" is better than "soon"
- Include times: "at 2pm" or "at 14:00"

---

## Next Steps

Once you have the basic system working:

1. **Add Recurring Appointments**
   ```python
   task = "Schedule weekly team meeting every Monday at 10am"
   ```

2. **Add Attendees**
   ```python
   task = "Schedule meeting with john@example.com tomorrow at 3pm"
   ```

3. **Conflict Detection**
   ```python
   task = "Check if I'm free on Tuesday at 2pm before scheduling"
   ```

4. **Bulk Import**
   ```python
   task = "Import all my calendar events from the past month into the database"
   ```

5. **Advanced Queries**
   ```python
   task = "Show me all appointments with Dr. Smith in the last 6 months"
   ```

---

## Resources

- **Full Integration Plan**: See `INTEGRATION_PLAN.md`
- **Google Calendar MCP**: https://github.com/guinacio/mcp-google-calendar
- **SQLite Server Code**: `mcp_server/sqlite_server.py`
- **ReAct Agent Code**: `agent/react_agent.py`

---

## Questions?

Before implementing, consider:

1. Do you want **bi-directional sync**? (calendar → DB and DB → calendar)
2. Should we support **multiple calendars**?
3. Do you need **recurring event** support?
4. Should there be **conflict detection**?
5. Do you want **email reminders**?

These can all be added incrementally!

---

**Ready to implement?** Let me know and I'll start building the multi-server agent!
