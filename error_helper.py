"""
Stripe Error Helper and Webhook Analyzer
Diagnoses common Stripe errors and analyzes webhook payloads using Anthropic
"""

import os
import json
import re
import logging
from typing import Dict, Any, Optional, List
import anthropic
import hashlib
import hmac

# Set up logging
logger = logging.getLogger(__name__)

class StripeErrorHelper:
    def __init__(self):
        """Initialize the StripeErrorHelper with Anthropic client."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
            
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        
    async def diagnose_error(self, error_log: str, context: Optional[str] = None) -> str:
        """Diagnose a Stripe error using Anthropic"""
        try:
            prompt = f"""You are a Stripe API expert. Analyze this error and provide a detailed explanation and solution.
            
Error:
{error_log}

Context: {context or 'No additional context provided'}

Please provide:
1. The likely cause of the error
2. Step-by-step solution
3. Code example to fix the issue (if applicable)"""
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error in LLM diagnosis: {e}")
            raise RuntimeError("Diagnosis provider failed") from e

    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str, tolerance: int = 300) -> bool:
        """Verify exact bytes and freshness before inspecting an event."""
        import time
        try:
            parts = [part.split("=", 1) for part in signature.split(",")]
            timestamp = next(value for key, value in parts if key == "t")
            if abs(time.time() - int(timestamp)) > tolerance:
                return False
            expected = hmac.new(secret.encode(), timestamp.encode() + b"." + payload, hashlib.sha256).hexdigest()
            return any(key == "v1" and hmac.compare_digest(value, expected) for key, value in parts)
        except (ValueError, StopIteration):
            return False

    async def analyze_webhook(self, payload: str, verify_signature: bool = False, signature: Optional[str] = None) -> str:
        if verify_signature:
            secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
            if not secret or not signature or not self.verify_webhook_signature(payload.encode(), signature, secret):
                raise ValueError("Webhook signature is invalid or expired")
        event = json.loads(payload)
        if not isinstance(event, dict) or not isinstance(event.get("data", {}).get("object"), dict):
            raise ValueError("Webhook must contain an event object")
        obj = event["data"]["object"]
        return f"Event: {event.get('type', 'unknown')}\nObject: {json.dumps(obj, sort_keys=True)}"
