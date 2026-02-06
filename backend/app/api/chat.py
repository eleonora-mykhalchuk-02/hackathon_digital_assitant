"""Chat API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.models import ChatRequest, ChatResponse
from app.services.orchestrator import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message.

    Args:
        request: Chat request with message and options

    Returns:
        Chat response with evaluation
    """
    try:
        orchestrator = get_orchestrator()

        conv_id, response, evaluation, iteration, input_critique = await orchestrator.process_message(
            user_message=request.message,
            conversation_id=request.conversation_id,
            mode=request.mode
        )

        # Get conversation history
        history = orchestrator.get_conversation_history(conv_id)

        return ChatResponse(
            conversation_id=conv_id,
            response=response,
            evaluation=evaluation,
            iteration=iteration,
            history=history
        )

    except Exception as e:
        logger.error(f"Chat request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.get("/chat/history/{conversation_id}")
async def get_history(conversation_id: str):
    """Get conversation history.

    Args:
        conversation_id: Conversation ID

    Returns:
        List of messages
    """
    try:
        orchestrator = get_orchestrator()
        history = orchestrator.get_conversation_history(conversation_id)

        if not history:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {"conversation_id": conversation_id, "messages": history}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")
