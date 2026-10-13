import asyncio
import hashlib
import hmac
import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import numpy as np
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from codegen import StripeCodeGenerator
from error_helper import StripeErrorHelper
from main import app as cli
from rag_engine import StripeDocument, StripeRAGEngine
from web_app import create_app


@pytest.mark.asyncio
async def test_retrieval_is_deterministic_and_context_reaches_provider(tmp_path):
    client = AsyncMock()
    client.messages.create.return_value = SimpleNamespace(content=[SimpleNamespace(text="grounded answer")])
    engine = StripeRAGEngine(client=client)
    engine.docs_cache = str(tmp_path / "references.json")
    engine.documents = [StripeDocument("Webhooks", "webhook signature verification", "https://example.test/webhooks", "webhooks"),
                        StripeDocument("Customers", "customer subscription metadata", "https://example.test/customers", "customers")]
    await engine._generate_embeddings()
    first = await engine._get_embedding("webhook signature")
    assert np.array_equal(first, await engine._get_embedding("webhook signature"))
    assert (await engine._retrieve_relevant_documents("webhook signature", 1))[0].title == "Webhooks"
    assert await engine.ask("webhook signature") == "grounded answer"
    system = client.messages.create.call_args.kwargs["system"]
    assert "webhook signature verification" in system
    assert "https://example.test/webhooks" in system
    await engine._cache_data()
    fresh = StripeRAGEngine()
    fresh.docs_cache = engine.docs_cache
    await fresh.initialize()
    assert np.array_equal(engine.documents[0].embedding, fresh.documents[0].embedding)
    await fresh.initialize()
    assert len(fresh.documents) == 2


@pytest.mark.asyncio
async def test_provider_failures_propagate_as_failures(tmp_path):
    client = AsyncMock()
    client.messages.create.side_effect = RuntimeError("controlled provider failure")
    engine = StripeRAGEngine(client=client)
    engine.docs_cache = str(tmp_path / "references.json")
    with pytest.raises(RuntimeError, match="controlled provider failure"):
        await engine.ask("payment intent")


def test_help_and_templates_work_without_credentials(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    runner = CliRunner()
    assert runner.invoke(cli, ["--help"]).exit_code == 0
    generated = runner.invoke(cli, ["generate", "subscription checkout"])
    assert generated.exit_code == 0
    assert "stripe.Subscription.create" in generated.output
    failed = runner.invoke(cli, ["generate", "custom integration"])
    assert failed.exit_code == 1
    assert "ANTHROPIC_API_KEY" in failed.output


def signature(payload, timestamp, secret="whsec_fixture"):
    digest = hmac.new(secret.encode(), str(timestamp).encode() + b"." + payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def test_webhook_rejects_tampering_stale_timestamps_and_missing_signature():
    helper = StripeErrorHelper()
    payload = b'{"type":"payment_intent.succeeded","data":{"object":{"id":"pi_fixture"}}}'
    now = int(time.time())
    assert helper.verify_webhook_signature(payload, signature(payload, now), "whsec_fixture")
    assert not helper.verify_webhook_signature(payload + b" ", signature(payload, now), "whsec_fixture")
    assert not helper.verify_webhook_signature(payload, signature(payload, now - 600), "whsec_fixture")
    assert not helper.verify_webhook_signature(payload, None, "whsec_fixture")
    with pytest.raises(ValueError, match="signature verification"):
        asyncio.run(helper.analyze_webhook(payload, verify_signature=True))


def test_browser_api_contracts_and_provider_errors(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    rag = StripeRAGEngine()
    rag.docs_cache = str(tmp_path / "docs.json")
    with TestClient(create_app(rag=rag)) as client:
        assert client.get("/").status_code == 200
        assert client.get("/static/styles.css").status_code == 200
        assert client.get("/health").json()["references"] > 0
        # The existing browser sends a form prompt and expects JSON code.
        response = client.post("/api/generate", data={"prompt": "create a payment intent", "language": "python", "framework": "flask"})
        assert response.status_code == 200
        assert "stripe.PaymentIntent.create" in response.json()["code"]
        assert client.post("/api/generate", json={"task": "create a payment intent"}).status_code == 200
        assert client.post("/api/ask", json={"question": "How do payments work?"}).status_code == 503
        assert client.post("/api/generate", data={"prompt": ""}).status_code == 422
        result = client.post("/api/debug", json={"error_log": "card_declined"})
        assert result.status_code == 200
        assert "card_declined" in result.json()["analysis"]
        result = client.post("/api/webhook", json={"payload": json.dumps({"type": "payment_intent.succeeded", "data": {}})})
        assert result.status_code == 200
        assert "unverified" in result.json()["analysis"]
        client_failure = AsyncMock()
        client_failure.messages.create.side_effect = RuntimeError("controlled failure")
        rag.client = client_failure
        assert client.post("/api/ask", json={"question": "payment intent"}).status_code == 502
