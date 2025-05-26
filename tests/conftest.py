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
def mock_openai_client():
    """Mock OpenAI client for testing"""
    with patch('openai.AsyncOpenAI') as mock_client:
        mock_client.return_value = AsyncMock()
        yield mock_client.return_value

@pytest.fixture
def sample_webhook_payload():
    """Sample webhook payload for testing"""
    return SAMPLE_WEBHOOK_PAYLOAD

@pytest.fixture
def sample_error_response():
    """Sample error response for testing"""
    return SAMPLE_ERROR_RESPONSE

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set up environment variables for testing"""
    # Load from .env.test if it exists
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env.test')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    monkeypatch.setenv(key, value.strip('"\''))

def pytest_configure():
    """Configure pytest"""
    # Create a test output directory if it doesn't exist
    test_output_dir = Path(__file__).parent / "test_output"
    test_output_dir.mkdir(exist_ok=True)
    
    # Set environment variable for test output directory
    os.environ["TEST_OUTPUT_DIR"] = str(test_output_dir)
