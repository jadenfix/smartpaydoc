SmartPayDoc: LLM-Powered Stripe Assistant

 

An intelligent command-line assistant that helps developers integrate Stripe faster using AI-powered documentation retrieval, code generation, and error diagnosis.

⸻

Table of Contents
	•	Features
	•	Quick Start
	•	Installation
	•	Setup
	•	Basic Usage
	•	Commands
	•	ask
	•	generate
	•	debug
	•	webhook
	•	Examples
	•	Ask Questions
	•	Generate Code
	•	Debug Errors
	•	Core Components
	•	Configuration
	•	Environment Variables
	•	Custom Templates
	•	Development
	•	Contributing
	•	Roadmap
	•	Use Cases
	•	License
	•	Acknowledgments
	•	Support

⸻

Features
	•	Smart Q&A: Ask questions about Stripe API in natural language
	•	Code Generation: Generate boilerplate code for payments, subscriptions, and more
	•	Error Diagnosis: Analyze and fix Stripe errors with AI-powered solutions
	•	Webhook Analysis: Understand and handle webhook payloads
	•	Multi-Language Support: Python, JavaScript, and more
	•	Framework-Aware: Flask, FastAPI, Express, and other frameworks

⸻

Quick Start

Installation

Clone the repository and install dependencies:

git clone https://github.com/jadenfix/smartpaydoc.git
cd smartpaydoc
pip install -r requirements.txt
cp .env.template .env  # Edit .env with your API keys

Setup
	1.	Obtain your OpenAI API key from the OpenAI Platform.
	2.	Obtain your Stripe keys from the Stripe Dashboard.
	3.	Populate your .env file:

OPENAI_API_KEY=sk-your-openai-key
STRIPE_SECRET_KEY=sk-your-stripe-key

	4.	Initialize SmartPayDoc:

python main.py init

Basic Usage

# Ask a question about Stripe
python main.py ask "How do I create a customer with metadata?"

# Generate code
python main.py generate "subscription checkout" --lang python --framework flask

# Debug errors
python main.py debug "card_declined: Your card was declined"

# Analyze webhooks
python main.py webhook webhook_payload.json


⸻

Commands

ask

Get answers to Stripe API questions with code examples.

# Basic question
smartpaydoc ask "How do I create a payment intent?"

# Language-specific examples
smartpaydoc ask "How to handle webhooks?" --lang javascript

generate

Create boilerplate code for common Stripe patterns.

# Payment integration
smartpaydoc generate "one-time payment" --lang python --framework flask

# Subscription billing
smartpaydoc generate "subscription with trial" --lang javascript --framework express

# Customer management
smartpaydoc generate "create customer" --lang python --framework fastapi

debug

Analyze and fix Stripe errors.

# Analyze error message
smartpaydoc debug "stripe.error.CardError: Your card was declined"

# With additional context
smartpaydoc debug "payment_intent creation failed" --context "Using React frontend"

webhook

Understand webhook payloads and implement handlers.

# Analyze webhook payload
smartpaydoc webhook '{"type": "payment_intent.succeeded", "data": {...}}'

# From file
smartpaydoc webhook webhook.json

# With signature verification
smartpaydoc webhook webhook.json --verify


⸻

Examples

Ask Questions

$ smartpaydoc ask "What's the difference between Charges and Payment Intents?"

💡 SmartPayDoc Answer:

Payment Intents are the modern way to handle payments in Stripe, while Charges are the legacy approach. Here are the key differences:

Payment Intents (Recommended):
	•	Built for Strong Customer Authentication (SCA)
	•	Handles complex payment flows automatically
	•	Better error handling and retry logic
	•	Supports authentication methods like 3D Secure

Charges (Legacy):
	•	Immediate charge attempt
	•	Limited SCA support
	•	Manual handling of authentication
	•	Being phased out for new integrations

intent = stripe.PaymentIntent.create(
    amount=2000,
    currency='usd',
    payment_method='pm_card_visa'
)

Generate Code

$ smartpaydoc generate "subscription checkout" --lang python --framework flask

📝 Generated Python Code:

from flask import Flask, request, jsonify
import stripe
import os

app = Flask(__name__)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@app.route('/create-subscription', methods=['POST'])
def create_subscription():
    try:
        data = request.get_json()
        
        # Create customer
        customer = stripe.Customer.create(
            email=data.get('email'),
            payment_method=data.get('payment_method_id'),
            invoice_settings={
                'default_payment_method': data.get('payment_method_id')
            }
        )
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': data.get('price_id')}],
            trial_period_days=data.get('trial_days', 0),
            expand=['latest_invoice.payment_intent']
        )
        
        return jsonify({
            'subscription_id': subscription.id,
            'customer_id': customer.id,
            'status': subscription.status
        })
        
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)

Debug Errors

$ smartpaydoc debug "Your card was declined"

🛠️ Error Diagnosis & Solution:

Error Type: CardError
Description: The card was declined by the issuer

Immediate Solutions:
	•	Ask customer to contact their bank
	•	Try a different payment method
	•	Check if card has sufficient funds
	•	Verify card details are correct

Prevention Strategy:
	•	Implement retry logic with exponential backoff

try:
    payment_intent = stripe.PaymentIntent.create(
        amount=amount,
        currency='usd',
        payment_method=payment_method_id
    )
except stripe.error.CardError as e:
    if e.code == 'card_declined':
        # Handle declined card
        return {'error': 'Card declined', 'decline_code': e.decline_code}


⸻

🏗️ Architecture

smartpaydoc/
├── main.py              # CLI interface
├── rag_engine.py        # Document retrieval & embeddings
├── codegen.py           # Code generation engine
├── error_helper.py      # Error diagnosis & webhook analysis
├── requirements.txt     # Dependencies
├── setup.py             # Package setup
├── .env.template        # Environment variables template
└── README.md            # Documentation


⸻

Core Components
	1.	RAG Engine (rag_engine.py)
	•	Ingests Stripe documentation
	•	Generates embeddings for semantic search
	•	Retrieves relevant context for queries
	2.	Code Generator (codegen.py)
	•	Template-based code generation
	•	LLM-powered custom code creation
	•	Multi-language and framework support
	3.	Error Helper (error_helper.py)
	•	Pattern matching for common errors
	•	AI-powered error diagnosis
	•	Webhook payload analysis

⸻

Configuration

Environment Variables

# Required
OPENAI_API_KEY=your_openai_api_key
STRIPE_SECRET_KEY=sk_test_your_stripe_key

# Optional
OPENAI_MODEL=gpt-4                    # Default: gpt-4
EMBEDDING_MODEL=text-embedding-ada-002 # Default: text-embedding-ada-002
CACHE_EMBEDDINGS=true                 # Default: true

Custom Templates

You can extend the code generator by adding custom templates:

# In codegen.py
self.templates["python"]["django"] = {
    "payment_intent": "your_django_template_here"
}


⸻

🚦 Development

Running Tests:

pip install -r requirements-dev.txt
pytest tests/
pytest --cov=smartpaydoc tests/


⸻

Contributing
	1.	Fork the repository
	2.	Create a feature branch: git checkout -b feature/amazing-feature
	3.	Commit your changes: git commit -m 'Add amazing feature'
	4.	Push to the branch: git push origin feature/amazing-feature
	5.	Open a Pull Request

⸻

Roadmap
	•	VSCode Extension: Native IDE integration
	•	GitHub Action: Automated PR analysis for Stripe errors
	•	Multi-SDK Support: Add PayPal, Square, and other payment processors
	•	Interactive Mode: Chat-like interface for complex workflows
	•	Testing Integration: Generate test cases for Stripe integrations

⸻

Use Cases
	•	Onboarding: Help new developers learn Stripe faster
	•	Debugging: Quickly diagnose production issues
	•	Prototyping: Generate boilerplate code for MVPs
	•	Documentation: Interactive Stripe documentation

⸻
