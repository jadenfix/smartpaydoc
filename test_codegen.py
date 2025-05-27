#!/usr/bin/env python3
"""
Test script to verify code generation functionality
"""
import asyncio
from codegen import StripeCodeGenerator

async def test_codegen():
    print("Testing Stripe code generation...")
    codegen = StripeCodeGenerator()
    
    # Test customer creation
    print("\nTesting customer creation:")
    result = await codegen.generate_code(
        "Create a new customer with email and name",
        "python",
        "flask"
    )
    print("\nGenerated code:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_codegen())
