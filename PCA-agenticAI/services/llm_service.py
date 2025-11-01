"""
LangChain-based LLM service for AI-powered features.
Uses LangChain with Google Gemini integration for agentic AI capabilities.
"""

import base64
import json
import os
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

try:
    from models.dtos import FacialAnalysisLLMResponse, LLMProductSelectionResponse

    PYDANTIC_DTOS_AVAILABLE = True
except ImportError:
    PYDANTIC_DTOS_AVAILABLE = False

try:
    from dotenv import load_dotenv

    # Load .env file from the PCA-agenticAI directory
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()
except ImportError:
    pass

# LangChain imports
try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_google_genai import ChatGoogleGenerativeAI

    LANGCHAIN_AVAILABLE = True
    PYDANTIC_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    PYDANTIC_AVAILABLE = False

# Get LLM configuration from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash-exp")


def _strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` fences if present."""
    if not text:
        return text
    t = text.strip()
    if t.startswith("```") and t.endswith("```"):
        lines = t.splitlines()
        if len(lines) >= 2:
            first = lines[0].strip()
            last = lines[-1].strip()
            if first.startswith("```") and last == "```":
                return "\n".join(lines[1:-1]).strip()
    return text


def _find_first_json_obj(text: str) -> Optional[str]:
    """Find the first balanced JSON object in text."""
    if not text:
        return None
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def parse_json_safely(text: str) -> Optional[Dict[str, Any]]:
    """Parse JSON from model output reliably."""
    if not text:
        return None

    # First strip code fences
    candidate = _strip_code_fences(text)

    # Try direct parse first
    try:
        return json.loads(candidate)
    except Exception:
        pass

    # Try to find first JSON object with balanced braces
    found = _find_first_json_obj(candidate)
    if found:
        try:
            return json.loads(found)
        except Exception:
            pass

    # Last attempt: try to extract JSON with regex (handles multiline)
    import re

    json_match = re.search(r"\{[\s\S]*\}", candidate)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except Exception:
            pass

    return None


def _validate_llm_response(
    data: Dict[str, Any],
    user_skin_type: Optional[str] = None,
    user_concerns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validate and normalize LLM response using Pydantic model.

    Args:
        data: Parsed JSON dict from LLM
        user_skin_type: Fallback skin type if not in data
        user_concerns: Fallback concerns if not in data

    Returns:
        Validated dict with skinType, concerns, and analysis fields
    """
    if not PYDANTIC_DTOS_AVAILABLE:
        # Fallback if Pydantic models not available
        print("DEBUG: Pydantic models not available, using manual validation")
        return {
            "skinType": data.get("skinType", user_skin_type or "normal"),
            "concerns": data.get("concerns", user_concerns or []),
            "analysis": data.get("analysis", ""),
        }

    try:
        # Validate using Pydantic model
        validated = FacialAnalysisLLMResponse(**data)
        print("DEBUG: Successfully validated LLM response with Pydantic")
        return {
            "skinType": validated.skinType,
            "concerns": validated.concerns,
            "analysis": validated.analysis,
        }
    except Exception as validation_error:
        print(f"DEBUG: Pydantic validation failed: {validation_error}")
        # Fallback: try to extract valid fields from data
        try:
            # Ensure skinType is a string
            skin_type = str(data.get("skinType", user_skin_type or "normal"))
            # Ensure concerns is a list of strings
            concerns = data.get("concerns", user_concerns or [])
            if not isinstance(concerns, list):
                concerns = [str(c) for c in concerns] if concerns else []
            # Ensure analysis is a string
            analysis = str(data.get("analysis", ""))

            print("DEBUG: Using fallback validation after Pydantic failure")
            return {
                "skinType": skin_type,
                "concerns": concerns,
                "analysis": analysis,
            }
        except Exception as fallback_error:
            print(f"DEBUG: Fallback validation also failed: {fallback_error}")
            # Ultimate fallback
            return {
                "skinType": user_skin_type or "normal",
                "concerns": user_concerns or [],
                "analysis": str(data.get("analysis", "Analysis unavailable.")),
            }


class LLMService:
    """
    LangChain-based LLM service for interacting with Google Gemini.
    Provides agentic AI capabilities through LangChain.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize LLM service with LangChain.

        Args:
            api_key: API key for Gemini service (defaults to GEMINI_API_KEY env var)
            model: Model name to use (defaults to LLM_MODEL env var)
        """
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or LLM_MODEL
        self._llm = None
        self._initialized = False

        if self.api_key:
            self._initialize()
        else:
            print("Warning: GEMINI_API_KEY not set. LLM features will be disabled.")

    def _initialize(self):
        """Initialize the LangChain LLM connection."""
        if not LANGCHAIN_AVAILABLE:
            print(
                "Warning: LangChain packages not installed. Install with: pip install langchain-google-genai langchain-core"
            )
            return

        try:
            self._llm = ChatGoogleGenerativeAI(
                model=self.model,
                google_api_key=self.api_key,
                temperature=0.7,
            )
            self._initialized = True
            print(
                f"LangChain LLM service initialized successfully (model: {self.model})"
            )
        except Exception as e:
            print(f"Warning: Failed to initialize LangChain LLM service: {str(e)}")
            self._initialized = False

    @property
    def llm(self):
        """Get the underlying LangChain LLM instance (for agents)."""
        return self._llm

    def is_available(self) -> bool:
        """Check if LLM service is available and initialized."""
        return self._initialized and self._llm is not None

    @property
    def available(self) -> bool:
        """Alias for is_available() for compatibility."""
        return self.is_available()

    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        max_retries: int = 1,
    ) -> Optional[str]:
        """
        Generate text using LangChain LLM.

        Args:
            prompt: User prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            max_retries: Maximum number of retry attempts

        Returns:
            Generated text or None if generation fails
        """
        if not self.is_available():
            print("DEBUG: generate_text called but LLM service is not available")
            return None

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                messages = []
                if system_prompt:
                    messages.append(SystemMessage(content=system_prompt))
                messages.append(HumanMessage(content=prompt))

                # Create a temporary LLM instance with custom temperature
                llm_instance = ChatGoogleGenerativeAI(
                    model=self.model,
                    google_api_key=self.api_key,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )

                response = llm_instance.invoke(messages)

                # Debug: log the response object type and metadata
                print(f"DEBUG: LLM response type: {type(response)}")

                # Check metadata for token usage info (important for Gemini 2.5 Flash reasoning tokens)
                if hasattr(response, "response_metadata"):
                    metadata = response.response_metadata
                    finish_reason = metadata.get("finish_reason", "unknown")
                    print(f"DEBUG: Finish reason: {finish_reason}")
                    if "usage_metadata" in metadata:
                        usage = metadata["usage_metadata"]
                        output_tokens = usage.get("output_tokens", 0)
                        print(f"DEBUG: Output tokens: {output_tokens}")
                        if "output_token_details" in usage:
                            details = usage["output_token_details"]
                            reasoning_tokens = details.get("reasoning", 0)
                            content_tokens = output_tokens - reasoning_tokens
                            print(
                                f"DEBUG: Reasoning tokens: {reasoning_tokens}, Content tokens: {content_tokens}"
                            )

                if hasattr(response, "content"):
                    result = response.content
                    print(
                        f"DEBUG: generate_text got content on attempt {attempt + 1} (type: {type(result)}, length: {len(result) if result else 0})"
                    )
                    # Check for empty/None content
                    if not result or (
                        isinstance(result, str) and len(result.strip()) == 0
                    ):
                        # Check if this is a reasoning token exhaustion issue
                        metadata = getattr(response, "response_metadata", {})
                        finish_reason = metadata.get("finish_reason", "")
                        usage = metadata.get("usage_metadata", {})
                        token_details = usage.get("output_token_details", {})
                        reasoning_tokens = token_details.get("reasoning", 0)

                        if finish_reason == "MAX_TOKENS" and reasoning_tokens > 0:
                            print(
                                f"DEBUG: ERROR - Model used all tokens for reasoning ({reasoning_tokens}), leaving 0 for content. Current max_tokens: {max_tokens}"
                            )
                            raise ValueError(
                                f"Token limit exhausted by reasoning tokens ({reasoning_tokens}). Need to increase max_output_tokens from {max_tokens} to at least {reasoning_tokens + 400}."
                            )
                        else:
                            print(
                                f"DEBUG: WARNING - LLM returned empty content. Response object: {response}, content: {repr(result)}"
                            )
                            raise ValueError("LLM returned empty response content")
                    print(
                        f"DEBUG: generate_text succeeded with valid content (length: {len(result)})"
                    )
                    return result
                elif isinstance(response, str):
                    print(
                        f"DEBUG: generate_text got string response on attempt {attempt + 1} (length: {len(response)})"
                    )
                    if not response or len(response.strip()) == 0:
                        print(f"DEBUG: WARNING - LLM returned empty string")
                        raise ValueError("LLM returned empty string response")
                    return response
                else:
                    result = str(response)
                    print(
                        f"DEBUG: generate_text converted response to string on attempt {attempt + 1} (length: {len(result)})"
                    )
                    if not result or len(result.strip()) == 0:
                        print(
                            f"DEBUG: WARNING - LLM returned empty string after conversion"
                        )
                        raise ValueError("LLM returned empty response after conversion")
                    return result

            except Exception as e:
                last_error = e
                print(
                    f"DEBUG: Exception on attempt {attempt + 1}/{max_retries + 1}: {str(e)}"
                )
                import traceback

                if attempt == 0:  # Only print full traceback on first attempt
                    print(f"DEBUG: Full traceback: {traceback.format_exc()}")
                if attempt < max_retries:
                    continue

        if last_error:
            print(
                f"DEBUG: Error generating text with LLM after {max_retries + 1} attempts: {str(last_error)}"
            )
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
        Generate AI-powered explanations for multiple product recommendations.

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

        # Use direct LLM call with manual JSON extraction
        try:
            if self.is_available():
                llm_with_json = ChatGoogleGenerativeAI(
                    model=self.model,
                    google_api_key=self.api_key,
                    temperature=0.7,
                    max_output_tokens=min(150 * len(products), 2000),
                )

                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]

                response = llm_with_json.invoke(messages)

                # Extract text from response
                response_text = (
                    response.content if hasattr(response, "content") else str(response)
                )

                # Extract JSON from response
                data = parse_json_safely(response_text)
                if isinstance(data, dict):
                    return {str(k): str(v) for k, v in data.items()}
        except Exception as e:
            print(f"Error in batch explanation: {e}")

        # Fallback to text generation and JSON parsing
        response_text = self.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=min(150 * len(products), 2000),
            max_retries=1,
        )

        if not response_text:
            return None

        # Try to parse JSON response
        data = parse_json_safely(response_text)
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}

        return None

    def health_check(self) -> Dict[str, Any]:
        """
        Check LLM service health and connectivity.

        Returns:
            Dictionary with health status information
        """
        if not LANGCHAIN_AVAILABLE:
            return {
                "available": False,
                "reason": "LangChain packages not installed",
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
                "reason": "Service initialization failed",
                "initialized": False,
            }

        # Test connection with a minimal request
        try:
            test_response = self._llm.invoke([HumanMessage(content="test")])
            return {
                "available": True,
                "initialized": True,
                "model": self.model,
                "connection_test": "success",
                "framework": "LangChain",
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
                parts = image_data.split(",")
                mime_type = parts[0].split(":")[1].split(";")[0]
                image_bytes = base64.b64decode(parts[1])
            elif image_data.startswith("http://") or image_data.startswith("https://"):
                if not REQUESTS_AVAILABLE:
                    return {
                        "skinType": user_skin_type or "normal",
                        "concerns": user_concerns or [],
                        "analysis": "Requests library not installed. Cannot fetch images from URLs.",
                    }
                http_response = requests.get(image_data)
                image_bytes = http_response.content
                content_type = http_response.headers.get("content-type", "image/jpeg")
                mime_type = content_type.split(";")[0]
                if mime_type not in [
                    "image/jpeg",
                    "image/png",
                    "image/gif",
                    "image/webp",
                ]:
                    mime_type = "image/jpeg"
            else:
                image_bytes = base64.b64decode(image_data)
                mime_type = "image/jpeg"

            # Create analysis prompt - make it very explicit about JSON format
            analysis_prompt = """Analyze this facial image and provide a detailed skin analysis.

Please identify:
1. Skin type: Choose ONE from: "oily", "dry", "combination", "sensitive", or "normal"
2. Visible skin concerns: List all detected concerns (e.g., "acne", "wrinkles", "dark spots", "sensitivity", "dryness", "oiliness", "redness", "texture issues")
3. Overall skin condition: Provide a detailed analysis paragraph explaining the skin condition and observations

CRITICAL: You MUST respond with ONLY valid JSON. Do NOT include markdown code blocks, backticks, or any other text. The exact required format is:

{
  "skinType": "normal",
  "concerns": ["dark spots", "wrinkles"],
  "analysis": "Your detailed analysis text here describing the skin condition, texture, tone, and any visible issues."
}

Field Requirements:
- "skinType" (string): Must be exactly one of: "oily", "dry", "combination", "sensitive", "normal"
- "concerns" (array of strings): List of detected concerns, can be empty array [] if none detected
- "analysis" (string): Detailed text analysis of the skin condition (minimum 50 words)

Return ONLY the JSON object, nothing else."""

            # Use direct Google Generative AI SDK (LangChain doesn't handle images well)
            # This is the same approach as the original recomsystem
            try:
                from google import genai
                from google.genai import types

                print("DEBUG: Using direct Gemini API for vision")
                client = genai.Client(api_key=self.api_key)

                config = types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=2000,  # Increased to allow longer analysis text
                    response_mime_type="application/json",
                )

                response = client.models.generate_content(
                    model=self.model,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        analysis_prompt,
                    ],
                    config=config,
                )

                # Check for empty response and provide helpful diagnostics
                if not response.text or not response.text.strip():
                    # Check response metadata for clues
                    finish_reason = None
                    safety_ratings = None
                    if hasattr(response, "response_metadata"):
                        metadata = response.response_metadata
                        finish_reason = metadata.get("finish_reason")
                        if "safety_ratings" in metadata:
                            safety_ratings = metadata.get("safety_ratings")

                    # Check candidates for finish reason
                    if hasattr(response, "candidates") and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, "finish_reason"):
                            finish_reason = candidate.finish_reason
                        if hasattr(candidate, "safety_ratings"):
                            safety_ratings = candidate.safety_ratings

                    error_msg = "Empty response from model"
                    if finish_reason:
                        if finish_reason == "MAX_TOKENS":
                            error_msg = "Model response exceeded token limit. Try reducing prompt or increasing max_output_tokens."
                        elif finish_reason == "SAFETY":
                            error_msg = "Response blocked by safety filters. The image may have triggered content safety policies."
                        elif finish_reason == "RECITATION":
                            error_msg = (
                                "Response blocked due to potential content recitation."
                            )
                        else:
                            error_msg = f"Response finished early: {finish_reason}"

                    if safety_ratings:
                        print(f"DEBUG: Safety ratings: {safety_ratings}")

                    print(f"DEBUG: Empty response - Finish reason: {finish_reason}")
                    # Return graceful fallback instead of raising
                    return {
                        "skinType": user_skin_type or "normal",
                        "concerns": user_concerns or [],
                        "analysis": f"AI analysis temporarily unavailable: {error_msg}. Using provided skin type: {user_skin_type or 'normal'}.",
                    }

                response_text = response.text
                print(f"DEBUG: Gemini API response length: {len(response_text)} chars")
                print(f"DEBUG: First 500 chars: {response_text[:500]}")

                # Parse JSON - the response should be valid JSON with response_mime_type="application/json"
                data = None
                try:
                    # First try direct parse (should work since we requested JSON)
                    data = json.loads(response_text)
                    print("DEBUG: Successfully parsed JSON directly")
                except json.JSONDecodeError as json_error:
                    print(f"DEBUG: Direct JSON parse failed: {json_error}")
                    # Try using parse_json_safely which handles edge cases
                    data = parse_json_safely(response_text)
                    if isinstance(data, dict):
                        print("DEBUG: Successfully parsed JSON using parse_json_safely")
                    else:
                        print(
                            f"DEBUG: parse_json_safely also failed, will try manual extraction"
                        )

                # If we have valid data, validate and return it
                if isinstance(data, dict):
                    print("DEBUG: Successfully parsed JSON from Gemini API")
                    return _validate_llm_response(data, user_skin_type, user_concerns)

                # Fallback: Try manual extraction with improved logic
                print("DEBUG: Attempting manual JSON extraction")
                import re

                # Remove markdown code blocks if present
                clean_text = response_text
                if "```json" in clean_text:
                    json_match = re.search(
                        r"```json\s*(\{[\s\S]*?\})\s*```", clean_text, re.DOTALL
                    )
                    if json_match:
                        clean_text = json_match.group(1)
                        print("DEBUG: Extracted JSON from ```json block")
                elif "```" in clean_text:
                    json_match = re.search(
                        r"```\s*(\{[\s\S]*?\})\s*```", clean_text, re.DOTALL
                    )
                    if json_match:
                        clean_text = json_match.group(1)
                        print("DEBUG: Extracted JSON from ``` block")

                # Try to find and parse JSON object
                json_obj = _find_first_json_obj(clean_text)
                if json_obj:
                    try:
                        data = json.loads(json_obj)
                        print(
                            "DEBUG: Successfully parsed JSON using _find_first_json_obj"
                        )
                        return _validate_llm_response(
                            data, user_skin_type, user_concerns
                        )
                    except json.JSONDecodeError as e:
                        print(f"DEBUG: JSON decode error: {e}")
                        print(f"DEBUG: JSON object preview: {json_obj[:300]}")

                # Try parsing entire cleaned text as JSON
                if clean_text.strip().startswith("{"):
                    try:
                        data = json.loads(clean_text)
                        print("DEBUG: Successfully parsed cleaned text as JSON")
                        return _validate_llm_response(
                            data, user_skin_type, user_concerns
                        )
                    except json.JSONDecodeError as e:
                        print(f"DEBUG: Direct JSON parse failed: {e}")

                # Remove code block markers and try again
                if "```" in clean_text:
                    lines = clean_text.split("\n")
                    cleaned_lines = []
                    in_code_block = False
                    for line in lines:
                        if line.strip().startswith("```"):
                            in_code_block = not in_code_block
                            continue
                        if not in_code_block:
                            cleaned_lines.append(line)
                    clean_text = "\n".join(cleaned_lines).strip()

                # If we have meaningful text (even if not JSON), extract what we can
                if clean_text and len(clean_text.strip()) > 10:
                    # Try to extract structured info from text even if not JSON
                    skin_type_match = re.search(
                        r"(?i)skin\s*type[:\s]+(\w+)", clean_text
                    )
                    concerns_matches = re.findall(
                        r"(?i)(acne|wrinkles|dark\s*spots?|aging|dryness|oiliness|sensitivity|redness)",
                        clean_text,
                    )

                    extracted_skin_type = (
                        skin_type_match.group(1).lower() if skin_type_match else None
                    )
                    extracted_concerns = (
                        list(set([c.lower() for c in concerns_matches]))
                        if concerns_matches
                        else []
                    )

                    return {
                        "skinType": extracted_skin_type or user_skin_type or "normal",
                        "concerns": extracted_concerns or user_concerns or [],
                        "analysis": clean_text[
                            :2000
                        ],  # Limit length but allow longer text
                    }

                return {
                    "skinType": user_skin_type or "normal",
                    "concerns": user_concerns or [],
                    "analysis": "Unable to parse AI analysis response. Please try again or check the image format.",
                }

            except ImportError:
                print("DEBUG: google.genai not available")
                # Fallback to error message
                return {
                    "skinType": user_skin_type or "normal",
                    "concerns": user_concerns or [],
                    "analysis": "Vision analysis requires google-genai package. Please install it.",
                }
            except Exception as api_error:
                print(f"DEBUG: Direct Gemini API error: {api_error}")
                import traceback

                print(f"Traceback: {traceback.format_exc()}")
                # Return error instead of raising
                return {
                    "skinType": user_skin_type or "normal",
                    "concerns": user_concerns or [],
                    "analysis": f"Error analyzing image: {str(api_error)}",
                }

        except Exception as e:
            print(f"Error analyzing facial image with LLM: {str(e)}")
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
            Dictionary with conflict analysis
        """
        if not self.is_available():
            return None

        try:

            def truncate_ingredients(ingredients: str, max_length: int = 300) -> str:
                if not ingredients or ingredients == "Not specified":
                    return "Not specified"
                if len(ingredients) <= max_length:
                    return ingredients
                truncated = ingredients[:max_length]
                last_comma = truncated.rfind(",")
                if last_comma > max_length * 0.8:
                    truncated = truncated[:last_comma]
                return truncated + " ... (more ingredients)"

            products_text = "\n".join(
                [
                    f"{i+1}. {p.get('name', 'Unknown')}: {truncate_ingredients(p.get('ingredients', 'Not specified'))}"
                    for i, p in enumerate(products)
                ]
            )

            system_prompt = """You are a cosmetic dermatology expert. Analyze ingredient safety and compatibility. You must always return valid JSON. Never return empty responses."""

            user_prompt = f"""Analyze potential ingredient conflicts or safety concerns between these cosmetic products. You must respond with valid JSON in this exact format:

{{
  "conflictDetected": true or false,
  "conflictDetails": "Brief explanation of any conflicts found (max 50 words)",
  "safetyWarning": "Safety warning if needed, or null",
  "alternatives": ["suggestion 1", "suggestion 2"] or []
}}

Products to analyze:
{products_text}

Instructions:
- Analyze each product's ingredients
- Check for known conflicts, incompatibilities, or safety concerns
- Return valid JSON only (no markdown, no code blocks)
- If no conflicts found, set conflictDetected to false but still provide analysis
- Always provide a response, even if brief"""

            print(f"DEBUG: Analyzing ingredient conflicts for {len(products)} products")
            # Use much higher max_tokens because gemini-2.5-flash uses reasoning tokens
            # which don't appear in content but count toward the limit
            # We need enough tokens for both reasoning (~400-800) AND content (~200-400)
            response_text = self.generate_text(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=2000,  # Increased significantly to account for reasoning + content tokens
                max_retries=3,
            )

            if not response_text:
                print(
                    "DEBUG: generate_text returned None for ingredient conflict analysis"
                )
                return None

            print(
                f"DEBUG: Received response for ingredient conflict analysis (length: {len(response_text) if response_text else 0})"
            )

            # Parse JSON response
            print(
                f"DEBUG: Attempting to parse JSON response (first 200 chars): {response_text[:200] if response_text else '(empty)'}"
            )
            data = parse_json_safely(response_text)
            if isinstance(data, dict):
                print(
                    "DEBUG: Successfully parsed JSON for ingredient conflict analysis"
                )
                return {
                    "conflictDetected": bool(data.get("conflictDetected", False)),
                    "conflictDetails": str(
                        data.get("conflictDetails", "No detailed analysis available.")
                    ),
                    "safetyWarning": (
                        data.get("safetyWarning") if data.get("safetyWarning") else None
                    ),
                    "alternatives": (
                        data.get("alternatives", [])
                        if isinstance(data.get("alternatives"), list)
                        else []
                    ),
                }
            else:
                print(
                    f"DEBUG: Failed to parse JSON, using fallback extraction (data type: {type(data)})"
                )

            # Fallback: try to extract basic info from text
            import re

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
                "conflictDetails": response_text[:500],
                "safetyWarning": (
                    None
                    if conflict_detected
                    else "Unable to parse response format. Please try again."
                ),
                "alternatives": [],
            }

        except Exception as e:
            print(f"Error analyzing ingredient conflicts with LLM: {str(e)}")
            import traceback

            print(f"Traceback: {traceback.format_exc()}")
            return None

    def select_top_products(
        self,
        products: List[Dict[str, Any]],
        skin_profile_summary: str,
        max_products: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """
        Select top products from all available products using LLM.
        LLM will analyze all products and return up to max_products that best match the user's profile.
        Can return fewer or none if none match well.

        Args:
            products: List of product dictionaries with full details (id, name, description, price, category, etc.)
            skin_profile_summary: Summary of user's skin profile and preferences
            max_products: Maximum number of products to select (default: 5)

        Returns:
            Dictionary with selectedProductIds (list of int) and reasons (dict mapping product_id string to reason),
            or None if LLM is unavailable or selection fails
        """
        if not self.is_available() or not products:
            return None

        try:
            # Build products list text with only name and ingredients
            products_text = "\n\n".join(
                [
                    f"Product ID: {p.get('id', 'N/A')}\n"
                    f"Name: {p.get('name', 'Unknown')}\n"
                    f"Ingredients: {p.get('ingredients', 'Not specified')}"
                    for p in products
                ]
            )

            user_prompt = f"""You are a skincare ingredient expert. Select the best products based on ingredient effectiveness for the user's skin concerns. Up to {max_products} products; fewer or none if not suitable.

User Profile:
{skin_profile_summary}

Products:
{products_text}

Rules:
- Evaluate INGREDIENTS only.
- Pick products that match user concerns (acne, wrinkles, spots, sensitivity, dryness, oiliness).
- Prefer proven actives (e.g., niacinamide, salicylic acid, retinol, HA, peptides, ceramides, vitamin C).
- Avoid products that don't support the user's needs.
- If no good matches, return empty list.

Output ONLY valid JSON:
{{"selectedProductIds":[...],"reasons":{{"id":"1–2 sentence ingredient justification"}}}}

CRITICAL: Return ONLY the JSON object, no markdown, no code blocks, no other text."""

            # Use JSON response format
            print(
                f"DEBUG: Selecting top {max_products} products from {len(products)} available products"
            )

            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=self.api_key)

                config = types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=8000,
                    response_mime_type="application/json",
                )

                response = client.models.generate_content(
                    model=self.model,
                    contents=user_prompt,
                    config=config,
                )

                # Check for empty response and provide helpful diagnostics
                if not response.text or not response.text.strip():
                    # Check response metadata for clues
                    finish_reason = None
                    safety_ratings = None
                    if hasattr(response, "response_metadata"):
                        metadata = response.response_metadata
                        finish_reason = metadata.get("finish_reason")
                        if "safety_ratings" in metadata:
                            safety_ratings = metadata.get("safety_ratings")

                    # Check candidates for finish reason
                    if hasattr(response, "candidates") and response.candidates:
                        candidate = response.candidates[0]
                        if hasattr(candidate, "finish_reason"):
                            finish_reason = candidate.finish_reason
                        if hasattr(candidate, "safety_ratings"):
                            safety_ratings = candidate.safety_ratings

                    error_msg = "Empty response from model"
                    # Handle both string and enum finish reasons
                    finish_reason_str = str(finish_reason)
                    if finish_reason:
                        if (
                            "MAX_TOKENS" in finish_reason_str
                            or "MAX_TOKENS" == finish_reason_str
                        ):
                            error_msg = "Model response exceeded token limit. Try reducing prompt or increasing max_output_tokens."
                        elif (
                            "SAFETY" in finish_reason_str
                            or "SAFETY" == finish_reason_str
                        ):
                            error_msg = "Response blocked by safety filters."
                        elif (
                            "RECITATION" in finish_reason_str
                            or "RECITATION" == finish_reason_str
                        ):
                            error_msg = (
                                "Response blocked due to potential content recitation."
                            )
                        else:
                            error_msg = f"Response finished early: {finish_reason}"

                    if safety_ratings:
                        print(f"DEBUG: Safety ratings: {safety_ratings}")

                    print(
                        f"DEBUG: Empty LLM product selection response - Finish reason: {finish_reason}"
                    )
                    # Return None to allow fallback to algorithm-based ranking
                    return None

                response_text = response.text
                print(
                    f"DEBUG: LLM product selection response length: {len(response_text)} chars"
                )

                # Parse JSON
                data = None
                try:
                    data = json.loads(response_text)
                    print("DEBUG: Successfully parsed JSON directly")
                except json.JSONDecodeError as json_error:
                    print(f"DEBUG: Direct JSON parse failed: {json_error}")
                    data = parse_json_safely(response_text)
                    if isinstance(data, dict):
                        print("DEBUG: Successfully parsed JSON using parse_json_safely")

                # Validate using Pydantic
                if isinstance(data, dict) and PYDANTIC_DTOS_AVAILABLE:
                    try:
                        validated = LLMProductSelectionResponse(**data)
                        print(
                            "DEBUG: Successfully validated product selection with Pydantic"
                        )

                        # Ensure selectedProductIds doesn't exceed max_products
                        selected_ids = validated.selectedProductIds[:max_products]

                        # Filter reasons to only include selected products
                        filtered_reasons = {
                            str(pid): validated.reasons.get(
                                str(pid), "Selected as a good match for your profile"
                            )
                            for pid in selected_ids
                        }

                        return {
                            "selectedProductIds": selected_ids,
                            "reasons": filtered_reasons,
                        }
                    except Exception as validation_error:
                        print(f"DEBUG: Pydantic validation failed: {validation_error}")
                        # Fallback: try to extract valid fields
                        selected_ids = data.get("selectedProductIds", [])
                        if not isinstance(selected_ids, list):
                            selected_ids = []
                        # Ensure it's a list of integers and limit to max_products
                        selected_ids = [
                            int(pid)
                            for pid in selected_ids[:max_products]
                            if isinstance(pid, (int, str))
                        ]
                        reasons = data.get("reasons", {})
                        if not isinstance(reasons, dict):
                            reasons = {}
                        return {
                            "selectedProductIds": selected_ids,
                            "reasons": {
                                str(pid): reasons.get(
                                    str(pid), "Selected as a good match"
                                )
                                for pid in selected_ids
                            },
                        }
                elif isinstance(data, dict):
                    # No Pydantic available, use manual validation
                    selected_ids = data.get("selectedProductIds", [])
                    if not isinstance(selected_ids, list):
                        selected_ids = []
                    selected_ids = [
                        int(pid)
                        for pid in selected_ids[:max_products]
                        if isinstance(pid, (int, str))
                    ]
                    reasons = data.get("reasons", {})
                    if not isinstance(reasons, dict):
                        reasons = {}
                    return {
                        "selectedProductIds": selected_ids,
                        "reasons": {
                            str(pid): reasons.get(str(pid), "Selected as a good match")
                            for pid in selected_ids
                        },
                    }

                print("DEBUG: Failed to parse LLM product selection response")
                return None

            except ImportError:
                print("DEBUG: google.genai not available, falling back to LangChain")
                # Fallback to LangChain if google.genai not available
                response_text = self.generate_text(
                    prompt=user_prompt,
                    system_prompt=None,  # Prompt already includes role
                    temperature=0.3,
                    max_tokens=4000,
                    max_retries=2,
                )

                if not response_text:
                    return None

                data = parse_json_safely(response_text)
                if isinstance(data, dict):
                    selected_ids = data.get("selectedProductIds", [])
                    if not isinstance(selected_ids, list):
                        selected_ids = []
                    selected_ids = [
                        int(pid)
                        for pid in selected_ids[:max_products]
                        if isinstance(pid, (int, str))
                    ]
                    reasons = data.get("reasons", {})
                    if not isinstance(reasons, dict):
                        reasons = {}

                    if PYDANTIC_DTOS_AVAILABLE:
                        try:
                            validated = LLMProductSelectionResponse(
                                selectedProductIds=selected_ids,
                                reasons={
                                    str(pid): reasons.get(str(pid), "Selected")
                                    for pid in selected_ids
                                },
                            )
                            return {
                                "selectedProductIds": validated.selectedProductIds,
                                "reasons": validated.reasons,
                            }
                        except:
                            pass

                    return {
                        "selectedProductIds": selected_ids,
                        "reasons": {
                            str(pid): reasons.get(str(pid), "Selected")
                            for pid in selected_ids
                        },
                    }

                return None

        except Exception as e:
            print(f"Error selecting products with LLM: {str(e)}")
            import traceback

            print(f"Traceback: {traceback.format_exc()}")
            return None


# Global instance
llm_service = LLMService()
