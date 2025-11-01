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

# Load environment variables early
try:
    from dotenv import load_dotenv

    # Load .env file from the recomsystem directory
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Also try loading from current directory
        load_dotenv()
except ImportError:
    pass  # dotenv not installed, will rely on system env vars

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

    def _is_max_tokens(self, finish_reason_str: str, finish_reason_name: str) -> bool:
        """
        Check if finish reason indicates MAX_TOKENS was reached.

        Args:
            finish_reason_str: String representation of finish reason
            finish_reason_name: Enum name of finish reason if available

        Returns:
            True if MAX_TOKENS was hit
        """
        if not finish_reason_str:
            return False
        upper_str = finish_reason_str.upper()
        upper_name = finish_reason_name.upper()
        return (
            "MAX_TOKENS" in upper_str
            or upper_name == "MAX_TOKENS"
            or ("MAX" in upper_str and "TOKEN" in upper_str)
        )

    def _extract_text_from_response(
        self, response: Any, debug: bool = False
    ) -> Optional[str]:
        """
        Extract text from LLM response object, trying multiple methods.

        Args:
            response: LLM response object
            debug: Enable debug logging

        Returns:
            Extracted text or None if not found
        """
        # Try response.text first
        if hasattr(response, "text"):
            try:
                text = response.text
                if text:
                    if debug:
                        print(f"Got text from response.text: {len(text)} chars")
                    return text
            except Exception as e:
                if debug:
                    print(f"Error accessing response.text: {e}")

        # Try extracting from candidates
        if not hasattr(response, "candidates") or not response.candidates:
            return None

        candidate = response.candidates[0]

        # Try candidate.text
        if hasattr(candidate, "text"):
            try:
                text = candidate.text
                if text:
                    if debug:
                        print(f"Extracted text from candidate.text: {len(text)} chars")
                    return text
            except Exception as e:
                if debug:
                    print(f"Error accessing candidate.text: {e}")

        # Try candidate.content.parts
        if hasattr(candidate, "content"):
            try:
                content = candidate.content
                if hasattr(content, "parts") and content.parts:
                    for i, part in enumerate(content.parts):
                        if hasattr(part, "text"):
                            text = part.text
                            if text:
                                if debug:
                                    print(
                                        f"Extracted text from content.parts[{i}]: {len(text)} chars"
                                    )
                                return text
                elif hasattr(content, "text"):
                    text = content.text
                    if text:
                        if debug:
                            print(
                                f"Extracted text from content.text: {len(text)} chars"
                            )
                        return text
            except Exception as e:
                if debug:
                    print(f"Error accessing candidate.content: {e}")

        return None

    def _get_finish_reason_info(self, candidate: Any) -> tuple[str, str]:
        """
        Extract finish reason information from candidate.

        Args:
            candidate: Candidate object from LLM response

        Returns:
            Tuple of (finish_reason_str, finish_reason_name)
        """
        if not hasattr(candidate, "finish_reason"):
            return "", ""

        finish_reason = candidate.finish_reason
        finish_reason_str = str(finish_reason)
        finish_reason_name = (
            finish_reason.name if hasattr(finish_reason, "name") else str(finish_reason)
        )

        return finish_reason_str, finish_reason_name

    def _debug_candidate_structure(self, candidate: Any) -> None:
        """
        Print debug information about candidate structure (for troubleshooting).

        Args:
            candidate: Candidate object from LLM response
        """
        print(
            f"DEBUG: Candidate attributes: {[attr for attr in dir(candidate) if not attr.startswith('_')]}"
        )
        if hasattr(candidate, "content"):
            print(f"DEBUG: Content type: {type(candidate.content)}")
            print(
                f"DEBUG: Content attributes: {[attr for attr in dir(candidate.content) if not attr.startswith('_')]}"
            )
            try:
                print(
                    f"DEBUG: content.parts type: {type(candidate.content.parts) if hasattr(candidate.content, 'parts') else 'no parts attr'}"
                )
                if hasattr(candidate.content, "parts") and candidate.content.parts:
                    print(f"DEBUG: Number of parts: {len(candidate.content.parts)}")
                    for i, part in enumerate(candidate.content.parts):
                        print(
                            f"DEBUG: Part {i} type: {type(part)}, has text: {hasattr(part, 'text')}"
                        )
                        if hasattr(part, "text"):
                            print(
                                f"DEBUG: Part {i} text length: {len(part.text) if part.text else 0}"
                            )
            except Exception as e:
                print(f"DEBUG: Error inspecting content: {e}")

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
        current_max_tokens = (
            max_tokens  # Track current token limit (may increase on retries)
        )
        for attempt in range(max_retries + 1):
            try:
                # Build the full prompt
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n{prompt}"

                # Configure generation parameters using new API
                # Use current_max_tokens which may have been increased on previous attempts
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=(
                        current_max_tokens if current_max_tokens else None
                    ),
                )

                # Generate response using new API
                response = self.client.models.generate_content(
                    model=self.model, contents=[full_prompt], config=config
                )

                # Extract text from response
                response_text = self._extract_text_from_response(response, debug=True)

                # Get finish reason info
                finish_reason_str = ""
                finish_reason_name = ""
                candidate = None
                if hasattr(response, "candidates") and response.candidates:
                    candidate = response.candidates[0]
                    finish_reason_str, finish_reason_name = (
                        self._get_finish_reason_info(candidate)
                    )
                    if finish_reason_str:
                        print(
                            f"Finish reason: {finish_reason_str} (name: {finish_reason_name})"
                        )

                    # Debug structure when MAX_TOKENS is detected
                    if self._is_max_tokens(finish_reason_str, finish_reason_name):
                        print("DEBUG: MAX_TOKENS detected!")
                        self._debug_candidate_structure(candidate)

                    # Handle MAX_TOKENS case
                    if self._is_max_tokens(finish_reason_str, finish_reason_name):
                        if response_text and response_text.strip():
                            print(
                                f"Warning: Response truncated at max_tokens, using partial response ({len(response_text)} chars)"
                            )
                            return response_text
                        else:
                            print("Error: MAX_TOKENS but could not extract any text")
                            # Increase tokens and retry
                            if attempt < max_retries:
                                current_max_tokens = (
                                    (current_max_tokens * 2)
                                    if current_max_tokens
                                    else 4000
                                )
                                print(
                                    f"Increasing max_tokens to {current_max_tokens} and retrying (attempt {attempt + 1})..."
                                )
                                continue  # Retry with higher token limit

                    # Log safety ratings if available
                    if candidate and hasattr(candidate, "safety_ratings"):
                        print(f"Safety ratings: {candidate.safety_ratings}")

                if not response_text or not response_text.strip():
                    # Check if there's a blocking reason or safety filter
                    if hasattr(response, "prompt_feedback"):
                        print(f"Prompt feedback: {response.prompt_feedback}")

                    if attempt < max_retries:
                        print(f"Empty response on attempt {attempt + 1}, retrying...")
                        continue  # Retry on empty response
                    # Only log error on final attempt to avoid spam
                    print(
                        f"Final attempt failed - empty response after {max_retries + 1} attempts"
                    )
                    return None
                return response_text
            except Exception as e:
                last_error = e
                print(f"Exception on attempt {attempt + 1}: {str(e)}")
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

    def analyze_ingredient_conflicts(
        self, products: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze ingredient conflicts between multiple cosmetic products using LLM.

        Args:
            products: List of product dictionaries with keys: id, name, ingredients

        Returns:
            Dictionary with conflict analysis including conflictDetected, conflictDetails, safetyWarning, and alternatives
        """
        if not self.is_available():
            return None

        try:
            # Build prompt with product information (truncate long ingredient lists)
            def truncate_ingredients(ingredients: str, max_length: int = 300) -> str:
                """Truncate ingredient list to prevent overly long prompts."""
                if not ingredients or ingredients == "Not specified":
                    return "Not specified"
                if len(ingredients) <= max_length:
                    return ingredients
                # Take first part and add indicator
                truncated = ingredients[:max_length]
                # Try to cut at a comma if possible
                last_comma = truncated.rfind(",")
                if last_comma > max_length * 0.8:  # If comma is reasonably close to end
                    truncated = truncated[:last_comma]
                return truncated + " ... (more ingredients)"

            products_text = "\n".join(
                [
                    f"{i+1}. {p.get('name', 'Unknown')}: {truncate_ingredients(p.get('ingredients', 'Not specified'))}"
                    for i, p in enumerate(products)
                ]
            )

            # Use JSON format prompt for very brief response
            system_prompt = """You are a cosmetic dermatology expert. Return ONLY valid JSON. Keep all text extremely brief - maximum 2-3 sentences per field."""

            user_prompt = f"""Analyze conflicts between these products. Return ONLY JSON:

{{
  "conflictDetected": true/false,
  "conflictDetails": "1-2 sentence summary",
  "safetyWarning": "1 sentence warning or null",
  "alternatives": ["short tip 1", "short tip 2"]
}}

Products:
{products_text}

Rules: conflictDetails max 50 words, alternatives max 3 items (5-10 words each). Be concise. JSON only."""

            # Request very brief JSON response
            prompt_length = len(user_prompt) + len(system_prompt or "")
            print(
                f"Calling LLM for ingredient conflict analysis with {len(products)} products (prompt length: {prompt_length} chars)"
            )
            response_text = self.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1,  # Very low temperature for consistent, brief JSON
                max_tokens=400,  # Increased slightly to handle multiple products but still brief
                max_retries=3,  # More retries to handle edge cases
            )

            if not response_text:
                print(
                    f"Warning: LLM returned empty response for ingredient conflict analysis"
                )
                print(f"Products: {[p.get('name') for p in products]}")
                print(f"Prompt length: {prompt_length} chars")
                return None

            # Parse JSON response
            try:
                # Try to extract JSON from response (may be wrapped in markdown code blocks)
                json_text = response_text.strip()

                # Remove markdown code blocks if present
                if json_text.startswith("```"):
                    # Extract JSON from code block
                    json_match = re.search(
                        r"```(?:json)?\s*(\{[\s\S]*\})\s*```", json_text
                    )
                    if json_match:
                        json_text = json_match.group(1)
                    else:
                        # Try to find JSON object
                        json_match = re.search(r"\{[\s\S]*\}", json_text)
                        if json_match:
                            json_text = json_match.group(0)

                # Parse JSON
                result = json.loads(json_text)

                # Validate and normalize response structure
                return {
                    "conflictDetected": bool(result.get("conflictDetected", False)),
                    "conflictDetails": str(
                        result.get("conflictDetails", "No detailed analysis available.")
                    ),
                    "safetyWarning": (
                        result.get("safetyWarning")
                        if result.get("safetyWarning")
                        else None
                    ),
                    "alternatives": (
                        result.get("alternatives", [])
                        if isinstance(result.get("alternatives"), list)
                        else []
                    ),
                }
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {e}")
                print(
                    f"Response text: {response_text[:500]}"
                )  # Print first 500 chars for debugging

                # Fallback: try to extract basic info from text
                response_lower = response_text.lower()
                conflict_detected = any(
                    keyword in response_lower
                    for keyword in [
                        "conflict",
                        "incompatible",
                        "interaction",
                        "warning",
                        "risk",
                    ]
                )

                return {
                    "conflictDetected": conflict_detected,
                    "conflictDetails": response_text[:500],  # Truncate to 500 chars
                    "safetyWarning": (
                        "Unable to parse response format. Please try again."
                        if not conflict_detected
                        else None
                    ),
                    "alternatives": [],
                }

        except Exception as e:
            print(f"Error analyzing ingredient conflicts with LLM: {str(e)}")
            import traceback

            print(f"Traceback: {traceback.format_exc()}")
            return None


# Global instance - connection will be established when imported
llm_client = LLMClient()
