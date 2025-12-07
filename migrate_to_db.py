"""
Migration script to move users from JSON to SQLite database
Run this once to migrate existing users.json data to the database
"""
import json
from pathlib import Path
from app.database import init_db, SessionLocal
from app.models.db_user import DBUser
from app.core.auth import get_password_hash

def migrate_users():
    """Migrate users from users.json to SQLite database"""
    # Initialize database
    init_db()
    
    # Load existing users from JSON
    users_file = Path(__file__).parent / "users.json"
    
    if not users_file.exists():
        print("No users.json file found. Nothing to migrate.")
        return
    
    with open(users_file, 'r') as f:
        users_data = json.load(f)
    
    if not users_data:
        print("No users in users.json. Nothing to migrate.")
        return
    
    db = SessionLocal()
    migrated_count = 0
    skipped_count = 0
    
    try:
        for email, user_data in users_data.items():
            # Check if user already exists in database
            existing_user = db.query(DBUser).filter(DBUser.email == email).first()
            if existing_user:
                print(f"User {email} already exists in database. Skipping.")
                skipped_count += 1
                continue
            
            # Create new user in database
            db_user = DBUser(
                email=user_data.get('email', email),
                username=user_data.get('username'),
                hashed_password=user_data.get('hashed_password')
            )
            
            db.add(db_user)
            migrated_count += 1
            print(f"Migrated user: {email}")
        
        db.commit()
        print(f"\nMigration complete!")
        print(f"Migrated: {migrated_count} users")
        print(f"Skipped: {skipped_count} users")
        print("\nYou can now delete users.json if you want (it's been backed up in the database)")
        
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_users()

