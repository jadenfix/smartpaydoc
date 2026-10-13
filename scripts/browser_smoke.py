"""Real browser check of the offline starter-template workflow; no paid API calls."""
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


def main():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    environment = dict(os.environ)
    environment.pop("ANTHROPIC_API_KEY", None)
    environment.pop("ANTHROPIC_MODEL", None)
    process = subprocess.Popen([sys.executable, "-m", "uvicorn", "web_app:app", "--host", "127.0.0.1", "--port", str(port)],
                               cwd=Path(__file__).resolve().parents[1], env=environment)
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                with urlopen(url + "/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                if process.poll() is not None:
                    raise RuntimeError("Server exited before becoming ready")
                time.sleep(.1)
        else:
            raise RuntimeError("Server did not become ready")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                for width, height in [(1280, 900), (390, 844)]:
                    page = browser.new_page(viewport={"width": width, "height": height})
                    page.goto(url)
                    page.locator("#prompt").fill("create a payment intent")
                    page.locator("#generateForm button[type=submit]").click()
                    page.wait_for_function("document.getElementById('codeOutput').textContent.includes('stripe.PaymentIntent.create')")
                    assert page.locator("#generateResult").is_visible()
                    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                    page.locator("#question").fill("How do payments work?")
                    page.locator("#askForm button[type=submit]").click()
                    page.wait_for_function("document.body.textContent.includes('ANTHROPIC_API_KEY')")
                    page.close()
                    print(f"PASS: {width}px template generation and missing-provider error")
            finally:
                browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    main()
