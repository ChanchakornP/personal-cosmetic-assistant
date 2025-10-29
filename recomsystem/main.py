import os
import sys
from pathlib import Path
from typing import Optional, Annotated

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from services.product_client import product_client
from services.llm_client import llm_client
from services.recommendation_engine import recommendation_engine
from models.dtos import (
    RecommendationRequest,
    RecommendationResponse,
    SkinProfileDTO
)

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
    llm_health = llm_client.health_check()
    return {
        "ok": True,
        "service": "Recommendation System",
        "productApiUrl": PRODUCT_API_URL,
        "productApiConnected": product_api_connected,
        "llmClient": llm_health
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

# Recommendation endpoints
@app.post("/api/recommendations", response_model=RecommendationResponse)
def get_recommendations(request: RecommendationRequest = Body(...)):
    """
    Get personalized product recommendations based on user skin profile.
    
    Request body should contain:
    - skinProfile: User's skin profile (skinType, concerns, preferredCategories, budgetRange, excludeProducts)
    - limit: Number of recommendations to return (1-50, default: 10)
    """
    try:
        response = recommendation_engine.get_recommendations(
            skin_profile=request.skinProfile,
            limit=request.limit or 10,
            strategy=(request.strategy or "hybrid")
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}"
        )

@app.get("/api/recommendations/quick", response_model=RecommendationResponse)
def get_quick_recommendations(
    skinType: Annotated[Optional[str], Query(description="Skin type: dry, oily, combination, sensitive, normal")] = None,
    category: Annotated[Optional[str], Query(description="Preferred product category")] = None,
    strategy: Annotated[Optional[str], Query(description="content | popularity | hybrid")] = "hybrid",
    limit: Annotated[int, Query(ge=1, le=50, description="Number of recommendations")] = 10
):
    """
    Quick recommendation endpoint using query parameters.
    
    Simplified interface for basic recommendations.
    """
    try:
        skin_profile = SkinProfileDTO(
            skinType=skinType,
            preferredCategories=[category] if category else None
        )
        response = recommendation_engine.get_recommendations(
            skin_profile=skin_profile,
            limit=limit,
            strategy=(strategy or "hybrid")
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendations: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

