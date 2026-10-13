"""CLI wiring with explicitly synthetic provider fixtures; no live API calls."""
import json
from unittest.mock import AsyncMock
import pytest
from typer.testing import CliRunner

@pytest.fixture
def cli(monkeypatch, mock_anthropic_client):
    import main
    monkeypatch.setattr(main, "rag", AsyncMock())
    monkeypatch.setattr(main, "codegen", AsyncMock())
    monkeypatch.setattr(main, "error_helper", AsyncMock())
    return main, CliRunner()

def test_ask(cli):
    main, runner = cli
    main.rag.query.return_value = "fixture answer"
    result = runner.invoke(main.app, ["ask", "payment question"])
    assert result.exit_code == 0, result.exception
    assert "fixture answer" in result.output
    main.rag.query.assert_awaited_once_with("payment question", "python")

def test_generate(cli):
    main, runner = cli
    main.codegen.generate_code.return_value = "print('fixture')"
    result = runner.invoke(main.app, ["generate", "custom integration"])
    assert result.exit_code == 0, result.exception
    assert "print('fixture')" in result.output

def test_debug(cli):
    main, runner = cli
    main.error_helper.diagnose_error.return_value = "fixture diagnosis"
    result = runner.invoke(main.app, ["debug", "fixture error"])
    assert result.exit_code == 0, result.exception
    main.error_helper.diagnose_error.assert_awaited_once()

def test_webhook_reads_real_file(cli, tmp_path):
    main, runner = cli
    path = tmp_path / "event.json"
    payload = json.dumps({"type": "payment_intent.succeeded", "data": {"object": {"id": "fixture"}}})
    path.write_text(payload)
    main.error_helper.analyze_webhook.return_value = "fixture event"
    result = runner.invoke(main.app, ["webhook", str(path)])
    assert result.exit_code == 0, result.exception
    assert "fixture event" in result.output
    main.error_helper.analyze_webhook.assert_awaited_once()

def test_examples(cli):
    main, runner = cli
    result = runner.invoke(main.app, ["examples"])
    assert result.exit_code == 0, result.exception

def test_init(cli):
    main, runner = cli
    result = runner.invoke(main.app, ["init"])
    assert result.exit_code == 0, result.exception
    main.rag.initialize.assert_awaited_once()
