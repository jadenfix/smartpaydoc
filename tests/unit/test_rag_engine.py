from types import SimpleNamespace
import numpy as np
import pytest
from rag_engine import StripeDocument, StripeRAGEngine

@pytest.mark.asyncio
async def test_lexical_retrieval_is_repeatable(mock_anthropic_client):
    engine = StripeRAGEngine()
    engine.documents = [StripeDocument("Payment intents", "payment intent card", "fixture://payments", "payments"), StripeDocument("Subscriptions", "recurring billing subscription", "fixture://billing", "billing")]
    await engine._generate_embeddings()
    query = await engine._get_embedding("payment intent")
    assert np.array_equal(query, await engine._get_embedding("payment intent"))
    assert engine._find_relevant_docs(query, 1)[0].title == "Payment intents"

@pytest.mark.asyncio
async def test_cache_roundtrip_and_prompt_grounding(mock_anthropic_client, tmp_path):
    engine = StripeRAGEngine()
    engine.documents = [StripeDocument("Fixture payments", "Payment intent requires amount in cents", "fixture://payments", "payments")]
    engine.docs_cache = str(tmp_path / "docs.json")
    engine.embeddings_cache = str(tmp_path / "vectors.pkl")
    await engine._generate_embeddings()
    await engine._cache_data()
    restored = StripeRAGEngine()
    restored.docs_cache, restored.embeddings_cache = engine.docs_cache, engine.embeddings_cache
    await restored._load_cached_data()
    assert np.array_equal(engine.documents[0].embedding, restored.documents[0].embedding)
    mock_anthropic_client.messages.create.return_value = SimpleNamespace(content=[SimpleNamespace(text="fixture grounded answer")])
    assert "fixture grounded answer" in await restored.ask("payment amount")
    assert "Payment intent requires amount in cents" in mock_anthropic_client.messages.create.call_args.kwargs["system"]
