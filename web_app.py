from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import subprocess
import logging
import os
import sys
import importlib.util

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Import the main module to access its functions
try:
    main_module = import_from_path('main', 'main.py')
    rag = main_module.rag
    codegen = main_module.codegen
    error_helper = main_module.error_helper
except Exception as e:
    logger.error(f"Failed to import main module: {e}")
    rag = None
    codegen = None
    error_helper = None

app = FastAPI(title="SmartPayDoc API",
             description="Web interface for SmartPayDoc - Stripe API Documentation Assistant",
             version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str
    language: str = "python"

class GenerateRequest(BaseModel):
    task: str
    language: str = "python"
    framework: str = "flask"

class DebugRequest(BaseModel):
    error_log: str
    context: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/ask")
async def ask_question(request: AskRequest):
    """Ask a question about Stripe API"""
    if not rag:
        raise HTTPException(status_code=500, detail="RAG engine not initialized")
    
    try:
        # Call the RAG engine directly instead of using subprocess
        import asyncio
        from rag_engine import StripeRAGEngine  # Import the RAG engine directly
        
        # Create a new instance of the RAG engine
        rag_engine = StripeRAGEngine()
        await rag_engine.initialize()  # Make sure to await the async initialize
        
        # Call the query method directly
        response = await rag_engine.query(request.question, request.language)
        
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in ask_question: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing your question: {str(e)}")



@app.post("/api/generate")
async def generate_code(request: GenerateRequest):
    """Generate boilerplate code"""
    if not codegen:
        raise HTTPException(status_code=500, detail="Code generator not initialized")
    
    try:
        import asyncio
        from codegen import StripeCodeGenerator  # Import the code generator directly
        
        # Create a new instance of the code generator
        code_generator = StripeCodeGenerator()
        
        # Call the generate_code method directly
        code = await code_generator.generate_code(request.task, request.language, request.framework)
        
        if not code:
            raise HTTPException(status_code=500, detail="No code was generated")
            
        return {"code": code}
    except Exception as e:
        logger.error(f"Error in generate_code: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating code: {str(e)}")


@app.post("/api/debug")
async def debug_error(request: DebugRequest):
    """Debug Stripe errors"""
    try:
        cmd = ["python", "main.py", "debug", request.error_log]
        if request.context:
            cmd.extend(["--context", request.context])
            
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
            
        return {"analysis": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
