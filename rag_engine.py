"""
RAG Engine for Stripe Documentation
Handles document ingestion, embedding, and retrieval
"""

import os
import json
import asyncio
import sys
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pickle
from dataclasses import dataclass
from pathlib import Path
import aiohttp
import re
import traceback
from bs4 import BeautifulSoup

# Use Anthropic
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

@dataclass
class StripeDocument:
    title: str
    content: str
    url: str
    category: str
    embedding: np.ndarray = None

class StripeRAGEngine:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self.client = AsyncAnthropic(api_key=api_key)
        self.documents: List[StripeDocument] = []
        self.embeddings_cache = "stripe_embeddings.pkl"
        self.docs_cache = "stripe_docs.json"
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
        
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
        """Generate embeddings for all documents using Anthropic"""
        print("🔍 Generating embeddings...")
        
        # Filter out documents that already have embeddings
        docs_to_embed = [doc for doc in self.documents if doc.embedding is None]
        
        if not docs_to_embed:
            print("✅ All documents already have embeddings")
            return
        
        # Generate embeddings one by one (Anthropic doesn't support batch embeddings)
        for i, doc in enumerate(docs_to_embed):
            try:
                # Use the first 8192 characters as that's the limit for Claude
                text = doc.content[:8192]
                
                # Get embeddings from Anthropic
                # Note: Anthropic doesn't provide direct embeddings, so we'll use a simple approach
                # In production, consider using a dedicated embedding model
                pass
                
                # For now, we'll use a simple embedding approach since Anthropic doesn't provide direct embeddings
                # In a production environment, you might want to use a dedicated embedding model
                doc.embedding = np.random.rand(1536)  # Using random embeddings as placeholder
                
                if (i + 1) % 10 == 0:
                    print(f"✅ Processed {i + 1}/{len(docs_to_embed)} documents")
                
            except Exception as e:
                print(f"❌ Error generating embedding for document {i}: {e}")
                # Use a zero vector if embedding fails
                doc.embedding = np.zeros(1536)
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

    async def stream_ask(self, question: str, language: str = "python"):
        """Stream the response from the RAG system with a question using Anthropic"""
        try:
            if not question or not question.strip():
                yield "Please provide a valid question."
                return
                
            print(f"\n[DEBUG] Starting streaming query for: {question}")
            
            # Generate embedding for the question
            try:
                question_embedding = np.random.rand(1536)
            except Exception as e:
                print(f"[ERROR] Failed to generate question embedding: {e}")
                yield "I encountered an error while processing your question. Please try again."
                return
            
            # Find most relevant documents
            try:
                similarities = []
                for doc in self.documents:
                    if doc.embedding is not None and len(doc.embedding) > 0:
                        try:
                            # Calculate cosine similarity
                            sim = cosine_similarity(
                                [question_embedding],
                                [doc.embedding]
                            )[0][0]
                            similarities.append((doc, sim))
                        except Exception as e:
                            print(f"[DEBUG] Error calculating similarity: {e}")
                
                # Sort by similarity (highest first)
                similarities.sort(key=lambda x: x[1], reverse=True)
                
                # Get top 3 most relevant documents
                context_docs = [doc for doc, _ in similarities[:3]]
                
                if not context_docs:
                    yield "I couldn't find any relevant information to answer your question."
                    return
                
                # Prepare the context
                context = "\n\n".join([f"Document: {doc.title}\nContent: {doc.content[:1000]}..." 
                                      for doc in context_docs])
                
                # System prompt
                system_prompt = f"""You are a helpful assistant that provides clear, concise answers about the Stripe API.
                Answer the user's question based on the following context. If you don't know the answer, say so.
                
                Context:
                {context}
                
                Guidelines:
                - Be concise and to the point
                - Use natural language, not code blocks
                - Format your response in markdown
                - Keep responses under 500 words
                """
                
                # Initialize the streaming response
                stream = await self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[{"role": "user", "content": question}],
                    stream=True
                )
                
                # Stream the response
                async for chunk in stream:
                    if chunk.type == 'content_block_delta' and chunk.delta.text:
                        yield chunk.delta.text
                        
            except Exception as e:
                print(f"[ERROR] Error in document processing: {e}")
                yield "I encountered an error while processing the documents. Please try again."
                
        except Exception as e:
            print(f"[CRITICAL] Unexpected error in stream_ask: {e}")
            yield "I'm sorry, but I encountered an unexpected error. Please try again later."
    
    async def ask(self, question: str, language: str = "python") -> str:
        """Query the RAG system with a question using Anthropic"""
        print(f"\n[DEBUG] Starting query for: {question}")
        print(f"[DEBUG] Number of documents: {len(self.documents)}")
        
        # Generate embedding for the question (using a simple approach since we're using random embeddings)
        question_embedding = np.random.rand(1536)
        print(f"[DEBUG] Generated question embedding: {question_embedding[:5]}...")
        
        # Find most relevant documents
        similarities = []
        valid_docs = 0
        
        for doc in self.documents:
            if doc.embedding is not None:
                valid_docs += 1
                similarity = cosine_similarity(
                    question_embedding.reshape(1, -1),
                    doc.embedding.reshape(1, -1)
                )[0][0]
                similarities.append((similarity, doc))
        
        print(f"[DEBUG] Found {valid_docs} documents with valid embeddings")
        print(f"[DEBUG] Number of similarities calculated: {len(similarities)}")
        
        # Sort by similarity (highest first)
        similarities.sort(reverse=True, key=lambda x: x[0])
        print(f"[DEBUG] Top similarity scores: {[s[0] for s in similarities[:3]]}")
        
        # Get top 3 most relevant documents
        context = "\n\n".join([
            f"Document: {doc.title}\nURL: {doc.url}\nContent: {doc.content[:1000]}..."
            for _, doc in similarities[:3]
        ])
        
        print(f"[DEBUG] Context length: {len(context)} characters")
        
        # Generate response using Anthropic
        prompt = f"""You are a helpful assistant that answers questions about Stripe API.
        Use the following context to answer the question. If you don't know the answer, say so.
        
        Context:
        {context}
        
        Question: {question}
        
        Please provide a detailed answer in {language} code examples where appropriate."""
        
        print(f"[DEBUG] Sending prompt to Anthropic (length: {len(prompt)} chars)")
        
        try:
            print("[DEBUG] Calling Anthropic API...")
            
            # Create system and user messages
            system_prompt = """You are a Stripe API expert. Provide clear, beginner-friendly explanations about Stripe concepts.
        
Your responses should:
1. Start with a simple explanation of the concept
2. Explain when and why to use it
3. Provide a high-level overview of how it works
4. Include key parameters or considerations
5. End with a brief pseudocode example
6. Mention the 'Generate Code' tab for implementation

Keep the tone friendly and approachable."""

            # Create message parameters
            messages = [
                {"role": "user", "content": question}
            ]
            
            # Call the Messages API
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                system=system_prompt,
                messages=messages
            )
            
            print("[DEBUG] Received response from Anthropic Messages API")
            
            if message and hasattr(message, 'content'):
                # Extract the response text from the message content
                response_text = ""
                for content_block in message.content:
                    if hasattr(content_block, 'text'):
                        response_text += content_block.text
                
                # Add a friendly footer with a call-to-action
                footer = """

---

### Ready to implement this in your code?

Head over to the 'Generate Code' tab to get a complete, production-ready implementation in your preferred language and framework. You can customize the code to match your specific needs!

Need help with something else? Just ask! 😊"""
                
                return response_text.strip() + footer
                
            return "I'm sorry, I couldn't generate a response. Please try again or rephrase your question."
                
        except Exception as e:
            error_msg = f"❌ Error generating response: {e}"
            print(error_msg, file=sys.stderr)
            print(f"[DEBUG] Error details: {type(e).__name__}: {str(e)}", file=sys.stderr)
            traceback.print_exc()
            return f"I'm sorry, I encountered an error while generating a response: {str(e)}"
            
    # Alias for backward compatibility
    query = ask

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
