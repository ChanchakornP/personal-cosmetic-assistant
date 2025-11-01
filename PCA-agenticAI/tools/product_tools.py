"""
LangChain tools for product-related operations.
These tools can be used by agents to search and filter products.
"""

import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.tools import tool
from models.dtos import ProductDTO
from services.supabase_client import supabase_client


@tool
def search_products_tool(
    search_query: str,
    category: Optional[str] = None,
    limit: int = 50,
) -> str:
    """
    Search for cosmetic products by name or description.

    Args:
        search_query: Search term to match product names or descriptions
        category: Optional category filter (e.g., "cleanser", "moisturizer")
        limit: Maximum number of products to return (default: 50)

    Returns:
        JSON string with list of products matching the search criteria
    """
    try:
        products = supabase_client.get_all_products(
            search_query=search_query,
            category=category,
            limit=limit,
        )

        # Convert to JSON-serializable format
        products_data = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "stock": p.stock,
                "category": p.category,
            }
            for p in products
        ]

        import json

        return json.dumps(products_data, indent=2)
    except Exception as e:
        return f"Error searching products: {str(e)}"


@tool
def get_product_by_id_tool(product_id: int) -> str:
    """
    Get detailed information about a specific product by its ID.

    Args:
        product_id: The unique identifier of the product

    Returns:
        JSON string with product details including name, description, price, ingredients, etc.
    """
    try:
        product = supabase_client.get_product_by_id(product_id)

        product_data = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "category": product.category,
            "mainImageUrl": product.mainImageUrl,
        }

        import json

        return json.dumps(product_data, indent=2)
    except Exception as e:
        return f"Error fetching product: {str(e)}"


@tool
def filter_products_by_category_tool(
    category: str,
    limit: int = 50,
) -> str:
    """
    Filter products by category.

    Args:
        category: Product category (e.g., "cleanser", "moisturizer", "serum")
        limit: Maximum number of products to return (default: 50)

    Returns:
        JSON string with list of products in the specified category
    """
    try:
        products = supabase_client.get_all_products(
            category=category,
            limit=limit,
        )

        products_data = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "stock": p.stock,
                "category": p.category,
            }
            for p in products
        ]

        import json

        return json.dumps(products_data, indent=2)
    except Exception as e:
        return f"Error filtering products by category: {str(e)}"


@tool
def filter_products_by_price_tool(
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    category: Optional[str] = None,
    limit: int = 50,
) -> str:
    """
    Filter products by price range.

    Args:
        min_price: Minimum price (optional)
        max_price: Maximum price (optional)
        category: Optional category filter
        limit: Maximum number of products to return (default: 50)

    Returns:
        JSON string with list of products within the price range
    """
    try:
        # Fetch products (with category filter if specified)
        products = supabase_client.get_all_products(
            category=category,
            limit=200,  # Fetch more to filter by price
        )

        # Filter by price range
        filtered_products = []
        for p in products:
            if min_price is not None and p.price < min_price:
                continue
            if max_price is not None and p.price > max_price:
                continue
            filtered_products.append(p)
            if len(filtered_products) >= limit:
                break

        products_data = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "stock": p.stock,
                "category": p.category,
            }
            for p in filtered_products
        ]

        import json

        return json.dumps(products_data, indent=2)
    except Exception as e:
        return f"Error filtering products by price: {str(e)}"
