"""Real local HTTP workflow with an explicitly controlled provider fixture."""
import asyncio
import hashlib
import hmac
import json
import os
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import requests
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag_engine import StripeRAGEngine
from web_app import FIXTURE_MODE, create_app


class FixtureClient:
    def __init__(self):
        self.messages = self
        self.last_request = None

    async def create(self, **kwargs):
        self.last_request = kwargs
        return SimpleNamespace(content=[SimpleNamespace(text="FIXTURE RESPONSE: inspect the PaymentIntent reference and adapt the server-side starter template.")])

    async def close(self):
        pass


def main():
    with tempfile.TemporaryDirectory() as directory, socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        provider = FixtureClient()
        rag = StripeRAGEngine(client=provider)
        rag.docs_cache = str(Path(directory) / "references.json")
        server = uvicorn.Server(uvicorn.Config(
            create_app(rag=rag, mode=FIXTURE_MODE), host="127.0.0.1", port=port, log_level="warning"
        ))
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{port}"
        try:
            deadline = time.monotonic() + 10
            while not server.started and time.monotonic() < deadline:
                time.sleep(.05)
            if not server.started:
                raise RuntimeError("Server did not become ready")
            assert requests.get(url, timeout=5).status_code == 200
            health = requests.get(url + "/health", timeout=5).json()
            assert health["references"] > 0
            assert health["mode"] == FIXTURE_MODE and health["fixture"] is True
            generated = requests.post(url + "/api/generate", data={"prompt": "create a payment intent", "language": "python", "framework": "flask"}, timeout=5)
            generated.raise_for_status()
            assert "stripe.PaymentIntent.create" in generated.json()["code"]
            answer = requests.post(url + "/api/ask", json={"question": "How do I create a PaymentIntent?"}, timeout=5)
            answer.raise_for_status()
            assert "FICTIONAL FIXTURE" in answer.text
            assert answer.headers["X-SmartPayDoc-Mode"] == FIXTURE_MODE
            assert provider.last_request is None
            diagnosed = requests.post(url + "/api/debug", json={"error_log": "card_declined"}, timeout=5)
            diagnosed.raise_for_status()
            assert "card_declined" in diagnosed.json()["analysis"]
            payload = json.dumps({"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_fixture", "amount": 2000}}})
            inspected = requests.post(url + "/api/webhook", json={"payload": payload}, timeout=5)
            inspected.raise_for_status()
            assert "unverified" in inspected.json()["analysis"]
            rejected = requests.post(url + "/api/webhook", json={"payload": payload, "verify": True}, timeout=5)
            assert rejected.status_code == 400
            print("PASS: actual HTTP UI → form generation → labeled fixture answer → error diagnosis → webhook inspection → reject missing signature")
            print("The response is an immutable fictional fixture. No live provider or Stripe request was made.")
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            if thread.is_alive():
                raise RuntimeError("Server did not shut down")


if __name__ == "__main__":
    main()
