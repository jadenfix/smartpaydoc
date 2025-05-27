#!/usr/bin/env python3
"""
<<<<<<< HEAD
SmartPayDoc: LLM-Powered Developer Assistant for Stripe Integrations using Anthropic
=======
SmartPayDoc: LLM-Powered Developer Assistant for Stripe Integrations
>>>>>>> origin/main
CLI Entry Point
"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
import asyncio
from typing import Optional
import os
from dotenv import load_dotenv

<<<<<<< HEAD
# Load environment variables first
load_dotenv()

# Verify required environment variables
if not os.getenv("ANTHROPIC_API_KEY"):
    raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
if not os.getenv("STRIPE_SECRET_KEY"):
    print("Warning: STRIPE_SECRET_KEY not set. Some features may not work.")

=======
>>>>>>> origin/main
from rag_engine import StripeRAGEngine
from codegen import StripeCodeGenerator
from error_helper import StripeErrorHelper

<<<<<<< HEAD
app = typer.Typer(help="🚀 SmartPayDoc: Your AI Stripe Integration Assistant")
console = Console()

# Initialize components with error handling
try:
    rag = StripeRAGEngine()
    codegen = StripeCodeGenerator()
    error_helper = StripeErrorHelper()
except Exception as e:
    console.print(f"❌ Error initializing components: {e}", style="red")
    raise
=======
# Load environment variables
load_dotenv()

app = typer.Typer(help="🚀 SmartPayDoc: Your AI Stripe Integration Assistant")
console = Console()

# Initialize components
rag = StripeRAGEngine()
codegen = StripeCodeGenerator()
error_helper = StripeErrorHelper()
>>>>>>> origin/main

@app.command()
def ask(
    question: str = typer.Argument(..., help="Your question about Stripe API"),
    language: str = typer.Option("python", "--lang", "-l", help="Programming language for examples")
):
    """Ask questions about Stripe API usage"""
    console.print(Panel.fit("🤔 Thinking...", style="blue"))
    
    try:
        response = asyncio.run(rag.query(question, language))
        
        console.print(Panel(
            Markdown(response),
            title="💡 SmartPayDoc Answer",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")

@app.command()
def generate(
    task: str = typer.Argument(..., help="What you want to implement"),
    language: str = typer.Option("python", "--lang", "-l", help="Programming language"),
    framework: str = typer.Option("flask", "--framework", "-f", help="Framework (flask, fastapi, express, etc.)")
):
    """Generate boilerplate code for Stripe integrations"""
    console.print(Panel.fit("⚡ Generating code...", style="blue"))
    
    try:
        code = asyncio.run(codegen.generate_code(task, language, framework))
        
        console.print(Panel(
            Syntax(code, language.lower(), theme="monokai", line_numbers=True),
            title=f"📝 Generated {language.title()} Code",
            border_style="green"
        ))
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")

@app.command()
def debug(
    error_log: str = typer.Argument(..., help="Stripe error message or webhook log"),
    context: Optional[str] = typer.Option(None, "--context", "-c", help="Additional context about what you were trying to do")
):
    """Debug Stripe errors and webhook issues"""
    console.print(Panel.fit("🔍 Analyzing error...", style="blue"))
    
    try:
        diagnosis = asyncio.run(error_helper.diagnose_error(error_log, context))
        
        console.print(Panel(
            Markdown(diagnosis),
            title="🛠️ Error Diagnosis & Solution",
            border_style="yellow"
        ))
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")

@app.command()
def webhook(
    payload: str = typer.Argument(..., help="Webhook payload JSON or file path"),
    verify: bool = typer.Option(False, "--verify", help="Verify webhook signature")
):
    """Analyze and explain webhook payloads"""
    console.print(Panel.fit("📡 Analyzing webhook...", style="blue"))
    
    try:
        # Check if payload is a file path
        if os.path.exists(payload):
            with open(payload, 'r') as f:
                payload = f.read()
        
        analysis = asyncio.run(error_helper.analyze_webhook(payload, verify))
        
        console.print(Panel(
            Markdown(analysis),
            title="📡 Webhook Analysis",
            border_style="cyan"
        ))
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")

@app.command()
def init():
    """Initialize SmartPayDoc and download Stripe documentation"""
    console.print(Panel.fit("🚀 Initializing SmartPayDoc...", style="blue"))
    
    try:
        asyncio.run(rag.initialize())
        console.print("✅ SmartPayDoc initialized successfully!", style="green")
        console.print("\n💡 Try these commands:")
        console.print("  • smartpaydoc ask 'How do I create a customer?'")
        console.print("  • smartpaydoc generate 'subscription checkout' --lang python")
        console.print("  • smartpaydoc debug 'card_declined: Your card was declined'")
    except Exception as e:
        console.print(f"❌ Initialization failed: {e}", style="red")

@app.command()
def examples():
    """Show example commands and use cases"""
    examples_text = """
# 🚀 SmartPayDoc Examples

## Ask Questions
```bash
smartpaydoc ask "How do I create a customer with metadata?"
smartpaydoc ask "What's the difference between payment intent and setup intent?"
smartpaydoc ask "How to handle failed payments?" --lang javascript
```

## Generate Code
```bash
smartpaydoc generate "one-time payment" --lang python --framework flask
smartpaydoc generate "subscription with trial" --lang javascript --framework express
smartpaydoc generate "marketplace payout" --lang python --framework fastapi
```

## Debug Errors
```bash
smartpaydoc debug "stripe.error.CardError: Your card was declined"
smartpaydoc debug "webhook signature verification failed" --context "Using Flask"
```

## Analyze Webhooks
```bash
smartpaydoc webhook '{"type": "payment_intent.succeeded", "data": {...}}'
smartpaydoc webhook webhook_payload.json --verify
```
    """
    console.print(Markdown(examples_text))

if __name__ == "__main__":
    app()