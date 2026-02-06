"""Chatbot service for generating responses."""

import logging
from typing import Dict, List, Optional

from app.config import settings
from app.services.llm_adapter import create_bedrock_adapter
from app.utils.prompts import (
    get_chatbot_prompt,
    get_chatbot_system_prompt,
    get_refinement_prompt,
)

logger = logging.getLogger(__name__)


class ChatbotService:
    """Service for generating chatbot responses."""

    def __init__(self):
        """Initialize chatbot service."""
        self.adapter = create_bedrock_adapter(model_id=settings.chatbot_model)
        self.system_prompt = get_chatbot_system_prompt()

    async def generate_response(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate a response to user message.

        Args:
            user_message: User's message
            conversation_history: Previous conversation context

        Returns:
            Generated response text
        """
        logger.info(f"Generating response for message: {user_message[:50]}...")

        messages = get_chatbot_prompt(
            user_message=user_message,
            conversation_history=conversation_history
        )

        try:
            response = await self.adapter.generate(
                messages=messages,
                system_prompt=self.system_prompt,
                temperature=0.7
            )

            logger.info(f"Response generated: {len(response)} characters")
            return response

        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")

    async def generate_response_stream(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ):
        """Generate a streaming response to user message.

        Args:
            user_message: User's message
            conversation_history: Previous conversation context

        Yields:
            Text chunks as they arrive
        """
        logger.info(f"Generating streaming response for message: {user_message[:50]}...")

        messages = get_chatbot_prompt(
            user_message=user_message,
            conversation_history=conversation_history
        )

        try:
            async for chunk in self.adapter.generate_stream(
                messages=messages,
                system_prompt=self.system_prompt,
                temperature=0.7
            ):
                yield chunk

        except Exception as e:
            logger.error(f"Streaming response generation failed: {str(e)}")
            raise Exception(f"Failed to generate streaming response: {str(e)}")

    async def refine_response(
        self,
        original_response: str,
        judge_feedback: str,
        suggestions: List[str],
        user_message: str
    ) -> str:
        """Refine a response based on judge feedback.

        Args:
            original_response: Original chatbot response
            judge_feedback: Judge's feedback
            suggestions: Specific improvement suggestions
            user_message: Original user question

        Returns:
            Refined response text
        """
        logger.info("Refining response based on judge feedback")

        messages = get_refinement_prompt(
            original_response=original_response,
            judge_feedback=judge_feedback,
            suggestions=suggestions,
            user_message=user_message
        )

        try:
            response = await self.adapter.generate(
                messages=messages,
                system_prompt=self.system_prompt,
                temperature=0.7
            )

            logger.info(f"Refined response generated: {len(response)} characters")
            return response

        except Exception as e:
            logger.error(f"Response refinement failed: {str(e)}")
            raise Exception(f"Failed to refine response: {str(e)}")


# Global chatbot service instance
_chatbot_service: Optional[ChatbotService] = None


def get_chatbot_service() -> ChatbotService:
    """Get or create chatbot service instance.

    Returns:
        ChatbotService instance
    """
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
    return _chatbot_service
