import os
import google.generativeai as genai
from typing import Iterator


class GeminiService:
    """Service for interacting with Google Gemini LLM with streaming support."""
    
    def __init__(self, api_key: str | None = None, model_name: str | None = None):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            model_name: Model name (defaults to GEMINI_MODEL env var or 'gemini-1.5-flash')
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment or passed to constructor")
        
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_stream(self, prompt: str) -> Iterator[str]:
        """
        Generate a response with streaming tokens.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Yields:
            Token strings as they are generated
            
        Raises:
            Exception: If generation fails
        """
        try:
            response = self.model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise Exception(f"Gemini generation error: {str(e)}")
    
    def generate(self, prompt: str) -> str:
        """
        Generate a complete response (non-streaming).
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            The complete generated text
            
        Raises:
            Exception: If generation fails
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini generation error: {str(e)}")
