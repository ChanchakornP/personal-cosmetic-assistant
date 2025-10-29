"""
Hybrid recommendation algorithm that combines content-based and popularity signals.
"""
from __future__ import annotations
from typing import List, Tuple
from models.dtos import ProductDTO, SkinProfileDTO
from .content_based import calculate_product_score
from .popularity import popularity_score


def rank_products(products: List[ProductDTO], skin_profile: SkinProfileDTO,
                  content_weight: float = 0.7, popularity_weight: float = 0.3) -> List[Tuple[ProductDTO, float]]:
    if not products:
        return []

    # Precompute category counts and recency boundaries for popularity
    # We reuse functions by calling popularity_score inside a loop but need helpers
    # Create lightweight caches
    category_counts: dict[str, int] = {}
    newest_ts = 0.0
    oldest_ts = float("inf")

    from datetime import datetime

    def _parse_created_at(value: str | None) -> float:
        if not value:
            return 0.0
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).timestamp()
            except Exception:
                continue
        return 0.0

    for p in products:
        if p.category:
            category_counts[p.category] = category_counts.get(p.category, 0) + 1
        ts = _parse_created_at(p.createdAt)
        if ts:
            newest_ts = max(newest_ts, ts)
            oldest_ts = min(oldest_ts, ts)

    scored: List[Tuple[ProductDTO, float]] = []
    # Normalize weights
    total_w = max(1e-6, content_weight + popularity_weight)
    cw = content_weight / total_w
    pw = popularity_weight / total_w

    for p in products:
        content = calculate_product_score(p, skin_profile)
        pop = popularity_score(p, category_counts, newest_ts, oldest_ts)
        score = cw * content + pw * pop
        scored.append((p, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored
