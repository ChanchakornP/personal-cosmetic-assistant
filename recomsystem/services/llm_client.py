"""
LLM client service for AI-powered features.
Initializes LLM connection on instantiation for better performance.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import OpenAI client (optional - graceful fallback if not configured)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Get LLM configuration from environment
LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
LLM_BASE_URL = os.getenv("OPENAI_BASE_URL")  # Optional custom base URL

class LLMClient:
    """
    Client for interacting with LLM services (OpenAI).
    Connection is initialized when the client is instantiated.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize LLM client and create connection.
        
        Args:
            api_key: API key for LLM service (defaults to OPENAI_API_KEY env var)
            model: Model name to use (defaults to LLM_MODEL env var or gpt-3.5-turbo)
            base_url: Optional custom base URL for the API
        """
        self.api_key = api_key or LLM_API_KEY
        self.model = model or LLM_MODEL
        self.base_url = base_url or LLM_BASE_URL
        self.client = None
        self._initialized = False
        
        # Initialize the connection if API key is provided
        if self.api_key:
            self._initialize()
        else:
            # Log warning but allow graceful degradation
            print("Warning: LLM_API_KEY not set. LLM features will be disabled.")
    
    def _initialize(self):
        """
        Initialize the LLM client connection.
        Called during __init__ to establish connection early.
        """
        if not OPENAI_AVAILABLE:
            print("Warning: OpenAI package not installed. Install with: pip install openai")
            return
        
        try:
            # Create client with connection pool
            client_params = {
                "api_key": self.api_key
            }
            if self.base_url:
                client_params["base_url"] = self.base_url
            
            self.client = OpenAI(**client_params)
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
        system_prompt: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate text using the LLM.
        
        Args:
            prompt: User prompt
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            
        Returns:
            Generated text or None if generation fails
        """
        if not self.is_available():
            return None
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating text with LLM: {str(e)}")
            return None
    
    def generate_recommendation_explanation(
        self,
        product_name: str,
        product_description: str,
        skin_profile_summary: str
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
            max_tokens=150
        )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check LLM service health and connectivity.
        
        Returns:
            Dictionary with health status information
        """
        if not OPENAI_AVAILABLE:
            return {
                "available": False,
                "reason": "OpenAI package not installed",
                "initialized": False
            }
        
        if not self.api_key:
            return {
                "available": False,
                "reason": "API key not configured",
                "initialized": False
            }
        
        if not self.is_available():
            return {
                "available": False,
                "reason": "Client initialization failed",
                "initialized": False
            }
        
        # Test connection with a minimal request
        try:
            test_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            return {
                "available": True,
                "initialized": True,
                "model": self.model,
                "connection_test": "success"
            }
        except Exception as e:
            return {
                "available": False,
                "initialized": True,
                "reason": f"Connection test failed: {str(e)}"
            }


# Global instance - connection will be established when imported
llm_client = LLMClient()

