"""
migrate_workshop_stories.py
Run this ONCE with: python migrate_workshop_stories.py
(from the project root: "MyAIStorybook - Mujahid")

Adds the 4 new columns to workshop_stories that are needed for the Workshop Library feature.
Safe to run multiple times - skips columns that already exist.
"""
import sys, os

# Ensure backend package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.auth.database import engine
from sqlalchemy import inspect, text

def migrate():
    inspector = inspect(engine)
    existing_cols = {c['name'] for c in inspector.get_columns('workshop_stories')}
    print(f"Current columns: {sorted(existing_cols)}")

    migrations = []

    if 'user_id' not in existing_cols:
        migrations.append(("user_id", "ALTER TABLE workshop_stories ADD COLUMN user_id INTEGER REFERENCES users(id)"))
    if 'title' not in existing_cols:
        migrations.append(("title", "ALTER TABLE workshop_stories ADD COLUMN title VARCHAR(255)"))
    if 'mode' not in existing_cols:
        migrations.append(("mode", "ALTER TABLE workshop_stories ADD COLUMN mode VARCHAR(50)"))
    if 'saved_by_user' not in existing_cols:
        migrations.append(("saved_by_user", "ALTER TABLE workshop_stories ADD COLUMN saved_by_user BOOLEAN NOT NULL DEFAULT FALSE"))

    if not migrations:
        print("All columns already exist. Nothing to do.")
        return

    with engine.connect() as conn:
        for col_name, sql in migrations:
            conn.execute(text(sql))
            print(f"  ✓ Added column: {col_name}")
        conn.commit()

    final_cols = {c['name'] for c in inspect(engine).get_columns('workshop_stories')}
    print(f"\nMigration complete. Final columns: {sorted(final_cols)}")

if __name__ == "__main__":
    migrate()
