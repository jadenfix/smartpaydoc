"""
Pytest configuration and fixtures for SmartPayDoc tests
"""
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
import json
from pathlib import Path

# Add the project root to the Python path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

# Sample test data
SAMPLE_WEBHOOK_PAYLOAD = {
    "id": "evt_123456789",
    "object": "event",
    "api_version": "2023-08-16",
    "created": 1679852800,
    "data": {
        "object": {
            "id": "pi_123456789",
            "object": "payment_intent",
            "amount": 2000,
            "currency": "usd",
            "status": "succeeded"
        }
    },
    "type": "payment_intent.succeeded"
}

SAMPLE_ERROR_RESPONSE = {
    "error": {
        "code": "card_declined",
        "decline_code": "insufficient_funds",
        "message": "Your card has insufficient funds.",
        "type": "card_error"
    }
}

@pytest.fixture
def mock_anthropic_client():
    client = AsyncMock()
    client.messages.create.return_value = Mock(content=[Mock(text="Mocked response from Anthropic")])
    return client

@pytest.fixture
def sample_webhook_payload():
    """Sample webhook payload for testing"""
    return SAMPLE_WEBHOOK_PAYLOAD

@pytest.fixture
def sample_error_response():
    """Sample error response for testing"""
    return SAMPLE_ERROR_RESPONSE

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch, request):
    """Set up environment variables for testing"""
    if request.node.get_closest_marker("live_provider"):
        return
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_anthropic_key")
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_123")
    monkeypatch.setenv("STRIPE_PUBLISHABLE_KEY", "pk_test_123")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setenv("CACHE_EMBEDDINGS", "false")
def pytest_configure():
    """Configure pytest"""
    # Create a test output directory if it doesn't exist
    test_output_dir = Path(__file__).parent / "test_output"
    test_output_dir.mkdir(exist_ok=True)
    
    # Set environment variable for test output directory
    os.environ["TEST_OUTPUT_DIR"] = str(test_output_dir)
