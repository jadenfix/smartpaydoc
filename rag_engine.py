"""
RAG Engine for Stripe Documentation
Handles document ingestion, embedding, and retrieval
"""

import os
import json
import asyncio
from typing import List, Dict, Any
import openai
from openai import AsyncOpenAI
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from dataclasses import dataclass
from pathlib import Path
import aiohttp
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
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.documents: List[StripeDocument] = []
        self.embeddings_cache = "stripe_embeddings.pkl"
        self.docs_cache = "stripe_docs.json"
        
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
                "url": "https://stripe.com/docs/error-handling",
                "category": "errors"
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

    async def _generate_embeddings(self):
        """Generate embeddings for all documents"""
        print("🧠 Generating embeddings...")
        
        for i, doc in enumerate(self.documents):
            try:
                response = await self.client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=f"{doc.title}\n\n{doc.content}"
                )
                doc.embedding = np.array(response.data[0].embedding)
                print(f"✅ Generated embedding {i+1}/{len(self.documents)}")
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Failed to generate embedding for {doc.title}: {e}")

    async def _cache_data(self):
        """Cache documents and embeddings"""
        # Cache embeddings
        embeddings_data = {
            'embeddings': [doc.embedding for doc in self.documents if doc.embedding is not None],
            'titles': [doc.title for doc in self.documents if doc.embedding is not None]
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

    async def query(self, question: str, language: str = "python") -> str:
        """Query the RAG system with a question"""
        if not self.documents:
            raise Exception("RAG engine not initialized. Run 'smartpaydoc init' first.")
        
        # Generate query embedding
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=question
            )
            query_embedding = np.array(response.data[0].embedding)
        except Exception as e:
            raise Exception(f"Failed to generate query embedding: {e}")
        
        # Find most relevant documents
        relevant_docs = self._find_relevant_docs(query_embedding, top_k=3)
        
        # Generate response using LLM
        context = "\n\n".join([
            f"**{doc.title}**\n{doc.content}"
            for doc in relevant_docs
        ])
        
        prompt = f"""You are SmartPayDoc, an expert Stripe developer assistant. Answer the user's question using the provided Stripe documentation context.

Context from Stripe documentation:
{context}

User question: {question}
Preferred language: {language}

Guidelines:
- Provide accurate, practical answers
- Include code examples in the requested language when relevant
- Explain concepts clearly
- Reference relevant Stripe documentation
- If the question can't be answered from the context, say so clearly

Answer:"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Failed to generate response: {e}")

    def _find_relevant_docs(self, query_embedding: np.ndarray, top_k: int = 3) -> List[StripeDocument]:
        """Find the most relevant documents using cosine similarity"""
        if not any(doc.embedding is not None for doc in self.documents):
            return self.documents[:top_k]  # Fallback if no embeddings
        
        similarities = []
        valid_docs = []
        
        for doc in self.documents:
            if doc.embedding is not None:
                similarity = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    doc.embedding.reshape(1, -1)
                )[0][0]
                similarities.append(similarity)
                valid_docs.append(doc)
        
        # Sort by similarity and return top_k
        sorted_indices = np.argsort(similarities)[::-1]
        return [valid_docs[i] for i in sorted_indices[:top_k]]