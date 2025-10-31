import os
import sys
from pathlib import Path
from typing import Annotated, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from models.dtos import (
    FacialAnalysisRequest,
    FacialAnalysisResponse,
    RecommendationRequest,
    RecommendationResponse,
    SkinProfileDTO,
)
from services.llm_client import llm_client
from services.recommendation_engine import recommendation_engine
from services.supabase_client import supabase_client

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Recommendation System API",
    version="1.0.0",
    description="AI-powered cosmetic product recommendation system",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment configuration (now using Supabase directly)


# Health check endpoint
@app.get("/api/health")
def health():
    """Health check endpoint"""
    supabase_connected = supabase_client.health_check()
    llm_health = llm_client.health_check()
    return {
        "ok": True,
        "service": "Recommendation System",
        "supabaseConnected": supabase_connected,
        "llmClient": llm_health,
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
            "quick_recommendations": "/api/recommendations/quick (GET)",
            "facial_analysis": "/api/facial-analysis (POST)",
        },
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
            strategy=(request.strategy or "hybrid"),
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate recommendations: {str(e)}"
        )


@app.get("/api/recommendations/quick", response_model=RecommendationResponse)
def get_quick_recommendations(
    skinType: Annotated[
        Optional[str],
        Query(description="Skin type: dry, oily, combination, sensitive, normal"),
    ] = None,
    category: Annotated[
        Optional[str], Query(description="Preferred product category")
    ] = None,
    strategy: Annotated[
        Optional[str], Query(description="content | popularity | hybrid")
    ] = "hybrid",
    limit: Annotated[
        int, Query(ge=1, le=50, description="Number of recommendations")
    ] = 10,
):
    """
    Quick recommendation endpoint using query parameters.

    Simplified interface for basic recommendations.
    """
    try:
        skin_profile = SkinProfileDTO(
            skinType=skinType, preferredCategories=[category] if category else None
        )
        response = recommendation_engine.get_recommendations(
            skin_profile=skin_profile, limit=limit, strategy=(strategy or "hybrid")
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate recommendations: {str(e)}"
        )


# Facial analysis endpoint
@app.post("/api/facial-analysis", response_model=FacialAnalysisResponse)
def analyze_facial_image(request: FacialAnalysisRequest = Body(...)):
    """
    Analyze facial image using vision model and get personalized product recommendations.

    Request body should contain:
    - imageUrl: Base64 encoded image or image URL
    - skinType: User-provided skin type (optional)
    - detectedConcerns: User-reported skin concerns (optional)
    - limit: Number of recommendations to return (1-50, default: 10)
    """
    try:
        # Use LLM to analyze the facial image
        analysis_result = llm_client.analyze_facial_image(
            image_data=request.imageUrl,
            user_skin_type=request.skinType,
            user_concerns=request.detectedConcerns,
        )

        if not analysis_result:
            # Fallback if LLM is not available
            analysis_result = {
                "skinType": request.skinType or "normal",
                "concerns": request.detectedConcerns or [],
                "analysis": f"AI analysis not available. Using provided skin type: {request.skinType or 'normal'}",
            }

        # Build skin profile from analysis results
        skin_profile = SkinProfileDTO(
            skinType=analysis_result["skinType"],
            concerns=analysis_result["concerns"],
            preferredCategories=None,
            budgetRange=None,
            excludeProducts=None,
        )

        # Get product recommendations based on analysis
        recommendations = recommendation_engine.get_recommendations(
            skin_profile=skin_profile, limit=request.limit or 10, strategy="hybrid"
        )

        # Return combined result
        return FacialAnalysisResponse(
            skinType=analysis_result["skinType"],
            detectedConcerns=analysis_result["concerns"],
            analysisResult=analysis_result["analysis"],
            recommendations=recommendations,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze facial image: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
