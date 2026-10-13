"""Code-generation contracts with an explicit local provider fixture."""
from types import SimpleNamespace
import pytest
from codegen import StripeCodeGenerator

@pytest.mark.asyncio
async def test_custom_generation_uses_provider(mock_anthropic_client):
    mock_anthropic_client.messages.create.return_value = SimpleNamespace(content=[SimpleNamespace(text="```python\nprint('fixture')\n```")])
    generator = StripeCodeGenerator()
    assert await generator.generate_code("custom integration", "python", "flask") == "print('fixture')"
    assert "python" in mock_anthropic_client.messages.create.call_args.kwargs["system"]

@pytest.mark.asyncio
async def test_template_survives_provider_failure(mock_anthropic_client):
    mock_anthropic_client.messages.create.side_effect = RuntimeError("fixture outage")
    result = await StripeCodeGenerator().generate_code("create payment intent", "python", "flask")
    assert "stripe.PaymentIntent.create" in result

@pytest.mark.asyncio
async def test_custom_failure_is_not_reported_as_code(mock_anthropic_client):
    mock_anthropic_client.messages.create.side_effect = RuntimeError("fixture outage")
    with pytest.raises(Exception, match="Failed to generate code"):
        await StripeCodeGenerator().generate_code("custom integration")

@pytest.mark.asyncio
async def test_context_failure_preserves_original_exception(mock_anthropic_client):
    mock_anthropic_client.messages.create.side_effect = RuntimeError("fixture outage")
    with pytest.raises(RuntimeError, match="Context-based code generation failed"):
        await StripeCodeGenerator()._generate_from_context("custom", "context")

def test_markdown_extraction(mock_anthropic_client):
    generator = StripeCodeGenerator()
    assert generator._extract_code_from_markdown("Answer\n```python\nprint(1)\n```") == "print(1)"
    assert "payment_intent" in generator._load_templates()["python"]["flask"]
