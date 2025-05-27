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

# Configure templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Create static directory if it doesn't exist
os.makedirs(BASE_DIR / "static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates.env.globals['url_for'] = lambda name, **params: f"/static/{params['filename']}" if name == 'static' else app.url_path_for(name, **params)
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

from rag_engine import StripeRAGEngine
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize RAG
rag = None

# Initialize RAG engine on startup
@app.on_event("startup")
async def startup_event():
    global rag
    try:
        print("[DEBUG] Initializing RAG engine...")
        rag = StripeRAGEngine()
        print("[DEBUG] RAG engine instance created, initializing...")
        await rag.initialize()
        print("✅ RAG engine initialized successfully")
        print(f"[DEBUG] RAG engine has {len(rag.documents)} documents loaded")
    except Exception as e:
        print(f"❌ Failed to initialize RAG engine: {e}")
        import traceback
        traceback.print_exc()
        rag = None

@app.post("/api/ask")
async def ask_question(question: str = Form(...)):
    try:
        if not rag:
            error_msg = "RAG engine not initialized. Please try again in a moment."
            print(f"[ERROR] {error_msg}")
            return {"error": error_msg}
            
        print(f"[DEBUG] Received question: {question}")
        
        # Get response from RAG
        print("[DEBUG] Calling rag.ask()...")
        response = await rag.ask(question)
        print(f"[DEBUG] Got response from rag.ask(): {response[:200] if response else 'None'}")
        
        if not response:
            error_msg = "Received empty response from RAG engine"
            print(f"[ERROR] {error_msg}")
            return {"error": error_msg}
        
        # Format the response
        print("[DEBUG] Formatting response...")
        formatted_response = format_response(response)
        print(f"[DEBUG] Formatted response: {formatted_response[:200]}...")
        
        return {"response": formatted_response}
        
    except Exception as e:
        import traceback
        error_msg = f"Error processing your question: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
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
    print("\n[DEBUG] ====== Starting code generation ======")
    print(f"[DEBUG] Prompt: {prompt}")
    print(f"[DEBUG] Language: {language}")
    print(f"[DEBUG] Framework: {framework}")
    
    try:
        print("[DEBUG] Importing StripeCodeGenerator...")
        from codegen import StripeCodeGenerator
        
        print("[DEBUG] Initializing code generator...")
        code_generator = StripeCodeGenerator()
        
        print("[DEBUG] Generating code...")
        code = await code_generator.generate_code(
            task=prompt,  # Changed from prompt=prompt to task=prompt
            language=language,
            framework=framework
        )
        print(f"[DEBUG] Raw generated code: {code[:200]}..." if code else "[DEBUG] No code generated")
        
        # Clean up the generated code
        cleaned_code = clean_code_output(code or "")
        print(f"[DEBUG] Cleaned code: {cleaned_code[:200]}..." if cleaned_code else "[DEBUG] No cleaned code")
        
        if not cleaned_code:
            raise ValueError("No code was generated")
            
        return {"code": cleaned_code}
        
    except Exception as e:
        import traceback
        error_msg = f"Error generating code: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[DEBUG] Traceback: {traceback.format_exc()}")
        return {"error": error_msg}
    finally:
        print("[DEBUG] ====== End of code generation ======\n")