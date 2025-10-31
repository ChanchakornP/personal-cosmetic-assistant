"""
Recommendation engine service that orchestrates recommendation algorithms.
"""

from typing import List, Dict, Optional
from models.dtos import ProductDTO, SkinProfileDTO, RecommendationResponse
from services.supabase_client import supabase_client
from services.llm_client import llm_client
from algorithms.content_based import rank_products as content_rank, generate_recommendation_reasons
from algorithms.popularity import rank_products as popularity_rank
from algorithms.hybrid import rank_products as hybrid_rank


class RecommendationEngine:
    """Main recommendation engine that coordinates recommendation algorithms"""
    
    def __init__(self):
        # Use Supabase client for direct database access
        self.product_client = supabase_client
        # LLM client connection is established at initialization
        self.llm_client = llm_client
    
    def get_recommendations(
        self,
        skin_profile: SkinProfileDTO,
        limit: int = 10,
        strategy: str = "hybrid"
    ) -> RecommendationResponse:
        """
        Get personalized product recommendations.
        
        Args:
            skin_profile: User's skin profile with preferences
            limit: Maximum number of recommendations to return
            
        Returns:
            RecommendationResponse with recommended products and reasons
        """
        # Fetch products from Product API
        all_products = self._fetch_products(skin_profile)
        
        # Filter out excluded products
        if skin_profile.excludeProducts:
            all_products = [
                p for p in all_products
                if p.id not in skin_profile.excludeProducts
            ]
        
        if not all_products:
            return RecommendationResponse(
                products=[],
                count=0,
                reasons={}
            )
        
        # Rank products using selected strategy
        strategy = (strategy or "hybrid").lower()
        if strategy == "content":
            ranked_products = content_rank(all_products, skin_profile)
        elif strategy == "popularity":
            ranked_products = popularity_rank(all_products)
        else:
            ranked_products = hybrid_rank(all_products, skin_profile)
        
        # Get top N products
        top_products = [product for product, _ in ranked_products[:limit]]
        
        # Generate reasons for each recommendation
        reasons = {}
        for product in top_products:
            score = next(score for p, score in ranked_products if p.id == product.id)
            
            # Try LLM-generated explanation first (uses product data from database)
            if self.llm_client.is_available():
                llm_explanation = self._generate_llm_explanation(product, skin_profile)
                if llm_explanation:
                    reasons[str(product.id)] = [llm_explanation]
                else:
                    # Fallback to rule-based reasons if LLM fails
                    product_reasons = generate_recommendation_reasons(product, skin_profile, score)
                    reasons[str(product.id)] = product_reasons
            else:
                # Use rule-based reasons if LLM not available
                product_reasons = generate_recommendation_reasons(product, skin_profile, score)
                reasons[str(product.id)] = product_reasons
        
        return RecommendationResponse(
            products=top_products,
            count=len(top_products),
            reasons=reasons
        )
    
    def _fetch_products(self, skin_profile: SkinProfileDTO) -> List[ProductDTO]:
        """
        Fetch products from Supabase database based on profile preferences.
        
        Args:
            skin_profile: User's skin profile
            
        Returns:
            List of products
        """
        # If preferred categories specified, fetch from those categories
        if skin_profile.preferredCategories:
            all_products = []
            seen_ids = set()
            
            # Fetch from each preferred category
            for category in skin_profile.preferredCategories:
                try:
                    category_products = self.product_client.get_all_products(
                        category=category,
                        limit=50
                    )
                    # Deduplicate products
                    for product in category_products:
                        if product.id not in seen_ids:
                            all_products.append(product)
                            seen_ids.add(product.id)
                except Exception:
                    # If category fetch fails, continue with others
                    continue
            
            # Also fetch some products from all categories as backup
            if all_products:
                try:
                    additional_products = self.product_client.get_all_products(limit=100)
                    for product in additional_products:
                        if product.id not in seen_ids:
                            all_products.append(product)
                            seen_ids.add(product.id)
                except Exception:
                    pass
            
            return all_products if all_products else self.product_client.get_all_products(limit=200)
        else:
            # No category preference, fetch all products
            try:
                return self.product_client.get_all_products(limit=200)
            except Exception:
                return []
    
    def _generate_llm_explanation(
        self,
        product: ProductDTO,
        skin_profile: SkinProfileDTO
    ) -> Optional[str]:
        """
        Generate LLM-powered explanation for a product recommendation.
        Uses product data directly from Supabase database.
        
        Args:
            product: Product from Supabase database
            skin_profile: User's skin profile
            
        Returns:
            LLM-generated explanation or None if generation fails
        """
        # Build skin profile summary
        profile_parts = []
        if skin_profile.skinType:
            profile_parts.append(f"Skin type: {skin_profile.skinType}")
        if skin_profile.concerns:
            profile_parts.append(f"Concerns: {', '.join(skin_profile.concerns)}")
        if skin_profile.budgetRange:
            min_price = skin_profile.budgetRange.get("min", 0)
            max_price = skin_profile.budgetRange.get("max", float('inf'))
            profile_parts.append(f"Budget: ${min_price:.2f} - ${max_price:.2f}")
        
        skin_profile_summary = "; ".join(profile_parts) if profile_parts else "No specific preferences"
        
        # Get product description from database (use description or name if description is empty)
        product_description = product.description or product.name
        
        # Generate explanation using LLM with product data from database
        return self.llm_client.generate_recommendation_explanation(
            product_name=product.name,
            product_description=product_description,
            skin_profile_summary=skin_profile_summary
        )


# Global instance
recommendation_engine = RecommendationEngine()

