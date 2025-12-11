from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import agent_router, auth_router, livekit_router
from app.config import settings

app = FastAPI(
    title="AI Avatar Interview API",
    description="Backend API for AI avatar interviews with LiveKit integration",
    version="2.0.0"
)

# Configure CORS
allow_origins = (
    ["*"] if not settings.allowed_origins or settings.allowed_origins == "*" 
    else settings.allowed_origins.split(",")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api")
app.include_router(agent_router.router, prefix="/api", tags=["agents"])
app.include_router(livekit_router.router, prefix="/api", tags=["livekit"])

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    from app.database import init_db
    from app.utils.logger import get_logger
    
    logger = get_logger(__name__)
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
    
    # Note: OpenAI agents are handled by LiveKit agents (separate process)
    # LiveKit token generation is handled by /api/livekit/token endpoint

@app.get("/")
async def root():
    return {
        "message": "AI Avatar Interview API",
        "version": "2.0.0",
        "description": "Backend API for AI avatar interviews with LiveKit token generation"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

