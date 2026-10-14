"""Verify source provenance and fully decode SmartPayDoc demo media."""
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "docs/demo"


def run(*args):
    return subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def probe(path):
    return json.loads(run("ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                          "-show_entries", "stream=width,height,nb_read_frames:format=duration", "-of", "json", str(path)))


def main():
    capture = json.loads((DEMO / "capture.json").read_text())
    manifest = json.loads((DEMO / "source-manifest.json").read_text())
    assert capture["source_commit"] == manifest["source_commit"]
    assert capture["source_tree"] == manifest["source_tree"]
    assert run("git", "rev-parse", f"{capture['source_commit']}^{{tree}}") == capture["source_tree"]
    for name, expected in manifest["inputs"].items():
        path = ROOT / name
        assert sha256(path) == expected["sha256"], f"worktree drift: {name}"
        assert run("git", "rev-parse", f"{capture['source_commit']}:{name}") == expected["git_blob"], name
    for name, expected in capture["media"].items():
        path = DEMO / name
        assert path.stat().st_size == expected["bytes"], name
        assert sha256(path) == expected["sha256"], name
        if path.suffix in {".gif", ".mp4"}:
            details = probe(path)
            stream = details["streams"][0]
            assert int(stream["nb_read_frames"]) >= 90, name
            assert int(stream["width"]) >= 800 and int(stream["height"]) >= 450, name
            subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"], check=True)
            print(f"PASS {name}: {stream['nb_read_frames']} frames, {stream['width']}x{stream['height']}, fully decoded")
        else:
            assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
            print(f"PASS {name}: PNG signature and receipt hash")
    print(f"PASS source {capture['source_commit']} tree {capture['source_tree']} ({len(manifest['inputs'])} inputs)")


if __name__ == "__main__":
    main()
