"""
End-to-end tests for the StripeRAGEngine.

These tests require a valid OPENAI_API_KEY to be set in the environment.
"""
import os
import pytest
import numpy as np
from rag_engine import StripeRAGEngine

# Skip these tests if no OpenAI API key is available
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set in environment"
)

class TestStripeRAGEEndToEnd:
    """End-to-end tests for the StripeRAGEngine."""
    
    @pytest.fixture
    async def rag_engine(self):
        """Fixture to provide an initialized RAG engine."""
        engine = StripeRAGEngine()
        await engine.initialize()
        return engine
    
    @pytest.mark.asyncio
    async def test_initialization(self, rag_engine):
        """Test that the RAG engine initializes correctly."""
        assert rag_engine is not None
        assert hasattr(rag_engine, 'documents')
        assert len(rag_engine.documents) > 0
        
        # Check that documents have embeddings
        for doc in rag_engine.documents[:5]:  # Check first 5 documents
            assert doc.embedding is not None
            assert len(doc.embedding) > 0
            assert isinstance(doc.embedding, np.ndarray)
    
    @pytest.mark.asyncio
    async def test_query(self, rag_engine):
        """Test querying the RAG engine with a simple question."""
        test_question = "How do I create a payment intent?"
        
        # Get a response from the RAG engine
        response = await rag_engine.query(test_question)
        
        # Basic validation of the response
        assert isinstance(response, str)
        assert len(response) > 0
        assert "payment" in response.lower() or "stripe" in response.lower()
    
    @pytest.mark.asyncio
    async def test_relevant_document_retrieval(self, rag_engine):
        """Test that the most relevant documents are retrieved for a query."""
        test_query = "How to handle webhook events"
        
        # Generate embedding for the test query
        response = await rag_engine.client.embeddings.create(
            model="text-embedding-ada-002",
            input=test_query
        )
        query_embedding = np.array(response.data[0].embedding)
        
        # Get relevant documents
        relevant_docs = rag_engine._find_relevant_docs(query_embedding, top_k=3)
        
        # Basic validation
        assert len(relevant_docs) == 3
        assert all(doc.embedding is not None for doc in relevant_docs)
        
        # Check that the documents are sorted by relevance (descending)
        similarities = [
            np.dot(query_embedding, doc.embedding) / 
            (np.linalg.norm(query_embedding) * np.linalg.norm(doc.embedding))
            for doc in relevant_docs
        ]
        assert all(similarities[i] >= similarities[i+1] for i in range(len(similarities)-1))
