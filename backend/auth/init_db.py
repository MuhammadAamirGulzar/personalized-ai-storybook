"""
Database initialization script
Run this once to create the database and tables
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.auth.database import engine, Base
from backend.auth.models import User

def init_database():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    print("\nYou can now start the backend server.")

if __name__ == "__main__":
    init_database()

