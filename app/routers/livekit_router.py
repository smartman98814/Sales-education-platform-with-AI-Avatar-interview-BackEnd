"""
Minimal LiveKit router for token generation only.
Frontend handles all LiveKit connections directly.
"""
import time
import json
import jwt
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Use manual JWT encoding with agent configuration
# The livekit Python package structure differs from the TypeScript SDK
# Manual JWT encoding works reliably and includes agent configuration
LIVEKIT_SDK_AVAILABLE = False

router = APIRouter()


class CreateRoomTokenRequest(BaseModel):
    """Request to create a LiveKit room token"""
    room_name: str
    participant_name: str
    agent_id: int = None


class CreateRoomTokenResponse(BaseModel):
    """Response with LiveKit room token and connection info"""
    token: str
    url: str
    room_name: str


@router.post(
    "/livekit/token",
    response_model=CreateRoomTokenResponse,
    summary="Create LiveKit room access token"
)
async def create_room_token(request: CreateRoomTokenRequest):
    """
    Create a LiveKit access token for joining a room.
    This is a minimal endpoint - frontend handles all LiveKit connections.
    """
    if not settings.livekit_url:
        raise HTTPException(
            status_code=503,
            detail="LiveKit URL not configured. Set LIVEKIT_URL in environment."
        )
    
    if not settings.livekit_api_key or not settings.livekit_api_secret:
        raise HTTPException(
            status_code=503,
            detail="LiveKit API credentials not configured. Set LIVEKIT_API_KEY and LIVEKIT_API_SECRET."
        )
    
    try:
        # Use manual JWT encoding with agent configuration
        # This matches the working implementation and reliably includes agent config
        now = int(time.time())
        exp = now + 3600  # Token expires in 1 hour
        
        # Build token claims
        claims = {
            "iss": settings.livekit_api_key,
            "nbf": now,
            "exp": exp,
            "sub": request.participant_name,
            "video": {
                "room": request.room_name,
                "roomJoin": True,
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True,
            }
        }
        
        # Add agent configuration to automatically dispatch agent
        # This is the key fix - adding room configuration with agent name
        # Note: Must use "agentName" (camelCase) to match LiveKit protocol
        # The TypeScript SDK uses "roomConfig" (camelCase), so we use that too
        agent_name = settings.livekit_agent_name or "Dakota-1e0"
        room_config = {
            "agents": [{"agentName": agent_name}]
        }
        # Use "roomConfig" (camelCase) to match TypeScript SDK serialization
        claims["roomConfig"] = room_config
        
        # Add agent metadata if provided
        if request.agent_id:
            claims["metadata"] = f'{{"agent_id": {request.agent_id}}}'
        
        # Log the claims structure for debugging
        logger.info(f"Token claims include roomConfig: {room_config}")
        
        # Generate JWT token using PyJWT
        token = jwt.encode(claims, settings.livekit_api_secret, algorithm="HS256")
        
        logger.info(f"Created LiveKit token for room '{request.room_name}', participant '{request.participant_name}', agent '{agent_name}'")
        logger.debug(f"Token claims structure: {json.dumps(claims, indent=2)}")
        
        return CreateRoomTokenResponse(
            token=token,
            url=settings.livekit_url,
            room_name=request.room_name,
        )
    except Exception as e:
        logger.error(f"Error creating LiveKit token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create token: {str(e)}")



