#!/usr/bin/env python3
"""
Database management script for handling migrations and database operations
"""
import os
import sys
from flask_migrate import init, migrate, upgrade, downgrade, current, history
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db


def create_migration_app():
    """Create app instance for migrations"""
    app = create_app()
    return app


def init_migrations():
    """Initialize migration repository"""
    app = create_migration_app()
    with app.app_context():
        try:
            init(directory="database/migrations")
            print("✅ Migration repository initialized successfully!")
        except Exception as e:
            print(f"❌ Error initializing migrations: {e}")


def create_migration(message=None):
    """Create a new migration"""
    app = create_migration_app()
    with app.app_context():
        try:
            if message:
                migrate(message=message)
            else:
                migrate()
            print("✅ Migration created successfully!")
        except Exception as e:
            print(f"❌ Error creating migration: {e}")


def run_migrations():
    """Apply pending migrations"""
    app = create_migration_app()
    with app.app_context():
        try:
            upgrade()
            print("✅ Migrations applied successfully!")
        except Exception as e:
            print(f"❌ Error applying migrations: {e}")


def rollback_migration(revision=None):
    """Rollback to a specific migration"""
    app = create_migration_app()
    with app.app_context():
        try:
            if revision:
                downgrade(revision=revision)
            else:
                downgrade()
            print("✅ Migration rolled back successfully!")
        except Exception as e:
            print(f"❌ Error rolling back migration: {e}")


def show_current():
    """Show current migration"""
    app = create_migration_app()
    with app.app_context():
        try:
            result = current()
            print(f"Current migration: {result}")
        except Exception as e:
            print(f"❌ Error getting current migration: {e}")


def show_history():
    """Show migration history"""
    app = create_migration_app()
    with app.app_context():
        try:
            result = history()
            print("Migration history:")
            for migration in result:
                print(f"  - {migration}")
        except Exception as e:
            print(f"❌ Error getting migration history: {e}")


def create_tables():
    """Create all tables (for development only)"""
    app = create_migration_app()
    with app.app_context():
        try:
            db.create_all()
            print("✅ All tables created successfully!")
        except Exception as e:
            print(f"❌ Error creating tables: {e}")


def drop_tables():
    """Drop all tables (DANGEROUS - use with caution)"""
    app = create_migration_app()
    with app.app_context():
        try:
            confirm = input("⚠️  This will DROP ALL TABLES. Type 'YES' to confirm: ")
            if confirm == "YES":
                db.drop_all()
                print("✅ All tables dropped!")
            else:
                print("❌ Operation cancelled.")
        except Exception as e:
            print(f"❌ Error dropping tables: {e}")


def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print(
            """
Database Management Commands:
  init          - Initialize migration repository
  migrate       - Create a new migration
  upgrade       - Apply pending migrations
  downgrade     - Rollback last migration
  current       - Show current migration
  history       - Show migration history  
  create-tables - Create all tables (dev only)
  drop-tables   - Drop all tables (DANGEROUS)

Usage: python manage_db.py <command> [args]
Examples:
  python manage_db.py init
  python manage_db.py migrate "Add new column"
  python manage_db.py upgrade
  python manage_db.py downgrade
        """
        )
        return

    command = sys.argv[1]

    if command == "init":
        init_migrations()
    elif command == "migrate":
        message = sys.argv[2] if len(sys.argv) > 2 else None
        create_migration(message)
    elif command == "upgrade":
        run_migrations()
    elif command == "downgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else None
        rollback_migration(revision)
    elif command == "current":
        show_current()
    elif command == "history":
        show_history()
    elif command == "create-tables":
        create_tables()
    elif command == "drop-tables":
        drop_tables()
    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
