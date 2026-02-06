"""Judge service for evaluating chatbot responses and user inputs."""

import logging
from typing import Dict, List, Optional

from app.config import criteria_config, settings
from app.models import CriterionScore, JudgeEvaluation
from app.services.llm_adapter import create_bedrock_adapter
from app.utils.prompts import (
    get_input_critique_prompt,
    get_judge_evaluation_prompt,
    get_judge_system_prompt,
)

logger = logging.getLogger(__name__)


class JudgeService:
    """Service for judging chatbot responses and user inputs."""

    def __init__(self):
        """Initialize judge service."""
        self.adapter = create_bedrock_adapter(model_id=settings.judge_model)
        self.criteria_config = criteria_config

    def _calculate_traffic_light(self, score: float) -> str:
        """Determine traffic light indicator based on score.

        Args:
            score: Overall score (0-100)

        Returns:
            Traffic light emoji (🟢/🟠/🔴)
        """
        thresholds = self.criteria_config.traffic_light_thresholds
        green_threshold = thresholds.get("green_threshold", 70)
        orange_threshold = thresholds.get("orange_threshold", 40)

        if score >= green_threshold:
            return "🟢"
        elif score >= orange_threshold:
            return "🟠"
        else:
            return "🔴"

    async def evaluate_response(
        self,
        user_message: str,
        chatbot_response: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> JudgeEvaluation:
        """Evaluate a chatbot response against configured criteria.

        Args:
            user_message: User's question
            chatbot_response: Chatbot's response
            conversation_history: Previous conversation context

        Returns:
            JudgeEvaluation with scores and feedback
        """
        logger.info("Evaluating chatbot response")

        # Get enabled criteria
        criteria = self.criteria_config.enabled_criteria
        if not criteria:
            raise ValueError("No enabled criteria found in configuration")

        # Build evaluation prompt
        system_prompt = get_judge_system_prompt(criteria)
        evaluation_prompt = get_judge_evaluation_prompt(
            user_message=user_message,
            chatbot_response=chatbot_response,
            conversation_history=conversation_history
        )

        messages = [{"role": "user", "content": evaluation_prompt}]

        try:
            # Get structured evaluation from judge LLM
            result = await self.adapter.generate_structured(
                messages=messages,
                system_prompt=system_prompt
            )

            # Parse and validate results
            scores = result.get("scores", {})
            feedback_dict = result.get("feedback", {})
            overall_feedback = result.get("overall_feedback", "No feedback provided")
            suggestions = result.get("suggestions", [])

            # Build criterion scores
            criterion_scores: List[CriterionScore] = []
            total_weighted_score = 0.0
            total_weight = 0.0

            for criterion in criteria:
                name = criterion["name"]
                weight = criterion["weight"]
                threshold = criterion["threshold"]

                score = scores.get(name, 0)
                passed = score >= threshold
                crit_feedback = feedback_dict.get(name, "")

                criterion_scores.append(CriterionScore(
                    name=name,
                    score=score,
                    weight=weight,
                    threshold=threshold,
                    passed=passed,
                    feedback=crit_feedback
                ))

                total_weighted_score += score * weight
                total_weight += weight

            # Calculate overall score
            overall_score = total_weighted_score / total_weight if total_weight > 0 else 0

            # Determine if regeneration needed
            overall_threshold = self.criteria_config.overall_threshold
            should_regenerate = overall_score < overall_threshold

            # Get traffic light indicator
            traffic_light = self._calculate_traffic_light(overall_score)

            evaluation = JudgeEvaluation(
                overall_score=round(overall_score, 2),
                criteria_scores=criterion_scores,
                feedback=overall_feedback,
                should_regenerate=should_regenerate,
                suggestions=suggestions,
                traffic_light=traffic_light
            )

            logger.info(f"Evaluation complete: score={overall_score:.2f}, traffic_light={traffic_light}")
            return evaluation

        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            raise Exception(f"Failed to evaluate response: {str(e)}")

    async def evaluate_response_streaming(
        self,
        user_message: str,
        chatbot_response: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ):
        """Evaluate a chatbot response and yield criterion results as they complete.

        Args:
            user_message: User's question
            chatbot_response: Chatbot's response
            conversation_history: Previous conversation context

        Yields:
            CriterionScore objects as each criterion is evaluated
        """
        logger.info("Starting streaming evaluation of chatbot response")

        # Get enabled criteria
        criteria = self.criteria_config.enabled_criteria
        if not criteria:
            raise ValueError("No enabled criteria found in configuration")

        criterion_scores: List[CriterionScore] = []
        total_weighted_score = 0.0
        total_weight = 0.0

        # Evaluate each criterion individually
        for criterion in criteria:
            name = criterion["name"]
            weight = criterion["weight"]
            threshold = criterion["threshold"]
            description = criterion.get("description", "")
            eval_prompt = criterion.get("evaluation_prompt", "")

            # Build prompt for this specific criterion
            criterion_prompt = f"""Evalueer het volgende chatbot-antwoord op basis van het criterium '{name}': {description}

Gebruikersvraag: {user_message}

Chatbot Antwoord: {chatbot_response}

Evaluatievraag: {eval_prompt}

Geef een score van 0-100 en beknopte feedback in het Nederlands. Return ALLEEN geldige JSON met deze structuur:
{{
  "score": <nummer>,
  "feedback": "<tekst>"
}}"""

            messages = [{"role": "user", "content": criterion_prompt}]

            try:
                result = await self.adapter.generate_structured(
                    messages=messages,
                    system_prompt="Je bent een expert evaluator. Geef objectieve, constructieve beoordelingen in het Nederlands."
                )

                score = result.get("score", 0)
                feedback = result.get("feedback", "")
                passed = score >= threshold

                criterion_score = CriterionScore(
                    name=name,
                    score=score,
                    weight=weight,
                    threshold=threshold,
                    passed=passed,
                    feedback=feedback
                )

                criterion_scores.append(criterion_score)
                total_weighted_score += score * weight
                total_weight += weight

                # Yield this criterion result immediately
                yield criterion_score

            except Exception as e:
                logger.error(f"Failed to evaluate criterion '{name}': {str(e)}")
                # Yield a default score on error
                criterion_score = CriterionScore(
                    name=name,
                    score=0,
                    weight=weight,
                    threshold=threshold,
                    passed=False,
                    feedback=f"Evaluation error: {str(e)}"
                )
                criterion_scores.append(criterion_score)
                yield criterion_score

    async def critique_input(self, user_message: str) -> Dict[str, any]:
        """Critique user input for quality and clarity.

        Args:
            user_message: User's input message

        Returns:
            Dict with critique scores and feedback
        """
        logger.info("Critiquing user input")

        prompt = get_input_critique_prompt(user_message)
        messages = [{"role": "user", "content": prompt}]

        try:
            result = await self.adapter.generate_structured(
                messages=messages,
                system_prompt="You are an expert at analyzing user questions and providing constructive feedback."
            )

            logger.info("Input critique complete")
            return result

        except Exception as e:
            logger.error(f"Input critique failed: {str(e)}")
            raise Exception(f"Failed to critique input: {str(e)}")

    async def evaluate_user_input(self, user_message: str):
        """Evaluate user input against criteria and yield results as they complete.
        
        This provides real-time feedback on the quality of the user's question
        based on configured input criteria (neutraliteit, impact, context, etc.).

        Args:
            user_message: User's input message

        Yields:
            CriterionScore objects as each criterion is evaluated
        """
        logger.info(f"Starting streaming evaluation of user input: '{user_message[:50]}...'")

        # Get enabled INPUT criteria (not output criteria)
        criteria = self.criteria_config.enabled_input_criteria
        if not criteria:
            logger.warning("No enabled input criteria found, falling back to output criteria")
            criteria = self.criteria_config.enabled_criteria

        logger.info(f"Evaluating user input against {len(criteria)} criteria: {[c['name'] for c in criteria]}")

        # Evaluate each criterion individually
        for idx, criterion in enumerate(criteria, 1):
            name = criterion["name"]
            weight = criterion["weight"]
            threshold = criterion["threshold"]
            description = criterion.get("description", "")
            eval_prompt = criterion.get("evaluation_prompt", "")

            logger.info(f"Evaluating criterion {idx}/{len(criteria)}: {name}")

            # Build prompt for this specific criterion applied to the user's question
            criterion_prompt = f"""Evalueer de volgende gebruikersvraag op basis van het criterium '{name}': {description}

Gebruikersvraag: {user_message}

Evaluatievraag: {eval_prompt}

Geef een score van 0-100 en beknopte feedback in het Nederlands. Return ALLEEN geldige JSON met deze structuur:
{{
  "score": <nummer>,
  "feedback": "<tekst>"
}}"""

            messages = [{"role": "user", "content": criterion_prompt}]

            try:
                result = await self.adapter.generate_structured(
                    messages=messages,
                    system_prompt="Je bent een expert evaluator die de kwaliteit van gebruikersvragen analyseert. Wees constructief en behulpzaam. Antwoord in het Nederlands."
                )

                score = result.get("score", 0)
                feedback = result.get("feedback", "")
                passed = score >= threshold

                criterion_score = CriterionScore(
                    name=name,
                    score=score,
                    weight=weight,
                    threshold=threshold,
                    passed=passed,
                    feedback=feedback
                )

                logger.info(f"Criterion '{name}' evaluated: score={score}, passed={passed}")

                # Yield this criterion result immediately
                yield criterion_score

            except Exception as e:
                logger.error(f"Failed to evaluate user input criterion '{name}': {str(e)}", exc_info=True)
                # Yield a default score on error
                criterion_score = CriterionScore(
                    name=name,
                    score=0,
                    weight=weight,
                    threshold=threshold,
                    passed=False,
                    feedback=f"Evaluatiefout: {str(e)}"
                )
                yield criterion_score

        logger.info("User input evaluation complete")


# Global judge service instance
_judge_service: Optional[JudgeService] = None


def get_judge_service() -> JudgeService:
    """Get or create judge service instance.

    Returns:
        JudgeService instance
    """
    global _judge_service
    if _judge_service is None:
        _judge_service = JudgeService()
    return _judge_service
