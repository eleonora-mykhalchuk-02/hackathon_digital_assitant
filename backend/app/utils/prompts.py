"""Prompt templates for LLM interactions."""

from typing import Dict, List


def get_judge_system_prompt(criteria: List[Dict]) -> str:
    """Generate system prompt for judge LLM.

    Args:
        criteria: List of evaluation criteria

    Returns:
        System prompt string
    """
    criteria_descriptions = "\n".join([
        f"- **{c['name']}** (weight: {c['weight']}, threshold: {c['threshold']}): {c['description']}"
        for c in criteria if c.get('enabled', True)
    ])

    return f"""You are an expert AI judge evaluating the quality of chatbot responses. Your role is to assess responses objectively based on specific criteria and provide constructive feedback.

EVALUATION CRITERIA:
{criteria_descriptions}

YOUR TASK:
1. Evaluate the response against each criterion (score 0-100)
2. Provide specific, actionable feedback for improvement
3. Be fair but thorough in your assessment
4. Consider the context of the conversation

RESPONSE FORMAT:
You must respond with valid JSON only, using this exact structure:
{{
    "scores": {{
        "criterion_name": score (0-100),
        ...
    }},
    "feedback": {{
        "criterion_name": "specific feedback for this criterion",
        ...
    }},
    "overall_feedback": "comprehensive summary of the evaluation",
    "suggestions": ["specific suggestion 1", "specific suggestion 2", ...]
}}

Remember: Be constructive, specific, and helpful in your feedback."""


def get_judge_evaluation_prompt(
    user_message: str,
    chatbot_response: str,
    conversation_history: List[Dict[str, str]] = None
) -> str:
    """Generate evaluation prompt for judge.

    Args:
        user_message: User's question/message
        chatbot_response: Chatbot's response to evaluate
        conversation_history: Previous conversation context

    Returns:
        Evaluation prompt
    """
    context = ""
    if conversation_history:
        context = "\n\nCONVERSATION HISTORY:\n"
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            role = msg.get("role", "").upper()
            content = msg.get("content", "")
            context += f"{role}: {content}\n"

    return f"""Please evaluate the following chatbot response:

USER'S QUESTION:
{user_message}

CHATBOT'S RESPONSE:
{chatbot_response}
{context}

Evaluate this response against all criteria and provide your assessment in JSON format."""


def get_input_critique_prompt(user_message: str) -> str:
    """Generate prompt for judging user input quality.

    Args:
        user_message: User's input to critique

    Returns:
        Critique prompt
    """
    return f"""Analyze the following user input for clarity, completeness, and appropriateness:

USER INPUT:
{user_message}

Evaluate on these aspects:
1. Clarity: Is the question clear and unambiguous?
2. Completeness: Does it provide enough context?
3. Appropriateness: Is it a reasonable request?

Provide feedback in JSON format:
{{
    "clarity_score": score (0-100),
    "completeness_score": score (0-100),
    "appropriateness_score": score (0-100),
    "feedback": "constructive feedback on how the user could improve their question",
    "suggestions": ["specific suggestion 1", "suggestion 2", ...]
}}"""


def get_chatbot_system_prompt() -> str:
    """Generate system prompt for chatbot LLM.

    Returns:
        System prompt string
    """
    return """You are a helpful, knowledgeable, and professional AI assistant. Your goal is to provide accurate, relevant, and clear responses to user questions.

GUIDELINES:
- Provide accurate and factual information
- Be comprehensive yet concise
- Use clear and professional language
- Structure your responses well
- Admit when you don't know something
- Be respectful and appropriate

Always aim for high-quality responses that fully address the user's needs."""


def get_chatbot_prompt(
    user_message: str,
    conversation_history: List[Dict[str, str]] = None
) -> List[Dict[str, str]]:
    """Generate chat messages for chatbot.

    Args:
        user_message: User's current message
        conversation_history: Previous conversation

    Returns:
        List of formatted messages
    """
    messages = []

    # Add conversation history (limit to last 10 messages)
    if conversation_history:
        for msg in conversation_history[-10:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message
    })

    return messages


def get_refinement_prompt(
    original_response: str,
    judge_feedback: str,
    suggestions: List[str],
    user_message: str
) -> List[Dict[str, str]]:
    """Generate prompt for refining a response based on judge feedback.

    Args:
        original_response: Original chatbot response
        judge_feedback: Judge's feedback
        suggestions: Specific improvement suggestions
        user_message: Original user question

    Returns:
        List of formatted messages
    """
    suggestions_text = "\n".join([f"- {s}" for s in suggestions])

    refinement_instruction = f"""Your previous response has been evaluated, and here's the feedback:

ORIGINAL RESPONSE:
{original_response}

JUDGE'S FEEDBACK:
{judge_feedback}

SPECIFIC SUGGESTIONS FOR IMPROVEMENT:
{suggestions_text}

Please provide an improved response that addresses this feedback while maintaining accuracy and relevance. Focus on the specific suggestions provided."""

    return [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": original_response},
        {"role": "user", "content": refinement_instruction}
    ]
