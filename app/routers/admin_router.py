"""
Admin panel router with CRUD operations for users and conversations
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func as sql_func
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime
import json

from app.database import get_db
from app.models.db_user import DBUser
from app.models.conversation import Conversation, ConversationMessage
from app.routers.auth_router import get_current_user
from app.core.auth import get_password_hash
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ==================== Admin Authorization ====================

async def get_admin_user(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify that current user is an admin"""
    # Get full user from database to check role
    db_user = db.query(DBUser).filter(DBUser.email == current_user.email).first()
    if not db_user or (db_user.role or "user") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return db_user


# ==================== Schemas ====================

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    created_at: datetime
    conversation_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class UserCreateRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: str = "user"


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


class ConversationListItemResponse(BaseModel):
    id: int
    user_id: int
    user_email: str
    user_username: str
    agent_id: int
    agent_name: str
    agent_role: Optional[str]
    room_name: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    final_score: Optional[float]
    tier: Optional[str]
    message_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(BaseModel):
    id: int
    user_id: int
    user_email: str
    user_username: str
    agent_id: int
    agent_name: str
    agent_role: Optional[str]
    room_name: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    final_score: Optional[float]
    tier: Optional[str]
    pre_deduction_total: Optional[float]
    raw_scores: Optional[dict] = None
    weighted_points: Optional[dict] = None
    deductions: Optional[List[dict]] = None
    strengths: Optional[List[str]] = None
    coaching_items: Optional[List[str]] = None
    detailed_feedback: Optional[str] = None
    messages: List[dict] = []
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationUpdateRequest(BaseModel):
    final_score: Optional[float] = None
    tier: Optional[str] = None
    detailed_feedback: Optional[str] = None


# ==================== User CRUD ====================

@router.get("/admin/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)"""
    query = db.query(DBUser)
    
    # Search filter
    if search:
        query = query.filter(
            (DBUser.email.ilike(f"%{search}%")) |
            (DBUser.username.ilike(f"%{search}%"))
        )
    
    # Get users with conversation count
    users = query.order_by(desc(DBUser.created_at)).offset(skip).limit(limit).all()
    
    result = []
    for user in users:
        conv_count = db.query(Conversation).filter(Conversation.user_id == user.id).count()
        result.append(UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            role=user.role or "user",
            created_at=user.created_at,
            conversation_count=conv_count
        ))
    
    return result


@router.get("/admin/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only)"""
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    conv_count = db.query(Conversation).filter(Conversation.user_id == user.id).count()
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role or "user",
        created_at=user.created_at,
        conversation_count=conv_count
    )


@router.post("/admin/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreateRequest,
    current_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Create new user (admin only)"""
    # Check if email already exists
    existing = db.query(DBUser).filter(DBUser.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Check if username already exists
    existing_username = db.query(DBUser).filter(DBUser.username == user_data.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Validate role
    if user_data.role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    new_user = DBUser(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        role=user_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"Admin {current_user.email} created user {new_user.email}")
    
    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        username=new_user.username,
        role=new_user.role or "user",
        created_at=new_user.created_at,
        conversation_count=0
    )


@router.put("/admin/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    current_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update user (admin only)"""
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update fields
    if user_data.email is not None:
        # Check if email is taken by another user
        existing = db.query(DBUser).filter(DBUser.email == user_data.email, DBUser.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already taken")
        user.email = user_data.email
    
    if user_data.username is not None:
        # Check if username is taken by another user
        existing = db.query(DBUser).filter(DBUser.username == user_data.username, DBUser.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = user_data.username
    
    if user_data.password is not None:
        user.hashed_password = get_password_hash(user_data.password)
    
    if user_data.role is not None:
        if user_data.role not in ["user", "admin"]:
            raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
        user.role = user_data.role
    
    db.commit()
    db.refresh(user)
    
    conv_count = db.query(Conversation).filter(Conversation.user_id == user.id).count()
    
    logger.info(f"Admin {current_user.email} updated user {user.email}")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        role=user.role or "user",
        created_at=user.created_at,
        conversation_count=conv_count
    )


@router.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete user (admin only)"""
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Delete related conversations and messages (cascade)
    conversations = db.query(Conversation).filter(Conversation.user_id == user_id).all()
    for conv in conversations:
        db.query(ConversationMessage).filter(ConversationMessage.conversation_id == conv.id).delete()
    db.query(Conversation).filter(Conversation.user_id == user_id).delete()
    
    # Delete user
    db.delete(user)
    db.commit()
    
    logger.info(f"Admin {current_user.email} deleted user {user.email}")
    
    return None


# ==================== Conversation CRUD ====================

@router.get("/admin/conversations", response_model=List[ConversationListItemResponse])
async def get_all_conversations(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all conversations (admin only)"""
    query = db.query(Conversation, DBUser).join(DBUser, Conversation.user_id == DBUser.id)
    
    # Filters
    if user_id:
        query = query.filter(Conversation.user_id == user_id)
    if agent_id:
        query = query.filter(Conversation.agent_id == agent_id)
    if search:
        query = query.filter(
            (DBUser.email.ilike(f"%{search}%")) |
            (DBUser.username.ilike(f"%{search}%")) |
            (Conversation.agent_name.ilike(f"%{search}%"))
        )
    
    results = query.order_by(desc(Conversation.created_at)).offset(skip).limit(limit).all()
    
    response_list = []
    for conv, user in results:
        msg_count = db.query(ConversationMessage).filter(ConversationMessage.conversation_id == conv.id).count()
        response_list.append(ConversationListItemResponse(
            id=conv.id,
            user_id=conv.user_id,
            user_email=user.email,
            user_username=user.username,
            agent_id=conv.agent_id,
            agent_name=conv.agent_name,
            agent_role=conv.agent_role,
            room_name=conv.room_name,
            started_at=conv.started_at,
            ended_at=conv.ended_at,
            final_score=conv.final_score,
            tier=conv.tier,
            message_count=msg_count,
            created_at=conv.created_at
        ))
    
    return response_list


@router.get("/admin/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    current_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get conversation detail (admin only)"""
    result = db.query(Conversation, DBUser).join(DBUser, Conversation.user_id == DBUser.id)\
        .filter(Conversation.id == conversation_id).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conv, user = result
    
    # Get messages
    messages = db.query(ConversationMessage)\
        .filter(ConversationMessage.conversation_id == conversation_id)\
        .order_by(ConversationMessage.timestamp_ms).all()
    
    messages_data = [
        {
            "id": msg.id,
            "sender": msg.sender,
            "text": msg.text,
            "timestamp_ms": msg.timestamp_ms,
            "participant_id": msg.participant_id,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        }
        for msg in messages
    ]
    
    # Parse score data
    raw_scores = json.loads(conv.raw_scores_json) if conv.raw_scores_json else None
    weighted_points = json.loads(conv.weighted_points_json) if conv.weighted_points_json else None
    deductions = json.loads(conv.deductions_json) if conv.deductions_json else None
    strengths = json.loads(conv.strengths_json) if conv.strengths_json else None
    coaching_items = json.loads(conv.coaching_items_json) if conv.coaching_items_json else None
    
    return ConversationDetailResponse(
        id=conv.id,
        user_id=conv.user_id,
        user_email=user.email,
        user_username=user.username,
        agent_id=conv.agent_id,
        agent_name=conv.agent_name,
        agent_role=conv.agent_role,
        room_name=conv.room_name,
        started_at=conv.started_at,
        ended_at=conv.ended_at,
        final_score=conv.final_score,
        tier=conv.tier,
        pre_deduction_total=conv.pre_deduction_total,
        raw_scores=raw_scores,
        weighted_points=weighted_points,
        deductions=deductions,
        strengths=strengths,
        coaching_items=coaching_items,
        detailed_feedback=conv.detailed_feedback,
        messages=messages_data,
        created_at=conv.created_at
    )


@router.put("/admin/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def update_conversation(
    conversation_id: int,
    conv_data: ConversationUpdateRequest,
    current_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update conversation (admin only)"""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conv_data.final_score is not None:
        conv.final_score = conv_data.final_score
    if conv_data.tier is not None:
        conv.tier = conv_data.tier
    if conv_data.detailed_feedback is not None:
        conv.detailed_feedback = conv_data.detailed_feedback
    
    db.commit()
    db.refresh(conv)
    
    # Get user info
    user = db.query(DBUser).filter(DBUser.id == conv.user_id).first()
    
    # Get messages
    messages = db.query(ConversationMessage)\
        .filter(ConversationMessage.conversation_id == conversation_id)\
        .order_by(ConversationMessage.timestamp_ms).all()
    
    messages_data = [
        {
            "id": msg.id,
            "sender": msg.sender,
            "text": msg.text,
            "timestamp_ms": msg.timestamp_ms,
            "participant_id": msg.participant_id,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        }
        for msg in messages
    ]
    
    # Parse score data
    raw_scores = json.loads(conv.raw_scores_json) if conv.raw_scores_json else None
    weighted_points = json.loads(conv.weighted_points_json) if conv.weighted_points_json else None
    deductions = json.loads(conv.deductions_json) if conv.deductions_json else None
    strengths = json.loads(conv.strengths_json) if conv.strengths_json else None
    coaching_items = json.loads(conv.coaching_items_json) if conv.coaching_items_json else None
    
    logger.info(f"Admin {current_user.email} updated conversation {conversation_id}")
    
    return ConversationDetailResponse(
        id=conv.id,
        user_id=conv.user_id,
        user_email=user.email if user else "",
        user_username=user.username if user else "",
        agent_id=conv.agent_id,
        agent_name=conv.agent_name,
        agent_role=conv.agent_role,
        room_name=conv.room_name,
        started_at=conv.started_at,
        ended_at=conv.ended_at,
        final_score=conv.final_score,
        tier=conv.tier,
        pre_deduction_total=conv.pre_deduction_total,
        raw_scores=raw_scores,
        weighted_points=weighted_points,
        deductions=deductions,
        strengths=strengths,
        coaching_items=coaching_items,
        detailed_feedback=conv.detailed_feedback,
        messages=messages_data,
        created_at=conv.created_at
    )


@router.delete("/admin/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    current_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete conversation (admin only)"""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete messages (cascade should handle this, but being explicit)
    db.query(ConversationMessage).filter(ConversationMessage.conversation_id == conversation_id).delete()
    
    # Delete conversation
    db.delete(conv)
    db.commit()
    
    logger.info(f"Admin {current_user.email} deleted conversation {conversation_id}")
    
    return None


# ==================== Statistics ====================

@router.get("/admin/stats")
async def get_admin_stats(
    current_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin statistics"""
    total_users = db.query(DBUser).count()
    total_conversations = db.query(Conversation).count()
    total_messages = db.query(ConversationMessage).count()
    
    # Average score
    avg_score = db.query(sql_func.avg(Conversation.final_score))\
        .filter(Conversation.final_score.isnot(None)).scalar()
    
    # Conversations by tier
    tier_counts = db.query(Conversation.tier, sql_func.count(Conversation.id))\
        .filter(Conversation.tier.isnot(None))\
        .group_by(Conversation.tier).all()
    
    return {
        "total_users": total_users,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "average_score": float(avg_score) if avg_score else None,
        "tier_distribution": {tier: count for tier, count in tier_counts}
    }

