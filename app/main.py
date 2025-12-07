from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import agent_router, auth_router
from app.config import settings

app = FastAPI(
    title="AI Agents API",
    description="Backend API with 10 unique AI agents sharing a knowledge base",
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

@app.on_event("startup")
async def startup_event():
    """Initialize database and agent manager on startup"""
    from app.database import init_db
    from app.services import agent_manager
    from app.utils.logger import get_logger
    
    logger = get_logger(__name__)
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
    
    # Initialize agent manager if OpenAI API key is configured
    if not settings.openai_api_key:
        logger.warning("OpenAI API key not configured. Use POST /api/agents/initialize after setting OPENAI_API_KEY.")
        return
    
    try:
        agent_manager.initialize()
        logger.info("Agent manager initialized. Call POST /api/agents/initialize to create agents.")
    except Exception as e:
        logger.warning(f"Could not initialize agent manager: {str(e)}")

@app.get("/")
async def root():
    return {
        "message": "AI Agents API",
        "version": "2.0.0",
        "agents": 10,
        "description": "10 unique AI agent personalities with shared knowledge base"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

