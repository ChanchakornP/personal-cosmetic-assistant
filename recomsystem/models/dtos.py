from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

# Product DTO (matching Product service structure)
class ProductDTO(BaseModel):
    """Product information from Product service"""
    id: int
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    category: Optional[str] = None
    mainImageUrl: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# User Profile DTOs
class SkinProfileDTO(BaseModel):
    """User skin profile for recommendations"""
    skinType: Optional[str] = Field(
        None, 
        description="Skin type: dry, oily, combination, sensitive, normal"
    )
    concerns: Optional[List[str]] = Field(
        default_factory=list,
        description="Skin concerns: acne, aging, darkSpots, dryness, oiliness, sensitivity"
    )
    preferredCategories: Optional[List[str]] = Field(
        default_factory=list,
        description="Preferred product categories"
    )
    budgetRange: Optional[dict] = Field(
        None,
        description="Budget range with min and max price"
    )
    excludeProducts: Optional[List[int]] = Field(
        default_factory=list,
        description="Product IDs to exclude from recommendations"
    )

class RecommendationRequest(BaseModel):
    """Request for product recommendations"""
    skinProfile: SkinProfileDTO
    limit: Optional[int] = Field(default=10, ge=1, le=50)
    strategy: Optional[str] = Field(
        default="hybrid",
        description="Recommendation strategy: content | popularity | hybrid"
    )

class RecommendationResponse(BaseModel):
    """Response containing recommended products"""
    products: List[ProductDTO]
    count: int
    reasons: Optional[dict] = Field(
        None,
        description="Explanation for each recommendation (product_id -> reasons)"
    )

