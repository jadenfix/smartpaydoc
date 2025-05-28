import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    # Add the project root to the Python path
    project_root = str(Path(__file__).parent.parent)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    logger.info(f"Python path: {sys.path}")
    
    # Ensure required environment variables are set
    required_env_vars = ['ANTHROPIC_API_KEY']
    for var in required_env_vars:
        if not os.getenv(var):
            logger.error(f"Missing required environment variable: {var}")
    
    # Import the FastAPI app after updating the path
    logger.info("Importing FastAPI application...")
    from web.main import app
    
    logger.info("FastAPI application imported successfully")
    
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
