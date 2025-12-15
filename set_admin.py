"""
Script to set a user as admin by email
"""
import sqlite3
import sys
import os
from pathlib import Path

# Database path
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "users.db"

def get_password_hash(password):
    """Hash password using bcrypt (same as backend)"""
    try:
        import bcrypt
        # Bcrypt has a 72-byte limit, so truncate if necessary
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    except ImportError:
        # Fallback to passlib if bcrypt not available
        try:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 72:
                password = password_bytes[:72].decode('utf-8', errors='ignore')
            return pwd_context.hash(password)
        except ImportError:
            print("⚠️  Error: bcrypt and passlib not available!")
            print("   Please install: pip install bcrypt")
            raise

def set_admin(email, password=None):
    """Set user as admin by email, optionally update password"""
    if not DB_PATH.exists():
        print("❌ Database file not found!")
        print(f"   Looking for: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # First ensure role column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'role' not in columns:
            print("Adding 'role' column...")
            cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user'")
            conn.commit()
            print("✅ Role column added")
        
        # Check if user exists
        cursor.execute("SELECT id, email, username FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"⚠️  User with email {email} not found!")
            print(f"Creating new admin user...")
            
            if not password:
                print("❌ Password required to create new user!")
                return
            
            # Create new user with admin role
            hashed_password = get_password_hash(password)
            username = email.split('@')[0]  # Use email prefix as username
            
            # Check if username already exists, if so add number
            cursor.execute("SELECT COUNT(*) FROM users WHERE username LIKE ?", (f"{username}%",))
            count = cursor.fetchone()[0]
            if count > 0:
                username = f"{username}{count + 1}"
            
            cursor.execute(
                "INSERT INTO users (email, username, hashed_password, role) VALUES (?, ?, ?, 'admin')",
                (email, username, hashed_password)
            )
            conn.commit()
            
            # Get the created user
            cursor.execute("SELECT id, email, username FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            print(f"✅ Created new admin user!")
            print(f"   Email: {email}")
            print(f"   Username: {user[2]}")
            print(f"   Password: {password}")
        else:
            # Update existing user to admin
            cursor.execute("UPDATE users SET role = 'admin' WHERE email = ?", (email,))
            
            # Optionally update password
            if password:
                hashed_password = get_password_hash(password)
                cursor.execute("UPDATE users SET hashed_password = ? WHERE email = ?", (hashed_password, email))
                print(f"✅ Password updated for {email}")
            
            conn.commit()
            print(f"✅ User {email} is now an admin!")
            print(f"   User ID: {user[0]}")
            print(f"   Username: {user[2]}")
        
        print(f"\n📝 You can now sign in with:")
        print(f"   Email: {email}")
        print(f"   Password: {password if password else '(unchanged)'}")
        print(f"   And access the Admin Panel!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # Set your email as admin
    # Note: If password needs to be set, sign up through the UI first, then run this script
    set_admin("softrdev0715@gmail.com", None)  # Set role only, don't change password

