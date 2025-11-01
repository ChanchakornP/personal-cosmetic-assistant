"""
Recommendation engine service that orchestrates recommendation algorithms and LangChain agents.
Enhanced with chain-of-thought thinking.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from algorithms.content_based import generate_recommendation_reasons
from algorithms.content_based import rank_products as content_rank
from algorithms.hybrid import rank_products as hybrid_rank
from algorithms.popularity import rank_products as popularity_rank
from models.dtos import ProductDTO, RecommendationResponse, SkinProfileDTO
from services.llm_service import llm_service
from services.supabase_client import supabase_client


class RecommendationEngine:
    """Main recommendation engine that coordinates recommendation algorithms and LangChain agents"""

    def __init__(self):
        # Use Supabase client for direct database access
        self.product_client = supabase_client
        # LLM service connection is established at initialization
        self.llm_service = llm_service

    def get_recommendations(
        self, skin_profile: SkinProfileDTO, limit: int = 10, strategy: str = "hybrid"
    ) -> RecommendationResponse:
        """
        Get personalized product recommendations.
        Uses traditional algorithms for ranking and LangChain agents for explanations.
        Now includes chain-of-thought reasoning in explanations.

        Args:
            skin_profile: User's skin profile with preferences
            limit: Maximum number of recommendations to return
            strategy: Recommendation strategy (content, popularity, or hybrid)

        Returns:
            RecommendationResponse with recommended products and reasons
        """
        # Fetch products from Supabase
        all_products = self._fetch_products(skin_profile)
        print(f"DEBUG: Fetched {len(all_products)} products from database")

        # Filter out excluded products
        if skin_profile.excludeProducts:
            all_products = [
                p for p in all_products if p.id not in skin_profile.excludeProducts
            ]
            print(f"DEBUG: After excluding products: {len(all_products)} products")

        if not all_products:
            print("DEBUG: No products available after fetching")
            return RecommendationResponse(products=[], count=0, reasons={})

        # Step 1: Filter by skin type using heuristic rules (combination, dry, normal, oily, sensitive)
        if skin_profile.skinType:
            print(f"DEBUG: Filtering by skin type: {skin_profile.skinType}")
            all_products = self._filter_by_skin_type(
                all_products, skin_profile.skinType
            )
            print(f"DEBUG: After skin type filter: {len(all_products)} products")
            if not all_products:
                print("DEBUG: No products match the skin type filter")
                return RecommendationResponse(products=[], count=0, reasons={})

        # Step 2: Filter by price range (if budgetRange specified)
        if skin_profile.budgetRange:
            print(f"DEBUG: Filtering by price range: {skin_profile.budgetRange}")
            all_products = self._filter_by_price(all_products, skin_profile.budgetRange)
            print(f"DEBUG: After price filter: {len(all_products)} products")
            if not all_products:
                print("DEBUG: No products match the price filter")
                return RecommendationResponse(products=[], count=0, reasons={})

        # Step 3: Use LLM to select top products based on ingredients
        # Build skin profile summary for LLM
        skin_profile_summary = self._build_skin_profile_summary(skin_profile)

        if self.llm_service.is_available():
            # Convert ProductDTO objects to dict format for LLM (only name and ingredients)
            products_for_llm = [
                {
                    "id": product.id,
                    "name": product.name,
                    "ingredients": product.ingredients or "Not specified",
                }
                for product in all_products
            ]

            print(
                f"DEBUG: Sending {len(products_for_llm)} products to LLM for selection"
            )

            # Ask LLM to select top products (maximum 5, but can be fewer or none)
            # Always cap at 5 as per requirement, even if limit is higher
            llm_selection = self.llm_service.select_top_products(
                products=products_for_llm,
                skin_profile_summary=skin_profile_summary,
                max_products=min(limit, 5),
            )

            if llm_selection and llm_selection.get("selectedProductIds"):
                selected_ids = llm_selection["selectedProductIds"]
                print(
                    f"DEBUG: LLM selected {len(selected_ids)} products: {selected_ids}"
                )

                # Map selected product IDs back to ProductDTO objects
                selected_ids_set = set(selected_ids)
                selected_products = [
                    product
                    for product in all_products
                    if product.id in selected_ids_set
                ]

                print(f"DEBUG: Mapped {len(selected_products)} products from selection")

                # Get reasons from LLM response
                llm_reasons = llm_selection.get("reasons", {})

                # Convert reasons format to match expected format (list of strings)
                reasons = {
                    str(product.id): [
                        llm_reasons.get(
                            str(product.id), "Selected as a good match for your profile"
                        )
                    ]
                    for product in selected_products
                }

                return RecommendationResponse(
                    products=selected_products,
                    count=len(selected_products),
                    reasons=reasons,
                )
            else:
                # LLM returned no products or selection failed - fall back to algorithm-based ranking
                print(
                    "DEBUG: LLM selection returned empty, falling back to algorithm-based ranking"
                )
                strategy = (strategy or "hybrid").lower()
                if strategy == "content":
                    ranked_products = content_rank(all_products, skin_profile)
                elif strategy == "popularity":
                    ranked_products = popularity_rank(all_products)
                else:
                    ranked_products = hybrid_rank(all_products, skin_profile)

                # Get top N products
                top_products = [product for product, _ in ranked_products[:limit]]

                # Generate reasons for each recommendation using rule-based approach
                reasons = {}
                for product in top_products:
                    score = next(
                        score for p, score in ranked_products if p.id == product.id
                    )
                    product_reasons = generate_recommendation_reasons(
                        product, skin_profile, score
                    )
                    reasons[str(product.id)] = product_reasons

                return RecommendationResponse(
                    products=top_products, count=len(top_products), reasons=reasons
                )
        else:
            # LLM not available, fall back to traditional algorithm-based ranking
            strategy = (strategy or "hybrid").lower()
            if strategy == "content":
                ranked_products = content_rank(all_products, skin_profile)
            elif strategy == "popularity":
                ranked_products = popularity_rank(all_products)
            else:
                ranked_products = hybrid_rank(all_products, skin_profile)

            # Get top N products
            top_products = [product for product, _ in ranked_products[:limit]]

            # Generate reasons for each recommendation using rule-based approach
            reasons = {}
            for product in top_products:
                score = next(
                    score for p, score in ranked_products if p.id == product.id
                )
                product_reasons = generate_recommendation_reasons(
                    product, skin_profile, score
                )
                reasons[str(product.id)] = product_reasons

            return RecommendationResponse(
                products=top_products, count=len(top_products), reasons=reasons
            )

    def _fetch_products(self, skin_profile: SkinProfileDTO) -> List[ProductDTO]:
        """
        Fetch products from Supabase database based on profile preferences.
        Note: Price filtering is NOT done here - it's done in step 2 after skin type filtering.

        Args:
            skin_profile: User's skin profile

        Returns:
            List of products (not filtered by price)
        """
        # If preferred categories specified, fetch from those categories
        if skin_profile.preferredCategories:
            all_products = []
            seen_ids = set()

            # Fetch from each preferred category (without price filtering)
            for category in skin_profile.preferredCategories:
                try:
                    category_products = self.product_client.get_all_products(
                        category=category,
                        limit=50,
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
                    additional_products = self.product_client.get_all_products(
                        limit=100,
                    )
                    for product in additional_products:
                        if product.id not in seen_ids:
                            all_products.append(product)
                            seen_ids.add(product.id)
                except Exception:
                    pass

            return (
                all_products
                if all_products
                else self.product_client.get_all_products(limit=200)
            )
        else:
            # No category preference, fetch all products (without price filtering)
            try:
                return self.product_client.get_all_products(limit=200)
            except Exception:
                return []

    def _filter_by_skin_type(
        self, products: List[ProductDTO], skin_type: str
    ) -> List[ProductDTO]:
        """
        Filter products by skin type using heuristic rules.
        Uses boolean fields in product (combination, dry, normal, oily, sensitive).

        Args:
            products: List of products to filter
            skin_type: User's skin type (combination, dry, normal, oily, sensitive)

        Returns:
            Filtered list of products that match the skin type
        """
        skin_type_lower = skin_type.lower()
        filtered_products = []

        # Debug: Check first few products' skin type values
        if products:
            sample_product = products[0]
            print(
                f"DEBUG: Sample product skin type values - normal: {sample_product.normal}, dry: {sample_product.dry}, "
                f"oily: {sample_product.oily}, combination: {sample_product.combination}, sensitive: {sample_product.sensitive}"
            )
            print(
                f"DEBUG: Sample product normal type: {type(sample_product.normal)}, value: {repr(sample_product.normal)}"
            )

        for product in products:
            # Check if product has the corresponding skin type field set to True
            # Use truthy check to handle True, 1, "true", etc.
            match = False
            if skin_type_lower == "combination":
                match = (
                    bool(product.combination)
                    if product.combination is not None
                    else False
                )
            elif skin_type_lower == "dry":
                match = bool(product.dry) if product.dry is not None else False
            elif skin_type_lower == "normal":
                match = bool(product.normal) if product.normal is not None else False
            elif skin_type_lower == "oily":
                match = bool(product.oily) if product.oily is not None else False
            elif skin_type_lower == "sensitive":
                match = (
                    bool(product.sensitive) if product.sensitive is not None else False
                )

            if match:
                filtered_products.append(product)

        print(
            f"DEBUG: Filtered {len(filtered_products)} out of {len(products)} products for skin type '{skin_type_lower}'"
        )
        return filtered_products

    def _filter_by_price(
        self, products: List[ProductDTO], budget_range: Dict[str, Optional[float]]
    ) -> List[ProductDTO]:
        """
        Filter products by price range.

        Args:
            products: List of products to filter
            budget_range: Dictionary with 'min' and/or 'max' price

        Returns:
            Filtered list of products within the price range
        """
        min_price = budget_range.get("min")
        max_price = budget_range.get("max")

        filtered_products = []
        for product in products:
            # If only min_price specified, product must be >= min_price
            if min_price is not None and max_price is None:
                if product.price >= min_price:
                    filtered_products.append(product)
            # If only max_price specified, product must be <= max_price
            elif min_price is None and max_price is not None:
                if product.price <= max_price:
                    filtered_products.append(product)
            # If both specified, product must be in range
            elif min_price is not None and max_price is not None:
                if min_price <= product.price <= max_price:
                    filtered_products.append(product)
            # If neither specified, include all products
            else:
                filtered_products.append(product)

        return filtered_products

    def _build_skin_profile_summary(self, skin_profile: SkinProfileDTO) -> str:
        """
        Build a summary string of the user's skin profile.

        Args:
            skin_profile: User's skin profile

        Returns:
            Summary string of the skin profile
        """
        profile_parts = []
        if skin_profile.skinType:
            profile_parts.append(f"Skin type: {skin_profile.skinType}")
        if skin_profile.concerns:
            profile_parts.append(f"Concerns: {', '.join(skin_profile.concerns)}")
        if skin_profile.budgetRange:
            min_price = skin_profile.budgetRange.get("min", 0)
            max_price = skin_profile.budgetRange.get("max", float("inf"))
            profile_parts.append(f"Budget: ${min_price:.2f} - ${max_price:.2f}")

        return "; ".join(profile_parts) if profile_parts else "No specific preferences"


# Global instance
recommendation_engine = RecommendationEngine()
