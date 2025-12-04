import requests
import os
from typing import Literal


class PhoBERTTelecomGateClient:
    """Client for PhoBERT TelecomGate API to check if input is telecom-related."""
    
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv("PHOBERT_TELECOMGATE_BASE_URL", "http://localhost:8136/v1")
    
    def infer(self, text: str) -> bool:
        """
        Check if the given text is related to telecommunications.
        
        Args:
            text: The input text to analyze
            
        Returns:
            True if the text is telecom-related, False otherwise
            
        Raises:
            Exception: If the API returns an error status code
        """
        url = f"{self.base_url}/infer"
        response = requests.post(url, headers={"Content-Type": "text/plain"}, data=text.encode('utf-8'))
        
        if response.status_code == 200:
            result = response.text.strip()
            if result == "true":
                return True
            elif result == "false":
                return False
            else:
                raise Exception(f"Unexpected response from PhoBERT TelecomGate: {result}")
        else:
            raise Exception(f"PhoBERT TelecomGate API error ({response.status_code}): {response.text}")


class ReasoningRouterClient:
    """Client for Reasoning Router API to check if reasoning is needed."""
    
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv("REASONING_ROUTER_BASE_URL", "http://localhost:8237/v1")
    
    def infer(self, text: str) -> Literal["lookup_only", "reasoning_needed"]:
        """
        Check if the given text requires reasoning capabilities to answer.
        
        Args:
            text: The input text to analyze
            
        Returns:
            "reasoning_needed" if reasoning is required, "lookup_only" otherwise
            
        Raises:
            Exception: If the API returns an error status code
        """
        url = f"{self.base_url}/infer"
        response = requests.post(url, headers={"Content-Type": "text/plain"}, data=text.encode('utf-8'))
        
        if response.status_code == 200:
            result = response.text.strip()
            if result in ["lookup_only", "reasoning_needed"]:
                return result  # type: ignore
            else:
                raise Exception(f"Unexpected response from Reasoning Router: {result}")
        else:
            raise Exception(f"Reasoning Router API error ({response.status_code}): {response.text}")
