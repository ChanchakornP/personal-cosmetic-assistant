"""
Supabase client service for direct database access.
Fetches product data directly from Supabase without going through Product API.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from models.dtos import ProductDTO
from supabase import Client, create_client

# Load environment variables
load_dotenv()

# Get Supabase configuration from environment (REQUIRED)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file.\n"
        "Example:\n"
        "SUPABASE_URL=https://hprgkalnbpshghzwfxhq.supabase.co"
        "SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhwcmdrYWxuYnBzaGdoendmeGhxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE3OTc0MDMsImV4cCI6MjA3NzM3MzQwM30.L5RA36_nIeofEAip52Xx7H1ZvTMq5M-peSaIrwCXBps"
    )


class SupabaseProductClient:
    """Client for fetching products directly from Supabase database"""

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize Supabase client.

        Args:
            url: Supabase project URL (defaults to SUPABASE_URL env var)
            key: Supabase anon key (defaults to SUPABASE_ANON_KEY env var)

        Raises:
            RuntimeError: If credentials are not provided
        """
        self.url = url or SUPABASE_URL
        self.key = key or SUPABASE_KEY

        if not self.url or not self.key:
            raise RuntimeError(
                "Supabase credentials are required. Set SUPABASE_URL and SUPABASE_ANON_KEY "
                "in your .env file or pass them as arguments."
            )

        self.client: Client = create_client(self.url, self.key)

    def _db_to_dto(self, row: dict) -> ProductDTO:
        """
        Convert database row to ProductDTO.

        Args:
            row: Database row from Supabase

        Returns:
            ProductDTO object
        """
        return ProductDTO(
            id=row["id"],
            name=row["name"],
            description=row.get("description"),
            price=float(row["price"]),
            stock=row.get("stock", 0),
            category=row.get("category"),
            mainImageUrl=row.get("main_image_url"),
            createdAt=row.get("created_at"),
            updatedAt=row.get("updated_at"),
        )

    def get_all_products(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        search_query: Optional[str] = None,
    ) -> List[ProductDTO]:
        """
        Fetch products from Supabase database.

        Args:
            category: Filter by category
            limit: Maximum number of products to return
            offset: Pagination offset
            search_query: Search query for product name

        Returns:
            List of ProductDTO objects

        Raises:
            Exception: If database query fails
        """
        try:
            query = self.client.table("product").select("*")

            # Apply filters
            if search_query:
                query = query.ilike("name", f"%{search_query}%")
            if category:
                query = query.eq("category", category)

            # Apply ordering (default: newest first)
            query = query.order("created_at", desc=True)

            # Apply pagination
            if limit:
                query = query.range(offset, offset + limit - 1)
            elif offset > 0:
                # If only offset specified, fetch a reasonable default
                query = query.range(offset, offset + 200)

            # Execute query
            res = query.execute()
            rows = res.data or []

            # Convert to DTOs
            return [self._db_to_dto(row) for row in rows]

        except Exception as e:
            raise Exception(f"Failed to fetch products from Supabase: {str(e)}")

    def get_product_by_id(self, product_id: int) -> ProductDTO:
        """
        Fetch a single product by ID from Supabase.

        Args:
            product_id: Product ID

        Returns:
            ProductDTO object

        Raises:
            Exception: If database query fails
        """
        try:
            res = (
                self.client.table("product")
                .select("*")
                .eq("id", product_id)
                .single()
                .execute()
            )

            if not res.data:
                raise Exception(f"Product {product_id} not found")

            return self._db_to_dto(res.data)

        except Exception as e:
            raise Exception(
                f"Failed to fetch product {product_id} from Supabase: {str(e)}"
            )

    def health_check(self) -> bool:
        """
        Check if Supabase connection is working.

        Returns:
            True if connection is working, False otherwise
        """
        try:
            # Try to fetch count from Product table
            res = (
                self.client.table("product")
                .select("id", count="exact")
                .limit(1)
                .execute()
            )
            return True
        except:
            return False


# Global instance
supabase_client = SupabaseProductClient()
