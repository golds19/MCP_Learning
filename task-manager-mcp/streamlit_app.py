#!/usr/bin/env python3
"""
Streamlit App for Multi-Server ReAct Agent
Interactive UI for testing appointment scheduling with natural language.
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path
import os

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.multi_server_agent import MultiServerReActAgent
from agent.server_config import ServerConfig, create_sqlite_config, create_google_calendar_config
from agent.llm_integration import MockLLMProvider, llm_callback_factory

# Page config
st.set_page_config(
    page_title="Appointment Scheduler Agent",
    page_icon="📅",
    layout="wide"
)

# Title
st.title("📅 Multi-Server ReAct Agent")
st.markdown("### Schedule appointments using natural language")

# Sidebar configuration
st.sidebar.header("⚙️ Configuration")

# Server selection
st.sidebar.subheader("MCP Servers")
use_sqlite = st.sidebar.checkbox("SQLite Database", value=True, disabled=True)
use_google_calendar = st.sidebar.checkbox("Google Calendar", value=True)

# LLM selection
st.sidebar.subheader("LLM Provider")
llm_provider = st.sidebar.selectbox(
    "Choose LLM",
    ["Mock (Demo)", "OpenAI GPT", "Ollama (Local)"],
    help="Mock uses predefined responses for demo purposes"
)

# LLM configuration
if llm_provider == "OpenAI GPT":
    openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    openai_model = st.sidebar.selectbox("Model", ["gpt-4", "gpt-3.5-turbo"])
elif llm_provider == "Ollama (Local)":
    ollama_model = st.sidebar.text_input("Model Name", value="llama2")
    ollama_url = st.sidebar.text_input("Ollama URL", value="http://localhost:11434")

# Google Calendar credentials
if use_google_calendar:
    st.sidebar.subheader("Google Calendar")
    cred_method = st.sidebar.radio(
        "Credentials Method",
        ["Environment Variable", "File Path"]
    )

    if cred_method == "File Path":
        cred_path = st.sidebar.text_input("Credentials Path", value="credentials.json")
    else:
        st.sidebar.info("Using GOOGLE_OAUTH_CREDENTIALS from environment")

# Agent settings
st.sidebar.subheader("Agent Settings")
max_iterations = st.sidebar.slider("Max Iterations", 1, 20, 10)
verbose = st.sidebar.checkbox("Verbose Output", value=True)

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'agent_output' not in st.session_state:
    st.session_state.agent_output = []


async def create_llm_callback(provider: str):
    """Create LLM callback based on provider selection."""
    if provider == "Mock (Demo)":
        # Use mock LLM for demo
        mock_llm = MockLLMProvider()

        # Add predefined responses for common tasks
        mock_llm.add_response("""Thought: I need to check if the appointments table exists first.
Action: describe_table
Action Input: {"table_name": "appointments"}""")

        if use_google_calendar:
            mock_llm.add_response("""Thought: Table exists. Let me list the available Google calendars.
Action: list-calendars
Action Input: {}""")

            mock_llm.add_response("""Thought: I can see the calendars. Now I'll create an appointment. Based on today being 2025-11-19, I'll schedule for next Tuesday which is 2025-11-25 at 2pm.
Action: create-event
Action Input: {"summary": "Appointment as requested", "start": {"dateTime": "2025-11-25T14:00:00", "timeZone": "America/Los_Angeles"}, "end": {"dateTime": "2025-11-25T15:00:00", "timeZone": "America/Los_Angeles"}}""")

            mock_llm.add_response("""Thought: Event created in calendar. Now I need to save this to the database with the event ID.
Action: insert_record
Action Input: {"table_name": "appointments", "data": {"title": "Appointment as requested", "start_datetime": "2025-11-25T14:00:00", "end_datetime": "2025-11-25T15:00:00", "google_event_id": "generated_event_id", "synced_to_calendar": 1, "status": "confirmed"}}""")
        else:
            mock_llm.add_response("""Thought: Table exists. I'll create an appointment in the database for the requested time.
Action: insert_record
Action Input: {"table_name": "appointments", "data": {"title": "Appointment as requested", "start_datetime": "2025-11-25T14:00:00", "end_datetime": "2025-11-25T15:00:00", "synced_to_calendar": 0, "status": "confirmed"}}""")

        mock_llm.add_response("""Thought: Let me verify the appointment was saved.
Action: read_records
Action Input: {"table_name": "appointments", "limit": 5}""")

        mock_llm.add_response("""Thought: Appointment successfully created and verified. Task complete!
Action: FINISH
Action Input: {}""")

        async def callback(prompt: str) -> str:
            return await mock_llm.generate(prompt)

        return callback

    elif provider == "OpenAI GPT":
        if not openai_api_key:
            st.error("Please provide OpenAI API key in the sidebar")
            return None
        return await llm_callback_factory("openai", api_key=openai_api_key, model=openai_model)

    elif provider == "Ollama (Local)":
        return await llm_callback_factory("ollama", model=ollama_model, base_url=ollama_url)


async def run_agent(task: str):
    """Run the agent with the given task."""

    # Setup server configurations
    project_root = Path(__file__).parent
    sqlite_server_path = project_root / "mcp_server" / "sqlite_server.py"

    servers = [
        ServerConfig(
            name="sqlite",
            command="python",
            args=[str(sqlite_server_path)],
            description="SQLite database"
        )
    ]

    # Add Google Calendar if enabled
    if use_google_calendar:
        try:
            if cred_method == "File Path" and cred_path:
                servers.append(create_google_calendar_config(cred_path))
            else:
                servers.append(create_google_calendar_config())
        except Exception as e:
            st.warning(f"Could not configure Google Calendar: {e}")

    # Create agent
    agent = MultiServerReActAgent(
        server_configs=servers,
        max_iterations=max_iterations,
        verbose=verbose
    )

    # Create LLM callback
    llm_callback = await create_llm_callback(llm_provider)
    if llm_callback is None:
        return None

    # Run agent
    try:
        result = await agent.run(task, llm_callback=llm_callback)
        return result, agent
    except Exception as e:
        st.error(f"Error running agent: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None, None


# Main interface
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Enter Your Instruction")

    # Example prompts
    with st.expander("📝 Example Prompts"):
        st.markdown("""
        **Create Appointments:**
        - Schedule appointment with Dr. Smith next Tuesday at 2pm
        - Create a dentist appointment for tomorrow at 10am
        - Add team meeting on Friday at 3pm

        **Query Appointments:**
        - Show me all appointments
        - List appointments for next week
        - Find appointments with "doctor" in the title

        **Database Operations:**
        - Create the appointments table if it doesn't exist
        - Show me the structure of the appointments table
        - List all tables in the database
        """)

    # Input field
    user_input = st.text_area(
        "Your instruction:",
        placeholder="e.g., Schedule appointment with Dr. Smith next Tuesday at 2pm",
        height=100
    )

    # Action buttons
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])

    with col_btn1:
        submit_btn = st.button("🚀 Execute", type="primary", use_container_width=True)

    with col_btn2:
        clear_btn = st.button("🗑️ Clear History", use_container_width=True)

with col2:
    st.subheader("📊 Status")

    # Database status
    db_path = Path(__file__).parent / "appointments.db"
    if db_path.exists():
        st.success("✅ Database: Ready")
    else:
        st.error("❌ Database: Not found")
        st.info("Run: `python db_schema/setup_database.py`")

    # Server status
    st.info(f"📦 SQLite: Enabled")
    if use_google_calendar:
        st.info(f"📅 Google Calendar: Enabled")
    else:
        st.warning("📅 Google Calendar: Disabled")

    # LLM status
    st.info(f"🤖 LLM: {llm_provider}")

# Clear history
if clear_btn:
    st.session_state.history = []
    st.session_state.agent_output = []
    st.rerun()

# Execute agent
if submit_btn and user_input:
    st.session_state.history.append({
        "task": user_input,
        "timestamp": pd.Timestamp.now() if 'pd' in dir() else None
    })

    with st.spinner("🤖 Agent is thinking and acting..."):
        # Run agent
        result, agent = asyncio.run(run_agent(user_input))

        if result:
            # Display results
            st.success("✅ Task completed successfully!")

            # Show execution summary
            st.subheader("📋 Execution Summary")

            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                st.metric("Iterations", result['iterations'])
            with col_res2:
                st.metric("Final State", result['final_state'].value)
            with col_res3:
                st.metric("Success", "Yes" if result['success'] else "No")

            # Show steps
            st.subheader("🔄 Agent Steps")

            for i, step in enumerate(result['steps'], 1):
                with st.expander(f"Step {i}: {step.state.value.title()}", expanded=(i == len(result['steps']))):
                    st.markdown(f"**💭 Thought:** {step.thought}")

                    if step.action:
                        st.markdown(f"**⚡ Action:** `{step.action}`")

                        if step.action_input:
                            st.json(step.action_input)

                        if step.observation:
                            st.markdown(f"**👁️ Observation:**")
                            st.code(step.observation, language="text")

            # Show connected servers
            if agent:
                st.subheader("🔗 Connected Servers")
                stats = agent.get_server_stats()

                for server_name, server_info in stats['servers'].items():
                    with st.expander(f"{server_name.upper()} ({server_info['tool_count']} tools)"):
                        for tool in server_info['tools']:
                            st.markdown(f"• `{tool}`")

# Display history
if st.session_state.history:
    st.divider()
    st.subheader("📜 Execution History")

    for i, item in enumerate(reversed(st.session_state.history[-5:]), 1):
        st.text(f"{len(st.session_state.history) - i + 1}. {item['task']}")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Multi-Server ReAct Agent v2.0 | Built with Streamlit</p>
    <p>📚 See RESULT.md and SETUP_INSTRUCTIONS.md for documentation</p>
</div>
""", unsafe_allow_html=True)

# Import pandas if needed for timestamp
try:
    import pandas as pd
except ImportError:
    pass
