"""
Popularity-based recommendation algorithm using simple heuristics.

Heuristics:
- In-stock items are preferred
- Lower price gets a bonus (affordable)
- Category frequency gets a bonus (popular categories)
- Recent items (by createdAt) get a small bonus if available
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.dtos import ProductDTO


def _parse_created_at(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        # Try common timestamp formats
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                dt = datetime.strptime(value, fmt)
                return dt.timestamp()
            except Exception:
                continue
    except Exception:
        pass
    return 0.0


def popularity_score(
    product: ProductDTO,
    category_counts: dict[str, int],
    newest_ts: float,
    oldest_ts: float,
) -> float:
    score = 0.0

    # In stock preferred
    if product.stock > 0:
        score += 30
    else:
        score -= 20

    # Affordable price bonus (inverse relation)
    try:
        # Clamp price for stability
        price = max(0.01, float(product.price))
        score += max(0.0, 50.0 / (1.0 + price))  # cheaper -> higher bonus up to ~50
    except Exception:
        pass

    # Category popularity bonus
    if product.category:
        score += 5.0 * category_counts.get(product.category, 0)

    # Recency bonus (if timestamps available)
    ts = _parse_created_at(product.createdAt)
    if ts and newest_ts > oldest_ts:
        recency_ratio = (ts - oldest_ts) / (newest_ts - oldest_ts)
        score += 10.0 * recency_ratio

    return score


def rank_products(products: List[ProductDTO]) -> List[Tuple[ProductDTO, float]]:
    if not products:
        return []

    # Category frequency map
    category_counts: dict[str, int] = {}
    newest_ts = 0.0
    oldest_ts = float("inf")
    for p in products:
        if p.category:
            category_counts[p.category] = category_counts.get(p.category, 0) + 1
        ts = _parse_created_at(p.createdAt)
        if ts:
            newest_ts = max(newest_ts, ts)
            oldest_ts = min(oldest_ts, ts)

    scored = [
        (p, popularity_score(p, category_counts, newest_ts, oldest_ts))
        for p in products
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored
