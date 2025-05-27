"""
Unit tests for codegen.py using Anthropic
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from codegen import StripeCodeGenerator

class TestStripeCodeGenerator:
    """Test cases for StripeCodeGenerator class with Anthropic"""
    
    @pytest.fixture(autouse=True)
    def setup_generator(self, mock_anthropic_client):
        """Set up the test generator with a mock Anthropic client"""
        self.generator = StripeCodeGenerator()
        self.mock_anthropic_client = mock_anthropic_client
    
    def test_load_templates(self):
        """Test that code templates are loaded correctly"""
        templates = self.generator._load_templates()
        
        # Check that we have templates for expected languages
        assert "python" in templates
        assert "javascript" in templates
        
        # Check that we have templates for expected frameworks
        assert "flask" in templates["python"]
        assert "fastapi" in templates["python"]
        assert "express" in templates["javascript"]
        
        # Check that we have templates for expected patterns
        assert "payment_intent" in templates["python"]["flask"]
        assert "subscription" in templates["python"]["flask"]
    
    @pytest.mark.asyncio
    async def test_generate_code_using_template(self):
        """Test code generation using pre-defined templates"""
        # Test with a known template
        task = "create a payment intent"
        language = "python"
        framework = "flask"
        
        # Mock the _get_template method to return a test template
        with patch.object(self.generator, '_get_template', return_value="@app.route\ndef payment_intent():\n    intent = stripe.PaymentIntent.create(\n        amount=2000,  # $20.00\n        currency='usd',\n    )\n    return jsonify({'client_secret': intent.client_secret})"):
            result = await self.generator.generate_code(task, language, framework)
            
            # Verify the result contains expected Flask route code
            assert "@app.route" in result
            assert "stripe.PaymentIntent.create" in result
            assert "return jsonify" in result
    
    def _extract_code_from_markdown(self, text: str) -> str:
        """Extract code blocks from markdown text.
        
        Args:
            text: The markdown text to extract code from
            
        Returns:
            The extracted code block, or the original text if no code block found
        """
        # Simple regex to extract code blocks
        import re
        code_blocks = re.findall(r'```(?:\w*\n)?(.*?)```', text, re.DOTALL)
        if code_blocks:
            # Return the first code block, stripping any leading/trailing whitespace
            return code_blocks[0].strip()
        return text
    
    @pytest.mark.asyncio
    async def test_generate_code_using_llm(self):
        """Test code generation using Anthropic fallback"""
        # Mock the Anthropic response
        mock_message = MagicMock()
        mock_message.content = [{"type": "text", "text": "```python\nprint('Hello World')\n```"}]
        self.mock_anthropic_client.messages.create.return_value = mock_message
        
        # Test with a custom task
        task = "create a custom payment flow"
        result = await self.generator.generate_code(task, "python", "flask")
        
        # Verify the result contains the expected code
        assert "print('Hello World')" in result
        
        # Verify the Anthropic client was called with the right parameters
        call_args = self.mock_anthropic_client.messages.create.call_args[1]
        assert call_args["model"] == "claude-3-opus-20240229"
        assert "create a custom payment flow" in call_args["messages"][0]["content"]
        assert "python" in str(call_args["messages"][0]["content"])
        assert "flask" in str(call_args["messages"][0]["content"])
    
    def test_extract_code_from_markdown(self):
        """Test extraction of code blocks from markdown"""
        # Test with a markdown string containing a code block
        markdown = """
        Here's some Python code:
        
        ```python
        def hello():
            print("Hello, World!")
        ```
        
        And here's some more text.
        """
        
        # Extract the code
        result = self.generator._extract_code_from_markdown(markdown)
        
        # Verify the code was extracted correctly
    
    @pytest.mark.asyncio
    async def test_generate_code_with_custom_instructions(self):
        """Test code generation with custom instructions"""
        # Mock the Anthropic response
        mock_message = MagicMock()
        mock_message.content = [{"type": "text", "text": "```python\n# Custom code\nprint('Hello')"}]        
        self.mock_anthropic_client.messages.create.return_value = mock_message
        
        # Test with custom instructions
        task = "create a custom payment form"
        instructions = "Use React hooks and Stripe Elements"
        
        result = await self.generator.generate_code(
            task, "javascript", "react", instructions=instructions
        )
        
        # Verify the result contains the custom code
        assert "print('Hello')" in result
        
        # Verify the Anthropic client was called with the custom instructions
        call_args = self.mock_anthropic_client.messages.create.call_args[1]
        assert instructions in str(call_args["messages"][0]["content"])
    
    def test_get_template(self):
        """Test getting the most relevant template for a task"""
        # Test with a task that should match the payment intent template
        task = "I need to create a payment intent"
        language = "python"
        framework = "flask"
        
        template = self.generator._get_template(task, language, framework)
        assert template is not None
        assert "@app.route" in template
        assert "stripe.PaymentIntent.create" in template
        
        # Test with a non-matching task (should return None)
        task = "this is a completely unrelated task"
        template = self.generator._get_template(task, language, framework)
        assert template is None
