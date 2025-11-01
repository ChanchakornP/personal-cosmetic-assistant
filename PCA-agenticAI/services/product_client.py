import os
import sys
from pathlib import Path
from typing import List, Optional

import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.dtos import ProductDTO

# Get Product API URL from environment
PRODUCT_API_URL = os.getenv("PRODUCT_API_URL", "http://localhost:8000")


class ProductClient:
    """Client for interacting with the Product API service"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or PRODUCT_API_URL
        self.api_base = f"{self.base_url}/api"

    def get_all_products(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        search_query: Optional[str] = None,
    ) -> List[ProductDTO]:
        """
        Fetch products from Product API

        Args:
            category: Filter by category
            limit: Maximum number of products to return
            offset: Pagination offset
            search_query: Search query for product name

        Returns:
            List of ProductDTO objects

        Raises:
            requests.exceptions.RequestException: If API request fails
        """
        params = {}
        if category:
            params["category"] = category
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        if search_query:
            params["q"] = search_query

        try:
            response = requests.get(
                f"{self.api_base}/products", params=params, timeout=10
            )
            response.raise_for_status()
            products_data = response.json()
            return [ProductDTO(**product) for product in products_data]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to fetch products from Product API: {str(e)}")

    def get_product_by_id(self, product_id: int) -> ProductDTO:
        """
        Fetch a single product by ID

        Args:
            product_id: Product ID

        Returns:
            ProductDTO object

        Raises:
            requests.exceptions.RequestException: If API request fails
        """
        try:
            response = requests.get(
                f"{self.api_base}/products/{product_id}", timeout=10
            )
            response.raise_for_status()
            product_data = response.json()
            return ProductDTO(**product_data)
        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Failed to fetch product {product_id} from Product API: {str(e)}"
            )

    def health_check(self) -> bool:
        """
        Check if Product API is accessible

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            return response.status_code == 200
        except:
            return False


# Global instance
product_client = ProductClient()
