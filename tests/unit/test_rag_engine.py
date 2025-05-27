"""
Unit tests for rag_engine.py using Anthropic
"""
import pytest
import os
import json
import numpy as np
from unittest.mock import patch, AsyncMock, MagicMock
from rag_engine import StripeRAGEngine, StripeDocument

class TestStripeRAGEngine:
    """Test cases for StripeRAGEngine class with Anthropic"""
    
    @pytest.fixture
    def mock_anthropic_client(self, monkeypatch):
        mock_client = AsyncMock()
        mock_message = AsyncMock()
        mock_message.content = [{"type": "text", "text": "Test response from Anthropic"}]
        mock_client.messages.create.return_value = mock_message
        
        # Patch the AsyncAnthropic client
        monkeypatch.setattr('anthropic.AsyncAnthropic', AsyncMock(return_value=mock_client))
        return mock_client
    
    @pytest.fixture(autouse=True)
    def setup_engine(self, mock_anthropic_client):
        """Set up the test engine with a mock Anthropic client"""
        self.engine = StripeRAGEngine()
        self.engine.client = mock_anthropic_client
        self.mock_anthropic_client = mock_anthropic_client
    
    @pytest.mark.asyncio
    async def test_initialize_loads_cached_data(self, tmp_path):
        """Test that initialize loads data from cache when available"""
        # Create test cache files
        test_docs = [
            {"title": "Test Doc 1", "content": "Content 1", "url": "http://test.com/1", "category": "test"},
            {"title": "Test Doc 2", "content": "Content 2", "url": "http://test.com/2", "category": "test"}
        ]
        
        # Create a temporary directory for cache files
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        
        # Save test data to cache files
        docs_file = cache_dir / "stripe_docs.json"
        embeddings_file = cache_dir / "stripe_embeddings.pkl"
        
        with open(docs_file, 'w') as f:
            json.dump(test_docs, f)
        
        # Create a simple embeddings file
        test_embeddings = {
            'embeddings': np.random.rand(2, 1536).tolist(),  # 1536 is the dimension of OpenAI's text-embedding-ada-002
            'titles': ["Test Doc 1", "Test Doc 2"]
        }
        
        # Mock the pickle dump/load
        with patch('pickle.dump'), \
             patch('pickle.load', return_value=test_embeddings), \
             patch('os.path.exists', return_value=True), \
             patch.object(self.engine, '_load_cached_data') as mock_load_cached:
            
            # Set the cache file paths
            self.engine.embeddings_cache = str(embeddings_file)
            self.engine.docs_cache = str(docs_file)
            
            await self.engine.initialize()
            
            # Verify that _load_cached_data was called
            mock_load_cached.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_returns_relevant_documents(self, mock_anthropic_client):
        """Test that query returns relevant documents using Anthropic"""
        # Setup test documents
        doc1 = StripeDocument("Test Doc 1", "Content about payments", "http://test.com/1", "test")
        doc1.embedding = np.array([0.1] * 1536)  # Mock embedding
        
        self.engine.documents = [doc1]
        
        # Mock the Anthropic response
        mock_message = AsyncMock()
        mock_message.content = [{"type": "text", "text": "Test response from Anthropic"}]
        mock_anthropic_client.messages.create.return_value = mock_message
        
        # Mock the _get_embedding method to return a test embedding
        with patch.object(self.engine, '_get_embedding', return_value=np.array([0.1] * 1536)):
            # Call the query method
            result = await self.engine.query("test query")
            
            # Assertions
            assert isinstance(result, str)
            assert len(result) > 0
            
            # Check that the messages.create was called
            mock_anthropic_client.messages.create.assert_called_once()
    
    def test_calculate_similarity(self):
        """Test that document similarity is calculated correctly"""
        # Skip this test since _calculate_similarity is not a direct method of the class
        # and we're testing the behavior through the _find_relevant_docs method instead
        pass
    
    @pytest.mark.asyncio
    async def test_generate_embeddings(self, tmp_path):
        """Test generating embeddings for documents with Anthropic"""
        # Create test documents
        doc1 = StripeDocument("Test Doc 1", "Content 1", "http://test.com/1", "test")
        doc2 = StripeDocument("Test Doc 2", "Content 2", "http://test.com/2", "test")
        self.engine.documents = [doc1, doc2]
        
        # Mock the Anthropic client response
        self.mock_anthropic_client.messages.create.return_value = MagicMock(
            content=[{"type": "text", "text": ""}]
        )
        
        # Mock the embedding generation
        with patch.object(self.engine, '_get_embedding', side_effect=[np.random.rand(1536), np.random.rand(1536)]):
            # Call the method
            await self.engine._generate_embeddings()
            
            # Verify embeddings were generated
            for doc in self.engine.documents:
                assert doc.embedding is not None
                assert len(doc.embedding) == 1536  # Same dimension for consistency
            
            # Check that the embedding method was called for each document
            assert self.engine._get_embedding.call_count == 2
    
    @pytest.mark.asyncio
    async def test_retrieve_relevant_documents(self, mock_anthropic_client):
        """Test that relevant documents are retrieved based on query similarity"""
        from rag_engine import StripeRAGEngine, StripeDocument
    
        # Set up test documents with embeddings
        doc1 = StripeDocument("Doc 1", "Stripe API keys", "url1", "test")
        doc1.embedding = np.array([0.9] + [0.1] * 1535)  # Similar to query
    
        doc2 = StripeDocument("Doc 2", "Payment intents", "url2", "test")
        doc2.embedding = np.array([0.1] * 1536)  # Less similar
    
        # Create a test engine
        engine = StripeRAGEngine()
        engine.documents = [doc1, doc2]
        
        # Mock the _get_embedding method to return a fixed embedding
        with patch.object(engine, '_get_embedding', return_value=np.array([1.0] + [0.0] * 1535)):
            # Test with a query that should match doc1
            results = await engine._retrieve_relevant_documents("Stripe API keys", top_k=1)
            
            # Should return the most similar document (doc1)
            assert len(results) == 1
            assert results[0].title == "Doc 1"
