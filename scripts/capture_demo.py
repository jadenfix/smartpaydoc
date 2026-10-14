"""Capture the real browser fixture workflow and write source/media receipts."""
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/demo"
SOURCE_INPUTS = [
    "README.md", "codegen.py", "error_helper.py", "llm.py", "rag_engine.py",
    "stripe_docs.json", "web_app.py", ".python-version", "pyproject.toml",
    "web/static/script.js", "web/static/styles.css", "web/templates/index.html",
    ".github/workflows/ci.yml", "scripts/browser_smoke.py", "scripts/capture_demo.py",
    "scripts/smoke_workflow.py", "scripts/verify_demo.py",
    "tests/integration/test_grounded_workflow.py", "requirements.txt", "requirements-dev.txt",
]


def run(*args):
    return subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if run("git", "status", "--porcelain"):
        raise SystemExit("capture requires a clean source checkout")
    source_commit = run("git", "rev-parse", "HEAD")
    source_tree = run("git", "rev-parse", "HEAD^{tree}")
    manifest = {
        path: {"git_blob": run("git", "rev-parse", f"HEAD:{path}"), "sha256": sha256(ROOT / path)}
        for path in SOURCE_INPUTS
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    environment = dict(os.environ)
    environment.pop("ANTHROPIC_API_KEY", None)
    environment.pop("ANTHROPIC_MODEL", None)
    environment["SMARTPAYDOC_DEMO_MODE"] = "fictional-fixture"
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "web_app:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT, env=environment,
    )
    url = f"http://127.0.0.1:{port}"
    temp_dir = Path(tempfile.mkdtemp(prefix="smartpaydoc-capture-", dir="/dev/shm"))
    webm = temp_dir / "capture.webm"
    frame_dir = temp_dir / "frames"
    frame_dir.mkdir()
    frame_count = 0

    def capture_frames(page, count):
        nonlocal frame_count
        for _ in range(count):
            page.screenshot(path=str(frame_dir / f"frame-{frame_count:04d}.png"))
            frame_count += 1
            page.wait_for_timeout(125)
    try:
        for _ in range(100):
            try:
                with urlopen(url + "/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(.1)
        with sync_playwright() as playwright:
            executable = os.getenv("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
            browser = playwright.chromium.launch(executable_path=executable) if executable else playwright.chromium.launch()
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                record_video_dir=str(temp_dir), record_video_size={"width": 1280, "height": 720},
            )
            page = context.new_page()
            page.goto(url)
            page.wait_for_function("document.getElementById('modeLabel').textContent.includes('FICTIONAL FIXTURE')")
            capture_frames(page, 12)
            page.locator("#askForm button[type=submit]").click()
            page.wait_for_function("document.getElementById('answerContent').textContent.includes('provider-free replay')")
            capture_frames(page, 16)
            page.locator("#generateForm button[type=submit]").click()
            page.wait_for_function("document.getElementById('codeOutput').textContent.includes('stripe.PaymentIntent.create')")
            page.locator("#generateResult").scroll_into_view_if_needed()
            capture_frames(page, 20)
            page.screenshot(path=str(temp_dir / "smartpaydoc-fixture-demo-poster.png"))
            page.locator("#modeBadge").scroll_into_view_if_needed()
            capture_frames(page, 12)
            video = page.video
            page.close()
            context.close()
            recorded = Path(video.path())
            if recorded.exists() and recorded.stat().st_size:
                shutil.copy2(recorded, webm)
            browser.close()
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    staged_mp4 = temp_dir / "smartpaydoc-fixture-demo.mp4"
    staged_gif = temp_dir / "smartpaydoc-fixture-demo.gif"
    source_args = ["-i", str(webm)] if webm.exists() and webm.stat().st_size else [
        "-framerate", "8", "-i", str(frame_dir / "frame-%04d.png")
    ]
    subprocess.run([
        "ffmpeg", "-y", *source_args, "-an", "-vf", "fps=24,format=yuv420p",
        "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-movflags", "+faststart", str(staged_mp4),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", *source_args, "-vf",
        "fps=12,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer",
        str(staged_gif),
    ], check=True)

    mp4 = OUTPUT / staged_mp4.name
    gif = OUTPUT / staged_gif.name
    poster = OUTPUT / "smartpaydoc-fixture-demo-poster.png"
    for source, destination in (
        (staged_mp4, mp4),
        (staged_gif, gif),
        (temp_dir / poster.name, poster),
    ):
        shutil.copy2(source, destination)

    media = {}
    for path in (gif, mp4, poster):
        media[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    (OUTPUT / "source-manifest.json").write_text(json.dumps({
        "source_commit": source_commit, "source_tree": source_tree, "inputs": manifest,
    }, indent=2, sort_keys=True) + "\n")
    (OUTPUT / "capture.json").write_text(json.dumps({
        "schema": 1,
        "scope": "Actual local FastAPI + Chromium workflow in explicit deterministic fictional-fixture mode; no live Stripe/Anthropic calls or performance claims.",
        "source_commit": source_commit, "source_tree": source_tree,
        "command": "python scripts/capture_demo.py", "media": media,
    }, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(temp_dir)
    print(json.dumps(media, indent=2))


if __name__ == "__main__":
    main()
