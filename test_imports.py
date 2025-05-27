#!/usr/bin/env python3
"""Test script to verify imports and environment."""

import os
import sys

print("Python version:", sys.version)
print("\nPython path:")
for p in sys.path:
    print(f"  - {p}")

print("\nEnvironment variables:")
for var in ["ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "STRIPE_SECRET_KEY"]:
    print(f"  {var} = {os.getenv(var, 'Not set')}")

print("\nAttempting imports...")
try:
    import anthropic
    print("✅ anthropic imported successfully")
    
    import rag_engine
    print("✅ rag_engine imported successfully")
    
    import codegen
    print("✅ codegen imported successfully")
    
    import error_helper
    print("✅ error_helper imported successfully")
    
    from main import app
    print("✅ main imported successfully")
    
    print("\n✅ All imports successful!")
    
    # Test Anthropic client initialization
    try:
        client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        print("✅ Anthropic client initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing Anthropic client: {e}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nCurrent working directory:", os.getcwd())
    print("\nDirectory contents:")
    for f in os.listdir('.'):
        print(f"  - {f}")
    
    if "error_helper" in str(e):
        print("\n⚠️  error_helper.py contents:")
        try:
            with open("error_helper.py", "r") as f:
                print(f.read())
        except Exception as e2:
            print(f"Error reading error_helper.py: {e2}")
