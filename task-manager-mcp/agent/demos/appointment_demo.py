#!/usr/bin/env python3
"""
Appointment Scheduling Demo
Demonstrates multi-server ReAct agent with SQLite + Google Calendar integration.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.multi_server_agent import MultiServerReActAgent
from agent.server_config import ServerConfig, create_sqlite_config, create_google_calendar_config
from agent.llm_integration import MockLLMProvider


async def demo_basic_scheduling():
    """
    Demo: Basic appointment scheduling workflow.
    Creates an event in Google Calendar and saves it to SQLite database.
    """
    print("\n" + "=" * 70)
    print("APPOINTMENT SCHEDULING DEMO")
    print("Multi-Server ReAct Agent: SQLite + Google Calendar")
    print("=" * 70 + "\n")

    # Get paths
    project_root = Path(__file__).parent.parent.parent
    sqlite_server_path = project_root / "mcp_server" / "sqlite_server.py"
    db_path = project_root / "appointments.db"

    # Check if database exists
    if not db_path.exists():
        print("⚠️  Appointments database not found!")
        print(f"Please run: python db_schema/setup_database.py")
        print(f"Expected location: {db_path}\n")
        return

    # Configure servers
    print("📋 Configuring servers...")
    servers = [
        ServerConfig(
            name="sqlite",
            command="python",
            args=[str(sqlite_server_path)],
            description="SQLite database for appointments"
        ),
        create_google_calendar_config()  # Reads from environment
    ]

    # Check Google Calendar credentials
    if not servers[1].env:
        print("\n⚠️  Google Calendar credentials not configured!")
        print("Please set one of these environment variables:")
        print("  - GOOGLE_OAUTH_CREDENTIALS (JSON string)")
        print("  - GOOGLE_OAUTH_CREDENTIALS_PATH (path to credentials.json)")
        print("\nFor testing without Google Calendar, you can:")
        print("  1. Remove google_calendar from server list")
        print("  2. Or set up Google Cloud OAuth credentials\n")

        response = input("Continue without Google Calendar? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            return
        # Remove Google Calendar server
        servers = servers[:1]

    # Create agent
    print(f"\n🤖 Creating multi-server agent...")
    agent = MultiServerReActAgent(
        server_configs=servers,
        max_iterations=10,
        verbose=True
    )

    # Create mock LLM with predefined responses for demo
    mock_llm = MockLLMProvider()

    # Response 1: Create appointments table if needed
    mock_llm.add_response("""Thought: First, I need to make sure the appointments table exists in the database.
Action: describe_table
Action Input: {"table_name": "appointments"}""")

    if "google_calendar" in [s.name for s in servers]:
        # Response 2: Get current date from Google Calendar
        mock_llm.add_response("""Thought: The appointments table exists. Now I need to get the current date to calculate 'next Tuesday'.
Action: list-calendars
Action Input: {}""")

        # Response 3: Create event in Google Calendar
        mock_llm.add_response("""Thought: I can see the calendars. Now I'll create an appointment for Dr. Smith next Tuesday at 2pm. Assuming today is 2025-11-19, next Tuesday would be 2025-11-25 at 14:00.
Action: create-event
Action Input: {"summary": "Appointment with Dr. Smith", "start": {"dateTime": "2025-11-25T14:00:00", "timeZone": "America/Los_Angeles"}, "end": {"dateTime": "2025-11-25T15:00:00", "timeZone": "America/Los_Angeles"}, "description": "Doctor appointment", "location": "Medical Center"}""")

        # Response 4: Save to database with event ID
        mock_llm.add_response("""Thought: The event was created successfully in Google Calendar. Now I need to save this appointment to the database with the event ID for future reference.
Action: insert_record
Action Input: {"table_name": "appointments", "data": {"title": "Appointment with Dr. Smith", "description": "Doctor appointment", "location": "Medical Center", "start_datetime": "2025-11-25T14:00:00", "end_datetime": "2025-11-25T15:00:00", "timezone": "America/Los_Angeles", "google_event_id": "event_abc123", "calendar_id": "primary", "synced_to_calendar": 1, "status": "confirmed"}}""")
    else:
        # Without Google Calendar: just save to database
        mock_llm.add_response("""Thought: The appointments table exists. I'll create an appointment record in the database for Dr. Smith next Tuesday at 2pm.
Action: insert_record
Action Input: {"table_name": "appointments", "data": {"title": "Appointment with Dr. Smith", "description": "Doctor appointment", "location": "Medical Center", "start_datetime": "2025-11-25T14:00:00", "end_datetime": "2025-11-25T15:00:00", "timezone": "America/Los_Angeles", "status": "confirmed", "synced_to_calendar": 0}}""")

    # Response 5: Verify by reading appointments
    mock_llm.add_response("""Thought: The appointment has been saved to the database. Let me verify it was saved correctly by reading the appointments.
Action: read_records
Action Input: {"table_name": "appointments", "where": "title LIKE '%Dr. Smith%'"}""")

    # Response 6: Finish
    mock_llm.add_response("""Thought: Perfect! The appointment with Dr. Smith has been successfully created in both Google Calendar and the database. Task is complete.
Action: FINISH
Action Input: {}""")

    # Create callback
    async def mock_callback(prompt: str) -> str:
        return await mock_llm.generate(prompt)

    # Run the task
    print("\n" + "=" * 70)
    task = "Schedule appointment with Dr. Smith next Tuesday at 2pm"
    print(f"TASK: {task}")
    print("=" * 70 + "\n")

    try:
        result = await agent.run(task, llm_callback=mock_callback)

        # Print results
        print("\n" + "=" * 70)
        print("DEMO RESULTS")
        print("=" * 70)
        print(f"Success: {result['success']}")
        print(f"Iterations: {result['iterations']}")
        print(f"Final State: {result['final_state'].value}")

        # Print summary
        agent.print_summary()

        print("\n💡 What happened:")
        print("  1. Agent connected to SQLite and Google Calendar servers")
        print("  2. Checked if appointments table exists")
        if "google_calendar" in [s.name for s in servers]:
            print("  3. Listed available Google calendars")
            print("  4. Created event in Google Calendar")
            print("  5. Saved appointment to SQLite with event ID")
        else:
            print("  3. Created appointment record in SQLite")
        print("  6. Verified the appointment was saved")
        print("\n✅ Appointment scheduled successfully!")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


async def demo_list_appointments():
    """Demo: List all appointments from database."""
    print("\n" + "=" * 70)
    print("LIST APPOINTMENTS DEMO")
    print("=" * 70 + "\n")

    project_root = Path(__file__).parent.parent.parent
    sqlite_server_path = project_root / "mcp_server" / "sqlite_server.py"

    servers = [
        ServerConfig(
            name="sqlite",
            command="python",
            args=[str(sqlite_server_path)]
        )
    ]

    agent = MultiServerReActAgent(
        server_configs=servers,
        max_iterations=5,
        verbose=True
    )

    mock_llm = MockLLMProvider()
    mock_llm.add_response("""Thought: I need to list all appointments from the database.
Action: read_records
Action Input: {"table_name": "appointments"}""")

    mock_llm.add_response("""Thought: I have retrieved all appointments. Task complete.
Action: FINISH
Action Input: {}""")

    async def mock_callback(prompt: str) -> str:
        return await mock_llm.generate(prompt)

    task = "Show me all appointments in the database"
    result = await agent.run(task, llm_callback=mock_callback)

    print("\n✅ Appointments listed successfully!")


def print_menu():
    """Print demo menu."""
    print("\n" + "=" * 70)
    print("APPOINTMENT DEMO MENU")
    print("=" * 70)
    print("1. Basic Scheduling (Create appointment in calendar + database)")
    print("2. List Appointments (Show all from database)")
    print("3. Server Info (Show connected servers and tools)")
    print("0. Exit")
    print("=" * 70)


async def main():
    """Main function."""
    print("\n🚀 Multi-Server ReAct Agent - Appointment Demo")
    print("=" * 70)

    # Check prerequisites
    project_root = Path(__file__).parent.parent.parent
    db_path = project_root / "appointments.db"

    if not db_path.exists():
        print("\n⚠️  Setup Required!")
        print(f"\nAppointments database not found at: {db_path}")
        print("\nPlease run the setup script first:")
        print(f"  cd {project_root}")
        print("  python db_schema/setup_database.py")
        print("\nThen run this demo again.\n")
        return

    while True:
        print_menu()
        choice = input("\nSelect option (0-3): ").strip()

        if choice == "0":
            print("\n👋 Goodbye!")
            break
        elif choice == "1":
            await demo_basic_scheduling()
            input("\nPress Enter to continue...")
        elif choice == "2":
            await demo_list_appointments()
            input("\nPress Enter to continue...")
        elif choice == "3":
            # Quick server info
            project_root = Path(__file__).parent.parent.parent
            sqlite_server_path = project_root / "mcp_server" / "sqlite_server.py"

            servers = [
                ServerConfig(
                    name="sqlite",
                    command="python",
                    args=[str(sqlite_server_path)]
                )
            ]

            try:
                servers.append(create_google_calendar_config())
            except:
                pass

            agent = MultiServerReActAgent(
                server_configs=servers,
                max_iterations=1,
                verbose=False
            )

            try:
                await agent.initialize_sessions()
                agent.print_server_info()
                await agent.cleanup_sessions()
            except Exception as e:
                print(f"\n❌ Error: {e}")

            input("\nPress Enter to continue...")
        else:
            print("Invalid choice. Please select 0-3.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
