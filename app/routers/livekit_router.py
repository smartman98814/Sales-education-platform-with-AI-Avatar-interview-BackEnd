"""
Minimal LiveKit router for token generation only.
Frontend handles all LiveKit connections directly.
"""
import time
import json
from jose import jwt
import httpx
from typing import Optional
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
    agent_id: Optional[int] = None
    heygen_session_id: Optional[str] = None


class CreateRoomTokenResponse(BaseModel):
    """Response with LiveKit room token and connection info"""
    token: str
    url: str
    room_name: str


class DeleteRoomResponse(BaseModel):
    """Response from room deletion"""
    success: bool
    message: str


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
        agent_name = settings.livekit_agent_name
        if not agent_name:
            raise HTTPException(
                status_code=503,
                detail="LiveKit agent name not configured. Set LIVEKIT_AGENT_NAME in environment."
            )
        
        room_config = {
            "agents": [{"agentName": agent_name}]
        }
        # Use "roomConfig" (camelCase) to match TypeScript SDK serialization
        claims["roomConfig"] = room_config
        
        # Add agent metadata if provided
        metadata_dict = {}
        if request.agent_id:
            metadata_dict["agent_id"] = request.agent_id
        if request.heygen_session_id:
            metadata_dict["heygen_session_id"] = request.heygen_session_id
        
        if metadata_dict:
            claims["metadata"] = json.dumps(metadata_dict)
        
        # Log the claims structure for debugging
        logger.info(f"Token claims include roomConfig: {room_config}")
        if request.heygen_session_id:
            logger.info(f"HeyGen session_id included in participant metadata: {request.heygen_session_id}")
        
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


@router.delete(
    "/livekit/room/{room_name}",
    response_model=DeleteRoomResponse,
    summary="Delete LiveKit room"
)
async def delete_room(room_name: str):
    """
    Delete a LiveKit room via the REST API.
    This closes the room immediately and disconnects all participants including agents.
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
        # Generate JWT token for API authentication
        now = int(time.time())
        exp = now + 60  # Token expires in 1 minute (short-lived for API calls)
        
        api_claims = {
            "iss": settings.livekit_api_key,
            "nbf": now,
            "exp": exp,
            "sub": "api",
            "video": {
                "room": "",
                "roomCreate": True,
                "roomJoin": True,
                "roomList": True,
                "roomRecord": True,
                "roomAdmin": True,  # Required for deleting rooms
                "canPublish": True,
                "canSubscribe": True,
                "canPublishData": True,
            }
        }
        
        api_token = jwt.encode(api_claims, settings.livekit_api_secret, algorithm="HS256")
        
        # Extract base URL from LiveKit URL (remove wss:// or ws://)
        base_url = settings.livekit_url.replace("wss://", "https://").replace("ws://", "http://")
        
        # LiveKit REST API endpoint for deleting rooms
        api_url = f"{base_url}/twirp/livekit.RoomService/DeleteRoom"
        
        # Make DELETE request to LiveKit API
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "room": room_name
                }
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully deleted LiveKit room: {room_name}")
                return DeleteRoomResponse(
                    success=True,
                    message=f"Room '{room_name}' deleted successfully"
                )
            elif response.status_code == 404:
                # Room doesn't exist - not necessarily an error
                logger.info(f"Room '{room_name}' not found (may have already been deleted)")
                return DeleteRoomResponse(
                    success=True,
                    message=f"Room '{room_name}' not found or already deleted"
                )
            else:
                error_text = response.text
                logger.error(f"Failed to delete room '{room_name}': HTTP {response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete room: {error_text}"
                )
                
    except httpx.TimeoutException:
        logger.error(f"Timeout while deleting room '{room_name}'")
        raise HTTPException(status_code=504, detail="Timeout while deleting room")
    except Exception as e:
        logger.error(f"Error deleting LiveKit room '{room_name}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete room: {str(e)}")

