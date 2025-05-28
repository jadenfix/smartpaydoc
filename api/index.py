import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Add the project root to the Python path
    project_root = str(Path(__file__).parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    logger.info(f"Python path: {sys.path}")
    
    # Import the FastAPI app after updating the path
    from web.main import app
    
    # Vercel requires a callable named 'app' for Python serverless functions
    app = app
    logger.info("FastAPI app imported successfully")
    
except Exception as e:
    logger.error(f"Error initializing application: {str(e)}", exc_info=True)
    raise

# For local testing
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server...")
    uvicorn.run("api.index:app", host="0.0.0.0", port=8000, reload=True)
