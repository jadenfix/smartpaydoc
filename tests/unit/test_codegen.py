"""
<<<<<<< HEAD
Unit tests for codegen.py using Anthropic
=======
Unit tests for codegen.py
>>>>>>> origin/main
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from codegen import StripeCodeGenerator

class TestStripeCodeGenerator:
<<<<<<< HEAD
    """Test cases for StripeCodeGenerator class with Anthropic"""
    
    @pytest.fixture(autouse=True)
    def setup_generator(self, mock_anthropic_client):
        """Set up the test generator with a mock Anthropic client"""
        self.generator = StripeCodeGenerator()
        self.mock_anthropic_client = mock_anthropic_client
=======
    """Test cases for StripeCodeGenerator class"""
    
    @pytest.fixture(autouse=True)
    def setup_generator(self, mock_openai_client):
        """Set up the test generator with a mock OpenAI client"""
        self.generator = StripeCodeGenerator()
        self.mock_openai_client = mock_openai_client
>>>>>>> origin/main
    
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
        
<<<<<<< HEAD
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
=======
        result = await self.generator.generate_code(task, language, framework)
        
        # Verify the result contains expected Flask route code
        assert "@app.route" in result
        assert "stripe.PaymentIntent.create" in result
        assert "return jsonify" in result
    
    @pytest.mark.asyncio
    async def test_generate_code_using_llm(self):
        """Test code generation using LLM fallback"""
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "```python\n# Test generated code\nprint('Hello, Stripe!')\n```"
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Test with a task that doesn't match any template
        task = "create a custom payment flow with 3D Secure"
        language = "python"
        framework = "django"
        
        result = await self.generator.generate_code(task, language, framework)
        
        # Verify the result contains the generated code
        assert "Test generated code" in result
        assert "print('Hello, Stripe!')" in result
        
        # Verify the LLM was called with the correct parameters
        call_args = self.mock_openai_client.chat.completions.create.call_args[1]
        assert "create a custom payment flow with 3D Secure" in call_args["messages"][0]["content"]
        assert "python" in call_args["messages"][0]["content"]
        assert "django" in call_args["messages"][0]["content"]
>>>>>>> origin/main
    
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
<<<<<<< HEAD
=======
        assert "def hello():" in result
        assert "print(\"Hello, World!\")" in result
        assert "Here's some Python code" not in result
        
        # Test with multiple code blocks (should return the first one)
        markdown = """
        ```javascript
        console.log("First code block");
        ```
        
        ```python
        print("Second code block")
        ```
        """
        
        result = self.generator._extract_code_from_markdown(markdown)
        assert "console.log" in result
        assert "print" not in result
        
        # Test with no code blocks (should return the original text)
        markdown = "Just some regular text, no code here."
        result = self.generator._extract_code_from_markdown(markdown)
        assert result == markdown
>>>>>>> origin/main
    
    @pytest.mark.asyncio
    async def test_generate_code_with_custom_instructions(self):
        """Test code generation with custom instructions"""
<<<<<<< HEAD
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
=======
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "```python\n# Custom code\nprint('Custom code')\n```"
        self.mock_openai_client.chat.completions.create.return_value = mock_response
        
        # Test with custom instructions
        task = "create a payment form"
        language = "python"
        framework = "flask"
        custom_instructions = "Use Flask-WTF for form handling"
        
        result = await self.generator.generate_code(
            task, language, framework, custom_instructions
        )
        
        # Verify the result contains the generated code
        assert "Custom code" in result
        
        # Verify the custom instructions were included in the LLM prompt
        call_args = self.mock_openai_client.chat.completions.create.call_args[1]
        assert "Use Flask-WTF for form handling" in call_args["messages"][0]["content"]
>>>>>>> origin/main
    
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
