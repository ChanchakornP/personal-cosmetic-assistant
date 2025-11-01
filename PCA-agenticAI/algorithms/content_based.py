"""
Content-based recommendation algorithm for cosmetic products.

Uses rule-based scoring to match user profile with product features.
"""

import sys
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.dtos import ProductDTO, SkinProfileDTO
from utils.helpers import extract_keywords, normalize_price_range

# Skin type keywords mapping
SKIN_TYPE_KEYWORDS = {
    "dry": ["dry", "hydrating", "moisturizing", "nourishing", "hydrating", "moisture"],
    "oily": [
        "oil-free",
        "matte",
        "non-comedogenic",
        "lightweight",
        "sebum",
        "oil control",
    ],
    "combination": ["balance", "combination", "normal", "balanced"],
    "sensitive": [
        "sensitive",
        "gentle",
        "hypoallergenic",
        "fragrance-free",
        "calming",
        "soothing",
    ],
    "normal": ["normal", "suitable for all", "universal"],
}

# Skin concern keywords mapping
CONCERN_KEYWORDS = {
    "acne": [
        "acne",
        "pimple",
        "blemish",
        "breakout",
        "salicylic",
        "anti-acne",
        "clearing",
    ],
    "aging": [
        "anti-aging",
        "wrinkle",
        "fine line",
        "collagen",
        "retinol",
        "anti-wrinkle",
        "aging",
    ],
    "darkSpots": [
        "dark spot",
        "hyperpigmentation",
        "brightening",
        "vitamin c",
        "lightening",
        "pigment",
    ],
    "dryness": ["dry", "hydration", "moisture", "dehydration", "hydrating"],
    "oiliness": ["oil", "sebum", "pore", "matte", "oil control", "oily"],
    "sensitivity": ["sensitive", "calming", "soothing", "irritation", "gentle"],
}


def calculate_product_score(product: ProductDTO, skin_profile: SkinProfileDTO) -> float:
    """
    Calculate recommendation score for a product based on user profile.

    Scoring breakdown:
    - Base score: 50 points
    - Category match: +25 points (if preferred categories specified)
    - Price in budget: +20 points
    - Price above budget: -30 points
    - Price below min budget: +5 points
    - Skin type match: +15 points per keyword match
    - Concern match: +10 points per concern matched
    - Has category: +10 points (if no preference specified)
    - In stock: +5 points (if stock > 0)
    - Out of stock: -50 points

    Args:
        product: Product to score
        skin_profile: User's skin profile

    Returns:
        Score between 0 and 100+ (higher is better)
    """
    score = 50.0  # Base score

    # Price range matching
    if skin_profile.budgetRange:
        min_price, max_price = normalize_price_range(skin_profile.budgetRange)
        if min_price <= product.price <= max_price:
            score += 20  # Within budget
        elif product.price > max_price:
            score -= 30  # Exceeds budget
        elif product.price < min_price:
            score += 5  # Below minimum (slight bonus for cheaper)

    # Category preference matching
    if product.category:
        if skin_profile.preferredCategories:
            if product.category in skin_profile.preferredCategories:
                score += 25  # Matches preferred category
        else:
            score += 10  # No preference, but product has category (bonus)

    # Stock availability check
    if product.stock <= 0:
        score -= 50  # Out of stock - major penalty
    elif product.stock > 0:
        score += 5  # In stock - small bonus

    # Skin type matching (based on product description)
    if product.description and skin_profile.skinType:
        description_text = f"{product.name} {product.description}".lower()
        skin_type_lower = skin_profile.skinType.lower()

        if skin_type_lower in SKIN_TYPE_KEYWORDS:
            keywords = SKIN_TYPE_KEYWORDS[skin_type_lower]
            matches = extract_keywords(description_text, keywords)
            if matches > 0:
                score += 15  # Skin type match found
                # Additional points for multiple keyword matches
                if matches > 1:
                    score += 5

    # Concern matching (based on product description)
    if product.description and skin_profile.concerns:
        description_text = f"{product.name} {product.description}".lower()

        for concern in skin_profile.concerns:
            concern_lower = concern.lower()
            if concern_lower in CONCERN_KEYWORDS:
                keywords = CONCERN_KEYWORDS[concern_lower]
                matches = extract_keywords(description_text, keywords)
                if matches > 0:
                    score += 10  # Concern match found
                    # Additional points for multiple matches
                    if matches > 1:
                        score += 3

    # Ensure score is non-negative
    return max(0.0, score)


def generate_recommendation_reasons(
    product: ProductDTO, skin_profile: SkinProfileDTO, score: float
) -> List[str]:
    """
    Generate human-readable reasons for recommending a product.

    Args:
        product: Recommended product
        skin_profile: User's skin profile
        score: Calculated recommendation score

    Returns:
        List of reason strings
    """
    reasons = []

    # Category match
    if product.category and skin_profile.preferredCategories:
        if product.category in skin_profile.preferredCategories:
            reasons.append(f"Matches your preferred category: {product.category}")

    # Price range
    if skin_profile.budgetRange:
        min_price, max_price = normalize_price_range(skin_profile.budgetRange)
        if min_price <= product.price <= max_price:
            reasons.append(f"Within your budget (${min_price:.2f} - ${max_price:.2f})")
        elif product.price < min_price:
            reasons.append("Below your budget range")
        elif product.price > max_price:
            reasons.append("Above your budget range")

    # Skin type
    if product.description and skin_profile.skinType:
        description_text = f"{product.name} {product.description}".lower()
        skin_type_lower = skin_profile.skinType.lower()

        if skin_type_lower in SKIN_TYPE_KEYWORDS:
            keywords = SKIN_TYPE_KEYWORDS[skin_type_lower]
            matches = extract_keywords(description_text, keywords)
            if matches > 0:
                reasons.append(f"Suitable for {skin_profile.skinType} skin")

    # Concerns
    if product.description and skin_profile.concerns:
        description_text = f"{product.name} {product.description}".lower()
        matched_concerns = []

        for concern in skin_profile.concerns:
            concern_lower = concern.lower()
            if concern_lower in CONCERN_KEYWORDS:
                keywords = CONCERN_KEYWORDS[concern_lower]
                if extract_keywords(description_text, keywords) > 0:
                    matched_concerns.append(concern)

        if matched_concerns:
            concerns_str = ", ".join(matched_concerns)
            reasons.append(f"Addresses your concerns: {concerns_str}")

    # Stock status
    if product.stock > 0:
        reasons.append("Currently in stock")
    else:
        reasons.append("Note: Currently out of stock")

    return reasons


def rank_products(
    products: List[ProductDTO], skin_profile: SkinProfileDTO
) -> List[tuple[ProductDTO, float]]:
    """
    Rank products by recommendation score.

    Args:
        products: List of products to rank
        skin_profile: User's skin profile

    Returns:
        List of tuples (product, score) sorted by score (descending)
    """
    # Calculate scores for all products
    scored_products = [
        (product, calculate_product_score(product, skin_profile))
        for product in products
    ]

    # Sort by score (descending)
    scored_products.sort(key=lambda x: x[1], reverse=True)

    return scored_products
