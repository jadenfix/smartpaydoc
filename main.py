#!/usr/bin/env python3
"""
SmartPayDoc: LLM-Powered Developer Assistant for Stripe Integrations using Anthropic
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
import sys
from dotenv import load_dotenv

# Debug print function
def debug_print(*args, **kwargs):
    """Print debug information to stderr"""
    print("\n[DEBUG]", *args, file=sys.stderr, **kwargs)

# Print Python version and path for debugging
debug_print(f"Python {sys.version}")
debug_print("Python path:", sys.path)

# Load environment variables
load_dotenv(override=True)
debug_print("Environment variables loaded")
debug_print(f"ANTHROPIC_API_KEY: {'***' if os.getenv('ANTHROPIC_API_KEY') else 'Not set'}")
debug_print(f"ANTHROPIC_MODEL: {os.getenv('ANTHROPIC_MODEL')}")
debug_print(f"STRIPE_SECRET_KEY: {'***' if os.getenv('STRIPE_SECRET_KEY') else 'Not set'}")

# Load environment variables first
load_dotenv(override=True)

# Verify required environment variables
required_vars = ["ANTHROPIC_API_KEY", "ANTHROPIC_MODEL"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Set default model if not specified
os.environ.setdefault("ANTHROPIC_MODEL", "claude-3-opus-20240229")

# Warn about missing optional variables
if not os.getenv("STRIPE_SECRET_KEY"):
    print("Warning: STRIPE_SECRET_KEY not set. Some features may not work.")

from rag_engine import StripeRAGEngine
from codegen import StripeCodeGenerator
from error_helper import StripeErrorHelper

app = typer.Typer(help="🚀 SmartPayDoc: Your AI Stripe Integration Assistant")
console = Console()

# Initialize components with error handling
try:
    rag = StripeRAGEngine()
    codegen = StripeCodeGenerator()
    error_helper = StripeErrorHelper()
    
    # Initialize the RAG engine
    debug_print("Initializing RAG engine...")
    asyncio.run(rag.initialize())
    debug_print("RAG engine initialized successfully")
    
except Exception as e:
    console.print(f"❌ Error initializing components: {e}", style="red")
    debug_print(f"Initialization error: {e}", exc_info=True)
    raise

@app.command()
def ask(
    question: str = typer.Argument(..., help="Your question about Stripe API"),
    language: str = typer.Option("python", "--lang", "-l", help="Programming language for examples")
):
    """Ask questions about Stripe API usage"""
    debug_print(f"\n{'='*50}")
    debug_print("ASK FUNCTION STARTED")
    debug_print(f"Question: {question}")
    debug_print(f"Language: {language}")
    
    console.print(Panel.fit("🤔 Thinking...", style="blue"))
    
    try:
        debug_print("\n[1/4] Preparing to call rag.query()...")
        debug_print(f"RAG engine type: {type(rag).__name__}")
        debug_print(f"RAG documents loaded: {len(rag.documents) if hasattr(rag, 'documents') else 'N/A'}")
        
        debug_print("\n[2/4] Calling rag.query()...")
        response = asyncio.run(rag.query(question, language))
        debug_print("✅ rag.query() completed successfully")
        debug_print(f"Response type: {type(response)}")
        debug_print(f"Response length: {len(response) if response else 0} characters")
        
        debug_print("\n[3/4] Formatting response...")
        debug_print(f"Response preview: {response[:200]}..." if response else "No response")
        
        debug_print("\n[4/4] Displaying response...")
        console.print(Panel(
            Markdown(response) if response else "No response received",
            title="💡 SmartPayDoc Answer",
            border_style="green"
        ))
        debug_print("✅ Response displayed successfully")
        
    except Exception as e:
        debug_print(f"\n❌ ERROR in ask(): {e}", exc_info=True)
        debug_print(f"Error type: {type(e).__name__}")
        debug_print(f"Error args: {e.args}")
        
        import traceback
        debug_print("\nStack trace:")
        debug_print(traceback.format_exc())
        
        console.print(Panel(
            f"❌ Error: {str(e)}\n\nPlease check the logs for more details.",
            title="Error",
            border_style="red"
        ))
    
    debug_print("\nASK FUNCTION COMPLETED")
    debug_print(f"{'='*50}\n")

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
    examples_text = """ """
    
    console.print(Panel(
        Markdown("""
        ## Example Commands
        
        ### Ask a question about Stripe API
        ```bash
        smartpaydoc ask "How do I create a customer with metadata?"
        ```
        
        ### Generate code for a specific task
        ```bash
        smartpaydoc generate "subscription checkout" --lang python
        ```
        
        ### Debug a Stripe error
        ```bash
        smartpaydoc debug "card_declined: Your card was declined"
        ```
        
        ### Analyze a webhook payload
        ```bash
        smartpaydoc webhook 'path/to/webhook_payload.json'
        ```
        """),
        title="📚 SmartPayDoc Examples",
        border_style="blue"
    ))

if __name__ == "__main__":
    app()
    