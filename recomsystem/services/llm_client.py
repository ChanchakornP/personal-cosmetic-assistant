"""
LLM client service for AI-powered features.
Initializes LLM connection on instantiation for better performance.
Uses Google Gemini API (free tier available).
"""

import base64
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import Pydantic for schema definitions
try:
    from pydantic import BaseModel

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

# Try to import Google Gemini client (optional - graceful fallback if not configured)
try:
    from google import genai
    from google.genai import types

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Get LLM configuration from environment
LLM_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")  # gemini-2.5-flash for vision


# Pydantic schema for facial analysis response
if PYDANTIC_AVAILABLE:

    class FacialAnalysisSchema(BaseModel):
        """Schema for structured facial analysis response"""

        skinType: str
        concerns: List[str]
        analysis: str

else:
    # Fallback if Pydantic not available
    FacialAnalysisSchema = None


class LLMClient:
    """
    Client for interacting with LLM services (Google Gemini).
    Connection is initialized when the client is instantiated.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM client and create connection.

        Args:
            api_key: API key for Gemini service (defaults to GEMINI_API_KEY env var)
            model: Model name to use (defaults to LLM_MODEL env var or gemini-2.5-flash)
        """
        self.api_key = api_key or LLM_API_KEY
        self.model = model or LLM_MODEL
        self.client = None
        self._initialized = False

        # Initialize the connection if API key is provided
        if self.api_key:
            self._initialize()
        else:
            # Log warning but allow graceful degradation
            print("Warning: GEMINI_API_KEY not set. LLM features will be disabled.")

    def _initialize(self):
        """
        Initialize the LLM client connection.
        Called during __init__ to establish connection early.
        """
        if not GEMINI_AVAILABLE:
            print(
                "Warning: Google genai package not installed. Install with: pip install google-genai"
            )
            return

        try:
            # Create client with API key using new API
            self.client = genai.Client(api_key=self.api_key)
            self._initialized = True
            print(f"LLM client initialized successfully (model: {self.model})")
        except Exception as e:
            print(f"Warning: Failed to initialize LLM client: {str(e)}")
            self._initialized = False

    def is_available(self) -> bool:
        """
        Check if LLM client is available and initialized.

        Returns:
            True if client is ready to use, False otherwise
        """
        return self._initialized and self.client is not None

    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        max_retries: int = 1,
    ) -> Optional[str]:
        """
        Generate text using the LLM.

        Args:
            prompt: User prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate (Gemini uses max_output_tokens)
            system_prompt: Optional system prompt (Gemini uses system_instruction)
            max_retries: Maximum number of retry attempts (default: 1, set to 0 to disable retries)

        Returns:
            Generated text or None if generation fails
        """
        if not self.is_available():
            return None

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                # Build the full prompt
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n{prompt}"

                # Configure generation parameters using new API
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens if max_tokens else None,
                )

                # Generate response using new API
                response = self.client.models.generate_content(
                    model=self.model, contents=[full_prompt], config=config
                )

                if not response.text:
                    if attempt < max_retries:
                        continue  # Retry on empty response
                    # Only log error on final attempt to avoid spam
                    return None
                return response.text
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    continue  # Retry on exception
                # Only log error on final attempt
                break

        # Log error only once after all retries exhausted
        if last_error:
            print(
                f"Error generating text with LLM after {max_retries + 1} attempts: {str(last_error)}"
            )
        else:
            print(f"Error: Empty response from LLM after {max_retries + 1} attempts")
        return None

    def generate_recommendation_explanation(
        self, product_name: str, product_description: str, skin_profile_summary: str
    ) -> Optional[str]:
        """
        Generate AI-powered explanation for a product recommendation.

        Args:
            product_name: Name of the recommended product
            product_description: Product description
            skin_profile_summary: Summary of user's skin profile

        Returns:
            Generated explanation or None if generation fails
        """
        if not self.is_available():
            return None

        system_prompt = """You are a cosmetic product recommendation expert. 
Generate concise, personalized explanations for why a product is recommended based on the user's skin profile.
Keep responses brief (1-2 sentences) and focus on how the product addresses the user's specific needs."""

        user_prompt = f"""Explain why this product is recommended:
        
Product: {product_name}
Description: {product_description}

User Profile: {skin_profile_summary}

Generate a brief, personalized explanation."""

        return self.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=150,
        )

    def generate_batch_recommendation_explanations(
        self,
        products: List[Dict[str, Any]],
        skin_profile_summary: str,
    ) -> Optional[Dict[str, str]]:
        """
        Generate AI-powered explanations for multiple product recommendations in a single LLM call.

        Args:
            products: List of product dictionaries with keys: id, name, description
            skin_profile_summary: Summary of user's skin profile

        Returns:
            Dictionary mapping product IDs (as strings) to explanations, or None if generation fails
        """
        if not self.is_available() or not products:
            return None

        system_prompt = """You are a cosmetic product recommendation expert. 
Generate concise, personalized explanations for why each product is recommended based on the user's skin profile.
Keep each explanation brief (1-2 sentences) and focus on how each product addresses the user's specific needs.
Return your response as a JSON object where each key is the product ID (as a string) and the value is the explanation for that product."""

        # Build product list in the prompt
        products_text = "\n\n".join(
            [
                f"Product ID: {p['id']}\nProduct: {p['name']}\nDescription: {p.get('description', p['name'])}"
                for p in products
            ]
        )

        user_prompt = f"""Explain why each of these products is recommended for this user:

User Profile: {skin_profile_summary}

Products:
{products_text}

Generate brief, personalized explanations for each product. Return your response as a JSON object with product IDs as keys and explanations as values.
Example format: {{"1": "This product...", "2": "This product..."}}"""

        response_text = self.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=min(
                150 * len(products), 2000
            ),  # Scale tokens with product count, but cap at 2000
            max_retries=1,
        )

        if not response_text:
            return None

        # Try to parse JSON response
        try:
            # Try direct JSON parse first
            explanations = json.loads(response_text)
            # Ensure all keys are strings (product IDs)
            return {str(k): str(v) for k, v in explanations.items()}
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                try:
                    explanations = json.loads(json_match.group())
                    return {str(k): str(v) for k, v in explanations.items()}
                except json.JSONDecodeError:
                    pass

            # Fallback: If JSON parsing fails, try to extract explanations by product ID
            # This is a best-effort fallback
            explanations = {}
            for product in products:
                product_id = str(product["id"])
                product_name = product["name"]
                # Look for text near the product ID or name
                pattern = rf"(?:{product_id}|{re.escape(product_name)})[:\-]?\s*([^\"\n]+?)(?=\n\n|\nProduct|\{{|$)"
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    explanations[product_id] = match.group(1).strip()

            return explanations if explanations else None

    def health_check(self) -> Dict[str, Any]:
        """
        Check LLM service health and connectivity.

        Returns:
            Dictionary with health status information
        """
        if not GEMINI_AVAILABLE:
            return {
                "available": False,
                "reason": "Google Generative AI package not installed",
                "initialized": False,
            }

        if not self.api_key:
            return {
                "available": False,
                "reason": "API key not configured",
                "initialized": False,
            }

        if not self.is_available():
            return {
                "available": False,
                "reason": "Client initialization failed",
                "initialized": False,
            }

        # Test connection with a minimal request
        try:
            config = types.GenerateContentConfig(max_output_tokens=5)
            test_response = self.client.models.generate_content(
                model=self.model, contents=["test"], config=config
            )
            return {
                "available": True,
                "initialized": True,
                "model": self.model,
                "connection_test": "success",
            }
        except Exception as e:
            return {
                "available": False,
                "initialized": True,
                "reason": f"Connection test failed: {str(e)}",
            }

    def analyze_facial_image(
        self,
        image_data: str,
        user_skin_type: Optional[str] = None,
        user_concerns: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze facial image using vision model and extract skin information.

        Args:
            image_data: Base64 encoded image or image URL
            user_skin_type: User-provided skin type (optional)
            user_concerns: User-reported concerns (optional)

        Returns:
            Dictionary with detected skin type, concerns, and analysis
        """
        if not self.is_available():
            return None

        try:
            # Determine if image_data is base64 or URL and get bytes + mime type
            if image_data.startswith("data:image"):
                # Extract base64 data and mime type
                parts = image_data.split(",")
                mime_type = parts[0].split(":")[1].split(";")[0]
                image_bytes = base64.b64decode(parts[1])
            elif image_data.startswith("http://") or image_data.startswith("https://"):
                # URL-based image
                if not REQUESTS_AVAILABLE:
                    return {
                        "skinType": user_skin_type or "normal",
                        "concerns": user_concerns or [],
                        "analysis": "Requests library not installed. Cannot fetch images from URLs.",
                    }
                http_response = requests.get(image_data)
                image_bytes = http_response.content
                # Guess mime type from content-type header or URL
                content_type = http_response.headers.get("content-type", "image/jpeg")
                mime_type = content_type.split(";")[0]
                if mime_type not in [
                    "image/jpeg",
                    "image/png",
                    "image/gif",
                    "image/webp",
                ]:
                    mime_type = "image/jpeg"  # Default fallback
            else:
                # Assume base64 without data URL prefix
                image_bytes = base64.b64decode(image_data)
                mime_type = "image/jpeg"  # Default assumption

            # Create analysis prompt
            analysis_prompt = """Analyze this facial image and provide a detailed skin analysis.

Please identify:
1. Skin type (oily, dry, combination, sensitive, normal)
2. Visible skin concerns (acne, wrinkles, dark spots, sensitivity, dryness, oiliness, redness, texture issues, etc.)
3. Overall skin condition and recommendations"""

            # Generate content with image using new API
            # Force JSON output by setting response_mime_type and response_schema
            config_params = {
                "temperature": 0.3,
                "max_output_tokens": 1000,
                "response_mime_type": "application/json",
            }

            # Add schema if Pydantic is available
            if PYDANTIC_AVAILABLE and FacialAnalysisSchema:
                config_params["response_schema"] = FacialAnalysisSchema

            config = types.GenerateContentConfig(**config_params)

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    analysis_prompt,
                ],
                config=config,
            )

            # Parse response
            if not response.text:
                raise ValueError("Empty response from model - no text in LLM response")

            # With schema, response.text should be valid JSON directly
            try:
                result = json.loads(response.text)
                return {
                    "skinType": result.get("skinType", user_skin_type or "normal"),
                    "concerns": result.get("concerns", user_concerns or []),
                    "analysis": result.get("analysis", ""),
                }
            except json.JSONDecodeError:
                # Fallback: Try to extract JSON from markdown code blocks
                json_match = re.search(r"\{[\s\S]*\}", response.text)
                if json_match:
                    result = json.loads(json_match.group())
                    return {
                        "skinType": result.get("skinType", user_skin_type or "normal"),
                        "concerns": result.get("concerns", user_concerns or []),
                        "analysis": result.get("analysis", ""),
                    }
                else:
                    # Last resort: return structured data from text
                    return {
                        "skinType": user_skin_type or "normal",
                        "concerns": user_concerns or [],
                        "analysis": response.text,
                    }

        except Exception as e:
            print(f"Error analyzing facial image with LLM: {str(e)}")
            # Fallback: return user-provided data
            return {
                "skinType": user_skin_type or "normal",
                "concerns": user_concerns or [],
                "analysis": f"Unable to perform AI analysis. User-reported skin type: {user_skin_type or 'not provided'}.",
            }


# Global instance - connection will be established when imported
llm_client = LLMClient()
