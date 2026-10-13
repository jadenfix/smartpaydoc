import hashlib
import hmac
import json
import time
from types import SimpleNamespace
import pytest
from error_helper import StripeErrorHelper

@pytest.mark.asyncio
async def test_diagnosis_calls_provider(mock_anthropic_client):
    mock_anthropic_client.messages.create.return_value = SimpleNamespace(content=[SimpleNamespace(text="fixture diagnosis")])
    assert await StripeErrorHelper().diagnose_error("card_declined") == "fixture diagnosis"
    assert "card_declined" in mock_anthropic_client.messages.create.call_args.kwargs["messages"][0]["content"]

@pytest.mark.asyncio
async def test_webhook_parsing_and_invalid_payload(mock_anthropic_client):
    helper = StripeErrorHelper()
    result = await helper.analyze_webhook(json.dumps({"type": "payment_intent.succeeded", "data": {"object": {"amount": 2000}}}))
    assert "2000" in result and "payment_intent.succeeded" in result
    with pytest.raises(ValueError):
        await helper.analyze_webhook("[]")

def test_webhook_signature_and_replay(mock_anthropic_client):
    helper = StripeErrorHelper()
    payload = b'{"amount":2000}'
    secret = "fixture-secret"
    timestamp = str(int(time.time()))
    digest = hmac.new(secret.encode(), timestamp.encode()+b"."+payload, hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={digest}"
    assert helper.verify_webhook_signature(payload, header, secret)
    assert not helper.verify_webhook_signature(b'{"amount":3000}', header, secret)
    assert not helper.verify_webhook_signature(payload, "t=1,v1=invalid", secret)
    assert not helper.verify_webhook_signature(payload, "malformed", secret)
