"""Pydantic models for API requests and responses."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message role types."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Chat message model."""
    id: str = Field(..., description="Unique message identifier")
    role: MessageRole = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg_123",
                "role": "user",
                "content": "What is the capital of France?",
                "timestamp": "2026-02-05T10:30:00Z",
                "metadata": {}
            }
        }


class CriterionScore(BaseModel):
    """Individual criterion evaluation score."""
    name: str = Field(..., description="Criterion name")
    score: float = Field(..., ge=0, le=100, description="Score (0-100)")
    weight: float = Field(..., ge=0, le=1, description="Criterion weight")
    threshold: float = Field(..., description="Minimum acceptable score")
    passed: bool = Field(..., description="Whether criterion met threshold")
    feedback: Optional[str] = Field(default=None, description="Specific feedback for this criterion")


class JudgeEvaluation(BaseModel):
    """Judge evaluation result."""
    overall_score: float = Field(..., ge=0, le=100, description="Weighted overall score (0-100)")
    criteria_scores: List[CriterionScore] = Field(..., description="Individual criterion scores")
    feedback: str = Field(..., description="Overall feedback from judge")
    should_regenerate: bool = Field(..., description="Whether response should be regenerated")
    suggestions: List[str] = Field(default_factory=list, description="Specific improvement suggestions")
    traffic_light: str = Field(..., description="Traffic light indicator (🟢/🟠/🔴)")

    class Config:
        json_schema_extra = {
            "example": {
                "overall_score": 75.5,
                "criteria_scores": [
                    {
                        "name": "accuracy",
                        "score": 80.0,
                        "weight": 0.25,
                        "threshold": 70,
                        "passed": True,
                        "feedback": "Information is accurate"
                    }
                ],
                "feedback": "Good response overall with minor improvements needed",
                "should_regenerate": False,
                "suggestions": ["Add more specific examples"],
                "traffic_light": "🟢"
            }
        }


class ConversationMode(str, Enum):
    """Conversation flow modes."""
    SIMPLE = "simple"  # User → Chatbot → Judge → Display
    FEEDBACK = "feedback"  # With iterative refinement
    INPUT_CRITIQUE = "input_critique"  # Judge critiques input first


class ChatRequest(BaseModel):
    """Chat request payload."""
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for history")
    mode: ConversationMode = Field(default=ConversationMode.FEEDBACK, description="Conversation mode")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is the capital of France?",
                "conversation_id": "conv_123",
                "mode": "feedback"
            }
        }


class ChatResponse(BaseModel):
    """Chat response payload."""
    conversation_id: str = Field(..., description="Conversation ID")
    response: str = Field(..., description="Chatbot response")
    evaluation: JudgeEvaluation = Field(..., description="Judge evaluation")
    iteration: int = Field(default=1, description="Iteration number (if refined)")
    history: Optional[List[Message]] = Field(default=None, description="Conversation history")


class WebSocketEventType(str, Enum):
    """WebSocket event types."""
    USER_MESSAGE = "user_message"
    USER_INPUT_EVALUATION = "user_input_evaluation"
    JUDGE_INPUT_CRITIQUE = "judge_input_critique"
    CHATBOT_GENERATING = "chatbot_generating"
    CHATBOT_CHUNK = "chatbot_chunk"
    CHATBOT_RESPONSE = "chatbot_response"
    JUDGE_EVALUATING = "judge_evaluating"
    JUDGE_CRITERION_RESULT = "judge_criterion_result"
    JUDGE_RESULT = "judge_result"
    CHATBOT_REFINING = "chatbot_refining"
    FINAL_RESPONSE = "final_response"
    ERROR = "error"


class WebSocketEvent(BaseModel):
    """WebSocket event message."""
    event: WebSocketEventType = Field(..., description="Event type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")


class Criterion(BaseModel):
    """Criterion configuration model."""
    name: str = Field(..., description="Criterion name")
    description: str = Field(..., description="Criterion description")
    weight: float = Field(..., ge=0, le=1, description="Criterion weight (0-1)")
    enabled: bool = Field(default=True, description="Whether criterion is enabled")
    threshold: float = Field(..., ge=0, le=100, description="Minimum acceptable score")
    evaluation_prompt: Optional[str] = Field(default=None, description="Evaluation question")


class CriteriaUpdateRequest(BaseModel):
    """Request to update criteria configuration."""
    criteria: Optional[List[Criterion]] = Field(default=None, description="Updated criteria list")
    active_profile: Optional[str] = Field(default=None, description="Active quality profile")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="Updated settings")
