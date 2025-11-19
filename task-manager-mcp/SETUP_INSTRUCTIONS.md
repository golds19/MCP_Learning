# Setup Instructions
## Multi-Server ReAct Agent with SQLite + Google Calendar

Follow these steps to get your appointment scheduling agent running.

---

## Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.8+** installed
- ✅ **Node.js 16+** installed (for Google Calendar MCP server)
- ✅ **MCP library**: `pip install mcp`
- ✅ **Google Cloud account** (free tier works)

---

## Step 1: Install Node.js (if needed)

Check if Node.js is installed:
```bash
node --version
```

If not installed, download from: https://nodejs.org/

Verify npm works:
```bash
npm --version
```

---

## Step 2: Setup Database

Navigate to your project directory and create the appointments database:

```bash
cd "c:\Research Folder\AI Learning\MCPLearning\MCP_Learning\task-manager-mcp"

# Run the database setup script
python db_schema/setup_database.py
```

You should see output like:
```
======================================================================
APPOINTMENTS DATABASE SETUP
======================================================================

📖 Reading schema from: db_schema\appointments_schema.sql
🔗 Connecting to database: appointments.db
⚙️  Creating tables and indexes...

✅ Database setup complete!

Created tables:
  • appointments
  • sync_log

Appointments table structure:
  Columns: 18
  ...
```

Verify the database:
```bash
python db_schema/setup_database.py --verify
```

---

## Step 3: Test SQLite MCP Server

Before integrating, verify your SQLite server works:

```bash
cd mcp_server
python sqlite_server.py
```

If it runs without errors, press `Ctrl+C` to stop it. It's working!

---

## Step 4: Setup Google Calendar (Optional but Recommended)

### 4.1 Create Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Create a new project (e.g., "Appointment Agent")
3. Enable Google Calendar API:
   - In the search bar, type "Google Calendar API"
   - Click on it
   - Click "Enable"

### 4.2 Create OAuth 2.0 Credentials

1. Go to "Credentials" in the left sidebar
2. Click "Create Credentials" → "OAuth client ID"
3. If prompted, configure OAuth consent screen:
   - User Type: External
   - App name: "Appointment Agent"
   - User support email: your email
   - Developer email: your email
   - Add scope: `https://www.googleapis.com/auth/calendar`
   - Add test user: your Gmail address
4. Back to "Create Credentials" → "OAuth client ID"
5. Application type: **Desktop app**
6. Name: "Appointment Agent Desktop"
7. Click "Create"
8. **Download JSON** - save it somewhere safe

### 4.3 Configure Credentials

You have two options:

**Option A: Environment Variable (Recommended)**
```bash
# Windows (PowerShell)
$env:GOOGLE_OAUTH_CREDENTIALS = Get-Content path\to\credentials.json -Raw

# Windows (Command Prompt)
set GOOGLE_OAUTH_CREDENTIALS=<paste entire JSON here>

# Linux/Mac
export GOOGLE_OAUTH_CREDENTIALS='{"installed":{...}}'
```

**Option B: File Path**
```bash
# Windows
set GOOGLE_OAUTH_CREDENTIALS_PATH=C:\path\to\credentials.json

# Linux/Mac
export GOOGLE_OAUTH_CREDENTIALS_PATH=/path/to/credentials.json
```

### 4.4 Test Google Calendar MCP Server

Test that the nspady server works:

```bash
npx @cocal/google-calendar-mcp
```

**What should happen:**
1. NPX downloads the package (first time only)
2. Browser window opens automatically
3. You log in to Google
4. Grant calendar permissions
5. Server starts successfully

Press `Ctrl+C` to stop it.

**Note:** Token is cached, so you won't need to authenticate again.

---

## Step 5: Run the Demo

Now you're ready to run the appointment scheduling demo!

```bash
cd agent
python demos/appointment_demo.py
```

### Demo Menu

You'll see a menu:
```
======================================================================
APPOINTMENT DEMO MENU
======================================================================
1. Basic Scheduling (Create appointment in calendar + database)
2. List Appointments (Show all from database)
3. Server Info (Show connected servers and tools)
0. Exit
======================================================================
```

**Try option 1** to schedule an appointment!

---

## What Happens in the Demo

### Option 1: Basic Scheduling

The agent will:
1. ✅ Connect to SQLite MCP server
2. ✅ Connect to Google Calendar MCP server
3. ✅ Check if appointments table exists
4. ✅ List available Google calendars
5. ✅ Create event in Google Calendar
6. ✅ Save appointment to SQLite database
7. ✅ Verify the appointment was saved

### Option 2: List Appointments

Queries the database and shows all appointments.

### Option 3: Server Info

Shows all connected servers and available tools.

---

## Troubleshooting

### "Database not found"
**Solution:** Run the setup script:
```bash
python db_schema/setup_database.py
```

### "Node.js not found"
**Solution:** Install Node.js from https://nodejs.org/

### "Google Calendar credentials not configured"
**Solution:** Set the environment variable:
```bash
set GOOGLE_OAUTH_CREDENTIALS_PATH=path\to\credentials.json
```

Or run without Google Calendar:
- The demo will ask if you want to continue without it
- Say "yes" to test SQLite functionality only

### "OAuth error" or "Token expired"
**Solution:**
1. Delete cached token (location varies by OS)
2. Run the demo again
3. Re-authenticate in browser

### "MCP library not found"
**Solution:**
```bash
pip install mcp
```

### "Import error: cannot import MultiServerReActAgent"
**Solution:** Make sure you're in the right directory:
```bash
cd "c:\Research Folder\AI Learning\MCPLearning\MCP_Learning\task-manager-mcp"
python agent/demos/appointment_demo.py
```

---

## Running Without Google Calendar

If you want to test SQLite functionality only (without Google Calendar):

### Option A: Modify Demo Script
Comment out Google Calendar in the demo:
```python
servers = [
    ServerConfig(
        name="sqlite",
        command="python",
        args=[str(sqlite_server_path)]
    ),
    # create_google_calendar_config()  # Commented out
]
```

### Option B: Say "Yes" When Prompted
The demo will detect missing credentials and ask if you want to continue without Google Calendar.

---

## Next Steps

Once the basic demo works:

1. **Try Custom Tasks**: Modify the demo to schedule different appointments
2. **Add LLM Integration**: Replace MockLLM with OpenAI or Ollama
3. **Build Custom Workflows**: Create your own multi-tool tasks
4. **Add Advanced Features**: Search, update, delete appointments

---

## File Structure

After setup, your project should look like:

```
task-manager-mcp/
├── agent/
│   ├── __init__.py
│   ├── react_agent.py
│   ├── multi_server_agent.py       # NEW
│   ├── server_config.py            # NEW
│   ├── llm_integration.py
│   └── demos/
│       ├── __init__.py             # NEW
│       └── appointment_demo.py     # NEW
│
├── mcp_server/
│   └── sqlite_server.py
│
├── db_schema/
│   ├── appointments_schema.sql     # NEW
│   └── setup_database.py           # NEW
│
├── appointments.db                  # NEW (created by setup)
├── INTEGRATION_PLAN.md
├── SERVER_COMPARISON.md
├── QUICK_START_GUIDE.md
└── SETUP_INSTRUCTIONS.md           # NEW (this file)
```

---

## Verifying Everything Works

Run this checklist:

- [ ] Database exists: `ls appointments.db`
- [ ] Database has tables: `python db_schema/setup_database.py --verify`
- [ ] SQLite server runs: `python mcp_server/sqlite_server.py` (Ctrl+C to stop)
- [ ] Node.js installed: `node --version`
- [ ] NPX works: `npx --version`
- [ ] Google Calendar server runs: `npx @cocal/google-calendar-mcp` (Ctrl+C to stop)
- [ ] Demo runs: `python agent/demos/appointment_demo.py`

---

## Success!

If you can run the demo and see:
```
✅ Appointment scheduled successfully!
```

Congratulations! Your multi-server ReAct agent is working!

---

## Getting Help

If you encounter issues:

1. Check the error message carefully
2. Review the troubleshooting section above
3. Verify all prerequisites are installed
4. Check that paths are correct for your system
5. Try running servers individually first

Common issue: **Paths on Windows**
- Use absolute paths or be in the correct directory
- Use forward slashes `/` or escaped backslashes `\\`

---

## What's Next?

Now that basic scheduling works, you can:

1. **Add Real LLM**: Replace MockLLM with GPT-4 or Claude
2. **Natural Language**: Test with: "Schedule dentist next Friday 3pm"
3. **Search**: Find appointments by keyword
4. **Update**: Modify existing appointments
5. **Delete**: Remove appointments from both systems
6. **Sync**: Import calendar events to database
7. **Recurring**: Handle weekly/monthly appointments

Refer to `INTEGRATION_PLAN.md` for advanced features!
