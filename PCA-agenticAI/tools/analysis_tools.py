"""
LangChain tools for analysis operations.
These tools help agents analyze ingredients and check skin compatibility.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.tools import tool
from services.llm_service import llm_service


@tool
def analyze_ingredients_tool(products: List[Dict[str, str]]) -> str:
    """
    Analyze ingredient conflicts between multiple cosmetic products.

    Args:
        products: List of product dictionaries. Each product should have:
            - id: Product ID
            - name: Product name
            - ingredients: Ingredient list (comma-separated string)

    Returns:
        JSON string with conflict analysis including:
        - conflictDetected: boolean
        - conflictDetails: string
        - safetyWarning: string or null
        - alternatives: list of strings
    """
    try:
        result = llm_service.analyze_ingredient_conflicts(products)

        if not result:
            return json.dumps(
                {
                    "conflictDetected": False,
                    "conflictDetails": "Analysis unavailable",
                    "safetyWarning": None,
                    "alternatives": [],
                }
            )

        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps(
            {
                "error": str(e),
                "conflictDetected": False,
                "conflictDetails": "Error during analysis",
                "safetyWarning": None,
                "alternatives": [],
            }
        )


@tool
def check_skin_compatibility_tool(
    product_description: str,
    skin_type: str,
    concerns: List[str],
) -> str:
    """
    Check if a product is compatible with a specific skin type and concerns.

    Args:
        product_description: Product description or ingredient list
        skin_type: User's skin type (dry, oily, combination, sensitive, normal)
        concerns: List of skin concerns (e.g., ["acne", "aging"])

    Returns:
        JSON string with compatibility analysis
    """
    if not llm_service.is_available():
        return '{"compatible": true, "reason": "LLM service unavailable, assuming compatible"}'

    try:
        concerns_str = ", ".join(concerns) if concerns else "none"
        prompt = f"""Analyze if this cosmetic product is suitable for the user's skin profile.

Product Description:
{product_description}

User Skin Profile:
- Skin Type: {skin_type}
- Concerns: {concerns_str}

Provide a brief compatibility assessment. Return JSON with:
- compatible: boolean
- reason: string (brief explanation)
- warnings: array of strings (any potential issues or warnings)
"""

        response = llm_service.generate_text(
            prompt=prompt,
            temperature=0.3,
            max_tokens=200,
        )

        if response:
            import re

            # Try to extract JSON from response
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                try:
                    return json_match.group(0)
                except:
                    pass

        # Fallback
        return json.dumps(
            {
                "compatible": True,
                "reason": "Unable to analyze compatibility",
                "warnings": [],
            }
        )
    except Exception as e:
        return json.dumps(
            {
                "error": str(e),
                "compatible": True,
                "reason": "Error during compatibility check",
                "warnings": [],
            }
        )
