"""Real-browser checks for explicit fixture mode and DOM-safe provider rendering."""
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
    environment["SMARTPAYDOC_DEMO_MODE"] = "fictional-fixture"
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "web_app:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=Path(__file__).resolve().parents[1], env=environment,
    )
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
            executable = os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
            browser = playwright.chromium.launch(executable_path=executable) if executable else playwright.chromium.launch()
            try:
                for width, height in [(1280, 900), (390, 844)]:
                    page = browser.new_page(viewport={"width": width, "height": height})
                    page.goto(url)
                    page.wait_for_function(
                        "document.getElementById('modeLabel').textContent.includes('FICTIONAL FIXTURE')"
                    )
                    assert page.locator("#fixtureNotice").is_visible()
                    overflow = page.evaluate("""() => ({
                        document: [document.documentElement.scrollWidth, window.innerWidth],
                        offenders: [...document.querySelectorAll('body *')]
                            .filter((element) => element.getBoundingClientRect().right > window.innerWidth + 1)
                            .slice(0, 5)
                            .map((element) => [element.tagName, element.id, element.className,
                                Math.round(element.getBoundingClientRect().right)]),
                        internal: [...document.querySelectorAll('body *')]
                            .filter((element) => element.scrollWidth > element.clientWidth + 1)
                            .slice(0, 8)
                            .map((element) => [element.tagName, element.id, element.className,
                                element.scrollWidth, element.clientWidth])
                    })""")
                    assert overflow["document"][0] <= overflow["document"][1], overflow

                    page.locator("#prompt").fill("create a payment intent")
                    page.locator("#generateForm button[type=submit]").click()
                    page.wait_for_function(
                        "document.getElementById('codeOutput').textContent.includes('stripe.PaymentIntent.create')"
                    )
                    assert page.locator("#generateResult").is_visible()

                    page.locator("#question").fill("malicious rendering probe")
                    page.locator("#askForm button[type=submit]").click()
                    page.wait_for_function(
                        "document.getElementById('answerContent').textContent.includes('window.__smartpaydocInjected=1')"
                    )
                    assert page.locator("#answerContent img").count() == 0
                    assert page.evaluate("window.__smartpaydocInjected === undefined")
                    assert page.locator("#answerContent").text_content().startswith("<img src=x")
                    overflow = page.evaluate("""() => ({
                        document: [document.documentElement.scrollWidth, window.innerWidth],
                        offenders: [...document.querySelectorAll('body *')]
                            .filter((element) => element.getBoundingClientRect().right > window.innerWidth + 1)
                            .slice(0, 5)
                            .map((element) => [element.tagName, element.id, element.className,
                                Math.round(element.getBoundingClientRect().right)]),
                        internal: [...document.querySelectorAll('body *')]
                            .filter((element) => element.scrollWidth > element.clientWidth + 1)
                            .slice(0, 8)
                            .map((element) => [element.tagName, element.id, element.className,
                                element.scrollWidth, element.clientWidth])
                    })""")
                    assert overflow["document"][0] <= overflow["document"][1], overflow
                    page.close()
                    print(f"PASS: {width}px fixture workflow and literal malicious-provider rendering")
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
