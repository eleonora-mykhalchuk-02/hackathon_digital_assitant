"""LLM Adapter for AWS Bedrock integration."""

import json
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from app.config import settings


class BedrockAdapter:
    """Adapter for AWS Bedrock Claude models."""

    def __init__(
        self,
        model_id: Optional[str] = None,
        region: Optional[str] = None
    ):
        """Initialize Bedrock adapter.

        Args:
            model_id: AWS Bedrock model ID (e.g., anthropic.claude-sonnet-4-5-v1:0)
            region: AWS region (defaults to settings)
        """
        self.model_id = model_id or settings.chatbot_model
        self.region = region or settings.aws_region

        # Initialize Bedrock client
        session_kwargs = {
            "region_name": self.region,
        }

        if settings.aws_access_key_id:
            session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            session_kwargs["aws_session_token"] = settings.aws_session_token

        self.client = boto3.client("bedrock-runtime", **session_kwargs)

    def _format_messages(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format messages for Claude API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt

        Returns:
            Formatted request body
        """
        # Claude expects alternating user/assistant messages
        formatted_messages = []
        for msg in messages:
            if msg["role"] in ["user", "assistant"]:
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": formatted_messages,
            "temperature": 0.7,
        }

        if system_prompt:
            body["system"] = system_prompt

        return body

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """Generate response from Claude.

        Args:
            messages: Conversation messages
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response

        Raises:
            Exception: If API call fails
        """
        body = self._format_messages(messages, system_prompt)
        body["temperature"] = temperature
        body["max_tokens"] = max_tokens

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )

            response_body = json.loads(response["body"].read())

            # Extract text from response
            if "content" in response_body and len(response_body["content"]) > 0:
                return response_body["content"][0]["text"]

            raise ValueError("No content in response")

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            raise Exception(f"AWS Bedrock error [{error_code}]: {error_message}")
        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}")

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ):
        """Generate streaming response from Claude.

        Args:
            messages: Conversation messages
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Text chunks as they arrive

        Raises:
            Exception: If API call fails
        """
        body = self._format_messages(messages, system_prompt)
        body["temperature"] = temperature
        body["max_tokens"] = max_tokens

        try:
            response = self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                body=json.dumps(body)
            )

            # Process streaming response
            for event in response["body"]:
                chunk = json.loads(event["chunk"]["bytes"])
                
                if chunk["type"] == "content_block_delta":
                    if "delta" in chunk and "text" in chunk["delta"]:
                        yield chunk["delta"]["text"]

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            raise Exception(f"AWS Bedrock error [{error_code}]: {error_message}")
        except Exception as e:
            raise Exception(f"Failed to generate streaming response: {str(e)}")

    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON response from Claude.

        Args:
            messages: Conversation messages
            system_prompt: Optional system prompt
            response_format: Expected JSON schema (for prompt engineering)

        Returns:
            Parsed JSON response
        """
        # Add JSON formatting instruction to system prompt
        json_instruction = "\n\nYou must respond with valid JSON only. No other text."
        if response_format:
            json_instruction += f"\n\nExpected format: {json.dumps(response_format, indent=2)}"

        enhanced_system = (system_prompt or "") + json_instruction

        response_text = await self.generate(
            messages=messages,
            system_prompt=enhanced_system,
            temperature=0.3  # Lower temperature for structured output
        )

        # Extract JSON from response (handle potential markdown wrapping)
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        response_text = response_text.strip()

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {response_text}")


def create_bedrock_adapter(model_id: Optional[str] = None) -> BedrockAdapter:
    """Factory function to create a Bedrock adapter.

    Args:
        model_id: Optional model ID override

    Returns:
        Configured BedrockAdapter instance
    """
    return BedrockAdapter(model_id=model_id)
