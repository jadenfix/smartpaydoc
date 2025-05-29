from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import subprocess
import logging
import os

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
    try:
        cmd = ["python", "main.py", "ask", request.question, "--lang", request.language]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
            
        return {"response": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
async def generate_code(request: GenerateRequest):
    """Generate boilerplate code"""
    try:
        cmd = ["python", "main.py", "generate", request.task, "--lang", request.language, "--framework", request.framework]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)
            
        return {"code": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
