"""SmartPayDoc CLI. Commands construct only the components they need."""
import asyncio
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax

from rag_engine import StripeRAGEngine
from codegen import StripeCodeGenerator
from error_helper import StripeErrorHelper

load_dotenv()
app = typer.Typer(help="SmartPayDoc: Stripe reference retrieval, starter code, and debugging")
console = Console()


def run(operation):
    try:
        return asyncio.run(operation)
    except Exception as error:
        console.print(f"Error: {error}", style="red")
        raise typer.Exit(1)


@app.command()
def ask(question: str, language: str = typer.Option("python", "--lang", "-l")):
    response = run(StripeRAGEngine().query(question, language))
    console.print(Markdown(response))


@app.command()
def generate(task: str, language: str = typer.Option("python", "--lang", "-l"),
             framework: str = typer.Option("flask", "--framework", "-f")):
    code = run(StripeCodeGenerator().generate_code(task, language, framework))
    console.print(Syntax(code, language, theme="monokai"))


@app.command()
def debug(error_log: str, context: Optional[str] = typer.Option(None, "--context", "-c")):
    console.print(Markdown(run(StripeErrorHelper().diagnose_error(error_log, context))))


@app.command()
def webhook(payload: str, verify: bool = typer.Option(False, "--verify"),
            signature: Optional[str] = typer.Option(None, "--signature")):
    try:
        path = Path(payload)
        if len(payload) < 240 and path.is_file():
            payload = path.read_text()
    except OSError:
        pass
    # Keep the legacy two-argument call when verification was not requested.
    helper = StripeErrorHelper()
    operation = helper.analyze_webhook(payload, verify_signature=True, signature=signature) if verify else helper.analyze_webhook(payload, False)
    console.print(run(operation))


@app.command()
def init():
    console.print("Initializing SmartPayDoc bundled reference excerpts...")
    run(StripeRAGEngine().initialize())
    console.print("Reference retrieval initialized. No live documentation fetch performed.")


@app.command()
def examples():
    console.print("Example Commands")
    console.print('smartpaydoc ask "How do I create a payment intent?"')
    console.print('smartpaydoc generate "create a payment intent" --lang python --framework flask')
    console.print('smartpaydoc debug "card_declined"')
    console.print('smartpaydoc webhook event.json')


if __name__ == "__main__":
    app()
