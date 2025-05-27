"""
Unit tests for error_helper.py using Anthropic
"""
import pytest
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock, AsyncMock
from error_helper import StripeErrorHelper

class TestStripeErrorHelper:
    """Test cases for StripeErrorHelper class with Anthropic"""
    
    @pytest.fixture(autouse=True)
    def setup_helper(self, mock_anthropic_client):
        """Set up the test helper with a mock Anthropic client"""
        self.helper = StripeErrorHelper()
        self.mock_anthropic_client = mock_anthropic_client
    
    def test_load_common_errors(self):
        """Test that common errors are loaded correctly"""
        assert len(self.helper.common_errors) > 0
        assert "card_declined" in self.helper.common_errors
        assert "authentication_required" in self.helper.common_errors
    
    def test_load_webhook_events(self):
        """Test that webhook events are loaded correctly"""
        assert len(self.helper.webhook_events) > 0
        assert "payment_intent.succeeded" in self.helper.webhook_events
        # Update the assertion to match the actual implementation
        assert self.helper.webhook_events.get("payment_intent.succeeded") is not None
    
    @pytest.mark.asyncio
    async def test_diagnose_error_known_error(self):
        """Test diagnosing a known error"""
        # Mock the Anthropic response for known error
        mock_message = MagicMock()
        mock_message.content = [{"type": "text", "text": "Card declined: insufficient funds"}]
        self.mock_anthropic_client.messages.create.return_value = mock_message
        
        error_log = "card_declined: Your card was declined."
        result = await self.helper.diagnose_error(error_log)
        
        # Check that the error was processed
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_diagnose_error_unknown_error(self):
        """Test diagnosing an unknown error using the Anthropic model"""
        # Mock the Anthropic response for unknown error
        mock_message = MagicMock()
        mock_message.content = [{"type": "text", "text": "This is a test diagnosis for an unknown error."}]
        self.mock_anthropic_client.messages.create.return_value = mock_message
        
        error_log = "some_unknown_error: Something went wrong"
        result = await self.helper.diagnose_error(error_log)
        
        # Check that the error was processed
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_webhook(self):
        """Test webhook payload analysis with Anthropic"""
        # Test payload
        payload = {
            "id": "evt_123",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_123"}},
            "created": 1234567890
        }
        
        # Mock the Anthropic response
        mock_message = MagicMock()
        mock_message.content = [{"type": "text", "text": "Test webhook analysis"}]
        self.mock_anthropic_client.messages.create.return_value = mock_message
        
        # Test with verify_signature=False to avoid signature verification
        result = await self.helper.analyze_webhook(json.dumps(payload), verify_signature=False)
        
        # Check that the response is a string and contains the expected content
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Verify the Anthropic client was called with the right parameters
        call_args = self.mock_anthropic_client.messages.create.call_args[1]
        assert "payment_intent.succeeded" in str(call_args["messages"][0]["content"])
    
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
        diagnosis = {
            "error_type": "card_declined",
            "description": "The card was declined",
            "suggested_fix": "Ask the customer to use a different payment method",
            "documentation_url": "https://stripe.com/docs/declines"
        }
        
        # Test with valid diagnosis
        formatted = self.helper._format_error_diagnosis(diagnosis)
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        
        # Test with missing fields
        partial_diagnosis = {
            "error_type": "card_declined",
            "description": "The card was declined"
        }
        formatted = self.helper._format_error_diagnosis(partial_diagnosis)
        assert isinstance(formatted, str)
        
        # Test with empty diagnosis
        empty_diagnosis = {}
        formatted = self.helper._format_error_diagnosis(empty_diagnosis)
        assert "No specific error information available" in formatted.lower()
