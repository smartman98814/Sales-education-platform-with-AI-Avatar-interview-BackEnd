"""
Authentication router
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.schemas.auth_schemas import SignUpRequest, SignInRequest, AuthResponse
from app.services.user_service import create_user, authenticate_user, get_user_by_email
from app.core.auth import create_access_token, decode_access_token
from app.models.user import User
from app.database import get_db
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_email(db, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignUpRequest, db: Session = Depends(get_db)):
    """Sign up a new user"""
    try:
        # Create user
        user = create_user(db, request)
        
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        
        logger.info(f"User signed up: {user.email}")
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "created_at": user.created_at
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during signup"
        )


@router.post("/signin", response_model=AuthResponse)
async def signin(request: SignInRequest, db: Session = Depends(get_db)):
    """Sign in an existing user"""
    user = authenticate_user(db, request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    logger.info(f"User signed in: {user.email}")
    
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user={
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "created_at": user.created_at
        }
    )


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "created_at": current_user.created_at
    }


@router.post("/logout")
async def logout():
    """Logout (client-side token removal)"""
    return {"message": "Successfully logged out"}

