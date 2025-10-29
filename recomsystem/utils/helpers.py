"""
Helper utility functions for recommendation system
"""

from typing import List, Dict, Any

def extract_keywords(text: str, keywords_list: List[str]) -> int:
    """
    Count how many keywords from keywords_list appear in text
    
    Args:
        text: Text to search in (case-insensitive)
        keywords_list: List of keywords to search for
        
    Returns:
        Number of keywords found
    """
    if not text:
        return 0
    
    text_lower = text.lower()
    count = 0
    for keyword in keywords_list:
        if keyword.lower() in text_lower:
            count += 1
    return count

def normalize_price_range(budget_range: Dict[str, Any]) -> tuple:
    """
    Normalize budget range, handling missing min/max values
    
    Args:
        budget_range: Dict with optional 'min' and 'max' keys
        
    Returns:
        Tuple of (min_price, max_price)
    """
    min_price = budget_range.get("min", 0) if budget_range else 0
    max_price = budget_range.get("max", float("inf")) if budget_range else float("inf")
    return (min_price, max_price)

