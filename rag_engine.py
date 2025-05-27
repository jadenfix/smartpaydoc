"""
RAG Engine for Stripe Documentation
Handles document ingestion, embedding, and retrieval
"""

import os
import json
import asyncio
from typing import List, Dict, Optional, Any, Tuple
import json
import pickle
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from sklearn.metrics.pairwise import cosine_similarity
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import re
from bs4 import BeautifulSoup

@dataclass
class StripeDocument:
    title: str
    content: str
    url: str
    category: str
    embedding: np.ndarray = None

class StripeRAGEngine:
    """RAG engine for Stripe documentation using Anthropic"""
    
    def __init__(self):
        # Initialize Anthropic client for both text and embeddings
        self.client = anthropic.AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        
        self.documents: List[StripeDocument] = []
        self.embeddings_cache = "stripe_embeddings.pkl"
        self.docs_cache = "stripe_docs.json"
        self.embedding_model = "claude-3-opus-20240229"
        
    async def initialize(self):
        """Initialize the RAG engine with Stripe documentation"""
        print("🔄 Initializing RAG engine...")
        
        # Load cached data if available
        if os.path.exists(self.embeddings_cache) and os.path.exists(self.docs_cache):
            print("📁 Loading cached documentation...")
            await self._load_cached_data()
        else:
            print("🌐 Fetching fresh Stripe documentation...")
            await self._fetch_stripe_docs()
            await self._generate_embeddings()
            await self._cache_data()
        
        print(f"✅ Loaded {len(self.documents)} Stripe documents")

    async def _fetch_stripe_docs(self):
        """Fetch and parse Stripe documentation"""
        # Stripe API documentation sections to scrape
        stripe_sections = [
            {
                "title": "Payment Intents",
                "content": """
Payment Intents represent your intent to collect payment from a customer, tracking charge attempts and payment state changes throughout the process.

Key concepts:
- Create a PaymentIntent on your server
- Collect payment method details on the client
- Confirm the PaymentIntent to attempt payment
- Handle authentication when required

Basic usage:
```python
import stripe
stripe.api_key = "sk_test_..."

# Create PaymentIntent
intent = stripe.PaymentIntent.create(
    amount=2000,  # $20.00
    currency='usd',
    metadata={'order_id': '123'}
)
```

States: requires_payment_method, requires_confirmation, requires_action, processing, requires_capture, canceled, succeeded
                """,
                "url": "https://stripe.com/docs/api/payment_intents",
                "category": "payments"
            },
            {
                "title": "Customers",
                "content": """
Customer objects allow you to perform recurring charges and track payments that belong to the same customer.

Key features:
- Store customer information securely
- Attach payment methods
- Track payment history
- Handle subscriptions

Basic usage:
```python
# Create customer
customer = stripe.Customer.create(
    email='customer@example.com',
    name='John Doe',
    metadata={'user_id': '123'}
)

# Retrieve customer
customer = stripe.Customer.retrieve('cus_...')
```

Common fields: id, email, name, phone, address, metadata, created, subscriptions
                """,
                "url": "https://stripe.com/docs/api/customers",
                "category": "customers"
            },
            {
                "title": "Subscriptions",
                "content": """
Subscriptions allow you to charge customers on a recurring basis. A subscription ties a customer to a particular pricing plan.

Key concepts:
- Create pricing plans first
- Subscribe customers to plans
- Handle billing cycles and proration
- Manage subscription lifecycle

Basic usage:
```python
# Create subscription
subscription = stripe.Subscription.create(
    customer='cus_...',
    items=[{'price': 'price_...'}],
    trial_period_days=7
)
```

Statuses: incomplete, incomplete_expired, trialing, active, past_due, canceled, unpaid
                """,
                "url": "https://stripe.com/docs/api/subscriptions",
                "category": "billing"
            },
            {
                "title": "Webhooks",
                "content": """
Webhooks allow your application to receive real-time notifications when events happen in your Stripe account.

Key concepts:
- Configure webhook endpoints in Dashboard
- Verify webhook signatures for security
- Handle idempotency for reliability
- Process events asynchronously

Basic webhook handling:
```python
import stripe
from flask import Flask, request

app = Flask(__name__)
endpoint_secret = 'whsec_...'

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print(f'Payment {payment_intent.id} succeeded!')
    
    return {'status': 'success'}
```

Common events: payment_intent.succeeded, invoice.payment_failed, customer.subscription.updated
                """,
                "url": "https://stripe.com/docs/webhooks",
                "category": "webhooks"
            },
            {
                "title": "Error Handling",
                "content": """
Stripe uses conventional HTTP response codes and provides detailed error information.

Common error types:
- CardError: Card was declined
- RateLimitError: Too many requests
- InvalidRequestError: Invalid parameters
- AuthenticationError: Invalid API key
- APIConnectionError: Network issues
- APIError: Stripe server error

Error handling example:
```python
try:
    charge = stripe.Charge.create(
        amount=2000,
        currency='usd',
        source='tok_visa'
    )
except stripe.error.CardError as e:
    # Card was declined
    print(f'Card declined: {e.user_message}')
except stripe.error.RateLimitError:
    # Rate limit exceeded
    print('Rate limit exceeded')
except stripe.error.InvalidRequestError as e:
    # Invalid parameters
    print(f'Invalid request: {e.user_message}')
```

HTTP Status Codes: 200 (OK), 400 (Bad Request), 401 (Unauthorized), 402 (Request Failed), 403 (Forbidden), 404 (Not Found), 409 (Conflict), 429 (Too Many Requests), 500+ (Server Errors)
                """,
        }
    ]
    
        # Add more comprehensive documentation
        for section in stripe_sections:
            doc = StripeDocument(
                title=section["title"],
                content=section["content"],
                url=section["url"],
                category=section["category"]
            )
            self.documents.append(doc)

    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a given text using Anthropic"""
        try:
            # For now, return a mock embedding
            # In a real implementation, you would call the Anthropic API
            # and process the response to extract the embedding
            return [0.1] * 1536  # Return a mock embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            # Return a zero vector as fallback
            return [0.0] * 1536

    async def _generate_embeddings(self):
        """Generate embeddings for all documents using Anthropic"""
        print("Generating embeddings...")
        
        # Filter out documents that already have embeddings
        docs_to_embed = [doc for doc in self.documents if not hasattr(doc, 'embedding') or doc.embedding is None]
        
        if not docs_to_embed:
            print("All documents already have embeddings")
            return
                    
        # Process documents one by one (Anthropic's API might have rate limits)
        for i, doc in enumerate(docs_to_embed):
            try:
                doc.embedding = await self._get_embedding(doc.content)
                print(f"Processed embedding for document {i + 1}/{len(docs_to_embed)}")
            except Exception as e:
                logger.error(f"Error processing document {doc.title}: {e}")
                continue

    async def _cache_data(self):
        """Cache documents and embeddings"""
        # Cache embeddings
        embeddings_data = {
            'embeddings': [doc.embedding for doc in self.documents if hasattr(doc, 'embedding') and doc.embedding is not None],
            'titles': [doc.title for doc in self.documents if hasattr(doc, 'embedding') and doc.embedding is not None]
        }
        with open(self.embeddings_cache, 'wb') as f:
            pickle.dump(embeddings_data, f)
            
        # Cache documents
        docs_data = [
            {
                'title': doc.title,
                'content': doc.content,
                'url': doc.url,
                'category': doc.category
            }
            for doc in self.documents
        ]
        with open(self.docs_cache, 'w') as f:
            json.dump(docs_data, f, indent=2)

    async def _load_cached_data(self):
        """Load cached documents and embeddings"""
        # Load documents
        with open(self.docs_cache, 'r') as f:
            docs_data = json.load(f)
            
        # Load embeddings
        with open(self.embeddings_cache, 'rb') as f:
            embeddings_data = pickle.load(f)
            
        # Reconstruct documents with embeddings
        for i, doc_data in enumerate(docs_data):
            doc = StripeDocument(
                title=doc_data['title'],
                content=doc_data['content'],
                url=doc_data['url'],
                category=doc_data['category']
            )
            if i < len(embeddings_data['embeddings']):
                doc.embedding = embeddings_data['embeddings'][i]
            self.documents.append(doc)

    async def query(self, question: str, language: str = "python"):
        """Query the RAG system with a question"""
        if not self.documents:
            raise Exception("RAG engine not initialized. Run 'smartpaydoc init' first.")
            
        # Get embedding for the query
        query_embedding = await self._get_embedding(question)
        
        # Retrieve relevant documents
        relevant_docs = await self._retrieve_relevant_documents(question)
        
        # Prepare context for the prompt
        context = "\n\n".join([
            f"<document>\nTitle: {doc.title}\nContent: {doc.content}\n</document>"
            for doc in relevant_docs
        ])
        
        system_prompt = """You are SmartPayDoc, an expert Stripe developer assistant. 
Answer the user's question using ONLY the provided Stripe documentation context.
If the context doesn't contain the answer, say "I couldn't find a specific answer in the documentation."
"""
        
        user_prompt = f"""<context>
{context}
</context>

<question>
{question}
</question>

Please provide a clear and concise answer to the question based on the context above.
If the question is code-related, provide a complete code example in the specified language.
If the context doesn't contain the answer, say so clearly.
"""

        try:
            response = await self.client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
                max_tokens=1000,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract the response text from the Anthropic API response
            if hasattr(response, 'content') and isinstance(response.content, list) and len(response.content) > 0:
                if hasattr(response.content[0], 'text'):
                    return response.content[0].text
                elif isinstance(response.content[0], dict) and 'text' in response.content[0]:
                    return response.content[0]['text']
            
            # Fallback if we can't extract the text
            return "I'm sorry, I couldn't generate a response. Please try again."
            
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return f"I'm sorry, I encountered an error while generating a response: {str(e)}"

    async def _retrieve_relevant_documents(self, query: str, top_k: int = 3) -> List[StripeDocument]:
        """Retrieve the most relevant documents for a query"""
        try:
            # If no documents, return empty list
            if not self.documents:
                return []
                
            # Get embedding for the query
            query_embedding = await self._get_embedding(query)
            
            # Calculate similarity scores for all documents
            similarities = []
            for doc in self.documents:
                if hasattr(doc, 'embedding') and doc.embedding is not None:
                    similarity = self._calculate_similarity(query_embedding, doc.embedding)
                    similarities.append((doc, similarity))
            
            # If no documents with embeddings, return empty list
            if not similarities:
                return []
                
            # Sort by similarity score in descending order
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Return top-k documents
            return [doc for doc, _ in similarities[:top_k]]
            
        except Exception as e:
            logger.error(f"Error retrieving relevant documents: {e}")
            return []

    def _calculate_similarity(self, query_embedding: List[float], doc_embedding: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        query_embedding = np.array(query_embedding)
        doc_embedding = np.array(doc_embedding)
        return cosine_similarity(query_embedding.reshape(1, -1), doc_embedding.reshape(1, -1))[0][0]