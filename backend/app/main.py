"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, criteria, websocket
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Args:
        app: FastAPI application
    """
    logger.info("Starting LLM Judge + Chatbot application...")
    logger.info(f"AWS Region: {settings.aws_region}")
    logger.info(f"Chatbot Model: {settings.chatbot_model}")
    logger.info(f"Judge Model: {settings.judge_model}")

    yield

    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title="LLM Judge + Chatbot API",
    description="API for LLM Judge + Chatbot proof of concept",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(criteria.router)
app.include_router(websocket.router)


@app.get("/")
async def root():
    """Root endpoint - health check.

    Returns:
        Status message
    """
    return {
        "status": "healthy",
        "service": "LLM Judge + Chatbot",
        "version": "0.1.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "chatbot_model": settings.chatbot_model,
        "judge_model": settings.judge_model
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
