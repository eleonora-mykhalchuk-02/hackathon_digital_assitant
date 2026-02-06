"""Orchestrator for managing conversation flow between chatbot and judge."""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from app.config import settings
from app.models import ConversationMode, JudgeEvaluation, Message, MessageRole
from app.services.chatbot import get_chatbot_service
from app.services.judge import get_judge_service

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    """Orchestrates conversation flow between chatbot and judge."""

    def __init__(self):
        """Initialize orchestrator."""
        self.chatbot = get_chatbot_service()
        self.judge = get_judge_service()
        self.conversations: Dict[str, List[Message]] = {}

    def _get_or_create_conversation(self, conversation_id: Optional[str] = None) -> Tuple[str, List[Message]]:
        """Get existing conversation or create new one.

        Args:
            conversation_id: Optional conversation ID

        Returns:
            Tuple of (conversation_id, message_history)
        """
        if conversation_id and conversation_id in self.conversations:
            return conversation_id, self.conversations[conversation_id]

        new_id = conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
        self.conversations[new_id] = []
        return new_id, self.conversations[new_id]

    def _add_message(self, conversation_id: str, role: MessageRole, content: str, metadata: Optional[Dict] = None) -> Message:
        """Add message to conversation history.

        Args:
            conversation_id: Conversation ID
            role: Message role
            content: Message content
            metadata: Optional metadata

        Returns:
            Created Message object
        """
        message = Message(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

        self.conversations[conversation_id].append(message)
        return message

    def _get_conversation_context(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get conversation history formatted for LLM.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of message dicts
        """
        history = self.conversations.get(conversation_id, [])
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in history
        ]

    async def process_simple(
        self,
        user_message: str,
        conversation_id: Optional[str] = None
    ) -> Tuple[str, str, JudgeEvaluation, int]:
        """Process message in simple mode (no feedback loop).

        Args:
            user_message: User's message
            conversation_id: Optional conversation ID

        Returns:
            Tuple of (conversation_id, response, evaluation, iteration)
        """
        logger.info(f"Processing in SIMPLE mode: {user_message[:50]}...")

        conv_id, history = self._get_or_create_conversation(conversation_id)

        # Add user message
        self._add_message(conv_id, MessageRole.USER, user_message)

        # Generate chatbot response
        context = self._get_conversation_context(conv_id)
        response = await self.chatbot.generate_response(user_message, context[:-1])  # Exclude current message

        # Evaluate response
        evaluation = await self.judge.evaluate_response(user_message, response, context[:-1])

        # Add assistant message with evaluation metadata
        self._add_message(
            conv_id,
            MessageRole.ASSISTANT,
            response,
            metadata={"judge_score": evaluation.overall_score, "iteration": 1}
        )

        return conv_id, response, evaluation, 1

    async def process_with_feedback(
        self,
        user_message: str,
        conversation_id: Optional[str] = None
    ) -> Tuple[str, str, JudgeEvaluation, int]:
        """Process message with feedback loop (iterative refinement).

        Args:
            user_message: User's message
            conversation_id: Optional conversation ID

        Returns:
            Tuple of (conversation_id, response, evaluation, iteration)
        """
        logger.info(f"Processing in FEEDBACK mode: {user_message[:50]}...")

        conv_id, history = self._get_or_create_conversation(conversation_id)

        # Add user message
        self._add_message(conv_id, MessageRole.USER, user_message)

        context = self._get_conversation_context(conv_id)

        # Initial response
        response = await self.chatbot.generate_response(user_message, context[:-1])
        evaluation = await self.judge.evaluate_response(user_message, response, context[:-1])

        iteration = 1
        max_iterations = settings.max_refinement_iterations

        # Refinement loop
        while evaluation.should_regenerate and iteration < max_iterations:
            logger.info(f"Response needs refinement (iteration {iteration + 1})")

            # Refine response based on judge feedback
            response = await self.chatbot.refine_response(
                original_response=response,
                judge_feedback=evaluation.feedback,
                suggestions=evaluation.suggestions,
                user_message=user_message
            )

            # Re-evaluate
            evaluation = await self.judge.evaluate_response(user_message, response, context[:-1])
            iteration += 1

        # Add final assistant message
        self._add_message(
            conv_id,
            MessageRole.ASSISTANT,
            response,
            metadata={
                "judge_score": evaluation.overall_score,
                "iteration": iteration,
                "refined": iteration > 1
            }
        )

        logger.info(f"Final response after {iteration} iteration(s), score: {evaluation.overall_score}")
        return conv_id, response, evaluation, iteration

    async def process_with_input_critique(
        self,
        user_message: str,
        conversation_id: Optional[str] = None
    ) -> Tuple[str, str, JudgeEvaluation, int, Optional[Dict]]:
        """Process message with input critique first.

        Args:
            user_message: User's message
            conversation_id: Optional conversation ID

        Returns:
            Tuple of (conversation_id, response, evaluation, iteration, input_critique)
        """
        logger.info(f"Processing in INPUT_CRITIQUE mode: {user_message[:50]}...")

        # Critique user input first
        input_critique = await self.judge.critique_input(user_message)

        # Then proceed with feedback loop
        conv_id, response, evaluation, iteration = await self.process_with_feedback(
            user_message, conversation_id
        )

        return conv_id, response, evaluation, iteration, input_critique

    async def process_message(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        mode: ConversationMode = ConversationMode.FEEDBACK
    ) -> Tuple[str, str, JudgeEvaluation, int, Optional[Dict]]:
        """Process user message according to specified mode.

        Args:
            user_message: User's message
            conversation_id: Optional conversation ID
            mode: Conversation mode

        Returns:
            Tuple of (conversation_id, response, evaluation, iteration, input_critique)
        """
        if mode == ConversationMode.SIMPLE:
            conv_id, response, evaluation, iteration = await self.process_simple(
                user_message, conversation_id
            )
            return conv_id, response, evaluation, iteration, None

        elif mode == ConversationMode.INPUT_CRITIQUE:
            return await self.process_with_input_critique(user_message, conversation_id)

        else:  # FEEDBACK mode (default)
            conv_id, response, evaluation, iteration = await self.process_with_feedback(
                user_message, conversation_id
            )
            return conv_id, response, evaluation, iteration, None

    def get_conversation_history(self, conversation_id: str) -> List[Message]:
        """Get conversation history.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of messages
        """
        return self.conversations.get(conversation_id, [])


# Global orchestrator instance
_orchestrator: Optional[ConversationOrchestrator] = None


def get_orchestrator() -> ConversationOrchestrator:
    """Get or create orchestrator instance.

    Returns:
        ConversationOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ConversationOrchestrator()
    return _orchestrator
