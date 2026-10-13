"""Shared lazy provider boundary; offline features never need credentials."""
import os
from anthropic import AsyncAnthropic


def create_client():
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY is required for AI operations")
    if not os.getenv("ANTHROPIC_MODEL"):
        raise ValueError("ANTHROPIC_MODEL is required for AI operations")
    return AsyncAnthropic(api_key=key, timeout=30.0, max_retries=1)


def response_text(message):
    blocks = getattr(message, "content", None)
    if blocks is None:
        raise ValueError("Provider returned no message content")
    text = "".join(block.get("text", "") if isinstance(block, dict) else getattr(block, "text", "") for block in blocks).strip()
    if not text:
        raise ValueError("Provider returned no text content")
    return text
