"""WebSocket handlers for real-time chat."""

import json
import logging
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models import ConversationMode, MessageRole, WebSocketEventType
from app.services.orchestrator import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and store WebSocket connection.

        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        """Remove WebSocket connection.

        Args:
            client_id: Client identifier
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_event(self, client_id: str, event_type: WebSocketEventType, data: Dict):
        """Send event to client.

        Args:
            client_id: Client identifier
            event_type: Event type
            data: Event data
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            message = {
                "event": event_type.value,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat.

    Args:
        websocket: WebSocket connection
    """
    client_id = f"client_{id(websocket)}"
    await manager.connect(websocket, client_id)

    orchestrator = get_orchestrator()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            event_type = data.get("event")
            event_data = data.get("data", {})

            if event_type == "evaluate_input":
                # Handle real-time user input evaluation
                user_input = event_data.get("input", "")
                
                logger.info(f"Evaluating user input from {client_id}: {user_input[:50]}...")
                
                try:
                    # Stream criterion evaluations for user input as they complete
                    criterion_count = 0
                    async for criterion_score in orchestrator.judge.evaluate_user_input(user_input):
                        criterion_count += 1
                        logger.info(f"Sending criterion {criterion_count}: {criterion_score.name} (score: {criterion_score.score})")
                        await manager.send_event(
                            client_id,
                            WebSocketEventType.USER_INPUT_EVALUATION,
                            {
                                "criterion": criterion_score.model_dump()
                            }
                        )
                    logger.info(f"User input evaluation complete. Sent {criterion_count} criteria.")
                except Exception as e:
                    logger.error(f"Error evaluating user input: {str(e)}", exc_info=True)
                    await manager.send_event(
                        client_id,
                        WebSocketEventType.ERROR,
                        {"error": f"Failed to evaluate input: {str(e)}"}
                    )

            elif event_type == "user_message":
                user_message = event_data.get("message", "")
                conversation_id = event_data.get("conversation_id")
                mode_str = event_data.get("mode", "input_critique")
                skip_user_evaluation = event_data.get("skip_user_evaluation", False)

                try:
                    mode = ConversationMode(mode_str)
                except ValueError:
                    mode = ConversationMode.INPUT_CRITIQUE

                logger.info(f"Received message from {client_id}: {user_message[:50]}...")

                try:
                    # STEP 1: Evaluate user input FIRST (unless skipped for retry)
                    if not skip_user_evaluation:
                        logger.info("[Step 1] Starting user input evaluation...")
                        criterion_count = 0
                        async for criterion_score in orchestrator.judge.evaluate_user_input(user_message):
                            criterion_count += 1
                            logger.info(f"[Step 1] Sending user criterion {criterion_count}: {criterion_score.name}")
                            await manager.send_event(
                                client_id,
                                WebSocketEventType.USER_INPUT_EVALUATION,
                                {
                                    "criterion": criterion_score.model_dump(),
                                    "message_id": event_data.get("message_id")
                                }
                            )
                        logger.info(f"[Step 1] User input evaluation complete. Sent {criterion_count} criteria.")
                    else:
                        logger.info("[Step 1] Skipping user input evaluation (retry)")
                    
                    # STEP 2: Generate response AFTER user evaluation is complete (or skipped)
                    logger.info("[Step 2] Starting response generation...")
                    
                    # Send chatbot generating event
                    await manager.send_event(
                        client_id,
                        WebSocketEventType.CHATBOT_GENERATING,
                        {"message": "Generating response..."}
                    )

                    # Start streaming response
                    conv_id, history = orchestrator._get_or_create_conversation(conversation_id)
                    orchestrator._add_message(conv_id, orchestrator.chatbot.MessageRole.USER if hasattr(orchestrator.chatbot, 'MessageRole') else MessageRole.USER, user_message)
                    
                    context = orchestrator._get_conversation_context(conv_id)
                    
                    # Stream the response
                    full_response = ""
                    async for chunk in orchestrator.chatbot.generate_response_stream(user_message, context[:-1]):
                        full_response += chunk
                        await manager.send_event(
                            client_id,
                            WebSocketEventType.CHATBOT_CHUNK,
                            {"chunk": chunk}
                        )
                    
                    logger.info("[Step 2] Response generation complete")
                    
                    # Send complete response
                    await manager.send_event(
                        client_id,
                        WebSocketEventType.CHATBOT_RESPONSE,
                        {
                            "response": full_response,
                            "conversation_id": conv_id,
                            "iteration": 1
                        }
                    )

                    # STEP 3: Evaluate agent response AFTER response is generated
                    logger.info("[Step 3] Starting agent response evaluation...")
                    
                    # Send judge evaluating event
                    await manager.send_event(
                        client_id,
                        WebSocketEventType.JUDGE_EVALUATING,
                        {"message": "Evaluating response quality..."}
                    )

                    # Stream criterion evaluations as they complete
                    all_criteria = []
                    async for criterion_score in orchestrator.judge.evaluate_response_streaming(user_message, full_response, context[:-1]):
                        all_criteria.append(criterion_score)
                        logger.info(f"[Step 3] Sending agent criterion: {criterion_score.name}")
                        # Send individual criterion result immediately
                        await manager.send_event(
                            client_id,
                            WebSocketEventType.JUDGE_CRITERION_RESULT,
                            {
                                "criterion": criterion_score.model_dump(),
                                "conversation_id": conv_id
                            }
                        )
                    
                    logger.info(f"[Step 3] Agent response evaluation complete. Sent {len(all_criteria)} criteria.")
                    
                    # Calculate final evaluation
                    total_weighted_score = sum(c.score * c.weight for c in all_criteria)
                    total_weight = sum(c.weight for c in all_criteria)
                    overall_score = total_weighted_score / total_weight if total_weight > 0 else 0
                    
                    overall_threshold = orchestrator.judge.criteria_config.overall_threshold
                    should_regenerate = overall_score < overall_threshold
                    traffic_light = orchestrator.judge._calculate_traffic_light(overall_score)
                    
                    from app.models import JudgeEvaluation
                    evaluation = JudgeEvaluation(
                        overall_score=round(overall_score, 2),
                        criteria_scores=all_criteria,
                        feedback="Evaluation complete",
                        should_regenerate=should_regenerate,
                        suggestions=[],
                        traffic_light=traffic_light
                    )
                    
                    # Add assistant message with evaluation
                    orchestrator._add_message(
                        conv_id,
                        MessageRole.ASSISTANT,
                        full_response,
                        metadata={"judge_score": evaluation.overall_score, "iteration": 1}
                    )

                    # Send complete judge evaluation
                    await manager.send_event(
                        client_id,
                        WebSocketEventType.JUDGE_RESULT,
                        {
                            "evaluation": evaluation.model_dump(),
                            "conversation_id": conv_id
                        }
                    )

                    # Send final response event
                    await manager.send_event(
                        client_id,
                        WebSocketEventType.FINAL_RESPONSE,
                        {
                            "conversation_id": conv_id,
                            "response": full_response,
                            "evaluation": evaluation.model_dump(),
                            "iteration": 1
                        }
                    )

                except Exception as e:
                    logger.error(f"Error processing message: {str(e)}")
                    await manager.send_event(
                        client_id,
                        WebSocketEventType.ERROR,
                        {"error": str(e)}
                    )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(client_id)
