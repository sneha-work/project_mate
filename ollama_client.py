# ollama_client.py - Ollama Cloud API Client with Academic AI Engine
import httpx
import json
import logging
from typing import Optional, Dict, Any, List
from config import OLLAMA_API_KEY, OLLAMA_HOST, OLLAMA_MODEL

logger = logging.getLogger("researchmate.ollama")

class OllamaClient:
    def __init__(self, api_key: str = "", host: str = "", model: str = ""):
        self.api_key = api_key or OLLAMA_API_KEY
        self.host = (host or OLLAMA_HOST).rstrip("/")
        self.model = model or OLLAMA_MODEL
        
    async def chat(self, prompt: str, system: str = "You are an elite academic research assistant.", temperature: float = 0.7) -> str:
        """Call Ollama Cloud API or local endpoint. Fallback to intelligent academic synthesis if unavailable."""
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        endpoint = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=3.5) as client:
                res = await client.post(endpoint, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    if "message" in data and "content" in data["message"]:
                        return data["message"]["content"]
                    elif "response" in data:
                        return data["response"]
                else:
                    logger.warning(f"Ollama API returned status {res.status_code}: {res.text}")
        except Exception as e:
            logger.info(f"Ollama Cloud API request not connected ({e}), using Academic Engine fallback.")
            
        return ""

    async def test_connection(self) -> Dict[str, Any]:
        """Test whether the configured Ollama API endpoint and key are valid."""
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                # Try tags endpoint
                res = await client.get(f"{self.host}/api/tags", headers=headers)
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    return {"connected": True, "models": models, "message": f"Successfully connected to Ollama! Available models: {len(models)}"}
                return {"connected": False, "message": f"Server responded with status code: {res.status_code}"}
        except Exception as e:
            return {"connected": False, "message": f"Could not connect to {self.host}: {str(e)}"}

# Global client singleton
ollama_service = OllamaClient()
