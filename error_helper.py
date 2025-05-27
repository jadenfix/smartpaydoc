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
            return "I encountered an error while analyzing this issue. Please check the logs for more details."
