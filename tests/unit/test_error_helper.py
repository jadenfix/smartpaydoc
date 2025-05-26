"""
Unit tests for error_helper.py
"""
import pytest
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock
from error_helper import StripeErrorHelper

class TestStripeErrorHelper:
    """Test cases for StripeErrorHelper class"""
    
    @pytest.fixture(autouse=True)
    def setup_helper(self, mock_openai_client):
        """Set up the test helper with a mock OpenAI client"""
        self.helper = StripeErrorHelper()
        self.mock_openai_client = mock_openai_client
    
    def test_load_common_errors(self):
        """Test that common errors are loaded correctly"""
        assert len(self.helper.common_errors) > 0
        assert "card_declined" in self.helper.common_errors
        assert "authentication_required" in self.helper.common_errors
    
    def test_load_webhook_events(self):
        """Test that webhook events are loaded correctly"""
        assert len(self.helper.webhook_events) > 0
        assert "payment_intent.succeeded" in self.helper.webhook_events
        assert "charge.failed" in self.helper.webhook_events
    
    @pytest.mark.asyncio
    async def test_diagnose_error_known_error(self):
        """Test diagnosing a known error"""
        error_log = "card_declined: Your card was declined."
        result = await self.helper.diagnose_error(error_log)
        assert "card_declined" in result.lower()
        assert "insufficient_funds" in result.lower()
    
    @pytest.mark.asyncio
    async def test_diagnose_error_unknown_error(self):
        """Test diagnosing an unknown error using the LLM"""
        error_log = "some_unknown_error: Something went wrong"
        
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This is a test diagnosis for an unknown error."
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        result = await self.helper.diagnose_error(error_log)
        assert "test diagnosis" in result.lower()
    
    def test_verify_webhook_signature_valid(self):
        """Test webhook signature verification with valid signature"""
        # Test payload and secret
        payload = b'{"test": "data"}'
        secret = "whsec_test_secret"
        timestamp = "1234567890"
        
        # Generate a valid signature
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            signed_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Format as Stripe signature header
        signature_header = f"t={timestamp},v1={expected_signature}"
        
        # Verify the signature
        result = self.helper.verify_webhook_signature(payload, signature_header, secret)
        assert result is True
    
    def test_verify_webhook_signature_invalid(self):
        """Test webhook signature verification with invalid signature"""
        payload = b'{"test": "data"}'
        secret = "whsec_test_secret"
        invalid_signature = "t=1234567890,v1=invalid_signature"
        
        result = self.helper.verify_webhook_signature(payload, invalid_signature, secret)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_analyze_webhook(self):
        """Test webhook analysis"""
        webhook_data = {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_123", "amount": 2000, "currency": "usd"}}
        }
        
        result = await self.helper.analyze_webhook(json.dumps(webhook_data))
        assert "payment_intent.succeeded" in result
        assert "2000" in result  # Check if amount is mentioned
        assert "usd" in result.lower()  # Check if currency is mentioned

    def test_format_error_diagnosis(self):
        """Test formatting of error diagnosis"""
        error_info = {
            "type": "card_error",
            "code": "card_declined",
            "message": "Your card was declined.",
            "solutions": ["Try a different payment method", "Contact your bank"],
            "documentation": "https://stripe.com/docs/declines"
        }
        
        result = self.helper._format_error_diagnosis(error_info, "card_declined: Your card was declined.")
        assert "card_declined" in result
        assert "contact your bank" in result.lower()
        assert "try a different payment method" in result.lower()
        assert "stripe.com/docs/declines" in result
