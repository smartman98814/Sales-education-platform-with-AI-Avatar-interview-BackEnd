"""
Conversation history and management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
import json

from app.database import get_db
from app.models.conversation import Conversation, ConversationMessage
from app.models.db_user import DBUser as User
from app.routers.auth_router import get_current_user
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class MessageCreate(BaseModel):
    text: str
    sender: str  # 'user' or 'agent'
    timestamp_ms: int
    participant_id: Optional[str] = None


class ConversationCreate(BaseModel):
    agent_id: int
    agent_name: str
    agent_role: Optional[str] = None
    room_name: Optional[str] = None
    messages: List[MessageCreate]
    started_at: Optional[datetime] = None


class ScoreData(BaseModel):
    final_score: float
    tier: str
    pre_deduction_total: float
    raw_scores: Dict[str, int]
    weighted_points: Dict[str, int]
    deductions: List[Dict[str, Any]]
    strengths: List[str]
    coaching_items: List[str]
    detailed_feedback: str


class ConversationSaveRequest(BaseModel):
    conversation: ConversationCreate
    score_data: Optional[ScoreData] = None


class ConversationResponse(BaseModel):
    id: int
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


class ConversationDetailResponse(ConversationResponse):
    messages: List[Dict[str, Any]]
    score_data: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    summary="Save conversation history"
)
async def save_conversation(
    request: ConversationSaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save a conversation/interview session with optional scoring data.
    """
    try:
        conversation = request.conversation
        score_data = request.score_data
        
        # Create conversation record
        db_conversation = Conversation(
            user_id=current_user.id,
            agent_id=conversation.agent_id,
            agent_name=conversation.agent_name,
            agent_role=conversation.agent_role,
            room_name=conversation.room_name,
            started_at=conversation.started_at or datetime.utcnow(),
            ended_at=datetime.utcnow()
        )
        
        # Add scoring data if provided
        if score_data:
            db_conversation.final_score = score_data.final_score
            db_conversation.tier = score_data.tier
            db_conversation.pre_deduction_total = score_data.pre_deduction_total
            db_conversation.raw_scores_json = json.dumps(score_data.raw_scores)
            db_conversation.weighted_points_json = json.dumps(score_data.weighted_points)
            db_conversation.deductions_json = json.dumps(score_data.deductions)
            db_conversation.strengths_json = json.dumps(score_data.strengths)
            db_conversation.coaching_items_json = json.dumps(score_data.coaching_items)
            db_conversation.detailed_feedback = score_data.detailed_feedback
        
        db.add(db_conversation)
        db.flush()  # Get the ID
        
        # Save messages
        for msg in conversation.messages:
            db_message = ConversationMessage(
                conversation_id=db_conversation.id,
                sender=msg.sender,
                text=msg.text,
                timestamp_ms=msg.timestamp_ms,
                participant_id=msg.participant_id
            )
            db.add(db_message)
        
        db.commit()
        db.refresh(db_conversation)
        
        logger.info(f"Saved conversation {db_conversation.id} with {len(conversation.messages)} messages")
        
        return ConversationResponse(
            id=db_conversation.id,
            agent_id=db_conversation.agent_id,
            agent_name=db_conversation.agent_name,
            agent_role=db_conversation.agent_role,
            room_name=db_conversation.room_name,
            started_at=db_conversation.started_at,
            ended_at=db_conversation.ended_at,
            final_score=db_conversation.final_score,
            tier=db_conversation.tier,
            message_count=len(conversation.messages),
            created_at=db_conversation.created_at
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save conversation: {str(e)}")


@router.get(
    "/conversations",
    response_model=List[ConversationResponse],
    summary="Get user's conversation history"
)
async def get_conversations(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of user's conversations, most recent first.
    """
    try:
        conversations = db.query(Conversation)\
            .filter(Conversation.user_id == current_user.id)\
            .order_by(desc(Conversation.created_at))\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        result = []
        for conv in conversations:
            message_count = db.query(ConversationMessage)\
                .filter(ConversationMessage.conversation_id == conv.id)\
                .count()
            
            result.append(ConversationResponse(
                id=conv.id,
                agent_id=conv.agent_id,
                agent_name=conv.agent_name,
                agent_role=conv.agent_role,
                room_name=conv.room_name,
                started_at=conv.started_at,
                ended_at=conv.ended_at,
                final_score=conv.final_score,
                tier=conv.tier,
                message_count=message_count,
                created_at=conv.created_at
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching conversations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get detailed conversation with messages and scoring"
)
async def get_conversation_detail(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get full conversation details including all messages and scoring data.
    """
    try:
        conversation = db.query(Conversation)\
            .filter(Conversation.id == conversation_id)\
            .filter(Conversation.user_id == current_user.id)\
            .first()
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Get messages
        messages = db.query(ConversationMessage)\
            .filter(ConversationMessage.conversation_id == conversation_id)\
            .order_by(ConversationMessage.timestamp_ms)\
            .all()
        
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
        score_data = None
        if conversation.final_score is not None:
            score_data = {
                "final_score": conversation.final_score,
                "tier": conversation.tier,
                "pre_deduction_total": conversation.pre_deduction_total,
                "raw_scores": json.loads(conversation.raw_scores_json) if conversation.raw_scores_json else {},
                "weighted_points": json.loads(conversation.weighted_points_json) if conversation.weighted_points_json else {},
                "deductions": json.loads(conversation.deductions_json) if conversation.deductions_json else [],
                "strengths": json.loads(conversation.strengths_json) if conversation.strengths_json else [],
                "coaching_items": json.loads(conversation.coaching_items_json) if conversation.coaching_items_json else [],
                "detailed_feedback": conversation.detailed_feedback
            }
        
        return ConversationDetailResponse(
            id=conversation.id,
            agent_id=conversation.agent_id,
            agent_name=conversation.agent_name,
            agent_role=conversation.agent_role,
            room_name=conversation.room_name,
            started_at=conversation.started_at,
            ended_at=conversation.ended_at,
            final_score=conversation.final_score,
            tier=conversation.tier,
            message_count=len(messages_data),
            created_at=conversation.created_at,
            messages=messages_data,
            score_data=score_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation detail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation: {str(e)}")

