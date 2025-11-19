#!/usr/bin/env python3
"""
Database Setup Script
Initializes the appointments database with the required schema.
"""

import sqlite3
import os
import sys
from pathlib import Path


def setup_database(db_path: str = "appointments.db", schema_path: str = None):
    """
    Set up the appointments database.

    Args:
        db_path: Path to the database file
        schema_path: Path to the SQL schema file
    """
    # Determine schema file path
    if schema_path is None:
        script_dir = Path(__file__).parent
        schema_path = script_dir / "appointments_schema.sql"

    # Check if schema file exists
    if not os.path.exists(schema_path):
        print(f"❌ Error: Schema file not found: {schema_path}")
        sys.exit(1)

    # Read schema
    print(f"📖 Reading schema from: {schema_path}")
    with open(schema_path, 'r') as f:
        schema_sql = f.read()

    # Connect to database
    print(f"🔗 Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Execute schema
        print("⚙️  Creating tables and indexes...")
        cursor.executescript(schema_sql)
        conn.commit()

        # Verify tables were created
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name;
        """)
        tables = cursor.fetchall()

        print("\n✅ Database setup complete!")
        print(f"\nCreated tables:")
        for table in tables:
            print(f"  • {table[0]}")

        # Get table info for appointments
        cursor.execute("PRAGMA table_info(appointments);")
        columns = cursor.fetchall()

        print(f"\nAppointments table structure:")
        print(f"  Columns: {len(columns)}")
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            col_notnull = "NOT NULL" if col[3] else ""
            col_default = f"DEFAULT {col[4]}" if col[4] else ""
            print(f"    • {col_name} {col_type} {col_notnull} {col_default}".strip())

        print(f"\n📁 Database file: {os.path.abspath(db_path)}")
        print(f"💾 Database size: {os.path.getsize(db_path)} bytes")

    except sqlite3.Error as e:
        print(f"\n❌ Error setting up database: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()


def verify_database(db_path: str = "appointments.db"):
    """
    Verify the database is set up correctly.

    Args:
        db_path: Path to the database file
    """
    print(f"\n🔍 Verifying database: {db_path}")

    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check appointments table
        cursor.execute("SELECT COUNT(*) FROM appointments;")
        count = cursor.fetchone()[0]
        print(f"  ✓ Appointments table exists ({count} records)")

        # Check sync_log table
        cursor.execute("SELECT COUNT(*) FROM sync_log;")
        count = cursor.fetchone()[0]
        print(f"  ✓ Sync log table exists ({count} records)")

        # Check indexes
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND sql IS NOT NULL
            ORDER BY name;
        """)
        indexes = cursor.fetchall()
        print(f"  ✓ {len(indexes)} indexes created")

        # Check triggers
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='trigger'
            ORDER BY name;
        """)
        triggers = cursor.fetchall()
        print(f"  ✓ {len(triggers)} triggers created")

        print("\n✅ Database verification passed!")
        return True

    except sqlite3.Error as e:
        print(f"\n❌ Database verification failed: {e}")
        return False

    finally:
        cursor.close()
        conn.close()


def reset_database(db_path: str = "appointments.db"):
    """
    Reset the database (delete and recreate).

    Args:
        db_path: Path to the database file
    """
    if os.path.exists(db_path):
        response = input(f"⚠️  Delete existing database '{db_path}'? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            os.remove(db_path)
            print(f"🗑️  Deleted: {db_path}")
        else:
            print("❌ Cancelled")
            return

    setup_database(db_path)


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Setup appointments database")
    parser.add_argument(
        '--db',
        default='appointments.db',
        help='Database file path (default: appointments.db)'
    )
    parser.add_argument(
        '--schema',
        default=None,
        help='Schema file path (default: appointments_schema.sql)'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify existing database'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset database (delete and recreate)'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("APPOINTMENTS DATABASE SETUP")
    print("=" * 70)
    print()

    if args.reset:
        reset_database(args.db)
    elif args.verify:
        verify_database(args.db)
    else:
        if os.path.exists(args.db):
            print(f"⚠️  Database already exists: {args.db}")
            response = input("Continue anyway? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("❌ Cancelled")
                return

        setup_database(args.db, args.schema)
        verify_database(args.db)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
