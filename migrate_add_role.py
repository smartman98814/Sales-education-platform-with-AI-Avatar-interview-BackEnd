"""
Migration script to add 'role' column to users table
Run this once to update existing database
"""
import sqlite3
from pathlib import Path

# Database path
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "users.db"

def migrate():
    """Add role column to users table if it doesn't exist"""
    if not DB_PATH.exists():
        print("Database file not found. It will be created on first run.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'role' not in columns:
            print("Adding 'role' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user'")
            conn.commit()
            print("✅ Migration completed: 'role' column added")
            
            # Update existing users to have 'user' role
            cursor.execute("UPDATE users SET role = 'user' WHERE role IS NULL")
            conn.commit()
            print("✅ Existing users updated with 'user' role")
        else:
            print("✅ Column 'role' already exists")
    except Exception as e:
        print(f"❌ Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

