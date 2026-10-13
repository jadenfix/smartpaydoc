"""Canonical local HTTP application for the SmartPayDoc browser and API."""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, ValidationError

from codegen import StripeCodeGenerator
from error_helper import StripeErrorHelper
from rag_engine import StripeRAGEngine

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=20000)
    language: str = "python"


class GenerateRequest(BaseModel):
    task: str = Field(min_length=1, max_length=20000)
    language: str = "python"
    framework: str = "flask"


class DebugRequest(BaseModel):
    error_log: str = Field(min_length=1, max_length=20000)
    context: Optional[str] = None


class WebhookRequest(BaseModel):
    payload: str = Field(min_length=1, max_length=200000)
    verify: bool = False
    signature: Optional[str] = None


def create_app(rag=None, codegen=None, error_helper=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.rag = rag or StripeRAGEngine()
        app.state.codegen = codegen or StripeCodeGenerator()
        app.state.error_helper = error_helper or StripeErrorHelper()
        await app.state.rag.initialize()
        yield
        seen = set()
        for component in (app.state.rag, app.state.codegen, app.state.error_helper):
            client = getattr(component, "client", None)
            if client is not None and id(client) not in seen:
                seen.add(id(client))
                await client.close()

    app = FastAPI(title="SmartPayDoc", version="1.0.0", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web/static")), name="static")
    templates = Jinja2Templates(directory=str(BASE_DIR / "web/templates"))

    @app.get("/")
    async def home(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/health")
    async def health():
        return {"status": "healthy", "references": len(app.state.rag.documents),
                "ai_configured": bool(os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_MODEL"))}

    async def execute(operation):
        try:
            return await operation
        except ValueError as error:
            message = str(error)
            if "ANTHROPIC_" in message:
                raise HTTPException(status_code=503, detail=message) from error
            raise HTTPException(status_code=400, detail=message) from error
        except Exception as error:
            logger.exception("Provider operation failed")
            raise HTTPException(status_code=502, detail="Provider operation failed") from error

    async def parse_request(request, model):
        try:
            if request.headers.get("content-type", "").startswith("application/json"):
                data = await request.json()
            else:
                data = dict(await request.form())
                if "prompt" in data and "task" not in data:
                    data["task"] = data.pop("prompt")
            return model.model_validate(data)
        except (ValueError, ValidationError) as error:
            raise HTTPException(status_code=422, detail="Invalid request fields") from error

    @app.post("/api/ask", response_class=PlainTextResponse)
    async def ask(request: Request):
        fields = await parse_request(request, AskRequest)
        return await execute(app.state.rag.ask(fields.question, fields.language))

    @app.post("/api/generate")
    async def generate(request: Request):
        fields = await parse_request(request, GenerateRequest)
        code = await execute(app.state.codegen.generate_code(fields.task, fields.language, fields.framework))
        return {"code": code}

    @app.post("/api/debug")
    async def debug(request: DebugRequest):
        return {"analysis": await execute(app.state.error_helper.diagnose_error(request.error_log, request.context))}

    @app.post("/api/webhook")
    async def webhook(request: WebhookRequest):
        return {"analysis": await execute(app.state.error_helper.analyze_webhook(
            request.payload, request.verify, signature=request.signature))}

    return app


app = create_app()
