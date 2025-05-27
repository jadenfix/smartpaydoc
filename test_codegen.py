import asyncio
import os
from dotenv import load_dotenv
from codegen import StripeCodeGenerator

async def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize the code generator
    generator = StripeCodeGenerator()
    
    # Test 1: Generate a payment intent handler
    print("Testing payment intent generation...")
    payment_intent_code = await generator.generate_code(
        task="Create a payment intent with customer details and metadata",
        language="python",
        framework="flask"
    )
    print("\nGenerated Payment Intent Code:")
    print("=" * 50)
    print(payment_intent_code)
    print("=" * 50)
    
    # Test 2: Explain some code
    print("\nTesting code explanation...")
    example_code = """
    import stripe
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    
    def create_customer(email, name):
        return stripe.Customer.create(
            email=email,
            name=name,
            metadata={"signup_source": "website"}
        )
    """
    explanation = await generator.explain_code(example_code, "python")
    print("\nCode Explanation:")
    print("=" * 50)
    print(explanation)
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())