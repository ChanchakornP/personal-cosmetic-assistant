import os
import sys
from pathlib import Path
from typing import Annotated, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from models.dtos import (
    FacialAnalysisRequest,
    FacialAnalysisResponse,
    IngredientConflictRequest,
    IngredientConflictResponse,
    RecommendationRequest,
    RecommendationResponse,
    SkinProfileDTO,
)
from services.llm_service import llm_service
from services.recommendation_engine import recommendation_engine
from services.supabase_client import supabase_client

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="PCA AgenticAI System API",
    version="2.0.0",
    description="LangChain-powered agentic AI system for cosmetic product recommendations",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/api/health")
def health():
    """Health check endpoint"""
    supabase_connected = supabase_client.health_check()
    llm_health = llm_service.health_check()
    return {
        "ok": True,
        "service": "PCA AgenticAI System",
        "version": "2.0.0",
        "framework": "LangChain",
        "supabaseConnected": supabase_connected,
        "llmClient": llm_health,
    }


# Root endpoint
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "PCA AgenticAI System API",
        "version": "2.0.0",
        "framework": "LangChain",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "recommendations": "/api/recommendations (POST)",
            "quick_recommendations": "/api/recommendations/quick (GET)",
            "facial_analysis": "/api/facial-analysis (POST)",
            "ingredient_conflict": "/api/ingredient-conflict (POST)",
        },
    }


# Recommendation endpoints
@app.post("/api/recommendations", response_model=RecommendationResponse)
def get_recommendations(request: RecommendationRequest = Body(...)):
    """
    Get personalized product recommendations based on user skin profile.
    Uses LangChain-powered recommendation engine with agentic AI capabilities.

    Request body should contain:
    - skinProfile: User's skin profile (skinType, concerns, preferredCategories, budgetRange, excludeProducts)
    - limit: Number of recommendations to return (1-50, default: 10)
    - strategy: Recommendation strategy (content | popularity | hybrid)
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
    Simplified interface for basic recommendations using LangChain agents.
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
    Analyze facial image using LangChain vision model and get personalized product recommendations.

    Request body should contain:
    - imageUrl: Base64 encoded image or image URL
    - skinType: User-provided skin type (optional)
    - detectedConcerns: User-reported skin concerns (optional)
    - budgetRange: Budget range with min/max price (optional, e.g., {"min": 0, "max": 50})
    - limit: Number of recommendations to return (1-50, default: 10)
    """
    try:
        # Use LangChain LLM service to analyze the facial image
        analysis_result = llm_service.analyze_facial_image(
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
            budgetRange=request.budgetRange,
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


# Ingredient conflict analysis endpoint
@app.post("/api/ingredient-conflict", response_model=IngredientConflictResponse)
def analyze_ingredient_conflicts(request: IngredientConflictRequest = Body(...)):
    """
    Analyze ingredient conflicts between multiple cosmetic products using LangChain agentic AI.

    Request body should contain:
    - products: List of product dictionaries with id, name, and ingredients
    """
    try:
        if not request.products or len(request.products) < 2:
            raise HTTPException(
                status_code=400, detail="Please provide at least 2 products to analyze"
            )

        # Check if LLM service is available
        if not llm_service.is_available():
            import os

            gemini_key = os.getenv("GEMINI_API_KEY")

            if not gemini_key:
                error_msg = (
                    "LLM service is not available: GEMINI_API_KEY environment variable is not set. "
                    "Please add GEMINI_API_KEY to your .env file in the PCA-agenticAI directory. "
                    "Get your API key from: https://makersuite.google.com/app/apikey"
                )
            else:
                error_msg = (
                    "LLM service is not available: Failed to initialize LangChain LLM service. "
                    "Please check: "
                    "1. GEMINI_API_KEY is valid "
                    "2. langchain-google-genai package is installed (pip install langchain-google-genai langchain-core) "
                    "3. Check server logs for initialization errors"
                )

            raise HTTPException(status_code=503, detail=error_msg)

        # Use LangChain LLM service to analyze ingredient conflicts
        analysis_result = llm_service.analyze_ingredient_conflicts(request.products)

        if not analysis_result:
            # If LLM analysis failed (e.g., empty response), provide helpful error
            raise HTTPException(
                status_code=503,
                detail="LLM analysis failed. The AI service returned no results. Please check your GEMINI_API_KEY configuration and try again.",
            )

        return IngredientConflictResponse(**analysis_result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze ingredient conflicts: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
