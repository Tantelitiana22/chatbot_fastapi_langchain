#!/usr/bin/env python3
"""
Database Migration Script for ChatGPT-like Chatbot

This script helps migrate existing databases to include the new columns:
- title: Conversation titles
- created_at: Creation timestamp
- updated_at: Last update timestamp

Usage:
    python migrate_db.py
"""

import sqlite3
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chat_app.infrastructure.repositories import (  # noqa: E402  # pylint: disable=C0413
    SQLiteConversationRepository,
)


def check_database_status():
    """Check the current status of the database"""
    db_path = Path("conversations.db")

    if not db_path.exists():
        print("❌ Database file 'conversations.db' not found")
        print(
            "   The database will be created automatically when you start "
            "the application"
        )
        return False

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Check table structure
    cur.execute("PRAGMA table_info(conversations)")
    columns = cur.fetchall()
    column_names = [col[1] for col in columns]

    print("📊 Current database status:")
    print(f"   Database file: {db_path.absolute()}")
    print(f"   Table columns: {', '.join(column_names)}")

    # Check for missing columns
    missing_columns = []
    required_columns = ["title", "created_at", "updated_at"]

    for col in required_columns:
        if col not in column_names:
            missing_columns.append(col)

    if missing_columns:
        print(f"   ⚠️  Missing columns: {', '.join(missing_columns)}")
        return False

    print("   ✅ All required columns present")

    # Check record count
    cur.execute("SELECT COUNT(*) FROM conversations")
    count = cur.fetchone()[0]
    print(f"   📝 Total conversations: {count}")

    # Check for records without timestamps
    cur.execute(
        "SELECT COUNT(*) FROM conversations WHERE created_at IS NULL "
        "OR updated_at IS NULL"
    )
    null_timestamps = cur.fetchone()[0]
    if null_timestamps > 0:
        print(f"   ⚠️  {null_timestamps} records missing timestamps")
        return False

    print("   ✅ All records have timestamps")
    conn.close()
    return True


def run_migration():
    """Run the database migration"""
    print("🔄 Starting database migration...")

    try:
        # Initialize the repository which will create/update the database schema
        SQLiteConversationRepository()
        print("✅ Migration completed successfully!")
        return True
    except Exception as e:  # pylint: disable=broad-except
        print(f"❌ Migration failed: {e}")
        return False


def main():
    """Main migration function"""
    print("🚀 ChatGPT-like Chatbot Database Migration")
    print("=" * 50)

    # Check current status
    is_up_to_date = check_database_status()

    if is_up_to_date:
        print("\n✅ Database is already up to date!")
        print("   No migration needed.")
        return

    print("\n🔄 Database needs migration...")

    # Ask for confirmation
    response = (
        input("\nDo you want to proceed with the migration? (y/N): ").strip().lower()
    )

    if response not in ["y", "yes"]:
        print("❌ Migration cancelled by user")
        return

    # Run migration
    success = run_migration()

    if success:
        print("\n🎉 Migration completed successfully!")
        print("   You can now start the application normally.")

        # Check final status
        print("\n📊 Final database status:")
        check_database_status()
    else:
        print("\n❌ Migration failed!")
        print("   Please check the error messages above and try again.")
        print("   You may need to backup your database before retrying.")


if __name__ == "__main__":
    main()
