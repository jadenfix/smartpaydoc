from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import subprocess
import os
from pathlib import Path

# Get the directory where main.py is located
BASE_DIR = Path(__file__).parent

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Configure templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Create static directory if it doesn't exist
os.makedirs(BASE_DIR / "static", exist_ok=True)
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

def clean_response_text(text: str) -> str:
    """Clean up the response text by removing debug info and formatting artifacts."""
    import re
    
    # Remove debug lines and timestamps
    text = re.sub(r'^\[DEBUG\].*$', '', text, flags=re.MULTILINE)
    
    # Remove any ANSI escape codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    
    # Remove lines with box-drawing characters
    text = re.sub(r'^[╭╰╰│╯─╮╰╯]+.*$', '', text, flags=re.MULTILINE)
    
    # Remove empty lines and trim whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)

def extract_code_blocks(text: str) -> list:
    """Extract all code blocks from the text."""
    import re
    code_blocks = []
    
    # Find all code blocks between triple backticks
    pattern = r'```(?:\w*\n)?([\s\S]*?)```'
    for match in re.finditer(pattern, text):
        code = match.group(1).strip()
        # Remove line numbers if present (e.g., "1: import os" -> "import os")
        code = re.sub(r'^\s*\d+:\s*', '', code, flags=re.MULTILINE)
        code_blocks.append(code)
    
    return code_blocks

def format_response(response_text: str) -> str:
    """Format the response to ensure clean, structured output with copy-pastable code blocks."""
    # Clean up the response text first
    cleaned_text = clean_response_text(response_text)
    
    # Extract code blocks
    code_blocks = extract_code_blocks(cleaned_text)
    
    # If we found code blocks, return them with markdown formatting
    if code_blocks:
        formatted_blocks = []
        for i, code in enumerate(code_blocks, 1):
            formatted_blocks.append(f"```python\n{code}\n```")
        return '\n\n'.join(formatted_blocks)
    
    # If no code blocks, return the cleaned text
    return cleaned_text

@app.post("/api/ask")
async def ask_question(question: str = Form(...)):
    try:
        print(f"Received question: {question}")
        result = subprocess.run(
            ["smartpaydoc", "ask", question],
            capture_output=True,
            text=True
        )
        
        # Format the response
        formatted_response = format_response(result.stdout or result.stderr or "No output from command")
        
        print(f"Formatted response: {formatted_response[:200]}...")
        return {"response": formatted_response}
    except Exception as e:
        error_msg = f"Error processing your question: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

def clean_code_output(code_text: str) -> str:
    """Clean up the code output to ensure it's properly formatted."""
    import re
    
    # Remove debug lines and timestamps
    code_text = re.sub(r'^\[DEBUG\].*$', '', code_text, flags=re.MULTILINE)
    
    # Remove any ANSI escape codes (colors, etc.)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    code_text = ansi_escape.sub('', code_text)
    
    # Remove box-drawing characters and other UI elements
    code_text = re.sub(r'^[╭╰╰│╯─╮╯]+.*$', '', code_text, flags=re.MULTILINE)
    
    # Remove line numbers if present (e.g., "1: import os" -> "import os")
    code_text = re.sub(r'^\s*\d+:\s*', '', code_text, flags=re.MULTILINE)
    
    # Remove any markdown code block formatting
    code_text = re.sub(r'^```(?:\w*\n)?|```$', '', code_text, flags=re.MULTILINE).strip()
    
    # Remove any leading/trailing whitespace from each line
    code_lines = [line.rstrip() for line in code_text.split('\n')]
    
    # Remove any empty lines at the beginning and end
    while code_lines and not code_lines[0].strip():
        code_lines.pop(0)
    while code_lines and not code_lines[-1].strip():
        code_lines.pop()
    
    # Remove any remaining UI elements
    code_lines = [line for line in code_lines 
                 if not any(c in line for c in '╭╰╯│─╮╯') 
                 and not line.startswith(('╭', '╰', '│', '╯', '─', '╮'))]
    
    return '\n'.join(code_lines)

@app.post("/api/generate")
async def generate_code(prompt: str = Form(...), language: str = Form("python"), framework: str = Form("flask")):
    try:
        print(f"Generating code for: {prompt}")
        
        result = subprocess.run(
            ["smartpaydoc", "generate", prompt, "--lang", language, "--framework", framework],
            capture_output=True,
            text=True
        )
        
        if result.stderr and not result.stdout:
            return {"error": f"Error generating code: {result.stderr}"}
        
        # Clean up the generated code
        cleaned_code = clean_code_output(result.stdout)
        
        # Return just the cleaned code without additional formatting
        # The frontend will handle the markdown formatting
        return {"code": cleaned_code}
    except Exception as e:
        error_msg = f"Error generating code: {str(e)}"
        print(error_msg)
        return {"error": error_msg}