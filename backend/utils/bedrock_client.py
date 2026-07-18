# backend/utils/bedrock_client.py
"""
Shared Amazon Bedrock client utility.
All agents call invoke_bedrock() instead of hitting localhost:11434.
Credentials are read from environment variables (AWS_ACCESS_KEY_ID, etc.)
"""
import os
import boto3
import json
from botocore.exceptions import ClientError, BotoCoreError


# Read once at import time — avoids repeated env lookups
_AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

# Singleton client — created once and reused across requests
_bedrock_client = None


def _get_client():
    """Lazily create and return a boto3 bedrock-runtime client."""
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = boto3.client(
            service_name="bedrock-runtime",
            region_name=_AWS_REGION,
        )
    return _bedrock_client


def invoke_bedrock(
    prompt: str,
    system: str = "You are a helpful assistant.",
    model_id: str = "us.anthropic.claude-sonnet-4-5-20251101-v1:0",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    retries: int = 3,
) -> str:
    """
    Call Amazon Bedrock (Claude Sonnet 4.5) and return the response as a plain string.

    This is a drop-in replacement for the old _ask_ollama() methods across all agents.
    The interface is identical: pass a prompt string, get a string back.

    Args:
        prompt:      The user-turn message / full prompt text.
        system:      Optional system instruction for the model.
        model_id:    Bedrock model ID. Defaults to Claude Sonnet 4.5.
        temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
        max_tokens:  Maximum tokens in the model's response.
        retries:     Number of retry attempts on transient errors.

    Returns:
        The model's text response as a stripped string.
        Falls back to an empty string on unrecoverable failure.
    """
    import time

    client = _get_client()

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }

    for attempt in range(1, retries + 1):
        try:
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            result = json.loads(response["body"].read())
            # Claude response shape: result["content"][0]["text"]
            text = result.get("content", [{}])[0].get("text", "").strip()
            return text

        except (ClientError, BotoCoreError) as e:
            print(f"[BedrockClient] ⚠️ Attempt {attempt}/{retries} failed: {e}")
            if attempt >= retries:
                print("[BedrockClient] ❌ All attempts failed. Returning empty string.")
                return ""


def invoke_bedrock_vision(
    image_base64: str,
    prompt: str,
    system: str = "You are a helpful assistant.",
    model_id: str = "us.anthropic.claude-sonnet-4-5-20251101-v1:0",
    temperature: float = 0.3,
    max_tokens: int = 256,
) -> str:
    """
    Call Amazon Bedrock (Claude Sonnet 4.6) with an image + text prompt (multimodal).

    Claude 4.6 supports vision natively — use this instead of the old local Llava model.

    Args:
        image_base64: Base64-encoded PNG/JPG image string (no data URI prefix needed).
        prompt:       The text question/instruction about the image.
        system:       System instruction for the model.
        model_id:     Bedrock model ID. Defaults to Claude Sonnet 4.6.
        temperature:  Sampling temperature.
        max_tokens:   Maximum tokens in the response.

    Returns:
        The model's text response as a stripped string, or empty string on failure.
    """
    import time

    client = _get_client()

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt,
                    },
                ],
            }
        ],
    }

    for attempt in range(1, 4):
        try:
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            result = json.loads(response["body"].read())
            text = result.get("content", [{}])[0].get("text", "").strip()
            return text

        except (ClientError, BotoCoreError) as e:
            print(f"[BedrockClient Vision] ⚠️ Attempt {attempt}/3 failed: {e}")
            if attempt >= 3:
                return ""
            time.sleep(2 * attempt)

        except Exception as e:
            print(f"[BedrockClient Vision] ❌ Unexpected error: {e}")
            return ""

    return ""
