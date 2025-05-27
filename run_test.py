# First, let's install the required packages
import subprocess
import sys

# Install required packages
subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv", "anthropic", "stripe"])

# Now let's run the test
print("Running the test script...")
result = subprocess.run([sys.executable, "test_codegen.py"], capture_output=True, text=True)

# Print the output
print("Test Output:")
print(result.stdout)
if result.stderr:
    print("\nErrors:")
    print(result.stderr)
