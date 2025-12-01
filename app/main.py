from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import openai_router

app = FastAPI(
    title="HeyGen Streaming Avatar API",
    description="Backend API for HeyGen Streaming Avatar application",
    version="1.0.0"
)

from app.config import settings
import os

# Get allowed origins from settings or environment variable
if settings.allowed_origins:
    allow_origins = settings.allowed_origins.split(",") if settings.allowed_origins != "*" else ["*"]
else:
    allow_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") and os.getenv("ALLOWED_ORIGINS") != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(openai_router.router, prefix="/api", tags=["openai"])

@app.get("/")
async def root():
    return {"message": "HeyGen Streaming Avatar API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

