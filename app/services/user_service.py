"""
User service for managing users with SQLite database
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User, UserCreate
from app.models.db_user import DBUser
from app.core.auth import get_password_hash, verify_password
from app.database import get_db, init_db
from app.utils.logger import get_logger

logger = get_logger(__name__)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    db_user = db.query(DBUser).filter(DBUser.email == email).first()
    if db_user:
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            created_at=db_user.created_at.isoformat() if db_user.created_at else None
        )
    return None


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    db_user = db.query(DBUser).filter(DBUser.username == username).first()
    if db_user:
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            created_at=db_user.created_at.isoformat() if db_user.created_at else None
        )
    return None


def create_user(db: Session, user_create: UserCreate) -> User:
    """Create a new user"""
    try:
        # Check if user already exists
        existing_user = db.query(DBUser).filter(DBUser.email == user_create.email).first()
        if existing_user:
            raise ValueError("User with this email already exists")
        
        existing_username = db.query(DBUser).filter(DBUser.username == user_create.username).first()
        if existing_username:
            raise ValueError("User with this username already exists")
        
        # Create new user
        hashed_password = get_password_hash(user_create.password)
        
        db_user = DBUser(
            email=user_create.email,
            username=user_create.username,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        logger.info(f"Created new user: {db_user.email}")
        
        return User(
            id=db_user.id,
            email=db_user.email,
            username=db_user.username,
            created_at=db_user.created_at.isoformat() if db_user.created_at else None
        )
    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        # Rollback on any other error
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise ValueError(f"Failed to create user: {str(e)}")


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    db_user = db.query(DBUser).filter(DBUser.email == email).first()
    
    if not db_user:
        return None
    
    if not verify_password(password, db_user.hashed_password):
        return None
    
    return User(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        created_at=db_user.created_at.isoformat() if db_user.created_at else None
    )


def update_user_profile(
    db: Session,
    user_id: int,
    new_username: Optional[str] = None,
    current_password: Optional[str] = None,
    new_password: Optional[str] = None
) -> User:
    """Update user profile (username and/or password)"""
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not db_user:
        raise ValueError("User not found")

    # If password change requested, current password must be provided and valid
    if new_password:
        if not current_password or not verify_password(current_password, db_user.hashed_password):
            raise ValueError("Current password is incorrect")
        db_user.hashed_password = get_password_hash(new_password)

    # Update username if provided and changed
    if new_username and new_username != db_user.username:
        existing_username = db.query(DBUser).filter(DBUser.username == new_username).first()
        if existing_username:
            raise ValueError("User with this username already exists")
        db_user.username = new_username

    db.commit()
    db.refresh(db_user)

    return User(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        created_at=db_user.created_at.isoformat() if db_user.created_at else None
    )


def delete_user_account(db: Session, user_id: int, current_password: str) -> None:
    """Delete user account after verifying password"""
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not db_user:
        raise ValueError("User not found")

    if not verify_password(current_password, db_user.hashed_password):
        raise ValueError("Current password is incorrect")

    db.delete(db_user)
    db.commit()
