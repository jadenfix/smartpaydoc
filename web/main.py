from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to Python path
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR.parent))

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Ensure static directory exists
os.makedirs(BASE_DIR / "static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Add url_for to templates
templates.env.globals['url_for'] = app.url_path_for
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
    """Format the response to ensure natural language output with proper formatting."""
    # Clean up the response text first
    cleaned_text = clean_response_text(response_text)
    
    # Remove any markdown code block formatting
    cleaned_text = cleaned_text.replace('```python', '').replace('```', '').strip()
    
    # Ensure the response is in natural language format
    if '```' in cleaned_text:
        # If there are still code blocks, format them as inline code
        cleaned_text = cleaned_text.replace('`', '`')
    
    # Ensure proper paragraph spacing
    cleaned_text = '\n\n'.join(p.strip() for p in cleaned_text.split('\n\n') if p.strip())
    
    return cleaned_text

# Import RAG engine with error handling
try:
    from rag_engine import StripeRAGEngine
    RAG_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import RAG engine: {e}")
    RAG_AVAILABLE = False

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=str(BASE_DIR.parent / '.env'))

# Initialize RAG
rag = None

# Check for required environment variables
required_env_vars = ["ANTHROPIC_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars and RAG_AVAILABLE:
    logger.warning(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.warning("RAG functionality will be disabled")
    RAG_AVAILABLE = False

# Initialize RAG engine on startup
@app.on_event("startup")
async def startup_event():
    global rag
    
    if not RAG_AVAILABLE:
        logger.warning("Skipping RAG engine initialization - not available")
        return
        
    try:
        logger.info("Initializing RAG engine...")
        rag = StripeRAGEngine()
        logger.info("RAG engine instance created, initializing...")
        await rag.initialize()
        logger.info(f"✅ RAG engine initialized successfully with {len(rag.documents)} documents")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG engine: {e}", exc_info=True)
        rag = None

@app.post("/api/ask")
async def ask_question(question: str = Form(...)):
    if not RAG_AVAILABLE or not rag:
        error_msg = "RAG functionality is currently unavailable. Please check server logs for details."
        logger.error(error_msg)
        return JSONResponse(
            status_code=503,
            content={"error": error_msg}
        )
    
    if not question or not question.strip():
        return JSONResponse(
            status_code=400,
            content={"error": "Question cannot be empty"}
        )
    
    try:
        logger.info(f"Processing question: {question[:100]}...")
        
        # Get response from RAG
        response = await rag.ask(question)
        
        if not response:
            error_msg = "No response from RAG engine. Please try again."
            logger.error(error_msg)
            return JSONResponse(
                status_code=500,
                content={"error": error_msg}
            )
        
        # Format the response
        formatted_response = format_response(response)
        logger.info("Successfully processed question")
        
        return {"response": formatted_response}
        
    except Exception as e:
        error_msg = f"Error processing your question: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": error_msg}
        )

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