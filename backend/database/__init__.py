"""
Database package initialization
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize SQLAlchemy instance
db = SQLAlchemy()
migrate = Migrate()


def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    migrate.init_app(app, db, directory="database/migrations")

    print("Using database:", app.config["SQLALCHEMY_DATABASE_URI"])

    # Import models to ensure they're registered with SQLAlchemy
    from database.models import ViolationReport, Violation, ViolationImage

    return db
