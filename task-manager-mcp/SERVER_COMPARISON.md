# Google Calendar MCP Server Comparison

## Option 1: nspady/google-calendar-mcp ⭐ RECOMMENDED
**Repository:** https://github.com/nspady/google-calendar-mcp
**NPM Package:** @cocal/google-calendar-mcp
**Language:** TypeScript/JavaScript (Node.js)

### Pros ✅
1. **NPX Installation** - Easiest setup, no repository cloning needed
   ```bash
   npx @cocal/google-calendar-mcp
   ```

2. **Intelligent Import** 🔥 - Create events from:
   - Screenshots (PNG, JPEG, GIF)
   - PDFs
   - Web links
   - Natural language parsing

3. **Professional Package** - Published to NPM, well-maintained

4. **Rich Features:**
   - Search events by text
   - Event color support
   - Multi-calendar support
   - Free/busy queries
   - Advanced recurring event handling
   - Natural language date/time understanding

5. **Better Documentation** - Clear setup guides, examples

6. **Active Development** - Recently updated, good community

### Cons ❌
1. **Requires Node.js** - Additional runtime dependency (your stack is Python)
2. **Test Mode Token Expiry** - OAuth tokens expire after 7 days in test mode
   - Solution: Set up production mode (one-time setup)

### Available Tools (8)
```javascript
1. list-calendars      // List all available calendars
2. list-events        // Get events with date filtering
3. search-events      // Search events by text query
4. create-event       // Create new events
5. update-event       // Modify existing events
6. delete-event       // Remove events
7. get-freebusy       // Check availability
8. list-colors        // Get available event colors
```

---

## Option 2: guinacio/mcp-google-calendar
**Repository:** https://github.com/guinacio/mcp-google-calendar
**Language:** Python

### Pros ✅
1. **Python-based** - Matches your existing stack
2. **Simple** - Straightforward implementation
3. **No Node.js required**

### Cons ❌
1. **Manual Installation** - Must clone repository
2. **Basic Features** - No intelligent import, no search, no colors
3. **Less Documentation**
4. **Fewer Advanced Features**

### Available Tools (8)
```python
1. list-calendars      // List calendars
2. get-events         // View events
3. create-event       // Create events
4. update-event       // Update events
5. delete-event       // Delete events
6. check-availability // Free/busy check
7. get-timezone-info  // Get timezone
8. get-current-date   // Get current date/time
```

---

## Side-by-Side Comparison

| Feature | nspady | guinacio |
|---------|--------|----------|
| **Language** | TypeScript/Node.js | Python |
| **Installation** | NPX (easiest) | Git clone + pip |
| **Intelligent Import** | ✅ Images, PDFs, web links | ❌ |
| **Search Events** | ✅ Text search | ❌ |
| **Event Colors** | ✅ | ❌ |
| **Natural Language** | ✅ Built-in | Basic |
| **Documentation** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **NPM Package** | ✅ Published | ❌ |
| **Active Maintenance** | ✅ Recent updates | ✅ |
| **OAuth Setup** | Production mode available | Standard |
| **MCP Protocol** | stdio | stdio |

---

## Recommendation: Use nspady/google-calendar-mcp

### Why?

1. **Intelligent Import is a Game Changer**
   - User can send screenshot of appointment reminder
   - Agent extracts details and creates event automatically
   - Perfect for your use case!

2. **NPX = Zero Setup Friction**
   - No repository management
   - No version conflicts
   - Just works™

3. **Better User Experience**
   - Search events by text
   - Color-coded events
   - Natural language parsing

4. **More Professional**
   - Published NPM package
   - Better docs
   - Active community

### Node.js Concern Addressed

**Q:** "But my stack is Python. Won't Node.js cause issues?"
**A:** No! Here's why:

1. **MCP is Language-Agnostic**
   - Your ReAct agent (Python) communicates via stdio
   - The server (Node.js) is a separate process
   - They communicate through MCP protocol (JSON over stdio)
   - Language doesn't matter!

2. **Easy Setup**
   ```bash
   # Install Node.js once (if not already installed)
   # Then the MCP server just works via NPX
   ```

3. **No Code Changes Needed**
   - Your Python agent code stays the same
   - Just point to the NPX command instead of Python script

---

## Updated Architecture with nspady Server

```
┌─────────────────────────────────────────┐
│   MultiServerReActAgent (Python)       │
└──────────┬──────────────────────────────┘
           │
     ┌─────┴─────┐
     │           │
     ↓           ↓
┌─────────┐ ┌─────────────────┐
│ Python  │ │ Node.js         │
│ Process │ │ Process         │
└────┬────┘ └─────┬───────────┘
     │            │
     ↓            ↓
┌─────────┐ ┌──────────────────┐
│ SQLite  │ │ Google Calendar  │
│ MCP     │ │ MCP Server       │
│ Server  │ │ (@cocal/...)     │
│ (Python)│ │ (TypeScript)     │
└─────────┘ └──────────────────┘
```

**Communication:**
- Both servers use stdio (stdin/stdout)
- MCP protocol is JSON-based
- Language barrier = non-existent

---

## Setup Comparison

### nspady Setup (5 minutes)
```bash
# 1. Install Node.js (if needed)
# Download from nodejs.org

# 2. Set up Google OAuth credentials
# (Same for both servers)

# 3. Configure environment
export GOOGLE_OAUTH_CREDENTIALS='{"installed":{"client_id":"..."}}'

# 4. Done! Use via NPX
npx @cocal/google-calendar-mcp
```

### guinacio Setup (15 minutes)
```bash
# 1. Clone repository
git clone https://github.com/guinacio/mcp-google-calendar.git
cd mcp-google-calendar

# 2. Install dependencies
pip install -e .

# 3. Set up Google OAuth credentials
# Copy credentials.json to project folder

# 4. Run server
python server.py
```

---

## Integration with Your ReAct Agent

### Using nspady Server

```python
# server_config.py
from dataclasses import dataclass

@dataclass
class ServerConfig:
    name: str
    command: str
    args: List[str]
    env: Optional[Dict] = None

# Configuration
servers = [
    ServerConfig(
        name="sqlite",
        command="python",
        args=["../mcp_server/sqlite_server.py"]
    ),
    ServerConfig(
        name="google_calendar",
        command="npx",  # ← Node.js via NPX
        args=["@cocal/google-calendar-mcp"],
        env={
            "GOOGLE_OAUTH_CREDENTIALS": os.getenv("GOOGLE_OAUTH_CREDENTIALS")
        }
    )
]
```

**That's it!** Your Python agent works seamlessly with the Node.js server.

---

## Tool Mapping (nspady Server)

```python
# Available tools from nspady server
GOOGLE_CALENDAR_TOOLS = {
    "list-calendars": "List all available calendars",
    "list-events": "Get events with date filtering",
    "search-events": "Search events by text query",
    "create-event": "Create new calendar events",
    "update-event": "Modify existing events",
    "delete-event": "Remove events",
    "get-freebusy": "Check availability across calendars",
    "list-colors": "Get available event colors"
}

# Your SQLite tools (unchanged)
SQLITE_TOOLS = {
    "create_table": "Create database table",
    "insert_record": "Insert data",
    "read_records": "Query data",
    "update_record": "Update data",
    "delete_record": "Delete data",
    "list_tables": "List all tables",
    "describe_table": "Get table schema",
    "execute_query": "Run custom SELECT queries"
}
```

---

## Advanced Use Cases with nspady

### 1. Intelligent Import from Screenshot
```python
task = """
I'm attaching a screenshot of an appointment reminder email.
Extract the details and create a calendar event, then save to database.
"""

# Agent will:
# 1. Use intelligent import to parse screenshot
# 2. Create event in Google Calendar
# 3. Save appointment to SQLite database
```

### 2. Search and Sync
```python
task = """
Search my calendar for all events with 'dentist' in the title
from the past year and save them to the database.
"""

# Agent will:
# 1. Use search-events tool
# 2. Loop through results
# 3. Insert each into appointments table
```

### 3. Color-Coded Categories
```python
task = """
Create a doctor appointment next Monday at 2pm
and mark it with the red color for urgent appointments.
"""

# Agent will:
# 1. List available colors
# 2. Create event with red color
# 3. Save to database with color info
```

---

## Final Recommendation

**Use nspady/google-calendar-mcp** because:

1. ✅ **Intelligent Import** - Perfect for your appointment use case
2. ✅ **NPX Installation** - Easiest setup possible
3. ✅ **Search Feature** - Find appointments by text
4. ✅ **Professional** - Well-maintained NPM package
5. ✅ **Language Agnostic** - Works perfectly with Python agent
6. ✅ **Better UX** - More features for users

The Node.js requirement is a non-issue because MCP is designed for multi-language interoperability!

---

## Next Steps

1. Install Node.js (if not already installed)
2. Set up Google OAuth credentials
3. Update integration plan to use nspady server
4. Test NPX installation
5. Build MultiServerReActAgent with nspady config

**Ready to proceed with nspady?**
