"""
Database Initialization Script for PostgreSQL
"""
import asyncio
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chat_app.infrastructure.postgresql_repositories import (  # pylint: disable=C0413
    create_tables,
)


async def init_database():
    """Initialize PostgreSQL database tables."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print(
            "Please set DATABASE_URL=postgresql+asyncpg://user:password@host:port/database"
        )
        return False

    if not database_url.startswith("postgresql"):
        print("❌ DATABASE_URL must be a PostgreSQL connection string")
        return False

    try:
        print(
            f"🔧 Initializing database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}"
        )
        await create_tables(database_url)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(init_database())
    sys.exit(0 if success else 1)
