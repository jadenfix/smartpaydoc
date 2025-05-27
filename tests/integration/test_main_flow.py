"""
Integration tests for the main application flow
"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from typer.testing import CliRunner
from main import app

class TestMainFlow:
    """Test the main application flow"""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing"""
        return CliRunner()
    
    @patch('main.StripeRAGEngine')
    @patch('main.StripeCodeGenerator')
    @patch('main.StripeErrorHelper')
    def test_ask_command(self, mock_error_helper, mock_codegen, mock_rag, runner):
        """Test the ask command"""
        # Setup mocks
        mock_instance = AsyncMock()
        mock_instance.query.return_value = "Test response"
        mock_rag.return_value = mock_instance
        
        # Run the command
        result = runner.invoke(app, ["ask", "How do I create a payment intent?"])
        
        # Verify the output
        assert result.exit_code == 0
        assert "Test response" in result.output
        mock_instance.query.assert_called_once_with("How do I create a payment intent?", "python")
    
    @patch('main.StripeCodeGenerator')
    def test_generate_command(self, mock_codegen, runner):
        """Test the generate command"""
        # Setup mocks
        mock_instance = AsyncMock()
        mock_instance.generate_code.return_value = "def test(): pass"
        mock_codegen.return_value = mock_instance
        
        # Run the command
        result = runner.invoke(app, [
            "generate", "payment intent", "--lang", "python", "--framework", "flask"
        ])
        
        # Verify the output
        assert result.exit_code == 0
        assert "def test():" in result.output
        mock_instance.generate_code.assert_called_once()
    
    @patch('main.StripeErrorHelper')
    def test_debug_command(self, mock_error_helper, runner):
        """Test the debug command"""
        # Setup mocks
        mock_instance = AsyncMock()
        mock_instance.diagnose_error.return_value = "Error diagnosis"
        mock_error_helper.return_value = mock_instance
        
        # Run the command
        result = runner.invoke(app, ["debug", "card_declined: Your card was declined"])
        
        # Verify the output
        assert result.exit_code == 0
        assert "Error diagnosis" in result.output
        mock_instance.diagnose_error.assert_called_once()
    
    @patch('main.StripeErrorHelper')
    @patch('builtins.open')
    def test_webhook_command_with_file(self, mock_open, mock_error_helper, runner, tmp_path):
        """Test the webhook command with a file input"""
        # Setup test file
        test_file = tmp_path / "webhook.json"
        webhook_data = {"type": "payment_intent.succeeded", "data": {"object": {}}}
        test_file.write_text(json.dumps(webhook_data))
        
        # Setup mocks
        mock_instance = AsyncMock()
        mock_instance.analyze_webhook.return_value = "Webhook analysis"
        mock_error_helper.return_value = mock_instance
        
        # Run the command
        result = runner.invoke(app, ["webhook", str(test_file)])
        
        # Verify the output
        assert result.exit_code == 0
        assert "Webhook analysis" in result.output
        mock_instance.analyze_webhook.assert_called_once()
    
    def test_examples_command(self, runner):
        """Test the examples command"""
        result = runner.invoke(app, ["examples"])
        assert result.exit_code == 0
        assert "Example Commands" in result.output
    
    @patch('main.StripeRAGEngine')
    def test_init_command(self, mock_rag, runner):
        """Test the init command"""
        # Setup mocks
        mock_instance = AsyncMock()
        mock_rag.return_value = mock_instance
        
        # Run the command
        result = runner.invoke(app, ["init"])
        
        # Verify the output
        assert result.exit_code == 0
        assert "Initializing SmartPayDoc" in result.output
        mock_instance.initialize.assert_called_once()
