import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from services.product_client import product_client

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Recommendation System API",
    version="1.0.0",
    description="AI-powered cosmetic product recommendation system"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment configuration
PRODUCT_API_URL = os.getenv("PRODUCT_API_URL", "http://localhost:8000")

# Health check endpoint
@app.get("/api/health")
def health():
    """Health check endpoint"""
    product_api_connected = product_client.health_check()
    return {
        "ok": True,
        "service": "Recommendation System",
        "productApiUrl": PRODUCT_API_URL,
        "productApiConnected": product_api_connected
    }

# Root endpoint
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Recommendation System API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "recommendations": "/api/recommendations (POST)",
            "quick_recommendations": "/api/recommendations/quick (GET)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

