# SmartPayDoc: AI-Powered Stripe Assistant

🚀 SmartPayDoc is your AI-powered developer assistant for Stripe integrations, powered by Anthropic's Claude LLM. Get instant answers, generate boilerplate code, and debug Stripe issues with natural language.

## ✨ Features

- **Ask Questions**: Get detailed answers about Stripe API usage with code examples
- **Generate Code**: Create production-ready boilerplate for common Stripe patterns
- **Debug Errors**: Analyze and resolve Stripe errors with AI-powered assistance
- **Webhook Analysis**: Understand and implement webhook handlers with ease
- **Multi-language Support**: Generate code in Python, JavaScript, and more

## 🛠️ Tech Stack

- **Backend**: Python 3.9.16, FastAPI 0.104.0
- **AI**: Anthropic Claude 3 (via API)
- **Payment Processing**: Stripe SDK 7.0.0
- **CLI**: Typer with Rich formatting
- **Vector Database**: FAISS for document retrieval

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- [Anthropic API key](https://console.anthropic.com/)
- [Stripe API key](https://dashboard.stripe.com/apikeys) (optional but recommended)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jadenfix/smartpaydoc.git
   cd smartpaydoc
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

4. Run the CLI:
   ```bash
   python -m smartpaydoc --help
   ```

## 🔧 Environment Variables

Create a `.env` file in the project root with the following variables:

```
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional (but recommended)
STRIPE_SECRET_KEY=your_stripe_secret_key
ANTHROPIC_MODEL=claude-3-opus-20240229  # Default
```

## 📚 Usage

### Ask Questions
Get answers to Stripe API questions with code examples:

```bash
# Basic question
smartpaydoc ask "How do I create a payment intent?"

# Language-specific examples
smartpaydoc ask "How to handle webhooks?" --lang javascript
```

### Generate Code
Create boilerplate code for common Stripe patterns:

```bash
# Payment integration
smartpaydoc generate "one-time payment" --lang python --framework flask

# Subscription billing
smartpaydoc generate "subscription with trial" --lang javascript --framework express

# Customer management
smartpaydoc generate "create customer" --lang python --framework fastapi
```

### Debug Errors
Analyze and fix Stripe errors:

```bash
# Analyze error message
smartpaydoc debug "stripe.error.CardError: Your card was declined"

# With additional context
smartpaydoc debug "payment_intent creation failed" --context "Using React frontend"
```

### Webhook Analysis
Understand webhook payloads and implement handlers:

```bash
# Analyze webhook payload
smartpaydoc webhook '{"type": "payment_intent.succeeded", "data": {...}}'

# From file
smartpaydoc webhook webhook.json

# With signature verification
smartpaydoc webhook webhook.json --verify
```

## 📦 Project Structure

```
smartpaydoc/
├── main.py            # CLI entry point
├── rag_engine.py      # Document retrieval and RAG implementation
├── codegen.py         # Code generation logic
├── error_helper.py    # Error analysis and debugging
├── requirements.txt   # Python dependencies
└── .env.template     # Template for environment variables
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Stripe](https://stripe.com/) for their excellent API and documentation
- [Anthropic](https://www.anthropic.com/) for their powerful AI models
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Typer](https://typer.tiangolo.com/) for building CLI applications
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output**
```python
=======


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

>>>>>>> origin/main
intent = stripe.PaymentIntent.create(
    amount=2000,
    currency='usd',
    payment_method='pm_card_visa'
)

<<<<<<< HEAD
### Generate Code

```bash
$ smartpaydoc generate "subscription checkout" --lang python --framework flask

📝 Generated Python Code:
```python
=======
Generate Code

$ smartpaydoc generate "subscription checkout" --lang python --framework flask

📝 Generated Python Code:

>>>>>>> origin/main
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

<<<<<<< HEAD
### Debug Errors

```bash
=======
Debug Errors

>>>>>>> origin/main
$ smartpaydoc debug "Your card was declined"

🛠️ Error Diagnosis & Solution:

<<<<<<< HEAD
**Error Type:** CardError
**Description:** The card was declined by the issuer

## Immediate Solutions
- Ask customer to contact their bank
- Try a different payment method  
- Check if card has sufficient funds
- Verify card details are correct

## Prevention Strategy
Implement retry logic with exponential backoff

## Code Example
```python
=======
Error Type: CardError
Description: The card was declined by the issuer

Immediate Solutions:
	•	Ask customer to contact their bank
	•	Try a different payment method
	•	Check if card has sufficient funds
	•	Verify card details are correct

Prevention Strategy:
	•	Implement retry logic with exponential backoff

>>>>>>> origin/main
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

<<<<<<< HEAD
## 🏗️ Architecture
=======

⸻

🏗️ Architecture

>>>>>>> origin/main
smartpaydoc/
├── main.py              # CLI interface
├── rag_engine.py        # Document retrieval & embeddings
├── codegen.py           # Code generation engine
├── error_helper.py      # Error diagnosis & webhook analysis
├── requirements.txt     # Dependencies
<<<<<<< HEAD
├── setup.py            # Package setup
├── .env.template       # Environment variables template
└── README.md           # Documentation


### Core Components

1. **RAG Engine** (`rag_engine.py`)
   - Ingests Stripe documentation
   - Generates embeddings for semantic search
   - Retrieves relevant context for queries

2. **Code Generator** (`codegen.py`)
   - Template-based code generation
   - LLM-powered custom code creation
   - Multi-language and framework support

3. **Error Helper** (`error_helper.py`)
   - Pattern matching for common errors
   - AI-powered error diagnosis
   - Webhook payload analysis

## 🔧 Configuration

### Environment Variables

```bash
=======
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

>>>>>>> origin/main
# Required
OPENAI_API_KEY=your_openai_api_key
STRIPE_SECRET_KEY=sk_test_your_stripe_key

# Optional
OPENAI_MODEL=gpt-4                    # Default: gpt-4
EMBEDDING_MODEL=text-embedding-ada-002 # Default: text-embedding-ada-002
CACHE_EMBEDDINGS=true                 # Default: true
<<<<<<< HEAD
Custom Templates
You can extend the code generator by adding custom templates:

python
=======

Custom Templates

You can extend the code generator by adding custom templates:

>>>>>>> origin/main
# In codegen.py
self.templates["python"]["django"] = {
    "payment_intent": "your_django_template_here"
}
<<<<<<< HEAD
🚦 Development
Running Tests
bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=smartpaydoc tests/
Contributing
Fork the repository
Create a feature branch (git checkout -b feature/amazing-feature)
Commit your changes (git commit -m 'Add amazing feature')
Push to the branch (git push origin feature/amazing-feature)
Open a Pull Request
📈 Roadmap
 VSCode Extension: Native IDE integration
 GitHub Action: Automated PR analysis for Stripe errors
 Multi-SDK Support: Add PayPal, Square, and other payment processors
 Interactive Mode: Chat-like interface for complex workflows
 Testing Integration: Generate test cases for Stripe integrations
 Documentation Generation: Auto-generate API documentation
🎯 Use Cases
For Interviews
Stripe Interview:

"I built SmartPayDoc to solve a real problem I faced - debugging webhook signature verification failures. It demonstrates deep Stripe knowledge and practical developer experience."

Windsurf Interview:

"This shows my ability to build LLM-native developer tools with proper RAG implementation, prompt engineering, and developer-first UX design."

For Development
Onboarding: Help new developers learn Stripe faster
Debugging: Quickly diagnose production issues
Prototyping: Generate boilerplate code for MVPs
Documentation: Interactive Stripe documentation
📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

🙏 Acknowledgments
Stripe for excellent API documentation
OpenAI for GPT-4 and embedding models
Typer for the CLI framework
Rich for beautiful terminal output
🤝 Support
📧 Email: support@smartpaydoc.com
🐛 Issues: GitHub Issues
💬 Discussions: GitHub Discussions
=======


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
>>>>>>> origin/main
