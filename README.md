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
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output
## 🛠️ Example: Debugging a Declined Card

```bash
# Debug a declined card error
$ smartpaydoc debug "Your card was declined"
```

### Expected Output:

```
🔍 Error Analysis:

Error Type: CardError
Description: The card was declined by the issuer

🛠️ Recommended Actions:
• Ask customer to contact their bank
• Try a different payment method
• Verify card details are correct
• Check if card has sufficient funds

💡 Prevention Strategy:
• Implement proper error handling with user-friendly messages
• Add retry logic with exponential backoff
• Consider implementing 3D Secure for additional security

📝 Code Example:
```python
try:
    payment_intent = stripe.PaymentIntent.create(
        amount=amount,
        currency='usd',
        payment_method=payment_method_id,
        confirm=True
    )
except stripe.error.CardError as e:
    # Handle specific error codes
    if e.code == 'card_declined':
        # Log the error
        logger.error(f"Card was declined: {e.user_message}")
        # Return user-friendly message
        return {"error": "Your card was declined. Please try another payment method."}
    # Handle other card errors...
```

For more detailed error handling, use the Stripe API's error codes to provide specific guidance to your users.

## 📈 Roadmap

- **VSCode Extension**: Native IDE integration
- **GitHub Action**: Automated PR analysis for Stripe errors
- **Multi-SDK Support**: Add PayPal, Square, and other payment processors
- **Interactive Mode**: Chat-like interface for complex workflows
- **Testing Integration**: Generate test cases for Stripe integrations
- **Documentation Generation**: Auto-generate API documentation

## 🎯 Use Case

- **For Development**: Use SmartPayDoc to streamline your development workflow, from onboarding to debugging.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Stripe](https://stripe.com/) for their excellent API and documentation
- [Anthropic](https://www.anthropic.com/) for their powerful AI models
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [Typer](https://typer.tiangolo.com/) for building CLI applications
- [Rich](https://github.com/Textualize/rich) for beautiful terminal output

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Report bugs**: Open an issue to report any bugs or issues you find
2. **Suggest features**: Have an idea for a new feature? Let us know!
3. **Submit PRs**: Feel free to submit pull requests with improvements

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 🎯 Use Cases

### For Developers
- **Rapid Prototyping**: Quickly generate Stripe integration code for new projects
- **Debugging**: Get AI-powered assistance for troubleshooting Stripe issues
- **Learning**: Understand Stripe concepts and best practices through interactive examples

### For Interviews
- **Stripe Interview**: Showcase your expertise in Stripe integrations and payment processing
- **Developer Tools Interview**: Demonstrate your ability to build LLM-powered developer tools
- **Full-Stack Interview**: Highlight both backend integration skills and developer experience design

## 🧪 Testing

To run the test suite:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/

# Run with coverage report
pytest --cov=smartpaydoc tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
