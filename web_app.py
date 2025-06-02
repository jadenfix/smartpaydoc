from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import os
import sys
import asyncio
import importlib.util
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Global instances
rag = None
codegen = None
error_helper = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize components
    global rag, codegen, error_helper
    
    try:
        # Import modules
        main_module = import_from_path('main', 'main.py')
        rag = main_module.rag
        codegen = main_module.codegen
        error_helper = main_module.error_helper
        
        # Initialize RAG if available
        if hasattr(rag, 'initialize'):
            logger.info("Initializing RAG engine...")
            await rag.initialize()
            logger.info("RAG engine initialized successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}", exc_info=True)
        rag = None
        codegen = None
        error_helper = None
    
    yield  # This is where the application runs
    
    # Cleanup (if needed)
    logger.info("Shutting down...")

# Create FastAPI app with lifespan
app = FastAPI(
    title="SmartPayDoc API",
    description="Web interface for SmartPayDoc - Stripe API Documentation Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS with specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Content-Type"],
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

from fastapi import FastAPI, HTTPException, Request, Depends, Body

@app.post("/api/ask")
async def ask_question(request_data: dict = Body(...)):
    """Ask a question about Stripe API"""
    if not rag:
        raise HTTPException(
            status_code=503, 
            detail="RAG engine not initialized. Please try again in a moment."
        )
    
    try:
        question = request_data.get('question', '').strip()
        language = request_data.get('language', 'python')
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Use the global rag instance that was initialized at startup
        response = await rag.ask(question, language)
        
        # Return as plain text with proper content type
        from fastapi.responses import PlainTextResponse
        response_obj = PlainTextResponse(
            content=response,
            media_type="text/plain; charset=utf-8"
        )
        
        # Add CORS headers
        response_obj.headers["Access-Control-Allow-Origin"] = "*"
        response_obj.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response_obj.headers["Access-Control-Allow-Headers"] = "Content-Type"
        
        return response_obj
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ask_question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing your question: {str(e)}"
        )



@app.post("/api/generate")
async def generate_code(request: GenerateRequest):
    """Generate boilerplate code"""
    if not codegen:
        raise HTTPException(
            status_code=503, 
            detail="Code generator not initialized. Please try again in a moment."
        )
    
    try:
        # Use the global codegen instance that was initialized at startup
        code = await codegen.generate_code(
            request.task, 
            request.language, 
            request.framework
        )
        
        if not code:
            raise HTTPException(
                status_code=500, 
                detail="No code was generated. Please try a different query."
            )
        
        # Format the response with Markdown code blocks for better readability
        formatted_response = f"""
Here's your generated code for: {request.task}

```{request.language}
{code}
```

You can copy this code and use it in your project. Make sure to:
1. Replace any placeholder values (like API keys)
2. Add your error handling logic
3. Test thoroughly before deploying to production

Need help with something else? Just ask! 😊"""
            
        # Return as plain text with proper content type
        from fastapi.responses import Response
        return Response(
            content=formatted_response,
            media_type="text/plain; charset=utf-8"
        )
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
        
    except Exception as e:
        logger.error(f"Error in generate_code: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating code: {str(e)}"
        )


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
