"""Real application routes and disk cache, with explicitly synthetic provider responses."""
from types import SimpleNamespace
import asyncio
from fastapi.testclient import TestClient
import pytest
import web_app
from codegen import StripeCodeGenerator
from error_helper import StripeErrorHelper
from rag_engine import StripeDocument, StripeRAGEngine


def test_http_workflow_with_fixture_provider_and_real_cache(mock_anthropic_client, tmp_path, monkeypatch):
    rag = StripeRAGEngine()
    rag.documents = [StripeDocument("Fixture payment intents", "Payment intents use amount in cents", "fixture://payments", "payments")]
    rag.docs_cache, rag.embeddings_cache = str(tmp_path / "docs.json"), str(tmp_path / "embeddings.pkl")
    asyncio.run(rag._generate_embeddings())
    asyncio.run(rag._cache_data())
    restored = StripeRAGEngine()
    restored.docs_cache, restored.embeddings_cache = rag.docs_cache, rag.embeddings_cache
    asyncio.run(restored._load_cached_data())
    monkeypatch.setattr(web_app, "rag", restored)
    monkeypatch.setattr(web_app, "codegen", StripeCodeGenerator())
    monkeypatch.setattr(web_app, "error_helper", StripeErrorHelper())
    mock_anthropic_client.messages.create.return_value = SimpleNamespace(content=[SimpleNamespace(text="fixture provider response")])
    client = TestClient(web_app.app)
    assert client.get("/health").json()["status"] == "ready"
    assert "fixture provider response" in client.post("/api/ask", json={"question": "payment amount"}).text
    assert "amount in cents" in mock_anthropic_client.messages.create.call_args.kwargs["system"]
    assert client.post("/api/ask", json={"question": []}).status_code == 422
    assert client.post("/api/ask", json={"question": " "}).status_code == 400
    assert "fixture provider response" in client.post("/api/generate", json={"task": "custom integration"}).text
    assert client.post("/api/debug", json={"error_log": "fixture error"}).json()["analysis"] == "fixture provider response"
    mock_anthropic_client.messages.create.side_effect = RuntimeError("fixture outage")
    assert client.post("/api/generate", json={"task": "custom integration"}).status_code == 500
    assert client.post("/api/debug", json={"error_log": "fixture error"}).status_code == 502
    assert client.post("/api/ask", json={"question": "payment amount"}).status_code == 500
    monkeypatch.setattr(web_app, "rag", None)
    assert client.post("/api/ask", json={"question": "payment"}).status_code == 503
    assert client.get("/health").json()["status"] == "unavailable"
